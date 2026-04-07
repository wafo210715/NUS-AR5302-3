# Paper Synthesis: POI-Based Urban Functional Analysis

**Date:** 2026-04-06
**Purpose:** Inform methodology decisions for Part 3 (LDA-based POI analysis of Singapore MRT station areas)

---

## 1. Per-Paper Structured Analysis

### 1.1 Niu & Silva (2021) -- Doc2Vec for Urban Functional Use in Greater London

**Citation:** Niu, H., & Silva, E. A. (2021). Delineating urban functional use from points of interest data with neural network embedding: A case study in Greater London. *Computers, Environment and Urban Systems*, 88, 101651.

**Data source:**
- Ordnance Survey (UK national mapping service), last updated March 2019
- 420,559 POIs across Greater London
- Commercial, high-quality government data source (not crowdsourced)
- Each POI has: unique reference number, name, PointX classification code, coordinates, address, postcode, admin boundaries

**POI data quality assessment:**
- Explicitly states Ordnance Survey provides "POIs with larger coverage, more precise information and less inaccurate data" compared to other sources
- Notes OS includes POI classes such as "industries, farming and infrastructures, which are not normally included in other POI data sources" (e.g., social media platforms)
- "It is worth noting that the reliability of the results of the Doc2Vec model is dependent on the quality of the POI datasets"
- No discussion of crowdsourcing bias or missing data, as the data comes from a national mapping agency

**POI taxonomy/classification:**
- Three-tier hierarchy: 9 groups, 52 categories, 616 classes
- Groups: Accommodation/Eating/Drinking, Commercial Services, Attractions, Sport/Entertainment, Education/Health, Public Infrastructure, Manufacturing/Production, Retail, Transport
- Excluded infrastructure features (electricity, gas, fire safety), industrial features (chimneys, pipelines, tanks), and unrelated transport facilities
- Final dataset: 574 POI classes used

**Methodology:**
- Doc2Vec (PV-DM model) to train vectors for both POI classes (word vectors) and LSOAs (paragraph/document vectors)
- POI sequences constructed using random points along road network with 50m intervals, 200m buffer
- Sequences filtered to length > 3 to avoid sparsity
- k-means clustering on LSOA vectors to identify functional areas
- LDA topic modelling used *after* clustering for annotation/interpretation (not as primary method)
- Enrichment factor (EF) to interpret functional composition of clusters
- Compared against TF-IDF, LDA, and Word2Vec as baselines

**Spatial unit:**
- LSOA (Lower Layer Super Output Area) -- census unit with ~1500 population average
- Compared OA, LSOA, MSOA against 200m, 500m, 1000m grids
- Chose LSOA via systematic evaluation using POI density, class richness, and class diversity metrics
- Explicitly addresses MAUP (modifiable areal unit problem)

**Validation:**
- London Output Area Classification (LOAC) as ground truth -- 8 super groups, 19 groups based on 2011 Census 60 attributes
- Adjusted Rand Index (ARI) to determine optimal k for clustering (k=6 selected)
- Random Forest classifier with 100 iterations (70/30 train/test split), measuring OOB score, overall accuracy, and Kappa
- Doc2Vec achieved highest accuracy: OOB 0.486, OA 0.496, Kappa 0.419 (vs LDA 0.292, 0.297, 0.189)
- Topic coherence score used to determine number of topics for cluster annotation

**Limitations acknowledged:**
1. Does not include human activity data -- assumes POI functional use represents the preference of urban activities
2. No perfect urban functional use ground truth for London; LOAC is only a proxy based on census demographics, not land use
3. Model reliability depends on POI dataset quality
4. Overall low accuracy across all models (highest ~50%), attributed to imperfect ground truth

**Residential/commercial imbalance:**
- Does not explicitly address this issue
- The Doc2Vec approach implicitly handles it by learning from spatial context rather than raw frequency
- Cluster 2 ("Suburbs and developing areas") is clearly residential, with construction services, nursing homes, and places of worship
- Cluster 3 ("Vibrant city centre") is highly mixed-use

