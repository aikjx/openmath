"""
structure.py —— 有限结构计算（finite structure computation，纯标准库）

本模块为填补「结构计算 / structure_computation」范式（此前完全空白，0 已实现）而写。

能力范围（**诚实声明，不得夸大**）：
  1. 有限群：由 Cayley 表判定群公理、求单位元/逆元/元素阶/中心/交换性/子群。
  2. 有限单纯复形与 CW/Δ-复形：构造链复形，在**域系数**（有理数 Q 与 GF(p)）上
     计算同调的秩（Betti 数）。
  3. 挠元（torsion）检测：用泛系数定理递归反演各素数 p 的 p-挠元**个数**。

边界（必须明示）：
  - 只处理**有限**对象；无限群、连续空间一律不在射程内。
  - 同调只支持域系数。p-挠元可检测**个数**，但**无法确定指数 k**
    （即能报"存在 Z_{2^k} 型挠"，不能判定 k 是否为 1）。
  - 与霍奇猜想所需的上同调（复射影代数簇的 Hodge 分解、(p,p) 类与代数闭链）
    相距极远；与 BSD 所需的椭圆曲线秩（Mordell-Weil 群）**不是同一回事**。
    本模块给不出这两者的任何结论。
  - 子群枚举默认完备（循环子群的 join 闭包，与阶无关）；只有闭包规模超过
    `subgroup_cap` 时才降级为"由 ≤3 个生成元生成的子群"（此时结果记为
    partial，不冒充完整分类）。
  - 有限群的**构造**只覆盖直积、循环群的扭曲扩张（Z_m ⋊_κ Z_2）、半直积与
    Pauli 群等显式构造；不声称对任一阶给出了同构分类的完备列表。
"""

from __future__ import annotations

import itertools
import math
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCOPE_NOTE = (
    "有限结构计算：有限群（Cayley 表）+ 有限链复形的域系数同调 + p-挠元个数检测。"
    "不含无限结构、不含整指数判定、不含椭圆曲线秩、不含 Hodge 分解。"
)

TORSION_NOTE = (
    "挠元由泛系数定理递归得到："
    "dim_Fp H_i = rank_Q H_i + t_p(H_i) + t_p(H_{i-1})，自 i=0 起递推。"
    "只能得到 p-挠元的个数，**无法确定 Z_{p^k} 的指数 k**。"
)

__all__ = [
    "SCOPE_NOTE", "TORSION_NOTE",
    "ChainComplex", "homology_summary", "euler_characteristic_from_betti",
    "rank_rational", "rank_gf",
    "analyze_group", "cyclic_additive_group", "symmetric_group", "dihedral_group",
    "STANDARD_COMPLEXES", "STANDARD_GROUPS",
    "KNOWN_BETTI", "KNOWN_TORSION", "KNOWN_GROUP_FACTS",
]


# ===========================================================================
# 1. 线性代数：域上的秩（Q 与 GF(p)）
# ===========================================================================
def _rank(rows: List[List[Any]], zero: Any, inv, sub, mul) -> int:
    """通用高斯消元求秩（行阶梯形）。rows 为数值矩阵，不修改入参。"""
    m = [r[:] for r in rows]
    if not m:
        return 0
    ncol = len(m[0])
    rank = 0
    col = 0
    row = 0
    while col < ncol and row < len(m):
        # 找主元
        piv = None
        for r in range(row, len(m)):
            if m[r][col] != zero:
                piv = r
                break
        if piv is None:
            col += 1
            continue
        m[row], m[piv] = m[piv], m[row]
        pv = inv(m[row][col])
        m[row] = [mul(pv, x) for x in m[row]]
        for r in range(len(m)):
            if r != row and m[r][col] != zero:
                f = m[r][col]
                m[r] = [sub(a, mul(f, b)) for a, b in zip(m[r], m[row])]
        row += 1
        col += 1
        rank += 1
    return rank


def rank_rational(matrix: Sequence[Sequence[int]]) -> int:
    """有理数域 Q 上的矩阵秩（用 Fraction，精确无浮点误差）。"""
    rows = [[Fraction(int(x)) for x in r] for r in matrix]
    if not rows:
        return 0
    return _rank(
        rows, Fraction(0),
        lambda v: Fraction(1) / v,
        lambda a, b: a - b,
        lambda f, v: f * v,
    )


def rank_gf(matrix: Sequence[Sequence[int]], p: int) -> int:
    """有限域 GF(p)（p 为素数）上的矩阵秩，用模逆实现除法。"""
    if p <= 1 or not _is_prime(p):
        raise ValueError(f"GF(p) 要求 p 为素数，收到 p={p}")
    rows = [[int(x) % p for x in r] for r in matrix]
    if not rows:
        return 0

    def inv(v: int) -> int:
        return pow(v % p, p - 2, p)  # 费马小定理

    def mul(f: int, v: int) -> int:
        return (f * v) % p

    def sub(a: int, b: int) -> int:
        return (a - b) % p

    return _rank(rows, 0, inv, sub, mul)


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


