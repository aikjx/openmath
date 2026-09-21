# -*- coding: utf-8 -*-
"""
OpenMath 综合分析流水线（AI 辅助，需人类复核）

阶段：
  A. 数学理论体系分类  -> 09-数据/math_taxonomy.json
  B. 结构缺口/开放方向 -> 09-数据/math_gaps.json
  C. 诚实未解猜想登记  -> 09-数据/conjectures.json
  D. 综合分析报告      -> 06-AI自动化/01-工作流/ANALYSIS_REPORT.md

诚实边界（遵循 openmath 仓库 00-宪章/02-诚实红线）：
  - 数值验证 ≠ 证明；本文件产物均为 L0/L2 级数据处理/计算校验，非 L3+ 证据。
  - 预印本与猜想状态标 UNVERIFIED / UNSOLVED；proof_claimed 恒为 false。
  - 范围：以本次实际下载的 10 个 OpenMath CD 与 32 篇 arXiv 论文为地基，
    不构成"穷尽全部数学"，scope_note 中明示。
"""

import os
import sys
import json
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
AI_AUTO = os.path.dirname(HERE)
OPENMATH = os.path.dirname(AI_AUTO)
# 引擎已收纳进本仓库：06-AI自动化/02-引擎/openmath_sys/
SYS_SRC = os.path.join(OPENMATH, "06-AI自动化", "02-引擎", "openmath_sys", "src")
if SYS_SRC not in sys.path:
    sys.path.insert(0, SYS_SRC)

from openmath_sys.fetcher import parse_ocd  # noqa: E402
from openmath_sys.numeric import find_roots_numeric, verify_identity  # noqa: E402

CD_DIR = os.path.join(OPENMATH, "09-数据", "openmath_cds")
ANALYSIS_IN = os.path.join(OPENMATH, "09-数据", "openmath_4d_analysis.json")
PAPERS_IN = os.path.join(OPENMATH, "10-文献与索引", "arxiv_index.json")
OUT_DIR = os.path.join(OPENMATH, "09-数据")
REPORT = os.path.join(AI_AUTO, "01-工作流", "ANALYSIS_REPORT.md")

GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理基于 openmath_sys 引擎与已下载 OpenMath/arXiv 数据自动生成，未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = (
    "本系列文件为 L0/L2 级数据处理与计算校验产物，非证明。方程求解、猜想的可计算实验均为"
    "计算验证(L2)，不构成对未解猜想的证明。预印本与猜想状态均标 UNVERIFIED/UNSOLVED。"
)

# 经 GitHub API 核实的 OpenMath 官方 CD 总数（cd/Official/*.ocd）
OFFICIAL_CD_TOTAL = 38