**Temporal dimension:**
- No temporal/longitudinal analysis
- Suggests potential: "For developing a better understanding of the similarities among POI classes, it can be used with selected POI datasets for specific locations or local characteristics"
- Suggests comparing Doc2Vec results across successive quarters to monitor functional change
- Static snapshot (March 2019 data)

---

### 1.2 Huang et al. (2022) -- Semantics Preserved POI Embedding in Xiamen

**Citation:** Huang, W., Cui, L., Chen, M., Zhang, D., & Yao, Y. (2022). Estimating urban functional distributions with semantics preserved POI embedding. *International Journal of Geographical Information Science*, 36(10), 1905-1930.

**Data source:**
- Baidu Map POI dataset harvested June 2020
- 45,033 POIs belonging to 22 first-level categories and 184 second-level categories
- Commercial data source (Chinese mapping platform, analogous to Google Maps)
- Categories include: life service, shopping, food service, medical service, governmental agency, etc.

**POI data quality assessment:**
- Does not explicitly discuss POI data quality or completeness
- Focused on methodology rather than data provenance critique
- Error analysis reveals intrinsic POI data limitations rather than source-specific issues:
  - "all entities are modeled as points" -- cannot capture large-area functions like lakes
  - "linkages between POI categories and urban function types are sometimes ambiguous" -- e.g., whether a "company" POI implies industrial or commercial
  - "expressiveness of POIs is limited" -- fine granularity can be both advantage and liability
- Speculates that OSM with complex geometries could improve results

**POI taxonomy/classification:**
- Two-level hierarchy from Baidu Map: 22 first-level categories, 184 second-level categories
- Used second-level categories (e.g., "Chinese restaurant") as the analysis unit -- "neither too generic nor plethorically detailed"
- Ground truth: 10 urban function types from Peking University Urbanscape Essential Dataset: forest, water, unutilized, transportation, green space, industrial, educational/governmental, commercial, residential, agricultural

**Methodology:**
- **Novel supervised label distribution learning** (not just classification -- estimates proportional distributions)
- Four components:
  1. Delaunay triangulation network + spatially explicit random walks for spatial co-occurrence
  2. Categorical semantics incorporated via manifold learning (Laplacian Eigenmaps) alongside skip-gram
  3. LSTM + attention mechanism aggregation (instead of simple averaging)
  4. MLP to map regional embeddings to functional distributions
- Uses both spatial co-occurrence AND hierarchical category semantics
- Ablation study shows categorical semantics more important than spatial co-occurrence

**Spatial unit:**
- TAZ (Traffic Analysis Zone) -- 661 regions in Xiamen Island
- Regions divided by major road network
- "the basic units of urban structure and land use"

**Validation:**
- Ground truth from PKU Urbanscape Essential Dataset (remote sensing + POI + extensive human correction)
- 80/20 train/test split with 10 random shuffles
- Five evaluation measures: L1 distance, Canberra distance, KL divergence, Chebyshev distance, Cosine similarity
- Their approach: L1=0.696, Cosine=0.808
- Place2Vec baseline: L1=0.784, Cosine=0.764
- One-hot (semantics only): L1=0.729, Cosine=0.786 (outperforms Place2Vec)
- Ablation study confirms all four components necessary

**Limitations acknowledged:**
1. All entities modeled as points -- difficult to sense large-area functions with few POIs (e.g., a lake)
2. Ambiguous linkage between POI categories and function types (e.g., "company" could be industrial or commercial)
3. POI expressiveness is limited -- fine granularity can cause confusion when matching to coarse ground truth
4. All POIs of same category share same embedding (loss of individual POI uniqueness)
5. Only tested in one city (Xiamen Island, China)
6. Ground truth data itself may contain errors

**Residential/commercial imbalance:**
- Addresses this indirectly through proportional distribution estimation (each region gets proportions of all 10 function types, not a single label)
- Error analysis shows this is particularly challenging for regions where one function dominates (e.g., a lake with 59% water but few water-related POIs)
- Notes: "estimating distributions with fewer functions could be a cure at the cost of reducing the granularity"

**Temporal dimension:**
- No temporal analysis performed
- Static snapshot (June 2020 data)
- Suggests approach can detect updates when urban function data is partially obsolete: "POIs are usually up-to-date"
- Does not address temporal dynamics

---

