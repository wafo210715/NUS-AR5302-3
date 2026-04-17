# Part 4 Handoff: Comparative Destination Analysis

**负责人：** yin
**分支：** `yin`
**状态：** 已完成当前一轮修订，可继续接手润色与导出
**更新日期：** 2026-04-17

---

## 一、任务目标

Part 4 的目标是基于校园相关 OD 子集数据，对 NUS、NTU、SMU、SUTD 四所高校的出行目的地进行对比分析，重点回答三个问题：

1. 不同大学社区的出行距离结构和目的地范围有何差异。
2. 不同大学社区偏好的城市功能类型是否不同。
3. 这些差异是否能通过图表和统计检验形成可写入报告/论文的结论。

当前这一轮工作的重点不是重写整个 pipeline，而是**修复 Part 4 对 Part 2 站点功能分类结果的接入、提高 topic 覆盖率、优化图表表达，并更新报告导出物**。

---

## 二、本轮完成的工作

### 1. 修复 Part 4 对站点功能分类文件的读取逻辑

原来的 `scripts/part4_comparative.Rmd` 优先读取：

- `data/station_topic_classification_harmonized.csv`
- 若不存在，则退回 `data/station_topic_classification.csv`

现在已改为优先读取：

- `data/station_topic_classification_supplemented.csv`
- 若不存在，则退回 `data/station_topic_classification.csv`

原因是 MRT OD 数据中存在复合编码或别名编码问题，直接使用原始 `station_topic_classification.csv` 会导致一部分 destination station 无法匹配 topic。

### 2. 新增补充版站点功能分类构建脚本

新增脚本：

- `scripts/build_station_topic_classification_supplemented.py`

这个脚本会：

1. 读取 `data/station_topic_classification.csv`
2. 读取 `data/mrt_station_codes.csv`
3. 扫描 `data/od_subset/origin_destination_train_*.csv` 中出现的复合 MRT 编码（如 `XXX/YYY`）
4. 如果复合编码中的某个单码没有 topic，就从已有编码继承对应 topic 标签
5. 输出 `data/station_topic_classification_supplemented.csv`

新增字段：

- `supplemented_from`
- `supplemented_station_name`
- `supplemented_via_compound`

这些字段主要用于追踪补充来源，便于后续复核。

### 3. 在 Part 4 中增加 compound alias fallback

仅靠补充版 CSV 还不够，因为 OD 中有些 destination 是复合编码本身。为此，`part4_comparative.Rmd` 中新增了：

- `compound_topic_lookup`
- `topic_label = coalesce(topic_label, topic_label_from_compound)`

这意味着：

1. 先按单站编码匹配 topic。
2. 如果单站编码没匹配到，再尝试用复合编码映射回已有 label。

这一步显著提高了 Part 4 的 topic match coverage。

### 4. 更新 Figure 4 副标题并重新生成图

Figure 4 的副标题已改为：

`Trip share distribution across distance bands for bus and MRT.`

并已重新渲染，更新了：

- `scripts/part4_comparative.html`
- `scripts/part4_comparative.knit.md`
- `scripts/figures/part4_fig6_distance_rings.png`

### 5. 优化若干图表文案和可读性

本轮还顺手做了几个可视化层面的修订：

- 去掉 MRT top destinations 图里 “NTU has no MRT-origin trips” 的副标题说明，使标题更中性。
- 将 topic share stacked bar 的标签显示阈值从 `4%` 放宽到 `2%`，便于阅读较小类别。
- 调整 sankey 图的左侧标签绘制逻辑，避免左侧大学名称与中右层标签混淆。
- 增大 sankey 图左边距，避免标签被裁切。

---

## 三、当前核心文件

### 代码

| 文件 | 作用 |
|------|------|
| `scripts/part4_comparative.Rmd` | Part 4 主分析脚本，所有表和图的源头 |
| `scripts/build_station_topic_classification_supplemented.py` | 构建补充版站点 topic 分类文件 |
| `scripts/export_part4_tables_to_word.py` | 将 knit markdown 中的表和图整理成 Word 报告 |

### 中间/输出文件

| 文件 | 作用 |
|------|------|
| `data/station_topic_classification_supplemented.csv` | Part 4 当前应优先使用的站点功能分类文件 |
| `scripts/part4_comparative.knit.md` | R Markdown 渲染后的 markdown 中间文件 |
| `scripts/part4_comparative.html` | 当前最新 HTML 报告 |
| `docs/part4_results_report.docx` | 当前 Word 报告主输出 |
| `docs/part4_result_tables.docx` | 兼容旧命名的 Word 输出 |

### 关键图件

