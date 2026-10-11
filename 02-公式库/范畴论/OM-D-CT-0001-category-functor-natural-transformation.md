---
id: OM-D-CT-0001
title_zh: 范畴、函子与自然变换
status: PROPOSED
---

# OM-D-CT-0001 · 范畴、函子与自然变换

\[ \mathcal{C}=\bigl(\mathrm{Ob}(\mathcal{C}),\ \mathrm{Hom}(A,B),\ \circ,\ \mathrm{id}\bigr) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-CT-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | CT（范畴论） |
| **录入** | 2026-10-11 |

## 一、要点

这条定义的价值在它的第三项：**自然变换是态射的态射**。函子之间的比较不需要新引入一层「结构」，它就是每个分量处的态射，且与所有态射可交换。有了自然性，泛性质才有意义——一个对象由它与其他所有对象的态射关系确定，而唯一性是同构而非相等，这正是自然变换语言要说的那件事。本卡的诚实边界：本库没有形式化任何范畴论证明，也没有把泛性质写成同构类唯一的机器可判定形式；这里登记的是定义本身与其在图里的邻接关系。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：每个 Hom(A,B) 是集合（本地小范畴），或已选定一个宇宙来容纳对象类
- 默认约定：复合满足结合律，id 是双侧单位

## 三、关系

- 本条暂无出边（会被 ORPHAN 点名，故不应出现）

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条只有入边（Yoneda 与 Lawvere 都 uses 它）没有出边；若 ORPHAN 把它点名，那是它暂无同库可连的上游，不是缺陷。

## 五、来源

- Mac Lane, S., Categories for the Working Mathematician, 2nd ed. (1998)
- Leinster, T., Basic Category Theory (2014)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

