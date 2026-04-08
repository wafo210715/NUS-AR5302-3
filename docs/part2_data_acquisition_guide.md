# Part 2: Historical POI Snapshots - Data Acquisition Guide

**Updated:** 2026-04-08
**Purpose:** Clarify the correct approach for historical POI analysis

---

## 数据获取策略

### ❌ 错误理解：用ohsome替代Overpass

**ohsome API的限制：**
- 只返回聚合统计（数量、编辑者等）
- **不返回具体POI列表**
- 无法构建document-term matrix
- 无法用于LDA分析

**ohsome的作用：**
- 数据质量背景理解
- 校验Overpass快照的可靠性
- 判断变化是真实的还是制图活动

### ✅ 正确流程：Overpass历史快照 + ohsome交叉验证

```
步骤1: 用Overpass date:爬取历史POI
├─ 2020-01-01 snapshot
├─ 2022-01-01 snapshot  
└─ 2024-01-01 snapshot

步骤2: 对每个snapshot运行LDA
├─ 构建DTM
├─ K=5主题建模
└─ 获取主题分布

步骤3: ohsome交叉验证
├─ 对比POI数量一致性
├─ 识别制图活动高峰期
└─ 校准结果解读
```

---

## 实施步骤

### Step 1: 下载历史POI快照

```bash
# 下载2020, 2022, 2024年快照
python utils/download_historical_pois.py --years 2020 2022 2024

# 输出文件：
# data/historical_pois/historical_pois_2020-01-01.csv
# data/historical_pois/historical_pois_2022-01-01.csv
# data/historical_pois/historical_pois_2024-01-01.csv
```

**注意：**
- 每个快照约需5-10分钟（4个子区域）
- 历史查询无法获取metadata（version, timestamp等）
- 总共约15-30分钟

### Step 2: 可视化对比

```bash
# 对比Overpass快照与ohsome数据
python utils/visualize_historical_pois.py

# 输出：
# figures/part2_historical_comparison.png
```

### Step 3: 对每个snapshot运行LDA

使用Part 3的LDA流程，分别处理三个历史快照：

```r
# 对每个历史快照
for year in c(2020, 2022, 2024) {
  # 1. 加载历史POI数据
  pois <- read.csv(file.path(data_dir, "historical_pois", paste0("historical_pois_", year, "-01-01.csv")))
  
  # 2. 复用Part 3流程
  # - 空间分配到站点
  # - 词汇过滤
  # - 构建DTM
  # - LDA K=5
  
  # 3. 保存结果
  write.csv(station_topic, paste0("data/historical_station_topics_", year, ".csv"))
}
```

---

## 数据质量考虑

### 历史查询限制

Overpass `date:`参数的限制：
- **无metadata** - 无法获取version, timestamp, user_id
- 无法计算历史数据质量指标
- 只能依赖ohsome的全局统计来推断

### 交叉验证策略

| 对比项 | Overpass快照 | ohsome统计 | 预期 |
|--------|--------------|-----------|------|
| 2020 POI数量 | ~30,000 | 30,555 | ±5% |
| 2022 POI数量 | ~38,000 | 38,245 | ±5% |
| 2024 POI数量 | ~49,000 | 50,490 | ±5% |

**如果差异>10%：** 可能存在查询问题或数据不一致

---

## 时间段选择建议

基于ohsome mapper activity分析：

| 年份 | 编辑者活动 | 可靠性 | 推荐 |
|------|-----------|--------|------|
| 2020-2021 | 中等 (40-70人/月) | 高 | ✅ |
| 2022 | 中等 (50-60人/月) | 高 | ✅ |
| 2023 | **高峰 (4,446次/月)** | **低** | ⚠️ 避免用2023 |
| 2024-2026 | 稳定 (55-65人/月) | 高 | ✅ |

**推荐快照年份：** 2020, 2022, 2024

---

## 预期输出

| 文件 | 内容 |
|------|------|
| `historical_pois_2020-01-01.csv` | 2020年POI快照 |
| `historical_pois_2022-01-01.csv` | 2022年POI快照 |
| `historical_pois_2024-01-01.csv` | 2024年POI快照 |
| `part2_historical_comparison.png` | Overpass vs ohsome对比图 |
| `historical_station_topics_2020.csv` | 2020年站点主题分布 |
| `historical_station_topics_2022.csv` | 2022年站点主题分布 |
| `historical_station_topics_2024.csv` | 2024年站点主题分布 |

---

## 快速开始

```bash
# 1. 下载数据（15-30分钟）
python utils/download_historical_pois.py --years 2020 2022 2024

# 2. 验证数据质量
python utils/visualize_historical_pois.py

# 3. 对每个年份运行LDA（复用Part 3脚本）
# 需要修改part3_poi_lda_yk.Rmd以支持历史快照输入
```
