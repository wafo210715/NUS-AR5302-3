# Project Info: Data, Naming & File Flow

## Data Files in `data/`

| File | Source | Description |
|------|--------|-------------|
| `nus_boundary.geojson` | OpenStreetMap (Overpass API) | NUS campus polygon, 67 points |
| `ntu_boundary.geojson` | OpenStreetMap (Overpass API) | NTU campus polygon, 85 points |
| `LTABusStop.geojson` | LTA DataMall | 5,166 bus stops across Singapore |
| `LTAMRTStationExitGEOJSON.geojson` | LTA DataMall | 597 MRT station exits (~130 unique stations) |
| `mrt_station_codes.csv` | LTA data.gov.sg + Wikipedia | MRT/LRT station code→name lookup (stn_code, station_name, mrt_line) |
| `OD_Data/` | LTA DataMall | 74 months (Jan 2020 – Feb 2026), 296 CSV files |

### OD Data Schema

**Origin-Destination files** (`origin_destination_bus_YYYYMM.csv`, `origin_destination_train_YYYYMM.csv`):
- YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, ORIGIN_PT_CODE, DESTINATION_PT_CODE, TOTAL_TRIPS

**Node files** (`transport_node_bus_YYYYMM.csv`, `transport_node_train_YYYYMM.csv`):
- YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, PT_CODE, TOTAL_TAP_IN_VOLUME, TOTAL_TAP_OUT_VOLUME

### LTA GeoJSON Schemas

**LTABusStop.geojson** (per feature):
- BUS_STOP_NUM: 5-digit bus stop code (e.g. "04168" or "4168")
- BUS_ROOF_NUM: bus shelter number
- geometry: Point [longitude, latitude]

**LTAMRTStationExitGEOJSON.geojson** (per feature):
- STATION_NA: full station name (e.g. "KENT RIDGE MRT STATION")
- EXIT_CODE: exit label (e.g. "Exit 1")
- geometry: Point [longitude, latitude]

## Column Naming Conventions

| Name | Meaning | Format | Example |
|------|---------|--------|---------|
| `pt_code` | Public transport station code | From LTA OD data | `"04168"` (bus), `"CC24"` (train) |
| `station_code` | Same as pt_code, clearer name | Used in our output CSVs | `"CC24"` |
| `bus_stop_code` | Bus stop number | 5-digit zero-padded | `"04168"` |
| `station_name` | Human-readable station name | String | `"KENT RIDGE"` |
| `pt_type` | Transport mode | "BUS" or "TRAIN" | `"BUS"` |
| `university` | Campus association | "NUS" or "NTU" | `"NUS"` |

**Note:** OD data CSVs use `ORIGIN_PT_CODE` and `DESTINATION_PT_CODE` (LTA naming). Our output CSVs use `pt_code` / `station_code`. They refer to the same concept.

## Coordinate Reference Systems

| EPSG | Name | Unit | Used for |
|------|------|------|----------|
| 4326 | WGS84 | Degrees (lat/lon) | Data storage, visualization, ggplot2 coord_sf() |
| 3414 | Singapore SVY21 | Meters | 500m buffer creation (needs meter-based distance) |

**Pattern:** Read in 4326 → transform to 3414 for buffering → transform back to 4326 for output/visualization.

## Data Flow

```
LTABusStop.geojson ──┐
                      ├── Part 1 script ── station_mapping.csv ── Parts 2, 3, 4
LTAMRTStationExit... ─┤                  ── sg_bus_stops_all.csv ─ Parts 3, 4
mrt_station_codes.csv ┤                  ── sg_mrt_stations_all.csv ─ Parts 3, 4
nus_boundary.geojson ──┤
ntu_boundary.geojson ──┘

OD_Data/*.csv ── Part 1 extraction script (TODO) ── OD subset ── Parts 2, 3, 4
OD_Data/*.csv ── Part 1 extraction script (TODO) ── Node subset ── Parts 2, 5
```

## Known Limitations

### Transfer trips
The LTA OD data records each public transport leg separately. A trip involving transfers (e.g., bus to MRT) appears as multiple independent OD pairs, not one journey. This study focuses on station-level analysis (which stations are popular destinations) rather than journey reconstruction. The NUS-vs-NTU comparative framing mitigates this limitation since both campuses are subject to the same measurement approach.

### Non-university travelers
The OD data captures all trips from/to stations near campus, including non-university users (residents, workers, visitors). We refer to these collectively as "university community" travel and acknowledge the noise in the Method section.