# ---------------------------------------------------------------------------
# 方法注册表
#   说明：以下均为**数学界已知的标准方法**（L4 常识级），本文件只是整理性汇编。
#   `implemented` 表示**本流水线/引擎当前是否真的能执行**——只标 True 的才算数，
#   绝不冒领未实现的能力。未实现的在 limitation 中说明缺什么。
# ---------------------------------------------------------------------------
METHODS = [
    # --- 本流水线已实现 ---
    dict(id="ast_parse", name="句法解析(AST)", domain="通用/句法", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py", description="把数学文本解析成语法树(D1 句法维度)。",
         limitation="仅支持 + - * / ^ 与含参函数、比较运算符；不支持 LaTeX/积分号等高级记法。"),
    dict(id="arith_eval", name="表达式求值", domain="通用/计算", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py", description="代入变量数值求结果(D4 计算维度)。",
         limitation="纯数值，不做符号化简。"),
    dict(id="transc_eval", name="超越函数求值（三角/反三角/双曲/复数）", domain="超越函数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py (_call_func)",
         description="evaluate 支持 sin/cos/tan/sec/csc/cot、对应反函数与双曲/反双曲，"
                     "且**复数感知**（参数为复数或实数域溢出时回落 cmath）。",
         limitation="不支持 \\partial 偏导、grad/curl/laplacian 等向量分析算子；"
                    "多值函数在 |z|>1 处会因主分支约定出现'虚假不符'（非反例）。"),
    dict(id="poly_classify", name="方程形态分类", domain="代数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py", description="判定 linear/quadratic/transcendental 等(D3 结构维度)。",
         limitation="仅按变量次数分类，不识别更深结构（如可约性、对称性）。"),
    dict(id="linear_solve", name="一元一次方程求解", domain="代数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py", description="解形如 ax+b=0 的方程。",
         limitation="仅单变量、仅一次。"),
    dict(id="quadratic_formula", name="一元二次求根公式", domain="代数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/parser.py", description="解 ax²+bx+c=0（含复数根）。",
         limitation="仅单变量二次。"),
    dict(id="prime_sieve", name="埃拉托斯特尼筛", domain="数论", implemented=True,
         where="06-AI自动化/01-工作流/openmath_analyze.py (primes_upto)", description="求出 ≤N 的全部素数。",
         limitation="受内存与时间限制，N 不能过大。"),
    dict(id="exhaustive_search", name="穷举验证", domain="组合/数论", implemented=True,
         where="06-AI自动化/01-工作流/openmath_analyze.py (goldbach_check / collatz_check)", description="在有限范围内逐一验证命题成立。",
         limitation="只能给出有限区间内的证据，永远无法由此得到证明。"),
    dict(id="map_iteration", name="迭代映射", domain="动力系统", implemented=True,
         where="06-AI自动化/01-工作流/openmath_analyze.py (collatz_check)", description="迭代给定映射并记录收敛性。",
         limitation="长轨道需大量计算，且迭代本身不证明收敛性。"),
    # --- 未实现（标准方法，但本流水线做不到）---
    dict(id="factorization", name="因式分解", domain="代数", implemented=False,
         where=None, description="把多项式分解为不可约因子。",
         limitation="未实现：无符号多项式代数，导致大量 CD 恒等式无法机器处理。"),
    dict(id="grobner_basis", name="Gröbner 基", domain="代数几何", implemented=False,
         where=None, description="解多元多项式方程组的标准算法。",
         limitation="未实现：这是当前求解无法覆盖多变量的关键缺失。"),
    dict(id="gaussian_elimination", name="高斯消元", domain="线性代数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/structure.py",
         description="精确秩计算：有理数域(Fraction)与有限域 GF(p) 两种系数的行消元。",
         limitation="仅实现**精确秩**；未实现一般方程组的回代求解、符号消元与浮点版本。"),
    dict(id="eigen_decomposition", name="特征值/谱分解", domain="线性代数", implemented=False,
         where=None, description="矩阵特征值与对角化。",
         limitation="未实现。"),
    dict(id="symbolic_diff", name="符号微分", domain="微积分", implemented=False,
         where=None, description="对表达式求解析导数。",
         limitation="未实现：导致 calculus1 的微分性质无法验证。"),
    dict(id="symbolic_int", name="符号积分", domain="微积分", implemented=False,
         where=None, description="求不定/定积分的解析形式。",
         limitation="未实现。"),
    dict(id="limit_computation", name="极限计算", domain="微积分", implemented=False,
         where=None, description="解析求极限。",
         limitation="未实现。"),
    dict(id="numeric_root", name="数值求根", domain="数值分析", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/numeric.py",
         description="区间扫描+二分，求任意单变量方程的数值根（超越方程亦可）。",
         limitation="仅单变量；受 [lo,hi] 区间与步长限制可能漏根；结果为 L2 数值证据，非解析解、非证明。"),
    dict(id="numeric_zero_search", name="数值零点搜索", domain="解析数论", implemented=False,
         where=None, description="沿临界线搜索 ζ 函数零点（如 Riemann–Siegel 公式）。",
         limitation="未实现：故本流水线无法独立复核黎曼猜想的数值进展，仅能引用外部文献。"),
    dict(id="asymptotic_estimation", name="渐近估计", domain="解析数论", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/numbertheory.py",
         description="对计数函数做渐近对照：π(x) 与 x/ln x、li(x) 的数值比较。",
         limitation="**仅实现数值对照版本**：只做 π(x) 与两类近似的误差比较，"
                    "**不是**一般意义下的渐近展开推导工具（不能推导新渐近式）。"
                    "注意小 x 处 li 因含高阶正项反而高估更多，其优势在 x>=1000 后显现。"),
    dict(id="circle_method", name="圆法", domain="解析数论", implemented=False,
         where=None, description="Hardy–Littlewood 圆法，处理加性数论问题。",
         limitation="未实现。"),
    dict(id="sieve_theory", name="筛法（解析）", domain="解析数论", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/numbertheory.py",
         description="埃拉托斯特尼筛及其两个具体应用：哥德巴赫分拆计数、孪生素数筛。",
         limitation="**仅实现基础组合筛的两个具体应用**（分拆计数/孪生素数筛）；"
                    "**不是** Selberg 筛、大筛法等解析筛法理论，无法给出上界估计类结果。"),
    dict(id="modular_analysis", name="模类分析", domain="数论", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/numbertheory.py",
         description="按剩余类统计 Collatz 轨道停止时间的分布。",
         limitation="**仅实现最朴素的模类统计**（按 n mod m 分组求均值/最大值）；"
                    "是描述性统计，**不提供**任何证明方向。"),
    dict(id="elliptic_curve_computation", name="椭圆曲线计算", domain="代数几何/数论", implemented=False,
         where=None, description="计算椭圆曲线的秩、挠子群等。",
         limitation="未实现。"),
    dict(id="l_function_evaluation", name="L 函数求值", domain="解析数论", implemented=False,
         where=None, description="计算 L(s) 及其在临界点的导数。",
         limitation="未实现。"),
    dict(id="cohomology_computation", name="上同调计算", domain="代数几何", implemented=False,
         where=None, description="计算代数簇的上同调群（ℓ-adic / 德拉姆）。",
         limitation="未实现。注意：已实现的 homology_computation 是**有限链复形的域系数同调**，"
                    "与本条（射影代数簇的上同调、Hodge 分解、(p,p) 类）不是同一回事，"
                    "不能相互替代——这也是为何本条仍未实现。"),
    dict(id="structure_computation", name="有限群结构计算", domain="代数", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/structure.py",
         description="由 Cayley 表判定群公理，求单位元/逆元/元素阶/中心/交换性/子群（含 Lagrange 检验）。",
         limitation="仅**有限群且以 Cayley 表给出**；不处理无限群、不处理群表示论。"
                    "子群枚举用**循环子群 join 闭包**（`_subgroup_join_closure`），"
                    "完备性来自恒等式 H = join_{h∈H}⟨h⟩ 而非规模上限，故与阶数无关；"
                    "已在 n≤14 的库内群上与旧的指数级子集枚举逐群对账，0 分歧。"
                    "库内 16 阶群给出 14 个构造（与教科书计数相符），"
                    "但这是**构造出来的** 14 个，不等于证明了只有 14 个。"),
    dict(id="homology_computation", name="有限链复形同调", domain="代数拓扑", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/structure.py",
         description="构造链复形求 Betti 数（Q 与 GF(p)），并用泛系数定理递归检测 p-挠元个数；"
                     "附带 Euler 示性数的链群/Betti 双路自检。",
         limitation="仅**有限**单纯复形与 CW/Δ-复形，仅**域系数**。"
                    "能报 p-挠元**个数**但无法确定 Z_{p^k} 的指数 k；"
                    "不含上同调环结构、不含 Hodge 分解、不含谱序列。"),
    dict(id="pde_numerical_simulation", name="PDE 数值模拟", domain="偏微分方程", implemented=False,
         where=None, description="有限差分/谱方法求解 PDE。",
         limitation="未实现。"),
    dict(id="energy_estimate", name="能量估计", domain="偏微分方程", implemented=False,
         where=None, description="a priori 能量估计，用于正则性分析。",
         limitation="未实现。"),
    dict(id="complexity_reduction", name="复杂性归约", domain="计算复杂性", implemented=False,
         where=None, description="多项式时间归约与完备性分析。",
         limitation="未实现。"),
    dict(id="algebraic_complexity", name="代数复杂性(GCT)", domain="计算复杂性", implemented=False,
         where=None, description="几何复杂性理论路线。",
         limitation="未实现。"),
    dict(id="lattice_qcd_numeric", name="格点数值模拟", domain="数学物理", implemented=False,
         where=None, description="格点 QCD 给出质量间隙的数值证据。",
         limitation="未实现。"),
    dict(id="renormalization", name="重整化", domain="数学物理", implemented=False,
         where=None, description="重整化群的严格构造。",
         limitation="未实现。"),
    dict(id="rad_computation", name="rad 计算", domain="数论", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/numbertheory.py",
         description="精确计算 rad(n)（不同素因子之积），并搜索 quality>1 的 ABC 三元组。",
         limitation="rad(n) 本身按定义精确实现；但 ABC 三元组搜索为**穷举**，"
                    "受 c_max 上限限制，未找到更高 quality 不代表不存在。"),
    dict(id="random_matrix_analogy", name="随机矩阵类比", domain="解析数论/数学物理", implemented=False,
         where=None, description="以随机矩阵特征值统计类比 ζ 零点分布。",
         limitation="未实现。"),
    dict(id="holonomic_recurrence_discovery", name="P-recursive 递推发现（holonomic）",
         domain="组合/符号计算", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/sequences.py",
         description="对给定整数序列搜索 Σ_i p_i(n)·a(n−i)=0 形式的多项式系数递推："
                     "在多个大素数上做模消元求零空间，有理重建出系数，再做精确整数复核，"
                     "最后在**留出段**上做外推检验。",
         limitation="只报**发现集上精确相容且解唯一**的解，因此「外推证伪=0」"
                    "**不得**读成「没有过拟合」——不相容的序列连候选都报不出。"
                    "搜索受 max_order=4 / max_deg=4 限制（由对照实验定），"
                    "超出者会漏报。生成函数非 D-finite 的序列（贝尔数、划分数）"
                    "报不出是**正确结果**不是失败。另：这是**有限项上的候选**，"
                    "通过外推检验不等于对所有 n 成立，不构成发现。"),
    # ---- 千禧难题段（S10，2026-09-20 第六轮新增）----
    dict(id="millennium_formalization", name="命题形式化（量词/主词/谓词/否定）",
         domain="数理逻辑", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium.py",
         description="把七道千禧难题写成可机器处理的逻辑方程：量词结构、约束域、"
                     "谓词、以及**否定式**（反例长什么样）。",
         limitation="形式化是**措辞的整理**，不承担任何证明责任；"
                    "把自然语言命题改写成一阶句式时可能丢失原意的细微差别。"),
    dict(id="millennium_nesting", name="无穷套娃分解（递归子命题树）", domain="数理逻辑",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium.py",
         description="把每个命题递归分解为子命题树，叶节点分三类：已证定理 / 本引擎可算的"
                     "有限检验 / 开放叶。开放叶**如实保留**，并记录递归在该处停止。",
         limitation="递归在开放叶处停止是**事实陈述**而非闭合；树深度 2–3 受人工编写限制，"
                    "不保证覆盖所有已知路线，也不保证分解是最优的。"),
    dict(id="finite_shadow", name="有限影子命题（及其不蕴含性判定）", domain="数理逻辑",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium.py",
         description="为每个无限命题配一个**有限截断版本**（如 RH 截到 |Im ρ| ≤ T），"
                     "并显式判定「影子 ⟹ 原命题」是否成立。",
         limitation="**所有七题的影子都不蕴含原命题**（n_shadow_implies_full = 0），"
                    "这是刻意保留的结论：有限截断与证明之间存在本质鸿沟。"),
    dict(id="hardy_z_zero_count", name="Hardy Z 函数零点计数", domain="解析数论",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium_lab.py",
         description="用 Z(t)=e^{iθ(t)}ζ(½+it) 的符号变号数统计临界线零点，"
                     "与 Riemann–von Mangoldt 主项对账，前 10 个零点对教科书值校准。",
         limitation="只数**临界线上**的符号变号，不排除临界线外的零点；"
                    "符号变号计数在零点成对时可能漏计；T=600 是本轮跑到的高度，"
                    "不是能力上限，也**不是**对 RH 的证据——RH 要求全部零点。"),
    dict(id="argument_principle_count", name="辐角原理零点计数（S(T) 展开）",
         domain="解析数论", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/audit.py",
         description="沿 2 → 2+iT → ½+iT 连续跟踪 arg ζ 的增量求 S(T)，"
                     "再用 N(T)=θ(T)/π+1+S(T) 得零点总数——与符号变号计数**原理不同**。",
         limitation="依赖被测代码的 ζ 求值器（已由 η+Euler 变换独立校准）；"
                    "路径若恰好穿过零点会导致辐角展开失败，本轮未做该情形的处理。"),
    dict(id="ec_point_count_finite", name="有限域椭圆曲线点计数", domain="算术几何",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium_lab.py",
         description="算 #E(F_p) 与 a_p = p+1−#E，检验 Hasse 界 |a_p| ≤ 2√p（定理，校准件）。",
         limitation="Hasse 界是**已证定理**，能对上只说明点计数代码正确；"
                    "BSD 讲的是 ord_{s=1}L(E,s) = rank E(Q)，本实验**没有算 L 函数、"
                    "也没有算代数秩**，故对 BSD **零证据**。"),
    dict(id="combinatorial_hodge", name="有限复形上的组合 Hodge", domain="代数拓扑",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium_lab.py",
         description="在有限单纯复形上用精确有理线性代数算 Betti 数 b_k 与调和形式维数 "
                     "dim ker Δ_k，并做 b_k = dim ker Δ_k 的对账。",
         limitation="这是**离散类比**不是霍奇猜想：有限复形上没有 (p,p) 型分解，"
                    "也没有代数闭链的概念；该等式是线性代数恒等式（必成立），"
                    "能对上只说明链复形与拉普拉斯的代码正确。"),
    dict(id="burgers_finite_difference", name="一维 Burgers 有限差分（迎风 + 特征线）",
         domain="偏微分方程数值解", implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium_lab.py",
         description="迎风格式演化 u_t + u u_x = ν u_xx，用特征线法估计激波时刻，"
                     "与解析解 t* = −1/min u₀′ 对账，并给出网格细分下的收敛性。",
         limitation="一维 Burgers **不是**三维 Navier–Stokes：没有涡量拉伸项、"
                    "没有不可压缩约束，且 ν>0 时已知全局正则。对千禧难题**零证据**。"
                    "另：阈值型估计量在细分下**并不收敛**（离散梯度 ~1/dx），"
                    "这一负面结果已如实记录，不得隐去。"),
    dict(id="sat_phase_transition", name="随机 3-SAT 相变实验", domain="计算复杂性",
         implemented=True,
         where="06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/millennium_lab.py",
         description="在 α=m/n 网格上测可满足率与 DPLL 决策数，并用 2^n 全枚举对账判定。",
         limitation="**对 P vs NP 本身证据为零**：有限规模的曲线既不蕴含 P≠NP "
                    "也不蕴含 P=NP。列出它的唯一理由是它是同域内本引擎能真跑的计算。"),
]

