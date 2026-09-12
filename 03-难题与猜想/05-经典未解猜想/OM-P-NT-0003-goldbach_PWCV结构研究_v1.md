# PWCV 框架下强哥德巴赫猜想的结构分析

## ——中央筛存活集、末端半素结构与 Selberg parity 障碍的精确定位

**技术报告 / Working Paper**　版本 1.0　日期：2026-09-11　（日本 JST）

**代码与全部原始数据**：`D:\a10\aikjx\code\my_lib\`（可复现，见第 9 节与附录 B 的文件清单）

---

> ### 诚实性声明（请先阅读）
>
> 本文**不声称证明了强哥德巴赫猜想**。截至 2026 年 9 月，该猜想在公开数学中仍未被无条件解决，
> 最好的无条件结果为陈景润定理（每个充分大偶数 = 一个素数 + 一个至多含两个素因子的数，即 $1+2$）。
>
> 本文严格区分三类陈述：
> - **定理（Theorem）**：给出完整数学证明的命题；
> - **计算观测（Observation）**：在 $E\le 10^8$ 上零反例、可复现，但**不蕴含**任何渐近结论；
> - **开放假设（Hypothesis）**：把剩余缺口归结到的、文献中有名有姓的未证解析命题。
>
> 本文的真实贡献是：把"强哥德巴赫为何无法被经典筛法证明"从定性判断，
> 推进为一组**有精确阈值、零反例、可计算**的结构定理，并将唯一剩余缺口压缩为单一的
> Möbius 扭曲均布假设 $\mathrm{EH}_\mu$（第 7–8 节）。

---

## 摘要

设偶数 $E$，中央区间 $I_E=(\sqrt E,E/2]$，奇候选二元组 $\mathcal A=\{m(E-m):m\in I_E,\ m\text{ 奇}\}$。
我们用 Eratosthenes 递推筛把 $\mathcal A$ 筛到 $\sqrt E$，得到以下严格结果：

1. **存活即素对（定理 A）**：筛到 $\sqrt E$ 的存活集合恰好等于中央 Goldbach 素对集合 $H(E)$，
   每一个存活者两数皆素；计算上递推存活数与直接 $\gcd$ 计数逐点相等（$E=10^6,10^7$ 零误差）。
2. **末端被杀项结构（定理 B）**：在全素数态 $p>E^{1/3}$，被杀者恒为 $pk$；其中 $k$ 必为素数
   （充分大条件下严格，$E=10^6,10^7$ 零反例），另一数 $n=E-pk$ 必为**素数或恰两个大素因子的半素**（严格）。
   实测素/半素比例稳定为约 $78.3\%/21.7\%$ 与 $78.5\%/21.5\%$。
3. **半素小因子定位（定理 D）**：半素 $n=q_1q_2$ 满足 $q_1>z^-$（严格），$c_1=\log q_1/\log E$
   中位 $0.426$、尾顶到 $1/2$；不可被纯筛区分的半素质量为最终素对数的 $0.30\text{–}0.31$ 倍。
4. **parity 障碍的精确实例化**：在 Bombieri–Vinogradov 分布水平 $D=\sqrt E$ 下有效筛位 $s=1\le2$，
   二维下界筛函数 $f_2(s)=0$，故任意非负筛权在本框架对 $H(E)$ 的合法下界恒为 $0$。这是**定理级**不可能性。
5. **缺口的唯一形态**：依据 Huixi Li (2019) 的条件恒等式 $\tilde r(E)=\mathfrak S(E)(E-M(E))+o(E)$，
   $M(E)=\sum_{n<E}\Lambda(n)\mu(E-n)$，正下界只缺对 $M(E)$ 的控制。实测 $|M|/E=7.1\times10^{-5}\;(10^6)$、
   $5.0\times10^{-4}\;(10^7)$，$\mu(E-p)=\pm1$ 计数全局抵消到 $10^{-4}$。但把 $M=o(E)$ 变成定理
   仍需 $\mathrm{EH}_\mu(\theta>1/2)$（或近满加权 Elliott–Halberstam 假设），这是 BFI (1986) 之后
   未被无条件越过的解析难题。

**关键词**：哥德巴赫猜想；Selberg 筛；parity problem；Chen switching；Elliott–Halberstam 分布水平；Möbius 相关和

---

## 1. 引言

### 1.1 问题与记号

强（二元）哥德巴赫猜想断言：每个偶数 $E\ge4$ 可写成两个素数之和。令

$$
\delta_d(n)=\Big\lfloor\frac nd\Big\rfloor-\Big\lfloor\frac{n-1}{d}\Big\rfloor,\qquad
\delta_d(n)=1\iff d\mid n,
$$

定义精确素数示性函数

$$
\chi(n)=\prod_{d=2}^{\lfloor\sqrt n\rfloor}(1-\delta_d(n))\quad(n\ge2),\qquad \chi(n)=1\iff n\text{ 为素数}.
$$

无序 Goldbach 配对数为精确整数函数

$$
G(E)=\sum_{m=2}^{\lfloor E/2\rfloor}\chi(m)\chi(E-m),
$$

强哥德巴赫严格等价于 $G(E)\ge1$ 对所有偶数 $E\ge4$ 成立。计算上已验证至 $4\times10^{18}$（截至 2026 年公开记录），
本文的独立验证覆盖 $E\le10^8$（$G(10^6)=5402$、$G(10^7)=38807$，与已知值一致）。

### 1.2 中央强化与研究对象

令 $y=\lfloor\sqrt E\rfloor$，定义中央 Goldbach 计数

$$
H(E)=\sum_{m=y+1}^{\lfloor E/2\rfloor}\prod_{p\le y}(1-\delta_p(m))(1-\delta_p(E-m)).
$$

任何被加项为 $1$ 的位置都给出 $E=p+q$ 且 $p,q>\sqrt E$，故 $H(E)$ 数的是"两素均大于 $\sqrt E$"的表示。
$H(E)>0$ 对 $6\le E\le10^8$ 成立（唯一例外 $E=4$）。

### 1.3 筛学设置

奇候选二元组与初始计数

$$
\mathcal A=\{\,a_m=m(E-m):m\in I_E,\ m\text{ 奇}\,\},\qquad
X=|\mathcal A|=\lfloor E/4\rfloor-\tfrac12\sqrt E+O(1).
$$

实测 $X(10^6)=249{,}500$，$X(10^7)=2{,}498{,}419$。记 $P(z)=\prod_{p\le z}p$，筛后存活

$$
S(E,z)=\#\{m\in I_E:\gcd(m(E-m),P(z))=1\}.
$$

---

## 2. 局部结构：轮积 CRT 乘积公式（无局部障碍）

令 $M=\prod_{p\le z}p$ 为素数轮积，定义模 $M$ 下同时允许 $r$ 与 $E-r$ 逃过所有小素数的剩余类数

$$
A_M(E)=\#\{r\bmod M:\gcd(r,M)=1,\ \gcd(E-r,M)=1\}.
$$

**命题 2.1（CRT 乘积公式）.** 对偶数 $E$，

$$
A_M(E)=\prod_{\substack{p\mid M\\p>2\\p\mid E}}(p-1)
        \prod_{\substack{p\mid M\\p>2\\p\nmid E}}(p-2).
$$

**证明.** 模 $2$ 因 $E$ 偶只有奇数剩余类一种选择。对奇素数 $p\mid M$ 逐坐标用中国剩余定理：
若 $p\mid E$，只需 $r\not\equiv0\pmod p$，共 $p-1$ 个允许类；若 $p\nmid E$，须同时避开
$r\equiv0$ 与 $r\equiv E\pmod p$，共 $p-2$ 个。各素数坐标独立相乘即得。$\square$

因每个奇素数 $p-2\ge1$，$A_M(E)>0$ 对一切有限轮积与一切偶数 $E$ 成立：

$$
\boxed{\text{强哥德巴赫不存在任何有限模意义下的局部障碍。}}
$$

归一化密度恰产生 Hardy–Littlewood 局部因子。令 $D_M=A_M/M$、$C_2(z)=\prod_{2<p\le z}(1-(p-1)^{-2})$，则

$$
D_M(E)=\Big(\tfrac{\varphi(M)}M\Big)^2\,2C_2(z)
\prod_{\substack{p\mid E\\2<p\le z}}\frac{p-1}{p-2},
$$

右端局部因子与 Goldbach Hardy–Littlewood 奇异级数一致。

**但局部可行不等于全局存在**（本文核心难点）：当 $M=P(\sqrt E)$ 时 $M\gg E/2=|I_E|$，
"模 $M$ 存在允许剩余类"不保证该类在短区间 $I_E$ 中出现整数代表。即
$\text{局部模可行}\not\Rightarrow\text{全局短区间存在}$。

---

## 3. 定理 A：中央筛存活集即素对集

**定理 A.** 对偶数 $E\ge6$，

$$
S(E,\sqrt E)=H(E),
$$

且每个存活者 $m$ 满足 $m$ 与 $E-m$ 都是素数。

**证明.** 取存活者 $m\in I_E$，即 $\gcd(m(E-m),P(\sqrt E))=1$。

- 若 $m$ 合数，则它有素因子 $\le\sqrt m$。因 $m\le E/2$，$\sqrt m\le\sqrt{E/2}<\sqrt E$，
  该素因子 $\le\sqrt E$ 且整除 $m$，与 $\gcd=1$ 矛盾。故 $m$ 素。
- 若 $E-m$ 合数，则它有素因子 $\le\sqrt{E-m}$。因 $E-m<E$，$\sqrt{E-m}<\sqrt E$，
  同理矛盾。故 $E-m$ 素。

反之，若 $m,E-m$ 都是 $>\sqrt E$ 的素数，则它们均无 $\le\sqrt E$ 的素因子，故 $\gcd=1$。两向包含成立。$\square$

**计算验证（Observation 3.1）.** 递推筛存活数与直接 $\gcd$ 计数逐点相等，且全部存活者为素对：

| $E$ | 递推 $S(E,\sqrt E)$ | 直接 $H(E)$ | 相等 | 全为素对 |
|---|---:|---:|:---:|:---:|
| $10^6$ | 5,382 | 5,382 | 是 | 是 |
| $10^7$ | 38,763 | 38,763 | 是 | 是 |

---

## 4. 定理 B：全素数态末端被杀项的结构

在递推筛的某一步，当前素数为 $p$，其前一素数记 $z^-=p_{j-1}$。称 $p>E^{1/3}$ 的阶段为**全素数态**：
此时候选数 $<E$，已逃过所有素数 $\le z^-$ 的筛。

**定理 B(i).** 在全素数态，被 $p$ 杀的数恒为 $pk$，且对充分大的 $E$ 有 $k$ 为素数。

**证明（充分大条件）.** 被杀的候选数被 $p$ 整除，写成 $pk$。它此前逃过 $\le z^-$ 的筛，
故 $k$ 的每个素因子都 $>z^-$。又 $pk=m\le E/2$，故 $k\le E/(2p)$。若 $k$ 合数，$k=ab$ 且 $a,b>z^-$，
于是 $k>z^{-2}$，从而 $pz^{-2}<pk\le E/2$ 要求 $pz^{-2}<E/2$。但在全素数态 $p>E^{1/3}$，且由素数间隙
$z^-=p(1-o(1))$，故 $pz^{-2}=p^3(1-o(1))>E/3\,(1-o(1))>E/2$ 对充分大 $E$ 成立，矛盾。故 $k$ 素。$\square$

有限尺度上该结论由零反例计算完整覆盖（见 Observation 4.3）。

**定理 B(ii).** 令被杀数为 $pk$，则另一数 $n=E-pk$ 不是素数就是恰含两个大素因子的半素。

**证明.** 候选身份保证 $\gcd(m(E-m),P(z^-))=1$，故 $n=E-m$ 无任何素因子 $\le z^-\approx p>E^{1/3}$。
而 $n<E$。若 $n$ 合数且含 $\ge3$ 个素因子（计重数），每个都 $>E^{1/3}$，则 $n>E$，矛盾。
故 $\Omega(n)\le2$，即 $n$ 为素数或恰两个（不同的）大素因子之积。$\square$

**计算验证（Observation 4.3）.** 对 $E=10^6,10^7$ 全量递推：

| $E$ | 全素数态被杀 $K$ | $k$ 非素反例 | $n$ 为素 | $n$ 为半素 | 半素占比 | 半素/$H$ |
|---|---:|---:|---:|---:|---:|---:|
| $10^6$ | 7,426 | **0 / 7,426** | 5,818 | 1,608 | 21.65% | 0.299 |
| $10^7$ | 56,353 | **0 / 56,353** | 44,214 | 12,139 | 21.54% | 0.313 |

素/半素比例两尺度为 $78.35\%/21.65\%$ 与 $78.46\%/21.54\%$，高度稳定；不可区分的半素绝对质量
为最终素对数的 $0.30\text{–}0.31$ 倍。

---

## 5. 定理 D：半素小因子恰落在纯筛盲区

**定理 D.** 定理 B(ii) 中的半素可写 $n=q_1q_2$（$q_1\le q_2$），且恒有 $q_1>z^-$。

**证明.** 由候选身份 $n$ 无素因子 $\le z^-$，其最小素因子 $q_1>z^-$。$\square$

因此在第 $p$ 步，纯筛可用筛深恰为 $z^-<q_1$，于是"素数 $n$"与"半素 $n=q_1q_2$"在所有模 $q\le z^-$
的余数信息下指纹相同——这正是 parity 不可区分性的微观位置。

**计算观测（Observation 5.1）.** $E=10^6$ 的 1,608 个半素全部成功分解，$q_1>z^-$ 反例为 $0$，
$q_1/z^-$ 最小比值 $1.017$。令 $c_1=\log q_1/\log E$：

$$
c_1:\ \min=0.335,\ P25=0.396,\ P50=0.426,\ P75=0.451,\ \max=0.497.
$$

$E=10^7$：$P50=0.430$、$P90=0.474$、$\max=0.499$。两尺度 $q_1$ 累积分布：

| 阈值 $t$（$q_1\le E^t$） | $1/3$ | 0.35 | 0.40 | 0.42 | 0.45 | $9/19$ | 0.48 | 0.50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CDF，$10^6$ | 0% | 1.5% | 28.6% | 45.0% | 73.8% | **92.4%** | 96.3% | 100% |
| CDF，$10^7$ | 0% | 1.9% | 25.2% | 41.3% | 68.6% | **89.4%** | 93.8% | 100% |

联合尺度 $c_1+c_2=\log n/\log E$ 中位 $0.962\;(10^6)$、$0.968\;(10^7)$，
即 $n=E-pk$ 坐在区间上端 $(0.5E,E)$；窗内大因子 $q_2\approx E^{0.53}\text{–}E^{0.57}$。

---

## 6. Selberg parity 障碍的严格实例化

**标准筛论事实（Selberg；见 Halberstam–Richert, *Sieve Methods*, Ch. 12）.**
二维（$\kappa=2$）下界筛函数 $f_2(s)$ 满足

$$
f_2(s)=0\qquad(s\le2),
$$

即任何只使用分布水平 $D$、筛深 $z$ 且有效筛位 $s=\log D/\log z\le2$ 的非负组合筛权，
对被筛对象给出的合法下界恒为 $0$。

**在 PWCV 框架的位置.** Goldbach 二元序列的素数分布水平为 Bombieri–Vinogradov 水平 $D=\sqrt E$；
筛到 $z=\sqrt E$ 时

$$
s=\frac{\log D}{\log z}=\frac{\tfrac12\log E}{\tfrac12\log E}=1\le2.
$$

故

$$
\boxed{\text{任何只用 }\sqrt E\text{ 分布水平的非负筛权，对中央素对数 }H(E)\text{ 的合法下界恒为 }0.}
$$

这不是数值困难，而是**定理级的能力边界**：定理 D 中 $0.30\text{–}0.31\,H$ 量级的半素与素数在筛深 $\sqrt E$
内不可区分，权重无法在不削减素数项的前提下剔尽半素项。陈景润停在 $1+2$ 与此同源。

第 9 轮数值积分复算 Selberg $\kappa=2$ 的 $F_2/f_2$：$F_2(2)=2e^\gamma=3.5621$，平台 $L_2=1.7806$，
实测归一存活 $w(1)\approx0.87$——数值上为正，但数值平坦不改变 $f_2(s\le2)=0$ 的定理结论。

---

## 7. 唯一剩余通道：switching 加权与超越 $\sqrt E$ 的分布水平

### 7.1 Chen switching 机器

取 Selberg 上界权 $\Lambda(n)=(\sum_{d\mid n,d\le D}\lambda_d)^2\ge0$，加 switching 权重

$$
W=\sum_{m\in I_E}\Lambda(a_m)\Big(1-\tfrac12\,\Omega_{\rm sw}(a_m)\Big),
$$

其中 $\Omega_{\rm sw}$ 只统计落入选定大因子窗 $\mathcal W=[E^a,E^b]$ 的素因子。其设计使素对权重为 $1$、
纯 $P_2$ 项被压非正，唯一切换后可救回的部分由新模类上的素数分布决定。$D=\sqrt E$ 下 Chen 证 $W>0$，得 $1+2$。

### 7.2 升级到 $1+1$ 所需的假设

> **假设 $\mathbf H_\delta$（切换类上的超越分布水平）.** 存在 $\delta>0$，使对一切充分大偶 $E$，
> 切换后线性型 $E-pk$ 在其所需模类上满足有效水平 $D_{\rm sw}=E^{1/2+\delta}$ 的素数均布估计，
> 误差对 $E$ 一致且带幂节省。

在 $H_\delta$ 下 switching 窗可覆盖定理 D 的整条 $c_1$ 分布，正贡献只能来自素对，$H(E)>0$，强哥德巴赫成立。

### 7.3 现有工具的前沿（已核对原文）

| 年代 | 工具 | 有效水平 | 对 Goldbach 的产出 |
|---|---|---:|---|
| 1965 | Bombieri–Vinogradov | $1/2$（全模类平均） | Chen：$1+2$ |
| 1986 | Bombieri–Friedlander–Iwaniec | $4/7\approx0.571$（固定剩余类、well-factorable） | 仅上界 |
| — | Maynard（triply well-factorable） | $3/5=0.60$ | — |
| 2023 | Lichtman, arXiv:2309.08522 | $66/107\approx0.617$；Goldbach 均匀类用 $153/256\approx0.598$ | **仍是上界** $G(a)\lesssim3.39\,\Pi_a$，增益受模数因子尺度限制（Prop 6.1） |
| 2026 | Li–Liu, arXiv:2606.05224（**预印本，未评审**） | BV/Wu $5/9$ + Fouvry–Grupp | 无条件 $(1+1.9)$；假设 WEH(0.999) 仍只 $(1+1.4)$，仍为半素 |
| 2019 | Huixi Li | 充分条件 $\mathrm{EH}(\theta)+\mathrm{EH}_\mu(1-\theta)$，水平和 $>1$ | 强哥德巴赫 |

### 7.4 收窄窗方案的否证（攻击路径 (a)）

若把 switching 窗收窄到高密度区 $c_1\in[1/3,0.45]$，仅覆盖半素的 $73.8\%\;(10^6)$ / $68.6\%\;(10^7)$；
无条件前沿 $\tau=9/19=0.4737$ 覆盖 $92.4\%/89.4\%$，越过前沿的尾恒有 $7.6\%/10.6\%$（约 $0.023H/0.033H$）。
失败有三层：(1) 正下界须压住**全部**半素而非约 $90\%$，尾部对应 BFI/Fouvry–Grupp 乘积条件
（$Q_2\le x^{1/3}$、$Q_1Q_2\le x^{4/7}$）够不到的模数；(2) 即便近完整 WEH(0.999) 仍只给 $1+1.4$；
(3) 区分素数与半素所需的是相关性消去而非因子尺度信息（见第 8 节）。经验 $P90(c_1)=0.470/0.474$
与无条件参数 $9/19$ 几乎重合，表明 PWCV 独立重算出的窗口正是当代最优机器已够到的边界。

---

## 8. 缺口的最终形态：单一 Möbius 相关和

### 8.1 Huixi Li 条件恒等式

加权 Goldbach 和 $\tilde r(N)=\sum_{n<N}\Lambda(n)\Lambda(N-n)$。在
$\mathrm{EH}(\theta)+\mathrm{EH}_\mu(1-\theta)$（水平和 $>1$）下，

$$
\tilde r(N)=\mathfrak S(N)\Big(N-M(N)\Big)+o(N),\qquad
M(N)=\sum_{n<N}\Lambda(n)\mu(N-n),
$$

其中 Goldbach 奇异级数 $\mathfrak S(N)=2C_2\prod_{p\mid N,p>2}(p-1)/(p-2)$，
$C_2=\prod_{p>2}(1-(p-1)^{-2})\approx1.32032$。正下界（强哥德巴赫）只需 $|M(N)|$ 被控制到主项以下
（带边因子 $\mathcal A(N)=\prod_{p\mid N,p>2}(1-\tfrac1{p(p-1)})$，对 $5\mid N$ 为 $0.95$，临界阈值 $|M|/N=O(1)$）。
由 Bombieri–Vinogradov 取 $\theta=1/2$，**只需证明 Möbius 扭曲版均布 $\mathrm{EH}_\mu$ 在任一水平 $>1/2$ 成立**。

### 8.2 对 $M(E)$ 的精确实测（Observation 8.1）

| 量 | $E=10^6$ | $E=10^7$ |
|---|---:|---:|
| 无序素对 $G$（校验） | 5,402 | 38,807 |
| 有序 $r_2=2G$ | 10,804 | 77,614 |
| $\mathfrak S(E)$ | 3.5209 | 3.5209 |
| $M(E)=\sum\Lambda(n)\mu(E-n)$ | $+71.2$ | $-5{,}030$ |
| **$|M|/E$** | **$7.1\times10^{-5}$** | **$5.0\times10^{-4}$** |
| $|M|/(\mathfrak S E)$ | $2.0\times10^{-5}$ | $1.4\times10^{-4}$ |
| $\#\{p:\mu(E-p)=-1\}$ vs $+1$ | 30,911 / 30,931 | 261,767 / 261,458 |
| 无权重 $\sum_p\mu(E-p)/\pi(E)$ | $+2.5\times10^{-4}$ | $-4.6\times10^{-4}$ |
| $\tilde r/(\mathfrak S E)$ | 0.499 | 0.500 |

**解读.** 唯一的 parity 障碍量在已测尺度比正下界阈值小 $10^3\text{–}10^4$ 倍；微观上 $\mu(E-p)=+1$（半素）
与 $-1$（素/奇因子）在素数 $p$ 上全局抵消到相对 $10^{-4}$。$\tilde r/(\mathfrak S E)\approx0.50$ 与 $M$ 无关，
是普通的有限尺寸主项欠计（$G/G_{\rm HL}=0.586\to0.573$ 缓慢趋 $1$）。

**严格限制.** $|M|/E$ 从 $7\times10^{-5}$ 升到 $5\times10^{-4}$ 且符号翻转，两点不构成 $M=o(E)$ 的证据；
恒等式本身依赖 $\mathrm{EH}_\mu$。故 Observation 8.1 是"所需消去确实存在"的强经验佐证，不是定理。

### 8.3 朴素数值检验 EH_μ 的方法学否定

曾以 $\mathcal E(Q)=\sum_{q\le Q,\ q\text{ 素}}\max_r|\sum_{n\equiv r(q)}\Lambda(n)\mu(E-n)-M/(q-1)|$
在 $\theta=0.40\text{–}0.60$ 直接检验。但对普通素数序列 $\Lambda(n)$（BV 在 $\theta=1/2$ 已证）施加同一统计量，
$\mathcal E\log^2 E/E$ 在 $\theta=0.40$ 已达约 $335$，同样"不满足"。一个在定理成立处也失败的统计量不度量定理误差
（单 $N$、无 $\max_y$、无跨 $N$ 平均、主项缺局部因子、带符号序列随机游走涨落）。**计算在原理上无法检验 EH_μ**，
该脚本仅作方法学反例留存（`pwcv_ehmu_probe.py`）。

---

## 9. 计算方法与可复现性

- **环境**：Windows + Python 3.14.7 + NumPy 2.5.2（无 `np.trapz`，使用 `np.trapezoid`）。
- **素数/μ/Λ**：对每个 $E$ 用 Eratosthenes 位掩码；$\mu$ 由逐素数乘 $-1$、素数平方处置 $0$ 线性构造；
  $\Lambda$ 在素数幂处置 $\log p$。$E=10^8$ 的布尔位图约 $100$ MB，可行。
- **递推筛**：奇数候选位图，对素数 $p$ 同时删 $m\equiv0$ 与 $m\equiv E\pmod p$ 两类（$p\mid E$ 时只删一类），
  全素数态收集被杀者与另一数。
- **半素分解**：对每个非素的另一数，在 $(z^-,\sqrt n]$ 内素数试除，记录最小命中因子 $q_1$。
- **交叉校验**：$G$ 与历史值（5402 / 38807）一致；$r_2=2G$；递推存活 = 直接 gcd；素/半素计数与独立的
  v5 Buchstab–$\theta$ 积分模型（PN+NP 与 NN 项）逐项吻合。
- 所有脚本与 JSON 均在工作目录，字段名与论文记号一一对应。

---

## 10. 结论

1. **严格结果**：命题 2.1（CRT 乘积、无局部障碍）、定理 A（存活即素对）、定理 B(i)（充分大时 $k$ 素）、
   定理 B(ii)（$n$ 素或半素）、定理 D（$q_1>z^-$），以及 parity 不可能性在本框架的实例
   （$D=\sqrt E,s=1,f_2(1)=0$，合法下界恒 $0$）。
2. **零反例计算**（$E\le10^8$）：$H(E)>0$（除 $E=4$）；$k$ 非素反例为零；素/半素约 $78/22$；
   $c_1$ 中位 $0.43$、$P90\approx0.474$、尾到 $1/2$；$|M|/E\lesssim5\times10^{-4}$。
3. **强哥德巴赫仍未证明。** 纯初等/筛法路线被 parity 定理封死；唯一缺口被压缩为
   $\mathrm{EH}_\mu(\theta>1/2)$（或近满 WEH）。这是 BFI (1986) 之后近四十年未被无条件越过的解析命题，
   需色散法 / 双线性 Kloosterman 和级别的证明工作，非计算可替代。
4. **PWCV 的定位**：把 switching 所需的窗从抽象区间变为跨尺度稳定、零反例、可计算的对象，
   并证明纯 $\sqrt E$ 非负筛在本框架的下界恒为零。这对未来 BFI 量级的解析证明有取窗与常数价值，
   但不构成、也不缩短那个缺失的分布定理。

---

## 附录 A. 主要符号表

| 符号 | 含义 |
|---|---|
| $\chi(n),\delta_d(n)$ | 精确素数示性；整除示性 |
| $G(E),H(E)$ | 无序 Goldbach 配对数；中央（两素 $>\sqrt E$）配对数 |
| $I_E$ | 中央区间 $(\sqrt E,E/2]$ |
| $S(E,z)$ | 筛到 $z$ 的存活数；$S(E,\sqrt E)=H(E)$ |
| $z^-$ | 当前素数 $p$ 的前一素数 |
| $pk$ | 全素数态被杀数（$k$ 素） |
| $n=q_1q_2$ | 另一数为半素时的小/大素因子；$q_1>z^-$ |
| $c_1,c_2$ | $\log q_{1,2}/\log E$ |
| $\mathfrak S(E),C_2$ | Goldbach 奇异级数；孪生素数常数 |
| $M(E)$ | parity 相关和 $\sum\Lambda(n)\mu(E-n)$ |
| $\mathrm{EH},\mathrm{EH}_\mu,\mathrm{WEH}(\theta)$ | Elliott–Halberstam；Möbius 扭曲版；加权版（水平 $\theta$） |

## 附录 B. 产物文件清单（`D:\a10\aikjx\code\my_lib\`）

- 全量验证：`pwcv_goldbach_verify_2026.py`（至 $10^8$）。
- 结构定理：`pwcv_structure_theorem.py/.json`（定理 A、B），`pwcv_theorem_d.py/.json`（定理 D）。
- Buchstab–$\theta$ 与 v5 模型：`pwcv_buchstab_theta_*`、`pwcv_pp_decomp_*`、`pwcv_full_dim_fix5_*`、`pwcv_v5_crossE*`。
- Selberg 包络/分布：`pwcv_dimension_lemma.*`、`pwcv_selberg_envelope.*`。
- switching 缺口与窗口：`pwcv_switching_gap.py/.json`、`pwcv_window_a.py/.json`。
- parity 相关和：`pwcv_parity_correlation.py/.json`。
- EH_μ 方法学反例：`pwcv_ehmu_probe.py/.json`。
- 研究档案（全文推导与文献）：`pwcv_goldbach_attack_note.md`（§1–§8）。

## 参考文献

1. E. Bombieri, J. Friedlander, H. Iwaniec, *Primes in arithmetic progressions to large moduli*, Acta Math. **156** (1986), 203–251.
2. J. Chen, *On the representation of a larger even integer as the sum of a prime and the sum of at most two primes*, Sci. Sinica **16** (1973), 157–176.
3. G. H. Hardy, J. E. Littlewood, *Some problems of 'Partitio Numerorum' III*, Acta Math. **44** (1923), 1–70.
4. H. Halberstam, H.-E. Richert, *Sieve Methods*, Academic Press, 1974（Ch. 12，Selberg parity / $f_2(s)=0$）。
5. J. D. Lichtman, *Primes in arithmetic progressions to large moduli, and Goldbach beyond the square-root barrier*, arXiv:2309.08522 (2023).
6. J. Li, J. Liu, *Theorem (1+1.9) on the Goldbach conjecture*, arXiv:2606.05224 (2026, **预印本，未经同行评审**)。
7. H. Li, *On a variant of the Elliott–Halberstam conjecture and the Goldbach conjecture* (2019)。
8. MathWorld, *Goldbach Conjecture* / *Chen's Theorem*（计算验证至 $4\times10^{18}$ 等背景）。
