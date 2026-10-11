---
id: OM-T-CT-0002
title_zh: Lawvere 对角不动点定理
status: PROPOSED
---

# OM-T-CT-0002 · Lawvere 对角不动点定理

\[ \gamma:A\twoheadrightarrow B^{A}\ \Longrightarrow\ (\forall f:A\to A)\ \exists a:1\to A,\ f\circ a=a \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-CT-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | CT（范畴论） |
| **录入** | 2026-10-11 |

## 一、要点

证明只需对角线一句：把点满射看成「把每个自态射都作为某个 a 的取值列出」，取 g = gamma 的对角复合再对 f 作反证，就得到一个不被任何 a 取到的元素——与点满射矛盾。因此它的可用形式往往是逆否：若某个 A 的每个自态射都有不动点，那么 A 不可能点满地枚举 B^A。Cantor（不可数）、Godel（不可判定）、Turing（停机）、Tarski（真不可定义）在文献里被读成这一条的不同实例。**必须留的三条边界**：一，这条定理不给拓扑不动点——Top 不是笛卡尔闭，指数对象不存在，Brouwer 不动点定理不在它的射程内；二，「是同一对角线的实例」是文献的读法而不是本库证明的蕴含，所以图上只写 related 不写 implies；三，它给的是不动点存在性，不是任何具体命题的不可判定性证明。

## 二、前提

- C 有有限积与指数对象 B^A
- gamma:A→B^A 是点满射（即 Hom(1,A)→Hom(1,B^A) 逐点覆盖）
- 1 为终对象
- 默认约定：广义元素（point）与全局元素同义，故需 1 是能区分态射的生成对象

## 三、关系

- 用到：OM-D-CT-0001
- 相关：OM-T-FD-0001, OM-T-TC-0001, OM-T-CT-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- related 的两条边指向第 1 批的 OM-T-FD-0001（哥德尔第一）与 OM-T-TC-0001（停机不可判定）；本卡把「实例化」这件事明确记为文献读法，图上因此是虚线相关的邻接而非蕴含。

## 五、来源

- Lawvere, F. W., An informal exposition of diagrams for pathologists (1969)
- Lawvere, F. W., Diagonal arguments and cartesian closed categories (1970)
- Ambuel, Datta, Easwaran, Diagonal Arguments and Cartesian Closed Categories (2016)

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

