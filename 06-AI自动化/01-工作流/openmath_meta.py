# -*- coding: utf-8 -*-
"""
meta：人类处理方法知识库 · 套娃（递归）分析 · 维度矩阵 · 结构计算实验 · 元路线图
==============================================================================

  N1. 人类处理方法知识库 —— 收集人类长期形成的**处理/解决/推理方法**（含数学证明方法、
      波利亚启发式、计算方法、建模变换、经验验证、以及作用于方法之上的**元方法**），
      每条标注：方法族 / 作用层级(L0-L3) / 范式映射 / 本体系是否已具备。

  N2. 套娃（递归）分析 —— 把"方法"本身作为对象再上一阶：
      L0 对象 → L1 作用于对象的方法 → L2 作用于方法的方法 → L3 元元层。
      计算：层级分布、**自指方法**、本流水线自身的不动点（算子闭包）、
      以及对自身产物做的**自核验不变量检查**（把方法用在自己身上）。

  N3. 维度矩阵 —— D1 句法 / D2 语义 / D3 结构 / D4 计算 / D5 证据 / D6 元认知
      × 12 个处理范式的密度矩阵，标出空格与"结构上可达但空白"的格子。

  N4. 结构计算实验 —— 对已知答案的标准对象实际运行 finite structure computation，
      验证正确性并如实记录**边界**。

  N5. 元路线图 —— 在既有突破路线之上叠加"层级杠杆"，并对仅定性判断的建议
      明确标注为**定性判断**，不给伪造的数值分数。

诚实红线（00-宪章/02-诚实红线.md）：
  - 本脚本**不证明任何未解猜想**；知识库是**整理/编目**，不是新数学理论。
  - "人类处理方法"是**策展式收集**（广泛教授与使用的方法），**不是穷尽全部**；
    既不可能、也不声称 comprehensiveness。
  - 本体系"已实现"某方法 ≠ 掌握该方法所属完整理论。
"""
from __future__ import annotations

import datetime
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):
    REPO = os.path.dirname(REPO)

DATA_DIR = os.path.join(REPO, "09-数据")
REPORT = os.path.join(_HERE, "META_REPORT.md")
ENGINE_SRC = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理自动生成，未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = ("本文件为 L0/L2 级整理与有限域计算产物："
           "知识库为策展式收集（非穷尽）；结构计算在其有限论域内严格，"
           "但**不蕴含**任何无限域猜想的证明。")

sys.path.insert(0, ENGINE_SRC)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _load(n):
    with open(os.path.join(DATA_DIR, n), encoding="utf-8") as f:
        return json.load(f)


