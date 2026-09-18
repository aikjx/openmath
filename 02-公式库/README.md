# 02-公式库

> 公式库是 OpenMath 中**密度最高、复用最多**的部分：每一条公式都是一个原子知识单元（AKU），可被定理、算法、纲领、验证脚本直接引用。

## 一、什么是"一条公式"

在本库中，公式（类型码 `F`）包括：

| 类别 | 示例 |
| --- | --- |
| 恒等式 | 欧拉恒等式 e^{iπ} + 1 = 0 |
| 函数方程 | Riemann ζ 函数方程 |
| 不等式 | Cauchy–Schwarz、Jensen |
| 渐近式 | Stirling 公式、素数定理 |
| 展开式 | Taylor、Fourier 级数 |
| 积分表示 | Γ 函数的 Euler 积分 |
| 递推关系 | Catalan 数递推 |
| 闭式解 | 二次方程求根公式 |
| 恒等变换 | Parseval、Plancherel |

**不收录**：纯定义（应归 `OM-D`）、含证明的命题（应归 `OM-T`）、数值算法步骤（应归 `OM-A`）。

## 二、记录格式

每条公式由**成对的两个文件**构成：

```
02-公式库/<域>/OM-F-<域>-<序号>-<slug>.yaml   ← 机器可读（权威）
02-公式库/<域>/OM-F-<域>-<序号>-<slug>.md     ← 人类可读（含推导、直觉、例子）
```

`.md` 文件的 YAML front-matter 中 `id` 必须与文件名一致（`lint` 强制）。

### 必填字段

```yaml
id: OM-F-AN-0002
kind: formula
title_zh: Riemann ζ 函数函数方程
title_en: Functional equation of the Riemann zeta function
domain: AN
msc: ["11M06"]
status: VERIFIED(L3)
evidence_level: L3
latex: "...表达式..."
assumptions: [...]
symbols: [...]
verification:
  levels: {L2: {...}, L3: {...}}
provenance: {ai_assisted: false, ...}
```

完整 schema 见 [`schema/记录schema.md`](schema/记录schema.md)。

## 三、验证要求

**每条公式至少要有一种可执行的验证方式**，否则不得入库。

| 验证方式 | 适用 | 引擎 |
| --- | --- | --- |
| 数值抽样 | 绝大多数 | mpmath（`openmath verify --level L2`） |
| 符号化简 | 恒等式 | SymPy（`--level L3`） |
| 级数/极限检验 | 渐近式与展开 | SymPy + mpmath |
| 特殊值比对 | 特殊函数 | 已知值表 |
| 形式化 | 已形式化的常数与等式 | Lean/Rocq（L4） |

**示例**（Riemann ζ 函数方程）：在 s = 0.5 + 14.1347...i（第一个非平凡零点）处，函数方程两边应同时为零。这是**极强的数值检验**，且天然可证伪。

## 四、目录结构

```
02-公式库/
├── README.md                 本文件
├── schema/                   schema 定义与说明
├── _模板/                     公式模板
├── 索引/                      自动生成的索引（勿手改）
├── 数学基础与逻辑/  (FD)
├── 集合论/          (ST)
├── 范畴论/          (CT)
├── 代数/            (AL GR)
├── 数论/            (NT)
├── 几何与拓扑/      (TG)
├── 分析/            (AN)   ← 现有示例条目
├── 概率与统计/      (PR SC)
├── 组合与图论/      (CB GT)
├── 计算数学/        (NA)
├── 信息论与编码/    (IT)
├── 动力系统/        (DS)
├── 数学物理/        (MP)
├── 博弈与优化/      (GO)
├── 运筹与系统/      (OR)
├── 理论计算机/      (TC)
└── 交叉与新兴/      (XS)
```

目录名与 `01-数学体系/` 的域一一对应（去掉数字前缀），便于交叉定位。

## 五、命名与 slug

