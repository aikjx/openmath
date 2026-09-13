# 强哥德巴赫：二维均方 Dispersion（BGD → DWSC）核验与判定

日期：2026-09-13　　对象：OpenMath 兰道问题 #1（强哥德巴赫，**仍 OPEN**）
上一轮：[01-强哥德巴赫_ζ温度判素体系.md](./01-强哥德巴赫_ζ温度判素体系.md)（USSD 路线）

脚本：`代码/二维均方GoldbachDispersion_验证.py`
产物：`数据/bgd_dispersion_verification.json`

> **本文不证明强哥德巴赫。** 本轮核验换元恒等式、gcd 能量、指数预算，并**首次实测** $C_N(k,h)$
> 的二维均方与局部奇异级数模型。核心结论之一是：**(2) 在可算尺度上被 Poisson 噪声完全掩盖，
> 数值不可达；同时模型 $\mathcal M_N$ 的局部因子是"载荷"的，一处写错就让 (2) 直接失败。**

---

## 0. 判定摘要

| # | 断言 | 判定 | 依据 |
|---|---|---|---|
| F1 | 换元 (5)(6) 是**精确**重写 | **成立（两条独立路径逐位相符）** | $(k,h,m)$ 三循环 vs $(x,t)$ 网格按定义构造 $W_N$，差 $5.8\cdot10^{-10}$（浮点） |
| F2 | gcd 能量 $\sum\gcd^2/(m_1^2m_2^2)\ll(\log M)^{O(1)}/M$ | **成立，且无对数增长** | $M\cdot\Sigma=0.624,0.609,0.603,0.599$（$M=50\!\sim\!400$），常数 $\approx0.6$ |
| F3 | $\|W_N\|_2^2\ll N^2/M$，$M=\sqrt N$ 时 $\|W_N\|_2\ll N^{3/4}$ | **成立**（由 F2） | 且 $\|W_N\|_1\asymp\|W_N\|_2^2\asymp N^2/M$（$|W|\asymp1$，无集中） |
| F4 | 对角项稀释 $(\log N)^2/K\to0$（式(4)） | **成立（渐近）**；可算尺度上仍占 $\approx0.3\sim0.8$ | 实测对角均方 $\approx0.6M^2\log^2N$；稀释率 $=0.6\log^2N/H$，按 $\log^2N/\sqrt N$ 衰减 |
| F5 | $\mathcal M_N$ 取"局部奇异级数"后模型**无偏** | **成立，但极其脆弱** | 修正 $\nu(p)$ 在 $p\mid N$ 处的取值后，实际/模型 $=0.967\pm0.293,\ 1.018\pm0.244$；**修正前偏差 $+21\%/+27\%$** |
| F6 | 式(10)"只需 $N^{-1/4}$ 节省" | **不成立（Cauchy 造成的假象）** | 用 Hölder 端点 $L^1\times L^\infty$：平凡界已是 $N^{3/2}\log^2N$，目标 $o(N^{3/2})$，**真正只需 $\log^{-A}$（$A>2$）** |
| F7 | (2) 可用数值验证 | **不可达** | 每对 $(k,h)$ 的期望事件数仅 $5.2/8.2/13.7$；相对涨落 $0.353/0.274/0.224\asymp\log N/N^{1/4}$，需 $N^{1/4}\gg\log^{A/2+1}$ 才进入 (2) 的体制 |
| F8 | 整条链的余量是幂次的 | **不成立** | 平凡界与目标只差 $\log^2N$；**余量是纯对数的**（见 §4.1） |
| F9 | $\mathcal E_N=o(N^{3/2})$  suffice | **部分成立**：$\mathcal E_N$ 只是 $S$ 的三块之一 | 另两块（模型项、对角项）也落在"平凡界 $=$ 目标"的边界上，需各自处理（§4.2） |

---

## 1. 链条验算（纯不等式部分，全部通过）

