---
id: OM-D-NT-0001
title_zh: 精确整除脉冲、素数指示与整数阶跃
status: VERIFIED(L2)
---

# OM-D-NT-0001 · 精确整除脉冲、素数指示与整数阶跃

## 一、定义

**整除脉冲**（对正整数 \(N,d\)）：

\[
\boxed{\delta_d(N)=\Big\lfloor\frac Nd\Big\rfloor-\Big\lfloor\frac{N-1}{d}\Big\rfloor}
\]

严格有

\[
\delta_d(N)=
\begin{cases}
1,&d\mid N,\\
0,&d\nmid N.
\end{cases}
\]

**素数指示函数**（\(N<2\) 时为 \(0\)，否则）：

\[
\boxed{I_{\mathbb P}(N)=\prod_{d=2}^{\lfloor\sqrt N\rfloor}\bigl(1-\delta_d(N)\bigr)}
\]

空乘积规定为 \(1\)。

**整数正阶跃**（整数 \(z\)）：

\[
\Theta(z)=\Big\lceil\frac{z}{|z|+1}\Big\rceil=
\begin{cases}
1,&z>0,\\
0,&z\le 0.
\end{cases}
\]

## 二、性质

- \(\delta_d(N)\) 把"是否整除"变成一个完全确定的代数整数量。
- \(I_{\mathbb P}(N)=1\iff N\) 为素数：若 \(N\) 为合数，则存在 \(2\le d\le\sqrt N\) 使
  \(\delta_d(N)=1\)，乘积中出现零因子；若 \(N\) 为素数，所有 \(\delta_d(N)=0\)，乘积为 \(1\)。
- 因此精确素数计数函数为严格等式

  \[
  \pi(X)=\sum_{N=2}^{X} I_{\mathbb P}(N),
  \]

  不是渐近关系 \(\pi(X)\sim X/\log X\)。

## 三、验证状态

| 层级 | 状态 | 说明 |
| --- | --- | --- |
| L0 结构 | ✅ | schema 字段齐备 |
| L1 良构 | ✅ | 符号表完整 |
| L2 数值 | ✅ | 见下，精确整数核对（残差恒为 0） |
| L3 符号 | ⬜ | 未做（离散恒等式不适合 SymPy 化简，收益低） |
| L4 形式化 | ⬜ | 未做 |

L2 实测（`05-验证中心/01-引擎/pwcv_theorems.py`，Python 3.8，纯标准库）：

| 检查 | 范围 | 结果 |
| --- | --- | --- |
| \(\delta_d(N)=1_{d\mid N}\) | \(t\le300,\ d\le t\) | 全部相等（残差 0） |
| \(I_{\mathbb P}(t)=1_{t\text{ prime}}\)（连乘 vs 独立试除） | \(t\le10000\) | 全部相等（残差 0） |
| \(\Theta(z)=1_{z>0}\) | \(z\in[-10,10]\) | 全部相等（残差 0） |

## 四、复杂度与诚实边界

- 直接用 \(I_{\mathbb P}(N)\) 试除至 \(\sqrt N\)，单点判素最坏约 \(O(\sqrt N)\) 次整除检查；
  逐点求 \(\pi(X)\) 朴素总代价约 \(O(X^{3/2})\)。这不是最优素数算法。
- L2 通过只能证伪、不能证明（红线一）。这些定义在初等数论中众所周知，本条目不构成任何优先权主张。
- 真正"素数求导"应是离散导数或分布导数（见 OM-T-NT-0001），而非普通连续导数。

## 五、相关

- OM-T-NT-0001（素数离散微积分闭环）
- OM-F-NT-0001（Legendre \(\phi\) 分块递归与轮积恒等式）
