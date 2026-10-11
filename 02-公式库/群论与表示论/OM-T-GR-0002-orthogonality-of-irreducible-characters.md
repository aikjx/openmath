---
id: OM-T-GR-0002
title_zh: 不可约字符的正交关系
status: PROPOSED
---

# OM-T-GR-0002 · 不可约字符的正交关系

\[ \frac{1}{|G|}\sum_{g\in G}\chi_i(g)\,\overline{\chi_j(g)}\ =\ \delta_{ij} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-GR-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GR（群论与表示论） |
| **录入** | 2026-10-11 |

## 一、要点

这条正交关系是「用字符把表示分类」这件事的机器：不可约字符在类函数空间里两两正交、模长为 1，所以任一字符按不可约字符展开的系数是非负整数，并且可以直接由内积算出。第二个正交关系（对固定 g 与不同类求和）则给出表的可逆性。诚实边界：本卡只登记第一条（列正交），第二条与实数域上的分裂字段问题不在本条范围内；uses 挂在同态定义上，因为表示就是同态 G→GL(V)。

## 二、前提

- G 为有限群
- 表示定义在复数域上（特征 0，Maschke 保证完全可约）
- chi_i、chi_j 取遍不可约字符
- 默认约定：类函数上取平均内积 (f,h)=(1/|G|) sum f(g) overline{h(g)}

## 三、关系

- 用到：OM-D-AL-0001
- 相关：OM-T-GR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与 OM-T-GR-0001 记 related：两者都是有限群结构的基本读数，一个数子群一个数表示；本库没有把它们之间的联系写成任何一条蕴含边。

## 五、来源

- Serre, J.-P., Linear Representations of Finite Groups (1977), §2.3
- Fulton and Harris, Representation Theory: A First Course (1991), §1.2

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

