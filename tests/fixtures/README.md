# Tier 1 Socrata fixtures

Captured against the live City of Edmonton and City of Calgary open-data portals on **2026-05-24**. Field names recorded below are the SoQL column names returned by the API at capture time. Downstream provider code (Tasks 5-7) must use these exact field names.

## Test points

| City | Lat | Lon | Landmark | Used for |
|---|---|---|---|---|
| Edmonton | 53.5444 | -113.4909 | Sir Winston Churchill Sq (City Hall) | parcel, permits, neighbour zones |
| Edmonton | 53.5402 | -113.4868 | Hotel Macdonald | heritage |
| Edmonton | 53.5340 | -113.4750 | Muttart Conservatory (river valley) | flood/hazard |
| Calgary  | 51.0450 | -114.0640 | Calgary City Hall area (110 9 Ave SW) | parcel |
| Calgary  | 51.0447 | -114.0631 | Calgary City Hall (Municipal Building) | permits, heritage, neighbour zones |
| Calgary  | 51.0530 | -114.0686 | Eau Claire / Prince's Island Park (Bow River) | flood |

The Calgary parcel point was nudged 30 m north of City Hall because the official 51.0447,-114.0631 coordinate falls in the road right-of-way between two parcels and `intersects` returned zero rows there.

## Edmonton (https://data.edmonton.ca)

| Feature | Dataset ID | Geometry column | Geometry type | Key fields captured |
|---|---|---|---|---|
| Parcel | `9tyx-zfd4` ("Land Parcels_Title Parcels (Point)") | `geometry_point` | Point (centroid) | `id`, `area` (m²), `latitude`, `longitude`, `geometry_point` |
| Permits | `q4gd-6q9r` ("Development Permits from 2019 to present") | `location` | Point | `city_file_number`, `permit_type`, `permit_class`, `permit_date`, `status`, `description_of_development`, `address`, `legal_description`, `neighbourhood`, `ward`, `zoning`, `land_parcel_count`, `latitude`, `longitude`, `location` |
| Heritage | `jgsn-dhai` ("The Register and Inventory of Historic Resources in Edmonton") | `geometry_point` | Point | `building_address`, `construction_completion_year`, `name_of_historic_resource`, `neighbourhood`, `warning_type_1`, `zoning_id`, `zoning_descr`, `ward_name`, `latitude`, `longitude`, `geometry_point` |
| Flood / hazard | `6w3s-58pv` ("Zoning Overlays") filtered to `overlay_code` in (`FP`, `NSRV`, `NS10`) | `geometry_multipolygon` | MultiPolygon | `objectid`, `overlay_code`, `overlay_descr`, `bylaw_no`, `special_area` |
| Neighbour zones | `fixa-tstc` ("Zoning Bylaw Geographical Data") | `geometry_multipolygon` | MultiPolygon | `zoning`, `description` |

### Edmonton capture notes

- **Edmonton no longer publishes parcel polygons via open data.** The portal's `Land Parcels_*` datasets only contain centroid points with an `area` (m²) attribute. The City of Edmonton transferred parcel boundary delivery to Alberta Data Partnerships (ADP) in November 2021. Downstream code can use `area` directly but cannot compute perimeter/frontage from this dataset — Tasks 5-7 must either skip frontage or use a separate boundary source. We picked the **Title Parcels** dataset (`9tyx-zfd4`) over Legal Parcels (`774r-kpz5`), Assessment Parcels (`dm3i-bp8w`), and Holding Parcels (`78hg-w763`) because title parcels reflect ownership boundaries (what a property report should describe). All four have identical schemas.
- Edmonton parcel fixture contains 3 rows (the 3 closest title parcels within 100 m of Churchill Square, ordered by descending area) so downstream code can demonstrate parcel-selection logic.
- Edmonton has **no dedicated flood/hazard dataset.** Flood risk is encoded through zoning overlays in `6w3s-58pv` — specifically `FP` (Floodplain Protection Overlay), `NSRV` (North Saskatchewan River Valley and Ravine System Protection Overlay Area 1), and `NS10` (Area 2: lands within 10 m of the river valley). The captured fixture is one `NSRV` row from the Muttart Conservatory point. The `geometry_multipolygon` field is omitted from the saved fixture because the NSRV overlay polygon is ~6 MB — too large for a test fixture. Downstream provider code must re-query at runtime when polygon math is needed; the saved fields are enough to verify schema and the flag.
- Edmonton heritage at Hotel Macdonald returned 1 hit (the hotel itself, "Macdonald Hotel" at "10065 - 100 STREET NW"). A wider radius at downtown captures additional historic buildings; we kept the 200 m radius for tightness.
- Edmonton neighbour zones at Churchill Square required a 300 m radius (vs the requested 100 m) because Socrata's `within_circle` against multipolygons requires actual overlap and the parcel is interior to the CCA polygon. The 300 m capture returns 4 zones: `PSN`, `PS`, `DC1`, `CCA`.
- No PII was returned by the Edmonton permits API for our capture window (no `applicant`/`contractor` columns are exposed in the public dataset).

