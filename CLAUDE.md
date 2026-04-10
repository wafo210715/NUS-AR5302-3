# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project: Beyond the Campus

## Research Question
How do travel patterns differ across university communities, and what characteristics define the destinations they frequent?

## Scope (v2)
- **4 universities**: NUS (Kent Ridge), NTU, SMU (Bras Basah), SUTD (Tampines)
- **Time period**: Aug 2024 – Jul 2025 (one school year, AY2024-25)
- **POI data**: Overture Maps Foundation (via Source Cooperative historical archive)
- **OD data**: Singapore LTA Origin-Destination data (74 months available, focus on 12 months)

## Data Sources
- **Overture Maps POI**: Downloaded from Source Cooperative (`source.coop/fused/overture`), GeoParquet format. 12 monthly snapshots available for Aug 2024 – Dec 2025.
- **LTA OD data**: 74 months (Jan 2020 – Feb 2026), shared via Google Drive. NOT in repo.
- **LTA bus stop coordinates**: `data/LTABusStop.geojson` (5,166 stops) — in shared folder
- **LTA MRT station exits**: `data/LTAMRTStationExitGEOJSON.geojson` (597 exits) — in shared folder
- **Campus boundaries**: `smu_boundary.geojson`, `sutd_boundary.geojson` — in shared folder
- **Shared data location**: `C:/0_Files/NUS/Course/R_Projects/Assignment_3/Data/` (read-only, NOT in repo)
- Each member must obtain data independently; never commit data files

## Python Setup
Run `uv sync` in project root before executing Python scripts. Key dependencies:
- `duckdb`, `s3fs` — Overture data access
- `gensim` — topic coherence calculation
- `geopandas`, `osmnx`, `matplotlib` — spatial analysis and visualization

## File Structure
```
scripts/
  report.Rmd                  # Main shared report
  part1_identify_stations.Rmd # Station identification (4 universities)
  part3_poi_lda_yk.Rmd        # LDA urban function analysis (Overture POI)
utils/
  download_overture_pois.py   # Overture POI downloader
  download_od_data.py         # OD data downloader
  download_geospatial_data.py # Campus boundary downloader
  calculate_topic_coherence_gensim.py
  visualize_k_selection.py
  export_lda_beta.R
data/                         # DO NOT COMMIT — gitignored
  OD_Data/                    # Raw OD data (74 months)
  od_subset/                  # Filtered OD for 4 universities
  node_subset/                # Tap-in/tap-out data
  overture_pois/              # Overture POI snapshots (TBD)
docs/
  workload_plan.md            # Pipeline and task division
  todo.md                     # Task tracking
  info.md                     # Data lineage and conventions
  paper_synthesis.md          # Literature review notes
figures/                      # Auto-generated (gitignored)
```

## Pipeline Overview
1. **Part 1 (DONE)**: Station mapping — 83 stations near 4 campuses (100m buffer). See `docs/part1_handoff.md`.
2. **Part 2**: Urban function identification — Overture POI → LDA topic modeling → station classification
3. **Part 3**: Temporal patterns — monthly OD analysis, semester/vacation comparison, intra-day patterns
4. **Part 4**: Comparative analysis — inter-university comparison of travel patterns and destination functions
5. **Part 5**: Paper assembly

### Visualization Checkpoints
Each pipeline step should produce a visible output figure:
- CP1: Station mapping map (4 campuses + stations)
- CP2: Overture POI quality (density heatmap, category distribution)
- CP3: OD extraction validation (monthly trip volumes)
- CP4: LDA K selection (coherence plot)
- CP5: Station classification map (urban functions)
- CP6: Temporal patterns (semester/exam/vacation shading)
- CP7: Comparative analysis (radar, Sankey)

## Code Style (R)
- Use tidyverse style (pipes `%>%`, consistent naming)
- Use meaningful variable names (no single letters except `i` in loops)
- Add comments for non-obvious logic
- Keep code chunks focused (one chunk = one logical step)
- Use chunk labels: `{r part1-load-data}`, `{r part2-hourly-plot}`, etc.
- Set `message=FALSE, warning=FALSE` on all chunks
- Hide code in final output where appropriate: `echo=FALSE` for data loading, `echo=TRUE` for analysis

## Code Style (Python)
- Use `uv run python script.py` to run scripts
- Follow PEP 8 naming conventions
- Keep scripts modular: one script = one clear purpose
- Save outputs to `data/` (data files) or `figures/` (visualizations)

## Terminology (IMPORTANT)
- Use "university community" — NOT "students" (data includes staff, visitors, residents)
- Use "travel to" — NOT "seek" or "activate"
- Use "suggest" or "indicate" — NOT "reveal"
- Use "travel" — NOT "play" or "leisure"

## Figure Guidelines
- Use ggplot2 for R figures, matplotlib for Python
- Include axis labels, titles, and legends
- Use clear fonts (min 10pt for labels)
- Set consistent figure size: `fig.width=8, fig.height=5`

## Git Rules
- NEVER commit data files (CSV, JSON, parquet, etc.)
- NEVER commit files larger than 10MB
- NEVER force push
- Use descriptive commit messages: "Part 1: add SMU/SUTD station mapping"
- Work on feature branches (e.g. `szh`)
- If stuck on a merge conflict, ask the group chat immediately

## Project Documentation
- `docs/part1_handoff.md` — Part 1 output details and handoff for downstream parts
- `docs/todo.md` — task tracking and pending items
- `docs/workload_plan.md` — pipeline division and timeline
- `docs/info.md` — data lineage, naming conventions, file flow
- `docs/paper_synthesis.md` — literature review and methodology notes

## Key Data Path Convention
- **Read** source data from shared folder: `C:/0_Files/NUS/Course/R_Projects/Assignment_3/Data/`
- **Write** output CSVs to repo `data/` directory (gitignored, but local to each member's clone)

## Coordination
- Ask questions in the group chat before making assumptions
- Announce in the group chat when you're about to push changes
