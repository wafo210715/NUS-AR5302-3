# ohsome API Integration Strategy

**Date:** 2026-04-06
**Purpose:** Document how ohsome API and Overpass API are used together in Part 3

## API Split

| Concern | Overpass API | ohsome API |
|---------|-------------|------------|
| **Current POI data** | Yes — returns individual elements with tags, coordinates, metadata | No — returns only counts, not elements |
| **Per-station quality metrics** | Yes — download all POIs with `out meta`, compute metrics locally | No — cannot do per-element analysis |
| **Yearly snapshots for LDA** | Yes — `date:` parameter returns full POI list at specific date | No — `/elements/count` returns counts only, not element lists |
| **POI growth curve over time** | Impractical — one query per date, no aggregation | Yes — single request returns full time series |
| **Unique mapper count over time** | Cannot — no contributor aggregation | Yes — `/users/count` with time range |
| **Create/update/delete rates** | Cannot — no edit type classification | Yes — `/contributions/count` tracks edit types |

## What ohsome Provides (Aggregate Numbers Only)

1. **POI count evolution** (`/elements/count`): Monthly POI counts for Singapore 2020-2026. Tells us if OSM is in growth phase or saturation.
2. **Mapper activity** (`/users/count`): Unique contributors over time. More mappers = better data quality.
3. **Edit type breakdown** (`/contributions/count`): Create vs update vs delete rates. High creation rate = dataset still being built out.

## How ohsome Cross-References Overpass

ohsome numbers provide **interpretive context** for Overpass results:
- If ohsome shows steep POI growth → snapshot comparisons may reflect mapping effort, not real change
- If ohsome shows stable mapper count → data quality is unlikely to change significantly between snapshots
- If ohsome shows high creation rate → newer POIs may be less reliable (single mapper, v1)

These insights feed into the limitations discussion and data quality caveats.

## ohsome API Details

- **Base URL:** `https://api.ohsome.org/v1/`
- **Method:** POST with JSON body
- **Key parameters:** `filter` (OSM tag filter), `bboxes` (bounding box), `time` (ISO-8601 range)
- **Rate limits:** Free tier available; we only need 3 nationwide queries so limits are not a concern
- **Authentication:** May require API key — check on first run

## References

- ohsome API documentation: https://api.ohsome.org/
- OSHDB GitHub: https://github.com/GIScience/oshdb
- ohsome-planet (GeoParquet): https://github.com/GIScience/ohsome-planet
