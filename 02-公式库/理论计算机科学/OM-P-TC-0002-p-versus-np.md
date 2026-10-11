---
id: OM-P-TC-0002
title_zh: P 与 NP 是否相等
status: PROPOSED
---

# OM-P-TC-0002 · P 与 NP 是否相等

\[ \mathbf{P} \overset{?}{=} \mathbf{NP} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-P-TC-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **数学主张状态** | `OPEN` |
| **域** | TC（理论计算机科学） |
| **录入** | 2026-10-11 |

## 一、要点

current_status = OPEN。这张卡的重点不是「悬而未决」这四个字，而是把**为什么难**机器可读地钉住：三条已证的障碍方法（相对化：Baker-Gill-Solovay 给出 P^A ≠ NP^A 与 P^A = NP^A 的谕示；自然证明：Razborov-Rudich 在单向函数存在的前提下排除一类下界论证；代数化：Aaronson-Wigderson 表明对代数扩展的论证同样受限）。把它们登记成 assumptions 之下的条目，是为了让下一轮不能把「新证明思路」写成一句没有对象的主张——任何主张都必须先说明它绕开了哪一条。本卡明确不采入任何「已证明 P≠NP」的外部声明，包括近期预印本：未经评审的近期声明按红线八只能记 UNVERIFIED，而本卡选择不为它们留位。

## 二、前提

- 确定性/非确定性图灵机的标准时间类定义
- 归约取多项式时间
- 默认约定：问题在 ZFC（或某个公认的弱算术系统）内可表达

## 三、关系

- 用到：OM-D-TC-0001
- 相关：OM-D-TC-0001, OM-T-TC-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- fact_check 的判定：本卡所有引用都是 1975-2009 的已刊文献，无 2020 年后的未评审来源；因此不触发「近期声明」条款，但也不构成 L2 以上证据。

## 五、来源

- Cook, S. A., The P versus NP problem (2000, Clay)
- Baker, Gill & Solovay, Relativizations of the P=NP question (1975)
- Razborov & Rudich, Natural proof systems (1997)
- Aaronson & Wigderson, Algebrization (2009)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

