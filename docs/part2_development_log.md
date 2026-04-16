# Part 2 开发日志：POI-based Urban Function Identification (Overture + LDA)

**负责人：** YK
**分支：** `YK`
**状态：** 已完成
**开发日期：** 2026-04-14 ~ 2026-04-15

---

## 一、任务目标

使用 Overture Maps Foundation 的 POI 数据，通过 LDA 主题模型识别新加坡公共交通站点周边的城市功能类型，最终将每个站点分类为一种主导城市功能。

**核心交付物：** `data/overture_pois/station_topic_classification.csv` — 供 Part 3（时间模式分析）和 Part 4（对比分析）使用。

---

## 二、Pipeline 执行时间线

| 日期 | Step | 内容 | 状态 |
|------|------|------|------|
| 2026-04-14 | Step 1 | 下载 Overture POI 数据 (Dec 2025 快照) | 完成 |
| 2026-04-14 | Step 2 | POI 数据质量检查 (EDA) | 完成 |
| 2026-04-15 | Step 3 | 空间分配 — 将 POI 分配到站点 (500m buffer) | 完成 |
| 2026-04-15 | Step 4 | 构建文档-词项矩阵 (DTM) | 完成 |
| 2026-04-15 | Step 5 | 运行 LDA 模型 (K=4~8) | 完成 |
| 2026-04-15 | Step 6 | K 选择 (Perplexity + C_v/U_MASS Coherence) | 完成 |
| 2026-04-15 | Step 7 | 主题解释与手动标注 | 完成 |
| 2026-04-15 | Step 8 | 站点分类 | 完成 |
| 2026-04-15 | Step 9 | 可视化 (热力图 + 地图) | 完成 |

---

## 三、遇到的问题及解决方案

### 问题 1：无法在 VSCode 中直接 Knit Rmd

**日期：** 2026-04-14

**问题描述：** Rmd 文件需要在 RStudio 中 Knit，但用户不方便使用 RStudio，希望能在 VSCode 的终端里运行。

**解决方案：** 将 Rmd 拆分为独立步骤，通过命令行逐段运行：
```bash
# 从 Git Bash (Windows) 中通过 PowerShell 调用 Rscript
cd scripts && powershell.exe -Command "Rscript -e 'rmarkdown::render(\"part2_poi_lda_yk.Rmd\")' 2>&1"
```
此外，对于需要跳过前面已完成步骤直接跑后续步骤的情况，创建了临时独立 R 脚本直接加载已有中间文件（如 DTM），避免重复运行前面的步骤。

---

### 问题 2：`as(dtm_wide, "dgTMatrix")` 类型转换失败

**日期：** 2026-04-15

**问题描述：** `readRDS()` 恢复的 DTM 是普通 `matrix` 对象，不能直接用 `as(dtm_wide, "dgTMatrix")` 转换为 `topicmodels::LDA()` 所需的 `dgTMatrix` 格式。

**错误信息：**
```
Error in as(dtm_wide, "dgTMatrix") :
  no method or default for coercing "matrix" to "dgTMatrix"
```

**根本原因：** R 的 `as()` 函数不能直接把基础 `matrix` 转为 `dgTMatrix`（稀疏三元组矩阵）。需要先转为稀疏矩阵（`dgCMatrix`），再转为目标格式。

**解决方案：**
```r
library(Matrix)
dtm_sparse <- as(Matrix(dtm_wide), "dgTMatrix")
```
- `Matrix(dtm_wide)` 先将密集矩阵转为稀疏列压缩格式（`dgCMatrix`）
- `as(..., "dgTMatrix")` 再转为稀疏三元组格式
- 会产生一个 deprecation warning（`as(<dgCMatrix>, "dgTMatrix")`），但功能正常

---

### 问题 3：关键词匹配自动标注产生标签冲突

**日期：** 2026-04-15

**问题描述：** 最初使用关键词匹配系统为 LDA 主题自动分配标签，出现以下问题：

