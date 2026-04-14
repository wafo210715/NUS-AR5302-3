# Part 2 开发计划：POI-based Urban Function Identification (Overture + LDA)

**负责人：** YK
**分支：** `YK_v2`
**状态：** 待开始
**创建日期：** 2026-04-14

---

## 一、任务目标

使用 Overture Maps Foundation 的 POI 数据，通过 LDA 主题模型识别新加坡公共交通站点周边的城市功能类型（urban function types），最终将每个站点分类为一种主导城市功能。

**核心产出：** `station_topic_classification.csv` — 每个站点的主题分类结果，供 Part 3（时间模式分析）和 Part 4（对比分析）使用。

---

## 二、前置条件（已满足）

| 条件 | 来源 | 状态 |
|------|------|------|
| 83 个站点坐标（station_mapping.csv） | Part 1 | ✅ 已完成 |
| LTA 全部公交站和地铁站坐标 | Part 1 | ✅ 已完成 |
| Python 环境（uv + duckdb + s3fs + gensim） | pyproject.toml | ✅ 已配置 |
| R 环境（topicmodels + stm + sf） | 本地 RStudio | ✅ 已安装 |
| Overture POI 下载脚本 | workload_plan 中提及，但**尚未创建** | ❌ 待创建 |

---

## 三、关键决策（已确定）

1. **使用单张快照做 LDA** — Dec 2025（最新可用）。理由：POI 景观月度间变化很小，时间维度由 OD 数据提供。
2. **空间范围：新加坡全岛所有站点** — 不是只做 4 个大学的站点，而是所有公交站 + 地铁站。LDA 需要足够的"文档"（站点）来训练模型。
3. **Buffer 半径：500m** — 步行可达范围。
4. **K 范围：4–8** — 通过 C_v topic coherence 选择最优 K。
5. **POI 数据源：Overture Maps** — 替换旧的 OSM 方案，Overture 有标准化的 categories.primary 分类体系（~280 种），更适合 LDA。

---

## 四、开发步骤

### Step 1：下载 Overture POI 数据

**文件：** `utils/download_overture_pois.py`（新建）

**要做什么：**
- 从 Source Cooperative 的 S3 存储下载 Overture Maps POI 的 GeoParquet 数据
- 使用 DuckDB 直接查询 S3，只提取新加坡范围内的 POI（bbox 约束）
- 只保留 Dec 2025 快照（最新）
- 提取关键字段：`id`, `names.primary`, `categories.primary`, `confidence`, `operating_status`, `geometry`
- 过滤：只保留 `operating_status = "open"` 的 POI
- 输出为本地 GeoParquet 或 CSV

**技术要点：**
```
S3 路径: s3://us-west-2.opendata.source.coop/fused/overture/{release}/theme=places/type=place/
```
- Overture 的 release 命名格式如 `2025-12-17.0`
- 用 DuckDB 的 `read_parquet` + HTTP/S3 扩展可以直接查询远程文件
- 新加坡 bbox: `lat [1.15, 1.48]`, `lon [103.60, 104.08]`
- 预计新加坡 POI 总量：~100k–300k 条

**输出文件：**
- `data/overture_pois/overture_sg_202512.parquet` — 全部 POI（过滤后）
- `data/overture_pois/overture_sg_202512.csv` — 备份 CSV

**Checkpoint 2：** POI 数据质量检查图

---

### Step 2：POI 数据质量检查

**文件：** `scripts/part2_poi_lda_yk.Rmd` — 开头几个 chunk

**要做什么：**
- 加载 POI 数据，统计总数量
- 检查 `categories.primary` 的分布（有多少种类别，各类别数量）
- 检查 `confidence` 分数分布
- 绘制新加坡 POI 密度热力图
- 绘制 Top 20 POI 类别条形图
- 检查是否有异常值（如 POI 坐标不在新加坡范围内）

**输出文件：**
- `figures/part2_poi_density_heatmap.png` — 密度热力图
- `figures/part2_poi_category_distribution.png` — 类别分布条形图

---

### Step 3：空间分配 — 将 POI 分配到站点

**文件：** `scripts/part2_poi_lda_yk.Rmd` — 空间处理 chunks

**要做什么：**
- 加载全部公交站 + 地铁站坐标（`sg_bus_stops_all.csv` + `sg_mrt_stations_all.csv`）
- 对每个站点创建 500m buffer（投影到 EPSG:3414 SVY21）
- 将 POI 分配给包含它的 buffer 对应的站点
- 如果一个 POI 落在多个 buffer 内，分配给最近的站点
- 如果一个 POI 不在任何 buffer 内，排除
- 去除 residential 类别的 POI（focus on destinations）

