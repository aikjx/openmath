# 工作流：OpenMath 自动摄取流水线

> 归属：`06-AI自动化/01-工作流` · 角色映射：档案员(Archivist) + 计算师(Computer)
> 性质：**AI 辅助自动生成，未经人类复核**，不构成证明。

## 一、它做什么

一条命令完成「下载 → 整理 → 分析 → 运行」，把外部数学基础设施接入本库：

1. **下载**：OpenMath 官方内容字典(CD, `cd/Official/*.ocd`) 与 arXiv 数学论文。
2. **整理**：CD 原始快照放入 `09-数据/openmath_cds/`；论文去重索引放入 `10-文献与索引/arxiv_index.json`。
3. **分析**：解析 CD 中的数学性质(CMP) 与内置示例方程，跑四维逻辑框架（句法/语义/结构/计算），产出可解析覆盖率等指标。
4. **运行**：全部产物落到本仓库对应目录，并生成 `RUN_REPORT.md`。

## 二、运行

```bash
python D:/a10/aikjx/code/my_lib/openmath/06-AI自动化/01-工作流/openmath_ingest.py
```

底层引擎复用 `../openmath_sys`（纯标准库，零第三方依赖）。

## 三、产物与落点

| 产物 | 路径 | 说明 |
| --- | --- | --- |
| CD 原始快照 | `09-数据/openmath_cds/<name>.ocd` | 官方 CD 本地快照（引用优先原则） |
| 符号目录 | `09-数据/openmath_cds/catalog.json` | 各 CD 的符号与性质计数 |
| 四维分析 | `09-数据/openmath_4d_analysis.json` | CMP 可解析率 + 方程分类/求解(L2) |
| 论文索引 | `10-文献与索引/arxiv_index.json` | 去重论文 + 分类分布 |
| 运行报告 | `06-AI自动化/01-工作流/RUN_REPORT.md` | 本次运行摘要 |

## 四、四维分析指标

- **CMP 可解析率** = 被本解析器成功解析的 CD 性质数 / 全部性质数。解析成功**不代表被证明(L4)**，仅说明其语法可机读。
- **方程分类**：linear / quadratic / transcendental / constant 等（对方程取 `lhs - rhs` 判定）。
- **求解**：仅对单变量多项式（线性/二次）给出数值根，属 **L2 计算校验**，非 L4 形式化证明。

## 五、诚实约束（红线绑定）

- 所有产物 `provenance.ai_assisted = true`，未经人类复核。
- arXiv 预印本 `fact_check.status = UNVERIFIED`，不得作为本库 L3+ 证据。
- 方程求解一律标注为 L2 计算校验；绝不写"已证明""定理""完成"。
- 不自称"完整/权威/终极"；摄取覆盖率受 CD 列表与解析器能力限制。
- 任何反例出现时，按 [诚实红线](../00-宪章/02-诚实红线.md) 保留并标注，不静默删除。

## 六、扩展

- 扩充 `CD_NAMES` / `QUERIES` 即可扩大摄取范围。
- 解析器(`openmath_sys/parser.py`)支持更多函数/运算符后，CMP 可解析率会自然上升。
- 若要纳入本库正式条目，须经 `openmath new` 走 AKU 生命周期，而非停留在数据目录。
