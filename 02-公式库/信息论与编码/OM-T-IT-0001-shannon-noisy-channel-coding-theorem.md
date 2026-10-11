---
id: OM-T-IT-0001
title_zh: Shannon 有噪信道编码定理
status: PROPOSED
---

# OM-T-IT-0001 · Shannon 有噪信道编码定理

\[ R<C\ \Longrightarrow\ \exists\ \text{码率}\ R\ \text{的码，误码率}\to 0;\qquad R>C\ \Longrightarrow\ \text{误码率不趋于}\ 0 \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-IT-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | IT（信息论与编码） |
| **录入** | 2026-10-11 |

## 一、要点

这条定理把通信问题变成了一道**阈值**题：容量以下可以任意可靠，以上不可能。它给的是存在性（随机编码论证：从典型分布随机抽码，平均误码率小⇒存在一棵好码树），而不是构造；工程上的 Shannon 极限与可达它的码族是另一件事，且到 2010 年代才有逼近容量而不失可解性的构造（Polar 码、LDPC）。为什么把概率论记进 uses：随机编码论证的骨架是大数律/典型性，不是信道代数。为什么与停机问题连 related：两条都是「某个极限处不可逾越」型定理，但一个关于计算、一个关于传输，本库不写它们之间的蕴含。

## 二、前提

- 信道离散、无记忆、容量 C 有限
- 码长 n 趋于无限，码率为每符号比特数
- 默认约定：误码率按最大或平均错误概率的通常口径；本卡两种口径都不区分

## 三、关系

- 用到：OM-D-IT-0001, OM-T-PR-0001
- 相关：OM-D-IT-0001, OM-T-TC-0001, OM-T-PR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- related 指向 OM-T-TC-0001 只是主题相邻（不可逾越的极限），本卡明确不把它写成 implies，以免图上出现一条无人证明过的边。

## 五、来源

- Shannon, C. E., A Mathematical Theory of Communication (1948), §10-11
- Cover and Thomas, Elements of Information Theory, 2nd ed. (2006), ch.8

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

