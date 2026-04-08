# Part 3 Development Plan: POI Data & LDA Urban Function Identification

**Created:** 2026-04-07
**Owner:** YK
**Status:** Implementation phase
**Deadline dependency:** Part 2 and Part 4 are blocked until Part 3 delivers the LDA model

---

## Overview

Use OpenStreetMap POI data and LDA topic modeling to automatically classify every public transport station in Singapore by its surrounding urban function (e.g., "Dining & Retail District", "Educational Zone", "Commercial Hub").

**Research question addressed:** What characteristics define the destinations that university communities frequent?

**Core analogy:**
- Each station = a "document"
- POI categories near that station = "words"
- LDA discovers latent "topics" = urban function types

---

## Pre-requisites

Before starting implementation, verify the following:

- [ ] `data/` directory exists locally with Part 1 outputs:
  - `station_mapping.csv` (136 campus stations with pt_code, pt_type, university, lat, lon)
  - `sg_bus_stops_all.csv` (5,166 bus stops with zero-padded codes + coordinates)
  - `sg_mrt_stations_all.csv` (~130 MRT stations with names, codes, coordinates)
- [ ] Python environment ready: run `uv sync` in project root (installs requests, osmnx, geopandas)
- [ ] R environment ready: install `topicmodels`, `stm`, `ldatuning` packages if not already installed
- [ ] Overpass API accessible from local network (use `overpass-api.de`; fallback: `overpass.kumi.systems`)
- [ ] ohsome API accessible: `https://api.ohsome.org/v1/`

---

## Task 1: Create POI Download Script

**File:** `utils/download_pois.py` (NEW)
**Estimated output:** `data/sg_pois_all.csv`

### What it does

Downloads all POIs across Singapore from OpenStreetMap via the Overpass API. Queries 8 POI keys: `amenity`, `shop`, `leisure`, `tourism`, `office`, `healthcare`, `craft`, `historic`.

### Technical requirements

1. **Singapore bounding box:** `(1.16, 103.60, 1.47, 104.08)`
2. **Split into 4 sub-regions** to avoid Overpass timeout (each ~0.08° × ~0.12°):
   - Region 1: Northwest `(1.16, 103.60, 1.32, 103.84)`
   - Region 2: Northeast `(1.32, 103.60, 1.47, 103.84)`
   - Region 3: Southwest `(1.16, 103.84, 1.32, 104.08)`
   - Region 4: Southeast `(1.32, 103.84, 1.47, 104.08)`
3. **Query format:** `out center meta` to get element metadata (version, timestamp, uid, changeset)
4. **For each element, extract:**
   - `osm_id`, `osm_type` (node/way), `lat`, `lon` (use center coordinates for ways)
   - All tags as-is (for later primary key extraction)
   - Element metadata: `version`, `timestamp`, `changeset_id`, `user_id`
5. **Retry logic:** Max 3 retries with 15s delay (same pattern as `explore_poi_metadata.py`)
6. **Rate limiting:** Sleep 5s between sub-region queries
7. **Deduplication:** Some POIs may appear as both node and way; keep both but flag with type

### Output schema (`data/sg_pois_all.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `osm_id` | integer | OSM element ID |
| `osm_type` | string | "node" or "way" |
| `lat` | float | Latitude (center for ways) |
| `lon` | float | Longitude (center for ways) |
| `version` | integer | OSM element version number |
| `timestamp` | string | Last-edited timestamp (ISO 8601) |
| `changeset_id` | integer | Changeset ID |
| `user_id` | integer | OSM user ID of last editor |
| `amenity` | string | Value of amenity tag (empty if not present) |
| `shop` | string | Value of shop tag (empty if not present) |
| `leisure` | string | Value of leisure tag (empty if not present) |
| `tourism` | string | Value of tourism tag (empty if not present) |
| `office` | string | Value of office tag (empty if not present) |
| `healthcare` | string | Value of healthcare tag (empty if not present) |
| `craft` | string | Value of craft tag (empty if not present) |
| `historic` | string | Value of historic tag (empty if not present) |
| `name` | string | POI name (may be empty) |
| `all_tags` | string | JSON string of all tags for reference |

