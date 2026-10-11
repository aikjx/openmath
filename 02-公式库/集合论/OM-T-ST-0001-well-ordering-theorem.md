---
id: OM-T-ST-0001
title_zh: 良序定理
status: PROPOSED
---

# OM-T-ST-0001 · 良序定理

\[ \forall X\ \exists \varrho\ \bigl(\varrho \text{ 良序 } X\bigr) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-ST-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | ST（集合论） |
| **录入** | 2026-10-11 |

## 一、要点

Zermelo 1904 年的证明当年被广泛质疑（循环使用选择公理之嫌），今日的标准处理是先把它等价化：AC ⇒ 良序（Hausdorff 极大链论证），良序 ⇒ AC（从全序直接定义选择函数取每段的下界）。本卡登记这个双向蕴含，因为图上「等价」不是一个可以一句带过的词——它是两条方向相反的边，少画一条就等于宣称另一方向尚未证明。

## 二、前提

- 接受选择公理（OM-D-ST-0001）
- ZF 其余公理
- 默认约定：良序 = 全序且每个非空子集有最小元

## 三、关系

- 蕴含：OM-D-ST-0001
- 用到：OM-D-ST-0001
- 相关：OM-D-ST-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 实数无法被显式良序这一「反直觉」是**构造缺失**而非存在缺失：在 ZFC 内良序存在，但在无 AC 的模型里可以不存在。这句话别读成「良序定理被否证」。

## 五、来源

- Zermelo, E., Math. Annalen 65 (1904)
- Hartogs lemma as the modern substitute for the disputed step

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

