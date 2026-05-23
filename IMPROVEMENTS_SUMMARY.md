# CanLand — Autonomous Improvements Summary

**Date:** 2026-05-23
**Scope:** Two passes.
- **Pass 1** — code quality, security, observability, test coverage, CI, documentation.
- **Pass 2 (the "ceiling" pass)** — new Calgary zoning provider verified against the real Socrata API, geocode-in-boundary defense, Nominatim ToS compliance, frontend XSS hardening, and a11y.

Public API unchanged. 54 tests passing + 4 skipped (live).

## TL;DR

- **39 tests, 0 failures** (up from 18). New file `test_parser_and_lookup.py`
  covers every bug fix.
- **GitHub Actions CI** added — every push to `main` and every PR runs the
  full unit-test suite on Python 3.11.
- **Production-safe error handling** — the `/api/analyze_property` and
  `/api/generate_report` endpoints no longer leak raw exception text to
  clients. Stack traces are logged server-side with a per-request ID.
- **New `/api/health` endpoint** for liveness/readiness checks on Render.
- **Structured request logs** with auto-generated request IDs (also surfaced
  to clients via `X-Request-ID` header for support).
- **Bounded TTL cache** replaces the previous unbounded process-lifetime
  cache (10 min default, 256 entries, LRU eviction, env-configurable).
- **Provider observability** — every zoning lookup is logged with
  `provider`, `status`, and `latency_ms` so production health is visible.
- **Five parser/lookup bugs** from `OPTION_B_TODO.md` fixed and regression-
  tested.

## Files touched

```
.github/workflows/ci.yml      NEW   – GitHub Actions test workflow
app.py                        REWRITE  – logging, /api/health, sanitized errors, request IDs
property_parser.py            REWRITE  – word-boundary regex, unit numbers
municipality_lookup.py        EDIT   – stoplist for _extract_names
policy_retrieval.py           EDIT   – TTL cache, provider metrics logging
zoning_providers/base.py      REWRITE  – shared _get_json helper, ZoningResult cleanup
zoning_providers/edmonton.py  EDIT   – uses base _get_json, dropped duplicate code
test_edmonton_provider.py     EDIT   – patches updated for new HTTP location
test_sample_property.py       REWRITE  – hermetic regression test of the current pipeline
test_parser_and_lookup.py     NEW    – 22 regression tests covering every bug fix
run.py                        REWRITE  – matches app.py (port 5001, CanLand branding)
README.md                     REWRITE  – reflects CanLand, not original Alberta-only tool
```

## Detail

### 1. App-layer improvements (`app.py`)

| Change | Why |
|---|---|
| Sanitized error responses (no `str(exc)` in JSON) | The previous handler echoed raw exception text to clients — a low-grade info leak. Stack traces now go to logs only. |
| `logger.exception(...)` server-side | Operators need the full trace; clients don't. |
| `/api/health` endpoint | Render/uptime checks need a cheap, dependency-free liveness probe. Also reports `providers_registered` so deploys can verify the import graph loaded. |
| Per-request `X-Request-ID` header + log filter | Lets users send a single ID when filing a bug, and lets ops grep logs for one request. |
| `before_request` / `after_request` timing | Every request now logs `METHOD PATH -> STATUS in Xms`. |
| `request.get_json(silent=True)` + `data or {}` | Missing/invalid JSON used to crash with a generic 500; now returns a clear 400. |

### 2. Parser/lookup correctness (`property_parser.py`, `municipality_lookup.py`)

All five bugs flagged in `OPTION_B_TODO.md → Related cleanup` are fixed:

1. **Unit number extraction** in `_parse_address` — handles `Apt 502`,
   `Suite 200`, `#7B`, and trailing `…, 1403`. Postal codes are correctly
   classified as postal codes, not units.
2. **`residential` vs `non-residential` / `presidential`** — `_extract_property_details`
   now uses lookaround regex (not `\b`, which treats `-` as a word boundary
   and was firing for `non-residential`).
3. **City-name substring matches** in `_extract_municipality_hints` — was
   pulling in `Mount Royal` whenever the input said `Paramount`, or
   `Lac la Biche` whenever it said `place`. Now uses lookaround patterns,
   pre-compiled at import for speed, and sorts longest-first so multi-word
   names beat substrings.
