# 09-数据

> 数学常量、整数序列、反例数据集。**引用外部数据，不复制外部数据库。**

## 一、原则

| 原则 | 说明 |
| --- | --- |
| **引用优先** | OEIS、CODATA、LMFDB 等已有权威来源的，**只存编号 + 本地快照** |
| **可复现** | 任何数值必须能由公式/算法重新生成 |
| **标注来源与日期** | 外部数据会更新（如 CODATA 每四年修订） |
| **高精度** | 常量默认存储 ≥ 50 位有效数字 |

## 二、目录结构

```
09-数据/
├── README.md
├── 常数/            数学与物理常数（高精度）
│   ├── README.md
│   └── constants.yaml
├── 序列/            OEIS 引用桥 + 本地快照
│   ├── README.md
│   └── oeis-refs.yaml
└── 反例数据集/       小规模可穷举对象（供 L5 探针使用）
    ├── README.md
    └── （小图库 / 小群库 / 小矩阵库的生成脚本）
```

## 三、数学常数（`常数/`）

| 类型 | 例子 |
| --- | --- |
| 基础常数 | π, e, γ（Euler–Mascheroni）, φ（黄金比） |
| 数论常数 | Mertens 常数、Artin 常数、孪生素数常数 |
| 特殊函数值 | Γ(1/2), ζ(3)（Apéry 常数）, Catalan 常数 G |
| 物理常数 | 见 [01-数学体系/12-数学物理](../01-数学体系/12-数学物理/README.md)，引用 CODATA |

**存储格式**：

```yaml
- name_zh: 圆周率
  name_en: pi
  symbol: "π"
  value: "3.14159265358979323846...(≥50位)"
  digits: 50
  source: "由 mpmath 生成（Chudnovsky 算法）"
  related: [OM-F-AN-0001]
  oeis: ["A000796"]
```

**重要**：常数的数值**应由脚本生成**，不得手工录入（避免抄错）。

## 四、整数序列（`序列/`）

**政策**：OEIS 有 A 编号的序列，**只存 A 编号 + 前 N 项快照 + 生成公式**，不复制整库。

```yaml
- oeis: "A000040"
  name_zh: 素数序列
  first_terms: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
  generator: "sympy.prime(n)"
  related: [OM-P-NT-0001]
```

**本库自造的序列**（无 A 编号）应提交到 OEIS 后再引用。

## 五、反例数据集（`反例数据集/`）

供 [05-验证中心/06-探针](../05-验证中心/06-探针/README.md) 使用的小规模穷举对象：

| 数据集 | 规模 | 用途 |
| --- | --- | --- |
| 非同构简单图（n ≤ 10） | 约 1.2×10⁷ 个 | 图论猜想的反例搜索 |
| 小阶群（阶 ≤ 2000 的部分） | — | 群论猜想 |
| 小矩阵（小维数、小元素） | — | 线性代数猜想 |
| 小区间整数 | — | 数论猜想扫描 |

**存储策略**：只存**生成脚本**与**索引**，不存全量数据（体积过大）。生成脚本必须确定性（可重现同一枚举顺序）。

## 六、当前状态（诚实）

| 项 | 状态 |
| --- | --- |
| 目录结构 | ✅ |
| 常数表 | ⬜ 未建立（应由脚本生成） |
| 序列桥 | ⬜ 未建立 |
| 反例数据集 | ⬜ 未建立（**反例猎犬组的首要任务**） |

## 七、AI 流水线产物（均已标注 `provenance.ai_assisted=true`）

> 以下文件由 `06-AI自动化/01-工作流/` 下的脚本生成，**全部为 L0/L2 级产物，不构成证明**。

| 文件 | 生成者 | 内容 | 证据等级 |
| --- | --- | --- | --- |
| `math_taxonomy.json` / `math_gaps.json` / `conjectures.json` / `method_system.json` / `numeric_solutions.json` | `openmath_analyze.py` | 理论体系分类、结构缺口、未解猜想登记、方法覆盖 | L0/L2 |
| `nt_experiments.json` | `openmath_experiments.py` | 数论计算实验 | L2 |
| `algorithm_coalition.json` / `breakthrough_roadmap.json` / `possibility_space.json` | `openmath_coalition.py` | 联盟注册表、路线图、可能性空间 | L0/L2 |
| `method_paradigms.json` / `conjecture_verification.json` / `finite_theorems.json` / `extended_dimensions.json` | `openmath_synthesis.py` | 处理范式、未破解验证、有限化定理 | L0/L2 |
| `human_methods_kb.json` / `recursion_analysis.json` / `dimension_matrix.json` / `structure_experiments.json` / `meta_roadmap.json` | `openmath_meta.py` | 处理方法知识库、套娃分析、维度矩阵 | L0/L2 |
| **`theory_forge.json`** | `openmath_theory.py` | 关系发现全量结果：候选、反例台账、被剔除的支配项 | L2 |
| **`theory_candidates.json`** | `openmath_theory.py` | 通过主筛选的候选 + 规模外推存活情况 | L2 |
| **`theory_net.json`** | `openmath_theory.py` | 各对象族不变量的理论体系网（库内独立基与表出） | L2 |

**读取 `theory_*.json` 的注意事项**：其中每条关系的成立范围**仅为被检验的有限对象集合**。
`status` 字段只会出现
`CANDIDATE_UNVERIFIED / FALSIFIED_ON_HELD_OUT / DEGENERATE / DEFINITIONAL /
IMPLIED_BY_DEFINITIONS / CONSEQUENCE_OF_KNOWN / KNOWN_THEOREM_REDISCOVERED / UNDERDETERMINED`
——**不存在**表示已证明的状态值。