**技术要点：**
- 使用 `sf::st_buffer()`, `sf::st_intersects()`, `sf::st_distance()`
- 新加坡全岛有 ~5300 个公交站 + ~130 个地铁站，每个站点一个 buffer
- 注意：`station_mapping.csv` 里的 83 个站点是"校园站点"，但 LDA 需要全岛所有站点作为训练数据

**输出文件：**
- `data/overture_pois/poi_station_assignment.csv` — POI-站点分配表

---

### Step 4：构建文档-词项矩阵 (DTM)

**文件：** `scripts/part2_poi_lda_yk.Rmd` — DTM 构建 chunks

**要做什么：**
- 每个 site = 一个 "document"
- 每个 `categories.primary` 值 = 一个 "term"（word）
- 单元格值 = 该站点 buffer 内该 POI 类别的数量
- 词汇表过滤：
  - 去除出现在 < 5 个站点的类别（太稀有 = 噪声）
  - 去除出现在 > 90% 站点的类别（太常见 = 无区分力）
- 站点过滤：去除 POI 数量 < 3 的站点（太稀疏的 "document" 会损害模型质量）

**输出文件：**
- `data/overture_pois/station_poi_dtm.rds` — R 稀疏矩阵格式
- `data/overture_pois/station_poi_counts.csv` — 可读 CSV 版本

---

### Step 5：运行 LDA 模型

**文件：** `scripts/part2_poi_lda_yk.Rmd` — LDA 训练 chunks

**要做什么：**
- 对 K = 4, 5, 6, 7, 8 分别训练 LDA 模型
- 使用 R 包 `topicmodels::LDA()`
- 参数设置：`alpha = 0.1`, `em = list(iter.max = 2000)`, `seed = 42`
- 保存每个 K 的模型为 `.rds` 文件

**输出文件：**
- `data/overture_pois/lda_model_k4.rds` ~ `lda_model_k8.rds`

---

### Step 6：选择最优 K（Topic Coherence）

**文件：**
- `utils/export_lda_beta.R`（已有，可直接复用）
- `utils/calculate_topic_coherence_gensim.py`（已有，可直接复用）

**要做什么：**
1. 用 `export_lda_beta.R` 从 R 模型中导出 beta（topic-word）矩阵为 CSV
2. 用 `calculate_topic_coherence_gensim.py` 计算 C_v 和 U_MASS coherence 分数
3. 综合考虑 coherence 分数 + perplexity + 主题可解释性，选择最优 K
4. 参考 Lin et al. (2025)：他们选了 K=6（伦敦），新加坡更紧凑，预期 K=5 或 K=6

**输出文件：**
- `data/overture_pois/lda_beta/beta_k4.csv` ~ `beta_k8.csv`
- `data/overture_pois/coherence_scores_gensim.json`
- `figures/part2_k_selection.png` — K 选择图（由 `visualize_k_selection.py` 生成）

**Checkpoint 4：** K 选择 coherence 图

---

### Step 7：主题解释与标注

**文件：** `scripts/part2_poi_lda_yk.Rmd` — 主题解释 chunks

**要做什么：**
- 提取选定 K 的 beta 矩阵（topic × POI class 概率分布）
- 对每个 topic，列出 Top 15 POI 类别及其概率
- 基于领域知识，手动为每个 topic 分配有意义的城市功能标签
- 标签示例（Overture 类别语境）："Dining & Retail"、"Commercial & Office"、"Healthcare & Wellness" 等
- 绘制 Topic-POI 关联热力图

**输出文件：**
- `data/overture_pois/topic_labels.csv`
- `figures/part2_topic_poi_heatmap.png`

**Checkpoint 5（部分）：** Topic-POI 热力图

---

### Step 8：站点分类

**文件：** `scripts/part2_poi_lda_yk.Rmd` — 分类 chunks

**要做什么：**
- 提取 gamma 矩阵（document-topic 概率分布）：P(topic | station)
- 每个站点的主导 topic = 概率最高的 topic
- 计算 purity score（主导 topic 的概率值）
- 将 topic 标签映射为城市功能名称
- 输出完整的站点分类表

**输出文件：**
- `data/overture_pois/station_topic_classification.csv`

这是 Part 3 和 Part 4 最重要的输入文件。

---

### Step 9：可视化 — 站点功能地图

**文件：** `scripts/part2_poi_lda_yk.Rmd` — 可视化 chunks

**要做什么：**
- 绘制新加坡全岛站点功能分类地图
- 每个站点按主导 topic 着色
- 标注 4 个大学的位置
- 使用统一的 project color scheme

