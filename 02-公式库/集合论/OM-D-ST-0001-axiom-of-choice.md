---
id: OM-D-ST-0001
title_zh: 选择公理
status: PROPOSED
---

# OM-D-ST-0001 · 选择公理

\[ \forall \mathcal{A}\ \bigl(\emptyset \notin \mathcal{A}\ \rightarrow\ \exists f\ \forall A \in \mathcal{A}\ f(A) \in A\bigr) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-ST-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

登记这一条是为了让「独立性」在图上有主语：CH 与 ¬CH（OM-C-ST-0001/0002）的独立性都是在 ZFC 这一侧讲的，也就是以本条为公理的一侧。值得写清的一条诚实边界：AC 与 ZF 的独立性方向不对称——ZF ⊬ AC 需要 Fraenkel-Mostowski 对称模型（再经 Jech-Sochor 迁移到集合论基座），而 ¬AC 与 ZF 的相容性由 Feferman-Levy 型模型给出；这些不是本卡的结论，本卡只把公理本身立住，把独立性留在后续记录。

## 二、前提

- A 是由非空集合组成的族
- 默认约定：ZF 的其余公理
- 默认约定：函数按有序对的集合定义理解

## 三、关系

- 蕴含：OM-T-ST-0001
- 相关：OM-T-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条 implication 指向良序定理，良序定理一侧同样写着它蕴含本条：等价性在 ZF 内双向可证，所以图上要出现两条 implies 边而不是一句「它们等价」。

## 五、来源

- Zermelo, E., Math. Annalen 65 (1908)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

