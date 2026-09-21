# Automation Run Memory — OpenMath 自动摄取流水线

## 运行记录
- 运行时间：2026-09-19T09:09（GMT+8）
- 触发：定时自动化任务
- 执行命令：受管 Python `C:/Users/mo/.workbuddy/binaries/python/versions/3.13.12/python.exe` 运行 `06-AI自动化/01-工作流/openmath_ingest.py`
- 退出码：0（成功，未因网络问题报错退出；本次网络可用，10/10 CD 实时抓取）

## 本次结果（高层汇总，非全量）
- CD 摄取：10/10 个成功，合计 91 个符号；原始快照落 `09-数据/openmath_cds/*.ocd`
- 论文索引：去重后 32 篇（arXiv API 实时检索），分类分布 cs.SC(10)/cs.MS(7)/math.RA(5)/math.QA(4)/cs.AI(4)
- 四维分析：CMP 可解析 106/114（率 0.9298 = 92.98%）；分析方程 113 条（含内置种子）
- 产物：`09-数据/openmath_cds/catalog.json`、`09-数据/openmath_4d_analysis.json`、`10-文献与索引/arxiv_index.json`、`06-AI自动化/01-工作流/RUN_REPORT.md`

## 诚实约束校验
- 三个 JSON 均含 `provenance.ai_assisted=true`
- `arxiv_index.json` 含 `fact_check.status=UNVERIFIED`
- 各 meta 含 honesty 注记：L0/L2 数据处理产物、非证明、方程求解为计算校验(L2)、CMP 解析成功不代表被证明(L4)
- 流水线未修改任何既有条目 status，未自称"完整/权威/终极"

## 备注
- openmath_sys 引擎位于 `D:/a10/aikjx/code/my_lib/openmath_sys/src`（仅依赖标准库，无需第三方包）
- 网络不可用时 fetcher 回退到 `openmath_sys/sample_data` 内置样例（仅 arith1.ocd 与 arxiv_sample.xml），不会报错退出

## 运行记录 (2026-09-20T09:20)
- 触发：定时自动化任务（九阶段全流水线 S1–S9）
- 执行：受管 Python 依次跑 `openmath_ingest/analyze/experiments/coalition/synthesis/meta/theory/audit/sequences.py`，9 阶段全部退出码 0。
- 关键事件：首轮执行时解析器处于损坏状态（`MathExpr` 缺 `functions` 字段，`parse_text` 吞掉 TypeError → 全量 `parse_ok=False`），导致 ① 四维分析 CMP 可解析 0/179、② analyze 0 方程、③ 恒等式产物全 0、④ 审计 1 失败（apery 缺外部参照）。该损坏在会话中途被修复（非本 agent 修改引擎）。
- 一致性处置：依「改引擎后须重生成受影响产物」原则，解析器修复后重跑全 9 阶段，产物恢复一致：CMP 可解析 42/137（方程型率 0.3066），恒等式产物 holds=20/fails=0/not_decidable=4/unevaluable=1，审计 4163 项全部通过（0 失败），验证器 116 项全过（真 34/34、假 11/11）。
- 唯一持续异常（与解析器无关，真实引擎能力缺口）：序列阶段自核验违规 1 项（`diff::apery`——差分变换对理论上封闭的 P-recursive 丢失 Apéry 序列的 P-recursive 性质），变换封闭性在理论封闭变换上真正丢失 1 条，已正确标注为「搜索失败/本引擎能力缺口」而非数学结论。
- 理论锻造：候选 411、留出集通过 343、规模外推证伪 42、重发现已知定理 5。
- 恒等式产物分布（09-数据/numeric_solutions.json）：holds=20, fails=0, not_decidable=4, unevaluable=1, symbolic_failed=25。