slug 使用**英文小写连字符**，选取公式的通用英文名：

| 好 | 坏 | 原因 |
| --- | --- | --- |
| `euler-identity` | `oula-hengdengshi` | 用国际通用名，便于检索 |
| `cauchy-schwarz-inequality` | `不等式-001` | 有意义 |
| `riemann-zeta-functional-equation` | `zeta` | 够具体 |

中文信息放在 `title_zh` 与 `.md` 正文中。

## 六、索引与检索

```bash
python -m openmath index                     # 重建全部索引
python -m openmath index --search "zeta"     # 关键词检索
python -m openmath index --domain NT         # 按域筛选
python -m openmath index --level L4          # 按证据等级筛选
```

生成物写入 `索引/`，**不要手工编辑**（会被覆盖）。

## 七、覆盖现状（诚实）

| 类别 | 数量 | 说明 |
| --- | --- | --- |
| 示例条目（`分析/`） | 2 | 欧拉恒等式、ζ 函数方程——示范格式与验证写法，**不是内容主体** |
| 数论条目（`数论/`） | 16 | F×4、T×8、A×1、D×1、P×2 |
| 难题条目（`03-难题与猜想/`） | 1 | OM-P-NT-0002（第 n 个素数低复杂度公式，开放） |
| **合计** | **19** | `python -m openmath lint` 19/19 L0 通过；`verify --level L2` 19/19 未发现反例 |
| 其中已到 L3（符号） | 2 | OM-F-NT-0003、OM-F-NT-0004 |
| **L4 形式化** | **0** | 本库**没有任何一条**可以说"已证明"（[红线一](../00-宪章/02-诚实红线.md)） |

**域覆盖**：已启用域仅 `NT` 与 `AN` 两个。schema 允许的 20 个域代码中，
其余 18 个（`FD`/`ST`/`CT`/`AL`/`GR`/`TG`/`PR`/`SC`/`CB`/`GT`/`NA`/`IT`/`DS`/`MP`/`GO`/`OR`/`TC`/`XS`）
**无任何条目**。这是本库当前最大的内容缺口。

数论条目的验证脚本有两个（均纯标准库）：

- [`05-验证中心/01-引擎/prime_pi_block.py`](../05-验证中心/01-引擎/prime_pi_block.py)
  （`python prime_pi_block.py --big --json`）——精确素数计数；
- [`05-验证中心/01-引擎/landau_scan.py`](../05-验证中心/01-引擎/landau_scan.py)
  （`python landau_scan.py --json`）——纯标准库，L2：Landau 第三/第四问题扫描；
- [`05-验证中心/01-引擎/landau_symbolic.py`](../05-验证中心/01-引擎/landau_symbolic.py)
  （`python landau_symbolic.py --json`）——sympy，L3：上述两条恒等式的**符号层**验证
  （Euler 积纯符号展开、CRT 构造性核对、完备化恒等式的**命题逻辑证明**、
  Mertens 交叉一致性）。

这两组引擎支撑
[OM-F-NT-0003](数论/OM-F-NT-0003-legendre-window-interval-count.md)、
[OM-F-NT-0004](数论/OM-F-NT-0004-n2plus1-legendre-mobius-sieve.md)、
[OM-P-NT-0003](数论/OM-P-NT-0003-legendre-conjecture.md)、
[OM-P-NT-0004](数论/OM-P-NT-0004-landau-n2plus1-primes.md)。

注意：

- **L2 通过 = 扫描范围内未发现反例**，只能证伪（[红线一](../00-宪章/02-诚实红线.md)）；
- **L3 通过 = 符号层未发现反例**，**仍不是证明**。本库唯一的 candidate-level
  符号证明是 OM-F-NT-0004 的 S4.3（`satisfiable`=False，命题层无反模型），
  但它依赖的前提本身不由本库导出；
- 开放问题条目（`OM-P-*`）的 `passed: true` 只表示"范围内未发现反例"。
