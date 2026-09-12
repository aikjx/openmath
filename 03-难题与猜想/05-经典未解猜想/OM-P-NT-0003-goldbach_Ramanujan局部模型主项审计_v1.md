# 强哥德巴赫：Ramanujan 局部模型主项的审计与缺口定位

日期：2026-09-13。接续 `证明整理与缺口审计.md`、`条件化主项_固定筛层定理与量词缺口.md`、
`OM-P-NT-0003-goldbach_PWCV结构研究_v1.md`。

> **诚实性声明**：本文**不证明强哥德巴赫猜想**。本文审计的对象是"用 Ramanujan 和构造的局部素数模型
> $\nu_w$"及其主项链 (1)–(13)。结论是：**(1)–(7) 严格成立（需一处量词修正），是无条件定理；
> (12)/(13) 未证，且它不是对原问题的归约，而是恒等式改写。**

核验脚本：`research/goldbach_pwcv/verify_ramanujan_local_model.py`（标准库，可复现）
机器可读结果：`research/goldbach_pwcv/ramanujan_local_model_verification.json`

---

## 0. 三行结论

1. **(1)–(7) 正确且严格**。正交关系、误差因子化、奇异级数下界 $\mathfrak S_w>2C_2=1.3203236316\ldots$
   全部逐条复算通过（穷举 1024 组 $(N,q,r)$、$q\le60$ 的 Ramanujan 和定义比对、$w=7$ 的闭式比对，
   零反例）。
2. **模型有闭式**：$\displaystyle \nu_w(n)=A_w\,\mathbf 1_{(n,P(w))=1},\quad A_w=\prod_{p\le w}\frac p{p-1}\sim e^\gamma\log w$。
   所以整个构造就是"筛到 $w$ 的埃拉托斯特尼筛 + 归一化权重"，与本机已有的 CRT 局部密度
   （`证明整理与缺口审计.md` 命题 3、`OM-P-NT-0003` 命题 2.1）是**同一个对象的两种写法**。
3. **(12)/(13) 是恒等式，不是归约**：由 (9)–(11) 相加即得
   $$
   2C_w(N)+Q_w(N)=R(N)-N\mathfrak S_w(N)+O(N^{0.1+o(1)}).
$$
   故 (12) $\iff R(N)>N\bigl(\mathfrak S_w(N)-1.3203\bigr)$，(13) $\iff |R(N)-N\mathfrak S_w(N)|<1.32N$。
   "缺口精确到一行"是真的，但那一行的强度就是"$R(N)$ 相对 Hardy–Littlewood 主项的偏差 $<1.32N$"，
   在已知方法下与"每个大偶数 $R(N)>0$"同等困难。

---

## 1. 逐条核验表

| 步骤 | 内容 | 状态 | 说明 |
|---|---|---|---|
| (1) | $\nu_w(n)=\sum_{q\mid P(w)}\frac{\mu(q)}{\varphi(q)}c_q(n)$ | 定理 | 显式有限和，无假设 |
| (2) | 周期平均 $=\;c_q(N)[q=r]$ | **已验证** | 展开后 $a/q\equiv b/r\pmod 1$，既约分数分母唯一 $\Rightarrow q=r,a=b$。穷举 $q,r\mid P(7)$、4 个 $N$，共 1024 组，**0 反例** |
| 误差 | $O\!\left(\sum_{q,r}[q,r]\right)$ | 正确 | 系数 $1/(\varphi(q)\varphi(r))$ 恰好抵消 $|c_qc_r|\le\varphi(q)\varphi(r)$，不完全周期损失 $\le L$；对角项 $\le 2/\varphi(q)\le2$ |
| (3) | $\sum[q,r]=\prod(1+3p)=e^{(1+o(1))w}$ | 正确 | 每素数贡献 $1,p,p,p$；$\log\prod=\theta(w)+\pi(w)\log3+O(\log\log w)=w\left(1+O\!\left(\frac1{\log w}\right)\right)$ |
| (4) | $\sum\nu\nu=N\mathfrak S_w+O(N^{1/10+o(1)})$ | 定理 | 由 (2)+(3) |
| (5) | $\mathfrak S_w=\prod_{p\le w}\left(1+\frac{c_p(N)}{(p-1)^2}\right)$ | 正确 | Ramanujan 和对互素模可乘 |
| (6) | $\mathfrak S_w>2C_2=1.3203236316\ldots$ | **正确但量词需修正** | 需 $w\ge2$，即 $N\ge e^{20}\approx4.9\times10^8$；见 §3.1 |
| (7) | 点态正主项 $>1.3203N-N^{0.1+o(1)}$ | 定理（同上量词） | 逐 $N$ 成立，不需 PNT、不需平均 |
| 纠错 | $\mu*(\Lambda*1)=\Lambda$ | **正确** | $\Lambda*1=\log$，$\mu*\log=\Lambda$；故完整三线性块确实在重建 Goldbach 本身 |
| (8)–(11) | $R=N\mathfrak S_w+2C_w+Q_w$ | 恒等式 | 交叉项对称合并已核对 |
| 素数幂 | $O(\sqrt N\log^2N)=o(N)$ | 正确（可略改进为 $O(\sqrt N\log N)$） | 素数幂个数 $O(\sqrt N/\log N)$，每项 $\le\log^2N$ |
| (12)/(13) | 余项下界 | **未证** | 见 §3.3、§4、§5 |