## Calgary (https://data.calgary.ca)

| Feature | Dataset ID | Geometry column | Geometry type | Key fields captured |
|---|---|---|---|---|
| Parcel | `4bsw-nn7w` ("Current Year Property Assessments (Parcel)") | `multipolygon` | MultiPolygon | `roll_year`, `roll_number`, `address`, `assessed_value`, `assessment_class`, `assessment_class_description`, `comm_code`, `comm_name`, `year_of_construction`, `land_use_designation`, `property_type`, `land_size_sm`, `land_size_sf`, `land_size_ac`, `mod_date`, `sub_property_use`, `multipolygon`, `cpid`, `unique_key` |
| Permits | `6933-unw5` ("Development Permits") | `point` | Point | `permitnum`, `address`, `applicant` (REDACTED), `category`, `description`, `proposedusecode`, `proposedusedescription`, `permitteddiscretionary`, `landusedistrict`, `landusedistrictdescription`, `statuscurrent`, `applieddate`, `communitycode`, `communityname`, `ward`, `quadrant`, `latitude`, `longitude`, `point` |
| Heritage | `99yf-6c5u` ("Historic Resource") | `point` | Point | `id`, `name`, `resource_ty`, `address`, `community`, `construction_yr`, `typology`, `orig_use_ty`, `architect`, `architecture_style`, `development_era`, `significance_summ`, `federal_dsgtn`, `provincial_dsgtn`, `municipal_dsgtn`, `point` (+ many descriptive criterion columns — see fixture) |
| Flood | `tp6q-x2v7` ("Regulatory Flood Map (Bylaw Flood Hazard)") | `multipolygon` | MultiPolygon | `description` (one of: `Floodplain`, `Flood Fringe`, `Floodway`, `Overland Flow`, `Normal River Channel`), `flood_cd` (100=Flood Fringe, 200=Floodway, 300=Overland Flow, 400=Floodplain, 500=Normal River Channel), `perimeter`, `multipolygon` |
| Neighbour zones | `qe6k-p9nh` ("Land Use Districts") | `multipolygon` | MultiPolygon | `lu_code`, `label`, `description`, `major`, `generalize` |

### Calgary capture notes

- **Parcel dataset ID corrected.** The original plan suggested `4bsw-nn7w` is "Property Parcel Polygon" — it is actually **"Current Year Property Assessments (Parcel)"**, which is the polygonised assessment dataset and is even richer than a plain parcel layer (includes assessed value, assessment class, land use designation, year of construction, and three area units). This is the right dataset for feasibility analysis. The geometry column is `multipolygon` as expected.
- **Building Permits vs Development Permits.** The plan suggested either `c2es-76ed` (Building Permits) or `6933-unw5` (Development Permits). I picked **Development Permits** because they map directly to land-use change (the question a feasibility report asks). Building Permits would also work and have richer columns (`workclass`, `estprojectcost`, `totalsqft`, `housingunits`); if downstream tasks need construction-cost data, capture `c2es-76ed` later.
- **Heritage dataset ID corrected.** The plan suggested `xtu2-3hxa` for "Heritage Sites" — that ID does not exist on data.calgary.ca. The correct dataset is **`99yf-6c5u`** ("Historic Resource"), the underlying tabular dataset for the "Map of Historic Resources in Calgary" map view (`jgg4-4e72`).
- **PII scrubbed:** Calgary Development Permits exposes an `applicant` field. All 20 captured rows had their `applicant` value replaced with `"REDACTED"` before commit. No `contractorname`, `phone`, or `email` fields exist on this dataset.
- The Calgary flood fixture is the single `Floodplain` polygon that intersects Prince's Island Park / Eau Claire. The `multipolygon` geometry is preserved (~250 KB) so downstream provider tests can do real area-within-flood math.
- Calgary neighbour zones at City Hall required a 500 m radius to get a diverse sample — within 300 m only `DC` (Direct Control) zones overlap. The 500 m capture returns 17 rows spanning 3 codes: `CC-MH`, `DC`, `S-CRI`.

## Rejected datasets