# ===========================================================================
# 2. 链复形与同调
# ===========================================================================
class ChainComplex:
    """
    有限链复形：... -> C_k --∂_k--> C_{k-1} -> ... -> C_0

    gens[k]      : 第 k 维生成元的名字列表（k = 0..dim）
    boundary[k]  : 长度 len(gens[k]) 的列表，第 j 项为 list[(coeff, index)]，
                   index 指向 gens[k-1]，即 ∂_k(gens[k][j]) = Σ coeff * gens[k-1][index]
    边界矩阵约定：行 = ∂ 的下游(k-1 维)生成元，列 = k 维生成元。
    整数系数即可；域系数在求秩时按域约化。
    """

    def __init__(self, name: str, gens: List[List[str]],
                 boundary: Dict[int, List[List[Tuple[int, int]]]]):
        self.name = name
        self.gens = gens
        self.boundary = boundary

    # -- 构造 ---------------------------------------------------------------
    @classmethod
    def from_simplicial(cls, name: str, simplices: Iterable[Sequence[Any]]):
        """由单纯形列表构造（自动向下封闭补齐所有面）。"""
        # 记法约定：含 k 个顶点的面是 **k-1 维**单形（顶点为 0 维、边为 1 维…）
        face_set: Dict[int, List[Tuple]] = {}
        for s in simplices:
            s = tuple(sorted(s, key=lambda x: str(x)))
            for nv in range(1, len(s) + 1):
                for face in itertools.combinations(s, nv):
                    d = nv - 1  # 面 = face，其维数为 nv-1
                    face_set.setdefault(d, [])
                    if face not in face_set[d]:
                        face_set[d].append(face)
        dim = max(face_set) if face_set else 0
        gens = [[str(f) for f in face_set.get(k, [])] for k in range(dim + 1)]
        index_of = [{f: i for i, f in enumerate(face_set.get(k, []))}
                    for k in range(dim + 1)]

        boundary: Dict[int, List[List[Tuple[int, int]]]] = {}
        for k in range(1, dim + 1):
            cols = []
            for simp in face_set.get(k, []):
                col = []
                for j in range(len(simp)):
                    face = simp[:j] + simp[j + 1:]
                    col.append(((-1) ** j, index_of[k - 1][face]))
                cols.append(col)
            boundary[k] = cols
        return cls(name, gens, boundary)

    @classmethod
    def from_cw(cls, name: str, gens: List[List[str]],
                boundary_spec: Dict[int, Dict[str, List[Tuple[int, str]]]]):
        """
        由 CW / Δ-复形构造：直接给出每个生成元的边界线性组合。
        boundary_spec[k][g] = [(coeff, lower_gen_name), ...]
        例（环面 T²）：gens=[[v],[a,b,c],[U,L]]，
            ∂_2 U = 1*a + 1*b + (-1)*c；∂_2 L = -1*a -1*b + 1*c
        """
        index_of = [{g: i for i, g in enumerate(gens[k])} for k in range(len(gens))]
        boundary: Dict[int, List[List[Tuple[int, int]]]] = {}
        for k in range(1, len(gens)):
            spec = boundary_spec.get(k, {})
            cols = []
            for g in gens[k]:
                col = []
                for coeff, low in spec.get(g, []):
                    if low not in index_of[k - 1]:
                        raise ValueError(f"未知生成元 {low!r}（第 {k-1} 维）")
                    col.append((int(coeff), index_of[k - 1][low]))
                cols.append(col)
            boundary[k] = cols
        return cls(name, gens, boundary)

    # -- 基本量 -------------------------------------------------------------
    @property
    def dim(self) -> int:
        return len(self.gens) - 1

    def ranks_of_generators(self) -> List[int]:
        return [len(g) for g in self.gens]

    def boundary_rank(self, k: int, field: Any) -> int:
        """∂_k 的秩。field = "Q" 或 int 素数 p。"""
        cols = self.boundary.get(k, [])
        nrow = len(self.gens[k - 1]) if k >= 1 else 0
        if not cols or nrow == 0:
            return 0
        matrix = [[0] * len(cols) for _ in range(nrow)]
        for j, col in enumerate(cols):
            for coeff, i in col:
                matrix[i][j] += coeff
        return rank_rational(matrix) if field == "Q" else rank_gf(matrix, field)

    def betti(self, field: Any) -> List[int]:
        """
        Betti 数 b_k = dim ker ∂_k - dim im ∂_{k+1}
                     = (n_k - rank ∂_k) - rank ∂_{k+1}}
        """
        n = self.ranks_of_generators()
        r = {k: self.boundary_rank(k, field) for k in range(1, self.dim + 1)}
        out = []
        for k in range(self.dim + 1):
            down = r.get(k, 0)
            up = r.get(k + 1, 0)
            out.append(n[k] - down - up)
        return out

    def euler_from_chain(self) -> int:
        """交错和 Σ(-1)^k n_k（按链群维数），用于与 Σ(-1)^k b_k 对照自检。"""
        return sum(((-1) ** k) * len(g) for k, g in enumerate(self.gens))


