---
id: OM-T-TG-0002
title_zh: Banach-Tarski 分球定理
status: PROPOSED
---

# OM-T-TG-0002 · Banach-Tarski 分球定理

\[ \exists A_1,A_2\subseteq S^{2},\ A_1\cap A_2=\varnothing:\ A_1\sim S^{2}\ \text{且}\ A_2\sim S^{2} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-TG-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

常被误读成「球被复制出更多体积」，其实它说的是：**不存在**一个定义在所有子集上、又在刚体运动下不变的可数可加体积。构造依赖自由群 F_2 的分裂（Hausdorff 的那一步），因此分块必然不可测——定理与「体积」并不矛盾，它挑出的是这两条要求不能同时成立。本卡把它记为冲突的一侧：与 OM-C-TG-0001（朴素可测性公设）成对，两边各写一次 contradicts。

## 二、前提

- 在 R^3 中，只允许刚体运动（旋转＋平移）
- 两块集合互不相交，且允许是不可测集
- 默认约定：承认选择公理（本库 OM-D-ST-0001）；\sim 表示有限分块后经刚体运动重排（等分意义下的等价）

## 三、关系

- 冲突（对称记账，两侧均写）：OM-C-TG-0001
- 用到：OM-D-ST-0001, OM-D-TG-0001
- 相关：OM-D-ST-0001, OM-C-TG-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- uses 指向 OM-D-ST-0001：选择公理在这里是真实的前提，不是修辞；去掉 AC 后结论可以失效（Solovay 模型里所有集合 Lebesgue 可测），那一层属于本条之外的账。

## 五、来源

- Banach and Tarski, Sur la décomposition des ensembles de points (1924)
- Wagon, S., The Banach-Tarski Paradox (1985), ch.1-2

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