1. **子串误匹配：** `grepl("school", "preschool")` 返回 TRUE，导致 `preschool` 被错误归类到 Education 类别
2. **子串误匹配：** `grepl("market", "supermarket")` 返回 TRUE，同样产生错误分类
3. **标签冲突：** Topic 2 和 Topic 3 都被标注为 "Dining & Hospitality"
4. **低概率词干扰：** 排在第 11-15 位的低概率类别放大了 Dining 类的得分
5. **Topic 4 无标签：** Overture 中的 `automotive_repair`、`car_dealer`、`construction_services` 等类别未在标签池中

**解决方案：** 完全放弃关键词匹配方案，改为**手动标注**。手动标注是 LDA 研究中的标准做法（Blei et al., 2003; Chang et al., 2009），通过检查每个主题的 Top 15 Overture 类别及其概率分布，基于领域知识分配标签：

```r
topic_labels <- data.frame(
  topic = paste0("Topic_", 1:5),
  label = c(
    "Education & Professional Services",  # Topic 1: education, professional_services, financial_service
    "Dining & Hospitality",               # Topic 2: restaurant, chinese_restaurant, hotel, cafe
    "Mixed-Use & Community",              # Topic 3: landmark, accommodation, community_services
    "Industrial & Automotive",            # Topic 4: automotive_repair, car_dealer, interior_design
    "Retail & Personal Care"              # Topic 5: beauty_salon, clothing_store, jewelry_store
  )
)
```

---

### 问题 4：viridis 颜色方案 `YlOrRd` 选项不存在

**日期：** 2026-04-15

**问题描述：** 在热力图中使用 `scale_fill_viridis_c(option = "YlOrRd", ...)` 报错：
```
Warning: The option "YlOrRd" does not exist. Using "viridis" instead.
```

**根本原因：** `YlOrRd` 是 `RColorBrewer` 的调色板，不属于 `viridisLite` 包支持的选项。viridis 系列只支持 `viridis`、`magma`、`inferno`、`plasma`、`cividis`。

**解决方案：** 改为 `scale_fill_viridis_c(option = "inferno", ...)`，`inferno` 提供了类似的从浅到深的暖色渐变效果。

---

### 问题 5：gensim 4.4.0 在 Python 3.14 上编译失败

**日期：** 2026-04-15

**问题描述：** 运行 `uv run python utils/calculate_topic_coherence_gensim.py` 时，`uv sync` 尝试安装 `gensim==4.4.0` 但在 Python 3.14 上编译失败（没有预编译的 wheel，需要从源码编译 C 扩展）。

**解决方案：** 重写 coherence 计算脚本，**不依赖 gensim**。C_v coherence 的核心算法只涉及：
- 滑动窗口分割文档
- 统计词频和词对共现频率
- 计算 NPMI（Normalized Pointwise Mutual Information）
- 取均值

这些操作只需 `collections.Counter` 和 `math.log`，无需外部库。

新脚本：`utils/calculate_topic_coherence.py`（纯 Python 实现），同时计算 C_v 和 U_MASS 两种 coherence 指标。

同时从 `pyproject.toml` 中移除了 `gensim>=4.3` 依赖。

---

### 问题 6：Topic 3（Mixed-Use & Community）占比过高 (50.6%)

**日期：** 2026-04-15

**问题描述：** 在 K=5 的分类结果中，Topic 3 "Mixed-Use & Community" 占了 1,615 / 3,194 = 50.6% 的站点，远超其他主题。这可能意味着：
1. K=5 不够，需要更多主题来区分 "Mixed-Use" 内部的异质性
2. 或者这是新加坡城市结构的真实反映——大多数站点周边确实是混合功能社区

**决策：** 保留 K=5。理由：
- C_v 和 U_MASS coherence 在 K=4~8 范围内差异很小（C_v 仅差 0.02），没有统计学上的强信号
- K=5 的 5 个主题都有清晰、可解释的城市功能标签
- Topic 3 的高占比反映了新加坡的 "mixed-use neighborhood" 特征——这在城市地理文献中是合理的（许多 HDB 站点周边确实是混合功能）
- 在报告中应该讨论这一发现，而不是试图"消除"它

---

## 四、关键参数与决策记录

