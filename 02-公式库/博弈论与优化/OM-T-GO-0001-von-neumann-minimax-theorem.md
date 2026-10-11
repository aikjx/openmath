---
id: OM-T-GO-0001
title_zh: von Neumann 极小极大定理
status: PROPOSED
---

# OM-T-GO-0001 · von Neumann 极小极大定理

\[ \max_{x\in\Delta_m}\ \min_{y\in\Delta_n}\ x^{\top}\,\mathcal{M}\,y\ =\ \min_{y\in\Delta_n}\ \max_{x\in\Delta_m}\ x^{\top}\,\mathcal{M}\,y \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-GO-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GO（博弈论与优化） |
| **录入** | 2026-10-11 |

## 一、要点

交换 max 与 min 不是恒等式——一般情形只有 max min <= min max。定理由此说的是：双线性＋单纯形这两条约束把间隙压成 0，于是零和博弈的双方值相等（博弈有值）。这也是线性规划对偶的最早形态之一。uses 记 Brouwer 是有依据的：von Neumann 的原证明走不动点路线；后来用凸分离（Fenchel）也能证，那是另一条路，本库不重复登记。边界：非零和情形不适用，那要换成 Nash 均衡概念。

## 二、前提

- \mathcal{M} 为实矩阵（支付表）
- 策略集为概率单纯形 \Delta_m、\Delta_n
- 默认约定：双线性型在紧凸集上连续，故可用不动点/分离超平面论证

## 三、关系

- 用到：OM-T-TG-0001
- 相关：OM-T-GO-0002, OM-T-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条与 OM-T-GO-0002 的差别是概念性的而非量的：零和博弈的「值」唯一，一般博弈的均衡可以有很多个，所以两条之间只记 related。

## 五、来源

- von Neumann, J., Zur Theorie der Gesellschaftsspiele (1928)
- Dantzig, G. B., Linear Programming and Extensions (1963), ch.8

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

