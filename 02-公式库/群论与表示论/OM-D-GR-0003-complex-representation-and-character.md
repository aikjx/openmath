---
id: OM-D-GR-0003
title_zh: 复表示与字符
status: PROPOSED
---

# OM-D-GR-0003 · 复表示与字符

\[ \rho:G\to \mathrm{GL}(V),\qquad \chi_\rho(g)=\mathrm{tr}\,\rho(g) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-GR-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GR（群论与表示论） |
| **录入** | 2026-10-11 |

## 一、要点

字符把表示这件「同态到一个矩阵群」的活压成一个复数值类函数，而它压得不亏：特征 0 下有限群的表示由其特征完全决定。本条要为图上做一件事：把「正交关系」用到的 chi_i、delta、GL(V) 挂在一处定义上，并把 delta（Kronecker 记号）在此固定为「指标相同取 1、否则取 0」，以免与同批 OM-T-GR-0002 里的 delta 被读成别的记号。边界：本卡不涉及模表示（特征 p 的情形完全可约失效，那是另一套语言）。

## 二、前提

- V 为有限维复向量空间
- chi 是类函数（在共轭类上常值）
- 默认约定：特征 0 保证 Maschke 完全可约，本卡的字符口径据此取不可约字符

## 三、关系

- 用到：OM-D-AL-0001
- 相关：OM-D-AL-0001, OM-T-GR-0002, OM-D-GR-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 为第 2 批 OM-T-GR-0002 补 chi_i、delta、GL(V) 三个记号；uses 挂 OM-D-AL-0001 因为表示的定义就是同态。

## 五、来源

- Serre, J.-P., Linear Representations of Finite Groups (1977), §1.1-2.1
- Fulton and Harris, Representation Theory: A First Course (1991), §1.1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

