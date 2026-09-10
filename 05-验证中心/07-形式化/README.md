# 07-形式化

> **L4 是 OpenMath 中唯一允许使用"已证明"的层级。**
> 本目录管理形式化绑定：把数学条目变成机器可检查的证明。

## 一、支持的系统

| 系统 | 基础 | 库 | 构建命令 | 本库状态 |
| --- | --- | --- | --- | --- |
| **Lean 4** | 依赖类型论（+ 经典公理） | mathlib | `lake build` | ⬜ 待绑定 |
| **Rocq / Coq** | 归纳构造演算 CIC | stdlib / MathComp | `coq_makefile -f _CoqProject && make` | ⬜ 待绑定 |
| **Isabelle** | 简单类型论 | AFP | `isabelle build -D .` | ⬜ 待绑定 |
| **Mizar** | 集合论（TG） | MML | — | 📌 参考 |
| **Metamath** | 集合论 | set.mm | — | 📌 参考 |

**策略**：**不自研定理证明器**，全部委托给成熟系统。本目录只负责：

1. 绑定（哪个条目对应哪个形式化声明）
2. 状态追踪（形式化到什么程度）
3. 可复现构建（锁定版本）

## 二、目录结构

```
07-形式化/
├── README.md              本文件
├── lean4/                 Lean 项目（lake）
│   ├── lakefile.toml
│   ├── lake-manifest.json ← 锁定 mathlib commit
│   ├── OpenMath/
│   │   ├── Formula/
│   │   ├── Theorem/
│   │   └── Programmes/
│   └── _CoqProject 风格的组织（按域分文件）
├── rocq/                  Rocq/Coq 项目
├── isabelle/              Isabelle 项目
└── bindings/              条目 ↔ 形式化声明的映射表
    └── bindings.yaml
```

## 三、绑定表格式

```yaml
bindings:
  - record_id: OM-F-AN-0001
    system: lean4
    declaration: "Complex.exp_pi_mul_I"
    file: "OpenMath/Formula/EulerIdentity.lean"
    status: AVAILABLE_IN_MATHLIB    # 已存在于库中，无需自证
    note: "mathlib 已有该定理，本库只需建立引用"
  - record_id: OM-F-AN-0002
    system: lean4
    declaration: ""
    file: ""
    status: NOT_FORMALIZED
    note: "需先确认 mathlib 中 Riemann zeta 的形式化状态"
```

**状态枚举**：

| 状态 | 含义 |
| --- | --- |
| `AVAILABLE_IN_MATHLIB` | 库里已有，直接引用 |
| `FORMALIZED_BY_US` | 本库已形式化 |
| `PARTIAL` | 部分形式化（如只形式化了陈述） |
| `NOT_FORMALIZED` | 尚未形式化 |
| `INFEASIBLE` | 当前不可行（需说明原因） |
| `DEPENDENT` | 依赖未形式化的前置理论 |

## 四、形式化的优先级策略

**不要从最难的开始。** 建议顺序：

| 优先级 | 类型 | 理由 |
| --- | --- | --- |
| 1 | **库中已有的定理** | 只需建立引用，成本极低 |
| 2 | 陈述简单、证明短的公式 | 快速积累，建立流程 |
| 3 | 经典教科书定理 | 有现成证明可翻译 |
| 4 | 已解决难题的关键引理 | 价值高 |
| 5 | 未解决猜想的形式化**陈述** | 不需证明，但澄清表述 |

**重要洞察**：**形式化一个未解决猜想的"陈述"是有价值的**，即使没证明。它迫使表述精确化，且为未来的证明提供了目标。例如 mathlib 中有 `RiemannHypothesis` 的陈述。

## 五、无 `sorry` 政策

| 构造 | 处理 |
| --- | --- |
| `sorry` / `admit` / `by omega` 失败 | **禁止** |
| `axiom` | 必须在白名单，并记录 |
| 非计算性 `noncomputable` | 允许，需标注 |
| 经典公理（`Classical.choice`、`propext`） | 允许（Lean 默认），需在记录中声明 |

**白名单示例**：排中律、选择公理、商类型、泛函外延性、命题外延性。

**CI 检查**：扫描全部 `.lean` 文件，发现 `sorry` 即失败（除显式标注的 `TODO` 区域）。

## 六、可复现构建

**必须提供**：

- `lake-manifest.json`（Lean）或等价的锁定文件
- 明确指出 mathlib commit
- 提供 `nix` / Docker 或至少"版本 + 构建命令"

```toml
# lakefile.toml 示例
name = "OpenMath"
version = "0.1.0"
[[require]]
name = "mathlib"
# 版本由 lake-manifest.json 锁定，构建前执行 lake update
```

> ⚠️ **禁止使用 `${}` 语法**（本库全局约定，见 [CONTRIBUTING](../../CONTRIBUTING.md)），所有版本号写成字面值。

## 七、自动形式化（Autoformalization）

**现状（诚实）**：叙述数学 → 形式化代码的自动翻译**错误率高**，是活跃研究问题。

**本库政策**：

- AI 生成的 Lean 代码必须**编译通过**才算数（编译是硬门槛）
- 编译通过 ≠ 语义正确（可能形式化了**错误的命题**）→ 需人工核对陈述
- 标记 `provenance.ai_assisted: true`

**关键风险**：AI 可能形式化一个**与原意不同但可证**的命题。这是最危险的失败模式，因为它看起来成功了。

**防范措施**：形式化条目必须有一名人类核对"形式化陈述是否与原始陈述等价"。

## 八、当前状态（诚实）

| 项 | 状态 |
| --- | --- |
| 规范与目录 | ✅ 已建 |
| Lean 项目 | ❌ 未建（下一个里程碑） |
| 绑定表 | ❌ 未建 |
| 首个形式化条目 | ❌ 无 |
| CI 无 `sorry` 检查 | ❌ 未实现 |

**本库自评**：**L4 的完全缺失是验证中心当前最大的能力缺口。** L0–L3 只能筛掉错误，不能确认真理。在 L4 建立之前，本库中**没有任何条目**可以被合法地称为"已证明"。这一点必须在所有对外表述中明确。