**输出文件：**
- `figures/part2_station_function_map.png`

**Checkpoint 5（完整）：** 站点功能分类地图

---

### Step 10：汇总输出与清理

**要做什么：**
- 确保所有输出文件在正确位置
- 生成一份 pipeline 完成摘要
- 更新 `docs/todo.md` 中的 Part 2 条目

---

## 五、文件清单

### 新建文件
| 文件 | 用途 |
|------|------|
| `utils/download_overture_pois.py` | Overture POI 下载器 |

### 修改文件
| 文件 | 变更说明 |
|------|----------|
| `scripts/part2_poi_lda_yk.Rmd` | 全面重写：OSM → Overture 数据源，更新所有数据加载和空间处理逻辑 |
| `docs/todo.md` | 更新 Part 2 完成状态 |

### 复用文件（无需修改）
| 文件 | 用途 |
|------|------|
| `utils/export_lda_beta.R` | 从 R LDA 模型导出 beta 矩阵 |
| `utils/calculate_topic_coherence_gensim.py` | 计算 C_v topic coherence |
| `utils/visualize_k_selection.py` | K 选择可视化 |

### 输出文件
| 文件 | 内容 | 使用者 |
|------|------|--------|
| `data/overture_pois/overture_sg_202512.parquet` | 新加坡 POI 原始数据 | Part 2 |
| `data/overture_pois/station_poi_dtm.rds` | 文档-词项矩阵 | Part 2 |
| `data/overture_pois/coherence_scores_gensim.json` | Coherence 分数 | Part 2 |
| `data/overture_pois/topic_labels.csv` | 主题标签映射 | Part 2, 3, 4 |
| **`data/overture_pois/station_topic_classification.csv`** | **站点功能分类** | **Part 3, 4** |
| `figures/part2_poi_density_heatmap.png` | POI 密度图 | Part 5 (论文) |
| `figures/part2_poi_category_distribution.png` | 类别分布图 | Part 5 (论文) |
| `figures/part2_k_selection.png` | K 选择图 | Part 5 (论文) |
| `figures/part2_topic_poi_heatmap.png` | 主题-POI 热力图 | Part 5 (论文) |
| `figures/part2_station_function_map.png` | 站点功能地图 | Part 5 (论文) |

---

## 六、与旧版本（OSM 方案）的主要区别

| 方面 | 旧版（OSM） | 新版（Overture） |
|------|------------|-----------------|
| POI 数据源 | OpenStreetMap / Overpass API | Overture Maps Foundation / Source Cooperative |
| POI 分类 | OSM key=value 组合（扁平、不一致） | `categories.primary`（标准化 ~280 类） |
| 数据质量 | 完整度约 28%（Tampines），标签不一致 | 商业级质量，标准化分类 |
| 下载方式 | Overpass API HTTP 查询 | DuckDB + S3 直接查询 GeoParquet |
| 需要的分类步骤 | 从 OSM tags 构建自定义词汇表 | 直接使用 `categories.primary` |
| 保留的分析逻辑 | — | 空间分配、DTM 构建、LDA 训练、K 选择、站点分类 — 全部保留 |

**核心变化只在数据获取和预处理阶段（Step 1–3），LDA 建模到站点分类的流程（Step 4–9）基本不变。**

---

## 七、风险与应对

| 风险 | 可能性 | 应对 |
|------|--------|------|
| Source Cooperative S3 不可用 | 低 | 尽早下载；如有问题尝试 Overture 官方 S3（60 天保留期） |
| 新加坡 POI 数量过少/过多 | 低 | Overture 在新加坡覆盖应优于 OSM；如有问题可调整 bbox |
| Overture categories 与城市功能映射不清 | 中 | 先做 EDA（Step 2），检查类别分布后再决定是否需要二次归类 |
| LDA 结果不可解释 | 中 | 尝试不同 K；参考 Lin et al. (2025) 的做法 |
| DuckDB + S3 连接问题 | 中 | 备选：先下载 GeoParquet 到本地再用 DuckDB 查询 |

---

## 八、执行顺序总结

```
Step 1: 下载 Overture POI 数据
   ↓
Step 2: POI 数据质量检查（EDA）
   ↓
Step 3: 空间分配（POI → 站点 buffer）
   ↓
Step 4: 构建 DTM（文档-词项矩阵）
   ↓
Step 5: 运行 LDA 模型（K=4~8）
   ↓
Step 6: 选择最优 K（coherence）
   ↓
Step 7: 主题解释与标注
   ↓
Step 8: 站点分类
   ↓
Step 9: 可视化
   ↓
Step 10: 汇总与清理
```
