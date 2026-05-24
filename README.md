# Plotline — Canadian zoning lookup &amp; feasibility

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/eokusany/Land-use-feasibility-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/eokusany/Land-use-feasibility-tool/actions/workflows/ci.yml)

Plotline (formerly *CanLand*) is a web application that helps developers,
planners, and property investors assess feasibility for properties anywhere
in Canada. It covers **92 municipalities across all 13 provinces and
territories** and is designed around a single principle: **never fabricate
zoning data.**

**Verified parcel-level zoning** is available for Edmonton and Calgary today,
pulled live from each city's open-data API. For the other 90 municipalities,
Plotline identifies the bylaw and planning department and tells the user
exactly what to verify — no guessed zone codes.

Live: <https://land-use-feasibility-tool.onrender.com>

## What it does

For any Canadian property, CanLand returns:

- The relevant municipality, province, and planning department contact info
- A link to the municipality's land use bylaw (when known)
- Province-aware development requirements (building code + planning act)
- A prominent verification banner telling the user what still needs to be
  confirmed with the city

For supported cities (currently **Edmonton**), CanLand additionally returns:

- The parcel-level zone code, verified from the city's open-data API
- Overlays that apply on top of the base zone
- A deep link into the bylaw section governing that specific zone
- Provider notes for site-specific zones (DC1/DC2 in Edmonton, CD-1 in
  Vancouver, etc.) where there is no generic rule set
- **Parcel context (Edmonton + Calgary):** Lot area, adjacent zones, recent permits, heritage and flood flags, plus a satellite snapshot of the parcel.

Setbacks, height limits, density, and permitted uses are never fabricated —
even with a verified zone code, those live in bylaw text. CanLand sends the
user to the bylaw section rather than guess.

## Architecture

```
app.py                       Flask routes + structured logging + request IDs
property_parser.py           Parse address, legal description, extract hints
canada_municipalities.py     92 municipalities across 13 provinces/territories
municipality_lookup.py       Name/coordinate-based municipality matching
policy_retrieval.py          Province-aware policy + provider integration
                             + bounded TTL cache + observability
zoning_providers/
    base.py                  ZoningProvider ABC + shared _get_json helper
    edmonton.py              Socrata-backed Edmonton provider (Bylaw 20001)
    __init__.py              Registry keyed by lowercased municipality name
report_generator.py          PDF feasibility report
templates/index.html         Bootstrap 5 + Leaflet UI
```

### Verification statuses

`policy_info["verification_status"]` is one of:

| Status              | Meaning                                                              |
|---------------------|----------------------------------------------------------------------|
| `unverified`        | No provider for this city. Option A mode — verify with planning dept.|
| `verified`          | Provider returned a parcel-level zone code from the city's API.      |
| `provider_failed`   | Provider exists but the API was unreachable or returned bad data.    |
| `outside_coverage`  | The geocoded point fell outside any zoning polygon for that city.    |

The UI and PDF surface these explicitly so users never confuse "verified" with
"preliminary".

## Quick start

### Prerequisites
- Python 3.11
- pip

### Install

```bash
git clone https://github.com/eokusany/Land-use-feasibility-tool.git
cd Land-use-feasibility-tool
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally

```bash
python app.py                       # http://localhost:5001
```

Or via the convenience launcher:

```bash
python run.py
```

### Health check

```bash
curl http://localhost:5001/api/health
```

### Run tests

```bash
# Backend unit tests (mocked, ~0.4s) — runs against production deps only
python -m unittest discover -v

# Backend with live municipal-API integration tests
RUN_LIVE_TESTS=1 python -m unittest test_edmonton_provider.py test_calgary_provider.py

