# OSM Historical Data & POI Quality: Methodology Research

**Date:** 2026-04-06 (updated with verified sources)
**Purpose:** Inform methodology for Part 2 (year-to-year POI evolution) and Part 3 (LDA urban function identification)
**Status:** Research phase — no implementation yet

---

## 1. OSM Historical Data Access Methods

### 1.1 Overpass API `date:` Parameter

The Overpass API supports querying the OSM database state at a specific point in time using the `date:` parameter in the global settings block.

**Syntax:**
```overpass
[out:json][timeout:120][date:"2022-01-01T00:00:00Z"];
(
  node["amenity"](1.16,103.60,1.47,104.08);
  way["amenity"](1.16,103.60,1.47,104.08);
);
out center;
```

**Verified behavior (tested in previous session):**
- Works reliably back to at least 2020 for Singapore data
- Returns the database state exactly as it existed at the specified date
- Returns full tag sets for elements that existed at that date
- **Critical limitation:** Does NOT return element metadata (timestamp, version, changeset, uid, user) when using `date:` queries. This means you cannot tell when an element was created, modified, or by whom.

**Implications for our project:**
- You can get "what POIs existed at date X" but not "when was this POI created"
- Cannot distinguish a newly opened shop from a newly mapped shop
- Cannot track element lifecycle (creation → modification → deletion) through this method alone
- Useful for snapshot comparisons (Part 2), not for change detection per element

**Performance considerations:**
- Historical queries may be slower than current-state queries
- Rate limiting applies; Singapore is small (~30MB total OSM data) so full queries should complete within timeouts
- Split large queries into sub-regions if needed (Orchard, CBD, residential zones)

### 1.2 Geofabrik Historical Extracts

Geofabrik provides pre-built geographic extracts of OSM data, including historical snapshots.

**Yearly snapshots (Jan 1st):**
- Available via the raw directory index at `https://download.geofabrik.de/asia/malaysia-singapore-brunei.html`
- Navigate to "Historical data" section at bottom of page
- Snapshots available as `.osm.pbf` files at yearly intervals
- Requires downloading and processing locally (e.g., with `osmium` tool or Python `osmium` bindings)

**Monthly snapshots (since 2014):**
- Not pre-built; require reconstructing from full history files
- Full history files available from:
  - `planet.openstreetmap.org/replication/hour/` (hourly diffs)
  - `planet.openstreetmap.org/history/` (full history dumps, requires OSM account due to personal data in metadata)
- Process: `osmium extract --history --time-filter=2022-01-01T00:00:00Z planet-XXXXXX.osm.pbf -o singapore_2022-01.osm.pbf -B singapore.poly`
- This is complex and requires significant disk space (~1TB for full planet history)

**Key caveat from Geofabrik blog:**
> "OSM data at time X tells you what OSM knew about the world at that time — not what the world was actually like at that time."

This is the fundamental epistemological challenge of using OSM for historical analysis. A POI appearing in 2022 could mean:
1. The POI was newly created in 2022 (new business opened)
2. The POI was newly mapped in 2022 (existing business finally added to OSM)
3. The POI was moved/retagged in 2022 (reclassification, not new creation)

### 1.3 OSM Full History API

The OSM API provides access to the complete version history of individual elements.

**Endpoint:** `https://api.openstreetmap.org/api/0.6/[node|way|relation]/[id]/history`

**Returns:** All versions of an element with full metadata (timestamp, changeset, user, tags per version).

**Limitations:**
- Per-element only — you must know the element ID beforehand
- No bulk queries; each element requires a separate HTTP request
- Rate limited (to prevent abuse of the live editing API)
- Not practical for querying thousands of POIs
- Version numbering resets on element deletion and recreation (a deleted shop reappearing gets version 1, not continuation)

**Use case for our project:** Not practical as primary method, but useful for validating specific examples (e.g., "when was this specific Orchard Road shop first mapped?").

### 1.4 OSHDB (OpenStreetMap History Database) — HeiGIT

The OSHDB is a specialized database framework developed by HeiGIT (Heidelberg Institute for Geoinformation Technology) for spatio-temporal analysis of OSM history data.