---

## 2. 闭式化简（本次审计新增，且可验算）

因为 $\mu(q)c_q(n)/\varphi(q)$ 对互素模可乘，

$$
\nu_w(n)=\prod_{p\le w}\left(1+\frac{\mu(p)c_p(n)}{\varphi(p)}\right)
=\prod_{p\le w}\left(1-\frac{c_p(n)}{p-1}\right),
\qquad
c_p(n)=\begin{cases}p-1,&p\mid n\\-1,&p\nmid n\end{cases}
$$

于是

$$
\boxed{\ \nu_w(n)=A_w\,\mathbf 1_{(n,P(w))=1},\qquad A_w=\prod_{p\le w}\frac p{p-1}\sim e^\gamma\log w\ }
$$

（脚本以精确有理数对 $w=7$、$n\le630$ 全量比对定义式与闭式，**0 反例**；$A_7=\frac21\frac32\frac54\frac76=\frac{35}{8}=4.375$。）

三点直接推论：

**(a) 主项是纯 CRT。** $\sum_{n<N}\nu\nu=A_w^2\#\{n<N:(n(N-n),P(w))=1\}=A_w^2\bigl(\tfrac NP A_M+O(P)\bigr)$，
而 $A_w^2A_M/P=\prod_{p\mid N}\frac p{p-1}\prod_{p\nmid N}\frac{p(p-2)}{(p-1)^2}=\mathfrak S_w(N)$（与 (5) 逐因子相同）。
故 (4) 就是"局部可行密度 $\times$ 归一化权重平方"，与本机命题 2.1/命题 3 完全同一对象。

**(b) 误差可以更锐。** Ramanujan 路线给 $O(\prod(1+3p))=O(e^w3^{\pi(w)})$；
直接用闭式给 $O(A_w^2P(w))=O(e^w\log^2w)$，小一个因子 $3^{\pi(w)}=N^{o(1)}$。
两者同为 $N^{1/10+o(1)}$，不影响结论，但闭式界更干净。

**(c) $\nu_w$ 不是"新模型"。** 它就是筛到 $w$ 的筛函数乘以常数 $A_w$。
因此 (1)–(7) 与本机已有结论"不存在任何有限模意义下的局部障碍"一致；
新意在于**用 Ramanujan 正交性把常数 $A_w^2D_M$ 一步写成 $\mathfrak S_w$**，写得漂亮且可逐项验算。

---

## 3. 三处必须修正

### 3.1 (6) 的"对所有偶数 $N$"应为"$N\ge e^{20}$"

$w=\frac1{10}\log N\ge2\iff N\ge e^{20}\approx4.85\times10^8$；
$w\ge3\iff N\ge e^{30}\approx1.07\times10^{13}$。
若 $w<2$，乘积为空、$\mathfrak S_w(N)=1<1.3203$，(6) 与 (7) 都失败。
**关键后果**：在一切可计算尺度上（$N\le10^{18}$ 也才 $w\le4.15$），$w=0.1\log N<2$，
模型几乎是空的（$N=2\times10^6$ 时 $w=1.45$，$\nu_w\equiv1$，$\mathfrak S_w=1$）。
所以 (7) 是**渐近定理**，它不能、也不必与有限数值验证对接。
（数值无碍：Goldbach 已被验证到 $4\times10^{18}\gg e^{20}$。）

### 3.2 Cauchy 的量级：$Q_w$ 是 $N\log N$，不是 $N\sqrt{\log N}$