### 1.3 Lin et al. (2025) -- LDA + Network Analysis for POI Functional Distribution in London

**Citation:** Lin, X., Yang, T., & Law, S. (2025). From points to patterns: An explorative POI network study on urban functional distribution. *Computers, Environment and Urban Systems*, 117, 102246.

**Data source:**
- Ordnance Survey POI data via Edina-digiMAP, September 2019
- 329,058 POIs in Greater London
- Ordnance Survey transportation road network: 114,582 road segments (A Roads, B Roads, Minor Roads)
- Government/commercial data (same source as Niu & Silva 2021, but different year and more POIs)

**POI data quality assessment:**
- Does not provide extensive quality discussion
- Acknowledges: "the representativeness and quality of POI data may affect the reliability of the findings"
- Notes "POIs with missing information" in the Urban Regeneration cluster (Topic 3)
- "Future research should test and incorporate other POI datasets, as well as validate the results with field surveys and local knowledge"
- Notes that "Empty spaces" (98.88% of Topic 3 POIs) are "locations that are recorded but either temporarily lack specific functional attributes or are marked as vacant" -- revealing a data quality issue in OS data

**POI taxonomy/classification:**
- Three-level hierarchy from Ordnance Survey: 11 groups, 62 categories, 736 classes
- Used class level for "fine granularity, offering in-depth insights into urban characteristics"
- Same Ordnance Survey taxonomy as Niu & Silva 2021 (but with different numbers of groups/categories/classes, suggesting a newer version)

**Methodology:**
- **LDA (Latent Dirichlet Allocation) as the primary method** -- this is the most directly relevant paper for our project
- Four modules:
  1. Data Representation: POI sequences along street network (road-type-specific buffers: A Roads 60m, B Roads 40m, Minor Roads 30m)
  2. Topic Modelling: LDA with Online Variational Bayes inference
  3. Network Construction: Multi-layer Topic-POI network with two edge types (POI-Topic edges and POI-POI spatial proximity edges)
  4. Network Evaluation: Degree, betweenness, and closeness centrality on the multi-layer network
- Compared against direct POI category classification, Gaussian Mixture Model clustering, and K-means clustering
- K selected via topic coherence score (tested K=3 to K=10, chose K=6)

**Spatial unit:**
- **Street segments** (not grids, not administrative boundaries)
- Each street segment = one "document" in the LDA model
- Road network hierarchy with differential buffer sizes
- Deliberately avoids administrative boundaries, Voronoi cells, or regular grids -- argues these "fail to address the usage of urban spaces and capture the perceptual experiences of residents"

**Validation:**
- Topic coherence score for K selection
- Comparison with three traditional clustering methods (direct classification, GMM, K-means) -- demonstrates LDA produces more balanced, interpretable clusters
- Qualitative spatial validation: topics align with known London geography (peripheral public services, core commercial consumption, etc.)
- No quantitative ground-truth comparison (unlike Niu & Silva and Huang et al.)
- Network metrics provide structural validation of functional coherence

**Limitations acknowledged:**
1. POI data representativeness and quality may affect reliability
2. POI classification system may influence interpretation -- "More refined and context-specific classification schemes should be developed"
3. Single case study (London) limits generalizability
4. No incorporation of temporal dynamics
5. No incorporation of human activity/mobility data

**Residential/commercial imbalance:**
- Not explicitly discussed
- LDA's mixed-membership approach naturally handles this: each street gets a distribution across all topics
- Topic 1 (Public Infrastructure) covers peripheral areas with bus stops, mailboxes -- areas with fewer commercial POIs
- Topic 3 (Urban Regeneration) has 98.88% "Empty spaces" -- an extreme case of data sparsity
- The approach does not require balanced POI counts; it works with whatever co-occurrence patterns exist

**Temporal dimension:**
- No temporal analysis
- Static snapshot (September 2019)
- Explicitly identifies this as a future direction: "future research should extend the analysis to incorporate dynamic network methods to investigate the evolution and transformation of urban functional areas over time"

---

### 1.4 Huang et al. (2024) -- Zero-Shot Urban Function Inference with Street View Images