### Validation after download

- [ ] Total POI count is reasonable (expect ~100,000-200,000 for Singapore)
- [ ] All 8 POI keys have non-zero counts
- [ ] No sub-region returned 0 results
- [ ] Coordinate range falls within Singapore bounds
- [ ] Name coverage > 70% (Orchard exploration found 76.3%)

---

## Task 2: Create ohsome Quality Metrics Script

**File:** `utils/ohsome_quality.py` (NEW)
**Estimated output:** `data/ohsome_quality_results.json`

### What it does

Queries the ohsome REST API to get aggregate temporal statistics about OSM mapping activity in Singapore. This provides context for interpreting POI data quality (e.g., "is POI growth due to new businesses or new mapping activity?").

### Technical requirements

1. **Base URL:** `https://api.ohsome.org/v1/`
2. **Method:** POST with JSON body
3. **Bounding box:** Same as Singapore bbox `(1.16, 103.60, 1.47, 104.08)`
4. **Three queries:**

   **Query A: POI count over time** (`/elements/count`)
   ```json
   {
     "filter": "amenity or shop or leisure or tourism or office or healthcare or craft or historic",
     "bboxes": "103.60,1.16,104.08,1.47",
     "time": "2020-01-01/2026-04-01/P1M"
   }
   ```

   **Query B: Unique mapper count over time** (`/users/count`)
   ```json
   {
     "filter": "amenity or shop or leisure or tourism or office or healthcare or craft or historic",
     "bboxes": "103.60,1.16,104.08,1.47",
     "time": "2020-01-01/2026-04-01/P1M"
   }
   ```

   **Query C: Edit type breakdown** (`/contributions/count`)
   ```json
   {
     "filter": "amenity or shop or leisure or tourism or office or healthcare or craft or historic",
     "bboxes": "103.60,1.16,104.08,1.47",
     "time": "2020-01-01/2026-04-01/P1M"
   }
   ```

5. **Save raw JSON response** to `data/ohsome_quality_results.json`
6. **Handle authentication:** ohsome may require an API key; check on first run and document if needed

### Output interpretation

- **Query A result:** Monthly total POI count. If steep growth → mapping effort increasing, not just new businesses.
- **Query B result:** Monthly unique contributors. Stable or growing = healthy mapping community. Declining = stale data risk.
- **Query C result:** Creation vs modification vs deletion counts per month. High creation rate = dataset still being built out.

### Cross-reference with Overpass results

- If ohsome shows steep POI growth → snapshot comparisons (Part 2) may reflect mapping effort, not real change
- If ohsome shows stable mapper count → data quality unlikely to change significantly between snapshots
- If ohsome shows high creation rate → newer POIs may be less reliable (single mapper, v1)

---

## Task 3: Create LDA Pipeline R Script (Standalone Development)

**File:** `scripts/part3_poi_lda_yk.Rmd` (NEW — standalone development file)
**Estimated outputs:**
- `data/station_quality_metrics.csv`
- `data/station_poi_counts.csv`
- `data/station_poi_dtm.rds`
- `data/lda_model_k4.rds` through `data/lda_model_k8.rds`
- `data/station_topic_classification.csv`
- 2-3 figures (saved to `figures/`)

### Development workflow (follow Part 1's pattern)

Part 1's approach (`scripts/part1_identify_stations.Rmd`) establishes the pattern:
1. Develop and test all code in a **standalone Rmd file** (output: `html_document`) that knits independently.
2. The standalone file has its own setup chunk (loads packages, defines paths, defines `project_colors` / `map_theme`).
3. The standalone file generates all data outputs and figures locally.
4. Once verified, the relevant chunks are adapted and copied into `scripts/report.Rmd` within the Part 3 section markers.

