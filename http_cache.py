"""Shared HTTP cache for outbound municipal-API calls.

Why this exists
---------------
Each zoning provider hits a city's open-data API (Socrata, ArcGIS REST, etc.).
Under gunicorn on Render we run multiple workers — each with their own in-
process LRU cache in `policy_retrieval`. That means up to N workers issuing N
calls to the same city API for the same parcel within the cache TTL window.

`requests-cache` gives us an HTTP-level cache that:
  - Sits below the in-process LRU (so we still avoid re-doing work even
    when the LRU evicts).
  - Uses SQLite on disk by default — shared across gunicorn workers.
  - Is URL-scoped: only caches calls to the municipal API hosts, NOT
    Nominatim (which we already throttle separately) or anything else.

Activation
----------
The cache only installs when `CANLAND_HTTP_CACHE_PATH` is set. Tests run
without it, so the existing `patch("zoning_providers.base.requests.get")`
calls keep working unchanged.

Env vars
--------
    CANLAND_HTTP_CACHE_PATH         Path to SQLite cache file (no extension).
                                    Empty/unset disables caching entirely.
    CANLAND_HTTP_CACHE_TTL_SECONDS  Per-entry TTL (default: 600 / 10 min)
"""

import logging
import os
from typing import Iterable, Set

logger = logging.getLogger(__name__)

# Hosts whose responses we are willing to cache. Anything not in this set
# bypasses the cache entirely — this keeps Nominatim, geocoders, internal
# health probes, etc. uncached.
_CACHEABLE_HOSTS: Set[str] = {
    "data.edmonton.ca",
    "data.calgary.ca",
}

# Sentinel: a module-level flag so install_cache is idempotent across
# multiple imports / worker restarts within the same process.
_INSTALLED: bool = False


def cacheable_hosts() -> Iterable[str]:
    """Expose the cache-allowed host set for tests / introspection."""
    return tuple(sorted(_CACHEABLE_HOSTS))


def install_http_cache_if_configured() -> bool:
    """Install the global HTTP cache iff `CANLAND_HTTP_CACHE_PATH` is set.

    Returns:
        True if a cache was installed (now or previously), False otherwise.
    """
    global _INSTALLED
    if _INSTALLED:
        return True

    cache_path = (os.environ.get("CANLAND_HTTP_CACHE_PATH") or "").strip()
    if not cache_path:
        return False

    try:
        ttl = int(os.environ.get("CANLAND_HTTP_CACHE_TTL_SECONDS", "600"))
    except ValueError:
        ttl = 600

    try:
        import requests_cache
    except ImportError:
        logger.warning(
            "CANLAND_HTTP_CACHE_PATH=%r set but requests-cache is not installed; "
            "running without HTTP cache.",
            cache_path,
        )
        return False

    # Per-URL expiry: cache only the known municipal-API hosts.
    # Anything else uses DO_NOT_CACHE (i.e. passes through unchanged).
    urls_expire_after = {
        f"{host}/*": ttl for host in _CACHEABLE_HOSTS
    }
    urls_expire_after["*"] = requests_cache.DO_NOT_CACHE

    try:
        # Ensure the parent directory exists so SQLite can create the file.
        parent = os.path.dirname(cache_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        requests_cache.install_cache(
            cache_name=cache_path,
            backend="sqlite",
            allowable_methods=("GET",),
            allowable_codes=(200,),
            urls_expire_after=urls_expire_after,
            # Don't include the canland user-agent string in the cache key —
            # different versions of the tool should still share cache hits.
            ignored_parameters=(),
            stale_if_error=False,
        )
    except Exception as exc:  # noqa: BLE001 — caching is best-effort
        logger.warning("Failed to install HTTP cache at %r: %s", cache_path, exc)
        return False

    _INSTALLED = True
    logger.info(
        "HTTP cache installed: path=%r ttl_seconds=%d hosts=%s",
        cache_path,
        ttl,
        sorted(_CACHEABLE_HOSTS),
    )
    return True


def reset_for_testing() -> None:
    """Reset the cache state so tests can re-exercise the install path."""
    global _INSTALLED
    _INSTALLED = False
    try:
        import requests_cache

        requests_cache.uninstall_cache()
    except Exception:  # noqa: BLE001
        pass
