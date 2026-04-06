# Todo

## Part 1: Data Infrastructure & Station Mapping

- [x] Obtain NUS and NTU campus boundary GeoJSON (from OSM)
- [x] Obtain bus stop coordinates (LTA DataMall GeoJSON)
- [x] Obtain MRT station coordinates (LTA DataMall GeoJSON)
- [x] Build Part 1 identification script (500m buffer, intersect, visualize)
- [x] Save shared CSVs for Parts 2-4 (sg_bus_stops_all.csv, sg_mrt_stations_all.csv)
- [x] Map MRT station names to OD data station codes (e.g. "KENT RIDGE" → "CC24")
- [x] Write R script to extract OD subsets from 74 months (filter by station codes)
- [x] Write R script to extract node subsets from 74 months
- [x] Run data quality checks (row counts, missing months, anomalies)
- [x] Create report.Rmd skeleton with shared setup chunk

## Extraction Chunks Added (2026-04-05)

The following chunks have been added to `scripts/part1_identify_stations.Rmd` (all `eval=FALSE`, run once in R console):
- `extract-setup` — load station codes, create output directories
- `extract-od-bus` — filter 74 months of bus OD by campus station codes
- `extract-od-train` — filter 74 months of train OD by campus MRT codes
- `extract-node-bus` — filter 74 months of bus node data
- `extract-node-train` — filter 74 months of train node data
- `data-quality` — row counts, missing months, station coverage, anomaly detection

## Remaining
- [x] Run extraction chunks in R console and verify outputs
- [x] Run data quality checks and review report
- [x] Share extracted subsets via Google Drive

## Visualization Improvements (low priority — for paper if needed)

- [ ] Add scale bar and north arrow to campus maps
- [ ] Add legend for bus stops vs MRT stations
- [ ] Reduce label clutter (currently all bus stop codes shown)
- [ ] Combine NUS + NTU into one figure with facet_wrap()

## Parts 2-5

- [ ] Part 2: Temporal travel pattern analysis
- [ ] Part 3: Spatial destination & POI analysis
- [ ] Part 4: Comparative network & statistical analysis
- [ ] Part 5: Literature review, methodology & paper assembly