- **Cauchy–Schwarz**：$|\mathcal E_N|^2\le\bigl(\sum|\beta_{k+h}\beta_k|^2\bigr)\bigl(\sum|C_N|^2\bigr)$ —— 成立。
- **$\beta$ 的能量**：$|\beta_k|\ll\tau(k)^A\Rightarrow\sum_{h,k}|\beta_{k+h}\beta_k|^2\ll HK(\log N)^{O_A(1)}$ —— 成立（$\sum_k\tau(k)^{4A}\ll K\log^{O(1)}K$）。
- **(2) $\Rightarrow$ (3)**：$|\mathcal E|\ll HKM\log^{-B}$，$HKM\asymp N^{3/2}$ —— 成立。
- **(3) $\Rightarrow f_W*f_W(N)=o(N)$**：由 $|T|^2\le M\cdot S$（对 $m$ 用 Cauchy）得需 $S=o(N^2/M)=o(N^{3/2})$ —— **量纲核对通过**。
- **(4) 对角稀释**：$C_N(k,0)\ll M\log N$，对角 $\ll KM^2\log^2N$，相对目标 $HKM^2$ 的比例为 $\log^2N/H$ —— 成立（需 $H\gg\log^{A+2}N$；$H\asymp\sqrt N$ 足够）。
  - 注意：要得到 $C_N(k,0)\ll M\log N$（而非 $M\log^2N$）**需要 Brun–Titchmarsh**（$\sum_m\Lambda(N-km)\ll \frac{k}{\phi(k)}M$）；完全平凡界给 $M\log^2N$，此时稀释率为 $\log^{A+4}/H$，**仍被 $H\asymp\sqrt N$ 吸收**，故 (4) 稳健。

---

## 2. 换元 (5)(6) 的精确复核（F1）

$N=20000$，$k\in[50,100]$，$m\in[50,100]$，$|h|\le25$，$\beta_k=\tau(k)$：

- 路径 A（$(k,h,m)$ 三循环）：$711922.725419$
- 路径 B（$(x,t)$ 网格上按定义 (6) 逐点构造 $W_N$）：$711922.725419$
- $|A-B|=5.8\cdot10^{-10}$ → **恒等式成立**。

**副产品（奇偶自动性）**：取 $\beta_k=(-1)^k\tau(k)$ 得到**完全相同的值**。原因：$N$ 偶，$x=N-km$ 为奇素数 $\Rightarrow k,m$ 奇；$x-t$ 为奇素数 $\Rightarrow h$ 偶。故全部非零项满足 $(-1)^h=1$，带符号 $\beta$ 不改变结果。这同时说明"不可容许"的奇偶类在奇异级数中自动给出 $\mathfrak S=0$（$\nu(2)=2$），**与主项的局部因子口径自洽**。

---

## 3. 二维均方实测（E3）

设置：$k\in[K,2K]$，$m\in[M,2M]$，$|h|\le H$ 且 $k+h\in[K,2K]$，$4KM<N$（保证 $x=N-km\asymp N$）。
模型取两个线性型 $L_1=N-km,\ L_2=N-(k+h)m$ 的局部奇异级数
$\mathfrak S(k,h)=\prod_p\frac{1-\nu(p)/p}{(1-1/p)^2}$，$\nu(p)=\#\{m\bmod p:L_1L_2\equiv0\}$；
$C_N(k,h)=\sum_{m}\Lambda(L_1)\Lambda(L_2)-(2M+1)\,\mathfrak S(k,h)$。

| $N$ | $K=M$ | $H$ | 均方$/M^2$ | Poisson 预测 | 比 | $\overline{\mathfrak S}$ | 每对事件数 $\mathcal N$ | 相对涨落 | 实际/模型 | 最坏 $|C|/M$ | 对角$/M^2$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $2.5\cdot10^5$ | 200 | 200 | 1.973 | 3.078 | 0.64 | 3.98 | 5.2 | 0.353 | $0.973\pm0.375$ | 5.26 | 90.9 |
| $10^6$ | 400 | 400 | 1.158 | 1.874 | 0.62 | 3.93 | 8.2 | 0.274 | $0.967\pm0.293$ | 4.27 | 110.4 |
| $4\cdot10^6$ | 800 | 350 | 0.791 | 1.144 | 0.69 | 3.96 | 13.7 | 0.224 | $1.018\pm0.244$ | 4.04 | 141.9 |

**三条硬读数**

1. **模型无偏，但极度脆弱。** $\overline{\mathfrak S}\approx3.95$（跨 $N$ 稳定，是真常数）。修正前（把 $p\mid N$ 时的 $\nu(p)$ 误取为 $2$）实际/模型 $=1.21\pm0.39$、$1.27\pm0.34$ —— **系统性正偏 $21\%\sim27\%$**；修正后回到 $0.97\sim1.02$。
   - 根因：$p\nmid k(k+h)$ 时两根 $Nk^{-1},\ N(k+h)^{-1}$ 重合的条件是 $p\mid h$ **或 $p\mid N$**（$L_1-L_2=hm$，且 $p\mid N$ 时两根同为 $m\equiv0$）。漏掉 "$p\mid N$" 会丢失因子 $\frac{p}{p-1}\big/\bigl(1-\frac1{(p-1)^2}\bigr)$，对 $p=5\mid N$ 即 $\times4/3$。
   - **判定（G1）**：(2) 要求逐对相对误差 $\ll\log^{-A/2}$；**一个局部因子的错误就造成 $\asymp30\%$ 的系统偏差，直接让 (2) 失败**。$\mathcal M_N$ 是载荷项，必须逐素数（$p\mid N$、$p\mid k$、$p\mid k+h$、$p\mid h$）写对。