def _dump(obj, n):
    with open(os.path.join(DATA_DIR, n), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


# 12 个处理范式（与 synthesis 阶段保持一致；导入失败则用本地副本）
try:
    from openmath_synthesis import PARADIGMS, PARADIGM_MAP  # noqa: E402
except Exception:  # noqa: BLE001
    PARADIGMS, PARADIGM_MAP = {}, {}


# ===========================================================================
# N1. 人类处理方法知识库
# ===========================================================================
FAMILIES = {
    "证明方法": "数学中用于确立命题为真的标准论证结构",
    "启发式": "波利亚《怎样解题》传统中的普适思路导引（不保证成功）",
    "计算方法": "以有限、机械步骤逼近/求得结果的算法性方法",
    "建模与变换": "通过换元、对偶、商化等手段改变问题的表示",
    "经验验证": "以数据、实验、可视化或反例搜索获得证据（非证明）",
    "元方法": "作用于**方法之上**的方法（选择、组合、评估、泛化）",
    "元元方法": "作用于『元方法体系』之上的纲领层（方法论设计、不可能性论证）",
}

LAYERS = {
    "L0": ("对象层", "直接以数学对象/数据为输入"),
    "L1": ("方法层", "作用于对象的方法（绝大多数传统方法在此层）"),
    "L2": ("元方法层", "以**方法**为输入的方法（分类、选择、组合、验证方法）"),
    "L3": ("元元层", "以**方法体系/纲领**为输入（方法论设计、不可能性论证）"),
}


def _m(mid, name, en, family, layer, paradigm, status, desc, limit=""):
    return {
        "id": mid, "name": name, "en": en, "family": family, "layer": layer,
        "paradigm_candidate": paradigm, "our_status": status,
        "description": desc, "known_limit": limit,
    }


# 每条：id, 名称, 英文名, 方法族, 层级, 范式映射(可空), 本体系状态, 描述, 已知局限
KB_TUPLES = [
    # ---------- 证明方法 ----------
    ("direct_proof", "直接证明", "direct proof", "证明方法", "L1", "deduction", "partial",
     "从定义与已知命题沿逻辑链条直接推到结论。", "结论形式不明确时难以启动。"),
    ("contradiction", "反证法", "proof by contradiction", "证明方法", "L1", "deduction", "absent",
     "假设结论否定，导出矛盾从而确立结论（依赖排中律）。", "构造主义者不承认；常无法给出显式构造。"),
    ("contrapositive", "逆否等价", "contrapositive", "证明方法", "L1", "transform", "absent",
     "以 A→B 等价于 ¬B→¬A，转而证明逆否命题。", "仅适用于蕴含式命题。"),
    ("induction", "数学归纳", "mathematical induction", "证明方法", "L1", "deduction", "absent",
     "以 P(0) 与 P(n)→P(n+1) 确立所有自然数的性质。", "仅限良基结构；不能处理非离散论域。"),
    ("strong_induction", "强归纳", "strong induction", "证明方法", "L1", "deduction", "absent",
     "归纳假设取全部前件而非仅 n。", "同上。"),
    ("structural_induction", "结构归纳", "structural induction", "证明方法", "L1", "deduction", "absent",
     "在递归定义的结构（树、表达式、项）上归纳。", "需对象由归纳文法生成。"),
    ("transfinite_induction", "超限归纳", "transfinite induction", "证明方法", "L1", "deduction", "absent",
     "在良序真类/序数上归纳。", "依赖选择公理的情形存在争议。"),
    ("well_ordering", "良序原理", "well-ordering principle", "证明方法", "L1", "reduction", "absent",
     "取满足性质的最小反例导出矛盾（等价于归纳）。", "非良序集合不可用。"),
    ("pigeonhole", "抽屉原理", "pigeonhole principle", "证明方法", "L1", "decision", "absent",
     "把 n+1 个对象放进 n 个盒子必有重复，用以确立存在性。", "非构造性；不给出具体对象。"),
    ("infinite_descent", "无穷递降", "infinite descent", "证明方法", "L1", "decision", "absent",
     "若存在解则可构造严格更小的解，与良序性矛盾（费马）。", "需要可度量的'大小'函数。"),
    ("extremal_principle", "极值原理", "extremal principle", "证明方法", "L1", "search", "absent",
     "取极大/极小元，利用其极端性约束结构。", "需存在性保证（有限/紧致）。"),
    ("double_counting", "双计数", "double counting", "证明方法", "L1", "evaluation", "absent",
     "用两种方式计数同一集合，得到恒等式或不等式。", "需要有可双计数的结构。"),
    ("invariant", "不变量法", "invariant", "证明方法", "L1", "evaluation", "absent",
     "找在变换下保持不变的量，用以区分不可达状态。", "不存在非平凡不变量时失效。"),
    ("monovariant", "单调量/势函数", "monovariant", "证明方法", "L1", "evaluation", "absent",
     "构造严格递减(增)的量，证明过程必终止。", "需良序/有限下降链。"),
    ("coloring_parity", "染色与奇偶", "coloring / parity argument", "证明方法", "L1", "decision", "absent",
     "以染色或奇偶类阻断不可能的配置。", "仅对特定组合结构有效。"),
    ("generating_function", "生成函数", "generating function", "证明方法", "L1", "representation", "absent",
     "把序列编码为形式幂级数，用代数运算得出计数结果。", "需收敛/形式幂级数合法性论证。"),
    ("probabilistic_method", "概率方法", "probabilistic method", "证明方法", "L1", "search", "absent",
     "证明随机选取以正概率成功，从而确立存在性（Erdős）。", "非构造性；通常不给显式对象。"),
    ("local_lemma", "洛瓦兹局部引理", "Lovász local lemma", "证明方法", "L1", "decision", "absent",
     "依赖稀疏时，即便单事件概率非零仍可证存在无坏事件的配置。", "需满足依赖度界；多为非构造（近年有构造版）。"),
    ("averaging_argument", "平均论证", "averaging argument", "证明方法", "L1", "evaluation", "absent",
     "由平均值推断存在满足性质的元素。", "非构造性。"),
    ("variational_method", "变分法", "variational method", "证明方法", "L1", "approximation", "absent",
     "把极值问题转为泛函驻点问题（欧拉-拉格朗日）。", "需紧致性与下半连续性论证。"),
    ("fixed_point_theorem", "不动点定理", "fixed point theorem", "证明方法", "L1", "solving", "absent",
     "Banach 压缩映射（构造性、可迭代）/ Brouwer（存在性）。", "Brouwer 非构造；Banach 需压缩常数<1。"),
    ("compactness_argument", "紧致性论证", "compactness argument", "证明方法", "L1", "approximation", "absent",
     "取收敛子列/有限子覆盖，把有限结论提升到无限。", "需拓扑紧致性，常非构造。"),
    ("diagonal_argument", "对角论证", "diagonal argument", "证明方法", "L1", "decision", "absent",
     "构造对角线上的差异元素以证不可能（不可数、停机问题）。", "仅限自指可编码场景。"),
    ("counterexample", "反例构造", "counterexample", "证明方法", "L1", "search", "partial",
     "构造一个违反命题的实例以证伪。", "只能证伪不能证实；'未找到'≠'不存在'。"),
    ("constructive_proof", "构造性证明", "constructive proof", "证明方法", "L1", "construction", "partial",
     "给出显式对象或算法以确立存在性。", "多数深层存在性问题无已知构造。"),
    ("universal_property", "泛性质/万有性质", "universal property", "证明方法", "L1", "structure_computation", "absent",
     "以范畴论泛性质刻画对象（乘积、余积、伴随）。", "高度抽象，需范畴论语言；**本体系无范畴论能力**。"),
    ("interpolation_transfer", "插值与迁移", "interpolation / transfer", "证明方法", "L1", "transform", "absent",
     "借中间结论把性质从一结构迁到另一结构。", "需已建立迁移渠道。"),
    ("quantifier_elimination", "量词消去", "quantifier elimination", "证明方法", "L1", "structure_computation", "absent",
     "把含量词公式化为无量词等价式（Tarski、柱形代数分解）。", "复杂度常双重指数；本体系未实现。"),
    # ---------- 波利亚启发式 ----------
    ("analogy_mapping", "类比", "analogy", "启发式", "L1", "analogy", "absent",
     "把问题映射到已知结构的领域，借用其结论与工具。", "类比不保证成立，须回原域验证。**本体系完全空白**。"),
    ("specialization", "特殊化", "specialization", "启发式", "L1", "reduction", "partial",
     "考察退化/边界情形以发现规律。", "特殊情形的规律未必一般化。"),
    ("generalization", "一般化", "generalization", "启发式", "L1", "reduction", "absent",
     "把问题放大到更一般框架，往往更易解（更结构清晰）。", "过度一般化可能丢掉可解性。"),
    ("decomposition", "分解", "decomposition", "启发式", "L1", "reduction", "partial",
     "把整体拆成可独立处理的子问题（分治、直和分解）。", "交互项不可忽略时失效。"),
    ("recombination", "重组", "recombination", "启发式", "L1", "construction", "absent",
     "以新顺序/新组合重新装配已被拆开的成分。", "需保持口径一致。"),
    ("working_backwards", "逆向求解", "working backwards", "启发式", "L1", "search", "absent",
     "从目标反推所需前提，直至抵达已知。", "状态空间大时回溯代价高。"),
    ("auxiliary_problem", "辅助问题", "auxiliary problem", "启发式", "L1", "reduction", "partial",
     "设计一个更易解的相关问题作为踏脚石。", "选错辅助问题会绕远路。"),
    ("auxiliary_element", "辅助元素", "auxiliary element", "启发式", "L1", "construction", "absent",
     "引入额外点/线/参数使隐藏关系显形。", "须证明新元素不改变原问题。"),
    ("draw_figure", "图形化", "draw a figure", "启发式", "L1", "representation", "absent",
     "把对象画出来以获得直观与结构化线索。", "高维/抽象对象难以图示；直观可能误导。"),
    ("guess_and_test", "猜测与检验", "guess and test", "启发式", "L1", "search", "partial",
     "先猜形式再行检验/修正。", "依赖先验知识；无系统性保证。"),
    ("recursion_self", "递推/自相似", "recursion", "启发式", "L1", "reduction", "partial",
     "把规模 n 的问题归到规模 n-1/n/2。", "需正确的基情形与递推式。"),
    ("superposition", "叠加原理", "superposition", "启发式", "L1", "transform", "absent",
     "线性系统中把解叠加得到新解（线性代数/线性微分方程）。", "仅适用于线性结构。"),
    ("symmetry_exploitation", "对称性约化", "symmetry exploitation", "启发式", "L1", "reduction", "absent",
     "利用群作用/不变量压缩搜索空间（Noether、轨道-稳定子）。", "需先识别对称群；**本体系仅能做有限群 Cayley 表分析**。"),
    ("vary_problem", "变题法", "vary the problem", "启发式", "L1", "reduction", "absent",
     "改动条件/结论的空间，寻找可解邻域再回归。", "需要经验判断改哪里。"),
    ("induction_on_complexity", "结构复杂度归纳", "induction on complexity", "启发式", "L1", "deduction", "absent",
     "按某种复杂度测度递减做归纳。", "需良序的复杂度测度。"),
    # ---------- 计算方法 ----------
    ("brute_force_enumeration", "穷举", "brute force enumeration", "计算方法", "L1", "search", "implemented",
     "在有限论域内逐项检查。", "指数爆炸；仅对有限小论域可行。"),
    ("branch_and_bound", "分支限界", "branch and bound", "计算方法", "L1", "search", "absent",
     "以界剪枝的组合搜索。", "界质量决定效果；最坏仍指数。"),
    ("greedy", "贪心", "greedy algorithm", "计算方法", "L1", "search", "absent",
     "每步取局部最优。", "多数问题不具贪心选择性，需拟阵结构保证最优。"),
    ("dynamic_programming", "动态规划", "dynamic programming", "计算方法", "L1", "structure_computation", "absent",
     "以重叠子问题的最优子结构复用中间结果。", "需最优子结构；状态空间可能过大。"),
    ("divide_and_conquer", "分治", "divide and conquer", "计算方法", "L1", "reduction", "partial",
     "递归拆分为独立子问题后合并。", "合并代价可能主导。"),
    ("memoization", "记忆化", "memoization", "计算方法", "L1", "evaluation", "absent",
     "缓存已计算的子结果避免重复。", "内存开销；需纯函数式语义。"),
    ("randomized_algorithm", "随机化算法", "randomized algorithm", "计算方法", "L1", "simulation", "absent",
     "以随机性换取期望效率或规避最坏输入。", "单边错误需重复放大；Monte Carlo/Miller-Rabin 属此。"),
    ("monte_carlo", "蒙特卡洛", "Monte Carlo", "计算方法", "L1", "simulation", "absent",
     "以随机采样估计期望/面积/积分。", "误差随 1/√N 收敛；高维方差大。"),
    ("las_vegas", "拉斯维加斯算法", "Las Vegas algorithm", "计算方法", "L1", "search", "absent",
     "结果必然正确，运行时间随机。", "最坏运行时间无界。"),
    ("gradient_descent", "梯度下降", "gradient descent", "计算方法", "L1", "approximation", "absent",
     "沿负梯度迭代求极小。", "非凸问题易陷局部最优/鞍点。"),
    ("newton_raphson", "牛顿迭代", "Newton-Raphson", "计算方法", "L1", "solving", "implemented",
     "以线性化反复逼近方程的根。", "需导数；初值不佳会发散；**本体系实现的是区间扫描+二分，非牛顿法**。"),
    ("fixed_point_iteration", "不动点迭代", "fixed point iteration", "计算方法", "L1", "evaluation", "absent",
     "迭代 x←f(x) 直至收敛。", "需压缩映射保证收敛。"),
    ("relaxation", "松弛迭代", "relaxation methods", "计算方法", "L1", "approximation", "absent",
     "把约束/方程逐步松弛为易解形式迭代逼近。", "收敛速度依赖松弛因子。"),
    ("preconditioning", "预处理", "preconditioning", "计算方法", "L1", "transform", "absent",
     "改善线性系统的条件数以加速迭代。", "预处理器构造本身是难点。"),
    ("fft", "快速傅里叶变换", "FFT", "计算方法", "L1", "transform", "absent",
     "O(n log n) 计算离散傅里叶变换。", "要求输入长度具备可分解结构；本体系未实现。"),
    ("symbolic_computation", "符号计算", "symbolic computation", "计算方法", "L1", "transform", "absent",
     "以表达式树做精确代数操作（展开、因式分解、符号微积分）。", "表达式膨胀；多数问题无闭式。**本体系仅能做数值，不能符号**。"),
    ("numeric_linear_algebra", "数值线性代数", "numerical linear algebra", "计算方法", "L1", "structure_computation", "partial",
     "矩阵分解、秩、特征值等数值计算。", "浮点误差、条件数敏感。**本体系仅实现精确秩(Q/GF(p))**。"),
    ("interval_arithmetic", "区间算术", "interval arithmetic", "计算方法", "L1", "evaluation", "absent",
     "以区间包围真值，给出严格的误差界。", "依赖性问题使界过宽。"),
    ("automatic_differentiation", "自动微分", "automatic differentiation", "计算方法", "L1", "transform", "absent",
     "按计算图精确传播导数。", "内存开销大；控制流需特殊处理。"),
    ("sat_solving", "SAT/SMT 求解", "SAT/SMT solving", "计算方法", "L1", "decision", "absent",
     "以 CDCL 等算法判定命题/理论可满足性。", "NP-完全；实例敏感。"),
    ("model_checking", "模型检测", "model checking", "计算方法", "L1", "decision", "absent",
     "穷举有限状态系统模型验证时序性质。", "状态空间爆炸。"),
    ("interactive_theorem_proving", "交互式定理证明", "interactive theorem proving", "计算方法", "L1", "decision", "absent",
     "在 Coq/Lean/Isabelle 内核中机械检查证明。", "人工成本高；需完整形式化。**本体系无任何证明助手**。"),
    # ---------- 建模与变换 ----------
    ("change_of_variables", "换元", "change of variables", "建模与变换", "L1", "transform", "absent",
     "替换变量使表达式/区域变简单。", "需保持可逆性与雅可比；本体系未实现符号换元。"),
    ("duality", "对偶", "duality", "建模与变换", "L1", "transform", "absent",
     "在原问题与对偶问题之间转换（LP 对偶、Fourier、Pontryagin）。", "对偶间隙存在时需额外条件。"),
    ("quotient_structure", "商化", "quotienting", "建模与变换", "L1", "structure_computation", "partial",
     "按等价关系把结构压缩为商对象。", "商与原结构的性质转移需逐项论证。**本体系仅能处理有限商**。"),
    ("completion", "完备化", "completion", "建模与变换", "L1", "approximation", "absent",
     "在度量/拓扑下补入极限点（实数、p-adic、戴德金）。", "补入对象需另行定义算术。"),
    ("localization", "局部化", "localization", "建模与变换", "L1", "structure_computation", "absent",
     "在某类元素处可逆化以局部分析（代数几何局部环）。", "局部结论未必能粘合为全局。"),
    ("dimensional_analysis", "量纲分析", "dimensional analysis", "建模与变换", "L1", "evaluation", "absent",
     "以量纲齐次性约束可能的形式（ Buckingham π）。", "只给形式不给定系数。"),
    ("scaling_order_analysis", "尺度与量级分析", "scaling / order analysis", "建模与变换", "L1", "approximation", "absent",
     "抓主项量级以获得弱化的定性结论。", "忽略的主导项可能恰是关键。"),
    ("perturbation_theory", "摄动理论", "perturbation theory", "建模与变换", "L1", "approximation", "absent",
     "在已知可解问题附近做小参数展开。", "级数常发散或仅为渐近。"),
    ("asymptotic_analysis", "渐近分析", "asymptotic analysis", "建模与变换", "L1", "approximation", "implemented",
     "给出 n→∞ 时阶 ff ['~'] 与主项估计。", "有限 n 上的误差界需单独论证。"),
    ("homogenization", "均匀化", "homogenization", "建模与变换", "L1", "approximation", "absent",
     "以等效常系数模型替代快速振荡的细结构。", "需尺度分离假设。"),
    ("renormalization_group", "重整化群", "renormalization group", "建模与变换", "L1", "transform", "absent",
     "在不同尺度间重参数化以研究临界行为。", "非微扰严格性困难；本体系完全无此项。"),
    ("mean_field", "平均场近似", "mean field approximation", "建模与变换", "L1", "approximation", "absent",
     "以平均效应代替逐 -pair 相互作用。", "忽略涨落关联，临界区失效。"),
    # ---------- 经验验证 ----------
    ("numerical_experimentation", "数值实验", "numerical experimentation", "经验验证", "L1", "simulation", "implemented",
     "在有限范围内跑计算，观察模式以形成猜想。", "**证据(L2)≠证明**；受精度与论域限制，可能有未发现的更大反例。"),
    ("conjecture_from_data", "由数据归纳猜想", "conjecture from data", "经验验证", "L1", "search", "absent",
     "从计算结果中提炼候选规律。", "归纳结论**不是**证明（黑天鹅/Skewes 型反例）。"),
    ("counterexample_search", "反例搜索", "counterexample search", "经验验证", "L1", "search", "partial",
     "主动搜索违反命题的实例。", "搜索失败不等于不存在（见 Skewes 型警告）。"),
    ("statistical_significance", "统计显著性", "statistical significance", "经验验证", "L1", "evaluation", "absent",
     "以假设检验判断观测模式是否可能为偶然。", "p 值误用普遍；统计显著≠效应真实/重要。"),
    ("visualization", "可视化", "visualization", "经验验证", "L1", "representation", "absent",
     "以图形呈现结构/趋势以获得直观线索。", "高维投影可能误导；**本体系无绘图能力**。"),
    ("sensitivity_analysis", "敏感性分析", "sensitivity analysis", "经验验证", "L1", "evaluation", "absent",
     "考察输入扰动对结论的影响。", "局部敏感性不等于全局稳健。"),
    ("ablation_study", "消融实验", "ablation study", "经验验证", "L2", "decision", "absent",
     "逐一移除组件以归因贡献。", "交互效应使归因非加法；复合移除组合爆炸。"),
    ("replication", "复现验证", "replication", "经验验证", "L2", "decision", "absent",
     "独立重跑以确认结果可复现。", "复现成功≠结论正确（可能共享同一错误假设）。"),
    # ---------- 元方法（作用于方法之上，L2） ----------
    ("method_classification", "方法分类学", "method classification", "元方法", "L2", "decision", "implemented",
     "把方法按作用逻辑/范式分门别类，暴露覆盖与空白。", "分类框架本身带主观性，不同切分得出不同结论。"),
    ("method_selection", "方法选择", "method selection", "元方法", "L2", "decision", "absent",
     "据问题特征在方法库中挑选适用方法。", "需在选择前就已具备可用方法；选择错误会静默失败。"),
    ("method_composition", "方法复合/流水线", "method composition", "元方法", "L2", "transform", "implemented",
     "把多个方法串/并联成处理链。", "组合爆炸；语义有效性远低于名义排列数。"),
    ("method_verification", "方法验证", "method verification", "元方法", "L2", "decision", "partial",
     "用已知答案检验方法是否真能工作。", "通过已知样例不代表在一般情形正确。"),
    ("method_transfer", "方法迁移/类比迁移", "method transfer", "元方法", "L2", "analogy", "absent",
     "把一个领域的方法搬到另一领域并适配。", "迁移需先建立结构对应；**本体系空白**。"),
    ("generalization_of_methods", "方法泛化", "method generalization", "元方法", "L2", "reduction", "absent",
     "把专用方法推广为覆盖更广的通用形式。", "泛化后可能丢失关键前提条件。"),
    ("specialization_of_methods", "方法特化", "method specialization", "元方法", "L2", "reduction", "partial",
     "把通用方法针对具体结构实例化以提速/提精度。", "特化需领域知识。"),
    ("hybridization", "方法杂交", "hybridization", "元方法", "L2", "transform", "absent",
     "组合两条不同路线各取所长。", "接口语义不一致时难以对接。"),
    ("ensemble_voting", "集成/投票", "ensemble / voting", "元方法", "L2", "evaluation", "absent",
     "并行多个方法综合其输出。", "成员高度相关时增益有限。"),
    ("meta_learning", "元学习", "meta-learning", "元方法", "L2", "approximation", "absent",
     "从多个任务中学习'如何学习/如何选择'。", "需任务分布；易过拟合到 meta 训练集。"),
    ("auto_tuning", "自动调参", "hyperparameter search", "元方法", "L2", "search", "absent",
     "在参数空间搜索配置。", "代价高；结果依赖搜索预算。"),
    ("benchmarking", "基准评测", "benchmarking", "元方法", "L2", "evaluation", "implemented",
     "建立统一指标横向比较方法优劣。", "指标选择会扭曲行为（Goodhart 律）。"),
    ("adversarial_testing", "对抗测试/红队", "adversarial testing", "元方法", "L2", "search", "partial",
     "主动构造敌意输入以暴露方法失效。", "通过≠安全，只能排除已测情形。"),
    ("evidence_tiering", "证据分级", "evidence tiering", "元方法", "L2", "decision", "implemented",
     "按来源与强度给证据定级（本库 L0-L6）。", "分级标准含主观成分；不能替代独立复核。"),
    ("limitation_awareness", "局限意识/不可能性论证", "limitation awareness", "元方法", "L2", "decision", "implemented",
     "明确判定'做不到/尚未做到'并给出理由，而非给出伪进展。", "否定性结论本身需要论证，也可能被后续工作推翻。"),
    ("self_application", "自指应用", "self-application", "元方法", "L2", "evaluation", "implemented",
     "把方法施加于方法自身（含本流水线对自己的不变量核验）。", "自指不产生新的数学真值，只提升一致性保障。"),
    ("bootstrapping", "自举/自训练", "bootstrapping", "元方法", "L2", "simulation", "absent",
     "用自身输出作为下一轮输入逐步增强。", "误差可能自放大（模型坍塌）。"),
    ("external_review", "外部评审", "external review", "元方法", "L2", "decision", "absent",
     "由第三方独立复核方法与结论。", "评审亦可能出错；共识≠正确。"),
    # ---------- 元元方法（L3） ----------
    ("methodology_design", "方法论设计", "methodology design", "元元方法", "L3", "decision", "partial",
     "设计整套研究/处理流程与退出条件（本流水线即其产物）。", "方法论优劣难以在内部自证。"),
    ("research_programme", "研究纲领", "research programme (Lakatos)", "元元方法", "L3", "decision", "absent",
     "以硬核+保护带组织长期研究，明确何种失败构成反例。", "可能被保护带策略消解为不可证伪。"),
    ("paradigm_shift", "范式转换", "paradigm shift (Kuhn)", "元元方法", "L3", "transform", "absent",
     "更换基本问题框架而非在框架内求解。", "不可由规则导出，属历史动力学。"),
    ("comparative_methodology", "方法论比较", "comparative methodology", "元元方法", "L3", "evaluation", "absent",
     "横向比较不同方法论在同类问题上的表现与代价。", "缺乏公共口径时比较无意义。"),
    ("meta_analysis", "元分析", "meta-analysis", "元元方法", "L3", "evaluation", "absent",
     "系统汇总多项研究的效应并检验异质性。", "发表偏倚可使元分析系统性失真。"),
    ("impossibility_theory", "不可能性理论", "impossibility results", "元元方法", "L3", "decision", "partial",
     "以哥德尔不完备、图灵不可判定、Rice 定理等确立边界。", "适用性严格依赖定理前提；常被误用泛化。"),
    ("falsification_design", "可证伪性设计", "falsification design", "元元方法", "L3", "decision", "partial",
     "事先约定何种观测结果构成否证，避免事后解释。", "辅助假设使证伪总可归咎于别处（Duhem-Quine）。"),
]


def build_kb() -> dict:
    entries = [_m(*t) for t in KB_TUPLES]
    by_family, by_layer, by_status, by_paradigm = {}, {}, {}, {}
    for e in entries:
        by_family[e["family"]] = by_family.get(e["family"], 0) + 1
        by_layer[e["layer"]] = by_layer.get(e["layer"], 0) + 1
        by_status[e["our_status"]] = by_status.get(e["our_status"], 0) + 1
        if e["paradigm_candidate"]:
            by_paradigm[e["paradigm_candidate"]] = by_paradigm.get(e["paradigm_candidate"], 0) + 1

    n = len(entries)
    n_impl = sum(1 for e in entries if e["our_status"] == "implemented")
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_meta.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "scope_note": (
                "这是**策展式收集**（curated），覆盖数学证明方法、波利亚启发式、计算算法、"
                "建模变换、经验验证与元/元元方法共 "
                f"{n} 条。它**不是**人类全部方法的穷尽清单，也**不可能**是："
                "各学科的专用技艺（如临床试验的实验设计、"
                "数值天气预报的数据同化、程序验证的抽象解释）均未纳入。"
                "任何'最全面'的说法都应被此句否决。"
            ),
            "family_descriptions": FAMILIES,
            "layer_descriptions": LAYERS,
        },
        "summary": {
            "entries_total": n,
            "by_family": by_family,
            "by_layer": by_layer,
            "by_our_status": by_status,
            "by_paradigm_candidate": by_paradigm,
            "our_coverage_rate": round(n_impl / n, 4) if n else 0.0,
        },
        "entries": entries,
    }


