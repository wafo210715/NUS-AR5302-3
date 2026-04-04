# Workload Division Plan

## Context

**Project:** Beyond the Campus: Mapping University Community Travel Patterns and Urban Destinations
**Research Question:** How do travel patterns differ across university communities, and what characteristics define the destinations they frequent?
**Deadline:** Sunday 19 April 2026 (end of day)
**Deliverable:** PDF academic paper (~10 pages) — Introduction, Literature Review, Method, Results, Conclusion, References

---

## Part 1: Data Infrastructure & Station Mapping (18%)

**Best fit:** Member with strongest data/engineering skills

**Tasks:**

- Obtain NUS and NTU campus boundary polygons from OpenStreetMap (Overpass API)
- Obtain bus stop coordinates from LTA DataMall GeoJSON (5,166 bus stops)
- Obtain MRT station exit coordinates from LTA DataMall GeoJSON (597 exits → ~130 stations)
- Identify NUS/NTU stations via 500m campus buffer + spatial intersection
- Build master station list with OD data codes (bus zero-padded 5-digit, MRT line codes)
- Map MRT station names to OD data codes using `mrt_station_codes.csv` lookup table
- Save shared CSVs for Parts 3–4: `sg_bus_stops_all.csv`, `sg_mrt_stations_all.csv`
- Cross-reference identified codes against OD data sample
- Extract OD subsets from all 74 months (filter by station codes) — reduces ~18GB to manageable size
- Extract corresponding node (tap-in/tap-out) data for the same stations
- Basic data quality checks (row counts, missing months, anomalies)
- Set up the shared setup chunk in `report.Rmd` (library loading, data paths)

**Completed (2026-04-02):**

- Campus boundaries acquired (NUS: 67-point polygon, NTU: 85-point polygon)
- Part 1 identification script (`scripts/part1_identify_stations.Rmd`) — knits end-to-end
- `data/station_mapping.csv` — campus-buffered stations with pt_code, pt_type, university, lat/lon
- `data/sg_bus_stops_all.csv` — all 5,166 Singapore bus stops with zero-padded codes
- `data/sg_mrt_stations_all.csv` — all ~130 MRT stations with names, codes, coordinates
- `data/mrt_station_codes.csv` — 182-row code→name lookup (NS, EW, NE, CC, DT, TE, LRT)
- MRT station codes mapped via Wikipedia + LTA data.gov.sg schema
- Bus code zero-padding: `sprintf("%05d", ...)` to match OD data format
- CRS: EPSG:4326 for storage, EPSG:3414 for 500m buffer creation
- Visualization: NUS and NTU campus maps with bus stops (red circles) and MRT stations (green triangles)

**Remaining:**

- Extract OD subsets from 74 months
- Extract node subsets
- Data quality checks
- Create `report.Rmd` skeleton with shared setup chunk

**Deliverables:**

- Station code mapping table (station name, PT_CODE, PT_TYPE, university)
- Extracted OD subset dataset + node subset dataset (shared via Google Drive)
- Data quality summary

**Paper section:** Method — Data subsection (~1 page)

**Dependencies:** None (this unblocks Parts 2, 3, 4)

---

## Part 2: Temporal Travel Pattern Analysis (20%)

**Best fit:** Member comfortable with time-series visualization

**Tasks:**

- Hourly profiles: peak/off-peak for NUS vs NTU (weekday vs weekend)
- Weekly patterns: weekday vs weekend/holiday comparison
- Monthly/seasonal trends across 2020–2026
- COVID-19 impact: pre-COVID (Jan–Feb 2020), during (Mar 2020–2021), recovery (2022–2026)
- Net flow analysis: inflow vs outflow by hour for each campus
- Produce 2–3 publication-quality figures

**Deliverables:**

- Analysis code + 2–3 figures (heatmap, line charts, time series)
- Written findings with interpretation

**Paper section:** Results — Temporal Patterns (~1.5 pages with figures)

**Dependencies:** Part 1 (extracted datasets)

---

## Part 3: Spatial Destination & POI Analysis (22%)

**Best fit:** Member interested in GIS/spatial analysis

**Tasks:**

- Obtain POI data for Singapore (OpenStreetMap/Overpass API, or SLA OneMap)
- Geocode all transport stations (lat/lng using LTA bus stop JSON files + MRT coordinate lists)
- Build destination profiles: for each destination station, count nearby POIs by category (dining, shopping, entertainment, parks, residential, commercial, etc.)
- Rank top destinations for NUS-originated vs NTU-originated trips
- Cluster destinations by POI profile (e.g., "commercial hub," "residential neighborhood")
- Produce 2–3 publication-quality maps/figures

