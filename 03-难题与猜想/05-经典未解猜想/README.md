# 05-经典未解猜想

> 除千年难题、Hilbert、Landau 之外的**其余重要未解猜想**，按分支组织。
> 本目录是 [03-难题与猜想](../README.md) 中**条目数量最多**的部分。

## 一、组织方式

按 `01-数学体系/` 的域代码分组。每条给出：陈述摘要、状态、难度感知、可证伪性。

**难度标注说明**（非官方，仅供导航）：

- ⭐ 入门级可理解，但证明可能极难
- ⭐⭐ 需要专业背景
- ⭐⭐⭐ 需要高度专业背景

## 二、数论（`NT`）

| 猜想 | 状态 | 难度 |
| --- | --- | --- |
| **abc 猜想** | `DISPUTED` | ⭐⭐ |
| **奇完美数是否存在** | `OPEN` | ⭐ |
| **Erdős–Straus 猜想**（4/n = 1/x+1/y+1/z） | `OPEN` | ⭐ |
| **Beal 猜想** | `OPEN` | ⭐ |
| **Lehmer 问题**（是否存在复合数 n 使 φ(n) | n−1） | `OPEN` | ⭐ |
| **Sierpinski / Riesel 数** | `OPEN` | ⭐ |
| **Carmichael 数无穷多** | `RESOLVED`（Alford–Granville–Pomerance 1994） | — |
| **ζ(5) 的无理性** | `OPEN` | ⭐⭐ |
| **Sato–Tate 猜想** | `RESOLVED`（BLGHT 2011 等） | — |
| **Andre–Oort 猜想** | 有重要进展（部分情形已解决） | ⭐⭐⭐ |
| **Green–Tao 的推广**（多项式模式的素数） | 有进展 | ⭐⭐⭐ |
| **第 n 个素数的低复杂度精确公式**（[OM-P-NT-0002](OM-P-NT-0002-nth-prime-low-complexity-formula.md)） | `OPEN`（"公式存在性"那一问已 `RESOLVED`：Willans 1964） | ⭐⭐ |
| **强哥德巴赫猜想**（[OM-P-NT-0003](OM-P-NT-0003-goldbach-conjecture.md)） | `PARTIAL`（强二元仍 `OPEN`；Chen 1+2、弱哥德巴赫 Helfgott 2013 已证；本库 L2 至 10⁷） | ⭐⭐⭐ |

**abc 猜想特别说明**（本库 `DISPUTED` 的范本）：

- 提出：Oesterlé 与 Masser（1985）
- 宣称证明：望月新一（Mochizuki），2012 年起发布"宇宙际 Teichmüller 理论"（IUT）系列论文
- 争议：Scholze 与 Stix（2018）指出 IUT 第三篇中的一处推论存在无法修复的缺口；望月一方否认
- 现状：论文已在期刊发表（2020 年代），但**相当一部分数论专家不认为证明成立**
- 本库立场：状态 `DISPUTED`，两条论据并列记录，不做裁决（见 [治理·争议裁决](../../00-宪章/06-治理与决策.md)）

## 三、组合与图论（`CB` / `GT`）

| 猜想 | 状态 | 难度 |
| --- | --- | --- |
| **Ramsey 数精确值**（如 R(5,5)） | `OPEN` | ⭐ |
| **图的重构猜想** | `OPEN` | ⭐ |
| **Erdős–Hajnal 猜想** | `PARTIAL` | ⭐⭐ |
| **Hadwiger–Nelson 问题**（平面染色数） | `PARTIAL` | ⭐ |
| **Hadamard 猜想** | `OPEN` | ⭐ |
| **Erdős–Faber–Lovász 猜想** | `PARTIAL` | ⭐ |
| **完美图猜想** | `RESOLVED`（强完美图定理 2006） | — |
| **四色定理** | `RESOLVED_CA`（形式化 2005） | — |

## 四、几何与拓扑（`TG`）

| 猜想 | 状态 | 难度 |
| --- | --- | --- |
| **四维光滑 Poincaré 猜想** | `OPEN` | ⭐⭐⭐ |
| **Kakeya 猜想（一般维数）** | `PARTIAL` | ⭐⭐⭐ |
| **Novikov 猜想** | `PARTIAL` | ⭐⭐⭐ |
| **Thurston 的 Virtual Haken / Virtual Fibration** | `RESOLVED`（Agol 2012 等） | — |
| **Willmore 猜想** | `RESOLVED`（Marques–Neves 2014） | — |
| **球面双覆盖 / Hopf 猜想** | 部分 | ⭐⭐ |

> ⚠️ 关于 Kakeya 猜想：低维情形在近年有重要宣布性进展，**是否已被完整证明需核对同行评议状态**。本库对未经充分检验的近期宣称一律保留 `fact_check.status: UNVERIFIED`。

## 五、动力系统与混沌（`DS`）

| 猜想 | 状态 |
| --- | --- |
| **Hilbert 第十六问题（极限环个数）** | `OPEN`（即使二次多项式系统的情形） |
| **MLC 猜想（Mandelbrot 集局部连通）** | `OPEN` |
| **遍历性猜想（一般情形）** | `PARTIAL` |
| **Lorenz 吸引子** | `RESOLVED_CA`（Tucker 2002，区间算术严格验证） |
| **Painlevé 猜想（n 体碰撞）** | `PARTIAL` |

## 六、分析（`AN`）

| 猜想 | 状态 |
| --- | --- |
| **Navier–Stokes** | `OPEN`（见千年难题） |
| **谱间隙猜想** | `PARTIAL` |
| **Carleson 问题的推广** | `PARTIAL` |
| **Sendov 猜想** | 有重要进展（近年） |
| **不变子空间问题（Hilbert 空间）** | `OPEN`（Banach 空间情形已被反例否定） |

## 七、代数与表示论（`AL` / `GR`）

| 猜想 | 状态 |
| --- | --- |
| **逆伽罗瓦问题** | `OPEN` |
| **Kazhdan–Lusztig 猜想的推广** | `PARTIAL` |
| **Alperin 权猜想** | `PARTIAL` |
| **McKay 猜想** | 有重要进展（近年有宣称的证明，需核查） |

## 八、理论计算机（`TC`）

| 猜想 | 状态 |
| --- | --- |
| **P vs NP** | `OPEN`（见千年难题） |
| **唯一游戏猜想（UGC）** | `OPEN` |
| **去随机化 BPP = P** | `OPEN` |
| **单向函数存在性** | `OPEN` |
| **L = NL** | `OPEN` |

## 九、数学物理（`MP`）

| 猜想 | 状态 |
| --- | --- |
| **杨–米尔斯质量间隙** | `OPEN`（千年难题） |
| **三维 Ising 模型的严格解** | `OPEN` |
| **四维非平凡 QFT 的严格构造** | `OPEN` |
| **湍流的数学理论** | `OPEN` |
| **Yang–Baxter 相关分类** | `PARTIAL` |

## 十、收录政策

新增条目时必须提供：

1. 精确陈述（含所有量词）
2. 至少一个**权威来源**（教材、综述、或公认的猜想列表）
3. 状态及其依据
4. **可证伪性说明**

**不接受**：仅凭记忆填写、来源为百科类网站的二手信息（除非该来源本身引用了权威文献）。