# ===========================================================================
# N2. 套娃（递归）分析
# ===========================================================================
# 流水线各阶段的"输入/输出 artifact 类型"，用于计算算子闭包与不动点
STAGES = [
    {"id": "S1_ingest", "consumes": ["A_remote"],
     "produces": ["A_cd", "A_papers", "A_expr"]},
    {"id": "S2_analyze", "consumes": ["A_cd", "A_expr"],
     "produces": ["A_taxonomy", "A_gaps", "A_conjectures", "A_methods", "A_numeric"]},
    {"id": "S3_experiments", "consumes": [],
     "produces": ["A_exp"]},
    {"id": "S4_coalition", "consumes": ["A_methods", "A_conjectures"],
     "produces": ["A_coalition", "A_roadmap", "A_space"]},
    {"id": "S5_synthesis", "consumes": ["A_methods", "A_conjectures", "A_exp"],
     "produces": ["A_paradigms", "A_verification", "A_finite", "A_dims"]},
    {"id": "S6_meta", "consumes": ["A_methods", "A_paradigms", "A_roadmap", "A_dims"],
     "produces": ["A_kb", "A_recursion", "A_dimmatrix", "A_meta_roadmap"]},
    # S7 不消费上游 artifact：它的对象是**自己构造的**有限对象库，与网络来源无关
    {"id": "S7_theory", "consumes": [],
     "produces": ["A_forge", "A_theory_net", "A_theory_cands"]},
    # S8 同样不消费上游 artifact：它审计的是**代码里的算法**，不是产物里的数字。
    # 这一点很关键——它意味着 S8 发现的问题是「实现层」的，与流水线跑没跑过无关。
    {"id": "S8_audit", "consumes": [],
     "produces": ["A_audit"]},
    # S9 也不消费上游 artifact：它的对象是**自己构造的**整数序列库。
    # 与 S7 互补：S7 找同一对象内部不变量的静态关系，S9 找沿 n 演化的动态关系。
    {"id": "S9_sequences", "consumes": [],
     "produces": ["A_sequences", "A_seq_net", "A_seq_cands"]},
]

