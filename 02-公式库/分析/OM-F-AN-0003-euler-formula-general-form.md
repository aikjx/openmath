---
id: OM-F-AN-0003
title_zh: 欧拉公式（一般形式）· 复指数把加法折成旋转
status: VERIFIED(L3)
---

# OM-F-AN-0003 · 欧拉公式（一般形式）

\[
e^{z} = e^{x}\big(\cos y + i\sin y\big)\qquad (z = x+iy)
\]

取 \(x = 0\) 即得最常见的形态：

\[
e^{i\theta} = \cos\theta + i\sin\theta
\]

本条目是为消解 [OM-F-AN-0001 欧拉恒等式](OM-F-AN-0001-euler-identity.md) 里那条**悬空引用**而铸的：
它的正文写着"推广：OM-F-AN-0003（待录入）"却没有任何载体，`graph --check` 把这条引用点名成
`DANGLING`（DEFECT）。补体之后，"推广"这一步在图上真的走得通。

## 一、这条公式说的到底是什么

把 \(z \mapsto e^{z}\) 看成**群同态**，一般形式说的是一句结构话，而不是一串三角恒等式：

| 说法 | 内容 |
| --- | --- |
| 同态 | \((\mathbb{C},+) \to (\mathbb{C}^{\times},\cdot)\)，\(z \mapsto e^{z}\)，因为 \(e^{z+w}=e^{z}e^{w}\) |
| 实轴映到什么 | \(x \mapsto e^{x}\)：正实轴（模长通道） |
| 虚轴映到什么 | \(\theta \mapsto e^{i\theta}\)：**单位圆**（相位通道） |
| 核 | \(2\pi i\,\mathbb{Z}\)：\(e^{z}=1 \iff z \in 2\pi i\mathbb{Z}\) |
| 推论 | \(\mathbb{C}/2\pi i\mathbb{Z} \cong \mathbb{C}^{\times}\)，即"对数是多值的"这件事的精确形式 |

模长与相位被**分开**处理是本公式的全部威力：\(|e^{z}| = e^{x}\)，\(\arg(e^{z}) \equiv y \pmod{2\pi}\)。

## 二、三个直接后果（都在同一条公式里）

1. **de Moivre 公式**：\((\cos\theta + i\sin\theta)^{n} = \cos n\theta + i\sin n\theta\)，
   因为 \(e^{in\theta} = (e^{i\theta})^{n}\)。幂运算被降格为加法。
2. **\(n\) 次单位根**：\(e^{z}=1\) 的解是 \(2\pi i\,\mathbb{Z}\)，故 \(z^{n}=1\) 的根恰为
   \(\zeta_{n}^{k} = e^{2\pi i k/n}\ (k = 0,\dots,n-1)\)，构成循环群 \(\cong \mathbb{Z}/n\mathbb{Z}\)。
   这是傅里叶分析、DFT、以及分圆域理论的公共起点。
3. **单位圆的参数化**：\(\theta \mapsto (\cos\theta, \sin\theta)\) 是**周期**参数化，周期 \(2\pi\)
   不是经验事实，而是核 \(2\pi i\mathbb{Z}\) 的像——本公式在此把"周期"与"指数"绑定。

## 三、为什么它在本库的难题侧被反复引用

\(e^{i\theta}\) 提供了"用加法写乘法、用线性写旋转"的唯一标准通道：任何**相位型**的量（波动、
规范场 \(U(1)\) 荷、筛法里的特征和 \(e(N\alpha)\)）都靠它把离散求和变成可解析延拓的对象。
本库难题侧的指数和审计（见 `05-验证中心/03-结果/2026/09/` 一系列结果档）使用的正是这条通道。

## 四、验证状态

| 层级 | 状态 | 说明 |
| --- | --- | --- |
| L0 结构 | ✅ | `openmath lint` 通过 |
| L1 良构 | ✅ | 符号表完整，假设声明了定义取法（幂级数） |
| L2 数值 | ✅ | mpmath 50 位，脚本现印 `SAMPLE_COUNT = 52`、`MAX_ABS_RESIDUAL = 9.23e-50`（容差 1e-40），载体 `scratch/FAN0003_verify.txt` |
| L3 符号 | ✅ | SymPy `simplify` 两式归零 |
| L4 形式化 | ⬜ | 未绑定 mathlib（`Complex.exp_mul_I` 存在但本库未接） |

**诚实说明**：在幂级数定义下，本公式是定义的直接推论，L2/L3 的"通过"**几乎不提供信息量**；
它检验的是实现一致性，不是数学内容。本条目的内容在 §一–§三的结构陈述里，而那些陈述**没有**被 L2/L3 检验。

## 五、已知陷阱（`caveat`）

1. **反解即多值**：由 \(w = e^{i\theta}\) 反解 \(\theta\) 只能模 \(2\pi\) 得到；凡"取辐角"的步骤都要显式分支，
   否则会把 \(e^{\log w}\) 与 \(w\) 的两个不同含义混用（前者单值、后者需选支）。
2. **数值伪通过**：双精度残差约 \(10^{-17}\) 而非 0，残差量级必须与精度设置匹配。
3. **定义循环**：若把 \(e^{i\theta}=\cos\theta+i\sin\theta\) 当作定义，则 §一 的同态性质需要另行证明；
   本记录取"级数定义"讲法，故同态性由 \(e^{z+w}=e^{z}e^{w}\)（级数的 Cauchy 乘积）给出。

## 六、相关条目

- 特例：[OM-F-AN-0001 欧拉恒等式](OM-F-AN-0001-euler-identity.md)（\(\theta = \pi\)）
- 相关：[OM-F-AN-0002 Riemann ζ 函数函数方程](OM-F-AN-0002-riemann-zeta-functional-equation.md)

## 七、复现

```bash
python 08-工具/examples/verify_OM-F-AN-0003.py
python -m openmath lint
python -m openmath graph --check
```
