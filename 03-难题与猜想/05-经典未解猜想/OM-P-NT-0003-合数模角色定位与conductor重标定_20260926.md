# OM-P-NT-0003 · 合数模角色定位与 conductor 重标定

> 日期：2026-09-26　状态：**OPEN（未解决）**　AI 辅助：是　独立人工复核：**否（待）**
> 机器证据：`05-验证中心/03-结果/2026/09/OM-P-NT-0003-conductor-localization-20260926.json`
> 引擎：`05-验证中心/01-引擎/goldbach_conductor_localization_20260926.py`
> 前稿：[结构分解定理：投影恒等式与角色锁定](OM-P-NT-0003-结构分解定理_投影恒等式与角色锁定_20260925.md)（T1–T5）
> 配套：`OM-P-NT-0003-charpair-correlation-20260925.json`、`OM-P-NT-0003-projection-identity-20260925.json`

---

## 0. 本文档是什么，不是什么

**是**：把前稿 §8.4 明确标注的**后续项**闭合 —— 前稿的 T4（角色定位）只对**素数模**成立，因为非本原特征的 \(\tau(\chi)\ne\sqrt q\)；本文给出任意模的 T4′，并补上非本原 Gauss 和公式（T6）与主特征公式（T6b）。三条都有机器校验，并含**一个阴性对照**（主动检验错误命题并期望被推翻）。

**不是**：哥德巴赫猜想的证明。**不**填满突破靶心清单中的任何一项，进度分子**不变**。猜想保持 **OPEN**。

---

## 1. 记号

\(\chi\) 为 \(\bmod q\) 的 Dirichlet 特征，\(G_q=(\mathbb Z/q\mathbb Z)^*\)，\(\varphi(q)=|G_q|\)。
\(\chi\) 的 **conductor** \(c(\chi)\) 是使 \(\chi\) 经 \(G_q\to G_d\) 分解、在核上平凡的最小 \(d\mid q\)；等价地 \(\chi\) 由**本原**特征 \(\chi^*\bmod c\) 诱导，\(c=c(\chi)\)。记

\[
r=\frac{q}{c},\qquad
\tau(\chi)=\sum_{a\in G_q}\chi(a)e\!\left(\frac aq\right),\qquad
\psi(N,\chi)=\sum_{n\le N}\Lambda(n)\chi(n)\ \ (\chi(n)=0\text{ 当 }(n,q)>1),
\]
\[
V_q(r)=\sum_{n\le N}\Lambda(n)e\!\left(\frac{rn}{q}\right),\qquad
R_q(r)=\sum_{\substack{n\le N\\(n,q)>1}}\Lambda(n)e\!\left(\frac{rn}{q}\right).
\]

约定 \(\mu\) 为 Möbius 函数，\(\chi^*(r)=0\) 当 \((r,c)>1\)。

---

## 2. T6 — 非本原特征 Gauss 和（imprimitivity）

**定理 6.** 设 \(\chi\bmod q\) 由本原特征 \(\chi^*\bmod c\) 诱导，\(r=q/c\)。则

\[
\boxed{\ \tau(\chi)=\mu(r)\,\chi^*(r)\,\tau(\chi^*)\ }\tag{6.1}
\]

其中 \(\chi^*(r)=0\) 当 \((r,c)>1\)。

**证明（文献引用 + 数值确认，本文不重证）.** (6.1) 是经典的 imprimitivity 公式（Davenport, *Multiplicative Number Theory*, Ch. 9；Iwaniec–Kowalski, *Analytic Number Theory*, (3.12)）。本文对该公式的态度与对待显式公式一致：**引用**，并在 §6 用 15 个模、111 个非主特征把它核对到 \(4.2\times10^{-14}\)。

需要明确指出 (6.1) 的两个退化机制，因为它们在有限尺度上**频繁发生**（本文 111 个特征中 28 个如此）：

1. **\((r,c)>1\)**：此时按约定 \(\chi^*(r)=0\)，公式给 \(\tau(\chi)=0\)；
2. **\(\mu(r)=0\)**（即 \(r\) 含平方因子）：公式给 \(\tau(\chi)=0\)。

两个机制的**一致性自检**：(a) \(c=q\)（本原，\(r=1\)）时 (6.1) 退化为恒等式 \(\tau(\chi)=\tau(\chi^*)\)，无信息但无矛盾；(b) 由 §3 的 T6b，\(q\) 含平方因子时主特征自身也满足 \(\tau=0\)，即"\(\tau=0\)"在本框架中是**常见**情形而非例外，故机制 2 并非人为修补。∎