def homology_summary(cx: ChainComplex, primes: Sequence[int] = (2, 3, 5, 7)) -> Dict[str, Any]:
    """在 Q 与 GF(p) 上算 Betti 数，并按泛系数定理递归推出各 p-挠元个数。"""
    bq = cx.betti("Q")
    per_prime = {}
    torsion_by_dim: Dict[int, Dict[int, int]] = {i: {} for i in range(len(bq))}
    for p in primes:
        bp = cx.betti(p)
        prev_t = 0
        t_list = []
        for i in range(len(bq)):
            tp = bp[i] - bq[i] - prev_t
            tp = max(tp, 0)  # 数值保护：理论上非负
            t_list.append(tp)
            if tp:
                torsion_by_dim[i][p] = tp
            prev_t = tp
        per_prime[p] = {"betti": bp, "torsion_counts": t_list}

    chi_chain = cx.euler_from_chain()
    chi_q = sum(((-1) ** i) * b for i, b in enumerate(bq))
    return {
        "name": cx.name,
        "dim": cx.dim,
        "generators_per_dim": cx.ranks_of_generators(),
        "betti_Q": bq,
        "per_prime": per_prime,
        "torsion_by_dim": {str(k): v for k, v in torsion_by_dim.items() if v},
        "euler_check": {
            "from_chain_groups": chi_chain,
            "from_betti_Q": chi_q,
            "consistent": chi_chain == chi_q,
        },
        "notes": {"scope": SCOPE_NOTE, "torsion": TORSION_NOTE},
    }


def euler_characteristic_from_betti(betti: Sequence[int]) -> int:
    return sum(((-1) ** i) * b for i, b in enumerate(betti))


# ===========================================================================
# 3. 标准复形（已知答案的检验件）
# ===========================================================================
def _build_point() -> ChainComplex:
    return ChainComplex.from_simplicial("点 point", [(0,)])


def _build_interval() -> ChainComplex:
    return ChainComplex.from_simplicial("区间 interval", [(0, 1)])


def _build_circle() -> ChainComplex:
    """S¹：三角形边界（3 顶点 3 边）。已知 b=[1,1]。"""
    return ChainComplex.from_simplicial("圆周 S¹", [(0, 1), (1, 2), (0, 2)])


def _build_wedge_of_two_circles() -> ChainComplex:
    """S¹∨S¹：两个三角形共用一个顶点。已知 b=[1,2]。"""
    return ChainComplex.from_simplicial("双环楔和 S¹∨S¹",
                                        [(0, 1), (1, 2), (0, 2), (2, 3), (3, 4), (2, 4)])


def _build_sphere() -> ChainComplex:
    """S²：四面体边界（4 顶点 6 边 4 面）。已知 b=[1,0,1]。"""
    return ChainComplex.from_simplicial(
        "球面 S²（四面体边界）",
        [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])


def _build_torus_cw() -> ChainComplex:
    """T²：标准 CW/Δ-复形。1 个顶点、3 条边 a,b,c、2 个面 U,L。已知 b=[1,2,1]。"""
    return ChainComplex.from_cw(
        "环面 T²（CW）",
        gens=[["v"], ["a", "b", "c"], ["U", "L"]],
        boundary_spec={
            1: {"a": [], "b": [], "c": []},
            2: {"U": [(1, "a"), (1, "b"), (-1, "c")],
                "L": [(-1, "a"), (-1, "b"), (1, "c")]},
        })


def _build_rp2_cw() -> ChainComplex:
    """RP²：标准 CW 结构，2-胞腔以度数 2 贴到 a 上。已知 Q: b=[1,0,0]，GF(2): b=[1,1,1]。"""
    return ChainComplex.from_cw(
        "实射影平面 RP²（CW）",
        gens=[["v"], ["a"], ["X"]],
        boundary_spec={1: {"a": []}, 2: {"X": [(2, "a")]}},
    )


