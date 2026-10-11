---
id: OM-T-FD-0002
title_zh: 哥德尔第二不完备定理
status: PROPOSED
---

# OM-T-FD-0002 · 哥德尔第二不完备定理

\[ \mathrm{Con}(T)\ \Rightarrow\ T \nvdash \mathrm{Con}(T) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-FD-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | FD（数学基础与逻辑） |
| **录入** | 2026-10-11 |

## 一、要点

第二定理比第一定理更直接地打击纲领：纲领要求用**有穷手段**证明分析学（形式化为某个 T）的一致性，而有穷手段能形式化进 T 本身，于是若 T 一致，它就给自己的无矛盾性提供了一个 T 内的证明——正是定理排除的形态。需要留的诚实边界：定理只封锁「同一系统内的标准一致性陈述」这一条路，不封锁更强的系统（ZFC 能证 PA 的一致性）、真值语义的论证（Gentzen 用超限归纳到 ε₀ 证明 PA 一致性，代价是把可接受性转移到超限归纳的原则上）。所以「纲领被否证」这句话要连着它的例外一起读。

## 二、前提

- T 一致、递归可公理化、包含初等算术
- 一致性以标准算术化表达（Con(T) = ¬∃p Proof_T(p, ⌜0=1⌝)）
- 默认约定：可证性谓词满足 Hilbert-Bernays-Lob 三条可证条件

## 三、关系

- 冲突（对称记账，两侧均写）：OM-P-FD-0001
- 蕴含：OM-P-FD-0001
- 用到：OM-T-FD-0001
- 相关：OM-T-FD-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本卡的 current_status 留空：它是一条定理而非待决问题；被否证的主张登记在 OM-P-FD-0001。

## 五、来源

- Godel, K. (1931), §II
- Hilbert & Bernays, Grundlagen der Mathematik (1934/1939)
- Gentzen, Die Widerspruchsfreiheit der reinen Zahlentheorie (1936)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