## 运行记录 (2026-09-20T10:29)
- 触发：续跑——核对上一轮标记的「唯一持续异常」diff::apery。
- 实证结论：该异常是阶段 S9 产物过期，非引擎能力缺口。当前引擎 P_DEG_MAX=4 已能找到 diff(apery) 的 order=3/deg=4 递推（两组实验复刻 transform_closure 逻辑均得 precursive_lost=False）。根因：sequence_theory.json 在 P_DEG_MAX=3 时代生成，参数提到 4 后未重生成产物。
- 处置：用受管 Python 重跑 openmath_sequences.py（退出 0，36s）。重新生成 sequence_theory.json / sequence_candidates.json / SEQUENCE_REPORT.md。
- 结果：自核验违规 1→0（12 项全过）；理论封闭变换（diff/prefix_sum/binomial）性质丢失 1→0；序列 31 / 重发现 19 / 候选 4 / 外推证伪 0 / 独立复核 479 项 0 失败。未改引擎代码。
- 相邻观察：even_subseq(apery) 仍记 precursive_lost，但 even_subseq 非封闭变换、且不违规（仅 31 项，4×4 搜索需 discovery_len≥33 被安全跳过），属长度边界，已正确排除出封闭性判据。
- 交付：诊断报告 06-AI自动化/01-工作流/DIFF_APERY_RESOLUTION.md。


## 运行记录 (2026-09-21T09:27)
- 触发：定时自动化任务（十阶段全流水线 S1-S10，顺序 ①②③④⑤⑥⑦⑩⑧⑨）
- 执行：受管 Python 3.13.14 依次跑 ingest/analyze/experiments/coalition/synthesis/meta/theory/millennium/audit/sequences.py，10 阶段全部退出码 0。
- 引擎现状：解析器已原生支持隐式乘法等（ingest.py 2026-09-20 23:34 更新）。本次无回退。
- ① 摄取：38 CD / 294 符号（联网 38、本地回退 0、XML 失败 0）；CMP 可解析 60/179(0.3352)、方程型 60/137(0.438)；防覆写闸门通过（cmp_parsed=60 ≥ 上一轮 42 一半，无 .rejected）。
- ② analyze：38 CD/294 符号/179 性质/58 方程；结构缺口 48；未解猜想 11（5 个无已实现方法）；方法 46（已实现 27）。
- ③ experiments：ABC q>1 三元组 57（max q=1.455673）；Goldbach 全偶数有分拆=True；孪生素数 2160 对；pi(x) li 误差 0.39% vs x/ln x 9.45%；Collatz mod6 均值 91.73。
- ④ coalition：52 成员（实现 33/未实现 19/拒 0）；方向覆盖率 37.1%->54.5%->100%；可能性空间名义 ~2.96e28、语义上界 5330。
- ⑤ synthesis：12 范式、完全空白 2（analogy/transform）；11 猜想 constitutes_proof 全 False；有限化定理 5；D1-D6 六维。
- ⑥ meta：方法库 110 条（覆盖率 9.1%）；递归 L1=83/L2=20/L3=7、不动点 4 轮、自核验违规 0；维度矩阵 13/72(18.1%)；结构实验 同调/群 全匹配=True；孤儿能力 20。
- ⑦ theory：候选 411、留出通过 343、规模外推证伪 42、重发现已知定理 5；自核验 6/0。
- ⑩ millennium：命题 7（未解 6）、开放叶 15、实验 8、自核验 8/0。shadow_implies_full 七题全 False(=0)；YM 无实验（四维量子测度未构造）；N(T) 辐角法 341.0 与符号变号 341 一致、偏离整数 0.0；S(T) 0.260502 vs 0.2605 吻合。
- ⑧ audit：4452 检查项、失败 0；自核验 6/0。验证器 117/117（真 35/35、假 11/11）；C4 模消元 vs 精确高斯消元 28 序列 0 分歧；序列递推独立重算 36 候选 0 分歧；证伪元检验 8/8 定位；千禧 288 项全过。
- ⑨ sequences：序列 31、重发现 19(候选)/13(序列)、候选 4、外推证伪 0；独立复核 479/0；递推重算分歧 0；变换封闭性 186 组、理论封闭变换丢失 0；自核验 12/0。
- 身份产物（numeric_solutions.json）：holds=40, fails=3, not_decidable=14, unevaluable=2；14 条拒答原因 parse_suspect 9 / logic 1 / non_elementary 3 / equation 1；sin A cos B+cos A sin B=sin(A+B) 已移出拒答集（移入判准，符合回归护栏）。
- 全流水线：各阶段自核验违规均 0；审计失败 0；双路径对账（C4、递推重算、N(T) 辐角 vs 变号、S(T) 两法）零分歧；理论封闭变换零丢失。无异常需上报。