# Playwright end-to-end UI tests — requires dev deps (pytest, playwright)
pip install -r requirements-dev.txt
python -m playwright install chromium     # one-time
python -m pytest tests_e2e/ -v
```

### Dependencies

| File                    | Purpose                                      |
|-------------------------|----------------------------------------------|
| `requirements.txt`      | Production deps — Render installs only this. |
| `requirements-dev.txt`  | Adds pytest + Playwright for local/CI e2e.   |
| `.python-version`       | Pins Render to Python 3.11.0.                |

## API

### `GET /api/health`
Liveness/readiness check. Returns the registered zoning providers and
municipality count so deploys can confirm the import graph loaded cleanly.

### `GET /api/provinces`
List of supported provinces and territories with city counts.

### `GET /api/cities/<province_code>`
Cities for a given province (e.g. `AB`, `BC`, `ON`).

### `POST /api/analyze_property`
```json
{
  "address": "1 Sir Winston Churchill Sq",
  "legal_description": "",
  "additional_info": "",
  "province": "AB",
  "city": "Edmonton"
}
```

Returns property info, municipality info, policy info (with
`verification_status`), and a feasibility summary.

### `POST /api/generate_report`
Generates a PDF feasibility report. Body is the JSON returned by
`/api/analyze_property`.

### `GET /api/municipalities`
Full list of supported municipalities.

## Configuration

Environment variables:

| Variable                          | Default      | Purpose                                                  |
|-----------------------------------|--------------|----------------------------------------------------------|
| `PORT`                            | `5001`       | HTTP listen port                                         |
| `FLASK_ENV`                       | `development`| `production` disables debug mode                         |
| `CANLAND_LOG_LEVEL`               | `INFO`       | Root logger level                                        |
| `CANLAND_POLICY_CACHE_TTL`        | `600`        | In-process LRU cache TTL (seconds) for policy objects    |
| `CANLAND_POLICY_CACHE_MAX`        | `256`        | Max policy-cache entries (LRU eviction)                  |
| `CANLAND_HTTP_CACHE_PATH`         | *unset*      | SQLite path to enable shared HTTP cache across workers   |
| `CANLAND_HTTP_CACHE_TTL_SECONDS`  | `600`        | HTTP cache TTL for municipal-API responses               |
| `CANLAND_GEOCODE_BOUNDARY_KM`     | `80`         | Max distance from muni centroid before geocode rejected  |
| `CANLAND_NOMINATIM_CONTACT`       | `canland@example.com` | Email in Nominatim User-Agent (per their ToS)   |
| `PLOTLINE_MAPBOX_TOKEN`           | *unset*      | Optional. Public Mapbox token (`pk.…`). When set, verified Edmonton and Calgary reports include a static aerial image of the parcel in the UI and the data payload. Sign up at https://account.mapbox.com/ — free tier covers Plotline's current volume. |
| `RUN_LIVE_TESTS`                  | *unset*      | When `1`, live-API tests run                             |

### HTTP cache (production)

Under gunicorn on Render, each worker has its own in-process LRU cache for
policy objects. Set `CANLAND_HTTP_CACHE_PATH=/tmp/canland_cache` to add a
shared **SQLite-backed HTTP cache** that all workers see — so two workers
analyzing the same address back-to-back only hit the city's API once. The
cache is **scoped to known municipal-API hosts only** (`data.edmonton.ca`,
`data.calgary.ca`); Nominatim and any other outbound call is never cached.

The `/api/health` endpoint reports `http_cache_enabled: true|false` so
operators can confirm the cache is active in production.

## Adding a city provider

The Edmonton provider is the reference implementation. To add a new city:

1. Find the city's open-data zoning endpoint (Socrata, ArcGIS REST, etc.).
2. Capture a real API response for a known downtown address and save it as
   mocked test fixtures.
3. Implement `zoning_providers/<city>.py` subclassing `ZoningProvider`. The
   base class provides `_get_json`, so providers only define `lookup` and the
   per-city query shape.
4. Register the class in `zoning_providers/__init__.py`.
5. Write tests in `test_<city>_provider.py` covering: success, no-hit,
   malformed response, HTTP error, network error, missing coordinates, and a
   `RUN_LIVE_TESTS`-gated integration test.
6. Ship one city per PR. Do not batch.

See [OPTION_B_TODO.md](OPTION_B_TODO.md) for the full Tier 1 roadmap.

## Disclaimers

CanLand is a preliminary feasibility tool. It does not replace municipal
planning advice, legal advice, or engineering due diligence. Always confirm
with the relevant municipality before relying on any output. Bylaws change
frequently and the tool intentionally does not cache results long-term.

## License

MIT — see [LICENSE](LICENSE).
