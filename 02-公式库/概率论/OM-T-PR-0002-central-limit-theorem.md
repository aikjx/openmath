---
id: OM-T-PR-0002
title_zh: 中心极限定理
status: PROPOSED
---

# OM-T-PR-0002 · 中心极限定理

\[ \frac{\sqrt{n}\,(\bar{X}_n-\mathbb{E}[X_1])}{\sigma}\ \xrightarrow{\ d\ }\ \mathcal{N}(0,1) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-PR-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | PR（概率论） |
| **录入** | 2026-10-11 |

## 一、要点

中心极限定理给的是一阶矩之外还需要**二阶矩**的那一层信息：波动的标度是 1/sqrt(n)，且极限形状与分布本身无关（普适性）。它与强大数律的分工要在图上分开记：一个说均值收敛到什么，一个说收敛的**误差长什么样**。方差无限时极限不再是正态，而落到稳定律族——那属于本条之外的账。边界：本卡登记 Lindeberg-Levy（同分布、二阶矩有限）版本，不是一般的 Lindeberg-Feller 三角阵版本。

## 二、前提

- X_i 独立同分布
- \sigma^{2}=\operatorname{Var}(X_1) 存在且 0<\sigma^{2}<\infty
- 默认约定：收敛指分布函数在连续点处逐点收敛（弱收敛）

## 三、关系

- 用到：OM-D-PR-0001
- 相关：OM-T-PR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与 OM-T-PR-0001 记 related（同一对象的两种收敛口径），刻意不记 implies：两条定理互不蕴含。来源一侧本轮删掉了「Levy, Theorie des additions aleatoires」那一行：它的年份（1923 还是 1937）本轮无法核对，与其留一个会被引用的错年份，不如只站得住的部分。

## 五、来源

- Lindeberg, J. (1922)
- Feller, W., An Introduction to Probability Theory and Its Applications, 3rd ed. (1968), ch.XV
- Billingsley, P., Convergence of Probability Measures, 2nd ed. (1999), ch.2

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