**说明（为什么不在此处补一个自造证明）**：\(G_q\cong G_c\times G_r\) 仅在 \((c,r)=1\) 时成立，而 \((c,r)>1\) 恰是需要机制 1 的情形；把 \(a\) 写成 \(b+ct\) 的朴素 CRT 参数化在 \((c,r)>1\) 时不再是双射。我们因此**不**给出自造证明，只引用并数值确认 —— 这与本库对显式公式的处理一致。

**推论 6.1（节省是 \(\sqrt{\text{conductor}}\)，不是 \(\sqrt q\)）.** \(|\tau(\chi)|=|\mu(r)|\cdot|\chi^*(r)|\cdot\sqrt c\)，故

\[
|\tau(\chi)|\in\{0,\ \sqrt{c(\chi)}\}.
\]

**说明**：\(\mu(r)=0\)（\(r\) 含平方因子）或 \((r,c)>1\) 时 \(\tau(\chi)=0\)。**这正是前稿把 \(|J|=\sqrt q\) 的检验局限于本原特征的真正原因** —— 对非本原特征，\(\sqrt q\) 是**错**的标度。

**共轭版本（T4′ 真正需要的）**：下节 (4.1′) 中出现的系数是 \(\tau(\overline\chi)\) 而非 \(\tau(\chi)\)，因此我们把 (6.1) 对 \(\overline\chi\) 单独核对了一遍（\(\overline\chi\) 由 \(\overline{\chi^*}\) 诱导，conductor 同为 \(c\)）：111 个特征全部满足 \(|\tau(\overline\chi)|\in\{0,\sqrt c\}\)，误差 \(\le2.4\times10^{-14}\)。**这不是 \(\tau(\chi)\) 结果的自动推论**（有 \(\tau(\overline\chi)=\chi(-1)\overline{\tau(\chi)}\)，标度相同但引用的公式不同），故必须单独验证。

**阴性对照（检验的鉴别力）.** 我们主动检验**错误**命题「非本原非主特征也满足 \(|\tau(\chi)|=\sqrt q\)」：在 10 个合数模、36 个非本原非主特征上，满足该式的有 **0 个** ⇒ 错误命题被推翻，说明 §6 的阳性结果不是"把什么都判为真"的空转。（对照样本 36，非空。）

---

## 3. T6b — 主特征的 Gauss 和

**定理 6b.** \(\chi_0\) 为 \(\bmod q\) 主特征（\(q>1\)），则

\[
\boxed{\ \tau(\chi_0)=\sum_{(a,q)=1}e\!\left(\frac aq\right)=\mu(q)\ }\tag{6.2}
\]

**证明.** 用 \(1_{(a,q)=1}=\sum_{d\mid(a,q)}\mu(d)\) 展开：

\[
\sum_{(a,q)=1}e\!\left(\frac aq\right)=\sum_{d\mid q}\mu(d)\sum_{\substack{a\bmod q\\ d\mid a}}e\!\left(\frac aq\right)
=\sum_{d\mid q}\mu(d)\sum_{k=0}^{q/d-1}e\!\left(\frac k{q/d}\right).
\]

内层和为 \(0\)（当 \(q/d>1\)）、为 \(1\)（当 \(d=q\)）。故结果为 \(\mu(q)\)。∎

**注**：\(q\) 含平方因子时 \(\tau(\chi_0)=0\) —— 与 (6.1) 中"\(\tau=0\) 是常见情形而非例外"一致（校验的 111 个特征中有 **28** 个 \(\tau=0\)）。

---

## 4. T4′ — 任意模的角色定位（前稿 T4 的合数模推广）

**定理 4′.** 对**任意** \(q\)、任意 \(r\in G_q\)：