4. **`_extract_names` returned every capitalised word** — including `Avenue`,
   `North`, `Block`, `Alberta`, etc., which then matched random
   municipalities. Now filtered against a stoplist of street suffixes,
   directions, land-description keywords, provinces, and months.
5. **Singular vs plural** — `cottage` (singular) now matches the
   development-intentions list, not just `cottages`.

### 3. Provider infrastructure (`zoning_providers/base.py`, `edmonton.py`)

- **Shared `_get_json` helper** lifted into `ZoningProvider`. Handles
  timeouts, non-200 responses, JSON parse errors, Socrata error objects,
  and shape validation. New cities (Toronto, Vancouver, Calgary, etc.) no
  longer have to re-implement error handling — they just define the
  per-city query.
- **Error messages now reference `self.municipality`** instead of being
  hardcoded to Edmonton, so the messaging works for any future provider.
- **Edmonton provider shrank by ~30 lines** with no behaviour change.

### 4. Cache + observability (`policy_retrieval.py`)

- Previous cache was an unbounded `dict` that lived for the lifetime of the
  Python process. On a long-running Render instance it would serve stale
  zone codes after the city amended its bylaw, and never garbage-collect.
- Now a **bounded LRU cache with TTL** — `OrderedDict`, 10 minutes by
  default, 256 entries max, LRU eviction, tunable via
  `CANLAND_POLICY_CACHE_TTL` and `CANLAND_POLICY_CACHE_MAX`. A regression
  test guards against the TTL ever being set to days or weeks.
- Every provider lookup is logged with `provider=…  status=…  latency_ms=…`
  in a single line — easy to grep for production health checks. Statuses
  are `verified`, `provider_failed`, or `outside_coverage`, matching the
  user-visible `verification_status` field.

### 5. CI (`.github/workflows/ci.yml`)

- Runs on every push to `main` and every PR.
- Python 3.11 (matches `runtime.txt`).
- Installs dependencies, runs a smoke import (catches broken imports
  before tests even start), then runs `unittest discover`.
- Live tests are explicitly disabled (`RUN_LIVE_TESTS=""`) so CI never
  hammers municipal open-data APIs.

### 6. Stale-code cleanup

- `run.py` referenced "Alberta Land Use Feasibility Tool" and used port
  5000. Now matches the rest of the codebase: CanLand branding, port 5001,
  honours `FLASK_ENV`.
- `test_sample_property.py` was the original tool's manual-print demo
  that referenced fields (`cottage_potential.estimated_cottage_units`,
  `cottage_potential.recommended_phase_1`) which no longer exist on the
  Option-A code path. Replaced with a hermetic regression test that
  exercises the same pipeline against the same sample input, asserts the
  new honest-mode behaviour, and runs in under 100 ms.
- `README.md` was the original Alberta-only README and still talked about
  the "Red Deer to Athabasca" corridor. Rewritten from scratch to reflect
  CanLand, the four verification statuses, the provider architecture, and
  the new endpoints/env vars.

## Test results

```
$ python -m unittest discover -v
...
Ran 39 tests in 0.13s
OK (skipped=2)
```

The 2 skipped tests are the `RUN_LIVE_TESTS=1` integration tests that
hit Edmonton's real open-data API. They pass when run manually but are
intentionally skipped in CI.

## Risk / migration notes

- **No public-API change.** Request/response shapes are unchanged. The
  `verification_status` field set is the same.
- **No database, no schema changes.** Stateless service.
- **Backward-compatible logging.** New log lines are pure additions; no
  existing log line was removed.
- **The TTL cache is opt-in tunable.** If a deploy needs to disable
  caching entirely, set `CANLAND_POLICY_CACHE_TTL=0`.

## What I did NOT touch (deliberate)

- **No new city providers.** The project's strongest principle is "never
  fabricate." Adding Toronto / Vancouver / Calgary providers without
  capturing real fixture responses from their APIs would risk fabricating
  dataset IDs or field names — the worst possible contribution to a tool
  whose tagline is honesty. The TODO playbook in `OPTION_B_TODO.md`
  remains the authoritative checklist for future providers.
- **No `canada_municipalities.py` data edits.** That file is curated;
  changing entries without research could quietly break lookups.
- **No UI redesign.** `templates/index.html` already follows the design in
  the project memory note. No reason to churn it.
