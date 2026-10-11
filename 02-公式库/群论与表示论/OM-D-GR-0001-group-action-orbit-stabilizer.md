---
id: OM-D-GR-0001
title_zh: 群作用、轨道与稳定子
status: PROPOSED
---

# OM-D-GR-0001 · 群作用、轨道与稳定子

\[ G\times X\to X,\quad \mathrm{Orb}(x)\ \cong\ G/\mathrm{Stab}(x) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-GR-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GR（群论与表示论） |
| **录入** | 2026-10-11 |

## 一、要点

轨道-稳定子双射把「G 有多少种把 x 搬走的方式」和「G 里哪些元素不动 x」这两件事连起来，商在这里出现得很具体：陪集 gStab(x) 就是同一个落点。它是 Sylow 定理的标准证明里唯一的机械装置（在陪集集合上作用并数轨道），所以本批把它单独立条，而不是把 Sylow 的 uses 直接挂到同态定义上。

## 二、前提

- 作用满足 e·x=x 与 g·(h·x)=(gh)·x
- 默认约定：X 为集合（本卡不登记拓扑作用的情形）

## 三、关系

- 用到：OM-D-AL-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-D-AL-0001：轨道与 G/Stab 的同构要用陪集与商的语言。

## 五、来源

- Lang, S., Algebra, revised ed. (1965), I.2
- Isaacs, I. M., Finite Group Theory (1990), §2.1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