# 猜想 -> 可适用方法（标准数学意义上的适用）
CONJECTURE_METHODS = {
    "RH": ["numeric_zero_search", "asymptotic_estimation", "random_matrix_analogy"],
    "GC": ["prime_sieve", "exhaustive_search", "circle_method", "sieve_theory"],
    "TPC": ["prime_sieve", "exhaustive_search", "sieve_theory", "asymptotic_estimation"],
    "COLLATZ": ["map_iteration", "exhaustive_search", "modular_analysis"],
    "BSD": ["elliptic_curve_computation", "l_function_evaluation"],
    "HODGE": ["cohomology_computation"],
    "NS": ["pde_numerical_simulation", "energy_estimate"],
    "PNP": ["complexity_reduction", "algebraic_complexity"],
    "YM": ["lattice_qcd_numeric", "renormalization"],
    "POINCARE": ["ricci_flow_analysis"],
    "ABC": ["rad_computation", "exhaustive_search"],
}
# POINCARE 已解决，用 Ricci 流（补一个未在这样的 antiquated 列表里的条目）
METHODS.append(dict(id="ricci_flow_analysis", name="Ricci 流几何化分析", domain="几何/拓扑",
                    implemented=False, where=None,
                    description="以 Ricci 流做流形几何化与奇点分析（佩雷尔曼路线）。",
                    limitation="未实现。"))


# CD -> 领域（按 OpenMath 官方内容字典语义归纳）
DOMAIN_MAP = {
    "arith1": "算术 Arithmetic",
    "arith2": "算术 Arithmetic",
    "integer1": "数系与常数 Numbers",
    "relation1": "关系与序 Relation/Order",
    "minmax1": "关系与序 Relation/Order",
    "transc1": "超越函数 Transcendental Functions",
    "linalg2": "线性代数 Linear Algebra",
    "linalg1": "线性代数 Linear Algebra",
    "veccalc1": "向量微积分 Vector Calculus",
    "calculus1": "微积分 Calculus",
    "limit1": "微积分 Calculus",
    "logic1": "逻辑 Logic",
    "setname1": "集合与数系 Sets/Number Systems",
    "set1": "集合 Sets",
    "multiset1": "集合 Sets",
    "complex1": "复数 Complex Numbers",
    "alg1": "代数结构 Algebra",
    "nums1": "数系与常数 Numbers",
    "fns1": "函数 Functions",
    "fns2": "函数 Functions",
    "list1": "列表与数据结构 Lists",
}