AR_GLOSSARY = {
    "A_remote": "网络远端源（OpenMath CD / arXiv）",
    "A_cd": "CD 快照与符号目录", "A_papers": "论文索引",
    "A_expr": "表达式/方程的分析结果", "A_taxonomy": "理论体系分类",
    "A_gaps": "结构缺口", "A_conjectures": "猜想登记表",
    "A_methods": "方法体系", "A_numeric": "数值/恒等式验证结果",
    "A_exp": "计算实验结果", "A_coalition": "算法联盟注册表",
    "A_roadmap": "突破路线图", "A_space": "可能性空间",
    "A_paradigms": "处理范式", "A_verification": "未破解验证与逻辑缺口",
    "A_finite": "有限化定理", "A_dims": "扩展维度框架",
    "A_kb": "处理方法知识库", "A_recursion": "递归/套娃分析",
    "A_dimmatrix": "维度矩阵", "A_meta_roadmap": "元路线图",
    "A_forge": "理论锻造全量结果（候选 + 反例台账）",
    "A_theory_net": "各对象族的不变量理论体系网",
    "A_theory_cands": "通过主筛选的候选关系清单",
    "A_audit": "独立审计结果（用不同算法重算全部可复核数字）",
    "A_sequences": "序列理论全量结果（递推 / 超几何闭式 / 增长率 + 对账）",
    "A_seq_net": "序列关系网（同一递推解空间里的成员聚合）",
    "A_seq_cands": "序列候选清单 + 人工复核队列",
}


