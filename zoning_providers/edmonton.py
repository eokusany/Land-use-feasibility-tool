"""
Edmonton zoning provider.

Queries the City of Edmonton open data portal (Socrata) for the parcel-level
zone designation under Zoning Bylaw 20001 (effective January 2024).

Datasets:
  - fixa-tstc  "Zoning Bylaw Geographical Data"  (base zones, includes bylaw URL per zone)
  - 6w3s-58pv  "Zoning Overlays"                  (overlays applying on top of the base zone)

The bug report that motivated this work — "8520 Jasper ave, 1403" — was
returning fabricated "R-1 Single Family Residential" for every Edmonton
address. The R-1 / R-2 / R-3 codes were retired by Bylaw 20001 in January
2024 and no longer exist in Edmonton's zoning system.
"""

from datetime import datetime, timezone
from typing import List, Optional

from .base import ProviderError, ZoningOverlay, ZoningProvider, ZoningResult


# Socrata SoQL endpoints. Public — no auth required for read-only queries
# under Socrata's default rate limits.
ZONES_ENDPOINT = "https://data.edmonton.ca/resource/fixa-tstc.json"
OVERLAYS_ENDPOINT = "https://data.edmonton.ca/resource/6w3s-58pv.json"


# Notes that get attached to specific zone codes to help the user
# understand what they're looking at. Kept short and factual.
_ZONE_NOTES = {
    "DC1": [
        "DC1 (Direct Development Control) is a site-specific zone — the rules "
        "are written into the bylaw provision for this exact site, not into a "
        "general zone template. The linked bylaw section IS the regulation."
    ],
    "DC2": [
        "DC2 (Site Specific Development Control Provision) is a custom zone "
        "negotiated for this site. The linked bylaw section is the actual "
        "regulation — there are no generic setbacks, height limits, or use "
        "lists that apply."
    ],
}


class EdmontonZoningProvider(ZoningProvider):
    name = "edmonton"
    municipality = "Edmonton"
    province = "AB"
    source = "City of Edmonton Open Data — Zoning Bylaw 20001"
    source_url = "https://data.edmonton.ca/Thematic-Features/Zoning-Bylaw-Geographical-Data/fixa-tstc"

    def lookup(self, lat: float, lon: float) -> Optional[ZoningResult]:
        if lat is None or lon is None:
            return None

        zone_row = self._query_zone(lat, lon)
        if not zone_row:
            return None  # outside Edmonton — caller falls back gracefully

        zone_code = (zone_row.get("zoning") or "").strip()
        zone_name = (zone_row.get("description") or "").strip()
        bylaw_url = (zone_row.get("url") or "").strip() or None

        if not zone_code:
            # Polygon hit but no zone code — treat as a malformed response
            raise ProviderError("Edmonton zoning API returned a polygon hit with no zone code")

        # Overlays are best-effort. If the overlay query fails we still
        # return the base zone — overlays are additional context, not the
        # core answer.
        try:
            overlays = self._query_overlays(lat, lon)
        except ProviderError:
            overlays = []

        notes = list(_ZONE_NOTES.get(self._zone_family(zone_code), []))

        return ZoningResult(
            zone_code=zone_code,
            zone_name=zone_name,
            source=self.source,
            source_url=self.source_url,
            retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            bylaw_section_url=bylaw_url,
            overlays=overlays,
            provider_notes=notes,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _zone_family(zone_code: str) -> str:
        """Return the zone code's family (e.g. 'RSM h12' -> 'RSM')."""
        return zone_code.split()[0].split("-")[0].upper() if zone_code else ""

    def _query_zone(self, lat: float, lon: float) -> Optional[dict]:
        params = {
            "$select": "id,zoning,description,url",
            "$where": f"intersects(geometry_multipolygon, 'POINT({lon} {lat})')",
            "$limit": "1",
        }
        rows = self._get_json(ZONES_ENDPOINT, params)
        return rows[0] if rows else None

    def _query_overlays(self, lat: float, lon: float) -> List[ZoningOverlay]:
        params = {
            "$select": "overlay_code,overlay_descr,bylaw_no",
            "$where": f"intersects(geometry_multipolygon, 'POINT({lon} {lat})')",
            "$limit": "20",
        }
        rows = self._get_json(OVERLAYS_ENDPOINT, params)
        overlays = []
        for row in rows:
            code = (row.get("overlay_code") or "").strip()
            desc = (row.get("overlay_descr") or "").strip()
            if not code:
                continue
            overlays.append(ZoningOverlay(
                code=code,
                description=desc,
                bylaw_no=(row.get("bylaw_no") or "").strip() or None,
            ))
        return overlays
