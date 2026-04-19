# Beyond the Campus

**How University Communities Travel Through Singapore's Urban Fabric**

AR5302 Assignment 3 — National University of Singapore

## Research Question

How do travel patterns differ across university communities, and what characteristics define the destinations they frequent?

## Universities

NUS (Kent Ridge), NTU, SMU (Bras Basah), SUTD (Tampines)

## Pipeline

1. **Station identification** — 83 transit stations within 100 m of 4 campuses
2. **Urban function classification** — Overture Maps POI → LDA topic modelling (K = 5) → station-level functional labels
3. **Temporal analysis** — Monthly OD trip volumes across academic calendar periods (Aug 2024 – Jul 2025)
4. **Comparative analysis** — Chi-square tests, Jaccard similarity, topic residuals, destination flow mapping

## Key Findings

- Geographic context, not institutional type, differentiates travel behaviour across the four university communities.
- NTU is the most spatially concentrated (73% of trips from 2 stations) and functionally isolated (67.8% topic coverage).
- SMU and SUTD share the most similar destination profiles (Jaccard = 0.888), driven by proximity within eastern Singapore.
- Destination urban functions remain stable across semester, exam, and vacation periods — geography's influence persists year-round.

## Scripts

| Script | Purpose |
|---|---|
| `part1_identify_stations.Rmd` | Station mapping (100 m buffer) |
| `part2_poi_lda_yk.Rmd` | LDA topic modelling on Overture POI |
| `part3_temporal_od_ari.Rmd` | Temporal OD analysis by academic period |
| `part4_comparative.Rmd` | Inter-university comparison |
| `make_destination_flow_map.R` | Destination flow visualisation |

## Setup

```bash
# Python dependencies
uv sync

# R packages (in R console)
install.packages(c(
  "tidyverse", "lubridate", "patchwork", "scales",
  "sf", "terra", "geosphere", "ggalluvial",
  "topicmodels", "tm", "Matrix",
  "fmsb", "viridis", "jsonlite", "knitr"
))
```

## Data Sources

- **Overture Maps Foundation** — POI data via Source Cooperative
- **LTA Singapore** — Origin-Destination trip data (Jan 2020 – Feb 2026), bus stops, MRT exits
