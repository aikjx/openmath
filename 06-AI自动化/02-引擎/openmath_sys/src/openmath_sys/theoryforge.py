# -*- coding: utf-8 -*-
"""
theoryforge.py —— 理论锻造：在**有限对象库**上发现不变量之间的候选关系
======================================================================

本模块做的事（一句话）：构造一批有限数学对象 -> 为每个对象算出一组**精确不变量** ->
在这些不变量之间搜索保持成立的候选关系（恒等式 / 单项式关系 / 不等式）-> 用**留出对象**
做反例搜索 -> 把存活下来的东西整理成一张"理论体系网"。

三条搜索通道：

  C1 线性通道： enumerate 不变量的小子集（含可选的常数项），求 Q 上的精确秩；
     若子矩阵不满秩，其零空间给出一组**原始整系数**的线性关系 Σ c_i·inv_i = 0。
  C2 单项式通道：搜索 Π (inv_i)^{e_i} = const，指数在 {-2,-1,1,2} 中取，支撑 ≤ 3。
  C3 不等式通道（Graffiti 传统）：搜索 inv_a ≤ inv_b、inv_a ≤ inv_b + inv_c、
     inv_a ≤ inv_b·inv_c，要求在所有发现集对象上成立且**在某对象上取等**（尖锐性）。

诚实红线（00-宪章/02-诚实红线.md）——本模块的输出性质必须被准确理解：

  1. 所有候选关系的成立范围**仅为已被检验的有限对象集合**，是 **L2 级证据**。
     这不是证明，也不是"新定理"。历史教训（Pólya 猜想、Mertens 猜想、Skewes 数）
     说明有限范围内的无反例完全可能是错觉。
  2. 发现集与检验集必须分离（本实现按确定性规则留出约 1/4 对象），
     在留出集上失败者记为 **FALSIFIED** 并**保留反例**，不删除、不改写。
  3. 参与搜索的不变量若其计算方式不一致（如子群枚举完备性不同），
     该不变量会被**整体排除**并记录原因——不允許把不可比的量混在一起凑关系。
  4. 发现的绝大多数关系属于三类之一：**已知定理的重发现**、
     **我们自己定义的派生量**（definitional）、**退化的巧合**。
     三者都必须被标注，不得冒充新发现。
"""
from __future__ import annotations

import itertools
import math
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:  # 包内相对导入
    from . import structure as st
    from .structure import (
        ChainComplex, STANDARD_COMPLEXES, analyze_group,
        cyclic_additive_group, dihedral_group, symmetric_group, homology_summary,
    )
except Exception:  # noqa: BLE001  # 作为顶层脚本被直接使用时的兜底
    import structure as st  # type: ignore
    from structure import (  # type: ignore  # noqa: F401
        ChainComplex, STANDARD_COMPLEXES, analyze_group,
        cyclic_additive_group, dihedral_group, symmetric_group, homology_summary,
    )

SCOPE_NOTE = (
    "理论锻造：有限对象库（整数 / 图 / 有限群 / 整数划分 / 有限链复形）上的"
    "精确不变量关系搜索，附留出集反例检查。输出为 L2 候选关系，**不是证明**。"
)

EVIDENCE_NOTE = (
    "所有关系仅在被检验的有限对象上成立（精确有理算术），属 L2 证据；"
    "有限集合上的无反例不构成任何证明。"
)

__all__ = [
    "SCOPE_NOTE", "EVIDENCE_NOTE",
    "build_sites", "discover_linear", "discover_monomial", "discover_inequality",
    "pareto_filter_inequalities", "recognize_known", "violations_on", "stress_test",
    "theory_net", "forge_all",
    "KNOWN_RELATIONS", "DEFINITIONAL", "CONST_TERM",
]

CONST_TERM = "1"


