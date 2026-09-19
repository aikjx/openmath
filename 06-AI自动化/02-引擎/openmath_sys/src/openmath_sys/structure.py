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
  - 子群枚举在阶较小时才完备，否则为"由 ≤3 个生成元生成的子群"（结果
    记为 partial，不冒充完整分类）。
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


def analyze_group(table: Sequence[Sequence[int]], full_enum_cap: int = 14,
                  gen_subset_max: int = 3) -> Dict[str, Any]:
    """
    由 Cayley 表判定并分析有限群。

    返回 群公理是否成立、单位元、逆元、元素阶、交换性、中心、子群列表。
    子群枚举在 n <= full_enum_cap 时为**完备**（枚举全部含单位元的子集）；
    否则退化为"由 ≤gen_subset_max 个元素生成的子群"，结果标记为 partial
    ——**不冒充完整子群分类**。
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

        found = set()
        if n <= full_enum_cap:
            subgroup_mode = "complete_subset_enumeration"
            others = [x for x in range(n) if x != identity]
            for r in range(0, len(others) + 1):
                for combo in itertools.combinations(others, r):
                    cl = closure(combo)
                    if cl is not None and len(cl) < n:  # 只收真子群
                        found.add(cl)
        else:
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
