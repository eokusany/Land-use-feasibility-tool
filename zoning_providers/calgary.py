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

from .aerial import build_static_aerial
from .base import ProviderError, ZoningProvider, ZoningResult
from .parcel_context import (
    AdjacentZone,
    LotCharacteristics,
    OverlayFlag,
    ParcelContext,
    PermitRecord,
)


# Public Socrata endpoint — no auth required for read-only queries.
ZONES_ENDPOINT = "https://data.calgary.ca/resource/qe6k-p9nh.json"
DATASET_URL = "https://data.calgary.ca/Base-Maps/Land-Use-Districts-Map/qe6k-p9nh"

# Tier 1 parcel-context endpoints — verified against data.calgary.ca on
# 2026-05-24. See tests/fixtures/README.md for the field-name source of truth.

# Calgary parcel — polygonised Current Year Property Assessments.
# Has area (land_size_sm) but no perimeter, so frontage/depth stay None.
PARCEL_ENDPOINT = "https://data.calgary.ca/resource/4bsw-nn7w.json"
PARCEL_GEOM = "multipolygon"
PARCEL_AREA_FIELD = "land_size_sm"

# Calgary Development Permits — point dataset, applieddate-driven.
PERMIT_ENDPOINT = "https://data.calgary.ca/resource/6933-unw5.json"
PERMIT_GEOM = "point"
PERMIT_NUMBER_FIELD = "permitnum"
PERMIT_DATE_FIELD = "applieddate"
PERMIT_STATUS_FIELD = "statuscurrent"
PERMIT_WORKTYPE_FIELD = "proposedusedescription"
PERMIT_DESCRIPTION_FIELD = "description"
PERMIT_SEARCH_RADIUS_M = 50
PERMIT_LOOKBACK_YEARS = 5

# Calgary heritage — Historic Resource point dataset.
HERITAGE_ENDPOINT = "https://data.calgary.ca/resource/99yf-6c5u.json"
HERITAGE_GEOM = "point"
HERITAGE_NAME_FIELD = "name"
HERITAGE_RADIUS_M = 25

# Calgary flood — Regulatory Flood Map polygons.
FLOOD_ENDPOINT = "https://data.calgary.ca/resource/tp6q-x2v7.json"
FLOOD_GEOM = "multipolygon"
FLOOD_TYPE_FIELD = "description"

# Neighbour zones radius — 250 m. 100 m is too tight (City Hall is interior to a
# single DC polygon), 500 m drifts into adjacent neighbourhoods. 250 m is the
# middle path. Both the zones dataset (qe6k-p9nh) and the parcel dataset
# (4bsw-nn7w) happen to use the same geometry column name (`multipolygon`),
# but they are independent datasets — keep the literal here for clarity.
NEIGHBOUR_ZONES_RADIUS_M = 250
NEIGHBOUR_ZONES_GEOM = "multipolygon"


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

    def context(self, lat: float, lon: float) -> Optional[ParcelContext]:
        """Return Tier 1 parcel context. Never raises — per-feature failures
        are recorded in `ParcelContext.warnings`. Call order is fixed because
        tests/test_calgary_context.py mocks responses in this order."""
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
        """Find the parcel polygon under the coordinate. Calgary has parcel
        polygons (unlike Edmonton's point dataset), so `intersects` works
        directly. land_size_sm is area in m²; perimeter is not exposed so
        frontage/depth stay None."""
        try:
            params = {
                "$select": ",".join([
                    "roll_number", "address", PARCEL_AREA_FIELD,
                    "land_use_designation", "year_of_construction",
                ]),
                "$where": f"intersects({PARCEL_GEOM}, 'POINT({lon} {lat})')",
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
            frontage_m=None,   # Calgary parcel dataset has no perimeter
            depth_m=None,
            orientation_deg=None,
            source="City of Calgary Property Assessments (Parcel)",
            source_url=PARCEL_ENDPOINT,
        )

    def _populate_permits(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        """Last 5 years of Development Permits at the coordinate."""
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
                source="City of Calgary Development Permits",
                source_url=PERMIT_ENDPOINT,
            ))

    def _populate_heritage(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        try:
            params = {
                "$select": f"{HERITAGE_NAME_FIELD},address",
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
                description=f"Historic resource within {HERITAGE_RADIUS_M} m",
                source="City of Calgary Historic Resource Inventory",
                source_url=HERITAGE_ENDPOINT,
            ))

    def _populate_flood(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        try:
            params = {
                "$select": f"{FLOOD_TYPE_FIELD},flood_cd",
                "$where": f"intersects({FLOOD_GEOM}, 'POINT({lon} {lat})')",
                "$limit": "5",
            }
            rows = self._get_json(FLOOD_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"flood lookup failed: {exc}")
            return
        for row in rows:
            hazard = (row.get(FLOOD_TYPE_FIELD) or "").strip() or "Flood-related polygon"
            ctx.overlay_flags.append(OverlayFlag(
                category="flood",
                code=hazard[:60],
                description=hazard,
                source="City of Calgary Regulatory Flood Map",
                source_url=FLOOD_ENDPOINT,
            ))

    def _populate_adjacent_zones(self, ctx: ParcelContext, lat: float, lon: float) -> None:
        try:
            params = {
                "$select": "lu_code,description",
                "$where": (
                    f"within_circle({NEIGHBOUR_ZONES_GEOM}, "
                    f"{lat}, {lon}, {NEIGHBOUR_ZONES_RADIUS_M})"
                ),
                "$limit": "50",
            }
            rows = self._get_json(ZONES_ENDPOINT, params)
        except ProviderError as exc:
            ctx.warnings.append(f"adjacent-zones lookup failed: {exc}")
            return
        counts: dict = {}
        for row in rows:
            code = (row.get("lu_code") or "").strip()
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
