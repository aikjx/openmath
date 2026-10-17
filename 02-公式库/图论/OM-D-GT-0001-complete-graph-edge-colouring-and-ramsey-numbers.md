---
id: OM-D-GT-0001
title_zh: 完全图、边着色与 Ramsey 数
status: PROPOSED
---

# OM-D-GT-0001 · 完全图、边着色与 Ramsey 数

\[ K_n=(V,E),\ |V|=n,\ E=\binom{V}{2};\qquad R_r(k)=\min\{N:\ \text{对每个}\ c:E(K_N)\to[r]\ \text{存在单色}\ K_k\} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-GT-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GT（图论） |
| **录入** | 2026-10-11 |

## 一、要点

本库的图论域（GT）此前**没有任何记录**，而组合数学里的 OM-T-CB-0001（Ramsey 定理）在陈述里用了 K_n、R_r(k) 两枚记号却没有定义条目——域覆盖缺口与记号缺口是同一件事的两面，这一张卡同时补两处，且补的是名实相符的内容。

要留的边界：本卡只定义记号，**不断言 R_r(k) 有限**——那是 OM-T-CB-0001 的内容；也不给任何具体取值（R_2(3)=6 之类属于计算，本批不做）。r 与 k 在这里是宿主全称量词绑定的变量，故意**不**收进定义名单：本库的记号台账按名字全域聚合，一旦定义 `k`＝单色子图顶点数，数论卡里作为下标的 `k`（如 p_k#）就会被判成同一件事已解决＝假绿。这条口径是第 4 批的铸卡纪律，写在这里以便读者检验我没有偷偷放宽它。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：r,k 均不小于 2（否则 Ramsey 数无意义或平凡）
- 默认约定：着色指对**边**着色，颜色集取 [r]={1,...,r}
- 默认约定：单色指存在一版同色的 K_k 顶点子集；本卡取通常的顶点完全子图口径

## 三、关系

- 相关：OM-T-CB-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡，同时是图论域（GT）的首条记录。定义不蕴含存在性下界，Ramsey 有限性归 OM-T-CB-0001；本卡不登记任何已知精确值。

## 五、来源

- Graham, R. L., Rothschild, B. L. and Spencer, J. H., Ramsey Theory, 3rd ed., Wiley (2015), ch.1（完全图与边着色记号）
- Radziszowski, S. P., Small Ramsey Numbers, Electronic Journal of Combinatorics, Dynamic Survey 1（R_r(k) 的取值台账）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

