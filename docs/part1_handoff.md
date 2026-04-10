# Part 1 Handoff: Station Mapping (Complete)

## What was done

Identified bus stops and MRT stations within **100m buffer** of 4 university campuses, and extracted the station code mapping needed for downstream OD analysis.

## Universities covered

| University | Bus Stops | MRT Stations | Total |
|-----------|-----------|-------------|-------|
| NUS (Kent Ridge) | 39 | 1 (Kent Ridge CC24) | 40 |
| NTU | 22 | 0 | 22 |
| SMU (Bras Basah) | 12 | 2 | 14 |
| SUTD (Tampines) | 6 | 1 | 7 |
| **Total** | **79** | **4** | **83** |

## Output files (in repo `data/`)

| File | Description | Used by |
|------|-------------|---------|
| `station_mapping.csv` | 83 stations with pt_code, pt_type, university, lat/lon, in_od_data flag | Parts 2, 3, 4 |
| `sg_bus_stops_all.csv` | All 5,166 Singapore bus stops (bus_stop_code, lon, lat) | Parts 3, 4 |
| `sg_mrt_stations_all.csv` | All ~130 MRT stations (station_name, station_code, lon, lat) | Parts 3, 4 |

### station_mapping.csv schema

```
station_name, pt_code, pt_type, university, latitude, longitude, source, in_od_data
```

- `pt_code`: station code as used in LTA OD data (e.g. `"15139"` for bus, `"CC24"` for train)
- `pt_type`: `"BUS"` or `"TRAIN"`
- `in_od_data`: `TRUE` if the code appears as origin or destination in the OD data (checked against all 12 months). One exception: bus stop `07509` (SMU) is `FALSE` — see [Data quality](#data-quality) below.

## OD extraction (DONE)

The extraction chunks in `scripts/part1_identify_stations.Rmd` (marked `eval=FALSE`) have been run. Output:

| Directory | Files | Description |
|-----------|-------|-------------|
| `data/od_subset/` | 24 CSVs | OD rows where origin OR destination is a campus station (Aug 2024 – Jul 2025) |
| `data/node_subset/` | 24 CSVs | Tap-in/tap-out volumes for campus stations (same period) |
| `data/data_quality_report.csv` | 1 CSV | Quality check: row counts, station coverage, anomalies per month |

**To re-run:** Open `part1_identify_stations.Rmd` in RStudio. Run chunks in order: `extract-setup` → extraction chunks → `data-quality`. The `extract-setup` and `data-quality` chunks must be run together in the same session (the quality check depends on variables defined in `extract-setup`).

### Data quality

| Dataset | Months | Rows/month (approx) | Stations found | Stations missing |
|---------|--------|---------------------|----------------|-----------------|
| OD Bus | 12/12 | 135k–150k | 78/79 | 1 (`07509`) |
| OD Train | 12/12 | 35k–37k | 4/4 | 0 |
| Node Bus | 12/12 | 2965–2988 | 78/79 | 1 (`07509`) |
| Node Train | 12/12 | 160 | 4/4 | 0 |

**All 12 months present**, no missing months. One minor anomaly flagged: `transport_node_bus_202506.csv` has 2965 rows (slightly below the ~2980 norm), within acceptable range.

**Seasonal pattern**: Both bus and train OD data show expected dips in Dec 2024 and Jun 2025 (~25–30% lower trip volumes), corresponding to vacation periods.

### Bus stop 07509 (SMU) — not in OD data

Bus stop `07509` is a real LTA bus stop (confirmed in `LTABusStop.geojson`), but has **zero rows** across all 74 months of LTA OD and node data. This is likely a very low-usage stop where LTA's privacy threshold suppresses aggregated trip data. Impact is negligible — 1 of 79 bus stops. The `in_od_data = FALSE` flag in `station_mapping.csv` correctly marks it; downstream analysis should skip it.

### Bug fixes applied to `part1_identify_stations.Rmd`

1. **`cross-reference-od` chunk**: Changed from reading a 100k-row sample to reading the full Aug 2024 OD file, and added `pad_bus_code` to handle zero-padding. The sample was too small and missed SMU downtown bus stops, causing 11 SMU stops to be incorrectly flagged `in_od_data = FALSE`.
2. **`data-quality` chunk**: Added `library(readr)` (needed for `read_csv`/`write_csv`). Replaced `length(unique(campus_codes)) - length(stations_found)` with `setdiff` for `stations_missing` — the subtraction produced incorrect results. Added code to re-save `station_mapping.csv` with corrected `in_od_data` values based on all 12 months of subset data.

## Source data (NOT in repo, gitignored)

| File | Location |
|------|----------|
| Campus boundaries (4 geojson) | `C:/0_Files/NUS/Course/R_Projects/Assignment_3/Data/` |
| LTA bus stops, MRT exits, MRT codes | Same shared `Data/` folder |
| Raw OD data (296 CSVs, Jan 2020 - Feb 2026) | Same shared `Data/OD_Data/` |

## Key decisions

- **Buffer distance**: 100m (not 500m). This captures stations immediately adjacent to campus boundaries.
- **SUTD boundary**: MultiPolygon — main campus (way 223860465) + Parcel D (way 1427933682) as separate polygons.
- **Analysis period**: Aug 2024 - Jul 2025 (12 months, AY2024-25 school year).
- **Coordinate system**: Data stored in EPSG:4326 (WGS84). Buffering done in EPSG:3414 (SVY21, meters).

## What Parts 2/3/4 need to know

1. Read `station_mapping.csv` to get campus station codes for filtering OD data.
2. Use `pt_code` column to match against `ORIGIN_PT_CODE` / `DESTINATION_PT_CODE` in OD data.
3. Bus codes are 5-digit zero-padded strings (e.g. `"15139"`). Train codes are MRT line codes (e.g. `"CC24"`).
4. The `university` column identifies which campus each station belongs to.
5. Use `data/od_subset/` files for OD analysis and `data/node_subset/` files for tap-in/tap-out analysis — do not re-read the raw OD data.
6. Bus stop `07509` (SMU) has no data in OD or node subsets — skip it in analysis.
7. OD bus subsets are large (~135k–150k rows/month) because each row includes the non-campus endpoint too (fan-out effect).
