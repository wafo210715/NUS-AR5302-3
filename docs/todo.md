# Todo

## Part 1: Data Infrastructure & Station Mapping

- [x] Obtain NUS and NTU campus boundary GeoJSON (from OSM)
- [x] Obtain bus stop coordinates (LTA DataMall GeoJSON)
- [x] Obtain MRT station coordinates (LTA DataMall GeoJSON)
- [x] Build Part 1 identification script (500m buffer, intersect, visualize)
- [x] Save shared CSVs for Parts 2-4 (sg_bus_stops_all.csv, sg_mrt_stations_all.csv)
- [x] Map MRT station names to OD data station codes (e.g. "KENT RIDGE" → "CC24")
- [ ] Write R script to extract OD subsets from 74 months (filter by station codes)
- [ ] Write R script to extract node subsets from 74 months
- [ ] Run data quality checks (row counts, missing months, anomalies)
- [ ] Create report.Rmd skeleton with shared setup chunk

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
