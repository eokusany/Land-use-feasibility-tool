# Option B — Real Per-City Zoning Lookup

## Why this exists

Option A (currently shipped) makes CanLand honest: it identifies the
municipality, links to the bylaw and planning department, and clearly tells
the user that parcel-level zoning must be verified directly with the city.

Option B is the work needed to **actually retrieve parcel-level zoning** for
the cities CanLand supports — replacing the verification callout with a real
zone designation, sourced from each city's open-data API and queried by the
geocoded coordinates of the property.

This document is the implementation plan.

---

## Architecture

Introduce a `ZoningProvider` interface and a registry keyed by municipality.

```python
# zoning_providers/base.py
class ZoningProvider:
    name: str
    municipality: str
    province: str
    source_url: str        # link to the dataset / portal
    last_verified: str     # YYYY-MM-DD — when we last checked the API still works

    def lookup(self, lat: float, lon: float) -> ZoningResult | None:
        ...

@dataclass
class ZoningResult:
    zone_code: str                  # e.g. "RS" or "CMU1"
    zone_name: str                  # human-readable name from the city
    bylaw_section_url: str | None   # deep link into the bylaw if available
    source: str                     # provider name + dataset name
    retrieved_at: str               # ISO timestamp
    raw: dict                       # the original API response, for debugging
```

`PolicyRetrieval.get_land_use_policies` becomes:

1. If a `ZoningProvider` is registered for this municipality AND we have
   coordinates → call `provider.lookup(lat, lon)`.
2. On success → return real zone code, link to source, drop the
   `verification_required` flag (or change it to `verification_recommended`).
3. On failure (no provider, no coords, API error, no polygon hit) → fall back
   to the current Option A behaviour. **Never fabricate.**

The UI should clearly distinguish "verified from city open data" vs
"preliminary template" — different badge colour, different banner text.

---

## Tier 1 cities (start here)

These all expose zoning polygons via public APIs. Listed in priority order
based on population and how clean the API is.

### 1. Edmonton, AB  ⭐ start here (this is the bug-report city)
- Portal: https://data.edmonton.ca
- Dataset: "Zoning (Bylaw 20001)" — ArcGIS REST FeatureServer
- Endpoint pattern: `https://services.arcgis.com/.../FeatureServer/0/query?geometry=<lon>,<lat>&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=json`
- Returns: zone code (e.g. `RS`, `CMU1`, `MU`), zone description, bylaw section
- Note: Edmonton **retired the old R-1/R-2/R-3 system** when Bylaw 20001 took
  effect in January 2024. The hardcoded codes that used to live in
  `policy_retrieval.PROVINCE_ZONING["AB"]` are obsolete for Edmonton.
- Bylaw: https://www.edmonton.ca/city_government/urban_planning_and_design/zoning-bylaw-renewal

### 2. Toronto, ON
- Portal: https://open.toronto.ca
- Dataset: "Zoning By-law" (Zoning By-law 569-2013)
- Endpoint: ArcGIS REST, polygon-by-point query
- Notes: Toronto's zoning is layered (base zone + overlays + exceptions). A
  single point can hit multiple polygons. Return all of them.

### 3. Vancouver, BC
- Portal: https://opendata.vancouver.ca
- Dataset: "Zoning Districts and Labels"
- Endpoint: OpenDataSoft API + downloadable GeoJSON
- Notes: Vancouver also has CD-1 (Comprehensive Development) zones — each one
  is unique and bylaw-text-only. For CD-1 hits, return the CD-1 number and
  link to the by-law search.

### 4. Calgary, AB
- Portal: https://data.calgary.ca
- Dataset: "Land Use Districts" (under Bylaw 1P2007)
- Endpoint: SODA API (Socrata) — supports GeoJSON queries
- Notes: Calgary's "Land Use District" terminology = zone. Codes like `R-C1`,
  `M-CG`, `C-N1`.

### 5. Ottawa, ON
- Portal: https://open.ottawa.ca
- Dataset: "Zoning"
- Endpoint: ArcGIS REST

