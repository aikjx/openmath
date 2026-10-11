---
id: OM-T-PR-0001
title_zh: Kolmogorov 强大数律
status: PROPOSED
---

# OM-T-PR-0001 · Kolmogorov 强大数律

\[ \bar{X}_n=\frac{1}{n}\sum_{i=1}^{n}X_i\ \longrightarrow\ \mathbb{E}[X_1]\quad a.s. \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-PR-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | PR（概率论） |
| **录入** | 2026-10-11 |

## 一、要点

强大数律说的是**整条轨道**收敛（除一个零测集外，每个样本点的均值序列都收敛），弱大数律只说每个 n 处偏离的概率趋于 0。这两者的差距不是定量而是类型：前者是关于序列的陈述，后者是关于一列事件的陈述。一阶矩存在是 Kolmogorov 证的门槛，也是真正的门槛——若 E|X_1|=infty，均值序列可以几乎必然不收敛。边界：本卡不给收敛速率，速率属于另一族问题（见 CLT 与不等式）。

## 二、前提

- X_i 独立同分布
- \mathbb{E}[|X_1|]<\infty（一阶矩存在即可，这是 Kolmogorov 版）
- 默认约定：概率空间足够承载无限序列（存在性由标准构造给出）

## 三、关系

- 用到：OM-D-PR-0001
- 相关：OM-T-PR-0002, OM-T-DS-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向本批的 OM-D-PR-0001（概率空间与随机变量定义）。

## 五、来源

- Kolmogorov, A., Sur la loi des grands nombres (1930)
- Durrett, R., Probability: Theory and Examples, 5th ed. (2019), §2.2

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

