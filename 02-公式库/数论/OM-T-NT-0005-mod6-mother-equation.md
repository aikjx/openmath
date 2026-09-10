---
id: OM-T-NT-0005
title_zh: 模 6 合数覆盖母方程
status: VERIFIED(L2)
---

# OM-T-NT-0005 · 模 6 合数覆盖母方程

## 一、定理陈述

设 \(N=6k+\varepsilon>3\)，\(\varepsilon\in\{-1,+1\}\)（即 \(N\equiv\pm1\pmod 6\)）。
则

\[
\boxed{N\text{ 为合数}\iff \exists\, a,b\ge1,\ \sigma=\pm1:\ k=6ab+a\varepsilon\sigma+b\sigma}.
\]

等价地

\[
k=(6a+\sigma)\,b+a\varepsilon\sigma,\qquad
1\le a\le\Big\lfloor\frac{\sqrt N-\sigma}{6}\Big\rfloor,\qquad
b=\frac{k-a\varepsilon\sigma}{6a+\sigma}\in\mathbb N.
\]

## 二、证明（要点）

若 \(N\) 为合数且与 \(6\) 互素，则非平凡因子也属 \(\pm1\pmod6\)。令较小因子为
\(6a+\sigma\)，另一因子必为 \(6b+\varepsilon\sigma\)（乘积余数回到 \(\varepsilon\)）。
展开 \((6a+\sigma)(6b+\varepsilon\sigma)=6k+\varepsilon\) 即得 \(k\) 的式子。

反之，若等式成立且 \(a,b\ge1\)，则 \(N=(6a+\sigma)(6b+\varepsilon\sigma)\) 分解为两因子均
\(>1\)，故为合数。

## 三、与四种经典形式的关系

\[
6ab-a-b,\ 6ab+a+b,\ 6ab+a-b,\ 6ab-a+b
\]

只是本母方程在 \((\varepsilon,\sigma)\in\{-1,+1\}^2\) 四种符号组合下的展开。

## 四、验证状态

| 层级 | 状态 |
| --- | --- |
| L0 结构 | ✅ |
| L2 数值 | ✅（精确整数核对，残差 0） |
| L4 形式化 | ⬜ |

L2 实测：对 \(N=6k\pm1\le500000\) 的全部合数（共 166666 个候选中的合数），
用独立最小素因子表分解，重构坐标 \((a,b,\sigma)\) 并验证 \(N=(6a+\sigma)(6b+\varepsilon\sigma)\)，
全部成立。

## 五、诚实边界

- 该结构是初等乘法恒等式，\(M=6\) 只是轮积理论的最低阶特例（见 OM-T-NT-0006）；
  **不能单独视为新的素数分布定律**（红线：不得越界）。
- L2 通过只能证伪、不能证明。

## 六、相关

- OM-D-NT-0001（素数指示）
- OM-T-NT-0006（一般 wheel 覆盖定理）
