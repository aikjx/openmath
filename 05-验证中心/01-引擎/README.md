# 01-引擎

> 引擎是验证中心的**可替换零件**。新增引擎不需要改核心代码。

## 一、引擎接口规范

每个引擎是一个 Python 模块，实现：

```python
def capabilities() -> dict:
    """声明能力，供运行时派发"""
    return {
        "name": "mpmath-numeric",
        "levels": ["L2"],
        "domains": ["*"],           # 或具体域代码列表
        "dependencies": ["mpmath>=1.3"],
        "deterministic": True,
    }

def available() -> bool:
    """依赖是否满足。False 时运行时标 SKIP"""

def run(record: dict, level: str, options: dict) -> dict:
    """执行验证，返回 Result 对象（见 ../00-验证协议/README.md）"""
```

**约定**：

- `run` 必须**捕获自身异常**并返回 `status: ERROR`（不得抛出）
- 必须填写 `environment`（依赖版本、精度、种子）
- 必须给出**残差值**，而非仅 `True/False`
- 不得修改输入记录

## 二、现有引擎

| 引擎 | 层级 | 依赖 | 状态 | 说明 |
| --- | --- | --- | --- | --- |
| `schema-lint` | L0 | 无 | ✅ | schema + ID + 引用检查 |
| `prime-pi-block` | L2 | 无（纯标准库） | ✅ | 精确素数计数：Legendre φ / Meissel / Lehmer / primorial wheel 交叉验证 + 运算量实测（[`prime_pi_block.py`](prime_pi_block.py)） |
| `wellformedness` | L1 | 无（可选 sympy） | ⚠️ 部分 | 符号表、类型一致 |
| `mpmath-numeric` | L2 | mpmath | ✅ | 50 位高精度数值，输出残差 |
| `sympy-symbolic` | L3 | sympy | ✅ | 化简；未归零时回退 L2 交叉确认 |
| **`prime-pi-block`** | **L2** | **无（仅标准库）** | ✅ | **精确素数计数**：brute / Legendre / Meissel / Lehmer + primorial wheel 四路交叉；自检 6/6 |
| **`pwcv-theorems`** | **L2** | **无（仅标准库）** | ✅ | **PWCV 框架定理**：整除脉冲/素数指示/离散微积分闭环/阶乘互素/首逃逸平方/模6母方程/一般wheel/安全窗口/Jacobsthal 上界；独立筛+SPF 基准，自检 10/10 |
| `dimensional` | L1/L3 | 无 | ⬜ 规划 | 量纲分析（物理条目） |
| `sat-counterexample` | L5 | python-sat | ⬜ 规划 | 命题/有限域反例搜索 |
| `lean4` | L4 | lake + mathlib | ⬜ 规划 | Lean 形式化 |
| `rocq` | L4 | rocq | ⬜ 规划 | Rocq/Coq 形式化 |
| `isabelle` | L4 | isabelle | ⬜ 规划 | Isabelle/AFP |

## 三、引擎注册表

`engines.yaml`（本目录）是**唯一注册点**：

```yaml
engines:
  - name: mpmath-numeric
    module: openmath.engines.mpmath_numeric
    levels: [L2]
    domains: ["*"]
    dependencies: ["mpmath>=1.3"]
    enabled: true
    priority: 10
```

**派发规则**：

1. 筛出支持该 `level` 且覆盖该 `domain` 的引擎
2. 过滤 `enabled: false`
3. 检查 `available()`（依赖缺失 → 跳过）
4. 按 `priority` 降序执行；同层可多引擎并行取**最严格**结果

## 四、新增引擎的步骤

1. 在 `openmath/engines/<name>.py` 实现接口（Python 包位于仓库根）
2. 在 `engines.yaml` 注册
3. 提交两个自检样例：`tests/engines/test_<name>.py`（一个必过、一个必败）
4. 在本文件表格中加一行

**评审要点**：

- 是否诚实报告 `SKIP`（依赖缺失时）
- 是否输出残差而非布尔
- 是否捕获自身异常
- 是否填写环境指纹

## 五、引擎的可信度（重要）

**引擎本身也可能是错的。** 本库的处理方式：

| 措施 | 说明 |
| --- | --- |
| **交叉验证** | 同层多引擎取最严格结果；不一致时标 `DISPUTED` |
| **已知偏差登记** | 每个引擎登记其已知缺陷（如 SymPy 的假设传播） |
| **引擎自检** | 每个引擎必须能通过"已知答案"测试集 |
| **不盲信** | L3 引擎返回 `True` **不构成**证明（[红线一](../../00-宪章/02-诚实红线.md)） |

**引擎缺陷登记表**：

| 引擎 | 已知缺陷 | 影响 |
| --- | --- | --- |
| SymPy `simplify` | 假设传播不完整；分支切割 | 可能假阳性（把错的判成对） |
| 浮点 `float` | 16 位精度不足 | L2 禁用，**必须用 mpmath** |
| SymPy `zeta` | 部分区域依赖假设 | 需显式 `s` 非正整数 |
| 任意符号引擎 | 不是判定器 | 化简失败 ≠ 不成立 |

## 六、资源限制

引擎在沙箱中运行（见 [02-运行时](../02-运行时/README.md)），受：

- 时间限制（默认 L2 60s / L3 120s / L4 600s）
- 内存限制
- 无网络（除显式允许的文献查询）
- 只读文件系统（除结果目录）

**超时的处理**：标 `UNKNOWN` 并记录，不得计为 `PASS`。

## 七、待办

- [ ] 实现 `dimensional` 量纲引擎（物理条目收益极大）
- [ ] 实现 SAT 反例搜索引擎
- [ ] 建立 Lean 4 绑定（优先级最高）
- [ ] 建立引擎自检基准集