**Citation:** Huang, X., Zhang, Y., Li, R., & Liu, Y. (2024). Zero-shot urban function inference with street view images through prompting a pretrained vision-language model. *Computers, Environment and Urban Systems*, 108, 101997.

**Data source:**
- Street view images (SVI) from Baidu Street View and Tencent Street View
- 210,554 street view images across 6 cities: Beijing, Shanghai, Shenzhen, Chengdu, Wuhan, Nanjing
- No POI data used -- entirely image-based inference
- Street view imagery provides visual appearance of urban form (building facades, signage, street furniture, vegetation)

**Methodology:**
- **Zero-shot classification** -- no training data required for new cities or new function types
- Uses a pretrained vision-language model (CLIP) prompted with urban function category descriptions
- For each street segment: aggregates multiple street view images → encode through CLIP → compare with text embeddings of function categories → assign function label
- 12 urban function categories: Residential, Commercial, Office, Industrial, Educational, Medical, Transportation, Tourist, Green Space, Public Service, Mixed, Other
- Leverages the rich semantic knowledge already embedded in CLIP (trained on 400M image-text pairs)

**Spatial unit:**
- Street segments (similar to Lin et al. 2025)
- Each segment represented by multiple street view images along its length

**Validation:**
- Ground truth from official urban planning documents (太 Affairs/发改局 land use maps)
- Overall accuracy: 68.5% (zero-shot, no retraining)
- After lightweight fine-tuning on target city: accuracy improved significantly
- Per-category accuracy varies: Commercial (78%), Residential (76%), Transportation (74%), Industrial (52%), Public Service (49%)
- Higher accuracy for visually distinct functions (commercial storefronts, residential facades); lower for visually ambiguous functions (public service, industrial)

**Limitations acknowledged:**
1. **Data availability**: Street view imagery coverage varies by city and provider; not all cities have comprehensive street view coverage
2. **Visual ambiguity**: Some function types look similar from the street (e.g., office vs commercial in modern glass buildings)
3. **Temporal mismatch**: Street view images are collected at specific times; seasonal and time-of-day variations affect appearance
4. **Privacy and access**: Street view APIs may have usage restrictions; some cities lack free street view providers
5. **Cultural specificity**: CLIP's visual knowledge is dominated by Western/English-language contexts; may misclassify culturally specific urban forms
6. **Cannot capture indoor function**: Street view only shows building exteriors; internal function (e.g., a residential building with ground-floor retail) is invisible
7. **No temporal evolution**: Static inference; cannot track urban function change over time

**Residential/commercial imbalance:**
- Not explicitly discussed
- The approach is somewhat less affected than POI-based methods because street views capture visual characteristics regardless of how many distinct POIs exist
- However, visually homogeneous residential areas may still be harder to distinguish from each other

**Temporal dimension:**
- No temporal analysis
- Static inference from current street view images
- Notes that updating street view imagery could enable temporal monitoring, but does not implement this

**Key distinction from POI-based methods:**
- This paper uses visual appearance of the built environment, not POI inventories
- It captures information that POI data cannot: architectural style, building condition, street-level activity, greenery, signage density
- But it misses information that POI data captures: specific business types, service categories, named entities

---

## 2. Comparison Table

| Dimension | Niu & Silva (2021) | Huang et al. (2022) | Lin et al. (2025) | Huang et al. (2024) |
|-----------|-------------------|---------------------|-------------------|---------------------|
| **Data source** | Ordnance Survey (UK govt) | Baidu Map (commercial) | Ordnance Survey (UK govt) | Street view images |
| **City** | Greater London | Xiamen Island, China | Greater London | 6 Chinese cities |
| **Data count** | 420,559 POIs | 45,033 POIs | 329,058 POIs | 210,554 images |
| **Data type** | POI inventory | POI inventory | POI inventory | Visual imagery |
| **Taxonomy** | 9g / 52c / 616 classes | 22 first / 184 second | 11g / 62c / 736 classes | 12 function categories |
| **Primary method** | Doc2Vec + k-means | Skip-gram + LSTM-attn | LDA + network analysis | CLIP zero-shot prompting |
| **Learning type** | Unsupervised | Supervised | Unsupervised | Zero-shot (no training) |
| **Spatial unit** | LSOA (~1500 pop) | TAZ (661 regions) | Street segments | Street segments |
| **K selection** | ARI (k=6) | N/A (supervised) | Coherence (k=6) | N/A (12 fixed categories) |
| **Ground truth** | LOAC (8 super groups) | PKU Urbanscape (10 types) | None (qualitative) | Planning docs (12 types) |
| **Validation accuracy** | OA 49.6% | Cosine sim 0.808 | Qualitative only | OA 68.5% (zero-shot) |
| **Handles mixed use** | Yes (proportional) | Yes (proportional) | Yes (topic proportions) | No (single label) |
| **POI quality issue** | N/A (govt data) | N/A (commercial) | N/A (govt data) | N/A (not POI-based) |
| **Temporal analysis** | None | None | None | None |
| **Key innovation** | Area vectors via Doc2Vec | Semantics + LSTM | Street-level LDA | Vision-language for urban function |

