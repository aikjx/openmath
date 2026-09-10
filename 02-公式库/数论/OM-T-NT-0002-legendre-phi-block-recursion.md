---
id: OM-T-NT-0002
title_zh: 素数计数分块递归分解（Legendre φ 递归恒等式）
status: VERIFIED(L2)
---

# OM-T-NT-0002 · 素数计数分块递归分解

## 一、定理陈述

Legendre 分块函数

\[
\phi(x,a)=\#\{1\le m\le x:\text{所有素因子}>p_a\}
\]

满足递归

\[
\boxed{\phi(x,a)=\phi(x,a-1)-\phi\!\left(\Big\lfloor\frac{x}{p_a}\Big\rfloor,a-1\right)},\qquad
\phi(x,0)=x.
\]

取 \(a=\pi(\lfloor\sqrt x\rfloor)\) 时有经典素数计数公式

\[
\boxed{\pi(x)=\phi\bigl(x,\pi(\lfloor\sqrt x\rfloor)\bigr)+\pi(\lfloor\sqrt x\rfloor)-1}.
\]

## 二、证明（要点）

\(\phi(x,a)\) 计 \(1..x\) 中不被前 \(a\) 个素数整除的整数。递归的直观：从"不被前
\(a-1\) 个整除"的集合中，减去那些被 \(p_a\) 整除且不被前 \(a-1\) 个整除者；后者恰为
\(p_a\) 乘以一个不被前 \(a-1\) 个整除的数，共
\(\phi(\lfloor x/p_a\rfloor,a-1)\) 个。

当 \(a=\pi(\lfloor\sqrt x\rfloor)\) 时，任何素因子均 \(>p_a\) 的合数至少为
\((p_a+1)^2>x\)，故 \(\phi\) 中除 \(1\) 外恰为大于 \(p_a\) 的素数，个数为
\(\pi(x)-a\)，于是 \(\pi(x)=\phi+a-1\)。

## 三、验证状态

| 层级 | 状态 |
| --- | --- |
| L0 结构 | ✅ |
| L2 数值 | ✅（精确整数核对，残差 0） |
| L4 形式化 | ⬜ |

L2 实测：

| 检查 | 范围 | 结果 |
| --- | --- | --- |
| \(\phi_{\text{rec}}(x,a)=\phi_{\text{direct}}(x,a)\) | \(a=0..7\)，\(x\in\{97,1000,99991,50000,200000\}\) | 全部相等 |
| \(\pi(x)=\phi(x,a)+a-1\)（\(a=\pi(\lfloor\sqrt x\rfloor)\)） | \(x\in\{10^3,10^4,10^5,2\cdot10^5,5\cdot10^5\}\) | 全部相等 |

## 四、诚实边界

- 本条目只核对 **Legendre 递归与其直接定义逐点一致**并举出 \(\pi=\phi+a-1\)；
  真正的 Meissel / Lehmer 加速（P2/P3 修正）由 OM-F-NT-0001 / OM-A-NT-0001 与
  `prime-pi-block` 引擎独立承担。
- 递归只是"分块"手段，本身非亚线性；亚线性来自 Meissel–Lehmer / LMO（见 OM-P-NT-0002）。
- L2 通过只能证伪、不能证明。本条目为经典恒等式，不构成优先权主张。

## 五、相关

- OM-F-NT-0001（Legendre \(\phi\) 与轮积恒等式）
- OM-A-NT-0001（Lehmer 素数计数算法）
- OM-D-NT-0001（素数指示）
- OM-P-NT-0002（第 \(n\) 素数的低复杂度公式，开放问题）
