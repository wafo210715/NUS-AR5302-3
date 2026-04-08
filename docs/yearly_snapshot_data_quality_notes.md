# Yearly Snapshot Data Quality Considerations

**Created:** 2026-04-08
**Purpose:** Document OSM data quality considerations for Part 2 (Yearly POI Evolution Analysis)

---

## Overview

Part 2 uses Overpass API's `date:` parameter to obtain historical POI snapshots at different time points. This document outlines the data quality limitations and how to interpret temporal changes correctly.

---

## 1. OSM Historical Data Limitations

### 1.1 No Element Metadata in Historical Queries

**Issue:** When using Overpass `date:` parameter to query historical OSM data, element metadata (version, timestamp, user_id, changeset) is **NOT available**.

**What you get:**
- POI state at the specified date (tags, coordinates)
- Element ID and type

**What you DON'T get:**
- Version number (how many times the POI has been edited)
- Creation timestamp
- Last editor information
- Edit history

**Implication:** Cannot compute per-snapshot quality metrics (version distribution, mapper activity) for historical data. Quality assessment is only possible for current state.

### 1.2 Snapshot Changes Reflect Multiple Factors

When comparing snapshots across years, observed changes may be due to:

1. **Real urban change** — New businesses opening, businesses closing, land use change
2. **Mapping effort** — Increased OSM contributor activity adding previously unmapped POIs
3. **Data cleanup** - Contributors correcting errors, standardizing tags, removing duplicates

**Without mapper activity data for each snapshot, it's difficult to distinguish these factors.**

---

## 2. Quality Baseline from Current Data Analysis

Based on ohsome API analysis of current OSM data (2020-2026):

### 2.1 POI Count Growth

| Metric | Value |
|--------|-------|
| Starting (Jan 2020) | 30,555 POIs |
| Ending (Feb 2026) | 55,995 POIs |
| Total Growth | +83.3% |
| CAGR | ~10% per year |

**Interpretation:** The dataset nearly doubled in size over 6 years. This reflects both:
- Real business growth in Singapore
- Increased mapping effort as OSM gains popularity

### 2.2 Mapper Activity

| Metric | Value |
|--------|-------|
| Mean active mappers | 56/month |
| Peak activity | 99 mappers (Jan 2020) |
| Low activity | 37 mappers (Dec 2023) |
| Stability | Moderate (std dev = 10.8) |

**Key observation:** Mapper activity is relatively stable with no dramatic trends. This suggests:
- 2020-2026 period does NOT have extreme mapping surges
- Snapshot comparisons are reasonably reliable
- Changes are more likely to reflect real urban change than mapping artifacts

### 2.3 Edit Volume

| Metric | Value |
|--------|-------|
| Mean edits/month | 1,216 |
| Peak | 4,446 (May 2023) |
| Total (2020-2026) | 88,734 edits |

**Notable spikes:**
- May 2023: 4,446 edits (3.7x mean) — Possible mapping campaign or data import
- June 2023: 4,446 edits — Continued high activity

**Implication for yearly snapshots:** If using 2023 as a snapshot point, be aware that this period had unusually high edit activity.

---

## 3. Recommendations for Part 2 Analysis

### 3.1 Snapshot Selection Strategy

**Recommended snapshot years:**
- 2020, 2022, 2024, 2026 (even years, ~2-year intervals)

**Rationale:**
- Avoids 2023 spike period
- Provides sufficient temporal separation to observe change
- Covers period of stable mapper activity

**Alternative:**
- 2021, 2023, 2025 (odd years) — but 2023 data may be less reliable due to spike

### 3.2 Interpreting Temporal Changes

When comparing POI evolution across snapshots:

1. **Cross-reference with ohsome activity curves**
   - Periods with high mapper growth → snapshot changes may overstate real change
   - Periods with stable mapper count → snapshot changes more reliable

2. **Focus on stable-mapping periods**
   - 2020-2022: Stable activity (~50-60 mappers)
   - 2024-2026: Stable activity (~55-65 mappers)
   - These periods provide more reliable urban change signals