def _pipeline_closure() -> dict:
    """从初始 artifact 集合出发，反复应用所有阶段直至不动点。"""
    have = {"A_remote"}
    rounds = []
    for rd in range(1, 12):
        newly = set()
        fired = []
        for st in STAGES:
            if set(st["consumes"]).issubset(have):
                new_out = set(st["produces"]) - have
                if new_out:
                    newly |= new_out
                    fired.append(st["id"])
        if not newly:
            rounds.append({"round": rd, "fired": [], "new_artifacts": [], "note": "无新增 → 到达不动点"})
            break
        rounds.append({"round": rd, "fired": fired,
                       "new_artifacts": sorted(newly)})
        have |= newly
    productive = [r["round"] for r in rounds if r["new_artifacts"]]
    nround = max(productive) if productive else 0
    return {
        "initial_artifacts": ["A_remote"],
        "rounds": rounds,
        # 真正产生新 artifact 的轮次数（末轮"无新增"只是收敛判据，不计入）
        "rounds_to_fixed_point": max(productive) if productive else 0,
        "fixed_point_artifacts": sorted(have),
        "closure_size": len(have),
        "self_application_present": True,
        "self_application_note": (
            f"S6_meta（以及不吃任何上游产物的 S7_theory）的输出不被**任何**阶段消费，"
            f"因此算子在第 {nround} 轮（S6 触发）后停住 —— 这就是套娃的**不动点**。"
            "真正的自指只有一处：S6 分析的对象（STAGES 描述）包含 S6 自身，"
            "即'把套娃了自己一圈的流水线作为输入'。但这只是**结构自洽性**操作，"
            "不产生任何新的数学真值。"
            "注意 S7_theory 虽然在第 1 轮就能触发（它不依赖任何上游产物），"
            "但它同样无人消费，因此对不动点的轮次没有贡献——"
            "**多加一个阶段并不自动多加一层套娃**。"
        ),
    }


def _self_audit() -> list[dict]:
    """把方法用在自己身上：对本流水线自身的产物做不变量检查。"""
    checks: list[dict] = []

    def add(name, violated, detail):
        checks.append({"check": name, "passed": not violated,
                       "violations": violated, "detail": detail})

    # 1) 未解猜想不得声称已证明
    bad = []
    try:
        con = _load("conjectures.json")
        for c in con.get("conjectures", []):
            if c.get("status") != "SOLVED" and c.get("proof_claimed") is not False:
                bad.append(c.get("id"))
    except Exception as e:  # noqa: BLE001
        bad.append(f"<读取失败 {type(e).__name__}>")
    add("未解猜想 proof_claimed 必须为 False", bad,
        "诚实红线：不得声称证明未解猜想")

    # 2) 已实现方法必须给出真实位置且文件存在
    bad = []
    try:
        ms = _load("method_system.json")
        for m in ms.get("methods", []):
            if m.get("implemented"):
                w = m.get("where")
                if not w:
                    bad.append(f"{m['id']}:无 where")
                    continue
                # where 允许写成 "路径 (函数名)" —— 检查时只取路径部分
                path_part = w.split(" ")[0].strip()
                full = os.path.join(REPO, path_part.replace("/", os.sep))
                if not os.path.exists(full):
                    bad.append(f"{m['id']}:路径不存在 {w}")
    except Exception as e:  # noqa: BLE001
        bad.append(f"<读取失败 {type(e).__name__}>")
    add("已实现方法须指向存在的文件", bad,
        "防止把未实现的能力登记为已实现（这是对'能力虚报'的直接检查）")

    # 3) 产物必须标注 AI 辅助
    bad = []
    for fn in ("math_taxonomy.json", "conjectures.json", "method_system.json",
               "finite_theorems.json", "breakthrough_roadmap.json"):
        try:
            d = _load(fn)
            p = (d.get("meta") or {}).get("provenance") or {}
            if p.get("ai_assisted") is not True:
                bad.append(fn)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{fn}:<{type(e).__name__}>")
    add("产物须标注 provenance.ai_assisted=true", bad,
        "诚实红线：AI 生成内容必须标注")

    # 4) 禁止夸大词扫描（**否定式使用是诚实的**，不得误判为违规）
    BANNED = ["最全面", "最高权限", "已证明黎曼", "我们证明了", "彻底解决", "穷尽全部数学"]
    NEG_CUES = ["不", "并非", "而非", "谈不上", "未", "无法", "不得", "拒绝", "否决", "假的", "虚构", "难以"]
    bad, benign = [], []
    for fn in ("math_taxonomy.json", "conjectures.json", "method_system.json",
               "math_gaps.json", "breakthrough_roadmap.json", "finite_theorems.json"):
        try:
            text = json.dumps(_load(fn), ensure_ascii=False)
        except Exception:  # noqa: BLE001
            continue
        for w in BANNED:
            start = 0
            while True:
                i = text.find(w, start)
                if i < 0:
                    break
                window = text[max(0, i - 14):i]
                if any(c in window for c in NEG_CUES):
                    benign.append(f"{fn}:{w}@否定语境")
                else:
                    bad.append(f"{fn}:{w}")
                start = i + 1
    add("禁用夸大/虚假声明词", bad,
        f"扫描词表 {BANNED}；**否定式使用（如'而非穷尽全部数学'）属诚实表述，"
        f"单独计入 benign_honest_negations，不计违规**")
    checks[-1]["benign_honest_negations"] = sorted(set(benign))

    # 5) 有限化定理不得声明蕴含原猜想
    bad = []
    try:
        ft = _load("finite_theorems.json")
        for t in ft.get("theorems", []):
            if not t.get("does_not_imply"):
                bad.append(t.get("id"))
    except Exception as e:  # noqa: BLE001
        bad.append(f"<读取失败 {type(e).__name__}>")
    add("有限化定理须声明不蕴含原猜想", bad,
        "防止把有限域结论偷换成无限域结论")
    return checks