STANDARD_COMPLEXES = {
    "point": _build_point,
    "interval": _build_interval,
    "circle": _build_circle,
    "wedge_two_circles": _build_wedge_of_two_circles,
    "sphere": _build_sphere,
    "torus": _build_torus_cw,
    "rp2": _build_rp2_cw,
}

# 已知 Betti 数（文献值，用作正确性判据）
KNOWN_BETTI: Dict[str, Dict[str, List[int]]] = {
    "point": {"Q": [1]},
    "interval": {"Q": [1, 0]},
    "circle": {"Q": [1, 1]},
    "wedge_two_circles": {"Q": [1, 2]},
    "sphere": {"Q": [1, 0, 1]},
    "torus": {"Q": [1, 2, 1], "GF2": [1, 2, 1]},
    "rp2": {"Q": [1, 0, 0], "GF2": [1, 1, 1]},
}
KNOWN_TORSION: Dict[str, Dict[str, Any]] = {
    "rp2": {"dim": 1, "prime": 2, "count": 1},
}


# ===========================================================================
# 4. 有限群
# ===========================================================================
def cyclic_additive_group(n: int) -> List[List[int]]:
    """Z/nZ 的加法 Cayley 表。"""
    if n <= 0:
        raise ValueError("n 必须为正")
    return [[(i + j) % n for j in range(n)] for i in range(n)]


def symmetric_group(n: int) -> Tuple[List[List[int]], List[Tuple[int, ...]]]:
    """对称群 S_n：返回 (Cayley 表, 元素列表)。复合约定：复合后作用的顺序（先 i 后 j）。"""
    elems = list(itertools.permutations(range(n)))
    idx = {e: i for i, e in enumerate(elems)}
    size = len(elems)
    table = [[0] * size for _ in range(size)]
    for i, a in enumerate(elems):
        for j, b in enumerate(elems):
            # 复合：(a∘b)(x) = a(b(x))
            c = tuple(a[b[x]] for x in range(n))
            table[i][j] = idx[c]
    return table, elems


def _subgroup_join_closure(op, n: int, identity: int,
                           subgroup_cap: int = 40000
                           ) -> Optional[List[Tuple[int, ...]]]:
    """完备枚举全部子群：循环子群在「join」下的闭包。

    为什么完备（这是恒等式，不是猜想、不是启发式）：对任意子群 H ≤ G，
        H = ⟨H⟩ = ⋁_{h ∈ H} ⟨h⟩
    即 H 恰好等于它自己全部元素所生成的循环子群的 join。因此只要初始集合
    含**全部**循环子群、且反复执行「与某个循环子群做 join」直到不动点，
    得到的集合就包含每一个子群。结合律保证 ⟨h1⟩∨⟨h2⟩∨…∨⟨hk⟩ 与加括号
    方式无关，所以"逐个并上循环子群"与"一次性并上全部"等价。

    为什么每个产物都是子群：闭包含单位元、对乘法封闭，且 G 有限 —— 对 a∈S，
    幂序列 a, a², … 必重复，a^k = a^m (k>m) ⇒ a^(k−m) = e ⇒ a^(k−m−1) = a⁻¹∈S。

    为什么终止：集合单调增长，且被 |Sub(G)| 界定。

    复杂度：约 |Sub(G)| × n 次闭包，取代旧版的 2^n 次子集枚举。这正是 16 阶
    群能被纳入的原因（旧版在 16 阶上约 2.8 s/群）。

    返回 None 表示闭包规模超过 subgroup_cap —— 调用方必须降级并如实标注，
    **不得**把截断结果当完备结果用。
    """
    def closure(seed: Iterable[int]) -> Tuple[int, ...]:
        s = {identity}
        s.update(seed)
        changed = True
        while changed:
            changed = False
            for a in list(s):
                for b in list(s):
                    c = op(a, b)
                    if c not in s:
                        s.add(c)
                        changed = True
        return tuple(sorted(s))

    cyc = {closure([g]) for g in range(n)}
    found = set(cyc)
    cyc_list = sorted(cyc)
    changed = True
    while changed:
        changed = False
        for h in list(found):
            for c in cyc_list:
                j = closure(list(h) + list(c))
                if j not in found:
                    found.add(j)
                    changed = True
                    if len(found) > subgroup_cap:
                        return None
    return sorted(found, key=lambda t: (len(t), t))