| 参数 | 值 | 理由 |
|------|-----|------|
| Overture Release | `2025-12-17-0` | 最新可用快照；POI 月度变化极小 |
| 空间范围 | 新加坡全岛所有站点 | LDA 需要足够多的"文档"来训练 |
| Buffer 半径 | 500m | 步行可达范围 |
| 坐标系 | EPSG:4326 (存储) / EPSG:3414 (buffer) | WGS84 标准存储，SVY21 用于米级距离计算 |
| DTM 词汇过滤 | 出现在 ≥5 个站点 且 ≤90% 站点 | 去除噪声词和无区分力词 |
| 站点过滤 | POI 数量 ≥3 | 稀疏文档损害模型质量 |
| K 范围 | 4 ~ 8 | 覆盖合理的主题数量范围 |
| LDA alpha | 0.1 | 鼓励文档集中于少量主题 |
| LDA iterations | 2000 | 确保收敛 |
| LDA seed | 42 | 可复现性 |
| **最优 K** | **5** | U_MASS peak + perplexity + domain interpretability |
| 手动标注 | 5 个主题 | 基于领域知识检查 Top 15 类别 |

### Coherence 计算结果

| K | C_v Coherence | U_MASS Coherence | Perplexity |
|---|---------------|-------------------|------------|
| 4 | **-0.1102** (最高) | -1.0282 | ~193 |
| **5** | -0.1201 | **-0.9352** (最高) | ~184 |
| 6 | -0.1306 | -0.9902 | ~180 |
| 7 | -0.1182 | -1.0505 | **~172** (最低) |
| 8 | -0.1231 | -1.1402 | ~175 |

> **说明：** C_v 全为负值，这在短文档/稀疏文档 POI 数据中是正常现象。不同 POI 类别（如 `restaurant` 和 `car_dealer`）在同一站点窗口中共现概率天然就低。绝对差异仅 0.02，无强统计信号。U_MASS（文档级共现）更适合 POI 数据，其峰值在 K=5。

---

## 五、LDA 主题分类结果摘要

| Topic | 标签 | Top 5 Overture 类别 | 站点数 | 占比 |
|-------|------|---------------------|--------|------|
| 1 | Education & Professional Services | professional_services, event_planning, software_development, financial_service, education | ~500 | ~15.7% |
| 2 | Dining & Hospitality | restaurant, chinese_restaurant, food_stand, hotel, coffee_shop | ~560 | ~17.5% |
| 3 | Mixed-Use & Community | landmark_and_historical_building, accommodation, education, real_estate, beauty_salon | ~1,615 | **50.6%** |
| 4 | Industrial & Automotive | automotive_repair, interior_design, event_planning, professional_services, car_dealer | ~270 | ~8.5% |
| 5 | Retail & Personal Care | beauty_salon, restaurant, clothing_store, jewelry_store, japanese_restaurant | ~250 | ~7.8% |

- **总站点数：** 3,194（注意：DTM 有 3,175 行，19 站点差异来自 `left_join` 时与 `station_poi_counts.csv` 的对齐）
- **平均 purity score：** 0.735（合理范围，unsupervised topic modeling 典型值 0.6~0.8）

---

## 六、交付物清单

### 6.1 核心脚本（代码）

| 文件 | 大小 | 说明 |
|------|------|------|
| `scripts/part2_poi_lda_yk.Rmd` | 26.6 KB | 主分析脚本，包含 Step 2~9 全部代码 |
| `utils/download_overture_pois.py` | 8.7 KB | Overture POI 下载器（S3 → DuckDB 过滤） |
| `utils/export_lda_beta.R` | 1.4 KB | 从 R LDA 模型导出 beta 矩阵为 CSV |
| `utils/calculate_topic_coherence.py` | 11.2 KB | C_v/U_MASS coherence 计算（纯 Python，无 gensim 依赖） |
| `utils/visualize_k_selection.py` | 8.5 KB | K 选择可视化（coherence 双面板 + C_v 单图） |
| `utils/calculate_topic_coherence_gensim.py` | 7.7 KB | 旧版 coherence 脚本（依赖 gensim，Python 3.14 不可用，已弃用） |

### 6.2 数据文件

#### 输入数据（需独立获取）

