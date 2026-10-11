---
id: OM-D-FD-0002
title_zh: 形式语言、证明关系与一致性陈述
status: PROPOSED
---

# OM-D-FD-0002 · 形式语言、证明关系与一致性陈述

\[ \mathrm{Proof}_T(p,\ \ulcorner\varphi\urcorner)\ \Longleftrightarrow\ p\ \text{是}\ T\ \text{中}\ \varphi\ \text{的一个证明编码} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-FD-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | FD（数学基础与逻辑） |
| **录入** | 2026-10-11 |

## 一、要点

不完备定理的全部技术体力活都住在这条定义里：**关系** Proof_T 是原始递归的，所以它在 T 内可表示；而「可证」是存在量化（存在一个 p 使 Proof_T(p, ulcorner-varphi)），于是可证性谓词是 Σ1，不是 Δ0——这条不对称就是第二定理的入口。要留的边界：一致性陈述 Con(T) 的定义依赖所选 Proof_T 的**具体写法**，不同编码给出的 Con 可能在 T 内不等价，所以「T 证不了自己的一致性」这句话必须先固定证明谓词才有唯一真值。本卡登记的就是这一层固定。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：语言与符号表可有效枚举，故句子可配 Gödel 码 ulcorner-varphi
- 默认约定：Proof_T 取原始递归（甚至 Δ0）的证明谓词，T 的公理集可判定或递归可枚举

## 三、关系

- 相关：OM-D-FD-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条为第 1 批的 OM-T-FD-0001、OM-T-FD-0002 与 OM-P-FD-0001 补记号定义：三条记录都用了 T、Con、Proof_T，而本库把「记号无定义」记进 UNDEFINED_SYMBOL 台账。

## 五、来源

- Hilbert and Bernays, Grundlagen der Mathematik, Bd. II (1934)
- Takeuti, M., Proof Theory (2013), §I.3

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