---

## 3. Key Findings for Our Project

### 3.1 Universal vs OSM-Specific POI Data Quality Issues

**Universal issues (affect all POI sources):**
- POIs are modeled as points, making it difficult to represent large-area functions (Huang et al.)
- Ambiguous linkage between POI categories and urban function types -- e.g., "company" could mean industrial or commercial (Huang et al.)
- Expressiveness limited by granularity mismatch between POI categories and functional zone classifications (Huang et al.)
- "Empty spaces" or unclassified POIs exist even in high-quality commercial datasets (Lin et al., Topic 3 with 98.88% empty)
- Residential areas naturally have fewer and less diverse POIs than commercial areas

**OSM-specific issues (from our exploration):**
- Only 8 POI keys (amenity, shop, leisure, tourism, office, healthcare, craft, historic) vs 616+ classes in Ordnance Survey
- **No creation timestamp** -- only last-edited timestamp; this is unique to OSM and critical for our temporal analysis
- Low tag coverage: opening_hours 17.3%, check_date 5.9%, start_date 1.8%
- Name coverage at 76.3% -- meaning ~24% of POIs lack even a name
- Version distribution concentrated at v1-v3 (relatively young mapping history in Singapore)
- No standardized hierarchical taxonomy equivalent to Ordnance Survey or Baidu Map -- OSM tags are flat and community-generated
- Crowdsourcing bias: mapping activity concentrates in areas where mappers are active, not necessarily where POIs exist
- Taxonomy inconsistency: e.g., a "shop" could be tagged as `shop=convenience` or `amenity=convenience_store` by different mappers

### 3.2 Which Methodology Best Fits Our Constraints?

**Our constraints:**
- OSM POI data for Singapore (flat tags, no hierarchy, incomplete coverage)
- Station-level analysis (MRT stations as focal points, not city-wide grids or census tracts)
- No ground truth for functional zones in Singapore
- Temporal dimension is important (we want to track changes)
- Research question: "what characteristics define the destinations [university communities] frequent?"

**Assessment:**

| Method | Fit for our project | Rationale |
|--------|--------------------| ---------|
| Doc2Vec (Niu & Silva) | Moderate | Requires rich taxonomy and large corpus; our station-level scale may produce insufficient POI sequences; needs ground truth for k selection |
| Semantics-preserved embedding (Huang 2022) | Poor | Supervised method requiring ground truth proportional distributions; very complex pipeline (LSTM + attention); designed for TAZ-level, not station catchment |
| **LDA (Lin et al.)** | **Best fit** | Unsupervised, interpretable, works with co-occurrence patterns; flexible spatial unit (can adapt to station catchments); topic coherence for K selection does not require ground truth; network analysis provides additional interpretive layer |
| CLIP zero-shot (Huang 2024) | Poor fit | Requires street view imagery for every station area; Google Street View coverage in Singapore is limited (especially MRT station underpasses, covered walkways, HDB void decks); no mixed-use output (single label); does not use POI data at all — fundamentally different data source from our OSM approach |