def analyze_group(table: Sequence[Sequence[int]], full_enum_cap: int = 14,
                  gen_subset_max: int = 3,
                  subgroup_cap: int = 40000) -> Dict[str, Any]:
    """
    由 Cayley 表判定并分析有限群。

    返回 群公理是否成立、单位元、逆元、元素阶、交换性、中心、子群列表。

    子群枚举默认走 `_subgroup_join_closure`（循环子群的 join 闭包），**与 n 无关
    地完备**，只在闭包规模超过 subgroup_cap 时才降级为"由 ≤gen_subset_max 个
    元素生成的子群"，此时结果标记为 partial ——**不冒充完整子群分类**。

    保留 `full_enum_cap` 参数仅为兼容旧调用；它现在只作为"闭包超限时是否还
    肯走老路"的兜底开关，不再决定完备性。
    """
    n = len(table)
    op = lambda i, j: table[i][j]

    # 闭包检查
    elements_ok = all(0 <= table[i][j] < n for i in range(n) for j in range(n))

    # 单位元
    identity = None
    for e in range(n):
        if all(op(e, x) == x and op(x, e) == x for x in range(n)):
            identity = e
            break

    # 结合律（O(n^3)）
    associative = True
    for a in range(n):
        for b in range(n):
            ab = op(a, b)
            for c in range(n):
                if op(ab, c) != op(a, op(b, c)):
                    associative = False
                    break
            if not associative:
                break
        if not associative:
            break

    # 逆元
    inverses: Dict[int, int] = {}
    inverses_ok = True
    if identity is not None:
        for a in range(n):
            inv = None
            for b in range(n):
                if op(a, b) == identity and op(b, a) == identity:
                    inv = b
                    break
            if inv is None:
                inverses_ok = False
                inverses[a] = -1
            else:
                inverses[a] = inv
    else:
        inverses_ok = False

    is_group = bool(elements_ok and identity is not None and associative and inverses_ok)

    abelian = all(op(i, j) == op(j, i) for i in range(n) for j in range(n))

    # 元素阶
    orders: List[int] = []
    for a in range(n):
        o, cur = 1, a
        while cur != identity and o <= n + 1:
            cur = op(cur, a)
            o += 1
        orders.append(o if cur == identity else -1)

    # 群的指数 = 全部元素阶的**最小公倍数**（不是最大值！）
    # 修正记录：早期版本把 exponent 取成 max(orders)，对 S3 会给出 3（正确值应为 lcm(2,3)=6）。
    # 该错误已于 2026-09-19 修正；旧值保留在 max_element_order 字段以免悄悄抹掉历史口径。
    def _lcm(a: int, b: int) -> int:
        return a // math.gcd(a, b) * b if a and b else 0

    exponent = None
    if orders and all(o > 0 for o in orders):
        ex = 1
        for o in orders:
            ex = _lcm(ex, o)
        exponent = ex
    max_element_order = max(orders) if orders and all(o > 0 for o in orders) else None

    # 中心
    center = [x for x in range(n) if all(op(x, y) == op(y, x) for y in range(n))]

    # 子群枚举
    subgroups: List[Tuple[int, ...]] = []
    subgroup_mode = "unknown"
    if identity is not None:
        def closure(seed: Iterable[int]) -> Tuple[int, ...] | None:
            s = set(seed)
            if identity not in s:
                s.add(identity)
            changed = True
            while changed:
                changed = False
                for a in list(s):
                    for b in list(s):
                        c = op(a, b)
                        if c not in s:
                            s.add(c)
                            changed = True
            return tuple(sorted(s))

        found: set = set()
        # 首选：循环子群 join 闭包（完备，且与 n 无关）
        complete = _subgroup_join_closure(op, n, identity,
                                          subgroup_cap=subgroup_cap)
        if complete is not None:
            subgroup_mode = "complete_join_closure_of_cyclic_subgroups"
            found = {s for s in complete if len(s) < n}   # 只收真子群
        elif n <= full_enum_cap:
            # 兜底一：闭包超限但群还小 —— 退回旧的子集枚举（仍然完备，只是慢）
            subgroup_mode = "complete_subset_enumeration"
            others = [x for x in range(n) if x != identity]
            for r in range(0, len(others) + 1):
                for combo in itertools.combinations(others, r):
                    cl = closure(combo)
                    if cl is not None and len(cl) < n:
                        found.add(cl)
        else:
            # 兜底二：**不完备**，必须如实标注
            subgroup_mode = f"generated_by_at_most_{gen_subset_max}_elements"
            others = [x for x in range(n) if x != identity]
            for r in range(1, min(gen_subset_max, len(others)) + 1):
                for combo in itertools.combinations(others, r):
                    cl = closure(combo)
                    if cl is not None and len(cl) < n:
                        found.add(cl)
        subgroups = sorted(found, key=lambda t: (len(t), t))

    # Lagrange 检验：子群阶须整除群阶
    lagrange_ok = all(n % len(s) == 0 for s in subgroups) if is_group else None

    return {
        "order": n,
        "is_group": is_group,
        "closure_ok": elements_ok,
        "associative": associative,
        "identity_found": identity is not None,
        "identity": identity,
        "inverses_exist": inverses_ok,
        "abelian": abelian,
        "center_size": len(center),
        "center": center,
        "element_orders": orders,
        "exponent": exponent,
        "max_element_order": max_element_order,
        "subgroup_enumeration_mode": subgroup_mode,
        "proper_subgroups_count": len(subgroups),
        "proper_subgroup_orders": sorted({len(s) for s in subgroups}),
        "proper_subgroups": [list(s) for s in subgroups],
        "lagrange_checked": lagrange_ok,
        "notes": {"scope": SCOPE_NOTE},
    }