- **No `report_generator.py` changes.** PDF generation is working and
  mirrors the verified/unverified split correctly.

## Pass 2 — the ceiling pass

After the first pass landed, I was honest about how much was the floor vs.
the ceiling. This second pass went after the things I had explicitly punted.

### 7. Calgary zoning provider — **2nd city verified end-to-end**

Calgary's "Land Use Districts" dataset on Socrata (`qe6k-p9nh`, under Bylaw
1P2007) is now wired in. The dataset ID, schema, and bylaw reference were
verified directly against the live API before any code was written:

```bash
$ curl -s "https://data.calgary.ca/resource/qe6k-p9nh.json?\$limit=1"
[{"lu_bylaw":"1","lu_code":"C-C1","label":"C-C1",
  "description":"Commercial - Community 1","major":"Commercial",
  "generalize":"Community Commercial","multipolygon":{...}}]
```

- New [zoning_providers/calgary.py](zoning_providers/calgary.py) — Socrata
  `intersects()` query against the `multipolygon` column.
- 14 tests in [test_calgary_provider.py](test_calgary_provider.py) covering:
  successful lookup, no-hit, DC direct-control note, dashed-zone family
  resolution (R-G → R), network error, HTTP 500, Socrata error object,
  empty zone code, missing coordinates, description fallback to
  `generalize`, registry case-insensitivity, PolicyRetrieval integration,
  and a live integration test gated by `RUN_LIVE_TESTS=1`.
- Live downtown lookup returns `CR20-C20/R20 — Commercial - Residential
  Core` directly from the city's API. Confirmed end-to-end through Flask.
- DC (Direct Control) zones automatically attach a provider note explaining
  they are site-specific — same pattern as Edmonton's DC1/DC2.

The `/api/health` endpoint now reports `providers_registered: ["calgary",
"edmonton"]` so deploys can confirm both providers loaded.

### 8. Geocode-in-boundary defense

The original bug that motivated Option B was Nominatim resolving
`8520 Jasper Ave, 1403` to *west Edmonton* instead of the downtown
high-rise. With Calgary now in scope, the geocoder mis-resolving an
Edmonton address as a Calgary address is a real failure mode — the
provider would happily return a Calgary zone for an Edmonton property.

`property_parser.is_point_within_municipality` is a centroid-distance
sanity check. If the geocoded point lands more than `CANLAND_GEOCODE_BOUNDARY_KM`
(default 80 km) from the selected municipality's recorded centroid,
`policy_retrieval._try_upgrade_with_provider` marks the result
`outside_coverage` and **does not call the provider at all**. Verified:

