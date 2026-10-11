---
id: OM-T-CB-0002
title_zh: Sperner 引理
status: PROPOSED
---

# OM-T-CB-0002 · Sperner 引理

\[ \text{满足 Sperner 标号条件的 }d\text{-单纯剖分中，全标号 }d\text{-单形的个数}\ \equiv\ 1\ (\mathrm{mod}\ 2) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-CB-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | CB（组合数学） |
| **录入** | 2026-10-11 |

## 一、要点

Sperner 引理本身完全是组合的：数一下带全标号的单形，模 2 得 1。它之所以重要，是因为它给出 Brouwer 不动点定理的**离散证明路线**——把剖分加细，全标号单形就逼出一个不动点。这一步骤把「拓扑定理需要分析/同调」的直觉换成「组合计数加极限」，这也是它在构造数学里比 Brouwer 更常被引用的原因。边界：本卡登记的是模 2 的计数陈述，不涉及带符号的版本（那给的是度数）。

## 二、前提

- 单纯形的 d+1 个顶点标号取自 \{0,1,\dots,d\} 且遵守边界约束
- 剖分为有限单纯剖分
- 默认约定：按模 2 计数，故结论是奇数而非某个具体数

## 三、关系

- 用到：OM-D-TG-0001
- 相关：OM-T-CB-0001, OM-D-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条是 OM-T-TG-0001 的 uses 上游；把这条链记进图里，是为了让 02 图上能看见「组合⇒拓扑」这类跨域依赖，而不是只在散文里说。记号一侧：本卡的 d 与 Ramsey 卡的四个记号同属一笔债，落在 UNDEFINED_SYMBOL 账上。

## 五、来源

- Sperner, E., Neuer Beweis für die Invarianz der Dimensionszahl und des Gebietes (1928)
- Soifer, A., Ramsey Theory, 2nd ed. (1994), ch.4

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

