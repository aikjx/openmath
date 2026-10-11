---
id: OM-T-GO-0002
title_zh: Nash 均衡存在性定理
status: PROPOSED
---

# OM-T-GO-0002 · Nash 均衡存在性定理

\[ \text{有限博弈}\ \Longrightarrow\ \exists\ \sigma^{*}\in\prod_i\Delta_{S_i}:\ \forall i,\ \sigma^{*}_{i}\in\arg\max_{x_i\in\Delta_{S_i}}u_i(x_i,\sigma^{*}_{-i}) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-GO-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GO（博弈论与优化） |
| **录入** | 2026-10-11 |

## 一、要点

证明的形状是把「每人对他人策略的最佳应对」打包成一个集值映射，再用 Kakutani 找一个不动点；不动点就是「没人能单方面改善」，即均衡。所以这条定理依赖的是角谷而不是 Brouwer 单值版（Nash 的原始证明用角谷；Glicksberg 之类后续给出过绕开集值的路线，本库未登记）。必须留的三条边界：一，纯策略均衡一般不存在（本卡只保证混合策略下存在）；二，定理不保证唯一，也不保证可计算；三，PPAD 复杂性结果说明「存在」与「能有效找到」是两件事，那一层属于本条之外的账。

## 二、前提

- 参与人与策略集均有限
- 允许混合策略（策略集上的概率分布）
- 默认约定：效用为期望效用（对混合策略线性），故最佳应对集值非空、凸、闭

## 三、关系

- 用到：OM-T-TG-0003, OM-D-TG-0001
- 相关：OM-T-GO-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-T-TG-0003：本卡的依赖链是 组合 Sperner ⇒ Brouwer ⇒ Kakutani ⇒ Nash，这是原证明路线而不是修辞。

## 五、来源

- Nash, J. F., Equilibrium points in n-person games (1950)
- Nash, J. F., Non-cooperative games (1951)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