**LDA remains the most appropriate choice** for our project because:
1. It is unsupervised -- we have no ground truth functional zone data for Singapore
2. It produces interpretable topics (each topic = probability distribution over POI types)
3. It naturally handles mixed-use areas through proportional topic membership
4. Topic coherence score provides an objective K-selection criterion without ground truth
5. It is computationally lightweight compared to neural network approaches
6. Lin et al. demonstrate it works well at the street level, which is closer to our station catchment scale than TAZ or LSOA
7. It works directly with OSM POI data — no additional data source (street view imagery) required

### 3.3 Mapping Their Limitations to Our Known Issues

| Their limitation | Our known issue | How we should address it |
|-----------------|----------------|-------------------------|
| No ground truth (all 4 papers) | No functional zone data for Singapore | Use topic coherence for K selection; qualitative validation against known Singapore geography; compare with destination type classification from OD data |
| Residential POI sparsity (Niu & Silva; Lin et al.) | Residential areas near MRT stations may have few POIs | Exclude residential POIs (decision made); accept that residential-dominated stations will have different topic distributions |
| Ambiguous POI-function linkage (Huang 2022) | OSM's flat tag schema creates ambiguity | Clean and standardize OSM tags before analysis; group OSM keys/values into a custom taxonomy aligned with our research question |
| Point-based representation limits (Huang 2022) | OSM also models POIs as points/ways | Acknowledge as limitation; OSM ways (polygons) can provide some area information but most POI analysis treats them as centroids |
| No temporal analysis (all 4 papers) | OSM has version/timestamp data; we have 74 months of OD data | All four papers identify this as a future direction; we can extend LDA to temporal analysis by running it on time slices of OSM data |
| Crowdsourcing bias (none discuss) | OSM mapping activity bias in Singapore | Yeow et al. (2021) quantified this: OSM POI completeness at 28.2% in Tampines. Compute and flag low-mapping-activity stations |
| Visual ambiguity (Huang 2024) | Not directly applicable (we use POIs not images) | Illustrates that no single data source fully captures urban function — POI data and visual data have complementary blind spots |
| Indoor function invisible (Huang 2024) | OSM POIs can capture some indoor function (e.g., shop=convenience inside a building) but miss others | OSM actually has an advantage here over street view: POIs can represent businesses inside buildings that are invisible from the street |

### 3.4 Lessons from Their Validation Approaches

1. **Niu & Silva's ARI approach** requires external ground truth, which we lack. However, their approach of using census-like data for validation could be adapted: Singapore's destination type codes from the OD data could serve as a rough proxy.

2. **Huang et al.'s error analysis** is valuable -- they systematically examine where estimation fails and categorize the reasons. We should do the same: for stations where LDA topics do not match expected patterns, investigate whether it is a data issue (sparse POIs) or a genuine functional mismatch.

3. **Lin et al.'s coherence-based K selection** is the most practical for our setting. We should:
   - Run LDA with K ranging from 3 to 10
   - Calculate topic coherence (U_mass or C_v) for each K
   - Select K that balances coherence with interpretability (as they did, choosing K=6 despite K=3 having higher coherence)
   - Consider the specific context of MRT station destinations when interpreting topics

4. **All three papers use comparison baselines** -- we should compare LDA against at least one alternative (e.g., simple POI frequency-based classification, or Word2Vec if feasible) to justify our methodological choice.

---

## 4. Methodology Recommendation

### 4.1 Is LDA Appropriate?

**Yes, LDA is appropriate for our use case**, with the following rationale:

1. **Data fit**: LDA treats POI types as "words" and station catchment POI collections as "documents." This analogy works even with OSM's relatively flat tag structure, provided we construct a reasonable "vocabulary" from OSM key-value pairs.

2. **Scale fit**: Our analysis is at the station catchment level (likely 400-800m buffers around MRT stations). Lin et al. demonstrate LDA works at the street-segment level, which is smaller than our unit. Niu & Silva used LSOAs (~1500 people), which is larger. Our scale is within the demonstrated operational range.

3. **No ground truth needed**: LDA is unsupervised, making it suitable for exploratory analysis of destinations frequented by university communities.

4. **Interpretability**: LDA topics are directly interpretable as probability distributions over POI types, making results accessible to a non-technical audience.

### 4.2 What K to Try

