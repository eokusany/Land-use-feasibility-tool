# Option B — Real Per-City Zoning Lookup

## Status

- [x] **Edmonton** — shipped 2026-04-08, commit `a3a9aac` (see [SUMMARY.md](SUMMARY.md))
- [x] **Calgary** — shipped 2026-05-23 (see [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md))
- [ ] Toronto, Vancouver, Ottawa, Montreal, Winnipeg, Halifax — pending
- [x] **Shared `_get_json` helper** — shipped 2026-05-23 (lifted to `ZoningProvider.base`)
- [x] **TTL cache** — shipped 2026-05-23 (10 min default, 256 entries, env-tunable)
- [x] **Geocode-in-boundary check** — shipped 2026-05-23 (centroid-distance, 80 km default)
- [x] **Metrics / observability** — shipped 2026-05-23 (provider/status/latency logged)
- [ ] **Rate limiting / Socrata app tokens** — still pending (requires real token)

**Current rollout plan:** collect real user feedback on the Edmonton
deployment first. Only scale to the next Tier 1 city once we've validated
the verified-zone UX, the overlay display, and the DC1/DC2 note pattern
with at least a handful of real Edmonton users.

## Why this exists

Option A (shipped for every city except Edmonton) makes CanLand honest: it
identifies the municipality, links to the bylaw and planning department, and
clearly tells the user that parcel-level zoning must be verified directly
with the city.

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

## Canada-wide scale plan

The Edmonton provider is the reference implementation for every other city.
The pattern to follow for each new city:

1. Find the city's open-data portal and locate the zoning dataset. Prefer
   Socrata → ArcGIS REST → OpenDataSoft → downloadable GeoJSON, in that order
   (Socrata's SoQL `intersects()` is the cleanest point-in-polygon query).
2. Capture a real API response for at least one known downtown address and
   save it as mocked test fixtures (matches `ZONE_HIT` / `OVERLAYS_HIT` in
   [test_edmonton_provider.py](test_edmonton_provider.py)).
3. Implement `zoning_providers/<city>.py` subclassing `ZoningProvider`.
   Mirror the Edmonton structure: `_query_zone` / `_query_overlays` /
   `_get_json`, raising `ProviderError` on network or shape failures,
   returning `None` on no-polygon-hit.
4. Add site-specific notes for any zones that don't have generic rules
   (Vancouver CD-1, Toronto site-specific exceptions, etc.).
5. Register the class in [zoning_providers/__init__.py](zoning_providers/__init__.py).
   Use the exact municipality name CanLand resolves (not raw user input).
6. Write tests in `test_<city>_provider.py`: successful lookup, no-hit,
   malformed response, HTTP error, network error, missing coordinates, and
   a `RUN_LIVE_TESTS`-gated live integration test.
7. Verify against the live API before merging.
8. Ship one city per PR. Do not batch.

### Provider-layer improvements (apply before Toronto)

Lessons from the Edmonton rollout that should become shared infrastructure
in [zoning_providers/base.py](zoning_providers/base.py) rather than copy-pasted
into each new provider:

- [ ] **Shared HTTP helper** — the `_get_json` method in the Edmonton provider
  handles timeouts, non-200s, JSON errors, Socrata error objects, and shape
  validation. Lift it to `ZoningProvider._get_json` so Toronto/Vancouver don't
  reimplement error handling.
- [ ] **Per-request cache** — the `PolicyRetrieval.policy_cache` is unbounded
  and lives for the life of the Python process. On a long-running Render
  instance this could serve a cached zone after the city amends it. Add a
  TTL (30 min max) or move caching to per-request only.
- [ ] **Geocode-in-boundary check** — the original bug was partly a geocoder
  failure (Nominatim resolved a downtown address to west Edmonton). Before
  calling any provider, verify the geocoded point is inside the selected
  municipality's boundary polygon. Otherwise provider returns `None`
  (outside_coverage) and users think the address isn't in the city.
- [ ] **Metrics / observability** — log (provider_name, status, latency_ms)
  for every lookup so we can see in production which cities are healthy,
  which are timing out, and how often we're falling back to Option A.
- [ ] **Rate limiting** — Socrata's default limit is ~1000 req/hr without an
  app token. With real user traffic across Tier 1 cities we'll hit that. Add
  per-provider app tokens via env vars and document in SUMMARY.md.

## Tier 1 cities

These all expose zoning polygons via public APIs. Listed in priority order
based on population and how clean the API is.

### 1. Edmonton, AB  ✅ SHIPPED 2026-04-08 (commit `a3a9aac`)
- Portal: https://data.edmonton.ca
- Dataset: "Zoning Bylaw Geographical Data" (fixa-tstc) + "Zoning Overlays" (6w3s-58pv)
- Socrata SoQL `intersects()` point-in-polygon query
- Implementation: [zoning_providers/edmonton.py](zoning_providers/edmonton.py)
- Tests: [test_edmonton_provider.py](test_edmonton_provider.py) — 18 tests
- Bylaw 20001 (effective January 2024) retired the old R-1/R-2/R-3 system
- DC1/DC2 site-specific zones get provider notes

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

## Tier 2+ cities (after Tier 1 is complete)

Once the Tier 1 cities are all shipped, broaden coverage to mid-size cities
that have decent open-data portals:

- Mississauga, Brampton, Hamilton, Surrey, Burnaby, Richmond, Markham,
  Vaughan, Kitchener, London, Windsor, Victoria, Saskatoon, Regina,
  Quebec City, Laval, Gatineau, Longueuil, St. John's, Charlottetown

For each, the playbook is identical to the Tier 1 rollout above. Skip any
city whose zoning data isn't published (fall back to Option A permanently).

## Long tail (Option A forever)

For the remaining ~70 cities in `canada_municipalities.py` that don't
publish zoning as open data, CanLand stays in Option A mode indefinitely.
The honest verification-required banner is the correct answer — we don't
need a provider for every municipality.

## Feedback loop for real users

Before scaling past Edmonton, collect feedback on these questions from
Edmonton users:

- [ ] Is the "Verified" badge and source attribution clear enough that users
  trust the zone code?
- [ ] Is the overlays list understandable, or does it need an explainer?
- [ ] Do DC1/DC2 provider notes prevent users from assuming generic rules?
- [ ] What do users actually do next after seeing a verified zone — do they
  click the bylaw section link? Do they contact the planning department?
- [ ] How often does `provider_failed` / `outside_coverage` fire in the wild,
  and is the messaging helpful when it does?

Decisions informed by that feedback should be applied to the shared provider
layer (see "Provider-layer improvements" above) before Toronto goes in.

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
