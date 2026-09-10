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

| 状态 | 数量 |
| --- | --- |
| 示例条目 | 2（欧拉恒等式、ζ 函数方程） |
| 数论条目 | 2（[OM-F-NT-0001](数论/OM-F-NT-0001-legendre-phi-recursion.md) Legendre φ 分块递归与轮积恒等式、[OM-A-NT-0001](数论/OM-A-NT-0001-lehmer-prime-counting.md) Meissel–Lehmer 精确计数） |
| 待录入 | 其余全部 |

示例条目的作用是**示范格式与验证写法**，不是内容主体。建议贡献者先阅读 [`分析/OM-F-AN-0002-*.yaml`](分析/OM-F-AN-0002-riemann-zeta-functional-equation.yaml) 作为范本。

数论两条的验证脚本是 [`05-验证中心/01-引擎/prime_pi_block.py`](../05-验证中心/01-引擎/prime_pi_block.py)
（纯标准库，`python prime_pi_block.py --big --json`）。注意它们**只到 L2**：
数值一致只能证伪，不构成证明（[红线一](../00-宪章/02-诚实红线.md)）。