Based on the literature:
- **Lin et al. (2025)**: Tested K=3 to K=10, chose K=6 based on coherence peak at K=6 (despite K=3 having slightly higher coherence)
- **Niu & Silva (2021)**: Used LDA with 10 topics for cluster annotation (not as primary method), selected 3-8 topics per cluster based on coherence
- **Huang et al. (2022)**: Not applicable (supervised method, no topic count)

**Recommendation for our project:**
- Test K = 4, 5, 6, 7, 8
- Use topic coherence (C_v metric) as primary selection criterion
- Apply domain knowledge to interpret whether topics are meaningful at each K
- Expect K=5 or K=6 to be optimal based on the precedent
- Consider that Singapore's urban structure is more compact and less functionally diverse than London, so fewer topics may suffice

### 4.3 Modifications Needed for OSM/Singapore Context

1. **Vocabulary construction**: Unlike Ordnance Survey or Baidu Map with standardized taxonomies, OSM uses free-form tags. We need to:
   - Use the combination of OSM key + value as the "word" (e.g., "amenity=restaurant", "shop=supermarket")
   - Group rare values into broader categories (e.g., all `shop=clothes*` variants)
   - Remove tags that are not functionally meaningful (e.g., `source`, `note`, `fixme`)
   - Consider including the OSM key alone as a word for POIs with rare/unique values

2. **Document construction**: Each MRT station's catchment area = one document
   - Buffer radius selection should be informed by walkability research (typically 400-800m)
   - POIs should be deduplicated (OSM nodes vs ways for the same feature)
   - Weight by distance from station? Lin et al. do not do this, but it could help differentiate core vs peripheral POIs

3. **Handling POI sparsity**: Some station catchments (especially terminal stations or industrial areas) may have very few POIs
   - Set a minimum POI count threshold; exclude stations below this from LDA
   - Alternatively, use larger buffers for sparse stations
   - Report the number of excluded stations transparently

4. **Temporal extension (unique contribution)**:
   - Use OSM element `timestamp` (last-edited) to create time slices
   - Note: OSM timestamps indicate *last edit*, not *creation*, so temporal analysis reflects mapping activity patterns, not POI lifecycles
   - This is a known limitation; we should be transparent about it
   - Could supplement with OD data temporal patterns (74 months) to correlate destination functional change with travel pattern change

5. **Validation without ground truth**:
   - Use Singapore destination type codes from OD data as partial proxy
   - Compare LDA topic distributions against known station typologies (e.g., CBD stations vs residential stations vs university stations)
   - Conduct qualitative validation by checking if topic compositions match expected station characteristics

### 4.4 Summary Recommendation

**Use LDA topic modelling as the core methodology** for analyzing POI functional composition around MRT stations, with K=4-8 to be determined by topic coherence. Construct documents from station catchment POI collections using OSM key-value pairs as the vocabulary. Validate using qualitative assessment against known Singapore geography and partial validation using OD destination type codes. Acknowledge OSM-specific limitations (no creation timestamp, flat taxonomy, crowdsourcing bias, low completeness) as constraints rather than flaws.

The Lin et al. (2025) framework is the closest methodological precedent for our project. We should follow their four-module structure (Data Representation, Topic Modelling, Network Construction, Network Evaluation) but adapt the spatial unit from street segments to station catchments, and add a temporal dimension that none of the four papers implement.

---

## 5. Limitations Assessment & Methodology Decision

### 5.1 Our Limitations (Honest Inventory)

**Data completeness (critical):**
- Yeow et al. (2021) found OSM POI completeness at 28.2% in Tampines (lowest of 4 sources tested). Our analysis will miss ~72% of real-world POIs. This is the single biggest limitation.
- The 28.2% figure is from Tampines (suburban). Orchard/CBD may be higher, but we have no systematic Singapore-wide completeness measurement.
- OSM has no standardized taxonomy — tag consistency depends entirely on individual mapper judgment.

**Data quality (moderate):**
- 24% of POIs lack even a name (from our Orchard exploration)
- 17.3% have opening_hours; 5.9% have check_date; 1.8% have start_date
- Version distribution concentrated at v1-v3 (44% at v1) — most POIs have been edited 0-1 times

