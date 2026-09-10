---
id: OM-T-NT-0006
title_zh: 一般 wheel 覆盖定理
status: VERIFIED(L2)
---

# OM-T-NT-0006 · 一般 wheel 覆盖定理

## 一、定理陈述

令 \(M\) 为任意正整数，定义约化剩余系

\[
R_M=\{r:1\le r<M,\ \gcd(r,M)=1\}.
\]

特别地可取 \(M=p_1p_2\cdots p_r=p_r\#\)。设 \(\gcd(N,M)=1\)，\(N=Mk+u\)，\(u\equiv N\pmod M\)。

则

\[
\boxed{N\text{ 为合数}\iff \exists\, r,s\in R_M,\ a,b\ge0:\ N=(Ma+r)(Mb+s)}
\]

即

\[
k=Mab+as+br+\frac{rs-u}{M}.
\]

## 二、证明（要点）

若 \(\gcd(N,M)=1\) 且 \(N=xy\)（\(x,y>1\)），则 \(\gcd(x,M)=\gcd(y,M)=1\)，故
\(x=Ma+r,\ y=Mb+s\)，\(r,s\in R_M\)。展开
\((Ma+r)(Mb+s)=M^2ab+Mas+Mbr+rs\)；令 \(u\equiv rs\pmod M\)、
\(t=(rs-u)/M\)，得 \(k=Mab+as+br+t\)。反之若等式成立且两因子 \(>1\)，\(N\) 为合数。

周期密度严格为

\[
\frac{\varphi(M_r)}{M_r}=\prod_{j=1}^{r}\Bigl(1-\frac1{p_j}\Bigr).
\]

## 三、验证状态

| 层级 | 状态 |
| --- | --- |
| L0 结构 | ✅ |
| L2 数值 | ✅（精确整数核对，残差 0） |
| L4 形式化 | ⬜ |

L2 实测（独立 SPF 分解后重组坐标）：

| \(M\) | 候选合数数 | 结果 |
| --- | --- | --- |
| 6 | 23742 | 全部成立 |
| 30 | 17076 | 全部成立 |
| 210 | 13268 | 全部成立 |

（与论文 §11 零误差表一致。）

## 四、诚实边界

- 本定理是 **primorial wheel / wheel sieve** 的成熟框架，\(M=6\) 只是最低阶特例（OM-T-NT-0005），
  **不构成首创**。
- 本定理只给**单点因子坐标**；整块覆盖计数（\(\bigl|\bigcup_{r,s}\operatorname{Im}K_{r,s}\bigr|\) 及交叠项）
  仍是开放问题（OM-P-NT-0002，方向 B）。
- L2 通过只能证伪、不能证明。

## 五、相关

- OM-T-NT-0005（模 6 母方程，本定理的特例）
- OM-A-NT-0001（wheel sieve 算法）
- OM-D-NT-0001（素数指示）
