---
id: OM-D-ST-0002
title_zh: 可数性与两个 aleph 基数
status: PROPOSED
---

# OM-D-ST-0002 · 可数性与两个 aleph 基数

\[ \aleph_0=\lvert\mathbb{N}\rvert,\quad \aleph_1=\min\{\kappa:\kappa\ \text{是不可数基数}\},\quad \lvert\mathbb{R}\rvert=2^{\aleph_0} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-ST-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

连续统假设之所以是一条**关于 aleph_1 与 2^aleph_0 是否相等**的陈述，全靠这条定义把两边写成可比较的对象。要留的三处精度：一，2^aleph_0 是幂集基数，写成指数形式而不是「实数有多少个」的口语；二，CH 说的只是第一个无限基数之后那一步，它不排除中间存在别的基数这一表述本身依赖于良序可比较；三，没有选择公理时「不可数」有若干不等价的读法，本卡按良序基数的口径登记，与 OM-T-ST-0001 的良序定理口径一致。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：基数取初始序数代表（选择公理下每个集合都可良序）
- 默认约定：不加 AC 时 aleph_1 仍是第一个不可数良序基数，但未必是每个不可数集合的基数

## 三、关系

- 用到：OM-D-ST-0001
- 相关：OM-C-ST-0001, OM-C-ST-0002, OM-T-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 1 批的 OM-C-ST-0001/0002 在陈述里用了 aleph_0 与 aleph_1 却没有定义条目，本条把这两个记号补进 kind=definition 的名单。

## 五、来源

- Cantor, G., Beiträge zur Begründung der transfiniten Mengenlehre (1895)
- Jech, T., Set Theory, Millennium ed. (2003), §1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