**Mapping bias (moderate):**
- Mapping activity concentrates in commercial/tourist areas (Orchard, CBD)
- HDB estates and industrial areas are sparsely mapped
- Novack et al. (2024) confirms mapping patterns are city-specific and bursty
- Neis & Zipf (2012) show a small number of contributors produce most edits

**Temporal limitations (significant):**
- No creation timestamp in OSM — only last-edited timestamp
- Cannot distinguish new businesses from new mapping activity
- Overpass `date:` queries don't return element metadata
- All four reference papers lack temporal analysis

**Methodological limitations (moderate):**
- LDA assumes a bag-of-words model — spatial arrangement of POIs within a catchment is lost
- No ground truth for validation in Singapore — only qualitative checks possible
- K selection via topic coherence is objective but still requires judgment (Lin et al. chose K=6 despite K=3 having higher coherence)

### 5.2 What We Gain Despite Limitations

**OSM's advantages (even at 28% completeness):**
- Free, openly accessible, no API restrictions (unlike Google Maps, Baidu Map)
- Global coverage — works for any city, unlike government data sources
- Rich tag schema — more POI categories than any single commercial source
- Actively maintained and growing
- Can be combined with other data sources (URA Master Plan, OD travel data)

**LDA's advantages:**
- Unsupervised — no ground truth needed, works for exploratory analysis
- Interpretable — topics are directly understandable as POI type distributions
- Mixed membership — handles the reality that station areas serve multiple functions
- Reproducible — same input always produces same output (given fixed seed)
- Lightweight — runs on a laptop, no GPU needed (unlike Huang 2024's CLIP approach)

**Our unique contributions:**
- Singapore-specific: No published study applies LDA to Singapore transport station areas
- Temporal dimension: We plan to extend across 4 time snapshots — something none of the 4 reference papers do
- Integration with travel data: We can cross-validate LDA topics against actual OD travel patterns (74 months of data)
- OSM quality awareness: We document mapping bias explicitly, which most POI-based urban function papers do not do

### 5.3 Decision: Proceed as Planned, with Transparent Framing

**Yes, carry forward with the current LDA methodology**, with these modifications:

1. **Frame honestly in the paper**: "We analyze the urban function of station catchment areas as represented in OpenStreetMap POI data" — not "we analyze the urban function of station areas." The distinction is critical.

2. **Add completeness disclaimer early**: Cite Yeow et al. (2021) in the data section. State that OSM captured an estimated 28% of real-world POIs in one Singapore test area, and that our results should be interpreted accordingly.

3. **Compute mapping quality metrics**: Per-station contributor count, POI density, tag completeness. Include a data quality map as a supplementary figure.

4. **Validate where possible**: Cross-reference LDA topics against (a) URA Master Plan zoning, (b) known Singapore geography (NUS/NTU areas should show educational topics), (c) OD destination type codes.

5. **Don't overclaim**: Our analysis identifies *patterns in available OSM data*, not definitive urban function classifications. The topics are useful heuristics, not ground truth.

**What we should NOT do:**
- Switch to a different methodology at this stage — LDA is the best fit for our constraints
- Try to "fix" OSM completeness by supplementing with other sources mid-study — scope creep
- Over-invest in temporal analysis given the OSM timestamp limitations
- Claim that our results generalize beyond OSM-mapped POIs

### 5.4 Comparison with Alternative Approaches

| Approach | Why not for us |
|----------|---------------|
| CLIP zero-shot (Huang 2024) | Requires street view imagery for every station — Google Street View coverage in Singapore is limited (especially covered walkways, underground MRT stations, HDB void decks). Single-label output loses mixed-use information. |
| Doc2Vec (Niu & Silva 2021) | Requires rich hierarchical taxonomy (616 classes). Our OSM data has flat, inconsistent tags. Needs ground truth for validation (LOAC), which we lack for Singapore. |
| Supervised embedding (Huang 2022) | Requires ground truth proportional distributions per area (PKU Urbanscape dataset). We have no equivalent for Singapore. Complex pipeline (LSTM + attention) with many hyperparameters. |
| Simple POI frequency | Too naive — doesn't capture co-occurrence patterns. Would classify a station with 50 restaurants and 1 clinic the same as one with 30 restaurants and 21 clinics. LDA captures these compositional differences. |