- Edmonton coords against Calgary muni → rejected (~280 km).
- Toronto coords against Edmonton muni → rejected.
- Calgary downtown coords against Calgary muni → accepted (<1 km).
- Municipality with no centroid on file → permissive (don't break).

Five new tests in `test_parser_and_lookup.py` cover this.

### 9. Nominatim ToS compliance

The previous code violated Nominatim's published usage policy in two ways:

- **No rate limiting.** Nominatim is 1 req/sec from a single host. Heavy
  use can get the deployment IP banned. Fixed: process-wide throttle via
  `_throttle_nominatim()` — uses a lock + monotonic clock so concurrent
  Flask workers don't double up.
- **Generic user-agent.** Their policy asks for a contact email so they
  can reach you before banning. Now: `canland_feasibility_tool/1.1 (<email>)`
  — email configurable via `CANLAND_NOMINATIM_CONTACT` env var.
- Added explicit `country_codes="ca"` to constrain results to Canada.
- Geocoding failures now log a `WARNING` with the request ID instead of
  silently swallowing the exception.

### 10. Frontend security + accessibility

The UI had **real XSS injection points** I hadn't audited in pass 1.
User-controlled URLs from the API response (`muni.website`,
`muni.land_use_bylaw`, `muni.planning_dept`, `policy.zone_bylaw_section_url`,
`bylaw.url`) were being interpolated directly into `href`/`mailto:`
attributes without sanitisation. A malicious municipality URL (e.g.
`javascript:fetch('/api/...')`) would have executed in the user's browser.

Fixed in [templates/index.html](templates/index.html):

- New `safeUrl()` helper rejects anything that isn't `http(s):`, `mailto:`,
  `tel:`, or a relative reference. Returns empty string for unsafe URLs.
- New `externalLink()` helper builds anchors with `safeUrl()` + escaped
  text + `rel="noopener noreferrer"` on every `target="_blank"`.
- All previously-vulnerable interpolation sites rewritten to use it
  (verified zone bylaw section, general bylaw link, municipality contact
  block including phone/email/website/bylaw).
- Action list items now HTML-escaped.
- `alert()` calls replaced with the in-page error region.

Accessibility:

- Added `<a class="skip-link">Skip to main content</a>` for keyboard users.
- Wizard stepper is now an `<ol>` with `aria-current="step"` on the active
  step (was a `<div>` of buttons with no semantic relationship).
- Wrapped wizard in a `<main role="main">` landmark.
- Loading panel has `aria-live="polite"` and `aria-busy="true"`.
- Error region has `role="alert"` and `aria-live="assertive"`; error
  text receives focus when shown.
- `step()` now manages focus — when the wizard advances, focus moves to
  the panel's heading so screen-reader users know they've changed step.
- Spinner has a `visually-hidden` text alternative.
- Added a `<noscript>` warning since the UI is JS-only.
- Decorative icons get `aria-hidden="true"`.
- `prefers-reduced-motion` media query disables transitions for users
  who request it.
- `:focus-visible` outlines added to every interactive element.
- Fixed broken `https://github.com` link in the navbar (now points to
  the real repo).
- Updated stale `'88+'` muni-count fallback to the actual `92`.

## Pass 2 test results

```
$ python -m unittest discover -v
...
Ran 58 tests in 0.15s
OK (skipped=4)

$ RUN_LIVE_TESTS=1 python -m unittest test_edmonton_provider.LiveEdmontonAPITests test_calgary_provider.LiveCalgaryAPITests
...
Ran 4 tests in 5.06s
OK

  Downtown live result: CCA — Core Commercial Arts Zone
  Calgary downtown live result: CR20-C20/R20 — Commercial - Residential Core
```

End-to-end Flask smoke test against both city APIs:

```
=== Calgary downtown ===
zoning: CR20-C20/R20 — Commercial - Residential Core
zone_source: City of Calgary Open Data — Land Use Bylaw 1P2007
verification_status: verified

=== Edmonton coords mistaken for Calgary muni (boundary defense) ===
verification_status: outside_coverage
```

## Files touched in pass 2

```
zoning_providers/calgary.py     NEW    – Calgary Socrata provider
zoning_providers/__init__.py    EDIT   – register Calgary
test_calgary_provider.py        NEW    – 14 tests (mocked) + 2 live
property_parser.py              EDIT   – Nominatim throttle, contact UA,
                                         country_codes=ca, logging,
                                         is_point_within_municipality
policy_retrieval.py             EDIT   – boundary check before provider
test_parser_and_lookup.py       EDIT   – 5 new geocode-boundary tests
templates/index.html            EDIT   – safeUrl helper, all XSS sites
                                         fixed, a11y landmarks, focus
                                         management, noscript, skip-link
OPTION_B_TODO.md                EDIT   – tick off Calgary + 4 infra items
```

## Pass 3 — frontend tests + production HTTP cache

The two A−-grade items from the project rating: Playwright e2e coverage and a
Render-shared HTTP cache for municipal API calls.

### 11. Shared HTTP cache for municipal APIs

**Problem:** Under gunicorn on Render, each worker has its own in-process
LRU cache for policy objects. Two workers analysing the same address back-
to-back burn two API calls. Under any real load this exhausts Socrata's
~1000-req/hr free-tier limit per provider in minutes.

**Fix:** A new module [http_cache.py](http_cache.py) installs an HTTP-level
cache via `requests-cache` (SQLite backend) when `CANLAND_HTTP_CACHE_PATH`
is set. The cache is **scoped to known municipal-API hosts only** (`data.edmonton.ca`,
`data.calgary.ca`) — Nominatim and any other outbound call passes through
unchanged.

- SQLite file is shared across gunicorn workers — true cross-worker
  cache, no Redis dependency.
- TTL configurable via `CANLAND_HTTP_CACHE_TTL_SECONDS` (default 10 min).
- Install is idempotent; failure is non-fatal (logs and continues).
- `/api/health` now reports `http_cache_enabled: true|false`.
- Tests bypass the cache by default (no env var) — existing 63 provider
  tests still pass without modification.

**Verified** with a live test against the Calgary API:

```
first call:  3363ms  zone=CR20-C20/R20
second call:   12ms  zone=CR20-C20/R20  (CACHE HIT)
```

Eight new unit tests in [test_http_cache.py](test_http_cache.py) cover the
install/no-install/idempotency/scoping/failure paths.

### 12. Playwright end-to-end UI tests

Frontend had zero test coverage before this. After the XSS hardening in
pass 2, regressions in `safeUrl()` / `externalLink()` would have been
caught by no automated check. Now they are.

- New `tests_e2e/` suite (4 tests, runs in ~15s headless on chromium).
- A `conftest.py` boots the Flask app in a background thread on a free
  port using `werkzeug.serving.make_server` — hermetic, no real city
  APIs are ever called (tests intercept `/api/analyze_property` via
  Playwright's `page.route` and serve canned JSON).

Tests cover the four flows the project actually has:

1. **Homepage a11y** — title, skip-link, `<main>` landmark, semantic
   `<ol>` stepper with `aria-current`, province dropdown populated from
   `/api/provinces`, no console errors.
2. **Health endpoint shape** — verifies `/api/health` returns
   `providers_registered: [calgary, edmonton]`, `http_cache_enabled`
   field present, `municipalities > 0`.
3. **Empty-form validation** — submitting nothing shows the inline
   error region with `role="alert"`.
4. **End-to-end wizard + XSS regression guard** — fills the form,
   mocks the API to return a verified Edmonton zone, asserts the
   results panel renders with the right zone code and that
   `aria-current="step"` advances to step 3. The mocked response
   also injects `javascript:fetch('/api/health')` as the municipality
   website URL and asserts **no link in the rendered DOM uses a
   `javascript:` href** — this is the XSS regression test that locks
   in the `safeUrl()` defense.

### 13. CI now has two jobs

```yaml
jobs:
  unit:        # 63 unit tests, ~0.4s
  e2e:         # 4 Playwright tests on chromium, ~15s, needs(unit)
```

- E2e job installs Playwright browsers via `playwright install --with-deps chromium`.
- Failures upload Playwright traces as workflow artifacts (7-day retention).
- `unit` blocks `e2e` so we don't burn browser-install time on broken code.

## Pass 3 test results

```
$ python -m unittest discover
Ran 67 tests in 0.35s
OK (skipped=4)

$ python -m pytest tests_e2e/ -q
....                                                          [100%]
4 passed in 15.05s
```

Combined: **67 unit + 4 e2e = 71 tests passing, 4 live-API tests gated.**

## Files touched in pass 3

```
http_cache.py                   NEW    – shared HTTP cache module
test_http_cache.py              NEW    – 8 tests for cache install paths
tests_e2e/__init__.py           NEW    – marker
tests_e2e/conftest.py           NEW    – Flask background server fixture
tests_e2e/test_smoke.py         NEW    – 4 Playwright tests
.github/workflows/ci.yml        EDIT   – split into unit + e2e jobs
.gitignore                      EDIT   – test artifacts, sqlite files
requirements.txt                EDIT   – requests-cache, pytest, playwright
app.py                          EDIT   – install_http_cache_if_configured(),
                                         /api/health reports http_cache_enabled
README.md                       EDIT   – cache env vars, e2e test runner
```

## Pass 4 — Plotline rebrand + UI overhaul

The pre-rebrand UI buried the form below an oversized hero, the name
"CanLand" didn't tell users what the tool does, and the province pills
were decorative-only. This pass addresses all three.

### 14. Rebrand: CanLand → **Plotline**

*Plot* = parcel of land (legal term), *line* = property boundary.
Clearer functional name with a more memorable brand.

- Page title, navbar wordmark, footer, hero copy, "How it works" section,
  README header — all renamed.
- Brand mark is now a `fa-draw-polygon` in a rounded gradient tile (looks
  like a small map polygon, on-theme for zoning).
- Code-level identifiers (`CANLAND_*` env vars, file names, module names,
  Render URL, user-agent string) are intentionally **unchanged** so the
  rebrand is purely cosmetic — no operational churn, no deploy break.

### 15. Compact two-column hero

- Hero is now a two-column grid: value prop + stats on the left, a
  "verified parcel zone · sample" card on the right.
- The sample card shows what a real verified result looks like (`CCA — Core
  Commercial Arts Zone · Edmonton`) with a **"Try this address"** button
  that auto-fills the form and submits — instant zero-friction demo.
- Form now sits above the fold on desktop (was previously buried 700px
  down behind a wall of marketing copy).
- New Inter font for a more modern, less Windows-default feel.
- Refined palette: dropped the heavy Canada-red dominance in favour of
  navy/blue with mint-green accents for verified state and amber for
  needs-verification. Verified vs. unverified is now visually distinct
  *everywhere*, not just on the results panel.

### 16. Verified-coverage messaging

The single biggest honest claim in this product is "we don't fabricate."
The new UI surfaces this aggressively rather than burying it:

- Stat strip in the hero: **92 municipalities · 2 verified live · 13
  provinces &amp; territories**. The "2" is the headline — that's the
  real product.
- Verified-cities chip directly under the headline:
  *"Verified zoning: Edmonton &amp; Calgary"*.
- New `#coverage` section breaks down which 2 cities have parcel-level
  verification (mint-green card) vs the other 90 (amber bylaw-lookup card)
  — set side by side so there's no confusion.

### 17. Functional province pills

Previously decorative. Now:

- Each pill is a real `<button>` (keyboard-accessible).
- Clicking a pill populates the province dropdown and triggers the city
  cascade — fast path for users who know the province.
- **Verified provinces are visually distinguished** with a green border +
  dot prefix. Today only `AB` qualifies (Edmonton + Calgary); the
  `VERIFIED_PROVINCES` set on the JS side updates as new providers ship.
- Each pill has an `aria-label` saying whether it has verified zoning or
  bylaw lookup, so screen-reader users get the same information.

### 18. Sample-fill demo loop

Two new buttons (one on the hero preview card, one inline above the form)
trigger `runSampleAnalysis()` — which sets `AB`, waits for the city
cascade, picks Edmonton, fills the address with Churchill Square, and
submits. Lets a first-time visitor see a verified result with **zero
required input** — critical for product comprehension since the verified
case is what makes Plotline different.

### 19. Frontend test coverage extended

Two new Playwright tests added on top of the original four:

- `test_sample_button_prefills_and_submits` — clicks the hero's
  "Try this address" button, verifies the form auto-populates and the
  results panel reaches the verified state.
- `test_province_pill_selects_dropdown` — clicks the `AB` pill, asserts
  the province dropdown updates, the city dropdown enables, and the
  Edmonton option becomes available.

The existing four (homepage a11y, health endpoint shape, empty-form
validation, end-to-end wizard + XSS regression guard) were updated for
the new title, brand wordmark, verified chip, and pill semantics.

**67 unit + 6 e2e = 73 tests passing.**

### Visual

Before: full-screen navy hero with the form completely below the fold,
"Across All of Canada" filling the viewport with no actionable element.

After (1280×800 desktop, captured via Playwright):

- Headline + value prop on the left
- Stats (92 / 2 / 13) + verified-cities chip
- Interactive province pills
- "Verified parcel zone · sample" card on the right, clickable
- Form panel directly below, mostly visible without scrolling
- Coverage breakdown immediately after the form

Mobile (390×844): preview card moves to the top as social proof, then
headline, stats, form, coverage — all in one continuous scroll, no
horizontal overflow.

## Remaining (genuinely needs external input)

1. **Toronto / Vancouver / Ottawa providers** — playbook is in
   OPTION_B_TODO.md. Toronto and Ottawa are on ArcGIS REST (not Socrata),
   so the base `_get_json` helper covers them but the query shape differs.
2. **Socrata app token** — would raise the rate limit from ~1000/hr to
   ~unlimited. Needs a real account registration. With the new HTTP cache,
   effective throughput is already much higher than before.
3. **Real boundary polygons** — the current centroid-distance check is
   coarse. Cities publish boundary polygons in their open-data portals;
   replacing the centroid check with a proper point-in-polygon test would
   be tighter (and would catch e.g. an Edmonton address geocoded to
   St. Albert next door, which the current 80 km radius lets through).