# ===========================================================================
# 1. 精确线性代数（Q 上）
# ===========================================================================
def _rref(rows: Sequence[Sequence[Fraction]], ncols: int):
    """行最简形。返回 (矩阵, 主元列索引列表)。"""
    m = [[Fraction(x) for x in r] for r in rows]
    nrow = len(m)
    pivots: List[int] = []
    r = 0
    for c in range(ncols):
        piv = None
        for i in range(r, nrow):
            if m[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        m[r], m[piv] = m[piv], m[r]
        pv = m[r][c]
        m[r] = [x / pv for x in m[r]]
        for i in range(nrow):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        pivots.append(c)
        r += 1
        if r == nrow:
            break
    return m, pivots


def _nullspace(rows: Sequence[Sequence[Fraction]], ncols: int) -> List[List[Fraction]]:
    """矩阵的（右）零空间基。"""
    if not rows:
        return []
    m, pivots = _rref(rows, ncols)
    free = [c for c in range(ncols) if c not in pivots]
    out = []
    for f in free:
        v = [Fraction(0)] * ncols
        v[f] = Fraction(1)
        for ri, pc in enumerate(pivots):
            v[pc] = -m[ri][f]
        out.append(v)
    return out


def _primitive_ints(vec: Sequence[Fraction]) -> List[int]:
    """化成分母已清除、系数为互素整数的表示，并约定首个非零系数为正。"""
    den = 1
    for x in vec:
        den = den * x.denominator // math.gcd(den, x.denominator)
    nums = [int(x * den) for x in vec]
    g = 0
    for n in nums:
        g = math.gcd(g, abs(n))
    if g:
        nums = [n // g for n in nums]
    for n in nums:
        if n > 0:
            break
        if n < 0:
            nums = [-x for x in nums]
            break
    return nums


def _rank_and_relations(rows: Sequence[Sequence[Fraction]], ncols: int) -> Tuple[int, List[List[int]]]:
    _, pivots = _rref(rows, ncols)
    rank = len(pivots)
    rels = [_primitive_ints(v) for v in _nullspace(rows, ncols)]
    return rank, rels


# ===========================================================================
# 2. 对象族 A —— 整数（算术函数）
# ===========================================================================
def _factorize(n: int) -> Dict[int, int]:
    f: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def arithmetic_invariants(n: int) -> Dict[str, Any]:
    """整数 n 的一组算术函数值（全部为精确值）。"""
    f = _factorize(n)
    tau = 1
    sigma = 1
    rad = 1
    phi = n
    big_omega = 0
    for p, e in f.items():
        tau *= (e + 1)
        sigma *= (p ** (e + 1) - 1) // (p - 1)
        rad *= p
        big_omega += e
        phi = phi // p * (p - 1)
    mu = 0 if any(e > 1 for e in f.values()) else ((-1) ** len(f))
    return {
        "n": Fraction(n),
        "tau": Fraction(tau),
        "sigma": Fraction(sigma),
        "phi": Fraction(phi),
        "omega": Fraction(len(f)),
        "Omega": Fraction(big_omega),
        "rad": Fraction(rad),
        "mu": Fraction(mu),
        "aliquot": Fraction(sigma - n),
        "abundance": Fraction(sigma, n),
        "phi_ratio": Fraction(phi, n),
        "squarefree": Fraction(1 if all(e == 1 for e in f.values()) else 0),
        "P_plus": Fraction(max(f) if f else 1),
        "p_minus": Fraction(min(f) if f else 1),
        "n_over_rad": Fraction(n, rad),
    }


# ===========================================================================
# 3. 对象族 B —— 有限简单图
# ===========================================================================
def _det_bareiss(mat: Sequence[Sequence[int]]) -> int:
    """无分式 Bareiss 算法的精确整数行列式。"""
    n = len(mat)
    if n == 0:
        return 1
    m = [list(r) for r in mat]
    sign = 1
    prev = 1
    for k in range(n - 1):
        if m[k][k] == 0:
            sw = None
            for i in range(k + 1, n):
                if m[i][k] != 0:
                    sw = i
                    break
            if sw is None:
                return 0
            m[k], m[sw] = m[sw], m[k]
            sign = -sign
        for i in range(k + 1, n):
            mik = m[i][k]
            for j in range(k + 1, n):
                m[i][j] = (m[i][j] * m[k][k] - mik * m[k][j]) // prev
        prev = m[k][k]
    return sign * m[n - 1][n - 1]


def _max_independent(nv: int, adj: List[List[int]]) -> int:
    """精确最大独立集（位掩码 + 分支限界）。不设规模哨兵值——
    宁可慢，也**不允许返回 -1 之类的假值**，否则会污染后续的关系搜索。"""
    if nv == 0:
        return 0
    adjmask = [0] * nv
    for v in range(nv):
        m = 0
        for u in adj[v]:
            m |= 1 << u
        adjmask[v] = m
    best = [0]

    def rec(candidates: int, count: int) -> None:
        if count + candidates.bit_count() <= best[0]:
            return
        if candidates == 0:
            if count > best[0]:
                best[0] = count
            return
        bit = candidates & -candidates
        v = bit.bit_length() - 1
        rec(candidates & ~bit & ~adjmask[v], count + 1)  # 取 v
        rec(candidates & ~bit, count)                    # 不取 v

    rec((1 << nv) - 1, 0)
    return best[0]


def _chromatic_number(nv: int, adj: List[List[int]]) -> int:
    if nv == 0:
        return 0
    order = sorted(range(nv), key=lambda v: -len(adj[v]))

    def can(k: int) -> bool:
        colors = [-1] * nv

        def bt(i: int) -> bool:
            if i == len(order):
                return True
            v = order[i]
            for c in range(k):
                if all(colors[u] != c for u in adj[v]):
                    colors[v] = c
                    if bt(i + 1):
                        return True
                    colors[v] = -1
            return False

        return bt(0)

    for k in range(1, nv + 1):
        if can(k):
            return k
    return nv


def _girth(nv: int, adj: List[List[int]]) -> int:
    """最短圈长；无圈（森林）返回 0。"""
    best = 0
    for s in range(nv):
        dist = [-1] * nv
        parent = [-1] * nv
        dist[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            for u in adj[v]:
                if dist[u] == -1:
                    dist[u] = dist[v] + 1
                    parent[u] = v
                    queue.append(u)
                elif u != parent[v]:
                    cyc = dist[v] + dist[u] + 1
                    if best == 0 or cyc < best:
                        best = cyc
        if best == 3:
            break
    return best


def graph_invariants(nv: int, edges: Sequence[Tuple[int, int]]) -> Dict[str, Any]:
    adj: List[List[int]] = [[] for _ in range(nv)]
    eset = set()
    for a, b in edges:
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        if key in eset:
            continue
        eset.add(key)
        adj[a].append(b)
        adj[b].append(a)
    ne = len(eset)
    degs = [len(adj[v]) for v in range(nv)]

    # 以 BFS 求连通分量个数与直径（顶点数 ≤ 10，规模无关紧要）
    seen = [False] * nv
    comps = 0
    for s in range(nv):
        if seen[s]:
            continue
        comps += 1
        seen[s] = True
        queue = [s]
        while queue:
            v = queue.pop(0)
            for u in adj[v]:
                if not seen[u]:
                    seen[u] = True
                    queue.append(u)
    diameter = 0
    for s in range(nv):
        dist = [-1] * nv
        dist[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            for u in adj[v]:
                if dist[u] == -1:
                    dist[u] = dist[v] + 1
                    queue.append(u)
        for u in range(nv):
            if dist[u] > diameter:
                diameter = dist[u]

    adjset = [set(adj[v]) for v in range(nv)]
    triangles = 0
    for a, b in eset:
        triangles += len(adjset[a] & adjset[b])
    triangles //= 3

    alpha = _max_independent(nv, adj)
    complement = [[u for u in range(nv) if u != v and u not in adjset[v]]
                  for v in range(nv)]
    omega = _max_independent(nv, complement)
    chi = _chromatic_number(nv, adj)
    girth = _girth(nv, adj)

    # 基尔霍夫矩阵树定理
    lap = [[0] * nv for _ in range(nv)]
    for v in range(nv):
        lap[v][v] = degs[v]
        for u in adj[v]:
            lap[v][u] = -1
    if comps == 1:
        if nv >= 2:
            minor = [[lap[i][j] for j in range(nv - 1)] for i in range(nv - 1)]
            trees = _det_bareiss(minor)
        else:
            # 平凡图（单点、无边）有恰好 1 棵生成树（空树）。
            # 审计实测：此前这里返回 0，是 n=1 的边界处理缺失。
            trees = 1
    else:
        trees = 0

    # 二部性（2-染色）
    color = [-1] * nv
    bipartite = True
    for s in range(nv):
        if color[s] != -1:
            continue
        color[s] = 0
        queue = [s]
        while queue:
            v = queue.pop(0)
            for u in adj[v]:
                if color[u] == -1:
                    color[u] = 1 - color[v]
                    queue.append(u)
                elif color[u] == color[v]:
                    bipartite = False

    return {
        "vertices": Fraction(nv),
        "edges": Fraction(ne),
        "degree_sum": Fraction(sum(degs)),
        "avg_degree": Fraction(2 * ne, nv) if nv else Fraction(0),
        "min_degree": Fraction(min(degs)) if nv else Fraction(0),
        "max_degree": Fraction(max(degs)) if nv else Fraction(0),
        "triangles": Fraction(triangles),
        "independent_number": Fraction(alpha),
        "clique_number": Fraction(omega),
        "chromatic_number": Fraction(chi),
        "components": Fraction(comps),
        "diameter": Fraction(diameter),
        "girth": Fraction(girth),
        "spanning_trees": Fraction(trees),
        "bipartite": Fraction(1 if bipartite else 0),
        "connected": Fraction(1 if comps == 1 else 0),
    }


def _cycle_graph(k: int) -> List[Tuple[int, int]]:
    if k < 3:
        return []
    return [(i, (i + 1) % k) for i in range(k)]


def _wheel_graph(k: int) -> List[Tuple[int, int]]:
    """轮图 W_k：一个中心 + k-1 个环上顶点。"""
    if k < 4:
        return []
    e = _cycle_graph(k - 1)
    e += [(k - 1, i) for i in range(k - 1)]
    return e


def _hypercube(d: int) -> List[Tuple[int, int]]:
    e = []
    for i in range(2 ** d):
        for b in range(d):
            j = i ^ (1 << b)
            if i < j:
                e.append((i, j))
    return e


def _petersen() -> List[Tuple[int, int]]:
    e = [(i, (i + 1) % 5) for i in range(5)]
    e += [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    e += [(i, 5 + i) for i in range(5)]
    return e


def _disjoint_union_family() -> List[Tuple[str, int, List[Tuple[int, int]]]]:
    """若干**不连通**图（用于让 components 等不变量真正变化）。"""
    out = []

    def joined(name, n1, e1, n2, e2):
        e = list(e1) + [(a + n1, b + n1) for a, b in e2]
        out.append((name, n1 + n2, e))

    joined("K3+K3", 3, [(0, 1), (1, 2), (0, 2)], 3, [(0, 1), (1, 2), (0, 2)])
    joined("C4+P3", 4, _cycle_graph(4), 3, [(0, 1), (1, 2)])
    joined("K4+P2", 4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)], 2, [(0, 1)])
    joined("C5+K3", 5, _cycle_graph(5), 3, [(0, 1), (1, 2), (0, 2)])
    joined("P4+K3", 4, [(0, 1), (1, 2), (2, 3)], 3, [(0, 1), (1, 2), (0, 2)])
    joined("K2+K2+K2", 2, [(0, 1)], 2, [(0, 1)])
    joined("C3+P5", 3, _cycle_graph(3), 5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    return out


def build_graph_library(extended: bool = False) -> List[Dict[str, Any]]:
    objs: List[Dict[str, Any]] = []

    def add(name, nv, edges):
        objs.append({"id": f"graph:{name}", "label": name,
                     "raw": (nv, list(edges)), "inv": graph_invariants(nv, edges)})

    for k in range(1, 9):
        add(f"P{k}", k, [(i, i + 1) for i in range(k - 1)])
    for k in range(3, 10):
        add(f"C{k}", k, _cycle_graph(k))
    for k in range(1, 8):
        add(f"K{k}", k, [(i, j) for i in range(k) for j in range(i + 1, k)])
    for k in range(1, 9):
        add(f"S{k}", k, [(0, i) for i in range(1, k)])
    for a in range(1, 5):
        for b in range(1, 5):
            if (a, b) != (1, 1):
                add(f"K{a}x{b}", a + b,
                    [(i, a + j) for i in range(a) for j in range(b)])
    for k in range(4, 9):
        add(f"W{k}", k, _wheel_graph(k))
    for d in range(1, 4):
        add(f"Q{d}", 2 ** d, _hypercube(d))
    add("Petersen", 10, _petersen())
    for name, nv, edges in _disjoint_union_family():
        add(name, nv, edges)
    if extended:
        for k in range(10, 15):
            add(f"C{k}", k, _cycle_graph(k))
        for k in range(11, 15):
            add(f"P{k}", k, [(i, i + 1) for i in range(k - 1)])
        add("K9", 9, [(i, j) for i in range(9) for j in range(i + 1, 9)])
        for k in range(9, 13):
            add(f"W{k}", k, _wheel_graph(k))
        for a, b in ((5, 5), (5, 6), (6, 6), (3, 8)):
            add(f"K{a}x{b}", a + b, [(i, a + j) for i in range(a) for j in range(b)])
        for k in range(9, 13):
            add(f"S{k}", k, [(0, i) for i in range(1, k)])
        k5 = [(i, j) for i in range(5) for j in range(i + 1, 5)]
        add("K5+K5", 10, k5 + [(a + 5, b + 5) for a, b in k5])
    return objs


# ===========================================================================
# 4. 对象族 C —— 有限群
# ===========================================================================
def _direct_product(t1: Sequence[Sequence[int]],
                    t2: Sequence[Sequence[int]]) -> List[List[int]]:
    m, n = len(t1), len(t2)
    size = m * n
    table = [[0] * size for _ in range(size)]
    for a in range(m):
        for b in range(n):
            for c in range(m):
                for d in range(n):
                    table[a * n + b][c * n + d] = t1[a][c] * n + t2[b][d]
    return table


def _conjugacy_classes(table: Sequence[Sequence[int]], n: int,
                       identity: int) -> List[List[int]]:
    inv_of = [0] * n
    for a in range(n):
        for b in range(n):
            if table[a][b] == identity:
                inv_of[a] = b
                break
    seen = [False] * n
    classes: List[List[int]] = []
    for a in range(n):
        if seen[a]:
            continue
        cls = set()
        for g in range(n):
            cls.add(table[g][table[a][inv_of[g]]])
        for c in cls:
            seen[c] = True
        classes.append(sorted(cls))
    return classes


def group_invariants(table: Sequence[Sequence[int]], max_order: int = 12) -> Dict[str, Any]:
    """由 Cayley 表算群不变量。子群枚举只对 |G| <= full_enum_cap 才是完备的。"""
    n = len(table)
    info = analyze_group(table, full_enum_cap=max_order)
    identity = info["identity"]
    cls = _conjugacy_classes(table, n, identity) if identity is not None else []
    orders = info["element_orders"]
    exponent = info["exponent"] or 0

    # 最小生成元个数（≤3）
    def generated_size(seed: Sequence[int]) -> int:
        s = {identity}
        s.update(seed)
        changed = True
        while changed:
            changed = False
            for a in list(s):
                for b in list(s):
                    c = table[a][b]
                    if c not in s:
                        s.add(c)
                        changed = True
        return len(s)

    min_gen = None
    for k in range(0, 4):
        hit = None
        if k == 0:
            hit = 1 == n
        else:
            for combo in itertools.combinations([x for x in range(n) if x != identity], k):
                if generated_size(combo) == n:
                    hit = True
                    break
        if hit:
            min_gen = k
            break

    return {
        "order": Fraction(n),
        "exponent": Fraction(exponent),
        "center_size": Fraction(info["center_size"]),
        "proper_subgroups_count": Fraction(info["proper_subgroups_count"]),
        "proper_subgroup_order_types": Fraction(len(info["proper_subgroup_orders"])),
        "abelian": Fraction(1 if info["abelian"] else 0),
        "subgroups_only_trivial": Fraction(1 if len(info["proper_subgroups"]) <= 1 else 0),
        "class_number": Fraction(len(cls)),
        "involutions": Fraction(sum(1 for o in orders if o == 2)),
        "elements_at_exponent": Fraction(sum(1 for o in orders if o == exponent)),
        "max_element_order": Fraction(info.get("max_element_order") or 0),
        "min_generators": Fraction(min_gen if min_gen is not None else -1),
        "subgroup_enumeration_mode": info["subgroup_enumeration_mode"],
        "lagrange_checked": info["lagrange_checked"],
        "is_group": info["is_group"],
    }


def _quaternion_group8() -> List[List[int]]:
    """四元数群 Q8：元素记作 (w, s)，w∈{1,i,j,k}，s∈{+1,-1}。"""
    def prod(w1, s1, w2, s2):
        if w1 == 0:
            return w2, s1 * s2
        if w2 == 0:
            return w1, s1 * s2
        if w1 == w2:
            return 0, -s1 * s2
        tab = {(1, 2): (3, 1), (2, 3): (1, 1), (3, 1): (2, 1)}
        if (w1, w2) in tab:
            w, s = tab[(w1, w2)]
            return w, s * s1 * s2
        w, s = tab[(w2, w1)]
        return w, -s * s1 * s2

    elems = [(w, s) for w in range(4) for s in (1, -1)]
    idx = {e: i for i, e in enumerate(elems)}
    size = len(elems)
    table = [[0] * size for _ in range(size)]
    for a in elems:
        for b in elems:
            table[idx[a]][idx[b]] = idx[prod(a[0], a[1], b[0], b[1])]
    return table


def build_group_library(extended: bool = False) -> List[Dict[str, Any]]:
    objs: List[Dict[str, Any]] = []

    def add(name, table):
        inv = group_invariants(table, max_order=16 if extended else 12)
        objs.append({"id": f"group:{name}", "label": name, "raw": table, "inv": inv})

    for n in range(1, 13):
        add(f"Z{n}", cyclic_additive_group(n))
    for n in range(2, 7):
        t, _ = dihedral_group(n)
        add(f"D{n}", t)
    t_sym3, _ = symmetric_group(3)
    add("S3", t_sym3)
    add("Q8", _quaternion_group8())
    for a, b in ((2, 2), (2, 3), (2, 4), (3, 3), (2, 5), (2, 6), (3, 4)):
        if a * b <= 12:
            add(f"Z{a}xZ{b}", _direct_product(cyclic_additive_group(a),
                                              cyclic_additive_group(b)))
    if extended:
        # 旧写的 extended 分支里 `a*b <= 12` 把 (2,8)/(4,4)/(3,5)… 全过滤掉了，
        # 于是 extended=True **一个群也没多加**——一个看起来在工作、其实空转的开关。
        for n in range(13, 16):
            add(f"Z{n}", cyclic_additive_group(n))
        t_d7, _ = dihedral_group(7)          # 14 阶
        add("D7", t_d7)
        add("Z3xZ5", _direct_product(cyclic_additive_group(3),
                                     cyclic_additive_group(5)))   # 15 阶
        # 16 阶：子群枚举换成「循环子群的 join 闭包」后不再是 2.8 s/群，可以纳入。
        # 14 个构造**不声称**是同构分类的完备列表，审计只验「两两可区分」与
        # 「与教科书计数 14 相符」。
        for name, t16 in st.order16_library():
            add(f"{name}(16)", t16)
    return objs


# ===========================================================================
# 5. 对象族 D —— 整数划分
# ===========================================================================
def _partitions(n: int, max_part: Optional[int] = None) -> List[List[int]]:
    if max_part is None or max_part > n:
        max_part = n
    if n == 0:
        return [[]]
    out = []
    first = n if max_part > n else max_part
    for k in range(first, 0, -1):
        for rest in _partitions(n - k, k):
            out.append([k] + rest)
    return out


def _conjugate(lam: Sequence[int]) -> List[int]:
    if not lam:
        return []
    biggest = lam[0]
    return [sum(1 for p in lam if p >= i) for i in range(1, biggest + 1)]


def partition_invariants(lam: Sequence[int]) -> Dict[str, Any]:
    conj = _conjugate(lam)
    total = sum(lam)

    def rank_of(p: Sequence[int]) -> int:
        return (p[0] if p else 0) - len(p)

    durfee = 0
    for i, p in enumerate(lam, start=1):
        if p >= i:
            durfee = i
        else:
            break
    return {
        "sum": Fraction(total),
        "length": Fraction(len(lam)),
        "largest_part": Fraction(lam[0] if lam else 0),
        "distinct_parts": Fraction(len(set(lam))),
        "odd_parts": Fraction(sum(1 for p in lam if p % 2 == 1)),
        "ones": Fraction(sum(1 for p in lam if p == 1)),
        "durfee": Fraction(durfee),
        "self_conjugate": Fraction(1 if conj == list(lam) else 0),
        "rank": Fraction(rank_of(lam)),
        "conjugate_rank": Fraction(rank_of(conj)),
        "conjugate_length": Fraction(len(conj)),
        "conjugate_distinct": Fraction(len(set(conj))),
    }


def build_partition_library(max_n: int = 8) -> List[Dict[str, Any]]:
    objs = []
    for m in range(1, max_n + 1):
        for lam in _partitions(m):
            name = "(" + "+".join(str(x) for x in lam) + ")"
            objs.append({"id": f"part:{name}", "label": f"λ⊢{m}:{name}",
                         "raw": list(lam), "inv": partition_invariants(lam)})
    return objs


# ===========================================================================
# 6. 对象族 E —— 有限链复形
# ===========================================================================
def complex_invariants(cx: ChainComplex) -> Dict[str, Any]:
    hs = homology_summary(cx)
    gens = list(hs["generators_per_dim"])
    bq = list(hs["betti_Q"])

    def pad(seq: Sequence[int], k: int) -> int:
        return seq[k] if k < len(seq) else 0

    torsion_total = 0
    for dim_str, per_p in hs["torsion_by_dim"].items():
        torsion_total += sum(per_p.values())
    c0, c1, c2 = pad(gens, 0), pad(gens, 1), pad(gens, 2)
    b0, b1, b2 = pad(bq, 0), pad(bq, 1), pad(bq, 2)
    return {
        "dim": Fraction(cx.dim),
        "c0": Fraction(c0),
        "c1": Fraction(c1),
        "c2": Fraction(c2),
        "cell_total": Fraction(c0 + c1 + c2),
        "b0": Fraction(b0),
        "b1": Fraction(b1),
        "b2": Fraction(b2),
        "betti_total": Fraction(sum(bq)),
        "euler_cells": Fraction(c0 - c1 + c2),
        "euler_betti": Fraction(b0 - b1 + b2),
        "torsion_count": Fraction(torsion_total),
        "has_torsion": Fraction(1 if torsion_total else 0),
        "euler_consistent": Fraction(1 if hs["euler_check"]["consistent"] else 0),
    }


def build_complex_library(extended: bool = False) -> List[Dict[str, Any]]:
    objs = []
    for key, builder in STANDARD_COMPLEXES.items():
        cx = builder()
        objs.append({"id": f"complex:{key}", "label": key,
                     "raw": key, "inv": complex_invariants(cx)})
    top = 15 if extended else 9
    for k in range(3, top):
        cx = ChainComplex.from_simplicial(f"cycleC{k}", _cycle_graph(k))
        objs.append({"id": f"complex:cycleC{k}", "label": f"cycleC{k}",
                     "raw": f"cycleC{k}", "inv": complex_invariants(cx)})
    cx2 = ChainComplex.from_simplicial("filled_triangle", [(0, 1, 2)])
    objs.append({"id": "complex:filled_triangle", "label": "filled_triangle",
                 "raw": "filled_triangle", "inv": complex_invariants(cx2)})
    if extended:
            # 带挠元的更多例子：CW 复形 ∂_2 = m·e（m 重贴合，H_1 含 Z_m 挠元）
            for m in (2, 3, 4, 5):
                cx = ChainComplex.from_cw(
                    f"moore_cw_{m}",
                    [["v"], ["e"], ["f"]],
                    {1: {"e": [(0, "v")]}, 2: {"f": [(m, "e")]}},
                )
                objs.append({"id": f"complex:moore_cw_{m}", "label": f"moore_cw_{m}",
                             "raw": f"moore_cw_{m}", "inv": complex_invariants(cx)})
            # **多挠元复形**：两个独立的 Z_2 挠元（H_1 = Z_2 ⊕ Z_2）
            cx2t = ChainComplex.from_cw(
                "double_torsion_cw", [["v"], ["a", "b"], ["U", "V"]],
                {1: {"a": [], "b": []}, 2: {"U": [(2, "a")], "V": [(2, "b")]}},
            )
            objs.append({"id": "complex:double_torsion_cw", "label": "double_torsion_cw",
                         "raw": "double_torsion_cw", "inv": complex_invariants(cx2t)})
            # Z_2 ⊕ Z_3：不同素数的挠元并存
            cx23 = ChainComplex.from_cw(
                "mixed_torsion_cw", [["v"], ["a", "b"], ["U", "V"]],
                {1: {"a": [], "b": []}, 2: {"U": [(2, "a")], "V": [(3, "b")]}},
            )
            objs.append({"id": "complex:mixed_torsion_cw", "label": "mixed_torsion_cw",
                         "raw": "mixed_torsion_cw", "inv": complex_invariants(cx23)})
    return objs


# ===========================================================================
# 7. 对象库的组装：统一出口 + 留出集切分
# ===========================================================================
FAMILY_NOTES = {
    "arithmetic": "整数 n（2..N）与一组经典算术函数。",
    "graph": "有限简单图：路、圈、完全图、星、完全二部图、轮、超立方、Petersen。",
    "group": " Cayley 表给出的有限群：循环群、二面体群、S3、循环群直积（含同构重复）。",
    "partition": "整数划分（含杨图共轭）",
    "complex": "有限链复形：标准 CW/Δ 复形 + 多边形边界 + 实心单形。",
}

NON_NUMERIC_KEYS = {"subgroup_enumeration_mode", "lagrange_checked", "is_group"}


def build_sites(int_max: int = 60, part_max: int = 8,
                extended: bool = False) -> Dict[str, Dict[str, Any]]:
    """构造五个对象族，并做确定性留出切分（每 4 个取第 4 个进检验集）。

    extended=True 时使用更大的对象库（用于**规模外推压力测试**）。
    """
    raw_objs: Dict[str, List[Dict[str, Any]]] = {}

    arith = []
    for n in range(2, int_max + 1):
        arith.append({"id": f"int:{n}", "label": f"n={n}", "raw": n,
                      "inv": arithmetic_invariants(n)})
    raw_objs["arithmetic"] = arith

    raw_objs["graph"] = build_graph_library(extended=extended)
    raw_objs["group"] = build_group_library(extended=extended)
    raw_objs["partition"] = build_partition_library(part_max)
    raw_objs["complex"] = build_complex_library(extended=extended)

    sites: Dict[str, Dict[str, Any]] = {}
    for fam, objs in raw_objs.items():
        # 不变量列：取各对象共有的数值字段（非数值的元信息另作处理）
        inv_names = sorted({key for key in objs[0]["inv"] if key not in NON_NUMERIC_KEYS})
        for o in objs[1:]:
            inv_names = sorted(set(inv_names) &
                               {key for key in o["inv"] if key not in NON_NUMERIC_KEYS})
        excluded: List[Dict[str, str]] = []
        if fam == "group":
            modes = {str(o["inv"].get("subgroup_enumeration_mode")) for o in objs}
            if len(modes) > 1:
                drop = ["proper_subgroups_count", "proper_subgroup_order_types",
                        "subgroups_only_trivial"]
                inv_names = [x for x in inv_names if x not in drop]
                excluded.append({
                    "reason": "子群枚举模式不统一（完备枚举 vs 有限生成元枚举），"
                              "不同对象之间的子群计数不可比",
                    "dropped_invariants": drop,
                })
        discovery = [o for i, o in enumerate(objs) if i % 4 != 3]
        test = [o for i, o in enumerate(objs) if i % 4 == 3]
        sites[fam] = {
            "family": fam,
            "note": FAMILY_NOTES.get(fam, ""),
            "objects": objs,
            "discovery": discovery,
            "test": test,
            "invariants": inv_names,
            "excluded_invariants": excluded,
            "counts": {"all": len(objs), "discovery": len(discovery), "test": len(test)},
        }
    return sites


# ===========================================================================
# 8. 已知定理 / 定义式 的识别表
# ===========================================================================
KNOWN_RELATIONS: List[Dict[str, Any]] = [
    {
        "id": "euler_poincare",
        "name": "欧拉-庞加莱公式（有限 CW 复形）",
        "family": "complex", "channel": "linear",
        "coeffs": {"euler_cells": 1, "euler_betti": -1},
        "note": "有限 CW 复形的链群交错和等于 Betti 数交错和；挠元不计入欧拉示性数。",
    },
    {
        "id": "handshaking",
        "name": "握手定理",
        "family": "graph", "channel": "linear",
        "coeffs": {"degree_sum": 1, "edges": -2},
        "note": "Σ deg(v) = 2|E|。",
    },
    {
        "id": "handshaking_monomial",
        "name": "握手定理（平均度形式）",
        "family": "graph", "channel": "monomial",
        "exponents": {"avg_degree": 1, "vertices": 1},
        "extra": {"edges": -1},
        "constant": 2,
        "note": "平均度 = 2|E|/|V|，即 deg_avg·|V|·|E|^{-1} = 2。",
    },
    {
        "id": "chi_ge_omega",
        "name": "χ(G) ≥ ω(G)（色数不小于团数）",
        "family": "graph", "channel": "inequality",
        "form": ("<=", "clique_number", ("chromatic_number",)),
        "note": "最大团中每点异色，经典且显然。",
    },
    {
        "id": "n_le_alpha_chi",
        "name": "α(G)·χ(G) ≥ |V|",
        "family": "graph", "channel": "inequality",
        "form": ("<=", "vertices", ("independent_number", "chromatic_number")),
        "note": "按颜色类划分：每色类为独立集，故 |V| ≤ α·χ。",
    },
    {
        "id": "phi_le_n_minus_1",
        "name": "φ(n) ≤ n-1",
        "family": "arithmetic", "channel": "inequality",
        "form": ("<=", "phi", "n"),
        "note": "等号当且仅当 n 为素数。此处以 ≤ 形式匹配。",
    },
    {
        "id": "partition_rank_conjugate",
        "name": "划分共轭反号 rank(λ') = -rank(λ)",
        "family": "partition", "channel": "linear",
        "coeffs": {"rank": 1, "conjugate_rank": 1},
        "note": "杨图共轭互换最大部与部数，故秩变号。",
    },
    {
        "id": "partition_conjugate_length",
        "name": "λ' 的最大部等于 λ 的部数",
        "family": "partition", "channel": "linear",
        "coeffs": {"conjugate_length": 1, "largest_part": -1},
        "note": "共轭的定义直接推论。",
    },
    {
        "id": "partition_distinct_parts_conjugate_invariant",
        "name": "λ 与 λ' 的不同部大小个数相等",
        "family": "partition", "channel": "linear",
        "coeffs": {"conjugate_distinct": 1, "distinct_parts": -1},
        "note": ("2026-09-19 由本引擎作为**候选**发现（当时在 n≤20 的全部 2713 个划分上"
                 "穷举无反例，但只标为 CANDIDATE_UNVERIFIED）；同日给出下面的证明。"
                 "**这是杨图共轭的直接推论，属教科书级别的简单事实，不是新数学**——"
                 "收录在此是为了让它成为搜索机制的校准件："
                 "机器能重新发现它，说明搜索通道没有只在产生垃圾。"),
        "proof": [
            "记 λ 的互异部大小为 v_1 > v_2 > ... > v_m，各值的重数为 c_1, ..., c_m，"
            "部数 k = c_1 + ... + c_m。所求即证 |D(λ')| = m。",
            "由共轭定义 λ'_i = #{j : λ_j ≥ i}。",
            "对任意 i，若 v_{t+1} < i ≤ v_t（约定 v_{m+1} = 0），"
            "则恰有前 t 组的部分满足 λ_j ≥ i，故 λ'_i = c_1 + ... + c_t =: C_t。",
            "对每个 t，区间 (v_{t+1}, v_t] 非空（因 v_t > v_{t+1} 且取整数 i = v_t 即可），"
            "所以每个 C_t 都确实作为 λ' 的某一项出现，即 D(λ') = {C_1, ..., C_m}。",
            "又因每个 c_t ≥ 1，故 C_1 < C_2 < ... < C_m 严格递增，m 个值两两互异。",
            "于是 |D(λ')| = m = |D(λ)|。证毕。",
        ],
        "proof_status": "已证明（人工核验前的草稿，见诚实红线五）",
    },
]

DEFINITIONAL: Dict[str, List[Dict[str, Any]]] = {
    "arithmetic": [
        {"name": "aliquot", "parents": {"sigma", "n"}},
        {"name": "abundance", "parents": {"sigma", "n"}},
        {"name": "phi_ratio", "parents": {"phi", "n"}},
        {"name": "n_over_rad", "parents": {"n", "rad"}},
    ],
    "graph": [
        {"name": "avg_degree", "parents": {"edges", "vertices"}},
        {"name": "degree_sum", "parents": {"vertices", "avg_degree"}},
        {"name": "connected", "parents": {"components"}},
    ],
    "partition": [
        {"name": "conjugate_rank", "parents": {"rank"}},
        {"name": "conjugate_length", "parents": {"largest_part"}},
    ],
    "complex": [
        {"name": "euler_cells", "parents": {"c0", "c1", "c2"}},
        {"name": "euler_betti", "parents": {"b0", "b1", "b2"}},
        {"name": "cell_total", "parents": {"c0", "c1", "c2"}},
        {"name": "betti_total", "parents": {"b0", "b1", "b2"}},
    ],
    "group": [],
}


def _norm_coeffs(coeffs: Dict[str, int]) -> Dict[str, int]:
    """归一化整系数：除以 gcd，约定首个（按名称排序）非零为正。"""
    items = [(k, v) for k, v in coeffs.items() if v]
    if not items:
        return {}
    g = 0
    for _, v in items:
        g = math.gcd(g, abs(v))
    d = {k: v // g for k, v in items}
    first = sorted(d)[0]
    if d[first] < 0:
        d = {k: -v for k, v in d.items()}
    return d


def recognize_known(family: str, channel: str, coeffs: Dict[str, int],
                    exponents: Optional[Dict[str, int]] = None,
                    constant: Optional[Fraction] = None,
                    ineq_form: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    """把候选关系与已知定理表对照。匹配不上返回 None（不猜测）。"""
    for k in KNOWN_RELATIONS:
        if k["family"] != family or k["channel"] != channel:
            continue
        if channel == "linear":
            want = dict(k.get("coeffs") or {})
            if want and _norm_coeffs(coeffs) == _norm_coeffs(want):
                return {"known_id": k["id"], "known_name": k["name"], "note": k["note"],
                        "proof": k.get("proof")}
        elif channel == "monomial":
            want = dict(k.get("exponents") or {})
            want.update(k.get("extra") or {})
            if want and _norm_coeffs(exponents or {}) == _norm_coeffs(want):
                if k.get("constant") is None or Fraction(k["constant"]) == constant:
                    return {"known_id": k["id"], "known_name": k["name"],
                            "note": k["note"], "proof": k.get("proof")}
        elif channel == "inequality":
            want = k.get("form")
            if want is not None and ineq_form is not None:
                if (want[0] == ineq_form[0] and want[1] == ineq_form[1]
                        and set(want[2]) == set(ineq_form[2])):
                    return {"known_id": k["id"], "known_name": k["name"],
                            "note": k["note"], "proof": k.get("proof")}
    return None


DEFINITIONAL_LINEAR: Dict[str, List[Dict[str, int]]] = {
    # 形如 Σ c·inv = 0 的**精确线性定义**。它们由本 module 自己引入，
    # 因此由它们线性组合出来的任何关系都**不是数学发现**。
    "arithmetic": [
        {"aliquot": 1, "sigma": -1, "n": 1},
    ],
    "partition": [
        {"rank": 1, "largest_part": -1, "length": 1},
        {"conjugate_rank": 1, "rank": 1},
        {"conjugate_length": 1, "largest_part": -1},
    ],
    "complex": [
        {"euler_cells": 1, "c0": -1, "c1": 1, "c2": -1},
        {"euler_betti": 1, "b0": -1, "b1": 1, "b2": -1},
        {"cell_total": 1, "c0": -1, "c1": -1, "c2": -1},
        {"betti_total": 1, "b0": -1, "b1": -1, "b2": -1},
    ],
    "graph": [],
    "group": [],
}


def implied_by_definitions(family: str, coeffs: Dict[str, int],
                           include_known: bool = True) -> bool:
    """
    判定候选线性关系是否落在"定义式 ∪ 已知定理"的线性张成里。
    做法：把这些式子写成行向量，检验加入候选后秩是否增加。
    落在其张成内的东西**不是数学发现**，只是已有事实的线性重排。
    """
    defs = list(DEFINITIONAL_LINEAR.get(family) or [])
    if include_known:
        for k in KNOWN_RELATIONS:
            if k["family"] == family and k.get("coeffs"):
                defs.append(dict(k["coeffs"]))
    if not defs or not coeffs:
        return False
    universe = sorted(set(coeffs) | {k for d in defs for k in d})
    pos = {nm: i for i, nm in enumerate(universe)}
    rows = []
    for d in defs:
        v = [Fraction(0)] * len(universe)
        for nm, c in d.items():
            v[pos[nm]] = Fraction(c)
        rows.append(v)
    cand = [Fraction(0)] * len(universe)
    for nm, c in coeffs.items():
        cand[pos[nm]] = Fraction(c)
    base_rank = len(_rref(rows, len(universe))[1]) if rows else 0
    aug_rank = len(_rref(rows + [cand], len(universe))[1])
    return base_rank == aug_rank


def _definitional_flag(family: str, support: Sequence[str]) -> Optional[str]:
    for entry in DEFINITIONAL.get(family, []):
        sup = set(support)
        parents = set(entry["parents"])
        target = entry["name"]
        if sup == parents | {target} or sup == parents:
            return f"涉及本 module 自行定义的派生量 {target}（非数学发现）"
    return None


# ===========================================================================
# 9. 三条搜索通道
# ===========================================================================
def _all_constant(site: Dict[str, Any], names: Sequence[str]) -> bool:
    """这些不变量在发现集上是否全部取常值（若是，则涉及它们的关系是退化的）。"""
    disc = site["discovery"]
    for nm in names:
        if len({Fraction(o["inv"][nm]) for o in disc}) > 1:
            return False
    return bool(names)


def _few_valued(site: Dict[str, Any], names: Sequence[str],
                max_distinct: int = 2) -> bool:
    """这些不变量在发现集上是否都只取极少几个值。

    若是，则涉及它们的关系很可能是**库的产物**（数据多样性不足造成的假规律），
    而不是数学规律——标记为 high 风险，但不据此删除，交付人工判断。
    """
    disc = site["discovery"]
    if not names:
        return True
    return all(len({Fraction(o["inv"][nm]) for o in disc}) <= max_distinct
               for nm in names)


def _value(obj: Dict[str, Any], name: str) -> Fraction:
    if name == CONST_TERM:
        return Fraction(1)
    return Fraction(obj["inv"][name])


def _residual(obj: Dict[str, Any], terms: Sequence[str], coeffs: Sequence[int]) -> Fraction:
    return sum((Fraction(c) * _value(obj, t) for t, c in zip(terms, coeffs)), Fraction(0))


def _statement(terms: Sequence[str], coeffs: Sequence[int]) -> str:
    parts = []
    for t, c in zip(terms, coeffs):
        if not c:
            continue
        sign = "+" if c > 0 else "-"
        mag = abs(c)
        core = t if mag == 1 else f"{mag}·{t}"
        parts.append(f"{sign} {core}")
    body = " ".join(parts)
    body = body[2:] if body.startswith("+ ") else "-" + body[2:]
    return f"{body} = 0"


def discover_linear(site: Dict[str, Any], max_support: int = 3) -> List[Dict[str, Any]]:
    """C1：含常数项的小支撑线性关系（Q 上精确求解）。"""
    names = list(site["invariants"])
    cols = names + [CONST_TERM]
    disc = site["discovery"]
    out: List[Dict[str, Any]] = []
    seen_keys = set()
    for k in range(2, max_support + 1):
        for combo in itertools.combinations(range(len(cols)), k):
            sub = [[_value(o, cols[c]) for c in combo] for o in disc]
            rank, rels = _rank_and_relations(sub, k)
            if rank >= k:
                continue
            for cv in rels:
                if not any(cv):
                    continue
                terms = [cols[c] for c in combo]
                real = {t: c for t, c in zip(terms, cv) if c and t != CONST_TERM}
                if len(real) < 1:
                    continue
                key = tuple(sorted((t, c) for t, c in zip(terms, cv) if c))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                const_coeff = 0
                for t, c in zip(terms, cv):
                    if t == CONST_TERM:
                        const_coeff = c
                # 退化判定：所有参与量在发现集上取常值
                degenerate = all(
                    len({Fraction(o["inv"][t]) for o in disc}) == 1 for t in real)
                failures = [o for o in site["test"] if _residual(o, terms, cv) != 0]
                free_checks = len(disc) - rank
                rec = recognize_known(site["family"], "linear", real)
                out.append({
                    "family": site["family"],
                    "channel": "linear",
                    "statement": _statement(terms, cv),
                    "terms": {t: c for t, c in zip(terms, cv) if c},
                    "has_constant_term": bool(const_coeff),
                    "n_discovery_objects": len(disc),
                    "submatrix_rank": rank,
                    "independent_checks": free_checks,
                    "evidence_is_nontrivial": free_checks >= 3,
                    "degenerate_on_discovery_set": degenerate,
                    "definitional": _definitional_flag(site["family"], list(real)),
                    "implied_by_definitions": implied_by_definitions(
                        site["family"], {t: c for t, c in zip(terms, cv) if c},
                        include_known=False),
                    "library_artifact_risk": (
                        len(real) >= 2 and _few_valued(site, list(real))),
                    "implied_using_known": implied_by_definitions(
                        site["family"], {t: c for t, c in zip(terms, cv) if c},
                        include_known=True),
                    "recognition": rec,
                    "test": _pack_test(site, failures, terms, cv),
                    "evidence_level": "L2（精确有理算术，有限对象库）",
                    "notes": EVIDENCE_NOTE,
                })
    return out


def _pack_test(site: Dict[str, Any], failures: List[Dict[str, Any]],
               terms: Sequence[str], coeffs: Sequence[int]) -> Dict[str, Any]:
    n_test = len(site["test"])
    ces = []
    for o in failures[:5]:
        ces.append({"object": o["id"], "label": o["label"],
                    "residual": str(_residual(o, terms, coeffs))})
    return {
        "n_test_objects": n_test,
        "n_failures": len(failures),
        "survived": len(failures) == 0,
        "counterexamples": ces,
    }


def discover_monomial(site: Dict[str, Any], max_support: int = 3,
                      exponents: Sequence[int] = (-2, -1, 1, 2)) -> List[Dict[str, Any]]:
    """C2：Π inv_i^{e_i} = const（发现集上恒定的单项式组合）。"""
    names = list(site["invariants"])
    disc = site["discovery"]
    out: List[Dict[str, Any]] = []
    seen = set()
    guard = 10 ** 14
    for k in range(2, max_support + 1):
        for combo in itertools.combinations(names, k):
            for exps in itertools.product(exponents, repeat=k):
                if math.gcd(*[abs(e) for e in exps]) != 1:
                    continue
                usable = [o for o in disc
                          if all(Fraction(o["inv"][nm]) != 0 for nm in combo)]
                if len(usable) != len(disc) or len(usable) < 4:
                    continue  # 存在零基底时跳过：该关系在此情形下无意义
                vals = []
                too_big = False
                for o in usable:
                    p = Fraction(1)
                    for nm, e in zip(combo, exps):
                        p *= Fraction(o["inv"][nm]) ** e
                        if abs(p.numerator) > guard or p.denominator > guard:
                            too_big = True
                            break
                    if too_big:
                        break
                    vals.append(p)
                if too_big:
                    continue
                c = vals[0] if vals else None
                if too_big or c is None or len(set(vals)) != 1:
                    continue
                # 规范形：若按名称排序后首个非零指数为负，则整体取倒数
                # （Π = c 与 Π^{-1} = 1/c 是同一条关系，必须去重）
                order = sorted(range(k), key=lambda i: combo[i])
                if exps[order[0]] < 0:
                    exps = tuple(-e for e in exps)
                    c = Fraction(1, 1) / c
                key = (tuple(zip(combo, exps)), c)
                if key in seen:
                    continue
                seen.add(key)
                degenerate = _all_constant(site, list(combo))
                failures = []
                not_evaluable = 0
                for o in site["test"]:
                    if any(Fraction(o["inv"][nm]) == 0 for nm in combo):
                        not_evaluable += 1
                        continue
                    p = Fraction(1)
                    for nm, e in zip(combo, exps):
                        p *= Fraction(o["inv"][nm]) ** e
                    if p != c:
                        failures.append({"object": o["id"], "label": o["label"],
                                         "lhs": str(p), "expected": str(c)})
                n_fail = len(failures)
                rec = recognize_known(site["family"], "monomial",
                                      {}, dict(zip(combo, exps)), c)
                mono_txt = "·".join(
                    nm if e == 1 else f"{nm}^{e}" for nm, e in zip(combo, exps))
                out.append({
                    "family": site["family"],
                    "channel": "monomial",
                    "statement": f"{mono_txt} = {c}",
                    "exponents": dict(zip(combo, exps)),
                    "constant": str(c),
                    "n_discovery_objects": len(disc),
                    "independent_checks": len(disc) - 1,
                    "evidence_is_nontrivial": len(disc) >= 4,
                    "degenerate_on_discovery_set": degenerate,
                    "definitional": _definitional_flag(site["family"], list(combo)),
                    "recognition": rec,
                    "test": {
                        "n_test_objects": len(site["test"]),
                        "n_failures": n_fail,
                        "not_evaluable_on_test": not_evaluable,
                        "survived": n_fail == 0,
                        "counterexamples": failures[:5],
                    },
                    "evidence_level": "L2（精确有理算术，有限对象库）",
                    "assumptions": ["参与各量在对象上非零才有意义"],
                    "notes": EVIDENCE_NOTE,
                })
    return out


def _compare(op: str, lhs: Fraction, rhs: Fraction) -> bool:
    return lhs <= rhs if op == "<=" else lhs >= rhs


def discover_inequality(site: Dict[str, Any]) -> List[Dict[str, Any]]:
    """C3：Graffiti 传统的不等式搜索（要求尖锐且有严格处）。"""
    names = list(site["invariants"])
    disc = site["discovery"]
    out: List[Dict[str, Any]] = []

    def try_form(lhs: str, rhs_terms: Sequence[str], kind: str):
        if lhs in rhs_terms:
            return
        op = "<="
        holds = True
        eq_hit = False
        strict_hit = False
        slack_min = None
        for o in disc:
            a = Fraction(o["inv"][lhs])
            if kind == "sum":
                b = sum((Fraction(o["inv"][t]) for t in rhs_terms), Fraction(0))
            else:
                b = Fraction(1)
                for t in rhs_terms:
                    b *= Fraction(o["inv"][t])
            if not _compare(op, a, b):
                holds = False
                break
            slack = b - a
            if slack == 0:
                eq_hit = True
            else:
                strict_hit = True
                if slack_min is None or slack < slack_min:
                    slack_min = slack
        if not (holds and eq_hit and strict_hit):
            return
        failures = []
        for o in site["test"]:
            a = Fraction(o["inv"][lhs])
            if kind == "sum":
                b = sum((Fraction(o["inv"][t]) for t in rhs_terms), Fraction(0))
            else:
                b = Fraction(1)
                for t in rhs_terms:
                    b *= Fraction(o["inv"][t])
            if not _compare(op, a, b):
                failures.append({"object": o["id"], "label": o["label"],
                                 "lhs": str(a), "rhs": str(b)})
        rhs_txt = ("+".join(sorted(rhs_terms)) if kind == "sum"
                   else "·".join(sorted(rhs_terms)))
        form = ("<=", lhs, tuple(sorted(rhs_terms)))
        rec = recognize_known(site["family"], "inequality", {}, None, None, form)
        out.append({
            "family": site["family"],
            "channel": "inequality",
            "statement": f"{lhs} ≤ {rhs_txt}",
            "lhs": lhs,
            "rhs_terms": list(rhs_terms),
            "rhs_kind": kind,
            "sharp_on_discovery": True,
            "min_slack_on_discovery": str(slack_min),
            "n_discovery_objects": len(disc),
            "degenerate_on_discovery_set": _all_constant(site, [lhs] + list(rhs_terms)),
            "definitional": _definitional_flag(site["family"],
                                               [lhs] + list(rhs_terms)),
            "recognition": rec,
            "test": {
                "n_test_objects": len(site["test"]),
                "n_failures": len(failures),
                "survived": len(failures) == 0,
                "counterexamples": failures[:5],
            },
            "evidence_level": "L2（精确有理算术，有限对象库）",
            "notes": EVIDENCE_NOTE,
        })

    for a in names:
        for b in names:
            if a != b:
                try_form(a, (b,), "sum")
    for a in names:
        for pair in itertools.combinations([x for x in names if x != a], 2):
            try_form(a, pair, "sum")
            try_form(a, pair, "product")
    return out


# ===========================================================================
# 10. 理论体系网：不变量之间的可定义性偏序
# ===========================================================================
def theory_net(site: Dict[str, Any],
               accepted: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    由全部对象构成的不变量矩阵出发：
      - RREF 的主元列 = 一组**线性独立不变量基**；
      - 其余不变量由主元列唯一线性表出（表出系数取自 RREF，可精确复核）；
      - 由已接受（存活）的稀疏关系给出**简约式表出**（支撑 ≤3）。
    """
    names = list(site["invariants"])
    objs = site["objects"]
    if not names or not objs:
        return {"family": site["family"], "basis": [], "derived": [], "note": "空库"}
    rows = [[Fraction(o["inv"][nm]) for nm in names] for o in objs]
    m, pivots = _rref(rows, len(names))
    basis = [names[c] for c in pivots]
    free_cols = [c for c in range(len(names)) if c not in pivots]

    derived = []
    for c in free_cols:
        expr = {names[pivots[i]]: m[i][c] for i in range(len(pivots)) if m[i][c] != 0}
        # 精确复核
        ok = True
        for o in objs:
            v = sum((coeff * Fraction(o["inv"][k]) for k, coeff in expr.items()),
                    Fraction(0))
            if v != Fraction(o["inv"][names[c]]):
                ok = False
                break
        derived.append({
            "invariant": names[c],
            "expressed_by": {k: str(v) for k, v in expr.items()},
            "support_size": len(expr),
            "parsimonious": len(expr) <= 3,
            "reverified_exactly": ok,
        })

    # 简约式：若某不变量在某条存活关系中系数为 ±1，则可用该关系解出
    from operator import itemgetter
    parsimonious_map: Dict[str, Dict[str, Any]] = {}
    for rel in accepted:
        if rel["channel"] != "linear":
            continue
        terms = rel["terms"]
        for tgt, co in terms.items():
            if tgt == CONST_TERM or abs(co) != 1:
                continue
            rhs = {k: Fraction(-v) / Fraction(co) for k, v in terms.items()
                   if k != tgt and k != CONST_TERM}
            if not rhs:
                continue
            const_part = Fraction(-terms.get(CONST_TERM, 0)) / Fraction(co)
            prev = parsimonious_map.get(tgt)
            if prev is None or len(rhs) < prev["support_size"]:
                parsimonious_map[tgt] = {
                    "invariant": tgt,
                    "via_relation": rel["statement"],
                    "rhs": {k: str(v) for k, v in rhs.items()},
                    "constant": str(const_part),
                    "support_size": len(rhs),
                }
    return {
        "family": site["family"],
        "n_objects": len(objs),
        "n_invariants": len(names),
        "rank": len(pivots),
        "independent_basis": basis,
        "derived_invariants": sorted(derived, key=itemgetter("support_size")),
        "parsimonious_expressions": sorted(parsimonious_map.values(),
                                           key=itemgetter("support_size")),
        "note": ("主元/自由列的划分依赖**当前对象库**：换一批对象结论就会变。"
                 "因此这里的'独立基'是库内概念，不是理论的独立性判定。"),
    }


def _rhs_values(cand: Dict[str, Any], objs: Sequence[Dict[str, Any]]) -> List[Fraction]:
    out = []
    for o in objs:
        if cand["rhs_kind"] == "sum":
            v = sum((Fraction(o["inv"][t]) for t in cand["rhs_terms"]), Fraction(0))
        else:
            v = Fraction(1)
            for t in cand["rhs_terms"]:
                v *= Fraction(o["inv"][t])
        out.append(v)
    return out


def pareto_filter_inequalities(site: Dict[str, Any],
                               cands: List[Dict[str, Any]]
                               ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    按 (左端, 右端类型) 分组做**帕累托收敛**：
    若另一条候选在**每个**发现集对象上给出更紧（或相等）的上界，且项数不多于本条，
    则本条被支配、剔除。目的是把"同一事实的多种松写法"压成一条最紧的。
    这不是数学上的蕴含判定，只是**记账上的去重**。
    """
    disc = site["discovery"]
    kept: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for c in cands:
        groups.setdefault((c["lhs"], c["rhs_kind"]), []).append(c)
    for _, group in groups.items():
        vecs = {id(c): _rhs_values(c, disc) for c in group}
        for c in group:
            dominated = False
            for d in group:
                if d is c or len(d["rhs_terms"]) > len(c["rhs_terms"]):
                    continue
                dv, cv = vecs[id(d)], vecs[id(c)]
                tighter_or_equal = all(a <= b for a, b in zip(dv, cv))
                strictly_better = (any(a < b for a, b in zip(dv, cv))
                                   or (dv == cv and len(d["rhs_terms"]) < len(c["rhs_terms"])))
                if tighter_or_equal and strictly_better:
                    dominated = True
                    c["dominated_by"] = d["statement"]
                    break
            # 注意：**已识别出为已知定理的候选一律保留**，即使被更紧的界支配；
            # 它们是这套搜索机制自身的校准件，不能因为"不够紧"而被丢掉。
            if dominated and c["recognition"] is None:
                removed.append(c)
            else:
                kept.append(c)
    return kept, removed


# ===========================================================================
# 11. 规模外推压力测试：把候选拿到更大的对象库上去找反例
# ===========================================================================
def violations_on(cand: Dict[str, Any],
                  objs: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], int]:
    """在给定对象集合上检验候选关系，返回 (违规列表, 因缺不变量而跳过的对象数)。"""
    bad: List[Dict[str, str]] = []
    skipped = 0
    for o in objs:
        inv = o["inv"]
        if cand["channel"] == "linear":
            need = [t for t in cand["terms"] if t != CONST_TERM]
            if any(t not in inv for t in need):
                skipped += 1
                continue
            res = sum((Fraction(c) * (Fraction(1) if t == CONST_TERM
                                      else Fraction(inv[t]))
                       for t, c in cand["terms"].items()), Fraction(0))
            if res != 0:
                bad.append({"object": o["id"], "detail": f"残差 {res}"})
        elif cand["channel"] == "monomial":
            need = list(cand["exponents"])
            if any(t not in inv for t in need):
                skipped += 1
                continue
            if any(Fraction(inv[t]) == 0 for t in need):
                skipped += 1
                continue
            prod = Fraction(1)
            for t, e in cand["exponents"].items():
                prod *= Fraction(inv[t]) ** int(e)
            if prod != Fraction(cand["constant"]):
                bad.append({"object": o["id"],
                            "detail": f"{o['label']}: 左侧={prod}，期望={cand['constant']}"})
        else:  # inequality
            need = [cand["lhs"]] + list(cand["rhs_terms"])
            if any(t not in inv for t in need):
                skipped += 1
                continue
            lhs = Fraction(inv[cand["lhs"]])
            if cand["rhs_kind"] == "sum":
                rhs = sum((Fraction(inv[t]) for t in cand["rhs_terms"]), Fraction(0))
            else:
                rhs = Fraction(1)
                for t in cand["rhs_terms"]:
                    rhs *= Fraction(inv[t])
            if lhs > rhs:
                bad.append({"object": o["id"],
                            "detail": f"{o['label']}: {lhs} > {rhs}"})
    return bad, skipped


def stress_test(cands: List[Dict[str, Any]],
                ext_site: Dict[str, Any]) -> Dict[str, Any]:
    objs = ext_site["objects"]
    survived, killed = [], []
    for c in cands:
        bad, skipped = violations_on(c, objs)
        rec = {
            "statement": c["statement"],
            "channel": c["channel"],
            "status_before": c.get("status"),
            "n_extended_objects": len(objs),
            "n_skipped": skipped,
            "n_violations": len(bad),
            "survived": not bad,
            "examples": bad[:3],
        }
        (survived if not bad else killed).append(rec)
    return {
        "extended_objects": len(objs),
        "n_tested": len(cands),
        "n_survived": len(survived),
        "n_falsified": len(killed),
        "falsified_details": killed,
    }


# ===========================================================================
# 12. 总入口
# ===========================================================================
DEFAULT_CONFIG = {
    "int_max": 60, "part_max": 8,
    "extended": {"int_max": 160, "part_max": 11, "extended": True},
}


def forge_all(int_max: int = 60, part_max: int = 8,
              run_stress: bool = True) -> Dict[str, Any]:
    sites = build_sites(int_max=int_max, part_max=part_max)
    result: Dict[str, Any] = {
        "scope": SCOPE_NOTE,
        "evidence": EVIDENCE_NOTE,
        "generated_at_note": "由 theoryforge.forge_all 生成",
        "config": {"int_max": int_max, "part_max": part_max},
        "families": {},
    }
    ext_cfg = DEFAULT_CONFIG["extended"]
    ext_sites = (build_sites(int_max=ext_cfg["int_max"], part_max=ext_cfg["part_max"],
                             extended=True) if run_stress else {})
    for fam, site in sites.items():
        lin = discover_linear(site)
        mono = discover_monomial(site)
        ineq_raw = discover_inequality(site)
        ineq, dominated = pareto_filter_inequalities(site, ineq_raw)
        cands = lin + mono + ineq
        for c in cands:
            c["status"] = _classify(c)
        accepted = [c for c in cands if c["status"] == "CANDIDATE_UNVERIFIED"]
        fam_out: Dict[str, Any] = {
            "note": site["note"],
            "counts": site["counts"],
            "n_invariants": len(site["invariants"]),
            "invariants": site["invariants"],
            "excluded_invariants": site["excluded_invariants"],
            "channel_counts": {
                "linear": len(lin), "monomial": len(mono),
                "inequality_raw": len(ineq_raw),
                "inequality_after_pareto": len(ineq),
                "inequality_dominated_removed": len(dominated),
            },
            "candidates": cands,
            # 被帕累托过滤剔除的候选**保留在此**（不删除，只是不当作主候选）
            "dominated_inequalities": [
                {"statement": c["statement"], "dominated_by": c.get("dominated_by")}
                for c in dominated
            ],
            "accepted_count": len(accepted),
            "theory_net": theory_net(site, accepted),
        }
        if run_stress and fam in ext_sites:
            fam_out["stress"] = stress_test(accepted, ext_sites[fam])
            fam_out["stress"]["extended_note"] = (
                f"扩展库：整数 ≤ {ext_cfg['int_max']}，划分 ≤ {ext_cfg['part_max']}，"
                "图/群/复形族追加更大实例")
        result["families"][fam] = fam_out

    total = {"candidates": 0, "accepted": 0, "stress_tested": 0, "stress_survived": 0}
    for fam_out in result["families"].values():
        total["candidates"] += len(fam_out["candidates"])
        total["accepted"] += fam_out["accepted_count"]
        if "stress" in fam_out:
            total["stress_tested"] += fam_out["stress"]["n_tested"]
            total["stress_survived"] += fam_out["stress"]["n_survived"]
    result["summary"] = total
    return result


def _classify(c: Dict[str, Any]) -> str:
    """按诚实口径给候选关系贴状态标签。**任何情况都不会给出 PROVEN。**"""
    # 留出集上的失败最优先：即便它长得像某条已知定理，被证伪的事实优先记录。
    if not c["test"]["survived"]:
        return "FALSIFIED_ON_HELD_OUT"
    if c.get("degenerate_on_discovery_set"):
        return "DEGENERATE"
    if c.get("implied_by_definitions"):
        return "IMPLIED_BY_DEFINITIONS"
    if c["recognition"] is not None:
        return "KNOWN_THEOREM_REDISCOVERED"
    if c.get("implied_using_known"):
        return "CONSEQUENCE_OF_KNOWN"
    if c.get("definitional"):
        return "DEFINITIONAL"
    if not c.get("evidence_is_nontrivial", True):
        return "UNDERDETERMINED"
    return "CANDIDATE_UNVERIFIED"