| 文件 | 对应内容 |
|------|----------|
| `scripts/figures/part4_fig6_distance_rings.png` | Figure 4 距离分带图 |
| `scripts/part4_comparative_files/figure-html/topic-share-bar-1.png` | topic share bar |
| `scripts/part4_comparative_files/figure-html/sankey-plot-1.png` | sankey 图 |
| `scripts/part4_comparative_files/figure-html/top-mrt-destinations-1.png` | MRT top destinations |

---

## 四、本轮修改的核心逻辑

### 1. topic 覆盖率提升的来源

topic 覆盖率的提升主要来自两步：

1. 构建 `station_topic_classification_supplemented.csv`
2. 在 Part 4 主脚本中加入 compound alias fallback

也就是说，这一轮并没有重新训练 Part 2 的 LDA 模型，而是**修正 Part 4 如何消费 Part 2 产出**。

### 2. 兼容不同字段名

补充版 topic 文件里，排序辅助列可能叫：

- `total_pois`
- `poi_count`

因此主脚本增加了 `topic_order_col` 判断逻辑，避免因为列名差异导致 `arrange(desc(...))` 失败。

### 3. 结果更依赖补充版 topic 文件

如果后续有人直接删除或忽略 `station_topic_classification_supplemented.csv`，Part 4 会退回原始 topic 分类文件，届时部分 topic 统计可能回落，和当前报告不一致。

---

## 五、如何重新运行

### Step 1：重建补充版 topic 文件

在仓库根目录运行：

```powershell
python scripts/build_station_topic_classification_supplemented.py
```

如果本机 `python` 不在 PATH，也可以改用对应解释器绝对路径。

### Step 2：重新渲染 Part 4 HTML

当前环境可用的 Rscript 路径是：

```powershell
& 'C:\Program Files\R\R-4.5.2\bin\Rscript.exe' -e "rmarkdown::render('part4_comparative.Rmd', output_file='part4_comparative.html')"
```

工作目录应为：

```text
scripts/
```

### Step 3：重新导出 Word 报告

在仓库根目录运行：

```powershell
python scripts/export_part4_tables_to_word.py
```

这会生成：

- `docs/part4_results_report.docx`
- `docs/part4_result_tables.docx`

---

## 六、交接时需要注意的事项

### 1. `scripts/part4_comparative.Rmd` 是唯一可信源码

`part4_comparative.html`、`part4_comparative.knit.md` 和 `*_files/figure-html/*.png` 都是渲染产物。后续如果需要改文案、改图、改统计逻辑，应只改 `Rmd`，然后整体重渲染。

### 2. 目录里有很多临时检查脚本

当前工作区里存在多个 `.tmp_*.R` 文件，它们主要是本轮排查 topic coverage、站点缺失、表格差异时留下的临时检查脚本，不属于正式 pipeline。

交接时可以：

- 保留作为排查痕迹
- 或在确认不再需要后统一清理

但不要把它们误认为正式分析入口。

### 3. Word 报告脚本依赖 markdown caption 文本精确匹配

`scripts/export_part4_tables_to_word.py` 里是按表题和图题文本抓取内容的。如果以后改了 knit markdown 里的表 caption，但没同步改这个 Python 脚本，导出会失败或抓错内容。

### 4. Figure 编号和文件名并不完全一一对应

例如当前 distance rings 图在脚本里保存为：

- `part4_fig6_distance_rings.png`

但在报告叙述里它是 Figure 4。这是历史命名遗留，暂时没有影响，但交接时最好知道这一点，避免误以为文件编号和论文编号总是同步。

### 5. 当前工作区不是干净状态

仓库里已有若干未跟踪或已修改文件，包括：

- 新生成的 docx
- html / knit / figure 输出
- 临时脚本

接手的人如果要提交，建议先确认提交范围，不要把无关临时文件一起带进去。

---

## 七、建议的下一步

1. 如果报告中的 Table 1 / topic coverage 数值还要用于论文正文，建议把最终数值补写进一份 `progress` 或 `report notes` 文档，避免只存在于 HTML/Word 导出物中。
2. 如果后续还会频繁改图题和 caption，建议把 `export_part4_tables_to_word.py` 中的 `FIGURE_SPECS` 与 `TABLE_SPECS` 抽成单独配置文件，减少手工同步成本。
3. 如果 Part 2 后续再次更新 `station_topic_classification.csv`，需要重新执行补充脚本并重跑 Part 4，否则当前报告和上游数据会失配。

---

## 八、一句话总结

这一轮 Part 4 工作的本质，是**修正站点 topic 映射、提升 destination-topic 覆盖率、微调图表表达，并把更新后的结果重新落到 HTML/PNG/Word 导出物中**。后续接手时，优先围绕 `part4_comparative.Rmd` 和 `station_topic_classification_supplemented.csv` 继续即可。
