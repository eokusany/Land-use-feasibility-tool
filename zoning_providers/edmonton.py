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

from .aerial import build_static_aerial
from .base import ProviderError, ZoningOverlay, ZoningProvider, ZoningResult
from .parcel_context import (
    AdjacentZone,
    LotCharacteristics,
    OverlayFlag,
    ParcelContext,
    PermitRecord,
)


# Socrata SoQL endpoints. Public — no auth required for read-only queries
# under Socrata's default rate limits.
ZONES_ENDPOINT = "https://data.edmonton.ca/resource/fixa-tstc.json"
OVERLAYS_ENDPOINT = "https://data.edmonton.ca/resource/6w3s-58pv.json"

# Tier 1 parcel context endpoints — verified against the open-data portal on
# 2026-05-24. See tests/fixtures/README.md for the field-name source of truth.
#
# Edmonton no longer publishes parcel polygons via open data (transferred to
# Alberta Data Partnerships in November 2021). The Title Parcels dataset
# below is point-based — we get `area` (m²) but no perimeter. Frontage and
# depth are therefore not derivable from this source and stay None.
PARCEL_ENDPOINT = "https://data.edmonton.ca/resource/9tyx-zfd4.json"
PARCEL_GEOM = "geometry_point"
PARCEL_AREA_FIELD = "area"
PARCEL_SEARCH_RADIUS_M = 50  # tight ring around the query point to find the parcel under it

# Edmonton development permits — point dataset.
PERMIT_ENDPOINT = "https://data.edmonton.ca/resource/q4gd-6q9r.json"
PERMIT_GEOM = "location"
PERMIT_NUMBER_FIELD = "city_file_number"
PERMIT_DATE_FIELD = "permit_date"
PERMIT_STATUS_FIELD = "status"
PERMIT_WORKTYPE_FIELD = "permit_type"
PERMIT_DESCRIPTION_FIELD = "description_of_development"
PERMIT_SEARCH_RADIUS_M = 50
PERMIT_LOOKBACK_YEARS = 5

# Edmonton heritage — point dataset (Register and Inventory of Historic Resources).
HERITAGE_ENDPOINT = "https://data.edmonton.ca/resource/jgsn-dhai.json"
HERITAGE_GEOM = "geometry_point"
HERITAGE_NAME_FIELD = "name_of_historic_resource"
HERITAGE_RADIUS_M = 25

# Edmonton "flood" is encoded as zoning overlays — same dataset as OVERLAYS_ENDPOINT,
# filtered to the three flood-related codes. We deliberately reuse the existing
# OVERLAYS_ENDPOINT constant rather than defining a separate flood endpoint.
FLOOD_OVERLAY_CODES = ("FP", "NSRV", "NS10")