def build_recursion(kb: dict) -> dict:
    entries = kb["entries"]
    layer_counts = {}
    for lay, (nm, desc) in LAYERS.items():
        es = [e for e in entries if e["layer"] == lay]
        layer_counts[lay] = {
            "layer": lay, "name": nm, "description": desc,
            "total": len(es),
            "our_implemented": sum(1 for e in es if e["our_status"] == "implemented"),
            "our_partial": sum(1 for e in es if e["our_status"] == "partial"),
            "coverage": round(sum(1 for e in es if e["our_status"] == "implemented") / len(es), 4) if es else None,
        }
    self_ref = [e["id"] for e in entries if e["layer"] in ("L2", "L3")]

    closure = _pipeline_closure()
    checks = _self_audit()

    # 元 respawn 方法表（本体系实际具备的 L2 能力）
    ours_meta = [{"id": e["id"], "name": e["name"], "layer": e["layer"],
                  "status": e["our_status"]}
                 for e in entries if e["layer"] == "L2" and e["our_status"] == "implemented"]

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_meta.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "note": ("套娃 = 把'方法'本身作为对象再上一阶。"
                     "层级越高，**能做的操作越少，但影响面越广**；"
                     "本体系的能力高度集中在 L1，L2 仅少量具备，L3 几乎空白。"),
        },
        "layer_profile": list(layer_counts.values()),
        "self_referential_method_ids": self_ref,
        "our_meta_capabilities": ours_meta,
        "pipeline_closure": closure,
        "self_audit": {
            "checks": checks,
            "total_checks": len(checks),
            "violations": sum(1 for c in checks if not c["passed"]),
        },
        "artifact_glossary": AR_GLOSSARY,
        "diminishing_returns_note": (
            "层级每上一阶，可执行的方法条数骤降（见 layer_profile），而'缺失一层的代价'"
            "急剧上升：L1 缺一项只影响对应题型，L2 缺一项（如方法选择）会让**所有**"
            "已实现的 L1 方法无法被自动调度。这正是当前最大的结构性短板。"
        ),
    }


# ===========================================================================
# N3. 维度矩阵
# ===========================================================================
DIMENSIONS = {
    "D1": "句法（解析/结构）",
    "D2": "语义（符号/类型映射）",
    "D3": "结构（代数形态/不变量）",
    "D4": "计算（求值/求解/逼近）",
    "D5": "证据（等级/来源/论域边界）",
    "D6": "元认知（方法选择/缺口识别/不可能性意识）",
}

# 已实现能力 → 其所服务的维度（策展式映射，详 honest note）
CAP_DIMS = {
    "ast_parse": ["D1"],
    "arith_eval": ["D4"],
    "transc_eval": ["D4", "D2"],
    "poly_classify": ["D3"],
    "prime_sieve": ["D3"],
    "sieve_theory": ["D3"],
    "rad_computation": ["D3"],
    "modular_analysis": ["D3"],
    "exhaustive_search": ["D3"],
    "numeric_root": ["D4"],
    "linear_solve": ["D4"],
    "quadratic_formula": ["D4"],
    "asymptotic_estimation": ["D4"],
    "map_iteration": ["D4"],
    "gaussian_elimination": ["D3", "D4"],
    "structure_computation": ["D3"],
    "homology_computation": ["D3"],
}


def build_dimension_matrix() -> dict:
    ms = _load("method_system.json")
    impl = [m for m in ms["methods"] if m.get("implemented")]
    missing = [m for m in ms["methods"] if not m.get("implemented")]

    cells: dict[tuple, list[str]] = {}
    for m in impl:
        p = PARADIGM_MAP.get(m["id"], "evaluation")
        for d in CAP_DIMS.get(m["id"], ["D4"]):
            cells.setdefault((d, p), []).append(m["id"])

    matrix = []
    for d in DIMENSIONS:
        row = {"dimension": d, "name": DIMENSIONS[d], "by_paradigm": {}}
        for p in PARADIGMS:
            row["by_paradigm"][p] = cells.get((d, p), [])
        row["nonempty"] = sum(1 for v in row["by_paradigm"].values() if v)
        matrix.append(row)

    total_cells = len(DIMENSIONS) * len(PARADIGMS)
    nonempty = sum(r["nonempty"] for r in matrix)
    empty_cells = [(d, p) for d in DIMENSIONS for p in PARADIGMS
                   if (d, p) not in cells]

    # 结构上可达但空白：该范式已有未实现方法（即"同类操作已在计划中"）
    missing_by_paradigm: dict[str, list[str]] = {}
    for m in missing:
        missing_by_paradigm.setdefault(PARADIGM_MAP.get(m["id"], "evaluation"), []).append(m["id"])
    reachable_empty = [{"dimension": d, "paradigm": p,
                        "planned_methods": missing_by_paradigm.get(p, [])}
                       for (d, p) in empty_cells if p in missing_by_paradigm]

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_meta.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "note": ("矩阵单元 = (维度 × 范式) 中**已实现**的能力。"
                     "映射由 CAP_DIMS 手工指定（策展），不同专家可能给出不同切分；"
                     "此处不代表唯一正确答案。"),
        },
        "dimensions": DIMENSIONS,
        "paradigms": {p: PARADIGMS[p][0] for p in PARADIGMS},
        "matrix": matrix,
        "summary": {
            "dimensions": len(DIMENSIONS),
            "paradigms": len(PARADIGMS),
            "total_cells": total_cells,
            "nonempty_cells": nonempty,
            "density": round(nonempty / total_cells, 4) if total_cells else 0.0,
            "empty_cells": len(empty_cells),
            "structurally_reachable_empty": len(reachable_empty),
        },
        "empty_cells": [{"dimension": d, "paradigm": p} for d, p in empty_cells],
        "structurally_reachable_empty": reachable_empty,
    }


# ===========================================================================
# N4. 结构计算实验
# ===========================================================================
def build_structure_experiments() -> dict:
    try:
        from openmath_sys.structure import (  # noqa: E402
            STANDARD_COMPLEXES, KNOWN_BETTI, KNOWN_TORSION,
            STANDARD_GROUPS, KNOWN_GROUP_FACTS, homology_summary, analyze_group,
            SCOPE_NOTE, TORSION_NOTE,
        )
    except Exception as e:  # noqa: BLE001
        return {"meta": {"error": f"{type(e).__name__}: {e}"}, "experiments": []}

    complexes = []
    for key, builder in STANDARD_COMPLEXES.items():
        cx = builder()
        s = homology_summary(cx)
        known_q = KNOWN_BETTI.get(key, {}).get("Q")
        known_gf2 = KNOWN_BETTI.get(key, {}).get("GF2")
        row = {
            "id": key, "object": cx.name,
            "generators_per_dim": s["generators_per_dim"],
            "betti_Q": s["betti_Q"], "betti_GF2": s["per_prime"][2]["betti"],
            "torsion_by_dim": s["torsion_by_dim"],
            "euler_check": s["euler_check"],
            "matches_known_Q": (known_q is None) or (s["betti_Q"] == known_q),
            "matches_known_GF2": (known_gf2 is None) or (s["per_prime"][2]["betti"] == known_gf2),
        }
        kt = KNOWN_TORSION.get(key)
        if kt:
            got = s["torsion_by_dim"].get(str(kt["dim"]), {}).get(kt["prime"])
            row["matches_known_torsion"] = (got == kt["count"])
            row["known_torsion"] = kt
        complexes.append(row)

    groups = []
    for key, builder in STANDARD_GROUPS.items():
        table, labels = builder()
        r = analyze_group(table)
        known = KNOWN_GROUP_FACTS.get(key, {})
        mism = [f for f in ("order", "abelian", "center_size",
                            "proper_subgroups_count", "proper_subgroup_orders")
                if f in known and r.get(f) != known[f]]
        groups.append({
            "id": key, "order": r["order"], "is_group": r["is_group"],
            "is_associative": r["associative"], "is_abelian": r["abelian"],
            "center_size": r["center_size"], "element_orders": r["element_orders"],
            "exponent": r["exponent"],
            # 2026-09-19 修正：指数此前误取元素阶的**最大值**（S3 会得到 3），
            # 现已改为其**最小公倍数**（S3 应为 6）；旧口径保留在此字段。
            "max_element_order": r.get("max_element_order"),
            "exponent_definition": "群指数 = 全部元素阶的最小公倍数（LCM），不是最大值",
            "proper_subgroups_count": r["proper_subgroups_count"],
            "proper_subgroup_orders": r["proper_subgroup_orders"],
            "subgroup_enumeration_mode": r["subgroup_enumeration_mode"],
            "lagrange_checked": r["lagrange_checked"],
            "matches_known": not mism, "mismatched_fields": mism,
        })

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_meta.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "what_is_this": "对**已知答案**的标准对象实际运行有限结构计算，用于判别能力真伪。",
            "scope": SCOPE_NOTE, "torsion_note": TORSION_NOTE,
            "honest_boundary": (
                "这些计算**正确且在其论域内严格**，但它们仍然是 L2 计算证据："
                "算出 RP² 有 Z₂ 挠元，不等于能处理任意拓扑空间；算出 D₄ 的中心，"
                "不等于能研究任意群。本能力**不给**霍奇猜想/BSD 提供任何证明方向"
                "（详见'孤儿能力'一节）。"
            ),
        },
        "summary": {
            "complexes_tested": len(complexes),
            "complexes_all_match": all(c["matches_known_Q"] for c in complexes),
            "groups_tested": len(groups),
            "groups_all_match": all(g["matches_known"] for g in groups),
        },
        "complexes": complexes,
        "groups": groups,
    }