2. **均方服从 Poisson 律，且 (2) 数值不可达。** 事件数 $X\sim{\rm Pois}(\mathcal N)$，$\mathcal N=M\overline{\mathfrak S}/\log^2N$；$C=\log^2N\,(X-\mathcal N)$ ⇒ $\mathbb E[C^2]=M\overline{\mathfrak S}\log^2N$。实测与预测之比稳定在 $0.62\sim0.69$（真实素数对计数的方差低于纯 Poisson，属预期），**标度完全吻合**：$\text{均方}/M^2\asymp\overline{\mathfrak S}\log^2N/M$。
   - 于是**逐对相对涨落** $\asymp\sqrt{\text{均方}}/(M\overline{\mathfrak S})\asymp \log N/N^{1/4}$（实测 $0.353\to0.274\to0.224$，与 $N^{-1/4}\log N$ 的预测比 $0.66$ 对实测 $0.63$ 相符）。
   - **判定（G3）**：(2) 要求相对涨落 $\ll\log^{-A/2}$，即 $N^{1/4}\gg\log^{A/2+1}$ —— 远超任何可算尺度。**本轮能验证的是"模型无偏"，不是"(2) 成立"**；(2) 是纯渐近命题，数值只能证伪不能证实。
3. **对角项确证 (4) 的输入**：对角均方 $\approx0.6\,M^2\log^2N$（即 $C_N(k,0)\asymp0.77\,M\log N$）✓ 与用户估计同量级。

---

## 4. 指数预算的修正与剩余缺口

### 4.1 F6：把 "$N^{-1/4}$" 改成 "$\log^{-A}$"

$|\langle W,\Delta\rangle|$ 的两条平凡路径：

| 路径 | 界 | 相对目标 $N^{3/2}$ |
|---|---|---|
| Cauchy $L^2\times L^2$ | $\|W\|_2\|\Delta\|_2=N^{3/4}\cdot N\log N$ | $N^{1/4}\log N$（$N=10^6$: $437$；$10^{12}$: $2.8\cdot10^4$） |
| **Hölder 端点 $L^1\times L^\infty$** | $\|W\|_1\|\Delta\|_\infty=\frac{N^2}{M}\cdot\log^2N$ | **$\log^2N$**（$N=10^6$: $191$；$10^{12}$: $763$） |

$\|W\|_1\asymp\|W\|_2^2\asymp N^2/M$（$|W_N|\asymp1$，无集中），$\|\Delta\|_\infty\asymp\log^2N$。
**故：真正需要的节省是 $\log^{-A}$（$A>2$），不是 $N^{-1/4}$。** 式(10) 的 $N^{-1/4}$ 恰是 Cauchy 相对 $L^1$ 端点的浪费因子 $N^{1/4}/\log N$（实测 $2.29\to5.43\to36.19$），是用错了 Hölder 端点造成的假象。

这个修正同时 sharpen 了问题的定位：**"在素数相关和中节省任意对数幂"正是 Bombieri–Vinogradov 型命题的形状**（单个 $\Lambda$ 在水平 $1/2$ 上，BV 恰好提供 $\log^{-A}$ 的平均节省）。所以 (2)/DWSC 的准确定位是：

> **水平 $1/2$ 的"两个线性型同时取素数"相关的 BV 型定理**（对模数 $k\asymp\sqrt N$ 与位移 $h$ 做 $L^2$ 平均）。

与单个 $\Lambda$ 的 BV 相比：BV 的证明依赖 **大筛 + Vaughan 恒等式**（$\Lambda$ 有 Type I/II 分解）；而 $\Lambda(L_1)\Lambda(L_2)$ 没有同等的双线性分解 —— **这就是缺口本身**。

### 4.2 F9：$S$ 的三块，都压在同一条边界上

$S=\sum_m\bigl|\sum_k\beta_k\Lambda(N-km)\bigr|^2$ 展开后 = **对角项** $+\underbrace{\sum_{h\ne0,k}\beta_{k+h}\bar\beta_k\,M\mathfrak S(k,h)}_{\text{模型项}}+\ \mathcal E_N$。
原文只处理了 $\mathcal E_N$；另外两块：

