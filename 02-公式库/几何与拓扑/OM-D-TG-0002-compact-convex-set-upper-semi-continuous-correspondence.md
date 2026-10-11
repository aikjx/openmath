---
id: OM-D-TG-0002
title_zh: 紧凸集与上半连续的集值映射
status: PROPOSED
---

# OM-D-TG-0002 · 紧凸集与上半连续的集值映射

\[ K\subseteq\mathbb{R}^{n}\ \text{紧凸},\quad \Phi:K\multimap K,\qquad x_k\to x,\ y_k\in\Phi(x_k),\ y_k\to y\ \Longrightarrow\ y\in\Phi(x) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-TG-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

单值映射的连续性写成「像趋于像」，集值映射必须有另一种说法：取一列 x_k 趋于 x、一列 y_k 属于 \Phi(x_k) 且趋于 y，则 y 必须仍在 \Phi(x) 里。这条就是上半连续。它为什么值得单独占一张定义卡：角谷定理的假设里，凸值保证 \Phi(x) 是「一整块」而不是离散几点，上半连续保证极限不丢点，两条各能单独被构造反例打破。边界：本卡只固定记号与口径，不主张无穷维情形（那是 Fan-Glicksberg 的范围，本库尚未登记）。

## 二、前提

- K 非空、紧、凸
- 集值映射 \Phi 的每个值都非空、凸、闭
- 默认约定：\Phi:K\multimap K 读成 \Phi 把每个 x 送到 \mathcal{P}(K) 的一个非空成员；上半连续在本卡按「闭图＋K 紧」这一口径给出，与图闭性同读

## 三、关系

- 用到：OM-D-TG-0001
- 相关：OM-D-TG-0001, OM-T-TG-0003

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条是第 3 批的记号补账：K、\Phi、\multimap、\mathcal{P} 四个记号此前只被定理卡使用而无定义条目。MSC 号按本库口径只作粗索引。

## 五、来源

- Berge, C., Topological Spaces (1963), ch.6 (集值映射与上半连续)
- Rockafellar, R. T., Convex Analysis (1970), §20 (闭映射与上半连续)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