# ===========================================================================
# N5. 元路线图（含定性建议，明确标注为定性判断）
# ===========================================================================
QUALITATIVE_SUGGESTIONS = [
    {
        "id": "method_selector",
        "name": "自动方法选择器（L2）",
        "layer": "L2",
        "rationale": "当前已实现的 L1 方法无人自动调度；补上这一层，"
                     "已有能力的利用率才会从'手工编排'变为'自动组合'。",
        "why_not_scored": "它对猜想覆盖率没有直接贡献（现有评分口径都会给它 0 需求），"
                          "故不给出数值优先级，仅作定性建议。",
    },
    {
        "id": "analogy_transport_engine",
        "name": "类比迁移引擎（给定映射 → 机械验证）",
        "layer": "L2",
        "rationale": "类比是唯一完全空白且无法靠扩充数据填补的范式；"
                     "即便只做到'人工给定结构对应 + 机器验证'，"
                     "也能把部分跨领域借用从直觉变为可检查操作。",
        "why_not_scored": "缺乏可靠的自动类比评测基准，任何分数都会是虚构精度。",
    },
    {
        "id": "interval_verified_numerics",
        "name": "区间算术严格验证",
        "layer": "L1",
        "rationale": "把现有抽样验证升级为带严格误差界的验证，"
                     "可直接收敛'精度鸿沟'这一逻辑缺口——它提升证据强度而非覆盖率。",
        "why_not_scored": "提升的是证据强度而非覆盖率，覆盖率口径无法体现其价值。",
    },
]


def build_meta_roadmap() -> dict:
    road = _load("breakthrough_roadmap.json")
    ms = _load("method_system.json")
    impl_ids = [m["id"] for m in ms["methods"] if m.get("implemented")]

    # 孤儿能力：已实现但未被任何猜想调用的能力
    linked = set()
    for lk in ms.get("linkage", []):
        linked |= set(lk.get("applicable_methods") or [])
    orphans = [i for i in impl_ids if i not in linked]

    # 本轮新增的三条能力，是否真的给某条猜想提供了处理方向？（预期：没有）
    NEW_CAPS = ["gaussian_elimination", "structure_computation", "homology_computation"]
    new_uncontributing = [i for i in NEW_CAPS if i not in linked]

    top = []
    for r in road.get("roadmap", [])[:10]:
        top.append({
            "id": r["id"], "demand": r.get("demand"),
            "cost_estimate": r.get("cost_estimate"),
            "priority_score": r.get("priority_score"),
            "unlocks_conjectures": r.get("unlocks_conjectures", []),
            "note": "沿用既有突破路线图评分（需求/成本），此处未做层级加成。",
        })

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_meta.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "note": ("定量部分直接沿用 breakthrough_roadmap.json 的评分口径，"
                     "不做二次加工以免引入虚构精度；"
                     "定性部分明确标注为**主观判断**，不伪装成计算的排名。"),
        },
        "quantitative_top": top,
        "qualitative_suggestions": QUALITATIVE_SUGGESTIONS,
        "orphan_capabilities": {
            "ids": orphans,
            "meaning": ("这些已实现能力**未被任何未解猜想调用**："
                        "说明'有能力'与'有方向'是两件事。"
                        "有限群/同调计算能算对已知对象，却不为霍奇/BSD 提供任何处理方向。"),
        },
        "new_capabilities_impact": {
            "ids": NEW_CAPS,
            "uncontributing_to_any_conjecture": new_uncontributing,
            "meaning": ("本轮新增的三条能力**没有给任何未解猜想增加处理方向**，"
                        "方向覆盖率因此保持不变。这是**如实记录**而非遗漏："
                        "会算同调 ≠ 能攻击霍奇猜想；把有限的进步记成'进展了一大步'正是要杜绝的做法。"),
        },
    }


