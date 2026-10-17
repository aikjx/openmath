---
id: OM-D-PR-0002
title_zh: 正态律与标准化记号
status: PROPOSED
---

# OM-D-PR-0002 · 正态律与标准化记号

\[ \mathcal{N}(\mu,\sigma^{2})\ \text{的密度}=(2\pi\sigma^{2})^{-1/2}\exp\!\bigl(-(x-\mu)^{2}/(2\sigma^{2})\bigr),\qquad \mathcal{N}(0,1)\ \text{为标准化} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-PR-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | PR（概率论） |
| **录入** | 2026-10-11 |

## 一、要点

中心极限定理（OM-T-PR-0002）的结论写成一个分布记号 `\mathcal{N}(0,1)`，此前本库只有概率空间与随机变量的定义卡（OM-D-PR-0001），没有把这条具体律的记号钉住。

值得写进卡片的精度有两点。一，两个参数是**均值与方差**而不是均值与标准差——文献两种写法并存，读错一版会让标准化式的系数差一次幂；本卡按方差写。二，sigma 趋于 0 的退化族不叫正态律（密度不存在），所以本卡在 assumptions 里把 sigma^{2}>0 钉死，免得 CLT 的陈述被读成允许退化。裸 `sigma` 仍未收：它在 OM-T-PR-0002 里是总体标准差，在 OM-D-GO-0001 里是混合策略（两处不同含义，全域定义即假绿）。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：sigma^{2}>0；退化情形（sigma=0，点质量）不写 \mathcal{N}，另按分布退化处理
- 默认约定：\xrightarrow{\ d\ } 表示依分布收敛，其口径在 OM-D-PR-0001 的概率空间记号里
- 默认约定：本卡按密度函数定义 \mathcal{N}，故只对绝对连续律成立

## 三、关系

- 用到：OM-D-PR-0001
- 相关：OM-T-PR-0002, OM-D-PR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡：固定 \mathcal{N} 的参数口径（均值与方差），并声明退化情形不在记号射程内。CLT 本身的主张归 OM-T-PR-0002。

## 五、来源

- Feller, W., An Introduction to Probability Theory and Its Applications, vol.I, 2nd ed., Wiley (1968)（正态密度与标准化）
- Billingsley, P., Probability and Measure, 3rd ed., Wiley (1995)（依分布收敛与中心极限定理的口径）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