# Adjacent zones — reuses the existing ZONES_ENDPOINT (fixa-tstc).
# 300 m radius (not 100 m) because Edmonton's downtown zoning polygons are large.
NEIGHBOUR_ZONES_RADIUS_M = 300


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

    def context(self, lat: float, lon: float) -> Optional[ParcelContext]:
        """Return Tier 1 parcel context. Never raises — per-feature failures
        are recorded in `ParcelContext.warnings`. Call order (parcel,
        permits, heritage, flood, neighbour zones) is locked because the
        tests in tests/test_edmonton_context.py mock responses in that order."""
        if lat is None or lon is None:
            return None
        ctx = ParcelContext()
        self._populate_lot(ctx, lat, lon)
        self._populate_permits(ctx, lat, lon)
        self._populate_heritage(ctx, lat, lon)
        self._populate_flood(ctx, lat, lon)
        self._populate_adjacent_zones(ctx, lat, lon)
        # Dedupe overlay flags by (category, code) — APIs can return multiple
        # identical polygons (e.g. several Floodplain polygons covering one parcel).
        seen = set()
        deduped = []
        for f in ctx.overlay_flags:
            key = (f.category, f.code)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(f)
        ctx.overlay_flags = deduped
        ctx.aerial_image = build_static_aerial(lat=lat, lon=lon)
        if ctx.aerial_image is None:
            ctx.warnings.append("aerial image skipped: PLOTLINE_MAPBOX_TOKEN not set")
        return ctx

    # ------------------------------------------------------------------
    # Per-feature helpers (Tier 1 parcel context)
    # ------------------------------------------------------------------

    def _populate_lot(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        """Fetch the closest title parcel under the coordinate and record its
        area. Edmonton's open data does not include parcel perimeter, so
        frontage/depth stay None.

        SoQL: `within_circle(geometry_point, <lat>, <lon>, 50)` plus
        `distance_in_meters` ORDER returns the nearest parcel centroid first.
        Limit 1 means we take only that nearest parcel.
        """
        try:
            params = {
                "$select": f"id,{PARCEL_AREA_FIELD},latitude,longitude",
                "$where": f"within_circle({PARCEL_GEOM}, {lat}, {lon}, {PARCEL_SEARCH_RADIUS_M})",
                "$order": f"distance_in_meters({PARCEL_GEOM}, 'POINT({lon} {lat})') ASC",
                "$limit": "1",
            }
            rows = self._get_json(PARCEL_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"parcel lookup failed: {exc}")
            return

        if not rows:
            ctx.warnings.append("no parcel found at this coordinate")
            return

        row = rows[0]
        area = _coerce_float(row.get(PARCEL_AREA_FIELD))
        ctx.lot = LotCharacteristics(
            area_m2=area,
            frontage_m=None,   # Edmonton parcel point dataset has no perimeter
            depth_m=None,
            orientation_deg=None,
            source="City of Edmonton Title Parcels (Point)",
            source_url=PARCEL_ENDPOINT,
        )

    def _populate_permits(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        """Last 5 years of Development Permits at the coordinate. Point dataset
        — use a 50 m circle so we include the parcel under the point plus any
        immediate neighbours that share an address-tagged location."""
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365 * PERMIT_LOOKBACK_YEARS)).strftime(
            "%Y-%m-%dT00:00:00.000"
        )
        try:
            params = {
                "$select": ",".join([
                    PERMIT_NUMBER_FIELD, PERMIT_DATE_FIELD, PERMIT_STATUS_FIELD,
                    PERMIT_WORKTYPE_FIELD, PERMIT_DESCRIPTION_FIELD,
                ]),
                "$where": (
                    f"within_circle({PERMIT_GEOM}, {lat}, {lon}, {PERMIT_SEARCH_RADIUS_M})"
                    f" AND {PERMIT_DATE_FIELD} > '{cutoff}'"
                ),
                "$order": f"{PERMIT_DATE_FIELD} DESC",
                "$limit": "20",
            }
            rows = self._get_json(PERMIT_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"permit lookup failed: {exc}")
            return

        for row in rows:
            number = (row.get(PERMIT_NUMBER_FIELD) or "").strip()
            if not number:
                continue
            date_raw = (row.get(PERMIT_DATE_FIELD) or "").strip()
            ctx.permits.append(PermitRecord(
                permit_number=number,
                issue_date=date_raw[:10] if date_raw else None,
                status=(row.get(PERMIT_STATUS_FIELD) or "").strip() or None,
                work_type=(row.get(PERMIT_WORKTYPE_FIELD) or "").strip() or None,
                description=(row.get(PERMIT_DESCRIPTION_FIELD) or "").strip() or None,
                source="City of Edmonton Development Permits",
                source_url=PERMIT_ENDPOINT,
            ))

    def _populate_heritage(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        try:
            params = {
                "$select": f"{HERITAGE_NAME_FIELD},building_address",
                "$where": f"within_circle({HERITAGE_GEOM}, {lat}, {lon}, {HERITAGE_RADIUS_M})",
                "$limit": "10",
            }
            rows = self._get_json(HERITAGE_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"heritage lookup failed: {exc}")
            return
        for row in rows:
            name = (row.get(HERITAGE_NAME_FIELD) or "").strip()
            if not name:
                continue
            ctx.overlay_flags.append(OverlayFlag(
                category="heritage",
                code=name[:60],
                description=f"Designated historic resource within {HERITAGE_RADIUS_M} m",
                source="City of Edmonton Register and Inventory of Historic Resources",
                source_url=HERITAGE_ENDPOINT,
            ))

    def _populate_flood(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        """Edmonton has no dedicated flood dataset. Flood-risk lands are encoded
        in the same Zoning Overlays dataset that backs _query_overlays, filtered
        to the FP / NSRV / NS10 overlay codes."""
        codes_clause = " OR ".join(f"overlay_code='{code}'" for code in FLOOD_OVERLAY_CODES)
        try:
            params = {
                "$select": "overlay_code,overlay_descr,bylaw_no",
                "$where": (
                    f"intersects(geometry_multipolygon, 'POINT({lon} {lat})')"
                    f" AND ({codes_clause})"
                ),
                "$limit": "5",
            }
            rows = self._get_json(OVERLAYS_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"flood lookup failed: {exc}")
            return
        for row in rows:
            code = (row.get("overlay_code") or "").strip()
            desc = (row.get("overlay_descr") or "").strip() or "Flood-related overlay"
            if not code:
                continue
            ctx.overlay_flags.append(OverlayFlag(
                category="flood",
                code=code,
                description=desc,
                source="City of Edmonton Zoning Overlays (flood)",
                source_url=OVERLAYS_ENDPOINT,
            ))

    def _populate_adjacent_zones(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        try:
            params = {
                "$select": "zoning,description",
                "$where": f"within_circle(geometry_multipolygon, {lat}, {lon}, {NEIGHBOUR_ZONES_RADIUS_M})",
                "$limit": "50",
            }
            rows = self._get_json(ZONES_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"adjacent-zones lookup failed: {exc}")
            return
        counts: dict = {}
        for row in rows:
            code = (row.get("zoning") or "").strip()
            if not code:
                continue
            entry = counts.setdefault(code, {"name": (row.get("description") or "").strip(), "count": 0})
            entry["count"] += 1
        ctx.adjacent_zones = sorted(
            [AdjacentZone(code=c, name=v["name"], count=v["count"]) for c, v in counts.items()],
            key=lambda z: (-z.count, z.code),
        )


def _coerce_float(value) -> Optional[float]:
    """Return value coerced to float, or None for missing/blank/non-numeric."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
