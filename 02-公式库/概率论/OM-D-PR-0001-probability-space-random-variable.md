---
id: OM-D-PR-0001
title_zh: 概率空间与随机变量
status: PROPOSED
---

# OM-D-PR-0001 · 概率空间与随机变量

\[ (\Omega,\mathcal{F},\mathbb{P}),\quad X:(\Omega,\mathcal{F})\to(S,\mathcal{S})\ \text{可测} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-PR-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | PR（概率论） |
| **录入** | 2026-10-11 |

## 一、要点

把概率写成三元组 (Omega, F, P) 的意义在于它把「随机」变成「可测」：随机变量不是随机取的数，而是一个函数， randomness 全在测度 P 里。这一步让强大数律、遍历定理与 Shannon 的编码定理共用同一套语言。边界：本卡只固定记号与口径，不讨论没有 sigma-代数结构时的其它概率表述（如 finitely additive 概率）。

## 二、前提

- \mathcal{F} 为 \sigma-代数
- \mathbb{P}(\Omega)=1 且 \mathbb{P} 可数可加
- 默认约定：本库的概率语言一律按 Kolmogorov 公理（测度论）口径写

## 三、关系

- 用到：OM-D-ST-0003
- 相关：OM-T-PR-0001, OM-T-DS-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条同时为第 3 批的概率记号补定义条目：\Omega、\mathcal{F}、\mathbb{P}、\mathbb{E}、\mu、\sigma、X_i、\bar{X}_n、a.s.、\mathcal{A} 与 \xrightarrow{\ d\ }，并把 sigma-代数这件事与集合论的关系（uses OM-D-ST-0003）记进图。

## 五、来源

- Kolmogorov, A., Grundbegriffe der Wahrscheinlichkeitsrechnung (1933)
- Billingsley, P., Probability and Measure, 3rd ed. (1995), §1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

