---
id: OM-D-GO-0001
title_zh: 博弈、策略、效用与混合策略单纯形
status: PROPOSED
---

# OM-D-GO-0001 · 博弈、策略、效用与混合策略单纯形

\[ \Gamma=(N,\ (S_i)_i,\ (u_i)_i),\qquad \Delta_{S_i}=\{p\in\mathbb{R}^{S_i}:\ p\ge 0,\ \textstyle\sum_{s}p(s)=1\},\qquad \mathrm{BR}_i(\sigma_{-i})=\arg\max_{x_i\in\Delta_{S_i}}u_i(x_i,\sigma_{-i}) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-GO-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GO（博弈论与优化） |
| **录入** | 2026-10-11 |

## 一、要点

「策略」有两种读法：纯策略是 S_i 的一个元素，混合策略是 S_i 上的一个分布。本卡把两者固定在同一套记号下：\Delta_{S_i} 之所以是**单纯形**，正因为它是非负且和为 1 的向量之集合——于是它是紧凸集；而最佳应对 \mathrm{BR}_i 一般是**集值**的（并列最优时是一个面而不是一个点）。这一步就是 Nash 证明的入口：把每人的 \mathrm{BR}_i 打包成乘积单纯形上的集值映射，再交给 OM-T-TG-0003（角谷）找不动点。边界：本卡只登记有限博弈的记号，不覆盖无限策略集、贝叶斯博弈的类型空间口径，也不覆盖相关均衡那种联合分布口径。

## 二、前提

- N 为有限参与人集，每个 S_i 为有限策略集
- 效用按期望效用口径（对混合策略多重线性）
- 默认约定：混合策略读作 S_i 上的概率分布，故 \Delta_{S_i} 是有限维单纯形

## 三、关系

- 用到：OM-D-PR-0001, OM-D-TG-0002
- 相关：OM-T-GO-0001, OM-T-GO-0002, OM-T-TG-0003

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条是第 3 批的记号补账：\Gamma、\Delta_m、\Delta_n、\Delta_{S_i}、\mathcal{M}、\sigma^{*}、\mathrm{BR}_i、\arg\max 八个记号此前只被两张定理卡使用而无定义条目。uses 指 OM-D-TG-0002：混合策略需要的「紧凸定义域＋集值映射」两处结构都在那张卡里固定。

## 五、来源

- Osborne, M. J. and Rubinstein, A., A Course in Game Theory (1994), ch.1-2, ch.6
- Fudenberg, D. and Tirole, J., Game Theory (1991), ch.2

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