def dihedral_group(n: int) -> Tuple[List[List[int]], List[Any]]:
    """二面体群 D_n（n 边形的对称群，阶 2n）。元素记 (r^k) 与 (s r^k)。"""
    # 元素 0..n-1 为旋转 r^k，n..2n-1 为反射 s r^k
    size = 2 * n
    table = [[0] * size for _ in range(size)]

    def mul(a: int, b: int) -> int:
        # a = s^ea r^ia, b = s^eb r^ib；关系 s r = r^{-1} s, s^2 = e
        ea, ia = (0, a) if a < n else (1, a - n)
        eb, ib = (0, b) if b < n else (1, b - n)
        e = (ea + eb) % 2
        # (s^ea r^ia)(s^eb r^ib) = s^(ea+eb) r^( (-1)^eb * ia + ib )
        i = ((-1) ** eb) * ia + ib
        i %= n
        return i if e == 0 else n + i

    for i in range(size):
        for j in range(size):
            table[i][j] = mul(i, j)
    labels = [f"r^{i}" if i < n else f"s·r^{i-n}" for i in range(size)]
    return table, labels


# ===========================================================================
# 群构造（用于把对象库扩到更大的阶）
# ---------------------------------------------------------------------------
# 这些构造都**不声称**给出某阶的同构分类完备列表；每造出来的 Cayley 表都会
# 被 analyze_group 逐条验群公理（闭合/结合律/单位元/逆元），验不过就是构造写
# 错了，不会被悄悄收进库里。
# ===========================================================================
def direct_product(A: Sequence[Sequence[int]],
                   B: Sequence[Sequence[int]]) -> List[List[int]]:
    """直积 A × B，元素编号 a*|B| + b。"""
    na, nb = len(A), len(B)
    n = na * nb
    table = [[0] * n for _ in range(n)]
    for a1 in range(na):
        for b1 in range(nb):
            for a2 in range(na):
                for b2 in range(nb):
                    table[a1 * nb + b1][a2 * nb + b2] = A[a1][a2] * nb + B[b1][b2]
    return table


def cyclic_twisted_extension(m: int, t: int, kappa: int) -> List[List[int]]:
    """Z_m 被 Z_2 的（可能不分裂的）扩张：元素 r^i·s^j，i∈Z_m, j∈Z_2。

        s·r·s⁻¹ = r^t ， s² = r^κ

    乘法：(i1,j1)·(i2,j2) = ( i1 + t^{j1}·i2 + κ·[j1=j2=1] , j1+j2 ) (mod m)
    结合律不靠我推算 —— 由 analyze_group 逐表验证。
    特例：t=7,κ=0 → D_{2m}（二面体）；t=7,κ=4(m=8) → Q16；t=3,κ=0 → SD16；
          t=5,κ=0 → M16；t=1,κ=0 → Z_m × Z_2。
    """
    n = 2 * m
    idx = lambda i, j: j * m + i          # noqa: E731
    table = [[0] * n for _ in range(n)]
    for j1 in range(2):
        for i1 in range(m):
            for j2 in range(2):
                for i2 in range(m):
                    i = (i1 + pow(t, j1, m) * i2
                         + (kappa if (j1 == 1 and j2 == 1) else 0)) % m
                    table[idx(i1, j1)][idx(i2, j2)] = idx(i, (j1 + j2) % 2)
    return table


def automorphisms(table: Sequence[Sequence[int]],
                  brute_force_max: int = 9) -> List[Tuple[int, ...]]:
    """穷举 Aut(G)，返回自置换元组列表（恒等置换在首位）。

    只在 |G| ≤ brute_force_max 时可用（|G|=8 时 8! = 40320 个置换，够快）。
    阶更大时返回空列表 —— **不猜**。
    """
    n = len(table)
    if n > brute_force_max:
        return []
    ident = None
    for e in range(n):
        if all(table[e][x] == x and table[x][e] == x for x in range(n)):
            ident = e
            break
    if ident is None:
        return []
    out: List[Tuple[int, ...]] = []
    rng = tuple(range(n))
    for perm in itertools.permutations(rng):
        if perm[ident] != ident:
            continue
        ok = True
        for a in range(n):
            pa = perm[a]
            row = table[pa]
            for b in range(n):
                if perm[table[a][b]] != row[perm[b]]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append(perm)
    return out