**Why this matters:**
- `report.Rmd` is shared by all 6 Parts. Editing it directly during development risks merge conflicts.
- A standalone file lets you iterate, debug, and knit freely without affecting others.
- The standalone file stays on the YK branch as a complete, reproducible record of Part 3's pipeline.

**Standalone file requirements:**

```yaml
---
title: "Part 3: POI Data & LDA Urban Function Identification (YK)"
author: "YK"
output: html_document
---
```

- **Must have its own setup chunk** — do NOT rely on report.Rmd's setup. Copy the shared definitions (`project_colors`, `map_theme`, `PROJ`, directory paths) into the standalone file's setup chunk. This ensures the file knits independently.
- **All 13 chunks below** live in this standalone file.
- **The file must knit end-to-end** without errors before any integration into report.Rmd.

### Chunk structure (13 chunks)

#### Chunk 1: `part3-setup` — Load libraries and data
- Libraries: `sf`, `dplyr`, `tidyr`, `stringr`, `topicmodels`, `stm`, `ldatuning`, `ggplot2`, `tm`, `widyr`
- Load `data/sg_pois_all.csv`, `data/sg_bus_stops_all.csv`, `data/sg_mrt_stations_all.csv`
- Define CRS constants (EPSG:4326 for storage, EPSG:3414 for buffering)
- Define 500m buffer radius

#### Chunk 2: `part3-assign-primary-class` — Extract primary POI class
- For each POI row, determine the primary key-value pair using priority:
  `amenity > shop > leisure > tourism > office > healthcare > craft > historic`
- Create a new column `poi_class` = the primary key-value (e.g., "amenity=restaurant")
- **Exclude** rows where the only POI key is `building=residential` or `landuse=residential`
- Remove POIs with no POI keys at all

#### Chunk 3: `part3-filter-vocabulary` — Vocabulary filtering
- Count how many unique stations each `poi_class` appears at (after spatial assignment in chunk 5, or approximate using grid)
- **Actually:** do spatial assignment first, then filter. Reorder:
  - Chunk 2: assign primary class
  - Chunk 3: convert to sf, create station buffers
  - Chunk 4: spatial join POIs to stations
  - Chunk 5: filter vocabulary (after knowing per-station counts)

#### Chunk 3 (revised): `part3-spatial-prep` — Convert to sf objects
- Convert POIs to `sf` points (EPSG:4326 → EPSG:3414 for operations)
- Convert bus stops and MRT stations to `sf` points
- Merge bus + MRT into a single `all_stations` sf object
- Remove duplicate stations (same location, different pt_type)
- Create 500m buffer around each station in EPSG:3414

#### Chunk 4: `part3-spatial-join` — Assign POIs to stations
- Use `sf::st_join(pois, station_buffers, join = st_intersects)`
- Each POI gets assigned to one or more station buffers
- For POIs in multiple buffers, assign to the nearest station (by distance)
- Result: a dataframe with `station_code` + `poi_class` for every assignment

#### Chunk 5: `part3-filter-vocabulary` — Vocabulary filtering
- Count frequency: how many stations each `poi_class` appears at
- **Remove** classes appearing at < 5 stations (too rare, noise)
- **Remove** classes appearing at > 90% of stations (too common, no discriminative power — "stopword analogy")
- Expected vocabulary: ~80–150 classes
- Save filtered vocabulary list

#### Chunk 6: `part3-filter-stations` — Station filtering
- Count total POIs per station
- **Remove** stations with < 3 total POIs (too sparse for LDA)
- Report how many stations removed (expected: ~5,300 → ~1,500-2,500)
- Save station list for reference

#### Chunk 7: `part3-build-dtm` — Build document-term matrix
- Each station = document, each POI class = term, counts = term frequencies
- Use `tm::DocumentTermMatrix()` or manual matrix construction
- Save as `data/station_poi_dtm.rds`
- Also save as `data/station_poi_counts.csv` (human-readable)

