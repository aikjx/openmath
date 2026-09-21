# -*- coding: utf-8 -*-
"""千禧难题档案引擎：命题形式化 / 逻辑方程 / 套娃分解 / 有限影子。

设计原则（与全仓库的诚实红线一致，写在这里是因为这一块最容易越线）：

1. **不声称证明任何未解难题**。本模块只做三件事：把命题写成机器可读的逻辑方程、
   把命题递归拆成子命题树、在**有限影子**上跑真计算。

2. **有限影子（finite shadow）**是把"不可判定的无限命题"接到"可算的有限检验"上的
   唯一诚实接口。对每道题，我们明确写出：
     · 影子命题是什么（∀ 量化 restricted 到有限域）
     · 影子在多大范围内被检验了
     · **影子是否蕴含原命题**（`shadow_implies_full`）
   七道题里这个字段几乎全是 False——这正是"数值验证到 10^13 个零点仍不是证明"的
   形式化表达。把它写成字段而不是散文，是为了让它无处可藏、也无法被误读。

3. **套娃分解不假装终止**。递归到开放叶时如实记录 `kind='open'`，
   并统计 `n_open_leaves`。开放叶数不为 0 是**正常结果**，不是缺陷；
   把它写成 0 才是伪造。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# 一、七道千禧难题的形式化（逻辑方程）
# ---------------------------------------------------------------------------
# 每题给出：
#   formula            人类可读的一阶/高阶逻辑表述
#   quantifiers        量词结构（机器可读）
#   predicate          待证谓词
#   negation           反命题（用于证伪通道：找到一个反例即否证）
#   finite_shadow      有限影子命题
#   shadow_implies_full 影子是否蕴含原命题
#   status             SOLVED / UNSOLVED / DISPUTED
#
# `status` 与 `proof_claimed` 一律如实填写；本模块**从不**把它们改成 SOLVED。

MILLENNIUM: List[Dict[str, Any]] = [
    {
        "id": "RH",
        "name": "黎曼猜想 Riemann Hypothesis",
        "domain": "解析数论",
        "prize": True,
        "status": "UNSOLVED",
        "formula": "∀ρ [ ζ(ρ)=0 ∧ 0<Re ρ<1 ] → Re ρ = 1/2",
        "quantifiers": [
            {"kind": "forall", "var": "ρ", "domain": "ζ 的非平凡零点（无限集）"},
        ],
        "predicate": "Re ρ = 1/2",
        "domain_constraint": "ζ(ρ)=0 ∧ 0<Re ρ<1",
        "negation": "∃ρ : ζ(ρ)=0 ∧ 0<Re ρ<1 ∧ Re ρ ≠ 1/2",
        "finite_shadow": (
            "∀ρ [ ζ(ρ)=0 ∧ 0<Re ρ<1 ∧ |Im ρ| ≤ T ] → Re ρ = 1/2，"
            "本引擎实测到 T=600（Hardy Z 符号变号计数 341 个零点，"
            "另用辐角原理独立复核得 N(600)=341，两法一致）"
        ),
        "shadow_bound": "T = 600（实测；不是能力上限，只是本轮跑到的高度）",
        "shadow_implies_full": False,
        "shadow_note": (
            "有限高度内无反例**不蕴含**全部零点都在临界线上：零点无限多，"
            "任何有限截断都可能漏掉第一个偏离的零点。这是数值验证与证明之间的本质鸿沟。"
        ),
        "statement": "黎曼 ζ 函数的所有非平凡零点实部均为 1/2。",
        "theoretical_gap": (
            "本质困难在于零点的全局分布与素数分布之间缺少可机器化的结构桥梁。"
            "Hilbert–Pólya 路线（把零点编码为某自伴算子的谱）至今未构造出该算子。"
        ),
    },
    {
        "id": "PNP",
        "name": "P vs NP",
        "domain": "计算复杂性理论",
        "prize": True,
        "status": "UNSOLVED",
        "formula": "P = NP ? （判定性问题；等价于 ∃L∈NP : L∉P 是否成立）",
        "quantifiers": [
            {"kind": "exists", "var": "L", "domain": "NP 语言族（无限族）"},
            {"kind": "forall", "var": "M", "domain": "确定性多项式时间图灵机（无限族）"},
        ],
        "predicate": "L ∉ P ⟺ ∀M ∀poly p : M 不能在 p(|x|) 内判定 L",
        "domain_constraint": "L ∈ NP",
        "negation": "P = NP ⟺ 每个 NP 语言都有多项式时间算法",
        "finite_shadow": (
            "对随机 3-SAT 实例，在子句/变量比 α 的网格上测量可满足率与 DPLL 求解代价；"
            "并在 n = 12 的小实例上用 2^n 全枚举逐例对账求解器的判定"
        ),
        "shadow_bound": "相变曲线 n = 40、α ∈ [3.0, 5.5]、每点 12 个实例；对账用 n = 12",
        "shadow_implies_full": False,
        "shadow_note": (
            "**本实验对 P vs NP 本身提供的证据为零**。有限规模的求解曲线既不蕴含 P≠NP，"
            "也不蕴含 P=NP：任何多项式算法都可能在 n > 10^6 才显现，"
            "而指数下界需要证明**所有**算法都不行，不是抽样几条实例能得到的。"
            "把它列进来的唯一理由是：它是本引擎能真实跑出来的、与问题同域的计算，"
            "而不是因为它能推进判定。"
        ),
        "statement": "是否所有 NP 问题都能在多项式时间内求解（P=NP）。",
        "theoretical_gap": (
            "缺乏区分'搜索'与'验证'复杂度的代数不变量；"
            "relativization / natural proofs / algebrization 三重障碍使经典对角化方法失效。"
        ),
    },
    {
        "id": "NS",
        "name": "纳维–斯托克斯存在性与光滑性",
        "domain": "偏微分方程",
        "prize": True,
        "status": "UNSOLVED",
        "formula": (
            "∀u₀∈C^∞_σ(R³) ∀T>0 ∃!u∈C^∞(R³×[0,T]) : "
            "∂ₜu+(u·∇)u = −∇p+νΔu, ∇·u=0, u(·,0)=u₀"
        ),
        "quantifiers": [
            {"kind": "forall", "var": "u₀", "domain": "光滑无散 initial data（无限维）"},
            {"kind": "forall", "var": "T", "domain": "(0,∞)"},
            {"kind": "exists", "var": "u", "domain": "C^∞ 解"},
        ],
        "predicate": "解全局存在且光滑（无有限时刻爆破）",
        "domain_constraint": "∇·u₀ = 0 且 u₀ 光滑速降",
        "negation": "∃u₀ ∃T*<∞ : 解在 T* 处失去光滑性",
        "finite_shadow": (
            "在周期盒上用迎风有限差分演化**一维** Burgers 方程（u₀ = −sin x），"
            "用特征线法估计激波时刻，与解析解 t* = −1/min u₀′ 对账"
        ),
        "shadow_bound": "一维，网格 n = 150 / 300；t ≤ 1.6；dt = 2e-4",
        "shadow_implies_full": False,
        "shadow_note": (
            "离散网格上不爆破**既不蕴含**连续问题不爆破（网格可能恰好抹掉奇性），"
            "也**不是**连续问题的反例。BKM 判据本身是**必要条件**方向的经典结果，"
            "我们只是在离散近似上观测它，不构成任何证明。"
        ),
        "statement": (
            "三维不可压缩 Navier–Stokes 方程对光滑初值是否存在全局光滑解（千禧版含 R³ 与周期两种表述）。"
        ),
        "theoretical_gap": (
            "缺少对非线性项 (u·∇)u 的、能控制所有尺度的先验估计；"
            "Leray–Hopf 弱解的唯一性与正则性仍是缺口。"
        ),
    },
    {
        "id": "BSD",
        "name": "BSD 猜想 Birch–Swinnerton-Dyer",
        "domain": "算术几何",
        "prize": True,
        "status": "UNSOLVED",
        "formula": "∀E/Q : ord_{s=1} L(E,s) = rank E(Q) 且 L^{(r)}(E,1)/r! = Ω·R·∏c_p·|Sha| / |E_tors|²",
        "quantifiers": [
            {"kind": "forall", "var": "E", "domain": "Q 上的椭圆曲线（无限族）"},
        ],
        "predicate": "解析秩 = 代数秩，且首项系数公式成立",
        "domain_constraint": "E/Q 为椭圆曲线",
        "negation": "∃E : ord_{s=1} L(E,s) ≠ rank E(Q) 或首项系数公式不成立",
        "finite_shadow": (
            "对若干具体曲线 E，计算 #E(F_p) 与 a_p = p+1−#E(F_p)，"
            "检验 Hasse 界 |a_p| ≤ 2√p（已知定理，作**校准件**），"
            "并给出截断的 L 值近似与已知代数秩对照"
        ),
        "shadow_bound": "p < 500；曲线 4 条",
        "shadow_implies_full": False,
        "shadow_note": (
            "Hasse 界是**已证明的定理**，在此只作求值器的校准件——"
            "能对上说明点计数代码没错，**不能**说明 BSD 成立。"
            "截断 L 值不等于 L(E,1)，有限个 p 的 a_p 也不决定解析秩。"
        ),
        "statement": "椭圆曲线 L 函数在 s=1 处的零点阶等于其有理点群的秩，且首项系数由算术不变量给出。",
        "theoretical_gap": (
            "已知结果（Gross–Zagier、Kolyvagin）只覆盖解析秩 ≤ 1 的情形；"
            "秩 ≥ 2 时无一般性结果，Sha 的有限性本身也未解决。"
        ),
    },
    {
        "id": "HODGE",
        "name": "霍奇猜想 Hodge Conjecture",
        "domain": "代数几何",
        "prize": True,
        "status": "UNSOLVED",
        "formula": "∀X 光滑射影代数簇 ∀p : H^{2p}(X,Q) ∩ H^{p,p}(X) = span_Q{[Z] : Z 为余维 p 的代数闭链}",
        "quantifiers": [
            {"kind": "forall", "var": "X", "domain": "光滑射影代数簇（无限族）"},
            {"kind": "forall", "var": "p", "domain": "0 ≤ p ≤ dim X"},
        ],
        "predicate": "每个 (p,p) 型有理 Hodge 类都是代数闭链类的有理线性组合",
        "domain_constraint": "X 光滑射影／C",
        "negation": "∃X ∃p ∃ Hodge 类不在代数闭链类张成的空间内",
        "finite_shadow": (
            "在有限单纯复形上做**组合 Hodge**（有理系数的上链复形 + 拉普拉斯），"
            "检验 Betti 数 b_k 与调和 k-形式维数 dim H^k_Δ 是否相等（Hodge 同构的离散类比）"
        ),
        "shadow_bound": "复形 ≤ 3 维，单形数 ≤ 54（S²: 4+6+4；T²: 9+27+18；S³: 5+10+10+5）",
        "shadow_implies_full": False,
        "shadow_note": (
            "这是**离散类比**，不是霍奇猜想本身：有限单纯复形没有 (p,p) 型分解，"
            "也没有代数闭链的概念。b_k = dim H^k_Δ 是线性代数恒等式，"
            "能对上是**计算正确性的校准**，与猜想无关。"
        ),
        "statement": "射影代数簇上的有理 (p,p) 型 Hodge 类是否都是代数闭链类的有理组合。",
        "theoretical_gap": (
            "缺少把 Hodge 类实现为代数闭链的构造性方法；"
            "即便 Lefschetz (1,1) 定理已知，p ≥ 2 时无对应工具。"
        ),
    },
    {
        "id": "YM",
        "name": "杨–米尔斯质量间隙 Yang–Mills Mass Gap",
        "domain": "数学物理",
        "prize": True,
        "status": "UNSOLVED",
        "formula": "∀ 紧单规范群 G ∃Δ>0 : 四维 Yang–Mills 理论的谱在 (0,Δ) 上为空",
        "quantifiers": [
            {"kind": "forall", "var": "G", "domain": "紧单李群"},
            {"kind": "exists", "var": "Δ", "domain": "(0,∞)"},
        ],
        "predicate": "真空与第一激发态之间存在正的质量间隙 Δ",
        "domain_constraint": "四维欧氏/闵氏 Yang–Mills，经典解已构造",
        "negation": "谱在 0 处无间隙（存在任意低能激发）",
        "finite_shadow": None,
        "shadow_bound": None,
        "shadow_implies_full": False,
        "shadow_note": (
            "**本题本引擎没有可算方面**。原因不是没做，而是问题的前提——"
            "四维量子 Yang–Mills 测度的构造——本身尚未完成，"
            "在测度都不存在的情况下不存在可计算的谱。"
            "格点 QCD 数值模拟属于未实现的 `lattice_qcd_numeric`，"
            "且即便实现也只是有限格点上的 L2 证据。此处如实留空，不编造实验。"
        ),
        "statement": "证明四维量子 Yang–Mills 理论存在质量间隙（千禧大奖的精确表述要求同时构造该理论）。",
        "theoretical_gap": (
            "四维量子规范场论的严格构造（Wightman/Osterwalder–Schrader 公理）本身未完成；"
            "这是比质量间隙更前置的障碍。"
        ),
    },
    {
        "id": "POINCARE",
        "name": "庞加莱猜想 Poincaré Conjecture",
        "domain": "几何拓扑",
        "prize": True,
        "status": "SOLVED",
        "formula": "∀M 闭三维流形 : π₁(M)=0 → M ≅ S³",
        "quantifiers": [
            {"kind": "forall", "var": "M", "domain": "闭三维流形"},
        ],
        "predicate": "单连通 ⇒ 同胚于 S³",
        "domain_constraint": "M 为闭（紧致无边界）三维流形",
        "negation": "∃ 单连通闭三维流形不同胚于 S³",
        "finite_shadow": (
            "对有限三角化的三维闭流形，检验同调型必要条件：H₀=Z, H₁=0, H₂=0, H₃=Z"
        ),
        "shadow_bound": "三角化顶点数 ≤ 20",
        "shadow_implies_full": False,
        "shadow_note": (
            "同调条件**只是必要不充分**：存在同调球面（homology sphere）"
            "其 H_* 与 S³ 相同但基本群非平凡（如 Poincaré 同调球面）。"
            "本题已由 Perelman 证明（2002–2003，基于 Hamilton 的 Ricci 流），"
            "此处的有限检验只用于确认同调计算代码正确，**不重复证明**。"
        ),
        "statement": "任何单连通的闭三维流形都同胚于三维球面。",
        "proof_by": "Perelman (2002–2003)，Ricci 流 + 手术；本仓库不声称贡献。",
        "theoretical_gap": None,
    },
]

MILLENNIUM_BY_ID = {m["id"]: m for m in MILLENNIUM}


# ---------------------------------------------------------------------------
# 二、套娃分解：把命题递归拆成子命题树
# ---------------------------------------------------------------------------
@dataclass
class Claim:
    """命题树上的一个节点。

    kind ∈ {root, theorem, computable, open, decomposition}
      theorem      已证定理（闭合叶，带出处）
      computable   本引擎可算的有限检验（闭合叶，带实验 id）
      open         开放叶 —— **递归在此停止但未闭合**，必须如实保留
    """
    id: str
    text: str
    kind: str
    depth: int
    evidence: str = ""
    status: str = "OPEN"          # CLOSED_THEOREM / CLOSED_COMPUTABLE / OPEN
    children: List["Claim"] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "text": self.text, "kind": self.kind,
            "depth": self.depth, "status": self.status,
            "evidence": self.evidence, "note": self.note,
            "children": [c.to_dict() for c in self.children],
        }


def _leaf_counts(node: Claim) -> Dict[str, int]:
    """统计叶节点分布。开放叶不为 0 是**正常结果**。"""
    if not node.children:
        key = "theorem" if node.status == "CLOSED_THEOREM" else (
            "computable" if node.status == "CLOSED_COMPUTABLE" else "open")
        return {key: 1, "total": 1}
    out: Dict[str, int] = {"total": 0}
    for c in node.children:
        sub = _leaf_counts(c)
        for k, v in sub.items():
            out[k] = out.get(k, 0) + v
    return out


def _max_depth(node: Claim) -> int:
    return max([node.depth] + [_max_depth(c) for c in node.children] or [node.depth])


def decompose(problem_id: str) -> Claim:
    """对一道题做套娃分解，返回命题树根。

    分解的结构统一为三层，第三层以下的展开由 `_DEEP` 表逐题给出；
    展开到 `kind='open'` 就停 —— 不假装能继续拆下去。
    """
    m = MILLENNIUM_BY_ID[problem_id]
    root = Claim(id=f"{problem_id}.0", text=m["formula"], kind="root",
                 depth=0, evidence=m.get("shadow_note", ""),
                 status="OPEN")

    spec = _DECOMPOSITION.get(problem_id, [])
    counter = [0]

    def _new_id() -> str:
        counter[0] += 1
        return f"{problem_id}.{counter[0]}"

    def _build(node_spec: Dict[str, Any], depth: int) -> Claim:
        nid = _new_id()
        kind = node_spec["kind"]
        status = {
            "theorem": "CLOSED_THEOREM",
            "computable": "CLOSED_COMPUTABLE",
            "open": "OPEN",
        }.get(kind, "OPEN")
        node = Claim(id=nid, text=node_spec["text"], kind=kind, depth=depth,
                     status=status, evidence=node_spec.get("evidence", ""),
                     note=node_spec.get("note", ""))
        for ch in node_spec.get("children", []):
            node.children.append(_build(ch, depth + 1))
        return node

    for s in spec:
        root.children.append(_build(s, 1))
    return root


# 逐题的分解规格。`open` 叶是**故意保留**的：它们就是"我们不知道怎么往下走"的地方。
_DECOMPOSITION: Dict[str, List[Dict[str, Any]]] = {
    "RH": [
        {"kind": "computable", "text": "临界线上的零点计数 vs Riemann–von Mangoldt 公式 N(T) 对账",
         "evidence": "实验 zeta_zero_count：Hardy Z 符号变号数 vs N(T)",
         "note": "这是**计数**对账，不是零点定位：能对上说明计数方法自洽，不说明零点都在临界线上。"},
        {"kind": "computable", "text": "ξ(s) 函数方程 ξ(s)=ξ(1−s) 的数值检验",
         "evidence": "实验 xi_functional_equation",
         "note": "函数方程是**已知定理**，此处只作求值器校准。"},
        {"kind": "open", "text": "Hilbert–Pólya：构造自伴算子使其谱 = 零点虚部",
         "note": "自 1910s 提出，至今无构造。这是本题最深的开放叶。",
         "children": [
             {"kind": "open", "text": "L1.1 该算子必须作用在什么 Hilbert 空间上",
              "note": "空间本身未定；不同候选（如 Berry–Keating 的 xp）都不完备。",
              "children": [
                  {"kind": "open", "text": "L1.1.1 边界条件/量子化条件如何选才能给出正确的零点密度",
                   "note": "再往下仍是开放——这就是'递归不终止'的实例。"},
              ]},
             {"kind": "open", "text": "L1.2 即便构造出来，如何证明谱**完全**等于零点集（而非只含部分）",
              "note": "自伴性只保证谱实，不保证与零点集一一对应。"},
             {"kind": "theorem", "text": "L1.3 类比：Selberg 迹公式把 Riemann 曲面的 Laplacian 谱与素数型长度联系起来",
              "evidence": "已知定理", "note": "这条**正是** Hilbert–Pólya 思路的可行性证据，但也说明差距在哪：Selberg 情形有现成的几何对象。"},
         ]},
        {"kind": "open", "text": "零点分布与随机矩阵（GUE）统计吻合的**原因**",
         "note": "Odlyzko 的数值吻合极好，但'吻合'本身不是定理，也没有被提升为证明。",
         "children": [
             {"kind": "theorem", "text": "L2.1 Montgomery–Dyson：零点对关联的极限分布 = GUE 的关联函数",
              "evidence": "数值/部分结果（Montgomery 定理只覆盖支撑在测试的受限类）",
              "note": "注意：Montgomery 的结果是**条件性且受限**的，常被过度引述为'已证明 GUE'。"},
             {"kind": "open", "text": "L2.2 从统计吻合到逐点结论（Re ρ = 1/2）的桥",
              "note": "统计性质是集合层面的，猜想是逐点的——两者之间**没有已知的推理通道**。这是本叶不闭合的根本原因。"},
         ]},
        {"kind": "theorem", "text": "Hardy 定理：临界线上有无穷多个零点",
         "evidence": "已知定理（1914）",
         "note": "无穷多 ≠ 全部。这条常被误引为'接近证明'，实则差得很远。"},
        {"kind": "theorem", "text": "平凡零点 ζ(−2n)=0 由函数方程直接推出",
         "evidence": "已知定理", "note": "与猜想本身无关，只作校准。"},
    ],
    "PNP": [
        {"kind": "computable", "text": "随机 3-SAT 在 α 网格上的 DPLL 代价曲线与相变位置",
         "evidence": "实验 sat_phase_transition",
         "note": "相变现象是**经验事实**，对 P vs NP 的判定价值为零。"},
        {"kind": "open", "text": "构造能区分 P 与 NP 的代数/几何不变量（GCT 路线）",
         "note": "需要把永久式 vs 行列式的表示论障碍推广到一般情形，未解决。",
         "children": [
             {"kind": "theorem", "text": "L1.1 Valiant：永久式是 VNP-完全的，行列式在 VP 内",
              "evidence": "已知定理（1979）", "note": "这是 GCT 的起点：把 P vs NP 类比成 VP vs VNP。"},
             {"kind": "open", "text": "L1.2 把永久式/行列式的表示论障碍（occurrence obstruction）推广到一般情形",
              "note": "已知该路线在**具体子类上已被证否**（见下一层）。",
              "children": [
                  {"kind": "theorem", "text": "L1.2.1 已证否：occurrence obstruction 不足以分离 VP 与 VNP",
                   "evidence": "已知不可能性结果",
                   "note": "**这是套娃的关键节点**：一条曾被寄予厚望的路线已被证明走不通，"
                          "于是'构造不变量'这个开放叶下面挂的是一条**已证的否定**，不是空白。"},
                  {"kind": "open", "text": "L1.2.2 是否存在其他类型的表示论障碍",
                   "note": "开放。递归在此不终止。"},
              ]},
         ]},
        {"kind": "open", "text": "绕过 relativization / natural proofs / algebrization 三重障碍",
         "note": "三重障碍都是**已证明的不可能性结果**：某类方法必然失败。要绕过必须换方法族。",
         "children": [
             {"kind": "theorem", "text": "L2.1 Baker–Gill–Solovay：存在 oracle A 使 P^A=NP^A，也存在 B 使 P^B≠NP^B",
              "evidence": "已知定理（1975）", "note": "⇒ 任何**相对化**的方法都证不了 P≠NP。"},
             {"kind": "theorem", "text": "L2.2 Razborov–Rudich：'自然证明'在标准密码学假设下无法分离 P 与 NP",
              "evidence": "已知定理（1997）", "note": "⇒ 一大类组合下界方法被排除。"},
             {"kind": "theorem", "text": "L2.3 Aaronson–Wigderson：algebrization 障碍",
              "evidence": "已知定理（2008）", "note": "⇒ 连'算术化 + 相对化'的组合方法也被排除。"},
             {"kind": "open", "text": "L2.4 是否存在不属于上述三类的证明技术",
              "note": "开放。注意 IP=PSPACE、PCP 定理这类'非相对化'结果确实存在，"
                      "说明障碍不是绝对的——但至今无人把它们转化成 P≠NP 的证明。"},
         ]},
        {"kind": "theorem", "text": "Ladner 定理：若 P≠NP 则存在 NP-中间问题",
         "evidence": "已知定理（1975）", "note": "条件性结果。"},
        {"kind": "theorem", "text": "Cook–Levin：SAT 是 NP-完全的",
         "evidence": "已知定理（1971）", "note": "归约框架，不是判定。"},
    ],
    "NS": [
        {"kind": "computable", "text": "周期盒上二维涡量/Burgers 有限差分演化，监测 BKM 型量",
         "evidence": "实验 ns_finite_difference",
         "note": "二维情形已知全局正则；本实验在二维上不爆破是**预期结果**，不含信息量。"},
        {"kind": "open", "text": "三维非线性项的跨尺度先验估计",
         "note": "核心缺口：缺少控制 (u·∇)u 的先验界。",
         "children": [
             {"kind": "theorem", "text": "L1.1 Ladyzhenskaya–Prodi–Serrin 正则性判据：u∈L^p_t L^q_x 且 2/p+3/q≤1 ⇒ 正则",
              "evidence": "已知定理", "note": "把正则性归约到某个范数的可积性——但那个可积性本身证不出来。"},
             {"kind": "open", "text": "L1.2 上述判据所需的 L^p_t L^q_x 界如何从方程自身推出",
              "note": "这是'先验估计'缺口的具体位置。递归不终止。"},
             {"kind": "open", "text": "L1.3 能量从大尺度向小尺度级联是否会在有限时间把能量集中到一点",
              "note": "物理直觉（Kolmogorov 级联）与严格证明之间无桥梁。"},
         ]},
        {"kind": "theorem", "text": "Leray–Hopf 弱解全局存在",
         "evidence": "已知定理（1934）", "note": "弱解存在但唯一性与正则性未解决。"},
        {"kind": "theorem", "text": "Beale–Kato–Majda 爆破判据",
         "evidence": "已知定理（1984）", "note": "必要条件：若爆破则 ∫‖ω‖_∞ dt = ∞。是判据不是结论。"},
        {"kind": "open", "text": "是否存在自相似爆破解（数值上已有候选，未证实）",
         "note": "数值候选解的存在性与严格性之间仍有距离。"},
    ],
    "BSD": [
        {"kind": "computable", "text": "点计数 #E(F_p) 与 Hasse 界 |a_p| ≤ 2√p 检验",
         "evidence": "实验 ec_point_count",
         "note": "Hasse 界是**定理**，作校准件：能对上说明点计数代码正确。"},
        {"kind": "theorem", "text": "秩 0 与秩 1 情形的 BSD（Kolyvagin / Gross–Zagier）",
         "evidence": "已知定理（1980s）", "note": "只覆盖解析秩 ≤ 1。"},
        {"kind": "open", "text": "秩 ≥ 2 的情形",
         "note": "无一般性结果；Sha 的有限性本身也未解决。"},
        {"kind": "open", "text": "Sha(E) 的有限性",
         "note": "连有限性都未证明，首项系数公式无从谈起。",
         "children": [
             {"kind": "theorem", "text": "L1.1 若 L(E,1)≠0 则 E(Q) 有限且 Sha 有限（Kolyvagin）",
              "evidence": "已知定理", "note": "仅覆盖秩 0。"},
             {"kind": "open", "text": "L1.2 秩 ≥ 2 时 Sha 的有限性",
              "note": "开放；首项系数公式里 |Sha| 这一项在此情形下连定义是否良好都不确定。"},
         ]},
    ],
    "HODGE": [
        {"kind": "computable", "text": "有限单纯复形上的组合 Hodge：b_k vs dim H^k_Δ",
         "evidence": "实验 combinatorial_hodge",
         "note": "离散类比，与猜想无逻辑关系，只作线性代数代码校准。"},
        {"kind": "theorem", "text": "Lefschetz (1,1) 定理：p=1 情形成立",
         "evidence": "已知定理", "note": "p ≥ 2 时无对应工具。"},
        {"kind": "open", "text": "p ≥ 2 的 Hodge 类如何代数化",
         "note": "缺少构造性方法。",
         "children": [
             {"kind": "theorem", "text": "L1.1 Lefschetz (1,1) 定理的证明依赖指数序列与 Picard 群",
              "evidence": "已知定理", "note": "p=1 时可用除子/线丛；p≥2 没有对应的'余维 p 闭链的上同调理论'。"},
             {"kind": "open", "text": "L1.2 是否存在 p≥2 的类似物（如某种高阶 Picard）",
              "note": "开放。将来的'母题（motive）'理论被视为候选框架，但尚未完成。"},
             {"kind": "open", "text": "L1.3 已知的**反例方向**：是否存在非代数的 Hodge 类（若存在则猜想为假）",
              "note": "迄今未找到反例；也没能证明不存在。这个'双向都走不通'的状态本身就是缺口。"},
         ]},
    ],
    "YM": [
        {"kind": "open", "text": "四维量子 Yang–Mills 测度的严格构造",
         "note": "**前置障碍**：连理论本身都还没构造出来，质量间隙无从谈起。",
         "children": [
             {"kind": "theorem", "text": "L1.1 二、三维量子规范场论已有严格构造",
              "evidence": "已知（部分情形）", "note": "维数降到 3 以下才可行——四维恰恰是临界且最难的。"},
             {"kind": "open", "text": "L1.2 四维的构造：连续极限下测度是否存在",
              "note": "开放。这正是千禧表述把'构造'与'质量间隙'**并列**为要求的原因。"},
             {"kind": "open", "text": "L1.3 重正化群的非微扰控制",
              "note": "微扰重正化已成熟，非微扰控制未解决。"},
         ]},
        {"kind": "open", "text": "存在该测度后，证明谱在 (0,Δ) 上为空",
         "note": "依赖上一条。",
         "children": [
             {"kind": "open", "text": "L2.1 如何定义'谱'（需要先有 Hilbert 空间与哈密顿量）",
              "note": "依赖 L1.2。递归在此真正无底：上一条不解决，这一条连问题都没定义清楚。"},
         ]},
        {"kind": "theorem", "text": "经典 Yang–Mills 方程的解存在",
         "evidence": "已知（经典层面）", "note": "经典 ≠ 量子化。"},
    ],
    "POINCARE": [
        {"kind": "computable", "text": "有限三角化三维闭流形的同调必要条件检验",
         "evidence": "实验 homology_sphere_check",
         "note": "**必要不充分**：同调球面反例存在（Poincaré 同调球面）。"},
        {"kind": "theorem", "text": "Perelman 的证明（Ricci 流 + 手术）",
         "evidence": "已解决 2002–2003", "note": "本仓库不声称贡献。"},
        {"kind": "theorem", "text": "Thurston 几何化猜想（同为 Perelman 所证）",
         "evidence": "已知定理", "note": "庞加莱猜想是其推论。"},
    ],
}


def build_dossier_structure() -> Dict[str, Any]:
    """产出七题的形式化 + 套娃树（不含实验；实验由 experiments.py 侧填充）。"""
    out: Dict[str, Any] = {"problems": []}
    for m in MILLENNIUM:
        tree = decompose(m["id"])
        counts = _leaf_counts(tree)
        out["problems"].append({
            **{k: v for k, v in m.items()},
            "decomposition": tree.to_dict(),
            "leaf_counts": counts,
            "decomposition_depth": _max_depth(tree),
        })
    out["summary"] = {
        "n_problems": len(MILLENNIUM),
        "n_unsolved": sum(1 for m in MILLENNIUM if m["status"] == "UNSOLVED"),
        "n_solved": sum(1 for m in MILLENNIUM if m["status"] == "SOLVED"),
        "n_with_finite_shadow": sum(1 for m in MILLENNIUM if m.get("finite_shadow")),
        "n_shadow_implies_full": sum(1 for m in MILLENNIUM if m.get("shadow_implies_full")),
        "total_open_leaves": sum(_leaf_counts(decompose(m["id"])).get("open", 0)
                                 for m in MILLENNIUM),
    }
    return out
