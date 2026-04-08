# Part 4: POI Metadata & Opening Hours Analysis Guide

**Created:** 2026-04-08
**Purpose:** Answer key questions about POI metadata for Part 4 analysis

---

## 问题1: LDA基于什么数据？

### 答案：基于所有有POI键的数据，不依赖name字段

**当前LDA使用的字段：**
- `poi_class` - 主POI类别（如 `amenity=restaurant`）
- 不使用 `name` 字段作为特征

**证据（从part3_poi_lda_yk.Rmd）：**
```r
# 分配主类别
pois_classified <- pois_raw %>%
  mutate(poi_class = apply(., 1, assign_primary_class))

# 只要有poi_class就保留，不检查name
pois_classified <- pois_classified %>%
  filter(!is.na(poi_class))
```

**name字段的作用：**
- 仅用于质量指标计算：`pct_named = mean(name != "") * 100`
- 不作为LDA输入特征

**结论：** LDA基于**所有有POI键的56,627个POI**，不管有没有name。

---

## 问题2: Part 4时间段分析策略

### 答案：使用有opening_hours的POI，与OD时间对齐

### 已提取数据

| 指标 | 数值 |
|------|------|
| **有opening_hours的POI** | 4,473个 (7.9%) |
| **早高峰覆盖** | 2,252个 (50.3%) |
| **日间覆盖** | 4,197个 (93.8%) |
| **晚高峰覆盖** | 4,056个 (90.7%) |
| **全天开放** | 2,108个 (47.1%) |

### 时间段定义（统一标准）

| 时段 | 时间范围 | OD数据 | opening_hours |
|------|----------|--------|---------------|
| 早高峰 | 06:00-10:00 | tap_in/out时间 | 06:00-10:00营业 |
| 日间 | 10:00-16:00 | tap_in/out时间 | 10:00-16:00营业 |
| 晚高峰 | 16:00-22:00 | tap_in/out时间 | 16:00-22:00营业 |

### 实施方案

#### Step 1: 提取OD数据的时间段
```r
# 从node数据提取tap-in/tap-out时间
# 按站点聚合三个时段的流量
```

#### Step 2: 创建时段POI集合
```r
# 早高峰POI: pois_with_opening_hours[morning == TRUE]
# 日间POI: pois_with_opening_hours[afternoon == TRUE]
# 晚高峰POI: pois_with_opening_hours[evening == TRUE]
```

#### Step 3: 时段-站点关联
```r
# 将POI分配到站点（500m缓冲）
# 计算每个站点在每个时段的POI数量
# 生成三个时段的station_poi_counts矩阵
```

#### Step 4: 时段LDA分析
```r
# 对三个时段分别运行LDA (K=5)
# 比较主题分布差异
```

---

## 问题3: 可用Metadata字段总结

### 完整Metadata列表

| 字段 | 类型 | Part 4用途 |
|------|------|-----------|
| `osm_id` | 整数 | POI唯一标识 |
| `osm_type` | 字符串 | node/way |
| `lat`, `lon` | 浮点数 | 空间位置 |
| `version` | 整数 (1-20) | 数据质量过滤 |
| `timestamp` | 时间戳 | 编辑时间 |
| `changeset_id` | 整数 | 批次标识 |
| `user_id` | 整数 | 贡献者ID |
| `amenity` | 字符串 | POI主类别 |
| `shop` | 字符串 | POI主类别 |
| `leisure` | 字符串 | POI主类别 |
| `tourism` | 字符串 | POI主类别 |
| `office` | 字符串 | POI主类别 |
| `healthcare` | 字符串 | POI主类别 |
| `craft` | 字符串 | POI主类别 |
| `historic` | 字符串 | POI主类别 |
| `name` | 字符串 | 53.1%有名称 |
| `all_tags` | JSON | 完整标签 |

### Part 4数据可用性

| Part 4需求 | 数据状态 | 文件 |
|------------|----------|------|
| LDA站点分类 | ✅ 可用 | `station_topic_classification.csv` |
| NUS/NTU站点 | ✅ 可用 | `station_mapping.csv` |
| OD时间数据 | ⚠️ 需提取 | 从node数据提取 |
| opening_hours POI | ✅ 已提取 | `pois_with_opening_hours.csv` |
| 空间分布图 | ✅ 已生成 | `part4_opening_hours_spatial_distribution.png` |

---

## 推荐分析流程

### 方案A：基于opening_hours的时段分析（推荐）

1. **使用三个时段POI子集**
   - 早高峰：2,252个POI
   - 日间：4,197个POI  
   - 晚高峰：4,056个POI

2. **与OD时间对齐**
   - 提取OD的tap_in/tap_out时间
   - 划分为相同三个时段
   - 分析时段出行模式

3. **优势**
   - 基于真实营业时间
   - 避免opening_hours覆盖不足的问题
   - 可直接与OD时间关联

### 方案B：全量POI + OD加权（备选）

1. **使用所有POI**
   - 56,627个POI
   - 不依赖opening_hours

2. **用OD流量加权**
   - 早高峰流量高的站点 → 早高峰POI权重高
   - 推断时段功能特征

3. **限制**
   - 基于流量推断，不是直接时间关联

---

## 生成的文件

| 文件 | 内容 |
|------|------|
| `data/pois_with_opening_hours.csv` | 4,473个有opening_hours的POI |
| `figures/part4_opening_hours_spatial_distribution.png` | 空间分布四面板图 |
| `figures/part4_opening_hours_overlap.png` | 时段重叠统计 |
| `docs/part4_time_of_day_proposal.md` | 完整方法论提案 |

---

## 下一步

1. **提取OD时间数据** - 从node数据获取tap_in/tap_out时间戳
2. **创建时段OD矩阵** - 按站点聚合三个时段的流量
3. **运行时段LDA** - 对每个时段POI集运行LDA
4. **NUS vs NTU比较** - 分时段分析两校出行差异
