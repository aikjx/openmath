---
id: OM-C-TG-0001
title_zh: 朴素可测性公设（体积在刚体运动下不变且定义于所有有界集）
status: PROPOSED
---

# OM-C-TG-0001 · 朴素可测性公设（体积在刚体运动下不变且定义于所有有界集）

\[ \exists\ \mathrm{vol}:\ \mathcal{P}(\mathbb{R}^{3})\to[0,\infty],\quad \mathrm{vol}\ \text{可数可加、刚体运动不变、}\ \mathrm{vol}([0,1]^{3})=1 \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-C-TG-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **数学主张状态** | `REFUTED` |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

这是几何直觉里那条不言自明的话：任何一块有界图形都有一个体积，移动旋转它不改体积，切成可数块则体积相加。三条单独都无可争议，而 Banach-Tarski（OM-T-TG-0002）证明三者不能同时成立——被放弃的那条是「对所有子集都有定义」，代价是承认存在不可测集。本卡的登记方式值得留意：它是一条**被否证**的主张，所以 current_status 写 REFUTED，而记录级 status 仍是 PROPOSED（L1），冲突边两边各记一次，图上从两侧都能走到对方。

## 二、前提

- 要求对**所有**子集定义
- 要求可数可加与刚体运动不变性
- 默认约定：[0,1]^{3} 的体积归一为 1；本卡刻意不写 \mu——\mu 在本库留给一般测度（见 OM-D-PR-0001）

## 三、关系

- 冲突（对称记账，两侧均写）：OM-T-TG-0002
- 相关：OM-T-TG-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与 OM-T-TG-0002 的冲突对称记账：定理一侧与公设一侧各写一次 contradicts，否则 CONTRADICTION_ASYMMETRIC 会点名单边账。

## 五、来源

- Wagon, S., The Banach-Tarski Paradox (1985), ch.1, §12
- Jech, T., Set Theory, Millennium ed. (2003), §10.1 (Solovay 模型的可测性)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