def semidirect_by_cyclic(A: Sequence[Sequence[int]], m: int,
                         alpha: Sequence[int]) -> List[List[int]]:
    """A ⋊_α Z_m：元素 (a, k)，(a1,k1)·(a2,k2) = ( a1 · α^{k1}(a2) , k1+k2 )。

    要求 α ∈ Aut(A) 且 α^m = id（调用方保证；结合律由 analyze_group 兜底验）。
    """
    na = len(A)
    n = na * m
    pows = [list(range(na))]
    for _ in range(m):
        pows.append([alpha[pows[-1][i]] for i in range(na)])

    def mul_A(x: int, y: int) -> int:
        return A[x][y]

    table = [[0] * n for _ in range(n)]
    idx = lambda a, k: k * na + a          # noqa: E731
    for k1 in range(m):
        for a1 in range(na):
            for k2 in range(m):
                for a2 in range(na):
                    a = mul_A(a1, pows[k1][a2])
                    table[idx(a1, k1)][idx(a2, k2)] = idx(a, (k1 + k2) % m)
    return table


def pauli_group16() -> List[List[int]]:
    """Pauli 群（16 阶）：由 X, Z, i·I 生成，XZ = −ZX。

    元素记作 i^ε·X^a·Z^b（ε∈Z_4, a,b∈Z_2）。
    (ε1,a1,b1)·(ε2,a2,b2) = ( ε1+ε2+2·b1·a2 (mod 4) , a1⊕a2 , b1⊕b2 )
    —— 来自 Z^b1·X^a2 = (−1)^{b1·a2}·X^a2·Z^b1。
    """
    n = 16
    table = [[0] * n for _ in range(n)]
    idx = lambda e, a, b: (e * 4 + a * 2 + b)   # noqa: E731
    for e1 in range(4):
        for a1 in range(2):
            for b1 in range(2):
                for e2 in range(4):
                    for a2 in range(2):
                        for b2 in range(2):
                            e = (e1 + e2 + 2 * b1 * a2) % 4
                            table[idx(e1, a1, b1)][idx(e2, a2, b2)] = \
                                idx(e, a1 ^ a2, b1 ^ b2)
    return table


def order16_candidates() -> List[Tuple[str, List[List[int]]]]:
    """16 阶群的候选构造集（**故意是超集**，交给上层去重与验证）。

    说明：这里**不声称**覆盖 16 阶全部同构类。做法是造一批候选、逐条验群公理、
    再按不变量指纹去重；最终个数会与教科书计数（14）对照并如实报告。
    """
    z = lambda k: cyclic_additive_group(k)     # noqa: E731
    out: List[Tuple[str, List[List[int]]]] = []

    # ① 交换的 5 个：16 = 4 / 3+1 / 2+2 / 2+1+1 / 1+1+1+1
    out.append(("Z16", z(16)))
    out.append(("Z8xZ2", direct_product(z(8), z(2))))
    out.append(("Z4xZ4", direct_product(z(4), z(4))))
    out.append(("Z4xZ2xZ2", direct_product(direct_product(z(4), z(2)), z(2))))
    out.append(("Z2^4", direct_product(direct_product(z(2), z(2)),
                                       direct_product(z(2), z(2)))))

    # ② Z_8 的扭曲扩张：t ∈ Aut(Z_8) = {1,3,5,7}，κ ∈ {0,4}
    for t in (1, 3, 5, 7):
        for kappa in (0, 4):
            out.append((f"Ext8(t={t},k={kappa})",
                        cyclic_twisted_extension(8, t, kappa)))

    # ③ Z_4 ⋊ Z_4 与 Z_4 × Z_4（ inversion 作用）
    z4 = z(4)
    autos4 = automorphisms(z4)
    for i, al in enumerate(autos4):
        out.append((f"Z4xZ4-sd{i}", semidirect_by_cyclic(z4, 4, al)))

    # ④ (C4×C2) ⋊ C2 与 (C2^3) ⋊ C2：遍历 Aut 中平方为 id 的自同构
    for name, base in (("C4xC2", direct_product(z(4), z(2))),
                       ("C2^3", direct_product(direct_product(z(2), z(2)),
                                               z(2)))):
        for i, al in enumerate(automorphisms(base)):
            # 只保留 α² = id —— 否则不构成 Z_2 的作用
            if all(al[al[x]] == x for x in range(len(base))):
                out.append((f"{name}:sdC2[{i}]",
                            semidirect_by_cyclic(base, 2, al)))

    # ⑤ C2^2 ⋊ C4
    c2c2 = direct_product(z(2), z(2))
    for i, al in enumerate(automorphisms(c2c2)):
        # 只保留 α⁴ = id —— 否则不构成 Z_4 的作用
        if all(al[al[al[al[x]]]] == x for x in range(4)):
            out.append((f"C2^2:sdC4[{i}]", semidirect_by_cyclic(c2c2, 4, al)))

    # ⑥ 直积型：D4×Z2（8 阶二面体 ×Z2）、Q8×Z2、D8（16 阶二面体）
    #    Q8 = Z_4 的扭曲扩张：s r s⁻¹ = r³，s² = r²
    d8 = dihedral_group(4)[0]
    q8 = cyclic_twisted_extension(4, 3, 2)
    out.append(("D4xZ2", direct_product(d8, z(2))))
    out.append(("Q8xZ2", direct_product(q8, z(2))))
    out.append(("Q8", q8))
    out.append(("D8(dihedral16)", dihedral_group(8)[0]))

    # ⑦ Pauli 群（中心积 C4 ∘ D8）
    out.append(("Pauli16", pauli_group16()))

    return out


