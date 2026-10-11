---
id: OM-P-FD-0001
title_zh: 希尔伯特纲领（有穷一致性证明）
status: PROPOSED
---

# OM-P-FD-0001 · 希尔伯特纲领（有穷一致性证明）

\[ \text{用有穷数学 } \mathrm{F} \text{ 证明形式系统 } T \text{ 的一致性： } \mathrm{F} \vdash \mathrm{Con}(T) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-P-FD-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **数学主张状态** | `REFUTED` |
| **域** | FD（数学基础与逻辑） |
| **录入** | 2026-10-11 |

## 一、要点

登记成 problem 而不是 definition，因为它是一条**研究纲领的主张**：它可以在图上被指认、被冲突边指向，而不是一句公理。current_status 记 REFUTED 只针对它的强形态（同一系统内以标准一致性陈述完成有穷证明）；弱形态仍在被研究——相对一致性、以额外公理（超限归纳、大基数反射）为代价的一致性证明，以及把「有穷」的边界重新划定的尝试。这段区分必须写在卡上，否则下一轮会把「纲领被否证」读成「证明一致性的所有努力都失败了」，那是错的。

## 二、前提

- 存在被广泛接受的有穷数学 F，且其推理可形式化进 T
- T 刻画分析学所需的数学
- 默认约定：有穷手段的可接受性不依赖被证系统的一致性

## 三、关系

- 冲突（对称记账，两侧均写）：OM-T-FD-0001, OM-T-FD-0002
- 用到：OM-T-FD-0002
- 相关：OM-P-TC-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与判定问题（OM-P-TC-0001）的关系登记为 related 而非 contradicts：两者共享「有效方法可决定一切」这一预设，但否证它们的不是同一条定理。

## 五、来源

- Hilbert, D., Math. Annalen 88 (1922)
- Hilbert & Ackermann, Grundzuge der theoretischen Logik (1928)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

