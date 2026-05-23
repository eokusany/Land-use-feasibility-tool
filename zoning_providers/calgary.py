"""Calgary zoning provider.

Queries the City of Calgary open data portal (Socrata) for the parcel-level
land-use district under Bylaw 1P2007.

Dataset:
    - qe6k-p9nh  "Land Use Districts"
      columns: lu_bylaw, lu_code, label, description, major, generalize,
               multipolygon (geometry)
    - As of mid-2026 the dataset contains ~10,340 polygons covering all of
      Calgary.

Verified against the live API on 2026-05-23.
"""

from datetime import datetime, timezone
from typing import Optional

from .base import ProviderError, ZoningProvider, ZoningResult


# Public Socrata endpoint — no auth required for read-only queries.
ZONES_ENDPOINT = "https://data.calgary.ca/resource/qe6k-p9nh.json"
DATASET_URL = "https://data.calgary.ca/Base-Maps/Land-Use-Districts-Map/qe6k-p9nh"

# Calgary's Direct Control districts. DC is site-specific — the actual rules
# live in the bylaw provision for that exact site, not in a generic template.
_ZONE_NOTES = {
    "DC": [
        "DC (Direct Control District) zones in Calgary are site-specific — "
        "the bylaw provision for this exact site is the regulation, not a "
        "generic template. Look up the DC bylaw amendment to see the rules "
        "that actually apply."
    ],
}


class CalgaryZoningProvider(ZoningProvider):
    name = "calgary"
    municipality = "Calgary"
    province = "AB"
    source = "City of Calgary Open Data — Land Use Bylaw 1P2007"
    source_url = DATASET_URL

    def lookup(self, lat: float, lon: float) -> Optional[ZoningResult]:
        if lat is None or lon is None:
            return None

        zone_row = self._query_zone(lat, lon)
        if not zone_row:
            return None  # outside Calgary — caller falls back gracefully

        zone_code = (zone_row.get("lu_code") or "").strip()
        description = (zone_row.get("description") or "").strip()
        major = (zone_row.get("major") or "").strip()
        generalize = (zone_row.get("generalize") or "").strip()

        if not zone_code:
            raise ProviderError(
                "Calgary zoning API returned a polygon hit with no land use code"
            )

        # Prefer the full description ("Commercial - Community 1") when present,
        # falling back to the generalised label ("Community Commercial").
        zone_name = description or generalize or major

        notes = list(_ZONE_NOTES.get(self._zone_family(zone_code), []))

        return ZoningResult(
            zone_code=zone_code,
            zone_name=zone_name,
            source=self.source,
            source_url=self.source_url,
            retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            # Calgary doesn't expose a per-zone deep link the way Edmonton's
            # bylaw 20001 does, so we link to the bylaw landing page.
            bylaw_section_url="https://www.calgary.ca/planning/land-use/bylaw-1p2007.html",
            overlays=[],
            provider_notes=notes,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _zone_family(zone_code: str) -> str:
        """Return the zone code's family (e.g. 'R-G' -> 'R', 'DC' -> 'DC')."""
        if not zone_code:
            return ""
        # DC (Direct Control) is exact — no dash, the whole code is the family.
        head = zone_code.split()[0]
        # Treat the prefix before the first dash as the family. "R-G" -> "R",
        # "C-COR2" -> "C", "S-SPR" -> "S", "DC" -> "DC", "MU-1" -> "MU".
        if head == "DC":
            return "DC"
        return head.split("-")[0].upper()

    def _query_zone(self, lat: float, lon: float) -> Optional[dict]:
        params = {
            "$select": "lu_bylaw,lu_code,label,description,major,generalize",
            "$where": f"intersects(multipolygon, 'POINT({lon} {lat})')",
            "$limit": "1",
        }
        rows = self._get_json(ZONES_ENDPOINT, params)
        return rows[0] if rows else None