def order16_library() -> List[Tuple[str, List[List[int]]]]:
    """16 阶群的 14 个**具名**代表构造。

    个数 14 取自教科书（16 阶群的同构类数）；本函数**不声称**自己证明了完备性。
    能给出的保证是：
      1. 每一个都过了 analyze_group 的群公理检查（由调用方/审计验）；
      2. 两两之间可用不变量指纹区分（审计逐对验）；
      3. 与教科书的 14 相符——若哪天构造写错导致退化成 13 个，审计会报出来。
    指纹相同**不等于**同构，所以"14 个互异"是 L2 证据，不是同构分类的证明。
    """
    z = lambda k: cyclic_additive_group(k)        # noqa: E731
    c4, c2 = z(4), z(2)

    # (C4×C2) ⋊ C2 用的自同构：⟨x⟩₄×⟨y⟩₂ 上 x ↦ x·y, y ↦ y。
    # 元素编号 a*2+b（a∈Z_4 为 x^a，b∈Z_2 为 y^b），故 (a,b) ↦ (a, b ⊕ (a mod 2))。
    base = direct_product(c4, c2)
    alpha_c4c2 = [0] * 8
    for a in range(4):
        for b in range(2):
            alpha_c4c2[a * 2 + b] = a * 2 + (b ^ (a % 2))
    # Z4 ⋊ Z4 用的自同构：a ↦ a⁻¹（加法记号下 a ↦ −a）
    autos4 = automorphisms(c4)
    inv4 = next(p for p in autos4 if p != tuple(range(4)))

    return [
        ("Z16", z(16)),
        ("Z8xZ2", direct_product(z(8), c2)),
        ("Z4xZ4", direct_product(c4, c4)),
        ("Z4xZ2xZ2", direct_product(direct_product(c4, c2), c2)),
        ("Z2^4", direct_product(direct_product(c2, c2),
                                direct_product(c2, c2))),
        ("D16", dihedral_group(8)[0]),
        ("SD16", cyclic_twisted_extension(8, 3, 0)),
        ("Q16", cyclic_twisted_extension(8, 7, 4)),
        ("M16", cyclic_twisted_extension(8, 5, 0)),
        ("D4xZ2", direct_product(dihedral_group(4)[0], c2)),
        ("Q8xZ2", direct_product(cyclic_twisted_extension(4, 3, 2), c2)),
        ("Pauli16", pauli_group16()),
        ("C4:C4", semidirect_by_cyclic(c4, 4, inv4)),
        ("(C4xC2):C2", semidirect_by_cyclic(base, 2, alpha_c4c2)),
    ]


STANDARD_GROUPS = {
    "Z6": (lambda: (cyclic_additive_group(6), [str(i) for i in range(6)])),
    "Z8": (lambda: (cyclic_additive_group(8), [str(i) for i in range(8)])),
    "S3": (lambda: symmetric_group(3)),
    "D4": (lambda: dihedral_group(4)),
}

# 已知判据（文献值）
KNOWN_GROUP_FACTS: Dict[str, Dict[str, Any]] = {
    "Z6": {"abelian": True, "center_size": 6, "proper_subgroups_count": 3,
           "proper_subgroup_orders": [1, 2, 3]},
    "Z8": {"abelian": True, "center_size": 8, "proper_subgroups_count": 3,
           "proper_subgroup_orders": [1, 2, 4]},
    "S3": {"abelian": False, "center_size": 1, "proper_subgroups_count": 5,
           "proper_subgroup_orders": [1, 2, 3]},
    "D4": {"abelian": False, "center_size": 2, "order": 8},
}
