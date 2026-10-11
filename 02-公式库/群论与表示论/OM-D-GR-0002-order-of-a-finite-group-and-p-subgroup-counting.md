---
id: OM-D-GR-0002
title_zh: 有限群的阶与 p-子群计数
status: PROPOSED
---

# OM-D-GR-0002 · 有限群的阶与 p-子群计数

\[ |G|=p^{a}m,\ p\nmid m,\qquad n_p=\lvert\{P\le G:\lvert P\rvert=p^{a}\}\rvert \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-GR-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GR（群论与表示论） |
| **录入** | 2026-10-11 |

## 一、要点

把记号单独立条有一个实际理由：Sylow 定理的三条各自量的不是同一件事——存在量的是子集的势，共轭量的是共轭作用下的轨道数，计数约束量的是 n_p 的同余与整除性质。若不先把 |G|=p^a m 与 n_p 写成符号，三条就会在图上塌成一条模糊的「Sylow 定理」。边界：本卡只固定记号与计数口径，不断言任何关于 n_p 的取值范围（那属于 OM-T-GR-0001 的内容）。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：G 为有限群，|G| 为其元素个数
- 默认约定：a 为 p 在 |G| 中的重数，m 为与 p 互素的余因子

## 三、关系

- 用到：OM-D-GR-0001
- 相关：OM-D-GR-0001, OM-T-GR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 为第 2 批的 OM-T-GR-0001 补 |G|、p、a、m、n_p、P 六个记号的定义条目。

## 五、来源

- Isaacs, I. M., Finite Group Theory (1990), §2.1
- Lang, S., Algebra, revised ed. (1965), I.2, §3

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

