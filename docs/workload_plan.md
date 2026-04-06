# Workload Division Plan

## Context

**Project:** Beyond the Campus: Mapping University Community Travel Patterns and Urban Destinations
**Research Question:** How do travel patterns differ across university communities, and what characteristics define the destinations they frequent?
**Deadline:** Sunday 19 April 2026 (end of day)
**Deliverable:** PDF academic paper (~10 pages) — Introduction, Literature Review, Method, Results, Conclusion, References

---

## Part 1: Data Infrastructure & Station Mapping (15%)

**Best fit:** Member with strongest data/engineering skills

**Tasks:**

- Obtain NUS and NTU campus boundary polygons from OpenStreetMap (Overpass API)
- Obtain bus stop coordinates from LTA DataMall GeoJSON (5,166 bus stops)
- Obtain MRT station exit coordinates from LTA DataMall GeoJSON (597 exits → ~130 stations)
- Identify NUS/NTU stations via 500m campus buffer + spatial intersection
- Build master station list with OD data codes (bus zero-padded 5-digit, MRT line codes)
- Map MRT station names to OD data codes using `mrt_station_codes.csv` lookup table
- Save shared CSVs for Parts 2–5: `sg_bus_stops_all.csv`, `sg_mrt_stations_all.csv`
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

- ~~Extract OD subsets from 74 months~~ (done)
- ~~Extract node subsets~~ (done)
- ~~Data quality checks~~ (done)
- ~~Create `report.Rmd` skeleton with shared setup chunk~~ (done: `scripts/report.Rmd`)

**Note (2026-04-05):** All extraction and quality check chunks executed. Subsets in `data/od_subset/` and `data/node_subset/`. Report skeleton at `scripts/report.Rmd`. See `docs/progress_20260405.md` for details.

**Deliverables:**

- Station code mapping table (station name, PT_CODE, PT_TYPE, university)
- Extracted OD subset dataset + node subset dataset (shared via Google Drive)
- Data quality summary

**Paper section:** Method — Data subsection (~1 page)

**Dependencies:** None (this unblocks Parts 2, 4, 5)

---

## Part 2: Year-to-Year POI Evolution Analysis (20%)

**Best fit:** Member comfortable with time-series visualization and GIS

**Tasks:**

1. **Obtain historical OSM POI snapshots** — Download Geofabrik monthly extracts for Singapore at 4 time points (e.g., 2020-01, 2022-01, 2024-01, 2026-02). Fallback: Overpass API `date:` parameter.
2. **Re-run Part 3 LDA pipeline on each snapshot** — Use the same preprocessing, vocabulary, and K value from Part 3. Build document-term matrix per time point, run LDA, extract topic distributions.
3. **Compare urban function changes over time** — For each station, track dominant topic shifts across snapshots. Aggregate: which function types grew/declined? Are there spatial patterns (e.g., new commercial hubs emerging)?
4. **Visualize evolution** — Stacked bar charts of topic proportions by year, map panels showing function changes for high-traffic stations.
- Produce 2–3 publication-quality figures
- **Literature contribution:** Find 2–3 papers on urban function evolution, POI-based longitudinal urban studies, and Singapore's urban development. Write 2–3 paragraphs.

**Note:** This part reuses Part 3's LDA pipeline — does not need to build it from scratch. Expected start: Day 7–8 after Part 3 delivers the pipeline.

**Deliverables:**

- Analysis code + 2–3 figures (topic evolution charts, spatial panels)
- Literature contribution: annotated bibliography + draft paragraphs
- Written findings on how urban functions around transport stations changed over 2020–2026

**Paper section:** Results — Urban Function Evolution (~1.5 pages with figures)

**Dependencies:** Part 3 (LDA pipeline, vocabulary, K selection)

---

## Part 3: POI Data & LDA Urban Function Identification (20%)

**Best fit:** Member interested in GIS/spatial analysis and topic modeling

**Tasks:**

1. **POI data acquisition** — OSM via Overpass API (or Geofabrik `.osm.pbf` + `osmextract` as fallback). Query `amenity`, `shop`, `leisure`, `tourism`, `office`, `healthcare`, `craft`, `historic` tags within Singapore bounding box. Handle Overpass timeouts by splitting into sub-region queries.
2. **POI preprocessing** — Extract primary key=value as POI "class" (priority: amenity > shop > leisure > tourism > office > healthcare > craft > historic). Filter: remove classes at <5 stations or >90% stations (stopword analogy). Expected vocab: ~80–150 classes.
3. **Spatial assignment (document-term matrix)** — 500m buffer around each bus/MRT station (EPSG:3414). Use `sf::st_join()` to assign POIs to stations. Each station = document, POI classes = vocabulary, counts = term frequencies. Filter out stations with <3 total POIs.
4. **LDA topic modeling** — `topicmodels::LDA()` in R. Start with K=8, validate with held-out likelihood + interpretability. Try K=6, 8, 10, 12. Set alpha=0.1 for sparse topic assignments. Extract beta (topic–word) and gamma (document–topic) distributions.
5. **Urban function interpretation** — Examine top 10–15 POI classes per topic. Manually label topics (e.g., "Dining & Retail District", "Educational Zone", "Residential Neighborhood", "Commercial Hub", "Recreational Zone").
6. **Station classification** — Assign each station to its dominant topic. Compute purity score (max gamma). Join to station coordinates.

