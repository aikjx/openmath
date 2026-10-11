---
id: OM-C-ST-0002
title_zh: 否定连续统假设 ¬CH
status: PROPOSED
---

# OM-C-ST-0002 · 否定连续统假设 ¬CH

\[ \exists A\ \bigl(|\mathbb{N}| < |A| < |\mathbb{R}|\bigr)\quad\text{即 } 2^{\aleph_0} > \aleph_1 \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-C-ST-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **数学主张状态** | `UNDECIDABLE` |
| **相对于** | ZFC |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

这一条单独立卡的目的只有两个：让 CH 的冲突边在图上有对端，并且让「¬CH 也是相对一致的」这一侧有可引用的载体——独立性是两句话，只立 CH 一张卡就等于把第二句话藏进了散文。登记纪律与 OM-C-ST-0001 相同：状态词 PROPOSED（记录级）、current_status UNDECIDABLE（数学主张级，相对 ZFC），本库不声称重造过 forcing 模型。

## 二、前提

- 在 ZFC 中讨论
- 基数比较由单射定义
- 默认约定：ZFC 一致
- 默认约定：forcing 的合并-稠密集论证可用

## 三、关系

- 冲突（对称记账，两侧均写）：OM-C-ST-0001
- 用到：OM-D-ST-0001
- 相关：OM-C-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- Easton 定理说明正则基数上 2^kappa 的行为远比 CH 丰富，本卡不引它作为「¬CH 更自然」的论据——那是价值判断。

## 五、来源

- Cohen, P. J., Ann. of Math. 84 (1966)
- Jech, Set Theory, ch. 14 (forcing, Easton support)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