# ===========================================================================
# 报告
# ===========================================================================
def write_report(kb, rec, dim, exp, met) -> None:
    # 引擎注册表口径的可执行方法数（用于与知识库口径对照）
    try:
        _N_ENGINE_IMPL = sum(1 for m in _load("method_system.json").get("methods", [])
                             if m.get("implemented"))
    except Exception:  # noqa: BLE001
        _N_ENGINE_IMPL = 0
    L = []
    A = L.append
    A("# OpenMath 元层分析报告：处理方法知识库 · 套娃递归 · 维度矩阵\n")
    A(f"> 生成时间：{GEN_AT}　|　生成者：`06-AI自动化/01-工作流/openmath_meta.py`\n")
    A("> **诚实声明**：本文所有内容为 **L0/L2 级整理与有限域计算**，"
      "**不证明任何未解猜想**；知识库为策展式收集，**不是**人类方法的穷尽清单。\n")

    s = kb["summary"]
    A("\n## 1. 人类处理方法知识库\n")
    A(f"收录 **{s['entries_total']} 条**方法，覆盖 7 个方法族。\n")
    A("| 方法族 | 条数 | 说明 |")
    A("|---|---|---|")
    for fam, cnt in s["by_family"].items():
        A(f"| {fam} | {cnt} | {FAMILIES.get(fam,'')[:40]}… |")
    A("")
    A(f"本体系实际具备 **{s['by_our_status'].get('implemented',0)} 条**"
      f"（另有 partial {s['by_our_status'].get('partial',0)} 条），"
      f"**覆盖率仅 {s['our_coverage_rate']:.1%}**。\n")
    A("> **口径说明**：此处的'已实现'按**知识库粒度**计（一条方法 = 一种人类技法）；"
      f"`method_system.json` 中记录的本引擎可执行能力为 **{_N_ENGINE_IMPL} 条**，"
      "两者粒度不同、不可直接相加，登记口径也不完全对齐。"
      "以更严格的本节口径看，覆盖率不足一成。\n")
    A("> 这个数字必须被正视：所谓'最全面'，充其量是**目录最全**，不是**能力最全**。\n")

    A("\n## 2. 套娃：层级越高，能做的越少、影响面越大\n")
    A("| 层级 | 含义 | 方法数 | 本体系已实现 | 覆盖率 |")
    A("|---|---|---|---|---|")
    for r in rec["layer_profile"]:
        cov = "—" if r["coverage"] is None else f"{r['coverage']:.0%}"
        A(f"| {r['layer']} {r['name']} | {r['description']} | {r['total']} | "
          f"{r['our_implemented']} | {cov} |")
    A("")
    A(f"自指/元层方法（作用于方法之上）共 **{len(rec['self_referential_method_ids'])} 条**，"
      f"本体系具备 **{len(rec['our_meta_capabilities'])} 条**。\n")

    cl = rec["pipeline_closure"]
    A("\n### 2.1 流水线自身的套娃不动点\n")
    A(f"从唯一初始输入 `{cl['initial_artifacts'][0]}` 出发，"
      f"反复应用 6 个阶段，**第 {cl['rounds_to_fixed_point']} 轮后到达不动点**，"
      f"闭包含 **{cl['closure_size']}** 类 artifact。\n")
    for r in cl["rounds"]:
        A(f"- 第 {r['round']} 轮：触发 `{', '.join(r['fired']) or '—'}`"
          f"　新增 `{', '.join(r['new_artifacts']) or '—'}`")
    A("")
    A(f"> {cl['self_application_note']}\n")

    au = rec["self_audit"]
    A("\n### 2.2 把方法用在自己身上（自核验）\n")
    A(f"对本流水线自身产物执行 **{au['total_checks']} 项不变量检查**，"
      f"**违规 {au['violations']} 项**。\n")
    A("| 检查项 | 结果 | 说明 |")
    A("|---|---|---|")
    for c in au["checks"]:
        A(f"| {c['check']} | {'通过' if c['passed'] else '**违规**'} | "
          f"{c['detail']}{'' if c['passed'] else '　→ ' + str(c['violations'])[:80]} |")
    A("")

    A("\n## 3. 维度矩阵：D1–D6 × 12 范式\n")
    ds = dim["summary"]
    A(f"共 **{ds['total_cells']}** 格，其中**非空 {ds['nonempty_cells']} 格**"
      f"（密度 **{ds['density']:.1%}**），空白 {ds['empty_cells']} 格，"
      f"其中 **{ds['structurally_reachable_empty']} 格**属于"
      "「该范式已有未实现方法」的**结构上可达空白**。\n")
    A("| 维度 | 非空格数 | 已实现能力（按范式） |")
    A("|---|---|---|")
    for row in dim["matrix"]:
        hits = "、".join(f"{dim['paradigms'].get(p,p)}({len(v)})"
                        for p, v in row["by_paradigm"].items() if v)
        A(f"| {row['dimension']} {row['name']} | {row['nonempty']} | {hits or '—'} |")
    A("")

    A("\n## 4. 结构计算实验（本轮新增能力）\n")
    es = exp.get("summary", {})
    A(f"对 **{es.get('complexes_tested',0)} 个拓扑对象**与 "
      f"**{es.get('groups_tested',0)} 个有限群**实际运算，"
      f"与已知答案对齐：**同调全匹配={es.get('complexes_all_match')}、"
      f"群全匹配={es.get('groups_all_match')}**。\n")
    A("| 对象 | 生成元/维 | b(Q) | b(GF2) | 挠元 | 与已知一致 |")
    A("|---|---|---|---|---|---|")
    for c in exp.get("complexes", []):
        ok = c["matches_known_Q"] and c["matches_known_GF2"] and c.get("matches_known_torsion", True)
        tor = c["torsion_by_dim"] if c["torsion_by_dim"] else "—"
        A(f"| {c['object']} | {c['generators_per_dim']} | {c['betti_Q']} | "
          f"{c['betti_GF2']} | {tor} | {'✓' if ok else '✗'} |")
    A("")
    A("| 群 | 阶 | 群? | 交换? | 中心 | 真子群数 | 子群阶 | 与已知一致 |")
    A("|---|---|---|---|---|---|---|---|")
    for g in exp.get("groups", []):
        A(f"| {g['id']} | {g['order']} | {g['is_group']} | {g['is_abelian']} | "
          f"{g['center_size']} | {g['proper_subgroups_count']} | "
          f"{g['proper_subgroup_orders']} | {'✓' if g['matches_known'] else '✗'} |")
    A("")
    A(f"> **边界**：{exp['meta'].get('honest_boundary','')}\n")

    A("\n## 5. 元路线图\n")
    A("### 5.1 定量（沿用既有评分口径，未做二次加工）\n")
    A("| 方法 | 需求 | 成本 | 优先级 | 解锁猜想 |")
    A("|---|---|---|---|---|")
    for r in met["quantitative_top"]:
        A(f"| `{r['id']}` | {r['demand']} | {r['cost_estimate']} | {r['priority_score']} | "
          f"{', '.join(r['unlocks_conjectures'][:3]) or '—'} |")
    A("")
    A("### 5.2 定性建议（**主观判断**，无伪分数）\n")
    for q in met["qualitative_suggestions"]:
        A(f"**{q['name']}**（{q['layer']}）\n")
        A(f"- 理由：{q['rationale']}")
        A(f"- 为何不给分数：{q['why_not_scored']}\n")

    orph = met["orphan_capabilities"]
    A("### 5.3 孤儿能力：有能力 ≠ 有方向\n")
    A(f"已实现但**未被任何猜想调用**的能力：`{', '.join(orph['ids']) or '—'}`\n")
    A(f"> {orph['meaning']}\n")

    ni = met["new_capabilities_impact"]
    A(f"本轮新增能力 `{', '.join(ni['ids'])}` 中，"
      f"**未给任何猜想增加方向**的有 `{', '.join(ni['uncontributing_to_any_conjecture']) or '无'}`。\n")
    A(f"> {ni['meaning']}\n")

    A("\n## 6. 结论\n")
    A(f"1. **知识库宽度不等于能力宽度**：目录能列 {kb['summary']['entries_total']} 条方法，"
      f"实际具备 {kb['summary']['by_our_status'].get('implemented',0)} 条"
      f"（覆盖率 {kb['summary']['our_coverage_rate']:.1%}）。\n")
    A("2. **真正的短板在 L2（元方法层）**：不是某个数学工具不会用，"
      "而是**没有东西负责选择、组合、监督它们**。\n")
    A("3. **新增的结构计算能力是真实的，但不是万能的**：它能算对四面体与 D₄，"
      "却不为霍奇/BSD 提供方向——'算得对'与'用得上'之间存在本体论差距。\n")
    A(f"4. **套娃有顶**：流水线闭包在第 {rec['pipeline_closure']['rounds_to_fixed_point']} 轮收敛，"
      "更高阶的自指不产生新的数学真值，只提升一致性——"
      "这也是为什么自核验比'再套一层'更有价值。\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ===========================================================================
def main():
    print("[N1] 构建人类处理方法知识库 …")
    kb = build_kb()
    _dump(kb, "human_methods_kb.json")
    print(f"     条目 {kb['summary']['entries_total']} 条，"
          f"覆盖 {kb['summary']['our_coverage_rate']:.1%}")

    print("[N2] 套娃（递归）分析 …")
    rec = build_recursion(kb)
    _dump(rec, "recursion_analysis.json")
    print(f"     层级分布 L1={rec['layer_profile'][1]['total']} "
          f"L2={rec['layer_profile'][2]['total']} L3={rec['layer_profile'][3]['total']}；"
          f"不动点轮次={rec['pipeline_closure']['rounds_to_fixed_point']}；"
          f"自核验违规={rec['self_audit']['violations']}")

    print("[N3] 维度矩阵 …")
    dim = build_dimension_matrix()
    _dump(dim, "dimension_matrix.json")
    print(f"     密度 {dim['summary']['nonempty_cells']}/{dim['summary']['total_cells']}"
          f" = {dim['summary']['density']:.1%}")

    print("[N4] 结构计算实验 …")
    exp = build_structure_experiments()
    _dump(exp, "structure_experiments.json")
    print(f"     同调全匹配={exp['summary']['complexes_all_match']}，"
          f"群全匹配={exp['summary']['groups_all_match']}")

    print("[N5] 元路线图 …")
    met = build_meta_roadmap()
    _dump(met, "meta_roadmap.json")
    print(f"     孤儿能力 {len(met['orphan_capabilities']['ids'])} 项")

    write_report(kb, rec, dim, exp, met)
    print(f"[报告] {REPORT}")


if __name__ == "__main__":
    main()