**Note:** POI data acquisition and geocoding can start immediately — does not need to wait for Part 1.

**Deliverables:**

- POI dataset + station geocoding table + destination profile dataset (shared via Google Drive)
- 2–3 figures (destination maps, POI category charts)
- Written findings

**Paper section:** Results — Destination Characteristics (~1.5 pages with figures)

**Dependencies:** Part 1 for main analysis (POI work can start in parallel)

---

## Part 4: Comparative Network & Statistical Analysis (20%)

**Best fit:** Member with strongest quantitative/statistics skills

**Tasks:**

- Destination overlap: Jaccard similarity, rank correlation between NUS and NTU
- Travel distance analysis: haversine distance between origin-destination pairs, compare distributions
- Catchment area comparison: what % of trips fall within 5km, 10km, 15km, 20km zones
- Statistical testing: chi-square test for destination distribution differences
- One "outside the box" analysis (pick one):
  - Gini coefficient of destination concentration (how dispersed is travel?)
  - Modality split: bus vs train usage for NUS vs NTU (NUS on Circle Line, NTU on East-West Line)
  - Network graph analysis of destination clusters
- Produce 2–3 figures

**Deliverables:**

- Analysis code + 2–3 figures (Sankey diagram, distance distributions, catchment charts)
- Written findings with statistical interpretation

**Paper section:** Results — Comparative Analysis (~1.5 pages with figures)

**Dependencies:** Part 1 (extracted datasets), optionally Part 3 (station coordinates)

---

## Part 5: Literature Review, Methodology & Paper Assembly (20%)

**Best fit:** Member with strongest academic writing skills

**Phase 1 (starts immediately, no dependencies):**

- Find 8–12 relevant academic papers (university travel behavior, OD analysis, Singapore transport, POI-based destination studies)
- Write Literature Review (~1–1.5 pages, organized thematically)
- Write Introduction (~1 page)
- Perform a standalone supplementary analysis: mode share comparison (bus vs train) using node tap-in/tap-out data

**Phase 2 (after Parts 2–4 produce findings):**

- Write Method section (~1–1.5 pages, synthesizing data prep from Part 1 + analytical methods from Parts 2–4)
- Write Conclusion (~0.5–1 page)
- Write Abstract (~150–250 words)

**Phase 3 (final days):**

- Ensure consistent terminology, voice, and formatting across all sections
- Write transitions between sections
- Proofread, check figure references, format references
- Coordinate group review session

**Paper sections:** YAML header, Abstract, Introduction, Literature Review, Method, Conclusion, References

**Dependencies:** None for Phase 1; Parts 2–4 draft findings for Phase 2; all sections for Phase 3

---

## Timeline


| Days  | Part 1                                     | Part 2                            | Part 3                            | Part 4                            | Part 5                              |
| ----- | ------------------------------------------ | --------------------------------- | --------------------------------- | --------------------------------- | ----------------------------------- |
| 1–3   | Station mapping + data extraction          | (blocked)                         | POI data acquisition + geocoding  | (blocked)                         | Literature search + reading         |
| 4–7   | Deliver subset + write Method data section | Temporal analysis + figures       | Spatial/POI analysis + figures    | Comparative analysis + figures    | Write lit review + intro            |
| 8–11  | Assist others if needed                    | Draft Results section             | Draft Results section             | Draft Results section             | Write Method + Conclusion           |
| 12–14 | Review all sections                        | Review all sections               | Review all sections               | Review all sections               | Assemble paper, abstract, proofread |
| 15–18 | Group review, final edits, submit          | Group review, final edits, submit | Group review, final edits, submit | Group review, final edits, submit | Group review, final edits, submit   |


## Coordination Checkpoints

- **Day 1:** Group meeting — agree on shared analysis period, figure style (colors, fonts), setup chunk packages, section markers in report.Rmd
- **Day 3–4:** Part 1 delivers extracted data — quick group sync to verify
- **Day 7–8:** Mid-project check-in — each member shares preliminary findings
- **Day 11–12:** Draft sections due to Part 5 for integration
- **Day 14–15:** Full draft circulated for group review
- **Day 18 (Apr 19):** Final submission

---

## Key Risks

1. **Merge conflicts on single .Rmd** — Strict section ownership, frequent pull/commit, group chat coordination. If conflicts persist, switch to child documents (`knit_child()`)
2. **Part 1 delays block everyone** — Kept at 18% workload; Part 3's POI work starts independently
3. **POI data availability** — OpenStreetMap via Overpass API is free for Singapore; SLA OneMap as backup
4. **Inconsistent analysis across Parts 2–4** — Agree on shared analysis period and terminology at Day 1 meeting
5. **Paper cohesion** — Part 5 owns assembly; group review session on Day 14–15

