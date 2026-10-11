---
id: OM-T-GR-0001
title_zh: 西罗定理
status: PROPOSED
---

# OM-T-GR-0001 · 西罗定理

\[ |G|=p^{a}m,\ p\nmid m\ \Longrightarrow\ \exists P\le G,\ |P|=p^{a},\quad n_p\equiv 1\ (p),\ n_p\mid m \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-GR-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | GR（群论与表示论） |
| **录入** | 2026-10-11 |

## 一、要点

三条分开读：存在性（有阶 p^a 的子群）、共轭性（所有 p-Sylow 彼此共轭，所以「唯一」就等于「正规」）、计数（n_p ≡ 1 mod p 且 n_p | m）。用它判小的有限群时，真正出力的是第三条：n_p 同时被同余与整除夹住，常常只剩一个值，于是得到一个正规 p-子群，群就可分解。边界：本库不重做证明；与 OM-T-NT-0001 连一条 related 边，因为 n_p 的约束完全是关于 |G| 的算术条件，属于数论语言在群论里的落点。

## 二、前提

- G 为有限群
- p 为素数
- n_p 为 p-Sylow 子群的个数
- 默认约定：拉格朗日定理可用（子群阶整除群阶）

## 三、关系

- 用到：OM-D-GR-0001
- 相关：OM-T-NT-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-D-GR-0001（在陪集集合上作用、数 2-轨道），related 指向第 1 批之外的既有记录 OM-T-NT-0001——引用闭包由铸造器现扫盘上 ID 核对。

## 五、来源

- Sylow, P., Théorèmes sur les groupes de substitutions (1872)
- Isaacs, I. M., Finite Group Theory (1990), §2.1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

