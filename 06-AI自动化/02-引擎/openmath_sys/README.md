# OpenMath 综合处理系统

> 一个面向数学对象检索、解析、四维逻辑推理与统一调度的最小可运行系统。
> 纯 Python 标准库实现，零第三方依赖，离线可运行。

---

## 0. 术语澄清（重要）

原始需求中部分术语无标准定义，本系统给出**明确且安全的工程化收敛**：

| 原始表述 | 工程定义 | 边界 |
|---|---|---|
| OpenMath 最优质论文 | 通过 arXiv API 检索数学类论文，按**关键词相关度 + 时效**做启发式排序（近似"优质"，非权威影响因子） | OpenMath 本身是标准/内容字典，并非论文库；论文源采用 arXiv |
| 方程处理方法与逻辑整理 | 解析器 + 知识库（OpenMath CD 语义 + 推理记录） | 覆盖常见代数/超越方程，非穷尽全部数学 |
| 四维逻辑处理框架 | D1 句法 / D2 语义 / D3 结构 / D4 计算 四个正交维度的推理模型 | 框架可扩展，但当前为可运行的最小实现 |
| 算法联盟最高权限处理模式 | 内部**权限分级调度器**（READ→COMPUTE→TRANSFORM→SUPREME），SUPREME 放行所有 `safe=True` 的内部算法 | **绝不映射操作系统提权**；任何破坏性/外部写出的算法 `safe=False`，任意模式均拒绝 |

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                      OpenMathProcessor (总编排)                │
├───────────┬───────────┬────────────────┬──────────────────────┤
│ 模块一    │ 模块二    │ 模块三         │ 模块四                │
│ 论文获取  │ 方程解析  │ 四维逻辑框架   │ 算法联盟调度          │
│ fetcher   │ parser    │ logic_framework│ scheduler             │
└───────────┴───────────┴────────────────┴──────────────────────┘
        │           │            │                    │
        └──────────►┴───────────►┴────────────────────┘
                     KnowledgeBase（符号语义 + 推理记录）
```

### 模块职责
1. **fetcher** — `fetch_arxiv()` 检索并排序论文；`fetch_openmath_cd()`/`parse_ocd()` 加载 OpenMath 内容字典符号语义。网络不可用时回退 `sample_data/`。
2. **parser** — 自包含词法/语法分析器，将文本方程转为 AST，并提供求值、结构分类（线性/二次/超越）、单变量多项式系数提取与求解。
3. **logic_framework** — `FourDimLogicEngine` 对每条表达式产出 D1–D4 四个 `LogicFacet` 与综合 `conclusions`。
4. **scheduler** — `AlgorithmAlliance` 按权限模式分发算法，内置权限门 + 安全门双闸。

---

## 2. 四维逻辑模型

| 维度 | 关注点 | 产出 |
|---|---|---|
| D1 句法 Syntactic | 解析、变量/算子/函数清单、AST 形态 | 结构表层特征 |
| D2 语义 Semantic | 符号→OpenMath CD 映射、类型推断 | 语义链接表 |
| D3 结构 Structural | 方程类别、变量次数、代数形态 | 形态分类 |
| D4 计算 Computational | 样本点求值、方程求解 | 可执行结果 |

四维一致判定：句法可解析 ∧ 语义可链接 ∧ 结构可分类 ∧ 计算可执行（沙箱内）。

---

## 3. 权限调度模型

```
Authority: READ(1) < COMPUTE(2) < TRANSFORM(3) < SUPREME(4)
dispatch(record, mode):
    for algo in registry:
        if algo.required_level > mode: skip        # 权限门
        if not algo.safe:        refused           # 安全门（破坏性/外部写出）
        else:                    execute -> report
```

`SUPREME` 仅放开**内部**逻辑授权；OS 级权限始终为当前用户上下文，不做任何提权尝试。

---

## 4. 运行

```bash
cd openmath_sys
python demo.py
```

产物写入 `openmath_sys/output/`：`papers.json`、`knowledge.json`。

---

## 5. 已知边界与扩展建议

- 论文"优质"为启发式，可接入 zbMATH/引文指标增强排序。
- 方程求解当前支持单变量多项式（线性/二次），可扩展 Gröbner 基、微分方程等。
- 语义层可扩展更多 OpenMath CD（如 `linalg2`、`calculus1`）。
- 调度器可插件化，将算法以 `safe=True` 注册即可纳入联盟。
