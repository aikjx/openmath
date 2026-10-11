---
id: OM-D-ST-0003
title_zh: 二元关系、良序与选择函数
status: PROPOSED
---

# OM-D-ST-0003 · 二元关系、良序与选择函数

\[ \varrho\subseteq X\times X,\qquad \varrho\ \text{良序}\ X\ \Longleftrightarrow\ \text{每个非空子集有}\ \varrho\text{-最小元} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-ST-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

这条定义看着琐碎，但它负责一件容易出错的事：良序定理陈述里的关系 \varrho 与被选择函数选出的元素属于同一层语言（都是集合），而「良序」的全部内容包括**每个非空子集都有最小元**——比「全序＋无降链」强，且在没有选择公理时几种写法不再等价。本卡的边界：MSC 号在这里只是粗索引；另外本条不主张任何「良序存在」的可构造性，它只固定记号与定义。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：关系按有序对集合来读，故 \varrho 是 X×X 的子集
- 默认约定：选择函数定义在一族非空集合的并上，每支取一个元素

## 三、关系

- 用到：OM-D-ST-0001
- 相关：OM-T-ST-0001, OM-D-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 1 批的 OM-T-ST-0001 在改名（R→varrho）后仍留有一枚无定义条目的记号；本条把它补在 kind=definition 的记录上，同时把选择函数写进同一处，与 OM-D-ST-0001（选择公理）互为记号上下游。

## 五、来源

- Jech, T., Set Theory, Millennium ed. (2003), §1.3, §2.1
- Halmos, P., Naive Set Theory (1960), §15-16

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

