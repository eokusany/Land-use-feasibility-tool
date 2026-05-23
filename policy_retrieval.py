"""
Policy retrieval for CanLand.

IMPORTANT — Honest preliminary mode (Option A):

This module DOES NOT retrieve real zoning data. It used to invent a zoning code,
setbacks, height limits, and a permitted-use list for every property based on
hardcoded templates. That produced confidently wrong reports for every address.

Until per-municipality zoning APIs are wired in (see OPTION_B_TODO.md), this
module returns only:

  - Municipality identification (name, province, contact info)
  - A link to the municipality's land use bylaw (when known)
  - Generic, province-aware development requirements (building code, planning act)
  - A clear "verification required" flag and verification steps

Anything that would require actually knowing the parcel's zone — the zone code,
permitted uses, setbacks, density, height limits — is intentionally returned as
empty / None. The UI and PDF render these as "Not retrieved — verify with the
municipal planning department."
"""

import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from zoning_providers import ProviderError, ZoningResult, get_provider

logger = logging.getLogger(__name__)

# Cache zoning lookups for at most this many seconds. Bylaws amend frequently,
# so we keep this short. Tunable via env vars for production deploys.
CACHE_TTL_SECONDS = int(os.environ.get("CANLAND_POLICY_CACHE_TTL", "600"))
CACHE_MAX_ENTRIES = int(os.environ.get("CANLAND_POLICY_CACHE_MAX", "256"))


# ---------------------------------------------------------------------------
# Province → (building code, planning act) lookup
# ---------------------------------------------------------------------------

PROVINCE_LEGISLATION = {
    "BC": ("BC Building Code", "Local Government Act"),
    "AB": ("Alberta Building Code", "Municipal Government Act"),
    "SK": ("National Building Code", "Planning and Development Act"),
    "MB": ("Manitoba Building Code", "The Planning Act"),
    "ON": ("Ontario Building Code", "Planning Act"),
    "QC": ("Code de construction du Québec", "Loi sur l'aménagement et l'urbanisme"),
    "NB": ("National Building Code", "Community Planning Act"),
    "NS": ("Nova Scotia Building Code", "Municipal Government Act"),
    "PE": ("National Building Code", "Planning Act"),
    "NL": ("National Building Code", "Urban and Rural Planning Act"),
    "YT": ("National Building Code", "Municipal Act"),
    "NT": ("National Building Code", "Cities, Towns and Villages Act"),
    "NU": ("National Building Code", "Nunavut Planning Act"),
}


VERIFICATION_STEPS = [
    "Look up the parcel on the municipality's online zoning map (link above).",
    "Contact the planning department directly using the contact information shown below.",
    "Request a Letter of Compliance or Zoning Memo for the legal title before relying on any zone designation.",
    "Confirm the current land use bylaw version — bylaws are amended frequently.",
    "If proceeding with development, engage a qualified land use planner familiar with the municipality.",
]