#### Chunk 8: `part3-quality-metrics` — Per-station data quality
- From Overpass metadata in `sg_pois_all.csv`, compute per station:
  - `poi_count`: total POIs in buffer
  - `unique_contributors`: number of unique `user_id` values
  - `avg_version`: mean POI version number
  - `pct_named`: % of POIs with non-empty `name`
  - `pct_version_1`: % of POIs at version 1 (never edited)
- Save as `data/station_quality_metrics.csv`

#### Chunk 9: `part3-run-lda` — Run LDA models
- For each K in [4, 5, 6, 7, 8]:
  - `LDA(dtm, k = K, control = list(alpha = 0.1, iter = 2000))`
  - Save model as `data/lda_model_k{K}.rds`
- Set seed for reproducibility: `set.seed(42)`

#### Chunk 10: `part3-select-k` — Select optimal K
- Compute topic coherence (C_v metric) for each K using `ldatuning::FindTopicsNumber()`
- Plot coherence vs K
- Apply domain knowledge: check interpretability at each K
- Select optimal K (expected: K=5 or K=6 based on Lin et al. 2025 precedent)
- Document the selection rationale

#### Chunk 11: `part3-interpret-topics` — Topic interpretation
- For the selected K, extract beta (topic–word) matrix
- For each topic, list top 10-15 POI classes by probability
- Manually assign labels based on top classes, e.g.:
  - High restaurant + café + bar → "Dining & Retail District"
  - High school + university + library → "Educational Zone"
  - High bank + office → "Commercial Hub"
  - High park + playground + sports_centre → "Recreational Zone"
- Create a topic label lookup table

#### Chunk 12: `part3-classify-stations` — Station classification
- Extract gamma (document–topic) matrix from the selected LDA model
- For each station:
  - Assign to dominant topic (highest gamma)
  - Record purity score (max gamma value)
- Join with station coordinates and quality metrics
- Save as `data/station_topic_classification.csv`
- Cross-check: verify no topic is dominated by low-quality stations

#### Chunk 13: `part3-figures` — Generate figures
- **Figure 1: POI class distribution** — Bar chart of top 20 POI classes by frequency
- **Figure 2: Data quality map** — Singapore map colored by per-station quality score (contributor count or POI density)
- **Figure 3: Topic–POI heatmap** — K × top_15_terms heatmap showing beta probabilities
- **Figure 4: Station function map** — Singapore map with stations colored by dominant topic (this is the key deliverable figure)
- Use `project_colors` from report.Rmd setup chunk for consistency
- All figures: `fig.width=8, fig.height=5`, min 10pt labels

---

## Task 4: Literature Contribution

**Location:** report.Rmd Part 3 section (after analysis chunks)
**Requirement:** 2-3 papers + 2-3 paragraphs

### Papers to find and annotate

Find 2-3 additional papers on:
1. POI-based urban function identification (beyond the 4 already analyzed in `paper_synthesis.md`)
2. LDA / topic modeling applied to urban studies or spatial analysis
3. Land use classification using crowdsourced data

### What to write

For each paper, provide:
- Full citation (APA format)
- 2-3 sentence summary of methodology
- 1-2 sentences on relevance to our project
- Key limitation or caveat

Then write 2-3 paragraphs synthesizing these with the existing literature, covering:
- How POI-based methods compare to traditional land use surveys
- Why unsupervised methods (LDA) are appropriate when ground truth is unavailable
- Known limitations of using OSM data for urban function analysis

### Existing literature already available (do NOT duplicate)

These are already covered in `docs/paper_synthesis.md` and should NOT be re-summarized:
- Niu & Silva (2021) — Doc2Vec, London
- Huang et al. (2022) — Semantics-preserved embedding, Xiamen
- Lin et al. (2025) — LDA + network, London
- Huang et al. (2024) — CLIP zero-shot, Chinese cities

---

## Task 5: Integration into report.Rmd

**File:** `scripts/report.Rmd` (EDIT existing, Part 3 section only)
**Source:** Chunks adapted from `scripts/part3_poi_lda_yk.Rmd`