**Components:**
- **OSHDB core**: PostgreSQL/PostGIS backend storing full OSM history
- **oshdb-api**: Java API for querying (supports Spark and SQL backends)
- **oshpy**: Python bindings for OSHDB
- **ohsome API**: REST API for OSM history analysis
- **ohsomeHeX**: Interactive QGIS plugin for OSM history exploration
- **ohsome Dashboard**: Web dashboard at `dashboard.ohsome.org`
- **ohsome-planet**: OSM history in GeoParquet format (newer, more accessible)

**Key capabilities:**
- Count POIs by tag within a bounding box over time
- Track element creation/deletion/modification rates
- Filter by geometry type, tags, and time ranges
- Compute intrinsic quality indicators (contributor count, edit frequency, version count)
- Built-in bias correction analyses

**Access options:**
1. **ohsome API** (free, no installation): `https://api.ohsome.org/v1/` — send POST requests with bounding box, tags, and time range
2. **oshdb on bigquery** (Google Cloud Public Dataset): `bigquery-public-data.osm_history` — query with SQL
3. **Local installation**: Requires downloading and importing full history data (large)
4. **ohsome-planet** (GeoParquet): Downloadable files for local analysis

**Relevance to our project:**
- The ohsome API can directly answer "how many amenity=restaurant POIs existed in Singapore in 2020-01 vs 2024-01?"
- Can compute mapping activity metrics (contributors per area, edit frequency) for bias detection
- Most practical option for Part 2's historical analysis without requiring heavy infrastructure

### 1.5 Comparison of Methods

| Method | Snapshot queries | Element history | Bulk analysis | Setup effort | Best for |
|--------|:-:|:-:|:-:|:-:|---------|
| Overpass `date:` | Yes | No | Moderate | Low | Snapshot POI lists at specific dates |
| Geofabrik yearly extracts | Yes | No | Full | Low | Offline processing, archival snapshots |
| OSM History API | No | Yes | No (per-element) | Low | Validating specific elements |
| OSHDB / ohsome API | Yes | Yes | Full | Medium | Systematic historical analysis with bias metrics |

**Recommendation for Part 2:**
- **Primary**: Overpass `date:` for 4 snapshot POI extractions (simple, no setup)
- **Supplementary**: ohsome API for mapping activity bias metrics (contributor counts, edit frequency per area)
- **Not recommended**: Geofabrik historical reconstruction (too complex for 4 time points)

---

## 2. POI Lifecycle Detection

### 2.1 The Fundamental Challenge

OSM is a living map, not a historical record. POIs in OSM represent the current state of mapping knowledge, not the ground truth of what existed at any given time. There is no reliable way to distinguish:

- **New business opening** → POI created because shop actually opened
- **Mapping activity** → POI created because a mapper surveyed the area
- **Data import** → POI created from an automated data import (e.g., government address data)

### 2.2 What Can Be Detected

**Element creation** (approximate):
- The first version of an element has a timestamp. This represents when the element was first added to OSM.
- But this timestamp reflects mapping activity, not business opening date.
- Only available through OSHDB or the History API, NOT through Overpass `date:` queries.

**Element deletion:**
- If an element disappears between two snapshots, it could mean: business closed, mapper deleted it, or it was merged/reclassified.
- Deletion detection requires comparing two snapshots and matching elements by ID.

**Tag modification (function change):**
- A POI's tags changing between versions (e.g., `amenity=bank` → `shop=convenience`) indicates either a real business change or a mapping correction.
- Only detectable through element history, not snapshots.

**Element version count:**
- High version count (>5) suggests either a real-world change (multiple edits as the POI evolved) or heavy mapping activity/disputes.
- Available through OSHDB or History API.

### 2.3 Practical Approach for Our Project

Given the limitations above, we cannot reliably detect individual POI lifecycles. Instead, we can:

1. **Aggregate-level change detection**: Compare total POI counts by category between snapshots. Growth in `amenity=restaurant` in an area suggests commercial development, regardless of individual mapping timing.

2. **Station-area function evolution**: Run LDA on each snapshot. Track dominant topic changes at the station level. A station shifting from "Residential" to "Commercial" over 2020-2026 is meaningful even if individual POI timestamps are unreliable.