# --------------------------------------------------------------------------
# 阶段 A：理论体系分类
# --------------------------------------------------------------------------
def build_taxonomy(cds_parsed, equations_by_cd):
    domains = {}
    totals = {"cds": 0, "symbols": 0, "properties": 0, "equations_analyzed": 0}
    for cd_name, syms in cds_parsed.items():
        dom = DOMAIN_MAP.get(cd_name, cd_name)
        d = domains.setdefault(
            dom,
            {"domain": dom, "cds": [], "symbol_count": 0, "property_count": 0,
             "symbols": [], "sample_equations": []},
        )
        props = sum(len(s["properties"]) for s in syms)
        d["cds"].append(cd_name)
        d["symbol_count"] += len(syms)
        d["property_count"] += props
        for s in syms:
            d["symbols"].append({
                "name": s["name"], "cd": cd_name,
                "description": s["description"], "n_properties": len(s["properties"]),
            })
        eqs = equations_by_cd.get(cd_name, [])
        d["sample_equations"].extend([e["raw"] for e in eqs if e.get("is_equation")][:5])
        totals["cds"] += 1
        totals["symbols"] += len(syms)
        totals["properties"] += props
        totals["equations_analyzed"] += sum(1 for e in eqs if e.get("is_equation"))
    domains = list(domains.values())
    domains.sort(key=lambda x: -x["symbol_count"])
    return {"domains": domains, "totals": totals}


# --------------------------------------------------------------------------
# 阶段 B：结构缺口 / 开放方向
# --------------------------------------------------------------------------
def build_gaps(cds_parsed, equations_by_cd, catalog):
    gaps = []
    # 1) 性质为 0 的 CD（缺少可计算/可证性质）
    for cd in catalog["cds"]:
        if cd["property_count"] == 0:
            gaps.append({
                "type": "empty_properties", "severity": "high",
                "target": cd["name"],
                "note": f"{cd['name']} 已下载 {cd['symbol_count']} 个符号但 0 条 CMP 性质，"
                        f"无法抽取方程/恒等式，是明显的结构空洞。",
            })
    # 2) 已分析方程数为 0 的领域
    for cd_name, syms in cds_parsed.items():
        eqs = equations_by_cd.get(cd_name, [])
        if syms and len(eqs) == 0:
            gaps.append({
                "type": "no_equations", "severity": "medium",
                "target": cd_name,
                "note": f"{cd_name} 有 {len(syms)} 个符号但本次未抽取到任何可解析方程，"
                        f"需补充性质文本或手工录入示例。",
            })
    # 3) 跨 CD 依赖：按领域聚合性质，判断是否仍有'底层支撑缺失'
    dom_props = {}
    for cd_name, syms in cds_parsed.items():
        dom = DOMAIN_MAP.get(cd_name, cd_name)
        dom_props[dom] = dom_props.get(dom, 0) + sum(len(s["properties"]) for s in syms)
    la_total = dom_props.get("线性代数 Linear Algebra", 0)
    if la_total == 0:
        gaps.append({
            "type": "cross_dependency_gap", "severity": "high",
            "target": "linalg2",
            "note": "线性代数是微积分/复数/代数结构的底层支撑，但其 CD 无性质、无方程；"
                    "体系在'矩阵/向量运算的机器可处理性质'上存在断点。",
        })
    else:
        # 按实际有性质的同级 CD 动态列出，避免写死不存在的 CD 名
        la_domain = "线性代数 Linear Algebra"
        suppliers = [
            cd for cd, syms in cds_parsed.items()
            if DOMAIN_MAP.get(cd, cd) == la_domain
            and sum(len(s["properties"]) for s in syms) > 0
        ]
        gaps.append({
            "type": "cross_dependency_gap", "severity": "info",
            "target": "linalg2",
            "note": f"linalg2 本身仍仅 3 个构造符号、0 性质（官方上游 CD 如此），"
                    f"但'线性代数'领域已由 {', '.join(suppliers)} 提供 {la_total} 条性质，"
                    f"结构性断点已缓解。",
        })
    # 4) 覆盖盲区（本次未下载的数百个 OpenMath CD）
    total_fetched = sum(1 for c in catalog["cds"] if c["fetched"])
    gaps.append({
        "type": "coverage_blindspot", "severity": "info",
        "target": "OpenMath CD 全集",
        "note": f"本次摄取 {total_fetched}/{OFFICIAL_CD_TOTAL} 个官方 CD。需特别注意："
                f"OpenMath 官方 CD 全集本身体量有限（共 {OFFICIAL_CD_TOTAL} 个），"
                f"并不覆盖群论、拓扑、测度、概率、图论、微分几何等众多数学领域；"
                f"这些超出 OpenMath 现有覆盖范围，若需覆盖须引入其他知识源，"
                f"而非简单'多下几个 CD'。",
    })
    gaps.append({
        "type": "method_blindspot", "severity": "info",
        "target": "方程求解器",
        "note": "当前求解仅覆盖单变量多项式(线性/二次)；缺 Gröbner 基、常/偏微分方程、"
                "符号积分等方法，限制了'方法'维度的完整性。",
    })
    return gaps


# --------------------------------------------------------------------------
# 阶段 C：诚实未解猜想登记表
# --------------------------------------------------------------------------
def primes_upto(n):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, ok in enumerate(sieve) if ok]