- Produce 1–2 publication-quality figures (topic–POI distribution, station function map)
- **Literature contribution:** Find 2–3 papers on POI-based urban function identification, LDA/topic modeling in urban studies, and land use classification. Write 2–3 paragraphs covering these themes.

**Note:** This part is fully independent — can start on Day 1 without waiting for Part 1.

**Deliverables:**

- POI dataset (`sg_pois_all.csv`) + document-term matrix (`station_poi_dtm.rds`) + LDA model (`lda_model_k8.rds`) + station classification (`station_topic_classification.csv`) — shared via Google Drive
- 1–2 figures (topic–POI distribution, station function map)
- Literature contribution: annotated bibliography + draft paragraphs

**Paper section:** Results — Urban Function Identification (~1 page with figures)

**Dependencies:** None (fully independent)

---

## Part 4: Destination Function Analysis (10%)

**Best fit:** Member who can bridge spatial and OD data

**Tasks:**

1. **Cross-reference LDA with OD data** — Load Part 3's `station_topic_classification.csv`. For NUS-originated vs NTU-originated trips, compare destination function types using LDA classification. Proportional comparison bar chart.
2. **POI-based comparative analysis:**
  - Jaccard similarity on destination function distributions (NUS vs NTU topic overlap)
  - Chi-square test on destination topic distributions (test if NUS and NTU communities have significantly different destination function preferences)
3. **Intra-day POI dynamics (supplementary, stretch goal)** — Use OSM `opening_hours` tag. Classify POI classes as daytime-only, evening, 24h, or unspecified. Weight topic profiles by time-of-day. Only pursue if time permits.

- Produce 1–2 publication-quality figures (NUS vs NTU destination function comparison)
- **Literature contribution:** Find 2–3 papers on destination choice, university community travel behavior, and urban function vs travel demand. Write 2–3 paragraphs.

**Note:** This part starts after Part 1 delivers OD data AND Part 3 delivers the LDA model. Expected start: Day 7–8.

**Deliverables:**

- Analysis code + 1–2 figures
- Literature contribution: annotated bibliography + draft paragraphs
- Written findings

**Paper section:** Results — Destination Function Comparison (~1 page with figures)

**Dependencies:** Part 1 (extracted datasets) + Part 3 (LDA model + station classification)

---

## Part 5: Comparative Network & Statistical Analysis (20%)

**Best fit:** Member with strongest quantitative/statistics skills

**Tasks:**

- Destination overlap: Jaccard similarity, rank correlation between NUS and NTU (raw trip counts by station)
- Travel distance analysis: haversine distance between origin-destination pairs, compare distributions
- Catchment area comparison: what % of trips fall within 5km, 10km, 15km, 20km zones
- Statistical testing: chi-square test for raw destination distribution differences (trip volumes by station)
- One "outside the box" analysis (pick one):
  - Gini coefficient of destination concentration (how dispersed is travel?)
  - Modality split: bus vs train usage for NUS vs NTU (NUS on Circle Line, NTU on East-West Line)
- Produce 2–3 publication-quality figures
- **Literature contribution:** Find 2–3 papers on travel distance analysis, catchment areas, and comparative transport studies. Write 2–3 paragraphs.

**Note:** POI-based comparative analyses (Jaccard on topic distributions, chi-square on topic distributions) are handled in Part 4.

**Deliverables:**

- Analysis code + 2–3 figures (Sankey diagram, distance distributions, catchment charts)
- Literature contribution: annotated bibliography + draft paragraphs
- Written findings with statistical interpretation

**Paper section:** Results — Comparative Analysis (~1.5 pages with figures)

**Dependencies:** Part 1 (extracted datasets)

---

## Part 6: Paper Assembly (15%)

**Best fit:** Member with strongest academic writing skills

**Tasks:**