\[
\boxed{\ V_q(r)=\frac{1}{\varphi(q)}\sum_{\chi\bmod q}\tau(\overline\chi)\,\chi(r)\,\psi(N,\chi)\;+\;R_q(r)\ }\tag{4.1'}
\]

其中余项有**闭式**

\[
\boxed{\ R_q(r)=\sum_{p\mid q}\log p\sum_{\substack{k\ge1\\ p^k\le N}}e\!\left(\frac{r p^k}{q}\right)\ }\tag{4.2'}
\]

从而

\[
|R_q(r)|\le\sum_{p\mid q}\log p\,\big\lfloor\log_p N\big\rfloor=O\!\big(\omega(q)\log N\big).
\]

**证明.**

**第 1 步（加性 → 乘性，任意模）.** 对任意模 \(q\)，\(\{\chi\}_{\chi\bmod q}\) 是 \(G_q\) 上函数空间的**正交基**（\(G_q\) 非循环时同样成立，这正是素数模证明可直接搬运的原因）：

\[
e\!\left(\frac aq\right)=\frac{1}{\varphi(q)}\sum_{\chi}\tau(\overline\chi)\chi(a),\qquad a\in G_q,
\]

因为 Fourier 系数 \(\frac1{\varphi(q)}\sum_{a\in G_q}e(a/q)\overline{\chi(a)}=\frac{\tau(\overline\chi)}{\varphi(q)}\)。

**第 2 步.** 对 \((n,q)=1\) 取 \(a\equiv rn\)，用乘性得 \(e(rn/q)=\frac1{\varphi(q)}\sum_\chi\tau(\overline\chi)\chi(r)\chi(n)\)；乘 \(\Lambda(n)\) 并对 \((n,q)=1,\ n\le N\) 求和，右端即 \(\psi(N,\chi)\)。

**第 3 步（余项的闭式）.** 剩余的 \(n\le N,\ (n,q)>1\)：\(\Lambda(n)\ne0\Rightarrow n=p^k\)，而 \((p^k,q)>1\iff p\mid q\)。故 \(R_q(r)=\sum_{p\mid q}\sum_{k:p^k\le N}\log p\,e(rp^k/q)\)，即 (4.2′)；逐项取模并用 \(|\{k:p^k\le N\}|=\lfloor\log_p N\rfloor\) 得界。\(\blacksquare\)

**推论 4′.1（前稿 T4 是 \(q\) 素数的特例）.** \(q\) 为素数时只有 \(p=q\) 一项，且 \(e(rq^k/q)=e(rq^{k-1})=1\)，故

\[
R_q(r)=\log q\cdot\lfloor\log_q N\rfloor=E_q,
\]

**与 \(r\) 无关**，恰为前稿 T4 的余项。**机器实测确认**（见 §6）：素数模余项离散度 \(\sim10^{-11}\)（无关），合数模则不然。

**推论 4′.2（合数模的余项本身携带非平凡模态）.** 对合数 \(q\)，\(R_q(r)\) 一般**依赖 \(r\)**（实测离散度 1.2–4.9），故 \(R_q\) 不是常数模态：\(P_q^\perp R_q\ne0\)。**这与素数模的结构性差别必须保留** —— 素数模下余项可整体并入主项，合数模下不行。

---

## 5. 结构含义：按 conductor 分层后的"节省"

把 §2 与 §4′ 合看。非主特征 \(\chi\ne\chi_0\) 在 (4.1′) 中由系数 \(\tau(\overline\chi)\) 加权，而 \(\overline\chi\) 与 \(\chi\) 有相同的 conductor \(c(\chi)\)，故

\[
|\tau(\overline\chi)|=|\tau(\chi)|\in\{0,\sqrt{c(\chi)}\}.
\]

于是"\(\sqrt q\) 节省"的正确读法是：

\[
\textbf{每个非主特征的有效节省是 }\sqrt{c(\chi)}\textbf{，按其 conductor 分层}\ \ \sum_{\chi\ne\chi_0}|\tau(\overline\chi)|\;\asymp\;\sum_{c\mid q}\sqrt c\cdot\#\{\chi^*\bmod c\ \text{本原}\}.
\]

这正是 Goldbach 分析中 \(q\)-平均的**实际结构**：先按 conductor 分层，再在每层内做 \(q\)-平均。前稿的"\(|J|=\sqrt q\)"仅在**本原层**（\(c=q\)）成立，是这一分层的顶项。

---

## 6. 机器校验汇总

脚本：`goldbach_conductor_localization_20260926.py`（纯标准库；特征由 CRT + 素数幂独立基构造，与前轮共用，不重复造轮子）。容差：T6/T6b 用 \(10^{-8}\)，T4′ 用 \(10^{-8}\)；下面给出**实测**值。

| 项 | 覆盖 | 实测残差 |
|---|---|---|
| T6 (6.1) 非本原 Gauss 和 | 15 模 / 111 个非主特征 | \(\max=4.16\times10^{-14}\)；其中 \(\tau=0\) 有 28 个、\(|\tau|=\sqrt c\) 有 83 个（28+83=111 ✓） |
| T6 的**共轭版本**（T4′ 实际使用） | 同上 111 个特征 | \(\max=2.43\times10^{-14}\)；\(|\tau(\overline\chi)|\in\{0,\sqrt c\}\) 覆盖 111/111 |
| T6 **阴性对照** | 10 模 / 36 个非本原非主特征 | 满足 \(\lvert\tau\rvert=\sqrt q\) 者 **0** 个（错误命题被推翻 ✓） |
| T6b (6.2) 主特征 | 18 模 | \(\max|\tau(\chi_0)-\mu(q)|=2.13\times10^{-15}\) |
| T4′ (4.1′) 恒等式 | 14 模 × 3 尺度（\(N=200,500,1000\)） | \(\max=9.58\times10^{-11}\) |
| T4′ (4.2′) 闭式余项 | 同上 | \(\max=9.58\times10^{-11}\) |
| T4′ 余项上界 | 同上 | **越界量 0.0**（界与实测同为 \(\sum_{p\mid q}\log p\lfloor\log_p N\rfloor\)） |
| T4′ 素数模余项与 \(r\) 无关 | \(q=3,5,7,11,13\) | 离散度 \(\sim10^{-11}\) ⇒ 无关 ✓（与推论 4′.1 一致） |

**合数模余项对 \(r\) 的依赖（离散度 \(\max_r|R_q(r)-R_q(r_1)|\)，跨 3 个尺度）：**

| \(q\) | 离散度区间 | 判定 |
|---|---|---|
| 4 | \(2.2\times10^{-13}\sim6.3\times10^{-12}\) | **退化**：\(R_4(r)=\log2\,(e(r/2)+1)\equiv0\) |
| 6 | \(1.3\times10^{-11}\sim1.20\) | 依赖 \(r\)；**在 \(N=500\) 上偶然相消为零**（披露见 §7） |
| 8 | 1.38629 | 依赖 |
| 9 | 1.90285 | 依赖 |
| 12 | 1.2006 \(\sim\) 4.5984 | 依赖 |
| 15 | 2.0897 \(\sim\) 4.8773 | 依赖 |
| 16 | 2.36655 | 依赖 |
| 25 | 3.06133 | 依赖 |
| 27 | 3.52428 | 依赖 |

脚本已把"按模跨尺度汇总"与"按单一尺度判定"分开记录，避免把上面的偶然相消误读为退化。

---

## 7. 诚实边界（不可绕过）

1. **全部结论是有限尺度数值核对，不是证明。** 容差 \(10^{-8}\)，模 \(q\le36\)，尺度 \(N\le1000\)。T6 的完整配对证明属经典结果，本文**引用并数值确认**（111 个特征，误差 \(10^{-14}\)），未重证。
2. **\(q=4\) 的"\(r\) 无关"是退化而非普遍现象**：\(R_4(r)\equiv0\)。已单独标注。
3. **余项 \(r\) 依赖可在个别 \(N\) 上偶然消失**：如 \(q=6,\ N=500\) 时 \(R_6(1)\) 的虚实部同时相消（\(R_6(-r)=\overline{R_6(r)}\)，故离散度 \(=2|\operatorname{Im}R_6(1)|\)）。因此**只按单一 \(N\) 判定"与 \(r\) 无关"会误判**；本文按模跨 3 个尺度汇总。
4. **本条不改变任何靶心状态**：T4′ 只把余项的**形状**说清楚，余项仍由非主角色 \(L\)-零点承载 —— 靶心 A/C 未动，靶心 B（\(\{N-p\}\) 的双线性相消）未动。
5. **未接入真实 \(L\) 零点**：本文用有限尺度的 von Mangoldt 频谱，未模拟零点分布；渐近行为需解析输入。
6. **独立人工复核：否。** 本稿由 AI 辅助完成，证据等级仍为 L2，不得使用"已证明"。

---

## 8. 与前稿、与靶心清单的对应

- 前稿 §8.4「T4 目前只对素数模给出带精确余项的形式；合数模需按 conductor 重新组织」——**已闭合**（本文 T4′ + 推论 4′.1）。
- 前稿 §8.3「模型与 \(G(N)\) 之间的 major/minor arc 过渡与截断尾项 \(q>Q\)」——**仍未完成**。
- 靶心裁定：

| 靶心 | 本轮影响 |
|---|---|
| A（分布水平 \(>1/2\)） | 未动。T4′ 反而更精确地指出：要 \(o(N)\) 必须把各 conductor 层的 \(|\psi(N,\chi)|\) 压到 \(\sqrt N\) 级 |
| B（双线性越障，FI 型） | 未动 |
| C（minor-arc） | 未动（A 的镜像） |
| D（新恒等式） | **部分推进**：T6/T6b/T4′ 是结构引理，但未给出 \(r(N)\ge1\) 的显式公式，**未填满** |
| E（条件归约） | 不计进度 |

**裁定：A–E 无一被填满 ⇒ 进度分子不变 ⇒ 强哥德巴赫猜想保持 OPEN。**

---

## 9. 复现

```bash
cd 05-验证中心/01-引擎
python goldbach_conductor_localization_20260926.py
# 输出：../03-结果/2026/09/OM-P-NT-0003-conductor-localization-20260926.json
```