3. **Mapping activity normalization**: Use ohsome API to compute contributor count and edit frequency per area. Areas with high mapping activity growth may show POI count increases that reflect mapping effort, not real change. Flag these for cautious interpretation.

4. **Cross-validation with known events**: Singapore's major developments (Jurong Lake District, Punggol Digital District, Tengah new town) have known timelines. Check if POI evolution in these areas matches expected patterns as a sanity check.

---

## 3. Published Research on OSM Data Quality & Temporal Analysis

### 3.1 Yeow et al. (2021) — POI Data Validation Methods: An Urban Case Study

**Citation:** Yeow, L. W., Low, R., Tan, Y. X., & Cheah, L. (2021). Point-of-Interest (POI) Data Validation Methods: An Urban Case Study. *ISPRS International Journal of Geo-Information*, 10(11), 735.

**Context:** SUTD (Singapore University of Technology and Design). This is the most directly relevant paper for our project — it systematically evaluates POI data quality in Singapore.

**Method:**
- Study area: Tampines planning area, Singapore (1.8 km²)
- Compared 4 POI sources against SLA (Singapore Land Authority) address database as ground truth:
  1. OpenStreetMap
  2. Google Maps (via Google Places API)
  3. HERE Maps
  4. OneMap (SLA's official map)
- Three validation methods tested:
  1. **String matching** — name-based comparison
  2. **Spatial matching** — distance-based (50m threshold)
  3. **Combined matching** — both name and distance criteria
- Metrics: Completeness (recall), Correctness (precision), Overall Quality (F1 score), Positional Accuracy

**Key findings:**

| Source | Completeness | Correctness | Overall Quality |
|--------|:-:|:-:|:-:|
| Google Maps | 72.9% | 89.0% | 80.0% |
| OneMap | 52.1% | 94.9% | 67.3% |
| HERE Maps | 47.4% | 82.0% | 60.0% |
| **OpenStreetMap** | **28.2%** | **58.3%** | **37.9%** |

- OSM had the **lowest completeness** of all four sources (28.2%) — only about 1 in 4 real-world POIs in Tampines were represented in OSM
- OSM also had the **lowest overall quality** (37.9%)
- Positional accuracy was reasonable across all sources (median error < 50m)
- Combined matching (name + distance) produced the most reliable results

**Limitations acknowledged by authors:**
- Study area limited to Tampines (one planning area) — results may not generalize to all of Singapore
- SLA address database used as reference may itself be incomplete
- POI type/category matching was not tested (only positional/name matching)
- Temporal dimension not addressed

**Relevance to our project:**
- Provides concrete, quantified evidence that OSM POI completeness in Singapore is low (~28%)
- We must frame our LDA analysis as "analysis of available OSM data" not "analysis of all urban POIs"
- This paper should be cited in our limitations section
- The 28.2% completeness figure is from Tampines (suburban town); Orchard/CBD completeness may be higher
- Suggests OSM is not suitable as a sole POI source — supplementary sources (Google, OneMap) provide better coverage

### 3.2 Novack, Vorbeck & Zipf (2024) — Temporality of OSM Data Contribution Activities

**Citation:** Novack, T., Vorbeck, L., & Zipf, A. (2024). An investigation of the temporality of OpenStreetMap data contribution activities. *International Journal of Digital Earth*, 17(1).

**Context:** HeiGIT (Heidelberg Institute for Geoinformation Technology). Uses the OSHDB framework.

**Method:**
- 12-year time series analysis (2008–2020) across 20 global cities
- Tracked 7 types of OSM data contribution activities: node creation, way creation, relation creation, tag changes, geometry modifications, deletions, and version changes
- Used OSHDB for systematic historical data extraction
- Cities span multiple continents and development levels

**Key findings:**
- OSM data growth follows distinct phases across cities, but no single universal pattern applies to all cities
- Different types of OSM edits (node creation vs. tag changes vs. deletions) have different temporal signatures
- Mapping activity is highly uneven — concentrated in bursts rather than steady growth
- The relationship between mapper count and data completeness varies significantly by city context
- Early mapping phases are dominated by a small number of highly active contributors
- Later phases show more distributed contribution patterns

**Relevance to our project:**
- Confirms that OSM temporal analysis is feasible with the OSHDB/ohsome tools
- The finding that mapping patterns are city-specific means we cannot rely on generalizations from other countries
- Singapore's mapping trajectory should be analyzed independently
- Supports our approach of using aggregate-level analysis (station catchments) rather than per-element tracking

### 3.3 Neis & Zipf (2012) — Contributor Activity Analysis

**Citation:** Neis, P., & Zipf, A. (2012). Analyzing the Contributor Activity of a Volunteered Geographic Information Project — The Case of OpenStreetMap. *ISPRS International Journal of Geo-Information*, 1(2), 146–165.

**Context:** Early foundational paper on OSM contributor behavior.

**Method:**
- Analyzed overall OSM contributor statistics (not Singapore-specific, not POI-specific)
- Extracted user data from OSM API
- Descriptive statistics on registration rates, edit frequency distributions, and contributor lifecycle

**Key findings:**
- Only 38% of registered OSM members had made at least one edit
- Only ~5% were active contributors (regular editing activity)
- Contribution volume follows a heavy-tailed distribution — small number of mappers produce the majority of edits
- Most contributors make very few edits then become inactive

**Relevance to our project:**
- Provides foundational understanding of OSM's contributor dynamics
- The heavy-tailed distribution means mapping quality in any given area depends heavily on whether at least one experienced mapper has surveyed it
- Less directly applicable than Yeow et al. (2021) for our Singapore-specific analysis

### 3.4 Hoong (2020) — OSM Building Data Quality in Singapore

**Citation:** Hoong, C. W. (2020). *Assessing the quality of OpenStreetMap building data in Singapore* [Master's thesis, National University of Singapore]. Available at: ual.sg/publication/2020-osm-sg-building-quality/

**Context:** NUS Urban Analytics Lab (UAL). Focused on building footprints, not POIs, but provides Singapore-specific OSM quality baseline.

**Method:**
- Compared OSM building footprints against official Singapore building data
- Assessed completeness, positional accuracy, shape accuracy, and attribute completeness
- Analyzed correlation between OSM quality and neighborhood socio-economic indicators

**Key findings:**
- Singapore's OSM building data has high completeness (especially for HDB public housing blocks)
- Positional accuracy is good (mean offset ~4m)
- Attribute completeness varies (postal codes ~55%, building levels ~54%)
- Weak correlation between OSM quality and neighborhood socio-economic status — likely because Singapore's government provides high-quality base geodata that OSM mappers can cross-reference

**Relevance to our project:**
- Building quality ≠ POI quality, but the finding that Singapore OSM has reasonable quality for buildings suggests mapper activity is not negligible
- The weak socio-economic bias is notable — contrasts with many global studies that find strong mapping bias toward wealthier areas
- However, Yeow et al. (2021) shows POI completeness is much lower (28%) than building completeness — buildings are easier to map than POIs

### 3.5 Yap et al. (2023) — Urbanity: Network-Based Urban Analysis

**Citation:** Yap, M. Y. et al. (2023). Urbanity: Automated modelling and analysis of multidimensional networks in cities. *Scientific Data* (Nature).

**Context:** NUS Urban Analytics Lab. Urbanity is an open-source Python package for urban morphological analysis.

**What it does:**
- Uses OSM data (via osmnx) to build multidimensional urban networks
- Constructs street networks, building networks, and other spatial networks
- Computes network-based urban morphology indicators (connectivity, accessibility, density, etc.)
- Provides automated urban form classification

**Relevance to our project:**
- Not directly about POI quality or LDA — focused on network morphology
- Uses OSM as its data source, which validates OSM's utility for urban analysis in Singapore
- The package itself is not needed for our POI analysis, but it demonstrates NUS UAL's engagement with OSM data
- May be useful as a supplementary tool for characterizing station catchment areas (street network density, connectivity)

### 3.6 Lan et al. (2022) — Site Selection via GCNN: Singapore Case Study

**Citation:** Lan, T. et al. (2022). Site Selection via Learning Graph Convolutional Neural Networks: A Case Study of Singapore. *Remote Sensing*, 14, 3692.

**Context:** NTU (Nanyang Technological University). The siteselect_sg project.

**What it does:**
- Uses Graph Convolutional Neural Networks (GCNN) for retail site selection in Singapore
- Built a Singapore POI dataset from multiple sources
- The associated siteselect_sg library provides access to ~8,672 POIs across Singapore with Google ratings, place types, and addresses

**Relevance to our project:**
- Demonstrates alternative approaches to understanding urban function via POI data
- The siteselect_sg dataset could supplement OSM POI data for validation purposes
- License restriction: non-commercial research use only (acceptable for our academic project)
- Different methodology (supervised deep learning vs. our unsupervised LDA) — not directly comparable

---

## 4. Singapore-Specific Considerations

### 4.1 Singapore OSM Data Quality

From Hoong (2020) thesis and Yeow et al. (2021):

**Building data (Hoong 2020):**
- High completeness for HDB public housing blocks (~97%)
- Good positional accuracy (mean offset ~4m)
- Attribute completeness varies: postal codes ~55%, building levels ~54%, street names ~50%

**POI data (Yeow et al. 2021):**
- OSM completeness: 28.2% (lowest of 4 sources tested, in Tampines)
- OSM correctness: 58.3%
- OSM overall quality: 37.9% (vs. Google Maps 80.0%)
- Positional accuracy acceptable (median < 50m) for POIs that do exist

**Our Orchard exploration (2026-04):**
- 1,151 total elements in Orchard bbox
- POI key distribution: amenity 588, shop 385, leisure 110, tourism 40, office 19, healthcare 5
- Name coverage: 76.3% — ~24% of POIs lack even a name
- Opening hours: 17.3%
- Version distribution: v1=44%, v2=21%, v3=10% — concentrated at low versions
- 128 unique mappers in Orchard area alone

**Implication:** Building quality is high in Singapore OSM, but POI quality is substantially lower. Our LDA analysis operates on POIs, not buildings, so Yeow et al.'s 28.2% completeness finding is the more relevant benchmark.

### 4.2 URA Master Plan Integration

The Urban Redevelopment Authority (URA) Master Plan is Singapore's statutory land use plan, reviewed every 5 years.

**Available data:**
- **Master Plan 2019**: Approved Nov 18, 2019. Available on `data.gov.sg` as GEOJSON — 25 datasets for "master plan land use", 61 for "land use" overall.
- **MP2019 amendments**: Available as separate datasets on data.gov.sg
- **Master Plan 2025**: Now available on data.gov.sg (superseding MP2019)

**Land use categories in URA MP:**
- Residential, Commercial, Mixed Use, Industrial, Open Space, Institution, Transport, Utilities, Reserve Site, Waterbody, etc.
- More granular than OSM tags, but at the parcel level (not per-building or per-POI)

**Potential integration with Part 2/3:**
- URA MP zoning can serve as ground truth for validating LDA-based function classification
- If LDA assigns "Commercial" to a station in an area zoned "Residential" by URA, this warrants investigation
- Cross-referencing POI evolution with zoning changes (MP2019 → MP2025) could strengthen causal claims
- **Timing mismatch**: MP2019 approved Nov 2019, but implementation happens over years. OSM POI changes may precede or lag official zoning changes.

**Practical approach:**
- Download MP2019 GEOJSON from data.gov.sg
- Spatial join with station buffers (same 500m as POI assignment)
- Compare URA-dominant land use vs LDA-dominant topic per station
- Compute agreement rate — expect some legitimate mismatch (mixed-use zones, transition areas)

### 4.3 Singapore's Mapping Landscape

**Government data:**
- Singapore has excellent government open data via data.gov.sg and URA/SLA portals
- OneMap (SLA) provides authoritative geospatial data
- LTA DataMall provides transport data (already used in Part 1)
- This government data availability may reduce OSM mapper motivation (less "gap filling")

**OSM community in Singapore:**
- Active but small compared to European cities
- Several notable contributors have mapped large portions of the city
- Commercial areas (Orchard, CBD, Marina Bay) are well-mapped
- HDB estates (Ang Mo Kio, Tampines, Woodlands) have variable quality
- Industrial areas (Jurong, Tuas) tend to be sparsely mapped

**Expected bias pattern:**
- Central region > East > North > West > Northeast (rough)
- Tourist/commercial areas > Residential > Industrial
- MRT-adjacent areas better mapped than bus-only areas

---

## 5. Mapping Activity Bias Detection

### 5.1 Intrinsic Quality Indicators

Based on Novack et al. (2024) and Neis & Zipf (2012), the following indicators can help assess mapping activity bias:

**Per-area indicators (computed per 500m station buffer):**
1. **Contributor count**: Number of unique OSM users who have edited POIs in this area. Neis & Zipf (2012) found that a small number of contributors produce most edits — areas with very few contributors may have incomplete mapping.
2. **Element version count**: Average versions per POI. Very low (<1.5) suggests initial import or single-pass mapping. Very high (>5) suggests either active maintenance or disputes.
3. **Edit recency**: Date of most recent edit per POI. Novack et al. (2024) found mapping activity occurs in bursts — stale data (no edits since 2019) may indicate areas mapped in a single pass and never updated.
4. **POI density per km²**: Total POI count / buffer area. Compare across areas — very low density in commercial zones suggests mapping gaps.

**Per-POI indicators (from our Orchard exploration):**
5. **Tag completeness**: Number of tags per element. Well-mapped POIs have 5-15 tags; imports have 2-3.
6. **Name presence**: 76.3% in Orchard exploration. Below 50% suggests poor mapping quality.
7. **Opening hours presence**: 17.3% in Orchard exploration. Low coverage limits time-based analysis.

### 5.2 Detection Methods

**Method 1: ohsome API queries (recommended for Part 2)**
```
POST https://api.ohsome.org/v1/elements/count/groupByBoundary
{
  "bpolys": "<station_buffer_geojson>",
  "filter": "amenity or shop or leisure or tourism",
  "time": "2020-01-01,2022-01-01,2024-01-01,2026-01-01"
}
```
This gives POI counts per station buffer over time — the growth pattern reveals mapping activity vs real change.

**Method 2: Overpass metadata analysis**
```overpass
[out:json][timeout:120];
(
  node["amenity"](1.298,103.828,1.308,1.342);
);
out meta;
```
Returns version, timestamp, changeset, uid, user for each element. From this, compute contributor count, version distribution, and edit recency.

**Method 3: Post-hoc LDA validation**
After running LDA, check if any topics are dominated by rare/incomplete POIs (many with no name, no opening hours, version=1). Such topics may reflect mapping artifacts rather than real urban functions.

### 5.3 Bias Correction Strategies

1. **Minimum quality threshold**: Exclude station buffers with <3 unique contributors or <10 total POIs from LDA. This reduces spatial coverage but improves reliability.

2. **Weighted LDA**: Weight term frequencies by POI quality score (e.g., POIs with name AND opening_hours get weight 2.0, POIs with only one tag get weight 0.5). This downweights poorly-mapped POIs.

3. **Spatial bias acknowledgment**: In the paper, explicitly acknowledge that results are more reliable for central/well-mapped areas. Include a data quality map as a supplementary figure.

4. **URA cross-validation**: Where URA MP land use is available, use it as an external validation of LDA results. Report agreement rate per region.

5. **Stability analysis**: Run LDA with different random seeds and K values. If results are stable across settings, mapping bias is unlikely to be driving the findings.

---

## 6. Recommendations for Our Project

### 6.1 For Part 2 (POI Evolution)

**Recommended approach — Snapshot comparison via Overpass `date:`:**

1. **4 snapshots**: 2020-01-01, 2022-01-01, 2024-01-01, 2026-02-01 (current)
2. **Query**: Same Overpass query for all 8 POI keys, full Singapore bbox
3. **Processing**: For each snapshot, assign POIs to station buffers (same 500m as Part 3), build DTM, run LDA with K=8 (same K as Part 3 for comparability)
4. **Comparison**: Per station, track dominant topic shifts. Aggregate: growth/decline of each topic type across all stations
5. **Bias check**: Use ohsome API to get POI counts per area over same time period. Flag areas with anomalous growth (e.g., >200% increase) that likely reflects mapping surges rather than real change
6. **Cross-validate**: Check POI evolution against known Singapore developments (Tengah, Jurong Lake District, Punggol Digital District)

**Not recommended:**
- Geofabrik full history reconstruction (too complex, marginal benefit over Overpass snapshots)
- Per-element lifecycle tracking (fundamentally unreliable with OSM data)

**Expected outcome:**
- 2-3 figures showing topic evolution (stacked bar charts, spatial panels)
- Written analysis of which urban function types grew/declined and where
- Explicit acknowledgment of OSM mapping bias as a limitation

### 6.2 For Part 3 (LDA Pipeline)

**Data quality checks to integrate into the pipeline:**

1. **Pre-LDA**: Report POI count per station, contributor count (via ohsome or Overpass meta), tag completeness metrics
2. **Vocabulary filtering**: Remove POI classes that appear at <5 stations AND have <50% name coverage (likely mapping artifacts)
3. **Station filtering**: Exclude stations with <3 total POIs OR <3 unique contributors in their buffer
4. **Post-LDA validation**: Check if any topic is dominated by "v1 only" POIs (single-version, never-edited) — these may reflect data imports, not real urban functions

**Critical framing for the paper:**
- Our analysis characterizes the OSM-mapped urban environment around stations, not the complete urban environment
- Yeow et al. (2021) found OSM POI completeness at 28.2% in Tampines — our results should be interpreted in light of this
- The LDA topics reflect patterns in available OSM data, which may underrepresent certain urban functions (e.g., small local businesses, new establishments)

### 6.3 For Part 4 (Opening Hours / Time-of-Day Analysis)

**Feasibility assessment:**
- 17.3% opening_hours coverage in Orchard (the best-mapped area)
- Expected coverage for full Singapore: likely 10-15%
- This is too low for reliable time-based analysis across all stations

**Possible salvage:**
- Restrict time-of-day analysis to well-mapped areas only (Orchard, CBD, Marina Bay) where coverage may reach 25-30%
- Use broad time categories (daytime/evening/24h) rather than hourly granularity
- Clearly label as "exploratory/supplementary" in the paper

**Recommendation**: Include opening_hours investigation in Task #7 as planned. If coverage is below 20% for most stations, deprioritize to "supplementary" status. Time is better spent on strengthening the core LDA analysis.

---

## 7. References

1. Yeow, L. W., Low, R., Tan, Y. X., & Cheah, L. (2021). Point-of-Interest (POI) Data Validation Methods: An Urban Case Study. *ISPRS International Journal of Geo-Information*, 10(11), 735. https://doi.org/10.3390/ijgi10110735
2. Novack, T., Vorbeck, L., & Zipf, A. (2024). An investigation of the temporality of OpenStreetMap data contribution activities. *International Journal of Digital Earth*, 17(1). https://doi.org/10.1080/17538947.2024.2346127
3. Neis, P., & Zipf, A. (2012). Analyzing the Contributor Activity of a Volunteered Geographic Information Project — The Case of OpenStreetMap. *ISPRS International Journal of Geo-Information*, 1(2), 146–165. https://doi.org/10.3390/ijgi1020146
4. Hoong, C. W. (2020). *Assessing the quality of OpenStreetMap building data in Singapore* [Master's thesis, National University of Singapore]. Available at: https://ual.sg/publication/2020-osm-sg-building-quality/
5. Yap, M. Y. et al. (2023). Urbanity: Automated modelling and analysis of multidimensional networks in cities. *Scientific Data* (Nature).
6. Lan, T. et al. (2022). Site Selection via Learning Graph Convolutional Neural Networks: A Case Study of Singapore. *Remote Sensing*, 14, 3692.
7. HeiGIT. ohsome API documentation. https://api.ohsome.org/
8. HeiGIT. ohsome-planet: OSM history in GeoParquet. https://github.com/GIScience/ohsome-planet
9. Geofabrik. Historical data extracts. https://download.geofabrik.de/
