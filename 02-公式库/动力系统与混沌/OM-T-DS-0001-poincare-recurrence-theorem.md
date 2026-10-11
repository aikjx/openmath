---
id: OM-T-DS-0001
title_zh: Poincare 回归定理
status: PROPOSED
---

# OM-T-DS-0001 · Poincare 回归定理

\[ \mu(X)<\infty,\ g:X\to X\ \text{保}\ \mu\ \text{测度}\ \Longrightarrow\ \mu\text{-a.e.}\ x\in\mathcal{A}\ \exists n\ge 1:\ g^{n}x\in\mathcal{A} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-DS-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | DS（动力系统与混沌） |
| **录入** | 2026-10-11 |

## 一、要点

证明短得可信：若有一批点离开 \mathcal{A} 后永不返回，它们的各次原像给出一列互不相交、测度都等于 \mu(\mathcal{A}) 的集合，全部塞进有限测度空间，于是只能是一列零测集。有限体积的保守系统不能「一去不回」，这就是统计力学里为什么要把遍历性与回归一起讨论。两条边界：一，有限测度不可去掉（平移在实线上保测但不回归）；二，回归时间可以长到没有可用上界，所以它**不**支持「系统在可观测时间内回到初态」这类物理口号。

## 二、前提

- X 带有限测度 \mu
- g 可逆且保 \mu 测度
- \mathcal{A} 为可测集
- 默认约定：「回归」指几乎每个 \mathcal{A} 中的点会无穷多次回到 \mathcal{A}，本卡按无穷多次口径写

## 三、关系

- 用到：OM-D-PR-0001
- 相关：OM-T-PR-0001, OM-D-PR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条的 MSC 号（37A35）按本库口径只作粗索引，不是分类学断言。

## 五、来源

- Poincare, H., Sur le probleme des trois corps et les equations de la dynamique (1890)
- Walters, P., An Introduction to Ergodic Theory (1982), §1.4

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