| 文件 | 大小 | 来源 | 说明 |
|------|------|------|------|
| `data/overture_pois/overture_sg_2025-12-17-0.parquet` | 11.3 MB | Source Cooperative S3 | 新加坡 POI 原始数据（GeoParquet） |
| `data/overture_pois/overture_sg_2025-12-17-0.csv` | 19.3 MB | 由 parquet 导出 | 备份 CSV |
| `data/LTABusStop.geojson` | — | Google Drive (Part 1) | 5,166 个公交站坐标 |
| `data/LTAMRTStationExitGEOJSON.geojson` | — | Google Drive (Part 1) | 597 个地铁站出口坐标 |

#### 中间产物

| 文件 | 大小 | 说明 |
|------|------|------|
| `data/overture_pois/poi_station_assignment.csv` | 13.7 MB | POI → 站点空间分配表 |
| `data/overture_pois/station_poi_counts.csv` | 4.8 MB | 各站点各类别 POI 计数矩阵 |
| `data/overture_pois/station_poi_dtm.rds` | 162 KB | 文档-词项矩阵（稀疏格式） |
| `data/overture_pois/lda_model_k4.rds` | 288 KB | LDA 模型 K=4 |
| `data/overture_pois/lda_model_k5.rds` | 317 KB | LDA 模型 K=5（最终选择） |
| `data/overture_pois/lda_model_k6.rds` | 349 KB | LDA 模型 K=6 |
| `data/overture_pois/lda_model_k7.rds` | 376 KB | LDA 模型 K=7 |
| `data/overture_pois/lda_model_k8.rds` | 399 KB | LDA 模型 K=8 |
| `data/overture_pois/lda_beta/beta_k4.csv` | 76.5 KB | Beta 矩阵 K=4 |
| `data/overture_pois/lda_beta/beta_k5.csv` | 92.4 KB | Beta 矩阵 K=5 |
| `data/overture_pois/lda_beta/beta_k6.csv` | 108 KB | Beta 矩阵 K=6 |
| `data/overture_pois/lda_beta/beta_k7.csv` | 124 KB | Beta 矩阵 K=7 |
| `data/overture_pois/lda_beta/beta_k8.csv` | 140 KB | Beta 矩阵 K=8 |

#### 最终产出（交付给 Part 3 / Part 4）

| 文件 | 大小 | 说明 | 使用者 |
|------|------|------|--------|
| **`data/overture_pois/station_topic_classification.csv`** | **602 KB** | **站点功能分类表**（核心交付物） | **Part 3, Part 4** |
| `data/overture_pois/topic_labels.csv` | 206 B | 主题标签映射 | Part 3, Part 4, Part 5 |
| `data/overture_pois/coherence_scores_gensim.json` | 463 B | Coherence 分数 | Part 5 (论文) |

### 6.3 可视化图表

| 文件 | 大小 | 说明 | 使用者 |
|------|------|------|--------|
| `figures/part2_poi_density_heatmap.png` | 420 KB | 新加坡 POI 密度热力图 | Part 5 (论文) |
| `figures/part2_poi_category_distribution.png` | 78 KB | Top 20 POI 类别分布条形图 | Part 5 (论文) |
| `figures/part2_k_selection.png` | 53 KB | Perplexity vs K 选择图 | Part 5 (论文) |
| `figures/part2_k_selection_metrics.png` | 139 KB | C_v + U_MASS 双面板对比图 | Part 5 (论文) |
| `figures/part2_cv_coherence_k_selection.png` | 108 KB | C_v Coherence 单独详细图 | Part 5 (论文) |
| `figures/part2_topic_poi_heatmap.png` | 108 KB | 主题-POI 关联热力图 | Part 5 (论文) |
| `figures/part2_station_function_map.png` | 175 KB | 新加坡站点功能分类地图 | Part 5 (论文) |

---

## 七、环境依赖

### R 包
- `sf` — 空间数据处理（buffer, intersects）
- `topicmodels` — LDA 主题建模
- `tm` — 文本挖掘工具
- `ggplot2` — 可视化
- `viridis` / `scales` — 颜色方案
- `Matrix` — 稀疏矩阵操作
- `dplyr`, `tidyr`, `tibble`, `stringr` — 数据处理
- `knitr`, `rmarkdown` — 文档生成