- **Weave literature contributions** — Collect draft paragraphs from Parts 2–5. Organize thematically into a unified Literature Review (~1–1.5 pages). Ensure coherent narrative flow.
- **Write Introduction** (~1 page)
- **Write Method section** (~1–1.5 pages) — Synthesize data prep from Part 1, LDA methodology from Part 3, and analytical methods from Parts 2, 4, 5
- **Write Conclusion** (~0.5–1 page)
- **Write Abstract** (~150–250 words)
- **Ensure consistency** — Terminology, voice, formatting, figure references, transitions between sections
- **Proofread** — Grammar, citation formatting, figure numbering
- **Coordinate group review session** — Circulate full draft, collect feedback, manage revisions

**Paper sections:** YAML header, Abstract, Introduction, Literature Review, Method, Conclusion, References

**Dependencies:** All Parts 1–5 draft findings and literature contributions for weaving

---

## Timeline


| Days  | Part 1                                     | Part 2                                   | Part 3                                                   | Part 4                                           | Part 5                               | Part 6                              |
| ----- | ------------------------------------------ | ---------------------------------------- | -------------------------------------------------------- | ------------------------------------------------ | ------------------------------------ | ----------------------------------- |
| 1–3   | Station mapping + data extraction          | (blocked)                               | POI acquisition + preprocessing + lit                    | (blocked)                                        | (blocked)                            | Literature search + reading         |
| 4–7   | Deliver subset + write Method data section | (blocked)                               | Spatial assignment + LDA modeling + interpretation       | (blocked)                                        | Comparative analysis + figures + lit | Draft Intro + Lit Review outline    |
| 8–11  | Assist others                              | Historical snapshots + re-run LDA + evolution analysis + lit | Deliver LDA model; station classification map | OD cross-reference + comparative + lit           | Draft Results section                | Write Method + Conclusion           |
| 12–14 | Review all sections                        | Draft Results section                    | Review all sections                                      | Draft Results + *(supplementary: opening_hours)* | Review all sections                  | Assemble paper, abstract, proofread |
| 15–18 | Group review, final edits, submit          | Group review, final edits, submit        | Group review, final edits, submit                        | Group review, final edits, submit                | Group review, final edits, submit    | Group review, final edits, submit   |


**Parallelism:** Part 3 starts Day 1 (independent). Part 5 starts Day 4 (after Part 1). Parts 2 and 4 start Day 7–8 (after Part 3 delivers LDA model).

## Coordination Checkpoints

- **Day 1:** Group meeting — agree on shared analysis period, figure style (colors, fonts), setup chunk packages, section markers in report.Rmd, literature search scope per part
- **Day 3–4:** Part 1 delivers extracted data — quick group sync to verify; Part 3 shares preliminary POI counts
- **Day 7–8:** Part 3 delivers LDA model + classification — Parts 2 and 4 can start; mid-project check-in for all parts
- **Day 11–12:** Draft sections + literature contributions due to Part 6 for integration
- **Day 14–15:** Full draft circulated for group review
- **Day 18 (Apr 19):** Final submission

---

## Key Risks

1. **Merge conflicts on single .Rmd** — Strict section ownership, frequent pull/commit, group chat coordination. If conflicts persist, switch to child documents (`knit_child()`)
2. **Part 1 delays block Parts 4, 5** — Kept at 15% workload (mostly done); Parts 2 and 3 are independent of Part 1
3. **Part 3 delays block Parts 2 and 4** — Part 3 is the critical path; Parts 2 and 4 can start literature contributions early while waiting
4. **POI data availability** — OpenStreetMap via Overpass API is free for Singapore; Geofabrik `.osm.pbf` as primary fallback (daily updates, ~30MB for Singapore)
5. **Inconsistent analysis across Parts 2–5** — Agree on shared analysis period and terminology at Day 1 meeting
6. **Paper cohesion** — Part 6 owns assembly; each part writes self-contained findings; group review session on Day 14–15
7. **Overpass API reliability for full Singapore POI query** — Use Geofabrik `.osm.pbf` + `osmextract` as primary source to avoid API timeouts entirely
8. **Sparse document-term matrix** — Many peripheral bus stops have few nearby POIs; filter stations with <3 POIs before LDA, reducing ~5,300 to ~1,500–2,500 active stations
9. **LDA short-document problem** — Station-level "documents" are short (10–50 non-zero entries); mitigate with lower K, smaller alpha (0.1), and more iterations
10. **OSM POI coverage bias** — Commercial areas (Orchard, CBD) are well-mapped; residential neighborhoods may be sparse. Acknowledge in Method; NUS-vs-NTU comparison partially controls for this
11. **Literature review fragmentation** — 4 people writing separate lit review contributions risks inconsistency; Part 6 must weave them into a coherent narrative. Mitigation: agree on thematic structure at Day 1 meeting; each part shares annotated bibliography early
12. **Historical OSM data availability** — Part 2 needs Geofabrik snapshots for 4 time points. If unavailable, fallback to Overpass `date:` parameter or reduce to 2–3 time points

