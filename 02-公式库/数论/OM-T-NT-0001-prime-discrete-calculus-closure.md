---
id: OM-T-NT-0001
title_zh: 素数离散微积分闭环（指示 ↔ 计数 ↔ 第 n 素数）
status: VERIFIED(L2)
---

# OM-T-NT-0001 · 素数离散微积分闭环

## 一、定理陈述

设 \(I_{\mathbb P}\) 为素数指示（OM-D-NT-0001），\(\pi\) 为素数计数函数。则：

\[
\boxed{\Delta\pi(N)=\pi(N)-\pi(N-1)=I_{\mathbb P}(N)}.
\]

即**素数位置 = \(\pi\) 的离散一阶导数**。反方向：

\[
\pi(X)=\sum_{N=2}^{X}\Delta\pi(N).
\]

且第 \(n\) 个素数满足

\[
\boxed{p_n=\min\{x\ge 2:\pi(x)\ge n\}},\qquad
\boxed{\pi(p_n)=n,\quad \pi(p_n-1)=n-1}.
\]

由此

\[
\boxed{\operatorname{LargestPrime}_{\le N}=p_{\pi(N)}},\qquad
\boxed{\operatorname{NextPrime}(N)=p_{\pi(N)+1}}.
\]

## 二、证明（要点）

- \(\pi(N)-\pi(N-1)\) 是区间 \((N-1,N]\) 中素数的个数，恰为 \(I_{\mathbb P}(N)\)。
- \(\pi\) 逐点单调（每步 \(+0\) 或 \(+1\)），故 \(p_n=\min\{x:\pi(x)\ge n\}\) 给出第
  \(n\) 个素数且 \(\pi(p_n)=n\)。
- \(\le N\) 的素数中最大的是第 \(\pi(N)\) 个，即 \(p_{\pi(N)}\)；下一个素数是第
  \(\pi(N)+1\) 个。

## 三、验证状态

| 层级 | 状态 |
| --- | --- |
| L0 结构 | ✅ |
| L2 数值 | ✅（精确整数核对，残差 0） |
| L4 形式化 | ⬜ |

L2 实测：

| 检查 | 范围 | 结果 |
| --- | --- | --- |
| \(\Delta\pi(N)=I_{\mathbb P}(N)\) | \(N\le20000\) | 全相等 |
| \(\pi(p_n)=n\) 且 \(p_n=\min\{x:\pi(x)\ge n\}\) | \(n\le2000\) | 全相等 |
| \(\operatorname{LargestPrime}_{\le N}=p_{\pi(N)}\) | \(N\le5000\) | 全相等 |

## 四、诚实边界

- 「素数求导」在数学上应理解为**离散导数或分布导数**（将 \(\pi\) 扩张为右连续阶梯函数后，
  \(D\pi=\sum_{p}\delta_p\)），不是普通连续导数。
- 精确公式 ≠ 快速公式：反演仍需逐点计算 \(\pi\)，快速化见 OM-F-NT-0002 与 OM-P-NT-0002。
- 本条目为初等推论，不构成优先权主张。

## 五、相关

- OM-D-NT-0001（整除脉冲 / 素数指示）
- OM-F-NT-0001、OM-A-NT-0001（分块递归计数）
- OM-F-NT-0002（n-only 母公式）