### What to add

Within the `<!-- ===== PART 3: POI & LDA ===== -->` markers:

1. **Data subsection** (~0.5 page)
   - POI data source (OSM via Overpass API)
   - Query parameters (8 keys, Singapore bbox)
   - Data quality summary (total POI count, name coverage, version distribution)
   - OSM completeness caveat (cite Yeow et al. 2021, 28.2%)

2. **Method subsection** (~0.5 page)
   - LDA methodology explanation (document-term analogy)
   - Spatial assignment (500m buffer, sf::st_join)
   - Vocabulary filtering rationale (<5 stations, >90% stations)
   - K selection (topic coherence C_v, range 4-8)
   - Parameter choices (alpha=0.1, 2000 iterations, seed=42)

3. **Results subsection** (~1 page with figures)
   - Data quality map figure
   - Topic interpretation table (topic labels + top POI classes)
   - Topic–POI heatmap figure
   - Station function map figure
   - Key findings (which topics dominate Singapore? Any spatial patterns?)
   - NUS/NTU campus station topics (do they match expectations?)

4. **Limitations** (brief, within results)
   - OSM completeness (~28%)
   - Crowdsourcing bias (commercial areas better mapped)
   - No creation timestamp in OSM
   - LDA bag-of-words assumption

### Figure style consistency

- Use `project_colors` defined in setup chunk
- Use `map_theme` defined in setup chunk for maps
- All chunks: `message=FALSE, warning=FALSE`
- Data loading chunks: `echo=FALSE`
- Analysis chunks: `echo=TRUE`

---

## Task 6: Pre-Merge Checklist (YK Branch)

**Before merging Part 3 work into `main`, complete these steps on the `YK` branch:**

### 6.1 Ensure standalone file is complete and knits

- [ ] `scripts/part3_poi_lda_yk.Rmd` knits end-to-end without errors
- [ ] All data outputs exist in `data/` (see Deliverables Summary)
- [ ] All figures are generated in `figures/`
- [ ] The YAML header includes `author: "YK"` for traceability

### 6.2 Verify standalone file matches the naming convention

The file must follow this naming pattern:
```
scripts/part3_poi_lda_yk.Rmd
```

This follows Part 1's convention (`scripts/part1_identify_stations.Rmd`) while adding the author tag `_yk` to distinguish it from potential future revisions by other members.

### 6.3 Commit standalone file to YK branch

```bash
git add scripts/part3_poi_lda_yk.Rmd
git commit -m "Part 3 (YK): standalone LDA pipeline — knits end-to-end"
```

### 6.4 Integrate into report.Rmd (on YK branch, before merge)

Only after the standalone file is verified:

1. `git pull origin main` — get the latest main
2. Open `scripts/report.Rmd`
3. **Only edit between the Part 3 markers:**
   ```
   <!-- ===== PART 3: POI & LDA URBAN FUNCTION ===== -->
   ... your code and text go here ...
   <!-- ===== END PART 3 ===== -->
   ```
4. Adapt chunks from the standalone file:
   - Remove the standalone setup chunk (report.Rmd has its own shared setup)
   - Adjust data paths to use `data_dir`, `figures_dir` etc. from report.Rmd's setup
   - Set `echo=FALSE` on data loading chunks, `echo=TRUE` on analysis chunks
   - Add narrative text (Data, Method, Results subsections as described in Task 5)
5. Knit `report.Rmd` locally to verify it compiles
6. Commit:
   ```bash
   git add scripts/report.Rmd
   git commit -m "Part 3 (YK): integrate LDA results into report.Rmd"
   ```

### 6.5 Push to main

```bash
git checkout main
git pull origin main
git merge YK
git push origin main
```

Announce in the group chat before pushing.

### 6.6 After merge, share deliverables

- Upload `data/station_topic_classification.csv` to Google Drive
- Share the standalone file `scripts/part3_poi_lda_yk.Rmd` so Part 2 and Part 4 members can reference the LDA pipeline parameters