$$
\|E_w\|_2^2=\sum_{n<N}E_w(n)^2,\qquad
\sum_{n<N}\Lambda(n)^2\sim N\log N,\quad
\sum_{n<N}\nu_w(n)^2=N\!\!\sum_{q\mid P(w)}\frac{\mu(q)^2}{\varphi(q)}\approx e^\gamma N\log w,
$$
且 $\sum\Lambda\nu_w\approx\sum\nu_w^2$（模型几乎就是 $\Lambda$ 的投影），故
$$
\|E_w\|_2^2\sim N\log N\ (\text{渐近}),\qquad
|Q_w|\le\|E_w\|_2^2,\qquad
|C_w|\le\|\nu_w\|_2\|E_w\|_2\sim N\sqrt{\log N\log\log N}.
$$
即：**$C_w$ 的损失因子是 $\sqrt{\log N}$，$Q_w$ 的损失因子是 $\log N$**——原文"Cauchy 给 $N\sqrt{\log N}$"
只对 $C_w$ 成立。实测（$N=10^6\sim2\times10^6$、$w=10,20$）：$\|E_w\|_2^2/N=7.0\sim9.1$，
而 $\log N=13.8\sim14.5$（有限尺度上模型已吸收一部分质量），仍需再压 $5\sim7$ 倍才能进到 $1.32$。

### 3.3 (12)/(13) 没有降低难度

由 (9)–(11) 相加，**恒等地**有
$$
2C_w(N)+Q_w(N)=R(N)-N\mathfrak S_w(N)+O(N^{0.1+o(1)}).
$$
左边被定义成"右边剩下的东西"，因此：

* (12) $\iff R(N)>N(\mathfrak S_w(N)-1.3203)$；
* (13) $\iff |R(N)-N\mathfrak S_w(N)|<1.32N$，即"$R$ 对 HL 主项的相对误差 $<100\%$"；
* 最弱的目标 $\Delta>-\mathfrak S_wN$ 就是 $R(N)>0$，与 Goldbach 完全等价。

这与本机 `证明整理与缺口审计.md` §8 已经得出的判断**完全一致**：
> "正确的最低需求是 $\Delta>-\mathcal M$。但它与 $H>0$ 完全等价，单独改写并未降低难度。"

命名"中心化余项"不改变这一点。**只能作为等价重述记录，不能写成引理。**

---

## 4. 分层：不同的 $N$ 到底需要多少

把常数 $1.3203$ 换回 $\mathfrak S_w(N)$ 本身，需求是

$$
R(N)>N\bigl(\mathfrak S_w(N)-1.3203\bigr),\qquad
\mathfrak S(N)=2C_2\!\!\prod_{p\mid N,p>2}\frac{p-1}{p-2}\in[2C_2,\;2C_2e^\gamma\log\log N].
$$

| $N$ 的类型 | $\mathfrak S$ | 需要 | 相对真值（$R\approx N\mathfrak S$） |
|---|---|---|---|
| $N=2^k$（无小奇素因子） | $1.3203+\dfrac{13.2}{\log N\log\log N}$ | $R(N)\gtrsim \dfrac{13.2\,N}{\log N\log\log N}$ | 差 $\log N\log\log N/13$ 倍 |
| $3\mid N$ | $2.6406$ | $R(N)>1.3203N$ | 主项的 $50\%$ |
| 小素因子多（如 $N=2310m$） | $\to 2C_2e^\gamma\log\log N$ | $R(N)\gtrsim(1-1.32/\mathfrak S)N\mathfrak S$ | 主项的 $70\%\sim100\%$ |

**硬情形是"小素因子多的 $N$"**（需要接近完整渐近），**最松情形是 $N=2^k$**（只需 $R(N)\gg N/\log N$ 量级）。
但即便最松的情形也完全开放：**目前对"所有充分大偶数"连 $R(N)>0$ 都无法无条件证明**，
更不用说 $R(N)\gg N/(\log N\log\log N)$。

---

## 5. (13) 周围的已知定理边界