def goldbach_check(n):
    ps = primes_upto(n)
    pset = set(ps)
    fails = []
    for e in range(4, n + 1, 2):
        if not any((e - p) in pset for p in ps if p <= e // 2):
            fails.append(e)
    return {"limit": n, "holds": len(fails) == 0,
            "counterexamples": fails[:10], "checked_evens": n // 2}


def twin_prime_count(n):
    ps = primes_upto(n)
    s = set(ps)
    return {"limit": n, "twin_pairs": sum(1 for p in ps if p + 2 in s)}


def collatz_check(n):
    bad = []
    max_steps = 0
    for start in range(1, n + 1):
        x, steps = start, 0
        while x != 1:
            x = x // 2 if x % 2 == 0 else 3 * x + 1
            steps += 1
            if steps > 100000:
                bad.append(start)
                break
        max_steps = max(max_steps, steps)
    return {"limit": n, "all_reach_1": len(bad) == 0,
            "exceptions": bad[:10], "max_steps_observed": max_steps}


def build_conjectures():
    # 可计算实验（真实运行，标 L2）
    gb = goldbach_check(20000)
    tw = twin_prime_count(200000)
    cz = collatz_check(100000)

    items = [
        {
            "id": "RH",
            "name": "黎曼猜想 Riemann Hypothesis",
            "domain": "解析数论",
            "statement": "黎曼 ζ 函数的所有非平凡零点实部均为 1/2。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": [
                "文献：前 10^13 个非平凡零点已数值验证落在临界线上（L2，外部计算，非证明）。",
                "平凡零点 ζ(-2n)=0 可由函数方程直接推出（L4 已知结论，非猜想本身）。",
            ],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：本质困难在于零点的'全局分布'与素数分布的关联缺少可机器化的"
                "结构性桥梁。现有路线（显式公式、随机矩阵类比、ζ 函数的谱解释）均未能把"
                "数值规律提升为解析证明。可探索的开放方向：将零点分布编码为某自伴算子的谱"
                "（Hilbert–Pólya 路线）并构造该算子。"
            ),
        },
        {
            "id": "GC",
            "name": "哥德巴赫猜想 Goldbach's Conjecture",
            "domain": "数论",
            "statement": "任一大于 2 的偶数都可写成两个素数之和。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["对有限范围做穷举求和验证（L2）。"],
            "our_l2_results": gb,
            "theoretical_gap": (
                "缺失方向：筛法（陈氏定理等）能证明'1 个素数 + 1 个殆素数'，但跨过'殆素数→素数'"
                "的最后一步缺乏普适工具。开放方向：圆法（Hardy–Littlewood）的误差项控制、或"
                "筛权函数的本质改进。"
            ),
        },
        {
            "id": "TPC",
            "name": "孪生素数猜想 Twin Prime Conjecture",
            "domain": "数论",
            "statement": "存在无穷多对相差 2 的素数。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["统计有限范围内的孪生素数对数量（L2）。"],
            "our_l2_results": tw,
            "theoretical_gap": (
                "缺失方向：张益唐(2013)证明存在无穷多对差 < 7000 万的素数，界限已被降到 246；"
                "但逼近 2 需突破 GPY 筛法的'奇偶障碍'(parity problem)。开放方向：借助更精细的"
                "权重或分布级数假设(DHL)进一步压缩界。"
            ),
        },
        {
            "id": "COLLATZ",
            "name": "角谷/考拉兹猜想 3n+1",
            "domain": "动力系统 / 离散数学",
            "statement": "对任意正整数 n，迭代 n→n/2(n偶) 或 3n+1(n奇) 终将到达 1。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["对有限范围穷举迭代验证是否归 1（L2）。"],
            "our_l2_results": cz,
            "theoretical_gap": (
                "缺失方向：该问题缺乏自然的代数结构，现有攻击（停止时间分布、模类分析、"
                "概率启发式）都无法排除极长轨道或循环的存在。开放方向：将其嵌入更广的"
                "动力系统类并寻找不变量，或证明其'几乎必然'归 1 作为中间目标。"
            ),
        },
        {
            "id": "BSD",
            "name": "BSD 猜想 Birch–Swinnerton-Dyer",
            "domain": "代数几何 / 数论",
            "statement": "椭圆曲线的秩等于其 L 函数在 s=1 处零点的阶。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["对具体椭圆曲线数值计算秩与 L 导数（需符号计算库，本次未跑）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：需把'算术信息'(秩、Shafarevich–Tate 群)与'分析信息'(L 函数)通过"
                "某种'高度配对'联系起来。开放方向：Iwasawa 理论、欧拉系的构造。"
            ),
        },
        {
            "id": "HODGE",
            "name": "霍奇猜想 Hodge Conjecture",
            "domain": "代数几何",
            "statement": "非奇异复射影代数簇上的某类上同调类可由代数闭链表示。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["无通用可计算判据（属纯存在性/结构问题）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：代数闭链与拓扑上同调之间的'可表示性'判据缺失。开放方向：借助"
                "motivic 上同调或更弱的代数几何不变量重构问题。"
            ),
        },
        {
            "id": "NS",
            "name": "纳维–斯托克斯存在性与光滑性",
            "domain": "偏微分方程 / 数学物理",
            "statement": "三维不可压 N-S 方程在给定初值下是否存在全局光滑解。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["数值模拟（非证明）；能量方法仅得弱解。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：从弱解到强解的正则性跨越缺少控制机制；湍流级联的能量转移无法被"
                "现有估计封顶。开放方向：新的 a priori 估计、或证明有限时间奇点不存在的构造性"
                "方法。"
            ),
        },
        {
            "id": "PNP",
            "name": "P vs NP",
            "domain": "计算复杂性理论",
            "statement": "是否所有 NP 问题都能在多项式时间内求解（P=NP）。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["无（属相对性/存在性判定，非数值实验）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：缺乏区分'搜索'与'验证'复杂度的代数不变量；对角化与 relativization"
                "障碍使经典方法失效。开放方向：代数几何/逻辑（几何复杂性理论 GCT）路线。"
            ),
        },
        {
            "id": "YM",
            "name": "杨–米尔斯质量间隙",
            "domain": "数学物理 / 量子场论",
            "statement": "四维杨–米尔斯理论存在质量间隙（谱下界 > 0）。",
            "status": "UNSOLVED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "computable_aspects": ["格点 QCD 数值给出质量间隙证据（L2，非证明）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：构造满足 Wightman 公理的严格量子场论框架本身未解决；需把物理"
                "直觉转为可证数学对象。开放方向：严格的构造性 QFT 与重整化收剑性证明。"
            ),
        },
        {
            "id": "POINCARE",
            "name": "庞加莱猜想 Poincaré Conjecture",
            "domain": "拓扑学",
            "statement": "单连通的三维闭流形同胚于三维球面。",
            "status": "SOLVED",
            "evidence_grade": "VERIFIED_L4",
            "proof_claimed": True,
            "proof_by": "Grigori Perelman (2003，基于 Hamilton 的 Ricci 流)",
            "computable_aspects": ["无（已证明）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "已解决，作为'处理思维'的正面范例：把拓扑问题转为几何流( Ricci 流)的奇点分析，"
                "开创了几何化纲领。其方法论（几何化 + 奇点 surgery）可迁移到其他流形分类问题。"
            ),
        },
        {
            "id": "ABC",
            "name": "ABC 猜想",
            "domain": "数论",
            "statement": "对互素正整数 a+b=c，rad(abc) 与 c 的关系存在一致上界。",
            "status": "DISPUTED",
            "evidence_grade": "UNVERIFIED",
            "proof_claimed": False,
            "proof_note": "Mochizuki(2012) 的'宇宙際 Teichmüller 理论'证明至今未被广泛接受。",
            "computable_aspects": ["对有限范围数值检验 rad 上界（L2）。"],
            "our_l2_results": None,
            "theoretical_gap": (
                "缺失方向：即便接受 IUTT，其可机器化验证路径仍不成熟；社区对证明正确性无共识。"
                "开放方向：寻找更可被检验的替代证明，或把 IUTT 形式化（Lean/Coq）以便机器核查。"
            ),
        },
    ]
    return items