| Dataset ID | City | Why rejected |
|---|---|---|
| `dkk9-cj9p`, `e4jh-7sw9`, `2vyq-bk6h` | Edmonton | IDs suggested in plan do not exist on data.edmonton.ca |
| `774r-kpz5`, `dm3i-bp8w`, `78hg-w763` | Edmonton | Alternate parcel point datasets — same schema as `9tyx-zfd4`, just different parcel type (Legal/Assessment/Holding vs Title). Title parcels best reflect ownership. |
| `9zth-y5hq` | Edmonton | "City of Edmonton Parcel Mapping Change" — has no columns / empty dataset |
| `ndtw-vdfy` (Hydrographic Features) | Edmonton | Rivers/lakes geometry only — describes water bodies, not regulatory flood zones |
| `y6z3-sitb` | Edmonton | Map view of heritage register; use the underlying tabular dataset `jgsn-dhai` instead |
| `xtu2-3hxa` | Calgary | Does not exist (suggested in plan) |
| `jd4f-yzxr` | Calgary | "Historic Resource Data Lens" — a story page, not a queryable dataset |
| `jgg4-4e72` | Calgary | Map view; use underlying `99yf-6c5u` |
| `c2es-76ed` | Calgary | Building Permits — usable, but Development Permits (`6933-unw5`) is a better fit for feasibility analysis. Recapture this one if construction cost/sqft is needed later. |
| `68hc-v6h3` | Calgary | "Flood Hazard Area" — empty / non-existent at capture time |

## Re-capture script

Every fixture in this directory was captured with `curl` + `jq`/`python3 -m json.tool`. To re-capture (e.g. after the upstream schema changes), the exact queries are:

```bash
# Edmonton parcel
curl -s "https://data.edmonton.ca/resource/9tyx-zfd4.json" \
  --data-urlencode '$where=within_circle(geometry_point, 53.5444, -113.4909, 100)' \
  --data-urlencode '$order=area DESC' --data-urlencode '$limit=3' -G \
  | python3 -m json.tool > edmonton/parcel.json

# Edmonton permits
curl -s "https://data.edmonton.ca/resource/q4gd-6q9r.json" \
  --data-urlencode "\$where=within_circle(location, 53.5444, -113.4909, 500) AND permit_date > '2021-01-01T00:00:00.000'" \
  --data-urlencode '$order=permit_date DESC' --data-urlencode '$limit=20' -G \
  | python3 -m json.tool > edmonton/permits.json

# Edmonton heritage
curl -s "https://data.edmonton.ca/resource/jgsn-dhai.json" \
  --data-urlencode '$where=within_circle(geometry_point, 53.5402, -113.4868, 200)' \
  --data-urlencode '$limit=10' -G \
  | python3 -m json.tool > edmonton/heritage.json

# Edmonton flood (zoning overlay, geometry stripped)
curl -s "https://data.edmonton.ca/resource/6w3s-58pv.json" \
  --data-urlencode "\$where=intersects(geometry_multipolygon, 'POINT(-113.4750 53.5340)') AND (overlay_code='FP' OR overlay_code='NSRV' OR overlay_code='NS10' OR starts_with(overlay_descr, 'River Valley'))" \
  --data-urlencode '$select=objectid,overlay_code,overlay_descr,bylaw_no,special_area' \
  --data-urlencode '$limit=20' -G \
  | python3 -m json.tool > edmonton/flood.json

# Edmonton neighbour zones
curl -s "https://data.edmonton.ca/resource/fixa-tstc.json" \
  --data-urlencode '$select=zoning,description' \
  --data-urlencode '$where=within_circle(geometry_multipolygon, 53.5444, -113.4909, 300)' \
  --data-urlencode '$limit=20' -G \
  | python3 -m json.tool > edmonton/neighbour_zones.json

# Calgary parcel
curl -s "https://data.calgary.ca/resource/4bsw-nn7w.json" \
  --data-urlencode '$where=intersects(multipolygon, "POINT(-114.0640 51.0450)")' \
  --data-urlencode '$limit=1' -G \
  | python3 -m json.tool > calgary/parcel.json

# Calgary permits (with PII scrub — applicant -> REDACTED)
curl -s "https://data.calgary.ca/resource/6933-unw5.json" \
  --data-urlencode "\$where=within_circle(point, 51.0447, -114.0631, 500) AND applieddate > '2021-01-01T00:00:00.000'" \
  --data-urlencode '$order=applieddate DESC' --data-urlencode '$limit=20' -G \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [r.update({'applicant':'REDACTED'}) for r in d if r.get('applicant')]; print(json.dumps(d, indent=2))" \
  > calgary/permits.json

# Calgary heritage
curl -s "https://data.calgary.ca/resource/99yf-6c5u.json" \
  --data-urlencode '$where=within_circle(point, 51.0447, -114.0631, 500)' \
  --data-urlencode '$limit=10' -G \
  | python3 -m json.tool > calgary/heritage.json

# Calgary flood
curl -s "https://data.calgary.ca/resource/tp6q-x2v7.json" \
  --data-urlencode '$where=intersects(multipolygon, "POINT(-114.0686 51.0530)")' \
  --data-urlencode '$limit=5' -G \
  | python3 -m json.tool > calgary/flood.json

# Calgary neighbour zones
curl -s "https://data.calgary.ca/resource/qe6k-p9nh.json" \
  --data-urlencode '$select=lu_code,label,description,major,generalize' \
  --data-urlencode '$where=within_circle(multipolygon, 51.0447, -114.0631, 500)' \
  --data-urlencode '$limit=20' -G \
  | python3 -m json.tool > calgary/neighbour_zones.json
```
