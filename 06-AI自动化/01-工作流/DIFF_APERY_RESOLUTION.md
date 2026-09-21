# `diff::apery` 异常诊断与处置报告

- 生成时间：2026-09-20T10:29（GMT+8）
- 处置方式：重新生成阶段 S9 产物（**未改动任何引擎代码**）
- 诚实等级：L2（计算核对）；本文件是对流水线产物的诊断，非数学证明。

---

## 1. 结论（先说结果）

此前报告中的「唯一持续异常」——`diff::apery`（自核验违规 1 项 + 变换封闭性在理论封闭变换上丢失 1 条 P‑recursive）——经实证核对，**并非引擎能力缺口，而是阶段 S9 产物的过期（stale）记录**。

当前磁盘上的引擎（`P_DEG_MAX = 4`）已经能找到 Apéry 差分序列的 `order=3 / deg=4` 递推。重新生成 S9 产物后，关键指标翻转：

| 指标 | 旧产物（过期） | 新产物（本次重生成） |
| --- | --- | --- |
| 自核验违规数（共 12 项） | 1 | **0** |
| 理论封闭变换（diff/prefix_sum/binomial）上性质丢失 | 1 条（apery 差分） | **0** |
| 序列总数 / 重发现 / 候选 | 31 / 19 / 4 | 31 / 19 / 4（不变） |
| 外推证伪 | 0 | 0 |
| 独立复核 | 479 项 0 失败 | 479 项 0 失败 |
| 递推重算分歧 | 0 | 0 |

无需修改引擎代码。

---

## 2. 根因

1. Apéry 数 `A(n)` 自身满足 `order=2 / deg=3` 的 P‑recurrence（已知校准件，已在 `KNOWN_PRECURENCES` 中逐项验过）。
2. 其差分 `ΔA(n) = A(n+1) − A(n)` 满足 `order=3 / deg=4` 的 P‑recurrence。这符合 P‑recursive 序列对差分封闭的定理（阶最多 +1、次数最多 +1）。
3. `sequences.py` 的对照实验（`tests/c4_ablation.py`）**早已发现**这一点，并据此把 `P_DEG_MAX` 从 3 提到 4。源码 1000–1014 行注释明确写着：「apery 的差分实际需要 order=3 / deg=4」。
4. 但 `09-数据/sequence_theory.json` 与 `06-AI自动化/01-工作流/SEQUENCE_REPORT.md` 是在 `P_DEG_MAX=3` 时代生成的——当时 `deg=4` 无法表示该差分，故被记为 `precursive_lost=["apery"]`。**引擎参数已改，产物未重生成**，于是出现了「引擎已修、报告未更」的假异常。
5. 这正对应本项目诚实红线之一：**改引擎后须重生成受影响产物**。本处置即落实该红线。

---

## 3. 实证验证（用当前引擎直接跑的两组实验）

- **实验 A**：对 `diff(apery)` 直接调用 `discover_polynomial_recurrence`，默认边界 `(max_order=4, max_deg=4)` → 命中 `order=3 / deg=4`，`survived_extrapolation=True`。
- **实验 B**：复刻 `transform_closure` 对 `apery / diff` 行的完整判定逻辑（`base_prec`、`after_prec`、`relaxed_prec`、`degenerate_out`）→ `base_prec=True, after_prec=True, relaxed_prec=True, degenerate=False` ⇒ `precursive_lost = False`。

两组实验一致证明：报告里的 `lost` 是过期产物，不是当前引擎的实时结论。

---

## 4. 处置（已执行）

- 用受管 Python 重跑阶段 S9：`06-AI自动化/01-工作流/openmath_sequences.py`，36 秒完成，退出码 0。
- 重新生成：`09-数据/sequence_theory.json`、`09-数据/sequence_candidates.json`、`06-AI自动化/01-工作流/SEQUENCE_REPORT.md`。
- 其余阶段（S1–S8）产物与当前引擎状态一致，无需重跑。其中 S8 审计的 C4 模‑精确交叉核对是独立实现、独立于 `P_DEG_MAX`，不受本次参数影响。

---

## 5. 一个相邻但非缺陷的观察：`even_subseq(apery)`

重新生成后，`even_subseq`（偶数项子序列）变换对 `apery` 仍被记为 `precursive_lost`。说明如下：

- `even_subseq` **不在** `CLOSED_TRANSFORMS` 中，引擎从不据此判封闭性，故**不构成违规**（自核验第 11 项只查 diff/prefix_sum/binomial 三个封闭变换）。
- 实测：`even_subseq(apery)` 只有 31 项；要在 `4×4` 及以上边界搜索需要 `discovery_len ≥ 33`，超过可用项数，被安全阈值 `n_eq < n_unk + 4` 跳过（故 0 候选）。这是**项数长度边界**，不是能力缺陷。
- 数学上，P‑recursive 序列的偶数子序列确为 P‑recursive，但其递推阶/次更高，需要更多项才能搜到；当前如实记为「观测」而非「丢失」，符合诚实口径。
- 处置：保持现状。如希望该观测也消失，可对少数序列单独延长 `even_subseq` 的搜索项数（属功能扩展，不紧急）。

---

## 6. 算法联盟（S4）推进建议（用户第二项提问）

现状（来自 S4 产物）：注册方法 **42**（已实现 23 / 未实现 19 / 安全门拒 0）；突破路线图 **19** 个未实现方法；方向覆盖率 **37.1% → Top5 54.5% → 100%**；BSD / Hodge / NS / P≠NP / Yang‑Mills 五个猜想当前可用方法数为 **0**。

建议（**本轮未执行**，需设计决策）：推进 = 实现那 19 个未实现方法以提升方向覆盖率，并为 5 个零方法猜想开辟方向。这是较大的工程，应单独开一轮「实现规划 + 对照实验 + 安全门」后再做，不宜顺手修改。

---

## 7. 下一步

1. `diff::apery`：已闭环（重生成即清除），无需改引擎。
2. `even_subseq(apery)`：属长度边界观察，已正确排除出封闭性判据；如需消除，单独延长该序列搜索项数（可选）。
3. 算法联盟：建议下一轮先规划再实施，不在本次处理。
