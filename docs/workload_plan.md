# Workload Division Plan (v2)

## Context

**Project:** Beyond the Campus: Mapping University Community Travel Patterns and Urban Destinations
**Research Question:** How do travel patterns differ across university communities, and what characteristics define the destinations they frequent?
**Time period:** Aug 2024 – Aug 2025 (AY2024-25 school year)
**Universities:** NUS (Kent Ridge), NTU, SMU (Bras Basah), SUTD (Tampines)

---

## Part 1: Data Infrastructure & Station Mapping (4 Universities)

**Status: DONE** (see `docs/part1_handoff.md` for full details)

**Completed tasks:**
1. Got SMU and SUTD campus boundaries from OSM (Overpass API)
2. Identified bus stops and MRT stations within 100m buffer of all 4 campuses
3. Built `station_mapping.csv` for NUS, NTU, SMU, SUTD (83 stations total)
4. OD extraction chunks ready in Rmd (eval=FALSE, not yet run)

**Station counts:**
| University | Bus Stops | MRT Stations | Total |
|-----------|-----------|-------------|-------|
| NUS (Kent Ridge) | 39 | 1 (Kent Ridge CC24) | 40 |
| NTU | 22 | 0 | 22 |
| SMU (Bras Basah) | 12 | 2 | 14 |
| SUTD (Tampines) | 6 | 1 | 7 |
| **Total** | **79** | **4** | **83** |

**Key decisions:**
- Buffer distance: 100m (not 500m)
- SUTD boundary: MultiPolygon (main campus + Parcel D as separate polygons)
- Analysis period: Aug 2024 – Jul 2025 (12 months)
- Output CSVs written to repo `data/` directory; source data read from shared `C:/0_Files/NUS/Course/R_Projects/Assignment_3/Data/`

**Output files (in repo `data/`):**
- `station_mapping.csv` — 83 stations with pt_code, pt_type, university, lat/lon
- `sg_bus_stops_all.csv` — all 5,166 Singapore bus stops
- `sg_mrt_stations_all.csv` — all ~130 MRT stations

**Pending (to run manually in RStudio):**
- OD extraction chunks in `part1_identify_stations.Rmd` (eval=FALSE) → produces `data/od_subset/` (24 files) and `data/node_subset/` (24 files)

**Checkpoint:** Map showing 4 campuses with buffers + identified stations. Station count table per university.

**Dependencies:** None (unblocks Parts 2, 3, 4)

---

## Part 2: POI-based Urban Function Identification (Overture + LDA)

**Data source:** Overture Maps Foundation POI data (via Source Cooperative historical archive)
- 12 monthly snapshots available: Aug 2024, Sep 2024, Oct 2024, Nov 2024, Dec 2024, Jan 2025, Mar 2025, Apr 2025, May 2025, Jun 2025, Sep 2025, Oct 2025, Nov 2025, Dec 2025
- Missing: Feb 2025, Jul 2025, Aug 2025
- S3 path: `s3://us-west-2.opendata.source.coop/fused/overture/{release}/theme=places/type=place/`
- Schema: id, names, categories.primary, confidence, operating_status, geometry

**Tasks:**
1. Download Overture POI data for Singapore from Source Cooperative
2. Preprocess: extract `categories.primary` as POI class, filter operating_status=open
3. Spatial assignment: 500m buffer around stations, build document-term matrix
4. LDA topic modeling: test K=4-8, select via C_v coherence
5. Interpret topics as urban function types
6. Classify stations by dominant topic

**Decision: Single snapshot for LDA** — use latest available (Dec 2025). POI landscape is stable month-to-month. Temporal variation comes from OD data.

**Checkpoint:**
- Singapore POI density heatmap + category distribution
- K selection coherence plot
- Topic-word heatmap for selected K
- Station classification map (all stations colored by urban function)

**Key files:**
- `utils/download_overture_pois.py` — Overture POI downloader (NEW)
- `scripts/part3_poi_lda_yk.Rmd` — LDA analysis (update from OSM to Overture input)
- `utils/calculate_topic_coherence_gensim.py` — coherence calculation (reuse)
- `utils/visualize_k_selection.py` — K selection visualization (reuse)
- `utils/export_lda_beta.R` — beta matrix export (reuse)