---

## Dependency Flow

```
Task 1 (download_pois.py)
    │
    ├──→ Task 3, Chunk 2-6 (POI preprocessing & spatial assignment)
    │
    └──→ Task 3, Chunk 8 (quality metrics from Overpass metadata)

Task 2 (ohsome_quality.py)
    │
    └──→ Task 5, Limitations subsection (interpretive context)

Task 3 (part3_poi_lda_yk.Rmd) — all 13 chunks, standalone development
    │
    ├──→ Task 5, Results subsection (figures + findings)
    │
    └──→ Deliverables for Part 2 (LDA pipeline + parameters)
    └──→ Deliverables for Part 4 (station_topic_classification.csv)

Task 4 (Literature)
    │
    └──→ Task 5, Literature Review section

Task 5 (report.Rmd integration)
    │
    └──→ Task 6 (pre-merge checklist, commit, push to main)
```

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Overpass API timeout on large Singapore query | Blocks Task 1 | Split into 4 sub-regions; use retries; try `overpass.kumi.systems` as fallback |
| ohsome API requires authentication | Blocks Task 2 | Check on first run; if key required, apply for free API key at HeiGIT |
| Low POI count at peripheral bus stops | Reduces station coverage | Accept ~1,500-2,500 active stations; report excluded count transparently |
| LDA topics not interpretable | Weak results | Try multiple K values; if none work, consider merging rare POI classes or adjusting vocabulary filter thresholds |
| `ldatuning` package computation slow for C_v | Delays K selection | Use smaller subsample of DTM for tuning; or use `perplexity` as faster alternative |
| Python `uv` not installed or not working | Blocks Tasks 1-2 | Fall back to `pip install -r requirements.txt`; or use conda |

---

## Deliverables Summary

| File | Format | Produced by |
|------|--------|-------------|
| `data/sg_pois_all.csv` | CSV | Task 1 |
| `data/ohsome_quality_results.json` | JSON | Task 2 |
| `data/station_quality_metrics.csv` | CSV | Task 3, Chunk 8 |
| `data/station_poi_counts.csv` | CSV | Task 3, Chunk 7 |
| `data/station_poi_dtm.rds` | RDS | Task 3, Chunk 7 |
| `data/lda_model_k{k}.rds` | RDS (×5) | Task 3, Chunk 9 |
| `data/station_topic_classification.csv` | CSV | Task 3, Chunk 12 |
| `figures/part3_poi_distribution.png` | PNG | Task 3, Chunk 13 |
| `figures/part3_quality_map.png` | PNG | Task 3, Chunk 13 |
| `figures/part3_topic_poi_heatmap.png` | PNG | Task 3, Chunk 13 |
| `figures/part3_station_function_map.png` | PNG | Task 3, Chunk 13 |
| `scripts/part3_poi_lda_yk.Rmd` | Rmd | Task 3 (standalone development file, author: YK) |
| Part 3 text in report.Rmd | Rmd | Task 4 + Task 5 |

---

## Coordination Notes

- **Part 3 blocks Part 2 and Part 4.** Prioritize completing the LDA pipeline (Task 3) so other members can start.
- **Announce in group chat** when POI download completes and when LDA model is ready.
- **Share `station_topic_classification.csv`** via Google Drive once available.
- **Do NOT edit other Parts' sections** in report.Rmd — only write within the Part 3 markers.
- **Git commit frequently** with descriptive messages: `"Part 3 (YK): create POI download script"`, `"Part 3 (YK): LDA pipeline chunks 1-7"`, etc.
- **Always `git pull` before starting work** to avoid merge conflicts.
- **The standalone file (`scripts/part3_poi_lda_yk.Rmd`) stays on the branch permanently** as a reproducible record. It is NOT deleted after integration into report.Rmd — this is the same pattern as Part 1's `scripts/part1_identify_stations.Rmd`.
