# CanLand — Progress Summary

## Where we are

CanLand is live at https://land-use-feasibility-tool.onrender.com with
Edmonton as the first city running **Option B** (real parcel-level zoning
lookup from the municipality's open data). Every other Canadian city still
runs in **Option A** (honest verification-required mode): CanLand identifies
the municipality and links to the bylaw, and tells the user to verify the
zone with the planning department.

## Option A — shipped (all cities)

Lives in [policy_retrieval.py](policy_retrieval.py). For any property CanLand
returns:

- Municipality name, province, planning contact info
- A link to that municipality's land use bylaw (when known)
- Province-aware development requirements (building code + planning act)
- A prominent "verification required" banner + verification steps
- **No fabricated** zone codes, setbacks, heights, density, or permitted uses

This replaced the original broken behaviour where every address was given
confidently-wrong values like "R-1 Single Family Residential" from a hardcoded
template, regardless of where the parcel actually was.

## Option B — shipped (Edmonton only)

### Architecture

- [zoning_providers/base.py](zoning_providers/base.py) — `ZoningProvider` ABC,
  `ZoningResult`, `ZoningOverlay`, `ProviderError`
- [zoning_providers/__init__.py](zoning_providers/__init__.py) — registry
  keyed by lowercased municipality name
- [zoning_providers/edmonton.py](zoning_providers/edmonton.py) — Socrata
  queries against `fixa-tstc` (base zones) + `6w3s-58pv` (overlays), with
  DC1/DC2 site-specific explanatory notes
- [policy_retrieval.py](policy_retrieval.py) — `_try_upgrade_with_provider`
  exposes 4 verification statuses: `unverified` / `verified` /
  `provider_failed` / `outside_coverage`
- [templates/index.html](templates/index.html) — verified-zone block with
  source attribution, overlays list, provider notes
- [report_generator.py](report_generator.py) — PDF mirrors the verified state
- [test_edmonton_provider.py](test_edmonton_provider.py) — 16 mocked unit +
  integration tests, 2 live tests gated by `RUN_LIVE_TESTS=1`

### Principles baked into the provider layer

1. **Never fabricate.** Provider returns only what the city's API actually
   says — zone code, zone name, bylaw section URL, overlays. Setbacks,
   height, density, and permitted uses remain empty even on a verified hit;
   the user is sent to the bylaw section for authoritative text.
2. **Fail loudly, not silently.** Network/API failures surface as
   `provider_failed` in the UI with the error message, so users know they're
   not seeing verified data. The app never silently degrades from "verified"
   to "template" without telling the user.
3. **No long-term caching.** Zoning bylaws amend frequently. In-memory cache
   per request only, timestamped `retrieved_at` on every result.
4. **Site-specific zones get notes.** DC1/DC2 zones in Edmonton don't have
   generic rules — the bylaw section IS the rule. Provider flags these with
   an explanatory note so users don't read a zone code and assume standard
   setbacks apply.

### Verification

- All 18 tests pass (unittest, ~7ms for mocked, ~2s for live)
- Live API verified against Churchill Square (53.5444, -113.4909) → returns
  `CCA — Core Commercial Arts Zone` ✓
- Deployed as commit `a3a9aac` on `main`

## What's next

See [OPTION_B_TODO.md](OPTION_B_TODO.md) for the Tier 1 rollout across the
remaining cities (Toronto, Vancouver, Calgary, Ottawa, Montreal, Winnipeg,
Halifax) and the Option A cleanup items noticed during the original bug hunt.

## How to run locally

```bash
pip install -r requirements.txt
python app.py                                      # port 5001
python -m unittest test_edmonton_provider.py -v    # mocked tests
RUN_LIVE_TESTS=1 python -m unittest test_edmonton_provider.py -v  # hit real API
```
