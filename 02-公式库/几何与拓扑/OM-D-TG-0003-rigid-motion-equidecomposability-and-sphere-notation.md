---
id: OM-D-TG-0003
title_zh: 刚体运动、等分等价与球面记号
status: PROPOSED
---

# OM-D-TG-0003 · 刚体运动、等分等价与球面记号

\[ S^{2}=\{x\in\mathbb{R}^{3}:\ \|x\|=1\},\qquad SO(3)=\{A\in\mathrm{GL}_3(\mathbb{R}):\ A^{\mathsf{T}}A=I,\ \det A=1\},\qquad A\sim B\iff A=\textstyle\bigcup_i A_i,\ B=\textstyle\bigcup_i g_iA_i,\ g_i\in SO(3) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-TG-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

Banach–Tarski 一族的四条记录（猜想 OM-C-TG-0001、定理 OM-T-TG-0002 及其上下游）共用 S^{2}、SO(3)、等分等价与 vol 四枚记号，此前全部没有定义条目。

**这张卡有一处必须说清的不对称**：`\mathrm{vol}` 被定义的是**记号**，不是对象。OM-C-TG-0001 写的是「存在这样一个体积」，而 OM-T-TG-0002 分球定理恰恰否证它。把 \mathrm{vol} 收进 kind=definition 的记录，读图上会出现一条从定义卡指向被否证对象的边，很容易被误读成「本库承认它存在」。所以本卡在 symbols 条目与 caveat 两处都写明：这是被否证的设想对象之名字。红线一在这里的具体形状就是：**定义记号不等于断言存在**。另一处精度：\sim 作为关系记号是全域复用的高危串（等价、全序、同胚在本库各域都写 \sim），本卡把它的定义固定在等分等价这一种用法上，图上因此会把它对其它卡的引用一并算成已定义——这是本库按名聚合判据的既有代价，登记在 §八 的口径债里。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：分块为**有限**分块且各块互不相交（并集取不相交并）
- 默认约定：等分等价只问刚体运动（旋转加平移），本卡的 SO(3) 只写旋转部分；平移部分在分球定理的论证里由自由群生成元承担
- 默认约定：S^{2} 取三维空间中的单位球面（二维曲面，不含内部）

## 三、关系

- 用到：OM-D-TG-0001
- 相关：OM-T-TG-0002, OM-C-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡。\mathrm{vol} 与 \sim 两枚刻意留下双重注记：前者定义的是被否证对象的记号，后者是全域复用的高危串。本卡不新增任何存在性主张。

## 五、来源

- Wagon, S., The Banach–Tarski Paradox, Cambridge University Press (1985), ch.1（S^{2}、SO(3) 与等分等价 ~ 的记号）
- Banach, S., Sur le problème de la mesure, Fundamenta Mathematicae 4 (1923)（把体积定义到一切子集上的设想与其失败）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