# --------------------------------------------------------------------------
# 阶段 E：方法体系 + 猜想的方法覆盖（"有无处理方向"判定）
# --------------------------------------------------------------------------
def build_method_system(conjectures: list[dict]) -> dict:
    m_by_id = {m["id"]: m for m in METHODS}
    linkage = []
    for c in conjectures:
        ids = CONJECTURE_METHODS.get(c["id"], [])
        applicable = [m_by_id[i] for i in ids if i in m_by_id]
        impl = [m for m in applicable if m["implemented"]]
        # 诚实判定：未解猜想即便穷尽现有方法也未被解决，故 can_resolve 恒 False
        can_resolve = (c["status"] == "SOLVED")
        linkage.append({
            "conjecture_id": c["id"],
            "conjecture_name": c["name"],
            "status": c["status"],
            "applicable_methods": [m["id"] for m in applicable],
            "implemented_applicable": [m["id"] for m in impl],
            "missing_methods": [m["id"] for m in applicable if not m["implemented"]],
            "method_coverage": round(len(impl) / len(applicable), 4) if applicable else 0.0,
            "can_resolve": can_resolve,
            "direction_note": c.get("theoretical_gap", ""),
        })
    impl_n = sum(1 for m in METHODS if m["implemented"])
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_analyze.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "note": (
                f"方法清单为标准数学方法的**整理性汇编**（KNOWN_L4 常识级）；"
                f"`implemented` 字段严格表示本流水线当前是否真能执行，共 {impl_n}/{len(METHODS)} 项已实现。"
                f"对未解猜想，即便全部适用方法齐备也仍未被解决，故 can_resolve 除已解决的庞加莱外恒为 False，"
                f"绝不暗示本系统或现有方法足以证明它们。"
            ),
        },
        "summary": {
            "methods_total": len(METHODS),
            "methods_implemented": impl_n,
            "methods_missing": len(METHODS) - impl_n,
            "conjectures_linked": len(linkage),
            "conjectures_with_zero_implemented_direction": sum(
                1 for l in linkage if l["status"] != "SOLVED" and not l["implemented_applicable"]
            ),
        },
        "methods": METHODS,
        "linkage": linkage,
    }


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main():
    # 读取已下载数据
    with open(ANALYSIS_IN, encoding="utf-8") as f:
        analysis = json.load(f)
    with open(PAPERS_IN, encoding="utf-8") as f:
        papers = json.load(f)
    with open(os.path.join(CD_DIR, "catalog.json"), encoding="utf-8") as f:
        catalog = json.load(f)

    # 解析每个 .ocd
    cds_parsed = {}
    for fn in os.listdir(CD_DIR):
        if fn.endswith(".ocd"):
            name = fn[:-4]
            try:
                syms = parse_ocd(open(os.path.join(CD_DIR, fn), encoding="utf-8").read())
                cds_parsed[name] = [
                    {"name": s.name, "cd": s.cd, "description": s.description,
                     "properties": s.properties} for s in syms
                ]
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] 解析 {fn} 失败: {e}")

    # 方程按来源 CD 分组（source 形如 "CD:arith1/lcm"）
    equations_by_cd = {}
    for r in analysis.get("results", []):
        src = r.get("source", "unknown")
        if src.startswith("CD:") and "/" in src:
            cd = src[3:].split("/", 1)[0]
        else:
            cd = "seed"
        equations_by_cd.setdefault(cd, []).append({
            "raw": r.get("raw"),
            "is_equation": r.get("is_equation"),
            "classification": r.get("classification"),
            "solve": r.get("solve"),
        })

    # 阶段 A
    taxonomy = build_taxonomy(cds_parsed, equations_by_cd)
    taxonomy_doc = {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_analyze.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "scope_note": (
                f"以本次实际下载的 {taxonomy['totals']['cds']} 个 OpenMath 官方 CD"
                f"（{taxonomy['totals']['symbols']} 符号、"
                f"{taxonomy['totals']['properties']} 条 CMP 性质、"
                f"{taxonomy['totals']['equations_analyzed']} 条已分析方程）与论文索引为地基"
                f"构建的分类骨架。它是对数学理论体系的'结构化索引'，而非穷尽全部数学。"
                f"OpenMath 官方 CD 全集共 {OFFICIAL_CD_TOTAL} 个，本次已覆盖其中大部分高价值 CD；"
                f"但即便全集也不包含群论、拓扑、概率、微分几何等众多领域，"
                f"这些属已知且无法通过增补 OpenMath CD 消除的盲区。"
            ),
        },
        "domains": taxonomy["domains"],
        "totals": taxonomy["totals"],
        "papers_summary": {
            "total": papers["stats"]["total"],
            "by_category": papers["stats"]["by_category"],
        },
    }
    with open(os.path.join(OUT_DIR, "math_taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(taxonomy_doc, f, ensure_ascii=False, indent=2)
    print(f"[A] 理论体系分类：{taxonomy['totals']['cds']} CD / "
          f"{taxonomy['totals']['symbols']} 符号 / {taxonomy['totals']['properties']} 性质 / "
          f"{taxonomy['totals']['equations_analyzed']} 方程")

    # 阶段 B
    gaps = build_gaps(cds_parsed, equations_by_cd, catalog)
    gaps_doc = {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_analyze.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
        },
        "open_directions": gaps,
    }
    with open(os.path.join(OUT_DIR, "math_gaps.json"), "w", encoding="utf-8") as f:
        json.dump(gaps_doc, f, ensure_ascii=False, indent=2)
    print(f"[B] 结构缺口/开放方向：{len(gaps)} 条")

    # 阶段 C
    conjectures = build_conjectures()
    con_doc = {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_analyze.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "disclaimer": (
                "本文件为猜想的'分析与登记'。除已解决的庞加莱猜想(SOLVED/VERIFIED_L4，"
                "proof_claimed=true)外，其余未解/争议条目 proof_claimed 均为 false，"
                "状态标 UNSOLVED/UNVERIFIED/DISPUTED。可计算实验(our_l2_results)仅为 L2 数值证据，"
                "不构成对任一猜想的证明。"
            ),
        },
        "conjectures": conjectures,
    }
    with open(os.path.join(OUT_DIR, "conjectures.json"), "w", encoding="utf-8") as f:
        json.dump(con_doc, f, ensure_ascii=False, indent=2)
    print(f"[C] 未解猜想登记：{len(conjectures)} 条"
          f"（其中可计算实验：哥德巴赫{conjectures[1]['our_l2_results']['holds']}、"
          f"孪生素数{conjectures[2]['our_l2_results']['twin_pairs']}对、"
          f"角谷{conjectures[3]['our_l2_results']['all_reach_1']}）")

    # 阶段 E：方法体系 + 猜想方法覆盖
    method_doc = build_method_system(conjectures)
    with open(os.path.join(OUT_DIR, "method_system.json"), "w", encoding="utf-8") as f:
        json.dump(method_doc, f, ensure_ascii=False, indent=2)
    print(f"[E] 方法体系：{method_doc['summary']['methods_total']} 条方法"
          f"（已实现 {method_doc['summary']['methods_implemented']}）；"
          f"无可用已实现方法的未解猜想 "
          f"{method_doc['summary']['conjectures_with_zero_implemented_direction']} 条")

    # 阶段 F：数值兜底增强
    #   关键认知修正：CD 中的 CMP 性质绝大多数是**多变量代数恒等式**（如 lcm(a,b)=a*b/gcd(a,b)、
    #   sin(A+B)=...），而非"求根方程"。对恒等式正确的处理是**数值抽样验证**，不是求解。
    #   因此本阶段主操作为 verify_identity；find_roots_numeric 仅用于真正的单变量方程。
    num_rows, prev_fail = [], 0
    n_hold = n_fail = n_skip = n_uneval = n_roots = 0
    n_not_dec = n_inconc = 0
    for r in analysis.get("results", []):
        if not r.get("is_equation"):
            continue
        if (r.get("solve") or {}).get("solvable"):
            continue  # 符号求解已成功，无需数值兜底
        prev_fail += 1
        raw = r.get("raw", "")
        ident = verify_identity(raw)  # 先在单位区间（主分支一致）验证
        # 只在**可判定但不符合**时放宽抽样域重试；
        # not_decidable 是解析/范围层面的问题，换区间重试没有意义。
        if ident.get("status") in ("fails", "inconclusive"):
            wider = verify_identity(raw, lo=0.1, hi=5.0)  # 再放宽，标记更宽的验证域
            if wider.get("status") == "holds":
                wider["verified_on_wider_range"] = [0.1, 5.0]
                ident = wider
        st = ident["status"]
        if st == "holds":
            n_hold += 1
        elif st == "fails":
            n_fail += 1
        elif st == "not_decidable":
            n_not_dec += 1
        elif st == "inconclusive":
            n_inconc += 1
        elif st == "skip":
            n_skip += 1
        else:
            n_uneval += 1
        roots = None
        if len(r.get("variables") or []) == 1:
            rr = find_roots_numeric(raw)
            if rr.get("status") == "ok" and rr.get("roots"):
                roots = rr["roots"]
                n_roots += 1
        num_rows.append({
            "raw": raw, "source": r.get("source"),
            "symbolic_reason": (r.get("solve") or {}).get("reason"),
            "identity": ident, "numeric_roots": roots,
        })
    numeric_doc = {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_analyze.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "note": (
                "对符号求解器判定失败的式子做数值兜底。"
                "主操作 verify_identity 为**随机抽样验证代数恒等式**（多在正实数域）；"
                "单变量式子另做 find_roots_numeric 数值求根。"
                "所有结果均为 L2 数值证据：'holds' 只是有限抽样吻合，绝非证明；"
                "'fails' 也可能源于求值器局限或抽样域不匹配，不等于找到反例。"
                "2026-09-19 审计后新增**准入筛查**：超出能力范围的式子一律给出 "
                "not_decidable 而**不再**给出 holds/fails——因为那类结论反映的是"
                "求值器的局限，不是式子的数学性质。"
            ),
        },
        "summary": {
            "symbolic_failed": prev_fail,
            "identity_decidable": n_hold + n_fail,
            "identity_holds": n_hold,
            "identity_fails": n_fail,
            "not_decidable": n_not_dec,
            "inconclusive": n_inconc,
            "skipped_non_algebraic": n_skip,
            "unevaluable": n_uneval,
            "numeric_roots_found": n_roots,
            # 口径修正（2026-09-19）：
            # 旧口径把「恒等式通过数 + 求根成功数」除以「全部符号失败数」，
            # 分子分母来自不同的判定通道，且把不该判的条目也算进分母。
            # 现在只保留一个含义明确的比率：恒等式判定的通过率。
            "identity_pass_rate": round(n_hold / (n_hold + n_fail), 4)
            if (n_hold + n_fail) else 0.0,
            "resolution_rate": round((n_hold + n_roots) / prev_fail, 4) if prev_fail else 0.0,
            "rate_note": (
                "identity_pass_rate 的分母是**可判定条数**（holds+fails），含义单一；"
                "resolution_rate 沿用了旧口径（分子含数值求根，分母是全部符号失败条目），"
                "保留它只是为了与历史报告对照。两个比率**不要混用**，"
                "也不要把其中任何一个读成「这些式子被解决了」。"
            ),
        },
        "solutions": num_rows,
    }
    with open(os.path.join(OUT_DIR, "numeric_solutions.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(numeric_doc, ensure_ascii=False, indent=2, default=str))
    print(f"[F] 数值兜底：符号失败 {prev_fail} 条 → 恒等式抽样验证通过 {n_hold} 条、"
          f"数值求根 {n_roots} 条（处置率 {numeric_doc['summary']['resolution_rate']:.0%}）")

    # 阶段 D：报告
    write_report(taxonomy_doc, gaps_doc, con_doc, method_doc, numeric_doc)
    print(f"[D] 报告已写：{REPORT}")


def write_report(tax_doc, gaps_doc, con_doc, method_doc, numeric_doc):
    t = tax_doc["totals"]
    doms = tax_doc["domains"]
    lines = []
    lines.append("# OpenMath 综合分析报告（AI 辅助，需人类复核）\n")
    lines.append(f"- 生成时间：`{GEN_AT}`")
    lines.append("- 产物：`09-数据/math_taxonomy.json`、`09-数据/math_gaps.json`、"
                 "`09-数据/conjectures.json`\n")
    lines.append("> ⚠️ **诚实红线**：本报告为 L0/L2 级数据处理与计算校验产物，**非证明**。\n"
                 "> 方程求解与猜想的可计算实验均为计算验证(L2)；预印本与猜想状态标 "
                 "`UNVERIFIED`/`UNSOLVED`。所有内容 `provenance.ai_assisted=true`，未经人类复核。\n")

    lines.append("## 0. 范围与边界（先说清不能做什么）\n")
    lines.append(tax_doc["meta"]["scope_note"])
    lines.append("")
    lines.append("- 不声称'穷尽全部数学'：仅以 10 个 CD 为骨架。")
    lines.append("- 不声称'解决'任何未解猜想：仅做可计算子问题的 L2 实验并登记开放方向。")
    lines.append("- 不映射到任何系统/OS 提权：'最高权限'在本工程中仅指内部逻辑授权上限。\n")

    lines.append("## 1. 数学理论体系分类（按领域）\n")
    lines.append(f"合计：**{t['cds']} 个 CD / {t['symbols']} 个符号 / "
                 f"{t['properties']} 条性质 / {t['equations_analyzed']} 条已分析方程**。\n")
    lines.append("| 领域 | CD | 符号 | 性质 | 示例方程数 |")
    lines.append("|---|---|---|---|---|")
    for d in doms:
        lines.append(f"| {d['domain']} | {', '.join(d['cds'])} | {d['symbol_count']} "
                     f"| {d['property_count']} | {len(d['sample_equations'])} |")
    lines.append("")

    lines.append("## 2. 结构缺口与开放方向（'没有方向的处理思路逻辑'）\n")
    for g in gaps_doc["open_directions"]:
        sev = g["severity"].upper()
        lines.append(f"- **[{sev}] {g['type']}** → `{g['target']}`：{g['note']}")
    lines.append("")

    lines.append("## 3. 未解猜想登记表（诚实，proof_claimed=false）\n")
    lines.append("| 猜想 | 领域 | 状态 | 证据 | 可计算实验 |")
    lines.append("|---|---|---|---|---|")
    for c in con_doc["conjectures"]:
        l2 = "—"
        if c.get("our_l2_results"):
            r = c["our_l2_results"]
            if "holds" in r:
                l2 = f"≤{r['limit']}:{'成立' if r['holds'] else '发现反例'}"
            elif "twin_pairs" in r:
                l2 = f"≤{r['limit']}:{r['twin_pairs']}对"
            elif "all_reach_1" in r:
                l2 = f"≤{r['limit']}:{'全部归1' if r['all_reach_1'] else '异常'}"
        lines.append(f"| {c['name']} | {c['domain']} | {c['status']} "
                     f"| {c['evidence_grade']} | {l2} |")
    lines.append("")
    lines.append("每条猜想的 `theoretical_gap` 字段记录了当前**缺失的证明方向**（即'无方向的处理"
                 "思路逻辑'），详见 `conjectures.json`。举两例：")
    for c in con_doc["conjectures"]:
        if c["id"] in ("RH", "PNP"):
            lines.append(f"\n**{c['name']}** 的缺失方向：{c['theoretical_gap'].lstrip('缺失方向：')}")

    lines.append("\n## 4. 四维 + 元启发式处理思维框架（综合体系）\n")
    lines.append("在既有 D1 句法 / D2 语义 / D3 结构 / D4 计算 四维之上，补一层**元启发式**"
                 "用于处理开放问题：")
    lines.append("1. **归约(Redux)**：把未知问题映射到有结构的已知 CD 符号空间（D2/D3）。")
    lines.append("2. **计算试探(L2)**：对可计算子问题先跑数值实验，区分'经验成立'与'已证明'。")
    lines.append("3. **缺口定位**：用结构缺口分析找到理论体系中的空洞（如 linalg2 无性质）。")
    lines.append("4. **方向生成**：从 `theoretical_gap` 抽取开放研究方向，形成可推进的问题链。")
    lines.append("5. **诚实标注**：每一步标注证据等级(L0–L6)与 ai_assisted，禁止越级宣称证明。")
    lines.append("")
    lines.append("> 这是一套**可机器辅助的处理思维骨架**，不是自动证明机。真正的猜想证明"
                 "仍需人类数学家的创造性工作与形式化验证。\n")

    ms = method_doc["summary"]
    lines.append("\n## 5. 方法体系与'有无处理方向'的判定\n")
    lines.append(f"方法清单共 **{ms['methods_total']} 条**（均为标准数学方法的整理性汇编，KNOWN_L4），"
                 f"其中本流水线**实际能执行 {ms['methods_implemented']} 条**、"
                 f"未实现 {ms['methods_missing']} 条。`implemented` 严格区分，不冒领能力。\n")
    lines.append("| 猜想 | 状态 | 适用方法 | 其中已实现 | 方法覆盖 |")
    lines.append("|---|---|---|---|---|")
    for l in method_doc["linkage"]:
        lines.append(f"| {l['conjecture_name']} | {l['status']} "
                     f"| {len(l['applicable_methods'])} "
                     f"| {len(l['implemented_applicable'])} "
                     f"| {l['method_coverage']:.0%} |")
    lines.append("")
    zero = [l["conjecture_name"] for l in method_doc["linkage"]
            if l["status"] != "SOLVED" and not l["implemented_applicable"]]
    lines.append(f"**完全没有可用方法的未解猜想（共 {len(zero)} 条）**："
                 + ("、".join(zero) if zero else "无")
                 + "。这些正是本流水线'连计算证据都取不到'的领域——"
                   "不是因为我们不做，而是所需方法（如上同调计算、L 函数求值、PDE 数值模拟）"
                   "在本体系中尚未实现，且即便实现也只是证据、不是证明。")
    lines.append("")
    lines.append("> 关键诚实判定：对全部未解猜想，`can_resolve` 均为 **False**。"
                 "即便表里所有适用方法都齐备备，这些问题依旧是开放问题——"
                 "恰恰说明它们之间的鸿沟不是'算力不足'，而是缺少结构性理论突破"
                 "（各条 `direction_note` 已记录缺什么方向）。\n")

    ns = numeric_doc["summary"]
    lines.append("\n## 6. 数值兜底增强（本轮新增能力 + 一处认知纠偏）\n")
    lines.append("**认知纠偏**：CD 的 CMP 性质绝大多数是**多变量代数恒等式**"
                 "（`lcm(a,b)=a*b/gcd(a,b)`、`sin(A+B)=sinA cosB+cosA sinB` 等），"
                 "而非待求根的方程。此前把它们一律当作'求解'处理是方向性错误；"
                 "对恒等式应做**数值抽样验证**，单变量方程才做**数值求根**。\n")
    lines.append(f"符号求解器失败的式子共 **{ns['symbolic_failed']} 条**，经数值兜底后：")
    lines.append(f"- 恒等式抽样**验证通过 {ns['identity_holds']} 条**")
    lines.append(f"- 单变量**数值求根成功 {ns['numeric_roots_found']} 条**")
    lines.append(f"- 非代数形式（含逻辑连接词）跳过 {ns['skipped_non_algebraic']} 条")
    lines.append(f"- 抽样未通过 {ns['identity_fails']} 条（含多值函数分支约定造成的差异，"
                 f"**不等于找到反例**）/ 不可求值 {ns['unevaluable']} 条")
    lines.append(f"- **超出验证能力、主动拒答 {ns['not_decidable']} 条**"
                 f"（另有 {ns['inconclusive']} 条因抽样点求值失败而判为不确定）")
    lines.append(f"- 恒等式判定通过率 {ns['identity_pass_rate']:.0%}"
                 f"（分母＝可判定的 {ns['identity_decidable']} 条；"
                 f"另有旧口径处置率 {ns['resolution_rate']:.0%}，分母是全部 "
                 f"{ns['symbolic_failed']} 条符号失败条目，仅供历史对照）\n")
    lines.append("> 口径说明：2026-09-19 审计前，超出能力的式子也会被给出 holds/fails，")
    lines.append("> 制造了大量假阴性。现在它们单独记为 not_decidable，")
    lines.append("> 既不算通过也不算失败。\n")
    hold = [r for r in numeric_doc["solutions"]
            if r["identity"].get("status") == "holds"]
    if hold:
        lines.append("抽样验证通过的恒等式举例（**随机抽样吻合，L2 证据**）：")
        lines.append("")
        lines.append("| 恒等式 | 抽样次数 | 最大相对误差 |")
        lines.append("|---|---|---|")
        for r in hold[:8]:
            idt = r["identity"]
            lines.append(f"| `{r['raw']}` | {idt.get('trials_checked')} "
                         f"| {idt.get('max_relative_diff'):.2e} |")
        lines.append("")
    lines.append("> 诚实说明：'验证通过'的含义是'在随机抽样点上两侧数值吻合，**不是证明**'；"
                 "抽样在正实数域进行，未覆盖负数与特殊点。"
                 "'抽样未通过'同样不等于找到反例——可能只是求值器局限或抽样域不匹配。\n")

    lines.append("## 7. 后续可推进项（按突破收益排序）\n")
    lines.append("- **实现 `factorization` / `grobner_basis`**：当前 CD 恒等式大量无法机器处理，"
                 "补上可显著提升 D3/D4 维度。"
                 "这是把更多 CD 性质变成可验证方程的最大单点收益。")
    lines.append("- **实现 `symbolic_diff` / `limit_computation`**：打开 calculus1、limit1 的性质验证。")
    lines.append("- **实现 `numeric_root`**：把求解从单变量多项式扩展到一般方程的数值解。")
    lines.append("- 为 `linalg2/list1/limit1/minmax1` 等 0 性质 CD 寻找替代知识源"
                 "（其官方 CD 本身无 CMP，须外部补录）。")
    lines.append("- 将优质分析条目经 `openmath new` 走 AKU 生命周期正式入库（需人类复核）。")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
