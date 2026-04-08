"""
Zoning provider registry.

Each provider knows how to query a single municipality's open-data API for
parcel-level zoning. PolicyRetrieval looks up the provider by municipality
name and falls back to the verification-required mode (Option A) when no
provider is registered or when a provider call fails.

To add a new city, implement a ZoningProvider subclass and add it to
PROVIDERS below.
"""

from typing import Dict, Optional, Type

from .base import ZoningProvider, ZoningResult, ProviderError
from .edmonton import EdmontonZoningProvider


# Registry — keys are lowercased municipality names. We match on the
# municipality name CanLand has already resolved (not on raw user input),
# so this stays a small, deliberate list.
PROVIDERS: Dict[str, Type[ZoningProvider]] = {
    "edmonton": EdmontonZoningProvider,
}


def get_provider(municipality_name: str) -> Optional[ZoningProvider]:
    """Return an instantiated provider for the given municipality, or None."""
    if not municipality_name:
        return None
    cls = PROVIDERS.get(municipality_name.strip().lower())
    return cls() if cls else None


__all__ = [
    "ZoningProvider",
    "ZoningResult",
    "ProviderError",
    "PROVIDERS",
    "get_provider",
]