class PolicyRetrieval:
    """
    Return municipality + bylaw context for a property.

    This class does NOT retrieve parcel-level zoning. It returns enough
    information for the user to find that themselves, plus a flag making
    clear that verification is required.
    """

    def __init__(self):
        # OrderedDict gives us O(1) LRU eviction. Values are (expires_at, dict).
        self.policy_cache: "OrderedDict[str, Tuple[float, Dict]]" = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_land_use_policies(self, municipality_info: Dict, property_info: Dict) -> Dict:
        cache_key = self._cache_key(municipality_info, property_info)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        muni_name = municipality_info.get("name", "")
        province = municipality_info.get("province") or None

        building_code, planning_act = PROVINCE_LEGISLATION.get(
            province or "", ("National Building Code of Canada", "Provincial Planning Legislation")
        )

        bylaw = self._get_bylaw_info(municipality_info)

        # Start from the verification-required (Option A) base. If a real
        # zoning provider is available for this municipality and we have
        # coordinates, we'll upgrade the relevant fields below.
        policy_info: Dict = {
            "municipality": muni_name,
            "province": province,

            # --- Verification status (may be upgraded by a provider hit) ---
            "verification_required": True,
            "verification_status": "unverified",   # unverified | verified | provider_failed | outside_coverage
            "verification_message": None,
            "zoning_status": (
                "Not retrieved. Parcel-level zoning must be verified directly "
                "with the municipal planning department."
            ),

            # --- Parcel-level fields (filled in by provider on success) ---
            "zoning": None,
            "zoning_code": None,
            "zone_category": None,
            "zone_overlays": [],
            "zone_source": None,
            "zone_source_url": None,
            "zone_retrieved_at": None,
            "zone_bylaw_section_url": None,
            "zone_provider_notes": [],

            # Permitted/discretionary uses, setbacks, density, height — we
            # still do not fabricate these. Even with a real zone code, the
            # actual numbers live in bylaw text and depend on overlays,
            # exceptions, and discretionary variances. The user is sent to
            # the linked bylaw section for the real values.
            "permitted_uses": [],
            "discretionary_uses": [],
            "setbacks": {},
            "density_restrictions": {},
            "height_restrictions": {},
            "special_provisions": [],

            # --- Generic, verifiable references ---
            "land_use_bylaw": bylaw,
            "bylaw_links": [bylaw["url"]] if bylaw and bylaw.get("url") else [],
            "development_requirements": self._get_dev_requirements(province, building_code, planning_act),
            "verification_steps": VERIFICATION_STEPS,
            "contact_info": municipality_info.get("contact_info", {}),

            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._try_upgrade_with_provider(policy_info, municipality_info, property_info)

        self._cache_put(cache_key, policy_info)
        return policy_info

    # ------------------------------------------------------------------
    # Bounded TTL cache helpers
    # ------------------------------------------------------------------

    def _cache_get(self, key: str) -> Optional[Dict]:
        entry = self.policy_cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            self.policy_cache.pop(key, None)
            return None
        # Mark recent — move to end for LRU semantics
        self.policy_cache.move_to_end(key)
        return value

    def _cache_put(self, key: str, value: Dict) -> None:
        self.policy_cache[key] = (time.time() + CACHE_TTL_SECONDS, value)
        self.policy_cache.move_to_end(key)
        while len(self.policy_cache) > CACHE_MAX_ENTRIES:
            self.policy_cache.popitem(last=False)

    # ------------------------------------------------------------------
    # Provider integration
    # ------------------------------------------------------------------

    def _try_upgrade_with_provider(
        self, policy_info: Dict, municipality_info: Dict, property_info: Dict
    ) -> None:
        """If a zoning provider exists for this municipality, query it and
        merge the result into policy_info. Falls back silently to the
        verification-required base on any failure (after recording the
        failure in verification_status / verification_message)."""
        muni_name = municipality_info.get("name", "")
        provider = get_provider(muni_name)
        if provider is None:
            return  # No provider for this city — stay in Option A mode

        coords = (property_info or {}).get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        if lat is None or lon is None:
            policy_info["verification_status"] = "provider_failed"
            policy_info["verification_message"] = (
                f"{provider.municipality} zoning lookup is supported, but no "
                "coordinates were available for this address. Geocoding may have failed."
            )
            return

        # Sanity-check the geocode against the municipality centroid before
        # hitting the provider. Catches the failure mode that motivated this
        # whole effort: Nominatim returning a point hundreds of km from where
        # the user actually meant. We import lazily to avoid a circular dep
        # at module import time.
        try:
            from property_parser import is_point_within_municipality
            in_bounds, dist_km = is_point_within_municipality(
                float(lat), float(lon), municipality_info
            )
        except Exception:  # noqa: BLE001 — boundary check is a hint, never fatal
            in_bounds, dist_km = True, 0.0

        if not in_bounds:
            policy_info["verification_status"] = "outside_coverage"
            policy_info["verification_message"] = (
                f"The geocoded coordinates are ~{dist_km:.0f} km from "
                f"{provider.municipality}'s centre. The geocoder may have "
                "returned the wrong location for this address. Try entering "
                "more specific information (postal code, intersection, or a "
                "neighbourhood name)."
            )
            return

        t0 = time.perf_counter()
        try:
            result: Optional[ZoningResult] = provider.lookup(float(lat), float(lon))
        except ProviderError as exc:
            self._log_provider_call(provider, "provider_failed", t0, error=str(exc))
            policy_info["verification_status"] = "provider_failed"
            policy_info["verification_message"] = (
                f"{provider.municipality} zoning service is currently unavailable "
                f"({exc}). Showing preliminary information only — verify with the "
                "municipality before relying on this report."
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive: never let a provider crash CanLand
            self._log_provider_call(provider, "provider_failed", t0, error=str(exc), unexpected=True)
            policy_info["verification_status"] = "provider_failed"
            policy_info["verification_message"] = (
                f"{provider.municipality} zoning lookup encountered an unexpected error: {exc}"
            )
            return

        if result is None:
            self._log_provider_call(provider, "outside_coverage", t0)
            policy_info["verification_status"] = "outside_coverage"
            policy_info["verification_message"] = (
                f"The geocoded coordinates do not fall inside any {provider.municipality} "
                "zoning polygon. The address may be outside the city, or the geocoder "
                "may have returned the wrong location."
            )
            return

        self._log_provider_call(provider, "verified", t0, zone=result.zone_code)

        # Success — upgrade to verified mode
        policy_info["verification_required"] = False
        policy_info["verification_status"] = "verified"
        policy_info["verification_message"] = (
            f"Zone retrieved from {result.source} on "
            f"{result.retrieved_at}. Setbacks, height limits, density, and "
            "permitted uses still must be read from the bylaw section linked below."
        )
        policy_info["zoning_status"] = (
            f"Verified from {result.source}. "
            "Specific setbacks, height limits, density, and use rules are not "
            "included here — open the linked bylaw section for the authoritative text."
        )
        policy_info["zoning"] = f"{result.zone_code} — {result.zone_name}".strip(" —")
        policy_info["zoning_code"] = result.zone_code
        policy_info["zone_overlays"] = [o.to_dict() for o in result.overlays]
        policy_info["zone_source"] = result.source
        policy_info["zone_source_url"] = result.source_url
        policy_info["zone_retrieved_at"] = result.retrieved_at
        policy_info["zone_bylaw_section_url"] = result.bylaw_section_url
        policy_info["zone_provider_notes"] = list(result.provider_notes)

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    @staticmethod
    def _log_provider_call(provider, status: str, t0: float, **extra) -> None:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        parts = [f"provider={provider.name}", f"status={status}", f"latency_ms={elapsed_ms}"]
        for key, value in extra.items():
            parts.append(f"{key}={value!r}")
        if status in {"provider_failed"}:
            logger.warning("zoning_lookup " + " ".join(parts))
        else:
            logger.info("zoning_lookup " + " ".join(parts))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(municipality_info: Dict, property_info: Dict) -> str:
        """Stable cache key based on municipality + raw property input.

        The previous implementation used `id(property_info)` which is reused
        after garbage collection and could collide between unrelated requests.
        """
        muni_name = municipality_info.get("name", "")
        province = municipality_info.get("province", "")
        raw = property_info.get("raw_input", {}) if isinstance(property_info, dict) else {}
        payload = json.dumps([muni_name, province, raw], sort_keys=True, default=str)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_bylaw_info(municipality_info: Dict) -> Optional[Dict]:
        url = municipality_info.get("land_use_bylaw")
        if not url:
            return None
        return {
            "url": url,
            "title": f"{municipality_info.get('name', '')} Land Use Bylaw".strip(),
        }

    def get_cottage_development_analysis(self, policy_info: Dict, property_details: Dict) -> Dict:
        """
        Cottage / resort development analysis.

        The previous implementation produced specific cottage-unit counts
        (e.g. "developable acreage * 4.5 units/acre") based on a fabricated
        zone category. Those numbers were not grounded in real zoning data
        and have been removed. Until per-municipality zoning lookup is wired
        in, this method returns a verification-required structure consistent
        with the rest of the tool.
        """
        return {
            "feasibility": "Verification Required",
            "cottage_potential": {},
            "regulatory_considerations": [
                "Cottage / tourist accommodation feasibility depends on the specific zone designation, "
                "which CanLand has not retrieved.",
                "Most rural and agricultural zones in Canada do not permit cottage rentals as of right; "
                "rezoning or a discretionary use approval may be required.",
                "Servicing constraints (water, septic, fire access) typically drive feasibility more than "
                "the zone code itself.",
            ],
            "next_steps": [
                "Confirm the current zone designation with the municipal planning department.",
                "Ask the municipality whether tourist accommodation / cottage rental is a permitted, "
                "discretionary, or prohibited use in that zone.",
                "Engage a qualified land use planner before incurring any further development costs.",
                "Commission a Phase 1 environmental site assessment.",
                "Obtain a servicing report (water supply, septic capacity, fire access).",
            ],
        }

    @staticmethod
    def _get_dev_requirements(province: Optional[str], building_code: str, planning_act: str) -> List[str]:
        # These apply to essentially any development in Canada and are safe to
        # state without parcel-level data.
        return [
            "Development permit required for most new construction or change of use",
            "Building permit required prior to construction",
            f"Compliance with {building_code}",
            f"Compliance with {planning_act}",
            "Servicing connections (water, sewer, stormwater) must be confirmed with the municipality",
            "Site-specific requirements (setbacks, height, density, parking) must be confirmed against the current land use bylaw",
        ]