3. **Qualify findings appropriately**
   - Use language like "OSM-mapped urban environment" rather than definitive "urban functions"
   - Acknowledge that changes reflect both real change and mapping effort
   - Cite ohsome analysis to support interpretation

### 3.3 Validation Checks

**Before drawing conclusions:**

1. **Check POI count changes per snapshot**
   - Sudden jumps (>20% YoY) may indicate mapping surges, not real change
   - Gradual growth more likely reflects real urban change

2. **Validate against known events**
   - Major development announcements (e.g., Tengah new town)
   - MRT line openings (e.g., TEL stages)
   - Do observed POI changes align with these events?

3. **Compare with official data**
   - URA planning reports
   - SingStat business establishment data
   - Do trends align?

---

## 4. Data Quality Flags for Part 2

### 4.1 Period-Specific Considerations

| Period | Mapper Activity | Data Quality | Notes |
|--------|----------------|--------------|-------|
| 2020-2021 | Moderate (40-70) | Good | Early COVID period, some business closures |
| 2021-2022 | Stable (~50-60) | Very Good | Baseline period |
| 2022-2023 | Variable (40-80) | Moderate | Mid-2022 spike, use with caution |
| 2023-2024 | Spike (4,446 edits May 2023) | Lower | High edit volume may introduce bias |
| 2024-2026 | Stable (~55-65) | Good | Recent period, reliable |

### 4.2 Functional Area-Specific Considerations

Based on Part 3 POI coverage validation:

- **Commercial areas (Orchard, CBD, Marina Bay):** High POI density, well-mapped
  - Snapshot changes here are more reliable
  - Good for studying commercial evolution

- **Residential areas (HDB towns):** Moderate POI density, stable
  - Changes reflect real urban development

- **Industrial areas:** Lower POI density, sparser mapping
  - Snapshot changes may be less reliable
  - Consider excluding or flagging

---

## 5. Methodology Recommendations

### 5.1 Handling Mapping Bias in LDA Comparisons

When running LDA on each snapshot's POI data:

1. **Use consistent preprocessing**
   - Same vocabulary filtering thresholds (<5 stations, >90% stations)
   - Same station filtering (≥3 POIs)
   - Same LDA parameters (alpha=0.1, 2000 iterations)

2. **Track vocabulary changes**
   - Document which POI classes appear/disappear across snapshots
   - New classes may reflect either real change or new mapping conventions

3. **Compare topic distributions carefully**
   - Use Jensen-Shannon divergence or similar metric for topic similarity
   - Direct label comparison may be misleading (Topic 1 in 2020 ≠ Topic 1 in 2022)

### 5.2 Reporting Template

For each snapshot comparison, report:

```markdown
## [Year A] to [Year B] Comparison

**Data Quality Context:**
- POI count change: [X] → [Y] ([Z]% growth)
- Mapper activity: [stable/increasing/decreasing]
- Edit volume: [low/normal/spike period]

**Observed Changes:**
- New POI classes added: [N]
- POI classes removed: [N]
- Top gainers: [list]
- Top losers: [list]

**Topic Evolution:**
- Topic similarity (JSD): [value]
- Dominant topic changes: [description]
- Notable spatial patterns: [description]

**Interpretation:**
- [Cautiously/Strongly] suggests [urban change trend]
- Qualifiers: [mapping effort bias, data limitations]
```

---

## 6. Key Takeaways

1. **OSM completeness is ~28%** (Yeow et al. 2021) — frame results as "OSM-mapped urban environment"

2. **Mapper activity was relatively stable 2020-2026** — except for May 2023 spike, snapshot comparisons are reasonably reliable

3. **POI count growth (+83%) reflects both real change and mapping effort** — use ohsome data to distinguish

4. **2023 data requires caution** — high edit volume may introduce bias

5. **Qualify all findings** — use tentative language, acknowledge limitations

---

## References

- Yeow et al. (2021). "Assessing the completeness of Points of Interest in OpenStreetMap: A case study in Tampines, Singapore." *IJGI* 10(11), 735.
- ohsome API analysis results: `data/ohsome_quality_results.json`
- Temporal quality summary: `data/temporal_quality_summary.json`
