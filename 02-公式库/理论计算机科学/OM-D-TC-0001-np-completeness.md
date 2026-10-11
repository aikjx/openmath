---
id: OM-D-TC-0001
title_zh: NP 完全性（多项式时间归约下的完全类）
status: PROPOSED
---

# OM-D-TC-0001 · NP 完全性（多项式时间归约下的完全类）

\[ L \in \mathbf{NP}\text{-complete} \iff L \in \mathbf{NP} \wedge \forall A \in \mathbf{NP}\ (A \leq_p L) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-TC-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TC（理论计算机科学） |
| **录入** | 2026-10-11 |

## 一、要点

定义先于 Cook-Levin 卡在这里，是因为完全性是**相对于归约概念**的：换掉 ≤p，同一个语言可以不再是完全的（Logspace 归约、图灵归约给出不同的分层）。本卡登记的诚实边界：把「NP 完全问题有一万个」读成难度证据之前，先确认这句话只在 P ≠ NP 这一未证前提下才有内容——若 P = NP，完全类仍然非空且仍相互归约，只是「最难」不再意味着「不可解」。

## 二、前提

- 归约取多项式时间多一归约 ≤p
- 机为确定性/非确定性图灵机的标准定义
- 默认约定：时间界以输入长度多项式度量
- 默认约定：编码约定不改变类（合理编码不变性）

## 三、关系

- 用到：OM-T-TC-0002
- 相关：OM-T-TC-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本卡与 OM-P-TC-0002（P vs NP）互相登记 related：定义里没有难度断言，难度断言全在那条未决问题里。

## 五、来源

- Karp, R. M., Com. Math. Phys. 6 (1972)
- Garey & Johnson, Computers and Intractability (1979)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