### Python 包
- `duckdb` — 查询 S3 上的 GeoParquet
- `s3fs` — S3 文件系统接口
- `pandas`, `numpy` — 数据处理
- `matplotlib` — 可视化

### 运行方式
```bash
# R 代码（通过 PowerShell 从 Git Bash 调用）
cd scripts && powershell.exe -Command "Rscript -e 'rmarkdown::render(\"part2_poi_lda_yk.Rmd\")' 2>&1"

# Python 脚本
uv run python utils/download_overture_pois.py
uv run python utils/calculate_topic_coherence.py
uv run python utils/visualize_k_selection.py
Rscript utils/export_lda_beta.R
```

---

## 八、注意事项与后续建议

1. **Topic 3 占比过高：** 在论文中应讨论这一发现的含义——可能是新加坡 "HDB 新镇" 模式的真实反映，而非模型缺陷。可以考虑在 Part 4 的对比分析中检验大学站点是否在 Topic 3 上有显著不同的分布。

2. **站点数差异：** `station_poi_counts.csv` 有 3,175 行（经过 DTM 过滤后的站点），而 `station_topic_classification.csv` 有 3,194 行（left_join 后的完整集）。Part 3/4 使用时应以 `station_topic_classification.csv` 为准，并注意 `purity` 列——NA 值表示该站点因 POI 过少被排除在 LDA 之外。

3. **可复现性：** LDA 使用 `seed = 42`，但 R 的 `topicmodels` 包在不同平台/版本上可能因浮点差异产生微小差异。如果需要精确复现，应使用保存的 `.rds` 模型文件而非重新训练。

4. **`calculate_topic_coherence_gensim.py` 已弃用：** 由于 gensim 在 Python 3.14 上无法编译，该脚本已被 `calculate_topic_coherence.py`（纯 Python 实现）替代。后者产生的 JSON 格式完全兼容，可直接被 `visualize_k_selection.py` 读取。

---

## 九、已知 Bug：station_poi_counts.csv 和 station_topic_classification.csv 缺失站点

**发现日期：** 2026-04-16
**发现者：** Part 4 队友 + YK 复核
**状态：** 待修复

### 问题概述

队友在 Part 4 使用 Part 2 的产出文件时，发现 `station_poi_counts.csv` 和 `station_topic_classification.csv` 缺失大量本应保留的站点。经独立验证（从 `poi_station_assignment.csv` 重新推算），有效站点数应为 **3,855** 个，但实际产出文件中站点数远少于此。

### 数据审计结果

| 文件 | 位置 | 行数 | 唯一站点数 | 数据源 | 备注 |
|------|------|------|-----------|--------|------|
| `poi_station_assignment.csv` | `data/overture_pois/` | 135,879 | 4,537（非 NA） | Overture | 最完整的上游表 |
| `station_poi_counts.csv` | `data/overture_pois/` | 3,175 | 3,175 | Overture | 缺 680 站点 |
| `station_topic_classification.csv` | `data/overture_pois/` | 3,194 | 3,175 | Overture | 缺 680 站点 + 19 行重复 |
| `station_poi_counts.csv` | `data/` 根目录 | 2,679 | — | **旧 OSM** | 错误文件！不应使用 |
| `station_topic_classification.csv` | `data/` 根目录 | 2,695 | — | **旧 OSM** | 错误文件！不应使用 |

### 已确认的 Bug 列表

#### Bug 1（严重）：站点去重逻辑只用了 X 坐标（经度）

**位置：** `scripts/part2_poi_lda_yk.Rmd` 第 200 行

```r
# 当前代码（有 Bug）
all_stations <- all_stations %>%
  mutate(xy = round(st_coordinates(.)[, 1], 5)) %>%   # ← 只取了 X（经度）！
  group_by(xy) %>%
  arrange(desc(pt_type)) %>%
  slice(1) %>%
  ungroup() %>%
  select(-xy)
```

**问题：** `st_coordinates(.)[, 1]` 只返回经度（X），没有包含纬度（Y）。变量名虽然叫 `xy`，但实际只有 `x`。

