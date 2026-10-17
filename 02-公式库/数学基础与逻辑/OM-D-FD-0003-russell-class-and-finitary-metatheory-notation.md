---
id: OM-D-FD-0003
title_zh: 罗素类与有穷数学的记号
status: PROPOSED
---

# OM-D-FD-0003 · 罗素类与有穷数学的记号

\[ \mathcal{R}=\{x:x\notin x\},\qquad \mathrm{F}\ \text{为有穷数学（finiter Mathematik），}\ \mathrm{F}\vdash\mathrm{Con}(T)\ \text{指在}\ \mathrm{F}\ \text{内给出一致性证明} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-FD-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | FD（数学基础与逻辑） |
| **录入** | 2026-10-11 |

## 一、要点

两枚记号分处基础层的两端：`\mathcal{R}` 是朴素概括原则的**反例载体**（OM-X-FD-0001 用它把该原则判死），`\mathrm{F}` 是纲领性难题（OM-P-FD-0001 希尔伯特纲领）里那个「有穷」一侧的名字。

本卡的诚实边界写在 assumptions 里：定义 `\mathrm{F}` 的记号**不等于**选定它的刻度。第二不完备定理的射程对 F 的具体选择敏感——若 F 强到能证 Con(T)，它自己就得被更强系统判一致性。纲领的那条陈述至今未决，把记号写清楚只是让它可讨论，不构成任何推进（红线一）。

`\mathcal{R}` 与裸 `R`（OM-T-ST-0001 里指二元关系）是两个串，本库按整串聚合，因此不构成同名假绿；这也是花体/正体记号在本库里的实际作用。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：\mathcal{R} 按朴素概括原则写成类；本卡不断言它是集合（它不是，这正是 OM-X-FD-0001）
- 默认约定：F 的具体刻度由希尔伯特纲领的选择决定（原始递归、有穷算术 PRA 等），本卡只固定记号并写明「不固定刻度则 Con 的陈述不唯一」这一层
- 默认约定：Con(T) 与 Proof_T 的记号口径在 OM-D-FD-0002，本卡不重复定义

## 三、关系

- 用到：OM-D-FD-0002
- 相关：OM-X-FD-0001, OM-P-FD-0001, OM-D-FD-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡。只固定 \mathcal{R} 与 \mathrm{F} 两枚记号；罗素类不是集合这一主张归 OM-X-FD-0001，希尔伯特纲领的未决状态归 OM-P-FD-0001。

## 五、来源

- Russell, B., The Principles of Mathematics (1903), ch.XII（不自属类导致的矛盾）
- Hilbert, D., Die Grundfragen der mathematischen Erkenntnis, Naturwissenschaftliche Wochenschrift 29 (1930)（有穷数学 F 的纲领表述）
- van Heijenoort, J. (ed.), From Frege to Gödel: A Source Book in Mathematical Logic, 1879–1931, Harvard (1967)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

