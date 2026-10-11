---
id: OM-C-ST-0001
title_zh: 连续统假设 CH
status: PROPOSED
---

# OM-C-ST-0001 · 连续统假设 CH

\[ \neg \exists A\ \bigl(|\mathbb{N}| < |A| < |\mathbb{R}|\bigr)\quad\text{即 } 2^{\aleph_0} = \aleph_1 \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-C-ST-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **数学主张状态** | `UNDECIDABLE` |
| **相对于** | ZFC |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

登记状态：current_status = UNDECIDABLE，independent_of = ZFC，并且这条独立性**只属于文献**——哥德尔 1938 用 L（可构造宇宙）给出 CH 与 V = L 与 ZFC 的相对相容性，科恩 1963 用 forcing 给出 ¬CH 的相对相容性，两边都是相对一致性，所以「CH 独立」这句话的全部内容是：若 ZFC 一致，则 ZFC 既不证 CH 也不证 ¬CH。本卡拒绝把它写成「CH 无真值」：那是哲学结论，不是定理。另外诚实记账：本库没有重做任何一侧的模型构造，也没有形式化绑定，所以 evidence_level 停在 L1，而 UNDECIDABLE 这一状态词按宪章第三节要求 L4，本卡因此把状态字段写作 PROPOSED，把 UNDECIDABLE 只放进 current_status（问题侧的数学主张）。

## 二、前提

- 基数比较由单射定义（无需选择公理即可谈 ≤）
- 在 ZFC 中讨论（选择公理在册，见 OM-D-ST-0001）
- 默认约定：ZFC 一致
- 默认约定：ℵ 序列由序数基数化给出

## 三、关系

- 冲突（对称记账，两侧均写）：OM-C-ST-0002
- 用到：OM-D-ST-0001
- 相关：OM-D-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 新纲领（Woodin 的 Pmax、Sealing 等）主张在附加公理下 CH 有确定答案：本卡不采入，理由是那些附加公理的可接受性尚在争论，把它写进来会伪装成共识。

## 五、来源

- Godel, K., Ann. of Math. 38 (1937/38)
- Cohen, P. J., Ann. of Math. 84 (1966)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