**Dependencies:** Part 1 (station mapping)

---

## Part 3: Temporal Travel Pattern Analysis

**Data source:** LTA OD data (Aug 2024 – Aug 2025) filtered for 4 university origins

**Tasks:**
1. Define academic calendar periods (broad categories):
   - **Semester** (Aug-Nov, Jan-Apr): Teaching weeks
   - **Exam** (Dec, May): Examination periods
   - **Vacation** (Jun-Jul, Dec-Jan break): Semester breaks
2. Monthly OD analysis: trip volumes by university, per month
3. Semester vs Vacation comparison
4. Intra-day analysis: morning (6-10), afternoon (10-16), evening (16-22), night (22-6)
5. Destination function analysis: cross-reference OD destinations with LDA station classifications

**Checkpoint:**
- Monthly trip volume line plot with semester/exam/vacation shading
- University × Month heatmap
- Destination function proportions by month

**Key files:**
- `scripts/part3_temporal_patterns.Rmd` — temporal analysis (NEW)

**Dependencies:** Part 1 (OD data) + Part 2 (LDA station classification)

---

## Part 4: Comparative Analysis (Inter-University)

**Tasks:**
1. Destination overlap: Jaccard similarity on destination station sets
2. Function preference comparison: proportion of trips to each topic
3. Travel distance: haversine distance distributions
4. Catchment area: % of trips within 5km, 10km, 15km, 20km
5. Statistical tests: chi-square on destination distributions

**Checkpoint:**
- Radar chart: function type preferences per university
- Box plot: travel distance distributions
- Sankey diagram: origin university → destination function type

**Key files:**
- `scripts/part4_comparative.Rmd` — comparative analysis (NEW)

**Dependencies:** Part 1 (OD data) + Part 2 (LDA classification) + Part 3 (temporal context)

---

## Part 5: Paper Assembly

**Tasks:**
1. Collect draft sections from Parts 1-4
2. Write Introduction (~1 page)
3. Write Literature Review (~1-1.5 pages)
4. Write Method section (~1-1.5 pages)
5. Write Results (~3 pages with figures)
6. Write Conclusion (~0.5-1 page)
7. Write Abstract (~150-250 words)
8. Proofread and ensure consistency

**Dependencies:** All Parts 1-4 draft findings

---

## Overture Maps Data Access

### Key URLs
- Documentation: https://docs.overturemaps.org/
- Source Cooperative archive: https://source.coop/fused/overture
- Release calendar: https://docs.overturemaps.org/release-calendar/
- Places schema: https://docs.overturemaps.org/schema/reference/places/place/
- Official S3 (60-day retention): `s3://overturemaps-us-west-2/release/`

### Access Methods
```bash
# Via DuckDB (recommended for filtering)
# Via s3fs + pandas
# Via overturemaps CLI (only for current release, no historical)
```

### Data Retention Policy
Overture maintains publicly available data releases for a maximum of **60 days** on official S3/Azure. Source Cooperative (`source.coop/fused/overture`) archives ALL historical releases since Feb 2024.

---

## Risks

1. **Overture data access**: Source Cooperative is a third-party mirror. If it goes down, historical data becomes unavailable. Mitigation: download and cache all needed snapshots early.
2. **Missing months**: Feb 2025, Jul 2025, Aug 2025 are missing from Source Cooperative mirror. Mitigation: these fall within vacation/transition periods, impact is limited.
3. **SMU/SUTD station density**: Urban campus (SMU) may have few dedicated bus stops. SUTD in Tampines may have limited transit options. Mitigation: expand buffer if needed.
4. **Overture category mapping**: Overture uses ~280 standardized categories (different from OSM tags). Need to verify categories are suitable for LDA topic modeling.
5. **Academic calendar differences**: 4 schools have slightly different semester dates. Mitigation: use broad period categories (semester/exam/vacation).
6. **OD data for Aug 2025**: Latest OD data goes to Feb 2026, so Aug 2025 should be available. Verify.
