# 02-引擎（openmath_sys）

本目录收纳流水线所依赖的**计算引擎** `openmath_sys`，使 openmath 仓库**自包含**：
克隆本仓库后无需依赖仓库外的任何代码即可运行 `01-工作流/` 下的全部脚本。

> 迁移说明：该引擎原先位于仓库外（`my_lib/openmath_sys/`），已整体移入此处，
> 四个流水线脚本中的 `sys.path` 引用已同步更新为本目录路径。

## 模块清单

| 模块 | 职责 | 备注 |
|---|---|---|
| `models.py` | 数据结构（MathExpr / LogicRecord / Authority / ExecutionReport） | |
| `parser.py` | 数学文本词法/语法分析、求值、方程分类与多项式求解 | 支持复数（`cmath` 分派）、反三角/双曲函数 |
| `logic_framework.py` | 四维逻辑框架：D1 句法 / D2 语义 / D3 结构 / D4 计算 | |
| `fetcher.py` | arXiv 检索、OpenMath CD 下载与解析 | 联网失败回退 `sample_data/` |
| `numbertheory.py` | 数论计算：rad / ABC 质量 / 哥德巴赫分拆 / 孪生素数筛 / li(x) / π(x) 渐近 / Collatz 模类 | 见下方范围声明 |
| `numeric.py` | 数值求根（区间扫描+二分）、代数恒等式随机抽样验证 | |
| `scheduler.py` | 算法联盟调度器：权限分级 READ→COMPUTE→TRANSFORM→SUPREME + 安全门 | **SUPREME 仅为内部逻辑授权上限，不映射 OS 提权** |
| `knowledge.py` / `system.py` | 知识库与总编排 | |

## 依赖

**纯 Python 标准库**，零第三方依赖（`requirements.txt` 为空占位），可离线运行。

## 如何被引用

`01-工作流/` 下的脚本通过以下方式引入（以仓库根为基准）：

```python
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src"))
```

## 范围声明（诚实红线）

- 引擎实现的是**可计算的简化版本**，不等于相应的完整数学理论。
  例如 `sieve_theory` 仅实现基础组合筛的两个具体应用，**不是** Selberg 筛/大筛法。
- 所有数值输出为 **L2 计算证据**，**不构成数学证明**；穷举/抽样仅在给定上限内有效。
- `safe=False` 的算法在任何权限层级下均被调度器拒绝。

## 自测

```bash
cd 06-AI自动化/02-引擎/openmath_sys && python demo.py
```