| 命题 | 状态 | 备注 |
|---|---|---|
| $\displaystyle\sum_{\substack{N\le X\\N\ \text{偶}}}\bigl(R(N)-N\mathfrak S_w(N)\bigr)=o(X^2)$ | **已证** | 只需 PNT：$\sum_{m\le Y}E_w(m)=o(Y)$，与 $N$ 求和交换即得。实测 $X=2\times10^5,w=10$：比值 $-1.48\times10^{-4}$ |
| (13) 对几乎所有偶数成立 | **已证** | Montgomery–Vaughan 型：例外集 $\ll X^{1-\delta}$（$\delta>0$，后人有数值改进）。属文献背景，本机未独立复算 |
| (13) 对**每个**偶数成立 | **开放** | 与"每个大偶数 $R(N)>0$"同等；本机 §6 已证 parity 屏障下非负筛权合法下界恒为 $0$ |
| $\|Q_w\|\le\|E_w\|_2^2\sim N\log N$ | 已证（Parseval） | 比所需大 $\log N$ 倍 |
| 用 Vinogradov 小弧界改进 $Q_w$ | 失败 | $\int_{\mathfrak m}|\hat E|^2\le\sup_{\mathfrak m}|\hat E|\int|\hat E|\ll N^{3/2}(\log N)^{-A}$，反而更差 |

**因此 (13) 的实质困难是标准的二元问题困难**：需要一个把 Parseval 改进 $\log N$ 倍的点态手段，
而这正是圆法小弧在二元问题上失效之处（与本机 `OM-P-NT-0003` §6–§8 的 EH$_\mu$ 缺口同源）。

---

## 6. 数值证据（`verify_ramanujan_local_model.py`，本次实跑）

| 检查 | 结果 |
|---|---|
| Ramanujan 和 定义 vs 闭式（$q\le60,\ n\le40$） | **0 反例** |
| 正交关系 (2)（$q,r\mid P(7)$，$N=30,100,2310,65536$，1024 组） | **0 反例** |
| 闭式 $\nu_w=A_w\mathbf 1_{(n,P(w))=1}$（$w=7$，精确有理数，$n\le630$） | **0 反例**，$A_7=35/8$ |
| $2C_2$ | $1.320323632042$（文献 $1.320323631694$，差 $3.5\times10^{-10}$，来自 $p\le2\times10^6$ 截断+尾部校正） |
| (4) 主项精度 $N=10^6,w=10$ | $\lvert S-N\mathfrak S_w\rvert=1.82$，界 $\prod(1+3p)=2.46\times10^4$ |
| (4) 主项精度 $N=2\times10^6,w=20$ | $\lvert S-N\mathfrak S_w\rvert=14.4$，界 $1.01\times10^{11}$ |
| $N=2^{20}$（$\mathfrak S$ 最小的类型） | $\mathfrak S_{20}=1.3347>2C_2=1.3203$ ✓ |
| $N=10^6$ | $\mathfrak S_{20}=1.7796$；$R/N=1.7566$ |
| 判据 $\lvert 2C_w+Q_w\rvert/N<1.32$（8 组 $N,w$） | $0.011\sim0.137$，**全部成立**（数值上远低于阈值） |
| $\|E_w\|_2^2/N$ | $7.0\sim9.1$（$\log N=13.8\sim14.5$） |
| 平均 $\sum_{\text{偶}N\le X}(R-N\mathfrak S_w)/X^2$，$X=2\times10^5$ | $-1.48\times10^{-4}$ |

> 数值全部"通过"不构成 (12) 的证据：可计算尺度上 $w=0.1\log N<2$，模型退化；
> 且有限数据永远不能决定一个逐点渐近估计（本机既有结论，§9）。

---

## 7. 状态框

$$
\boxed{\text{局部同余主项：已严格证明，且一致为正（}$\mathfrak S_w>2C_2$，\ N\ge e^{20}$\text{）}}
$$

$$
\boxed{\text{未证：真实素数相对局部模型的固定移位二阶相关下界（等价于 }R(N)-N\mathfrak S_w(N)>-1.3203N\text{）}}
$$

**强哥德巴赫仍未证明。** 若继续此框架，唯一有内容的目标是下列等价命题之一：

1. $Q_w(N)+2C_w(N)=o(N)$ 的点态版本；
2. $R(N)\ge(1-o(1))N\mathfrak S(N)$ 对**每个**偶数（即 HL 渐近的逐点形式）；
3. 弱化版：$R(N)\gg N/(\log N\log\log N)$ 对**每个**偶数（对 $N=2^k$ 已够，仍开放）；
4. 本机既有等价目标：$\mathrm{EH}_\mu(\theta>1/2)$（`OM-P-NT-0003` §8）。

**不应做的事**：把 (12) 命名为引理、或用"余项看起来很小/数值支持"替代证明。
