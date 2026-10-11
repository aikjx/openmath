---
id: OM-T-AL-0001
title_zh: 第一同构定理
status: PROPOSED
---

# OM-T-AL-0001 · 第一同构定理

\[ G/\ker\varphi\ \cong\ \mathrm{im}\,\varphi \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-AL-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | AL（代数） |
| **录入** | 2026-10-11 |

## 一、要点

这条定理的实际用处是它给的构造方向：想证明两个群同构，就构造一个满同态并把它的核算清楚。它也解释了为什么「商掉什么」等价于「允许什么相等」——核里的元素正是被压成单位元的那一批。与米田连一条 related 边是有内容的：把 G/ker→im 看成由泛性质决定的唯一同构，正是「态射由它对源对象的商的作用决定」这一范畴式说法的群论形态。边界：本库未形式化该证明，L1 只表示结构良构。

## 二、前提

- varphi:G→H 为群同态
- 默认约定：商按正规子群 ker varphi 取

## 三、关系

- 用到：OM-D-AL-0001
- 相关：OM-T-CT-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-D-AL-0001：定理的陈述里 ker/im/商三个记号全靠那条定义。

## 五、来源

- Lang, S., Algebra, revised ed. (1965), I.3, Theorem 3.7
- Hungerford, T. W., Algebra (1974), I.5, Theorem 5.7

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

