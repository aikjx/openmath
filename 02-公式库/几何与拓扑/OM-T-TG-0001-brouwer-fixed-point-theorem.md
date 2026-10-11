---
id: OM-T-TG-0001
title_zh: Brouwer 不动点定理
status: PROPOSED
---

# OM-T-TG-0001 · Brouwer 不动点定理

\[ f:\overline{B}^{\,n}\to\overline{B}^{\,n}\ \text{连续}\ \Longrightarrow\ \exists x\in\overline{B}^{\,n}:\ f(x)=x \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-TG-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

定理的否定形式更常被使用：若 f 无不动点，则从球心出发的射线给出一个把闭球映到其边界的 retraction，而同调（或 Sperner 的组合计数）说这种 retraction 不存在。所以这条定理真正的内容是「球不能无收缩地压到边界」。两条必须留的边界：一，凸性（或同胚于凸紧集）不可去掉，圆盘上的旋转就没有不动点；二，它是**存在性**的，不给出算法，也不给唯一性——这条与 OM-T-CT-0002 的不动点是两种不动点，Lawvere 那条需要指数对象，而 Top 不是笛卡尔闭，所以两者之间没有蕴含边。

## 二、前提

- 定义域是闭单位球（同胚于任意紧凸集）
- f 连续，不需要可微
- 默认约定：n>=1；n=0 时结论退化为平凡情形

## 三、关系

- 用到：OM-T-CB-0002, OM-D-TG-0001
- 相关：OM-T-TG-0003, OM-D-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 走的是构造路线：Sperner 引理（组合）给出本定理的离散证明；rel 连 OM-T-TG-0003（集值推广）而不是从它出发，因为推广是后来的事。

## 五、来源

- Brouwer, L. E. J., Ein Fixpunktsatz (1912)
- Munkres, J. R., Elements of Algebraic Topology (1984), §3.5

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

