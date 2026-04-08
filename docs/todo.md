# Todo (v2)

## Phase 0: Setup (DONE)
- [x] Clean up obsolete OSM-specific files
- [x] Update project configuration (pyproject.toml, CLAUDE.md)
- [x] Rewrite documentation (workload_plan.md, todo.md)

## Part 1: Station Mapping (4 Universities)

### Campus Boundaries
- [x] NUS Kent Ridge boundary (`data/nus_boundary.geojson`)
- [x] NTU boundary (`data/ntu_boundary.geojson`)
- [ ] SMU Bras Basah boundary (get from OSM)
- [ ] SUTD Tampines boundary (get from OSM)

### Station Identification
- [x] Bus stop coordinates (`data/sg_bus_stops_all.csv`, 5,166 stops)
- [x] MRT station coordinates (`data/sg_mrt_stations_all.csv`)
- [x] MRT code lookup (`data/mrt_station_codes.csv`)
- [ ] Identify stations near SMU (500m buffer)
- [ ] Identify stations near SUTD (500m buffer)
- [ ] Build `station_mapping.csv` for all 4 universities

### OD Data Extraction (Aug 2024 – Aug 2025)
- [ ] Re-extract OD subsets for 4 universities (13 months: 202408–202508)
- [ ] Re-extract node subsets for same period
- [ ] Data quality check: no missing months, reasonable volumes

### Checkpoint 1: Station Mapping Validation
- [ ] Map: 4 campuses with buffers + identified stations
- [ ] Table: Station count per university

## Part 2: POI + LDA Urban Function Identification

### Overture POI Data
- [ ] Build `utils/download_overture_pois.py`
- [ ] Download 12 monthly snapshots from Source Cooperative
- [ ] Data quality check: POI counts, category distribution, operating_status

### LDA Analysis
- [ ] Update `scripts/part3_poi_lda_yk.Rmd` for Overture input
- [ ] Preprocess Overture categories (categories.primary)
- [ ] Build document-term matrix (stations × POI categories)
- [ ] Run LDA for K=4-8
- [ ] K selection via C_v coherence
- [ ] Interpret and label topics

### Checkpoints 2 & 4 & 5
- [ ] CP2: Overture POI quality heatmap + category bars
- [ ] CP4: K selection coherence plot
- [ ] CP5: Station classification map

## Part 3: Temporal Travel Pattern Analysis

- [ ] Define academic calendar periods (semester/exam/vacation)
- [ ] Monthly OD analysis by university
- [ ] Semester vs vacation comparison
- [ ] Intra-day analysis (morning/afternoon/evening)
- [ ] Destination function cross-reference with LDA

### Checkpoint 6
- [ ] Monthly trip volume with period shading
- [ ] University × Month heatmap

## Part 4: Comparative Analysis

- [ ] Destination overlap (Jaccard similarity)
- [ ] Function preference comparison
- [ ] Travel distance distributions
- [ ] Catchment area analysis
- [ ] Statistical tests

### Checkpoint 7
- [ ] Radar chart: function preferences
- [ ] Sankey: university → destination function

## Part 5: Paper Assembly

- [ ] Collect draft sections
- [ ] Write Introduction
- [ ] Write Literature Review
- [ ] Write Method
- [ ] Write Results
- [ ] Write Conclusion + Abstract
- [ ] Proofread