**后果：** 所有经度相同（精确到 5 位小数 ≈ ~1.1 米）但纬度不同的站点会被错误地当作"同一位置"而合并。在新加坡，沿南北走向道路分布的公交站经常共享相同的经度但纬度相差数百米，因此会被大量错误合并。这导致：
- `all_stations` 站点数被过度缩减
- 被错误合并的站点失去独立的 500m buffer
- 下游 POI 分配、DTM 构建、LDA 训练、站点分类全部受影响

**修复方案：** 同时使用 X 和 Y 坐标创建唯一键：

```r
# 修复后的代码
all_stations <- all_stations %>%
  mutate(xy = paste(round(st_coordinates(.)[, 1], 5),
                    round(st_coordinates(.)[, 2], 5), sep = "_")) %>%
  group_by(xy) %>%
  arrange(desc(pt_type)) %>%
  slice(1) %>%
  ungroup() %>%
  select(-xy)
```

#### Bug 2（中等）：classification 输出存在多对多 join 产生的重复行

**位置：** `scripts/part2_poi_lda_yk.Rmd` 第 582-593 行

```r
station_coords <- all_stations %>%
  filter(station_code %in% station_class$station_code) %>%
  ...
station_class <- station_class %>%
  left_join(station_coords, by = "station_code")
```

**问题：** `all_stations` 中同一 `station_code` 可能对应多行（例如 MRT 同一站点的多个出口有不同坐标）。`left_join` 时产生一对多展开，导致 `station_topic_classification.csv` 出现 19 行重复（3,194 行 vs 3,175 唯一站点）。

**后果：**
- Part 4 使用时可能产生重复计数
- 同一站点出现在多行中可能误导下游分析

**修复方案：** join 前对 `all_stations` 去重，或使用 `station_class` 的 `station_code` 做 anti-join 验证。

#### Bug 3（中等）：`data/` 根目录存在旧版 OSM 产出文件

**涉及文件：**
- `data/station_poi_counts.csv`（2,679 行，OSM 风格列名如 `amenity=xxx`）
- `data/station_topic_classification.csv`（2,695 行，旧标签如 "Neighborhood Recreation"）

**问题：** 这两个文件是旧 OSM pipeline 的残留物，不是当前 Overture pipeline 的产出。它们位于 `data/` 根目录而非 `data/overture_pois/`，容易导致队友误用。

**后果：**
- 队友使用旧文件会得到完全不同的分类结果
- 列名、标签、站点编码均与当前 pipeline 不兼容

**修复方案：** 删除 `data/` 根目录下的这两个旧文件。

### 缺失站点分析

从 `poi_station_assignment.csv` 重新推算，经过 vocabulary filtering（783 个有效类别）和 >= 3 POI 站点过滤后，应保留 **3,855** 个站点。但 `overture_pois/station_poi_counts.csv` 只有 **3,175** 个，缺失 **680** 个。

部分被错误遗漏的高 POI 覆盖站点：

| 站点编码 | 应保留 POI 数 |
|----------|--------------|
| 52008 | 484 |
| 42311 | 428 |
| 47559 | 372 |
| 22009 | 358 |
| 14141 | 349 |
| 80159 | 339 |
| 02149 | 311 |
| 47751 | 311 |

### 修复影响评估

修复 Bug 1（去重逻辑）后，需要重新运行 **整个 Part 2 pipeline**（Step 3 ~ Step 9），因为去重是空间分配的上游步骤。修复后的预期变化：
- `all_stations` 数量增加（更多独立站点保留）
- `poi_station_assignment.csv` 变化（更多 POI 被正确分配）
- DTM 维度变化（更多站点行）
- LDA 模型需要重新训练（因为 DTM 变化）
- `station_topic_classification.csv` 需要重新生成

### 待办事项

- [ ] 修复 Bug 1：去重逻辑改为 X+Y 双坐标
- [ ] 修复 Bug 2：classification 输出去重
- [ ] 清理 Bug 3：删除 `data/` 根目录的旧 OSM 文件
- [ ] 重新运行 Part 2 pipeline
- [ ] 重新验证站点数量
- [ ] 通知 Part 4 队友更新数据源
