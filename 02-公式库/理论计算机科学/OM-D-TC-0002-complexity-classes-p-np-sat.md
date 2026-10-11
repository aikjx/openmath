---
id: OM-D-TC-0002
title_zh: 复杂性类 P、NP 与 SAT
status: PROPOSED
---

# OM-D-TC-0002 · 复杂性类 P、NP 与 SAT

\[ \mathrm{P}\ \subseteq\ \mathrm{NP},\qquad \mathrm{SAT}\in\mathrm{NP},\qquad \mathrm{SAT}\in\mathrm{P}\ \Longrightarrow\ \mathrm{P}=\mathrm{NP} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-TC-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TC（理论计算机科学） |
| **录入** | 2026-10-11 |

## 一、要点

第三段式（SAT 在 P ⇒ P=NP）不是 NP 完全性的**定义**，而是它的一个直接推论：SAT 是 NP 难的，所以若它落在 P 里，NP 中每个语言都能多项式归约进 P。要留的两处精度：一，「P 是否等于 NP」是关于**这些具体定义**的问题，换归约口径（如 Levin 归约）或换模型（如概率、量子）都会改问题；二，本卡刻意不把 P⊆NP 写成严格包含，因为严格性正是未决的那件事。与 OM-D-TC-0001（NP 完全的定义）分条：那里定义「完全」，这里定义「类」。

## 二、前提

- 判定问题编码成字母表上的语言
- 机时为 n 的多项式，机存自变量对数
- 默认约定：归约取多项式时间多一归约（Karp 归约），本卡不登记对数空间版本

## 三、关系

- 相关：OM-D-TC-0001, OM-T-TC-0002, OM-P-TC-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 1 批的 OM-T-TC-0002（Cook-Levin）与 OM-P-TC-0002（P vs NP）在陈述里用了 P、NP、SAT 三个记号而无定义条目；本条把它们补成 kind=definition 的记录。

## 五、来源

- Cobham, A., The intrinsic computational difficulty of functions (1964)
- Garey and Johnson, Computers and Intractability: A Guide to the Theory of NP-Completeness (1979), §1-3

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