- **对角项**：需 Brun–Titchmarsh（见 §1），可得 $\asymp N\log^{O(1)}N\ll N^{3/2}$ ✓（平凡界 $N^{3/2}\log^2$ 不够，必须真用一次上界筛）。
- **模型项**：$\sum_{h,k}\beta_{k+h}\bar\beta_k M\mathfrak S(k,h)$。$\mathfrak S(k,h)$ 含 $\prod_{p\mid h}\frac{p}{p-1}$ 等因子（实测 $\overline{\mathfrak S}\approx3.95$），其平凡界为 $M\cdot HK\cdot\log^{O(1)}\asymp N^{3/2}\log^{O(1)}$ —— **恰好等于目标**。必须证明 $\beta$ 与 $\mathfrak S$ 的相关有 $\log^{-A}$ 抵消（$\mathfrak S$ 可展开为 $\sum_d c_d\mathbf 1_{d\mid h}$ 型，化为对 $\beta$ 的 Type I/II 估计）。**这一块原文未列，属新增缺口（G2）。**

### 4.3 G4：(11) 的谱展开落在哪里

$\mathbf 1_{m\mid u}=\frac1m\sum_{a\bmod m}e(au/m)$ 代入后，$a=b=0$ 项给出主项 $N^2/m^2$ 型密度；其余项产生**模 $m\asymp\sqrt N$ 的素数和** $\sum_x\Lambda(x)e(ax/m)\Lambda(x-t)e(\ldots)$。
即：节省必须来自**模 $\asymp\sqrt N$ 的素数指数和的次弧/双线性估计**，且需要对 $m\sim M$ 与频率 $a$ 双重平均 —— 仍是**水平 $1/2$**。无幂次余量可退。

### 4.4 定位：与 USSD 同深度，但形状对齐得多

- 二者都蕴含强哥德巴赫，都落在"水平 $1/2$ ＋ 对数节省"这一档；
- DWSC 比 USSD 更贴近现成机器（BV／大筛／dispersion／Vaughan 分解），**这是真实的进步**；
- 但它没有降阶：所需输入仍是"素数相关和的对数级节省"，parity 依旧在位（表现为：要在 $\asymp N/\log N$ 尺度上区分"两个线性型同时为素数"与"其中一个是殆素数"）。

---

## 5. 下一步（按信息增益/代价）

1. **先补 G2（模型项）**：把 $\sum_{h,k}\beta_{k+h}\bar\beta_k\mathfrak S(k,h)$ 写成 $\mathfrak S$ 的除数展开，验证它是否可归约为对 $\beta$ 的 Type I/II 估计（若不能，整条链在 $\mathcal E_N$ 之外就已经断裂）。
2. **文献比对（P16 式逐条核对）**：(2) 与"两个线性型的 Bombieri–Vinogradov"相关的已知结果（Mikawa、Perelli–Pintz–Salerno、Drappeau–Topacogullari、Assing–Blomer–Li 的 shift-uniform Titchmarsh）在**模数范围、位移与主尺度同阶、逐 $N$ 量词**三点上是否覆盖。**不要假设"BV 型"就等于"已知"。**
3. **可算尺度的替代实验**：既然 (2) 不可达，改用**可测的替代品**——例如固定 $N$ 后测 $\frac1{HK}\sum|C_N|^2/(M\overline{\mathfrak S}\log^2N)$ 是否稳定（实测 $0.62\sim0.69$）；若该比值随 $N$ 显著漂移，说明 Poisson 模型失效，需重估。
4. **不要做的事**：不要把 (10) 的 $N^{-1/4}$ 当作真实预算（见 F6）；不要只估 $\mathcal E_N$ 而漏掉模型项（G2）。

---

## 6. 文件与复现

```
python openmath/03-难题与猜想/04-兰道问题/代码/二维均方GoldbachDispersion_验证.py
```

输出：`openmath/03-难题与猜想/04-兰道问题/数据/bgd_dispersion_verification.json`
（E1 换元双路径；E2 gcd 能量；E3 三个 $N$ 的均方/模型/Poisson 对照；E4 两条 Hölder 端点）

环境：Python 3.8.8 + NumPy 1.24.3，运行约 40 秒。

---

**一句话结论**：换元 (5)(6) **精确成立**、gcd 能量 (7)(8) **成立**、对角稀释 (4) **渐近成立**；但式 (10) 的 $N^{-1/4}$ 是 Cauchy 的假象（真预算是 $\log^{-A}$），而 (2) 在可算尺度被 **Poisson 噪声**（每对仅 $5\sim14$ 个事件）完全掩盖、数值不可达——本轮真正验证到的是**模型 $\mathcal M_N$ 的无偏性**，并由此暴露出最脆弱的一环：**$p\mid N$ 处 $\nu(p)$ 取错即产生 $30\%$ 系统偏差，足以让 (2) 直接失败**。缺口仍在同一堵墙：**水平 $1/2$ 的素数对相关的对数级节省**。