### 6. Montreal, QC
- Portal: https://donnees.montreal.ca
- Dataset: "Zonage" — but split per borough (arrondissement). Each borough
  publishes its own. Need a borough lookup step first.
- Language: zone descriptions are in French only.

### 7. Winnipeg, MB
- Portal: https://data.winnipeg.ca
- Dataset: "Zoning Districts" (Socrata)

### 8. Halifax, NS
- Portal: https://catalogue-hrm.opendata.arcgis.com
- Dataset: "Zoning" (note: HRM has multiple bylaw areas — Centre Plan,
  Regional MPS, etc.)

---

## Implementation steps

1. **Create the provider interface** (`zoning_providers/base.py`)
2. **Build the Edmonton provider first** (`zoning_providers/edmonton.py`)
   - Hardcode the FeatureServer URL
   - Query by lon/lat, parse the response, return `ZoningResult`
   - Handle: no hit, multiple hits, network timeout, malformed response
   - Add a unit test that mocks the HTTP call with a real captured response
   - Add an integration test gated by `RUN_LIVE_TESTS=1` env var that hits
     the actual API
3. **Wire it into `PolicyRetrieval`**
   - Provider registry: `{municipality_name (lowercased): ProviderClass}`
   - In `get_land_use_policies`, look up provider; on success return real
     data with `verification_required: False` (or `verification_recommended`)
4. **Update the UI** to show "Verified from City of Edmonton open data"
   instead of the verification banner when a provider returns a result
5. **Update the PDF** the same way (different banner colour, source line
   under the zone code)
6. **Repeat for Tier 1 cities** in priority order. Each city is its own PR.

---

## Things NOT to do (lessons from the original bug)

- **Do NOT fabricate setbacks, height, density, or coverage** even if the
  city's API returns the zone code. Those numbers live in the bylaw text and
  vary by overlays, exceptions, site-specific amendments, and discretionary
  variances. Returning the zone code is enough — link to the bylaw section
  and let the user (or a planner) read the requirements that actually apply.
- **Do NOT cache zoning results long-term.** Cities amend zoning bylaws
  frequently (Toronto's amendments run weekly). Cache for at most a few
  hours, and always include the `retrieved_at` timestamp in the report.
- **Do NOT silently fall back to templates** if a provider fails. Surface
  the failure to the user — "Edmonton zoning service unavailable, falling
  back to verification-required mode" — so they know they're not getting
  verified data.
- **Do NOT trust geocoder output blindly.** The original bug also revealed
  that Nominatim mis-resolved `8520 Jasper Ave, 1403` to a west-Edmonton
  location instead of the downtown high-rise. Before calling a zoning API,
  validate the geocode result is inside the municipality's boundary polygon.

---

## Related cleanup (smaller, can be done independently of Option B)

These were noticed during the Option A debug pass and are worth fixing
regardless:

- [ ] `property_parser.py` — `_parse_address` doesn't extract unit numbers
  (e.g. "1403" from `8520 Jasper Ave, 1403`). Add a unit-number group and
  pass it through to the report.
- [ ] `property_parser.py` — `_extract_property_details` substring-matches
  `"residential"` against `additional_info`, which also fires on
  `"non-residential"` and `"presidential"`. Use word-boundary regex.
- [ ] `property_parser.py` — `_extract_municipality_hints` substring-matches
  ALL Canadian city names (thousands) against the input. Words like "Mount"
  or "Lac" will spuriously match many cities. Switch to word-boundary
  matching and/or require province context.
- [ ] `municipality_lookup.py` — `_extract_names` returns any capitalised
  word as a candidate place name. Filter against a stoplist of common
  capitalised non-place words ("Avenue", "Street", "North", etc.).
- [ ] `app.py` — analyze endpoint catches `Exception` and returns the raw
  message in JSON. Sanitize before returning, and log the full trace
  server-side.
- [ ] Geocoder validation — verify the returned point is inside the
  selected municipality's boundary polygon before trusting it.
