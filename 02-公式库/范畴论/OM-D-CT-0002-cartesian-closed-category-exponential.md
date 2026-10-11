---
id: OM-D-CT-0002
title_zh: 笛卡尔闭范畴与指数对象
status: PROPOSED
---

# OM-D-CT-0002 · 笛卡尔闭范畴与指数对象

\[ \mathrm{Hom}(X\times A,\ B)\ \cong\ \mathrm{Hom}(X,\ B^{A}) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-CT-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | CT（范畴论） |
| **录入** | 2026-10-11 |

## 一、要点

这条同构说的是「把两个变量的态射拆成一次一个」这件事在范畴内部可做：currying 不只是编程技巧，它是 Hom 的双自然同构。 Lawvere 对角不动点定理的全部前提就写在这里——它需要 B^A 存在，还需要 gamma 是**点满射**，即 Hom(1,A)→Hom(1,B^A) 覆盖每个全局元素。诚实边界（也是常被越界的一处）：Top 有积但没有通常意义下的指数对象，所以拓扑空间的连续映射不能直接套这条；这既是本定义的适用边界，也是它与拓扑不动点定理（Brouwer 型结果，本批尚未登记，故此处不写它的 ID——配对 md 正文里的 OM-* 字样会被收成 cites 边，指向不存在的号就是 DANGLING）之间没有 uses 边的原因。

## 二、前提

- C 有有限积（含终对象 1）
- 对每对 A,B 指数对象 B^A 存在并满足上述自然同构
- 默认约定：同构对 X 自然，故它是泛性质而非某个特定同构的选取

## 三、关系

- 用到：OM-D-CT-0001
- 相关：OM-D-CT-0001, OM-T-CT-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条为第 2 批的 OM-T-CT-0002 补记号（B^A、gamma、f、a、ev、1），并把「Lawvere 需要笛卡尔闭、Brouwer 不在其射程」这条边界写进同一处，免得图上出现一条越界的 uses。

## 五、来源

- Mac Lane, S., Categories for the Working Mathematician, 2nd ed. (1998), §IV.4
- Kock, A., Synthetic Differential Geometry (1981), ch.1

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

