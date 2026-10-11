---
id: OM-D-TG-0001
title_zh: 拓扑空间、连续映射与同胚
status: PROPOSED
---

# OM-D-TG-0001 · 拓扑空间、连续映射与同胚

\[ (X,\tau),\quad f:(X,\tau_X)\to(Y,\tau_Y)\ \text{连续}\ \Longleftrightarrow\ f^{-1}(\tau_Y)\subseteq\tau_X \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-TG-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

拓扑把「距离」换成了「哪些集合算开」，于是连续不再关于 eps-delta，而关于开集的原像。同胚就是这条等价关系的商：两个空间相同当且仅当存在双向连续的 bijection。诚实边界一处：本卡声明的 f 与 OM-D-CT-0002 里的 f 都是「所在陈述里的那个映射」，这是同一个泛用记号在两个语境下的用法，不构成两条不同的定义；两处都按局部绑定读。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：本卡取一般拓扑（不假设可度量化、不假设 Hausdorff）
- 默认约定：\overline{B}^{\,n} 指 R^n 中通常拓扑下的闭单位球

## 三、关系

- 用到：OM-D-ST-0003
- 相关：OM-D-CT-0001, OM-T-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-D-ST-0003：本库把「二元关系」这件事记在那条定义上，连续映射作为集合上的关系要靠它。

## 五、来源

- Munkres, J. R., Topology, 2nd ed. (2000), §12-18
- Willard, S., General Topology (1970), §6

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

