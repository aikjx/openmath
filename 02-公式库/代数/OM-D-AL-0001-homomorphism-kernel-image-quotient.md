---
id: OM-D-AL-0001
title_zh: 同态、核、像与商
status: PROPOSED
---

# OM-D-AL-0001 · 同态、核、像与商

\[ \varphi:G\to H,\quad \ker\varphi=\{g\in G:\varphi(g)=e_H\}\trianglelefteq G,\quad \mathrm{im}\,\varphi=\varphi(G)\le H \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-AL-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | AL（代数） |
| **录入** | 2026-10-11 |

## 一、要点

这条定义把「同构定理」这件事的全部体力活放在一处：商 G/N 的元素是陪集，而陪集上的运算良定义当且仅当 N 正规。核之所以特殊，是因为它是唯一一个让「把 N 视作相等」这件事与同态相容的子群——用范畴的话说，核是把这个同态变成等化的那个 congruence。诚实边界：本卡只登记定义与其邻接，不涉及任何本库内的构造性证明。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：乘法记法的群；核必须是正规子群，否则商集上没有良好定义的运算
- 默认约定：环的情形核换成双边理想，本卡只登记群的语言

## 三、关系

- 相关：OM-D-CT-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与 OM-D-CT-0001 记 related：同态在范畴观点下就是态射，核与商在加法范畴里有泛性质版本；本库没有把那条抽象路线记成独立条目，所以这里只连一条相关边。

## 五、来源

- Lang, S., Algebra, revised ed. (1965), I.3
- Hungerford, T. W., Algebra (1974), I.5

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

