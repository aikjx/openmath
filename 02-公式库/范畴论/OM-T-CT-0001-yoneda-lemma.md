---
id: OM-T-CT-0001
title_zh: 米田引理
status: PROPOSED
---

# OM-T-CT-0001 · 米田引理

\[ \mathrm{Nat}\bigl(\mathrm{Hom}(A,-),\ F\bigr)\ \cong\ F(A) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-CT-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | CT（范畴论） |
| **录入** | 2026-10-11 |

## 一、要点

这条双射的内容比它看起来强得多：F 在 A 处的每个元素 x∈F(A) 都唯一决定一个自然变换 Hom(A,-)→F（把 f:A→B 映到 F(f)(x)），反之亦然。所以「元素」可以被完全替换成「从表示函子出发的自然变换」——这就是泛元素（universal element）的说法，也是为什么代表函子之间的态射全由一个元素决定。常见误读要留一条边界：米田引理不是「C 全嵌入 Set^C」这一句的口头版本吗？是——协变米田给出 C→[C,Set] 的全忠实嵌入，但那是推论，且它把「对象」变成了「函子」，不改变对象本身的可构造性。

## 二、前提

- C 为本地小范畴
- F:C→Set 为协变函子
- 自然同构对 A 与 F 都自然
- 默认约定：Hom(A,-) 是按第二个变量的协变表示函子

## 三、关系

- 用到：OM-D-CT-0001
- 相关：OM-D-CT-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 与 OM-D-CT-0001 同时写 related 与 uses：uses 是因为证明只用函子与自然变换的定义，related 是因为这条边的存在性本身要在图里可见（02 图上两类箭头不同型）。

## 五、来源

- Yoneda, N., Kokyuroku Matematikuni Gakushuin Daigaku (1954)
- Mac Lane, S., Categories for the Working Mathematician, 2nd ed. (1998), §II.4

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

