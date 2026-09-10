---
id: OM-F-NT-0002
title_zh: 第 n 素数的 n-only 有限表示（母公式）
status: VERIFIED(L2)
---

# OM-F-NT-0002 · 第 n 素数的 n-only 有限表示

## 一、公式

对 \(n\ge 6\)，取经典显式上下界

\[
L_n=\Big\lfloor n(\log n+\log\log n-1)\Big\rfloor+1,\qquad
U_n=\Big\lceil n(\log n+\log\log n)\Big\rceil,
\]

则 \(L_n\le p_n<U_n\)。令整数正阶跃 \(\Theta(z)=1_{z>0}\)（OM-D-NT-0001），有

\[
\boxed{p_n = L_n + \sum_{x=L_n}^{U_n-1}\Theta\bigl(n-\pi(x)\bigr)},
\]

其中

\[
\pi(x)=\sum_{t=2}^{x} I_{\mathbb P}(t).
\]

## 二、正确性

若 \(L_n\le x<p_n\)，则 \(\pi(x)<n\)，阶跃项为 \(1\)；若 \(p_n\le x<U_n\)，则
\(\pi(x)\ge n\)，阶跃项为 \(0\)。故求和恰为 \(p_n-L_n\)，得 \(p_n\)。

由于 \(\pi(x)\) 已被 \(I_{\mathbb P}\) 的连乘定义完全展开，整条公式**只依赖 \(n\)**。

## 三、验证状态

| 层级 | 状态 |
| --- | --- |
| L0 结构 | ✅ |
| L2 数值 | ✅（精确整数核对，残差 0） |
| L4 形式化 | ⬜ |

L2 实测：母公式（用 \(I_{\mathbb P}\) 连乘展开 \(\pi\)）与独立筛法第 \(n\) 素数逐点相等，
\(n=6..1000\)（995 个样本），残差恒为 0。

## 四、诚实边界

- **精确公式 ≠ 快速公式**：内部仍需精确计算 \(\pi(x)\)。随机访问 \(n\to p_n\) 的快速化
  必须接到 Lehmer / LMO / Deléglise–Rivat 后端（OM-P-NT-0002，方向 A）。
- 同类「第 \(n\) 素数闭式」早在 Willans（1964）等工作中出现；本母公式是已知构造的
  再表述，**不构成优先权主张**。
- L2 通过只能证伪、不能证明。

## 五、相关

- OM-D-NT-0001（整除脉冲 / 素数指示 / 阶跃）
- OM-T-NT-0001（\(p_n\) 的离散逆定义）
- OM-P-NT-0002（第 \(n\) 素数的低复杂度公式，开放问题）
