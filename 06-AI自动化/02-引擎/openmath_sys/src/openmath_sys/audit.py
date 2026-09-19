# -*- coding: utf-8 -*-
"""
独立审计模块（S8 的计算核心）。

它做的事情可以用一句话概括：**不信任本仓库自己算出来的任何数字**。

方法上有三条硬约束：
  1. 每一项的参考值要么来自教科书已知值，要么来自**与被测代码完全不同的算法**
     （例如 li(x) 用 Ei 幂级数对照 Simpson 积分；划分数用五边形数递推对照直接生成；
     生成树数用 Bareiss 行列式对照库内的基尔霍夫实现）。
  2. 审计**不修改**被审对象，只报告差异。修不修、怎么修由人决定。
  3. 审计自身也可能出错，所以每一条 FAIL 都必须带上可复核的具体数值，
     不允许只写"不一致"。

已实测的教训（2026-09-19 首次全量审计）：
  - 审计的**参考值本身**也可能是错的：我一度认为 li(10)=5.120，
    那其实是 ∫₂¹⁰ dt/ln t；真值 6.1656。被测代码是对的，参考错了。
  - 最严重的问题不在算术，而在**判定口径**：恒等式验证器把超出能力范围的式子
    也判了真伪，制造了十几条假阴性（详见 numeric.screen_identity）。
"""
from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction
from typing import Any, Dict, List, Sequence, Tuple

from . import numbertheory as nt
from . import structure as st
from . import theoryforge as tf
from . import sequences as sq
from .numeric import verify_identity

EULER_GAMMA = 0.5772156649015328606

SCOPE_NOTE = (
    "本模块只审计**有限、可枚举、有独立参照**的计算：数论函数、素数计数、"
    "划分函数、图不变量、有限群、有限链复形同调、恒等式验证器。"
    "它不审计任何关于未解猜想的论断，也不把'审计通过'解释成'结论正确'。"
)


# ===========================================================================
# 一、独立参考算法（刻意与被审实现走不同路径）
# ===========================================================================
def indep_li(x: float) -> float:
    """li(x) = Ei(ln x)，用 Ei 的幂级数 Ei(z)=γ+ln|z|+Σ z^k/(k·k!) 独立计算。"""
    z = math.log(x)
    s, term = 0.0, 1.0
    for k in range(1, 300):
        term *= z / k
        s += term / k
        if abs(term / k) < 1e-17:
            break
    return EULER_GAMMA + math.log(z) + s


def indep_phi(n: int) -> int:
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)


def indep_tau(n: int) -> int:
    return sum(1 for d in range(1, n + 1) if n % d == 0)


def indep_sigma(n: int) -> int:
    return sum(d for d in range(1, n + 1) if n % d == 0)


def indep_rad(n: int) -> int:
    m, r, p = n, 1, 2
    while p * p <= m:
        if m % p == 0:
            r *= p
            while m % p == 0:
                m //= p
        p += 1
    return r * m


def indep_partitions(n: int) -> int:
    """欧拉五边形数递推：p(n) = Σ (-1)^{k-1} [p(n-g_k) + p(n-g_{-k})]。"""
    p = [0] * (n + 1)
    p[0] = 1
    for i in range(1, n + 1):
        s, k, sign = 0, 1, 1
        while True:
            g1 = k * (3 * k - 1) // 2
            if g1 > i:
                break
            s += sign * p[i - g1]
            g2 = k * (3 * k + 1) // 2
            if g2 <= i:
                s += sign * p[i - g2]
            k += 1
            sign = -sign
        p[i] = s
    return p[n]


def _lap_minor_det(nv: int, edges: Sequence[Tuple[int, int]]) -> int:
    """矩阵树定理的另一种写法：Bareiss 精确消元（库内用的是同一思想的不同实现）。"""
    L = [[0] * nv for _ in range(nv)]
    for a, b in edges:
        L[a][a] += 1
        L[b][b] += 1
        L[a][b] -= 1
        L[b][a] -= 1
    if nv <= 1:
        return 1
    M = [[Fraction(x) for x in row[:-1]] for row in L[:-1]]
    m = len(M)
    det = Fraction(1)
    for c in range(m):
        piv = None
        for r_ in range(c, m):
            if M[r_][c] != 0:
                piv = r_
                break
        if piv is None:
            return 0
        if piv != c:
            M[c], M[piv] = M[piv], M[c]
            det = -det
        det *= M[c][c]
        for r_ in range(c + 1, m):
            if M[r_][c] != 0:
                f = M[r_][c] / M[c][c]
                for cc in range(c, m):
                    M[r_][cc] -= f * M[c][cc]
    return int(det)


def _adj(nv: int, edges) -> List[set]:
    adj = [set() for _ in range(nv)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def indep_independent_number(nv: int, edges) -> int:
    adj = _adj(nv, edges)
    best = 0
    for mask in range(1 << nv):
        if mask.bit_count() <= best:
            continue
        if all(not (adj[v] & {u for u in range(nv) if (mask >> u) & 1})
               for v in range(nv) if (mask >> v) & 1):
            best = mask.bit_count()
    return best


def indep_clique_number(nv: int, edges) -> int:
    adj = _adj(nv, edges)
    best = 0
    for mask in range(1 << nv):
        if mask.bit_count() <= best:
            continue
        vs = [v for v in range(nv) if (mask >> v) & 1]
        if all(u in adj[v] for v in vs for u in vs if u != v):
            best = len(vs)
    return best


def indep_chromatic_number(nv: int, edges) -> int:
    adj = [sorted(s) for s in _adj(nv, edges)]
    for k in range(1, nv + 1):
        color = [0] * nv

        def bt(i: int) -> bool:
            if i == nv:
                return True
            for c in range(1, k + 1):
                if all(color[u] != c for u in adj[i] if u < i):
                    color[i] = c
                    if bt(i + 1):
                        return True
                    color[i] = 0
            return False
        if bt(0):
            return k
    return nv


def indep_girth(nv: int, edges):
    adj = [[] for _ in range(nv)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    best = None
    for s in range(nv):
        dist = [-1] * nv
        par = [-1] * nv
        dist[s] = 0
        q = [s]
        while q:
            nq = []
            for v in q:
                for u in adj[v]:
                    if dist[u] == -1:
                        dist[u] = dist[v] + 1
                        par[u] = v
                        nq.append(u)
                    elif par[v] != u and par[u] != v and u != v:
                        cyc = dist[v] + dist[u] + 1
                        if best is None or cyc < best:
                            best = cyc
            q = nq
    return best


def indep_diameter(nv: int, edges) -> int:
    adj = [[] for _ in range(nv)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    inf = float("inf")
    best = 0
    for s in range(nv):
        dist = [inf] * nv
        dist[s] = 0
        q = [s]
        while q:
            nq = []
            for v in q:
                for u in adj[v]:
                    if dist[u] == inf:
                        dist[u] = dist[v] + 1
                        nq.append(u)
            q = nq
        for u in range(nv):
            if dist[u] < inf:
                best = max(best, dist[u])
    return best


def indep_subgroups(table) -> List[set]:
    """暴力枚举全部子集判定子群（与库内的枚举策略不同，纯 2^n 穷举）。"""
    n = len(table)
    out = []
    for r in range(1, n + 1):
        for comb in itertools.combinations(range(n), r):
            S = set(comb)
            if all(table[a][b] in S for a in S for b in S):
                out.append(S)
    return out


def indep_center_size(table) -> int:
    n = len(table)
    return sum(1 for a in range(n)
               if all(table[a][b] == table[b][a] for b in range(n)))


def indep_class_number(table) -> int:
    n = len(table)
    ident = None
    for i in range(n):
        if all(table[i][j] == j and table[j][i] == j for j in range(n)):
            ident = i
            break
    if ident is None:
        return -1
    inv = [0] * n
    for a in range(n):
        for b in range(n):
            if table[a][b] == ident:
                inv[a] = b
                break
    seen, count = set(), 0
    for a in range(n):
        if a in seen:
            continue
        count += 1
        seen |= {table[table[g][a]][inv[g]] for g in range(n)}
    return count


def _dense_boundary(cx, i: int):
    bd = cx.boundary
    if i not in bd:
        return None
    dims = [len(g) for g in cx.gens]
    rows = dims[i - 1] if i - 1 < len(dims) else 0
    cols = dims[i] if i < len(dims) else 0
    M = [[0] * cols for _ in range(rows)]
    for c, chain in enumerate(bd[i]):
        for coef, gidx in chain:
            if 0 <= gidx < rows:
                M[gidx][c] += coef
    return M


def _rank_gf(M, p: int) -> int:
    if not M or not M[0]:
        return 0
    A = [[x % p for x in row] for row in M]
    rows, cols = len(A), len(A[0])
    r = 0
    for c in range(cols):
        piv = None
        for i in range(r, rows):
            if A[i][c] % p:
                piv = i
                break
        if piv is None:
            continue
        A[r], A[piv] = A[piv], A[r]
        inv = pow(A[r][c], p - 2, p)
        A[r] = [(x * inv) % p for x in A[r]]
        for i in range(rows):
            if i != r and A[i][c] % p:
                f = A[i][c]
                A[i] = [(A[i][j] - f * A[r][j]) % p for j in range(cols)]
        r += 1
    return r


def indep_betti_gf(cx, p: int) -> List[int]:
    dims = [len(g) for g in cx.gens]
    betti = []
    for i in range(len(dims)):
        mi = _dense_boundary(cx, i)
        mj = _dense_boundary(cx, i + 1)
        r_i = _rank_gf(mi, p) if mi else 0
        r_j = _rank_gf(mj, p) if mj else 0
        betti.append(dims[i] - r_i - r_j)
    return betti


# ===========================================================================
# 二、各维度审计
# ===========================================================================
class Auditor:
    def __init__(self) -> None:
        self.sections: List[Dict[str, Any]] = []

    def section(self, name: str, note: str) -> Dict[str, Any]:
        rec = {"name": name, "note": note, "checks": 0, "failures": []}
        self.sections.append(rec)
        return rec

    @staticmethod
    def check(rec: Dict[str, Any], what: str, got, want) -> None:
        rec["checks"] += 1
        if got != want:
            rec["failures"].append({"item": what, "got": str(got), "want": str(want)})

    @staticmethod
    def close(rec: Dict[str, Any], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        rec["passed"] = rec["checks"] - len(rec["failures"])
        rec["ok"] = not rec["failures"]
        if extra:
            rec.update(extra)
        return rec


def audit_arithmetic(aud: Auditor, n_max: int = 120) -> Dict[str, Any]:
    rec = aud.section("arithmetic", "算术函数 φ/τ/σ/rad：库内实现 vs 暴力定义（互素计数、除数枚举、质因数分解）")
    for n in range(1, n_max + 1):
        inv = tf.arithmetic_invariants(n)
        aud.check(rec, f"phi({n})", inv["phi"], Fraction(indep_phi(n)))
        aud.check(rec, f"tau({n})", inv["tau"], Fraction(indep_tau(n)))
        aud.check(rec, f"sigma({n})", inv["sigma"], Fraction(indep_sigma(n)))
        aud.check(rec, f"rad({n})", inv["rad"], Fraction(indep_rad(n)))
    return aud.close(rec, {"n_max": n_max})


def audit_primes(aud: Auditor) -> Dict[str, Any]:
    rec = aud.section("primes", "素数计数 π(x) 对照教科书已知值")
    known = {10: 4, 100: 25, 1000: 168, 10000: 1229, 100000: 9592}
    for x, want in sorted(known.items()):
        aud.check(rec, f"pi({x})", len(nt.sieve_primes(x)), want)
    return aud.close(rec, {"known_values": known})


def audit_li(aud: Auditor, tol: float = 1e-9) -> Dict[str, Any]:
    rec = aud.section("logarithmic_integral", "li(x)：库内 Simpson 积分 vs Ei 幂级数（完全不同的算法）")
    for x in (2.5, 5.0, 10.0, 100.0, 1000.0, 1e4, 1e5, 1e6):
        got, want = nt.logarithmic_integral(x), indep_li(x)
        rel = abs(got - want) / max(1.0, abs(want))
        aud.check(rec, f"li({x:g}) rel_err<=1e-9", rel <= tol, True)
        rec.setdefault("details", []).append({"x": x, "li": got, "ei": want, "rel_err": rel})
    return aud.close(rec)


def audit_partitions(aud: Auditor, n_max: int = 40) -> Dict[str, Any]:
    rec = aud.section("partitions", "划分数 p(n)：直接生成 vs 欧拉五边形数递推；并校验共轭是对合")
    for n in range(0, n_max + 1):
        aud.check(rec, f"p({n})", len(tf._partitions(n)), indep_partitions(n))
    conj_bad = 0
    for n in range(1, 25):
        for lam in tf._partitions(n):
            if tf._conjugate(tf._conjugate(lam)) != lam:
                conj_bad += 1
    aud.check(rec, "conjugate 是对合 (n<=24)", conj_bad, 0)
    return aud.close(rec, {"n_max": n_max, "conjugate_failures": conj_bad})


def audit_graphs(aud: Auditor, nv_cap: int = 12) -> Dict[str, Any]:
    rec = aud.section("graphs", "图不变量：库内实现 vs 独立暴力（位掩码枚举独立集/团、回溯染色、BFS 围长与直径、Bareiss 生成树）")
    lib = tf.build_graph_library()
    for o in lib:
        nv, edges = o["raw"]
        inv = o["inv"]
        aud.check(rec, f"{o['label']}.vertices", inv["vertices"], Fraction(nv))
        aud.check(rec, f"{o['label']}.edges", inv["edges"], Fraction(len(edges)))
        aud.check(rec, f"{o['label']}.degree_sum", inv["degree_sum"], Fraction(2 * len(edges)))
        aud.check(rec, f"{o['label']}.spanning_trees", inv["spanning_trees"],
                  Fraction(_lap_minor_det(nv, edges)))
        g = indep_girth(nv, edges)
        aud.check(rec, f"{o['label']}.girth", inv["girth"], Fraction(g if g is not None else 0))
        aud.check(rec, f"{o['label']}.diameter", inv["diameter"], Fraction(indep_diameter(nv, edges)))
        if nv <= nv_cap:
            aud.check(rec, f"{o['label']}.independent_number", inv["independent_number"],
                      Fraction(indep_independent_number(nv, edges)))
            aud.check(rec, f"{o['label']}.clique_number", inv["clique_number"],
                      Fraction(indep_clique_number(nv, edges)))
        if nv <= 10:
            aud.check(rec, f"{o['label']}.chromatic_number", inv["chromatic_number"],
                      Fraction(indep_chromatic_number(nv, edges)))
    return aud.close(rec, {"objects": len(lib), "exhaustive_up_to_vertices": nv_cap})


def audit_groups(aud: Auditor, order_cap: int = 12) -> Dict[str, Any]:
    rec = aud.section("groups", "有限群：中心/共轭类/子群数 vs 独立暴力枚举；并逐元素核对元素阶")
    lib = tf.build_group_library()
    for o in lib:
        table = o["raw"]
        n = len(table)
        if n > order_cap:
            continue
        info = st.analyze_group(table)
        subs = indep_subgroups(table)
        aud.check(rec, f"{o['label']}.proper_subgroups_count",
                  info["proper_subgroups_count"], len([s for s in subs if len(s) < n]))
        aud.check(rec, f"{o['label']}.center_size", info["center_size"], indep_center_size(table))
        aud.check(rec, f"{o['label']}.class_number",
                  tf.group_invariants(table)["class_number"], Fraction(indep_class_number(table)))
        for a in range(n):
            k, cur = 1, a
            while cur != info["identity"] and k <= n + 1:
                cur = table[cur][a]
                k += 1
            aud.check(rec, f"{o['label']}.ord(elem {a})",
                      info["element_orders"][a], k if cur == info["identity"] else -1)
    return aud.close(rec, {"objects": len(lib), "order_cap": order_cap})


def audit_homology(aud: Auditor) -> Dict[str, Any]:
    rec = aud.section("homology", "有限链复形同调：库内 summary vs 独立 GF(p) 高斯消元")
    for key, builder in st.STANDARD_COMPLEXES.items():
        cx = builder()
        h = st.homology_summary(cx)
        aud.check(rec, f"{key}.betti_Q", h["betti_Q"], indep_betti_gf(cx, 104729))
        for p, block in h["per_prime"].items():
            aud.check(rec, f"{key}.betti_GF({p})", block["betti"], indep_betti_gf(cx, p))
        ec = h["euler_check"]
        aud.check(rec, f"{key}.euler_consistent", ec["consistent"], True)
    return aud.close(rec, {"complexes": len(st.STANDARD_COMPLEXES)})


# 恒等式验证器的**标准答案测试集**：左侧是式子，右侧是人工可判的期望结论
VERIFIER_TESTSET: List[Tuple[str, str]] = [
    # 真恒等式（期望 holds）
    ("sin(x)^2 + cos(x)^2 = 1", "holds"),
    ("exp(x)*exp(-x) = 1", "holds"),
    ("sin(2*x) = 2*sin(x)*cos(x)", "holds"),
    ("cos(2*x) = cos(x)^2 - sin(x)^2", "holds"),
    ("sinh(x) = (exp(x)-exp(-x))/2", "holds"),
    ("cosh(x)^2 - sinh(x)^2 = 1", "holds"),
    ("(x+1)^2 = x^2 + 2*x + 1", "holds"),
    ("exp(2*x) = exp(x)^2", "holds"),
    ("sqrt(x)*sqrt(x) = x", "holds"),
    ("tan(x) = sin(x)/cos(x)", "holds"),
    ("log(x^2) = 2*log(x)", "holds"),
    ("arcsin(x) = -i*ln(sqrt(1-x^2)+i*x)", "holds"),
    # 假恒等式（期望 fails）
    ("sin(x)^2 + cos(x)^2 = 2", "fails"),
    ("(x+1)^2 = x^2 + 1", "fails"),
    ("exp(x) = x", "fails"),
    ("log(x*y) = log(x)*log(y)", "fails"),
    ("sqrt(x+1) = sqrt(x)+1", "fails"),
    ("sin(x) = x", "fails"),
]

# 这些式子**超出**随机抽样验证的能力范围，验证器必须拒答（not_decidable）
VERIFIER_REFUSALS: List[str] = [
    "e = the sum as j ranges from 0 to infinity of 1/(j!)",
    "sin A cos B + cos A sin B = sin(A + B)",
    "grad(F) = (\\partial(F)/\\partial(x_1), ...)",
    "a*x^2 + b*x + c = 0",
]


def audit_identity_verifier(aud: Auditor) -> Dict[str, Any]:
    rec = aud.section("identity_verifier",
                      "恒等式验证器：在**能力范围内**的判准率 + 对超出能力范围的式子是否拒答")
    tp = tn = 0
    for expr, want in VERIFIER_TESTSET:
        got = verify_identity(expr)["status"]
        aud.check(rec, f"判准 {expr[:38]}", got, want)
        if got == want:
            if want == "holds":
                tp += 1
            else:
                tn += 1
    n_true = sum(1 for _, w in VERIFIER_TESTSET if w == "holds")
    n_false = len(VERIFIER_TESTSET) - n_true
    for expr in VERIFIER_REFUSALS:
        got = verify_identity(expr)["status"]
        aud.check(rec, f"拒答 {expr[:38]}", got, "not_decidable")
    return aud.close(rec, {
        "true_identities_correct": f"{tp}/{n_true}",
        "false_identities_correct": f"{tn}/{n_false}",
        "note": ("判准率只统计'在能力范围内'的式子；"
                 "对超出范围的式子，正确的行为是**拒答**而不是给出 holds/fails。"),
    })


# ===========================================================================
# 九、序列引擎审计（S9 的独立复核）
# ===========================================================================
# 这里的参照值**不来自本仓库任何代码**：它们是教科书 / OEIS 的标准前若干项。
# 目的就是给 sequences.build_sequences 一个外部锚——生成器写错，这里立刻红。
# （教训同 li(10)：参考值本身也可能写错，所以每条都写清出处口径。）
SEQUENCE_REFERENCE_TERMS: Dict[str, List[int]] = {
    # 索引口径与 build_sequences 一致：下标从 0 开始（见各序列 index_base）
    "fibonacci": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34],
    "lucas": [2, 1, 3, 4, 7, 11, 18, 29, 47, 76],
    "tribonacci": [0, 0, 1, 1, 2, 4, 7, 13, 24, 44],
    "powers_of_two": [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
    "mersenne": [0, 1, 3, 7, 15, 31, 63, 127, 255, 511],
    "squares": [0, 1, 4, 9, 16, 25, 36, 49, 64, 81],
    "triangular": [0, 1, 3, 6, 10, 15, 21, 28, 36, 45],
    "factorial": [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880],
    # 卡特兰数自 C_0=1 起
    "catalan": [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862],
    # 中心二项式系数 C(2n,n)，自 n=0 起
    "central_binomial": [1, 2, 6, 20, 70, 252, 924, 3432, 12870, 48620],
    # 错排数 !n，自 n=0 起
    "derangements": [1, 0, 1, 2, 9, 44, 265, 1854, 14833, 133496],
    "motzkin": [1, 1, 2, 4, 9, 21, 51, 127, 323, 835],
    "bell": [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147],
    # 划分数 p(n)，自 p(0)=1 起
    "partition": [1, 1, 2, 3, 5, 7, 11, 15, 22, 30],
    # A001608 Perrin：P(0)=3,P(1)=0,P(2)=2，P(n)=P(n-2)+P(n-3)
    "perrin": [3, 0, 2, 3, 2, 5, 5, 7, 10, 12],
    # A000931 Padovan（offset 0）：a(0)=1,a(1)=a(2)=0，a(n)=a(n-2)+a(n-3)
    "padovan": [1, 0, 0, 1, 0, 1, 1, 1, 2, 2],
    # A001045 Jacobsthal：J(n)=J(n-1)+2J(n-2)
    "jacobsthal": [0, 1, 1, 3, 5, 11, 21, 43, 85, 171],
    "fib_prefix_sum": [0, 1, 2, 4, 7, 12, 20, 33, 54, 88],
    # 素数计数 π(x)，下标即 x，自 x=0 起
    "primes_count": [0, 0, 1, 2, 2, 3, 3, 4, 4, 4],
    # 相邻素数间隙，自 3-2 起
    "prime_gaps": [1, 2, 2, 4, 2, 4, 2, 4, 6, 2],
    # 以下算术函数下标从 n=1 起
    "euler_phi": [1, 1, 2, 2, 4, 2, 6, 4, 6, 4],
    "sigma": [1, 3, 4, 7, 6, 12, 8, 15, 13, 18],
    "tau": [1, 2, 2, 3, 2, 4, 2, 4, 3, 4],
    "omega": [0, 1, 1, 1, 1, 2, 1, 1, 1, 2],
    "bigomega": [0, 1, 1, 2, 1, 2, 1, 3, 2, 2],
    "mobius": [1, -1, -1, 0, -1, 1, -1, 0, 0, 1],
    "radical": [1, 2, 3, 2, 5, 6, 7, 2, 3, 10],
    "phi_prefix_sum": [1, 2, 4, 6, 10, 12, 18, 22, 28, 32],
    "tau_prefix_sum": [1, 3, 5, 8, 10, 14, 16, 20, 23, 27],
    # Collatz 总步数，下标从 n=1 起
    "collatz_steps": [0, 1, 7, 2, 5, 8, 16, 3, 19, 6],
}

# 增长类型的**外部期望**。只在这里写我有把握的条目；
# 没把握的（如 partition、tau_prefix_sum）宁可不写，也不硬凑一条会误报的断言。
# 第二项是理论底数 λ（仅对纯指数增长给出，容差见 GROWTH_BASE_TOL）。
SEQUENCE_GROWTH_EXPECT: Dict[str, Tuple[str, Optional[float]]] = {
    "fibonacci": ("exponential", 1.6180339887498949),   # 黄金比
    "lucas": ("exponential", 1.6180339887498949),
    "tribonacci": ("exponential", 1.8392867552141611),  # tribonacci 常数
    "powers_of_two": ("exponential", 2.0),
    "mersenne": ("exponential", 2.0),
    "jacobsthal": ("exponential", 2.0),
    "fib_prefix_sum": ("exponential", 1.6180339887498949),
    "squares": ("polynomial_like", 2.0),
    "triangular": ("polynomial_like", 2.0),
    "phi_prefix_sum": ("polynomial_like", 2.0),         # Σφ(k) ~ 3n²/π²
    "factorial": ("super_exponential", None),
    "derangements": ("super_exponential", None),        # !n ~ n!/e
    "bell": ("super_exponential", None),
    # Perrin / Padovan 同属 a(n)=a(n-2)+a(n-3)，公比为塑性数 ρ
    "perrin": ("exponential", 1.3247179572447460),
    "padovan": ("exponential", 1.3247179572447460),
    # 以下三类是 λ^n 乘多项式因子：类型应为 exponential，但**底数**在有限窗口
    # 必然偏低（窗口偏差），故不断言底数，只把偏差记录下来。
    "catalan": ("exponential", None),                   # 理论 λ=4
    "central_binomial": ("exponential", None),          # 理论 λ=4
    "motzkin": ("exponential", None),                   # 理论 λ=3
    # 含零与负值，无法取对数：正确的行为是**拒答**而不是硬给一个类型
    "mobius": ("unknown", None),
}

# 理论底数（只用于记录窗口偏差，不用于判定）
SEQUENCE_THEORETICAL_BASE = {"catalan": 4.0, "central_binomial": 4.0, "motzkin": 3.0}

# 这些序列的真实增长是**次指数**的（如 p(n) ~ exp(π√(2n/3))/(4n)）。
# 引擎若给出 exponential 但不带 subexponential_warning，就是过度断言。
SEQUENCE_MUST_WARN_SUBEXP = {"partition"}

GROWTH_BASE_TOL = 5e-3
GROWTH_DEGREE_TOL = 0.15

# C1 递推的**主特征根**应当等于的经典常数（容差 1e-6）。
# 这条检查的意义在于：它验的不是"拟合得好不好"，而是"递推系数本身对不对"——
# 系数错一个数字，特征根就会跑到别处去。
SEQUENCE_CHAR_ROOT_EXPECT: Dict[str, float] = {
    "fibonacci": 1.6180339887498949,       # 黄金比 φ
    "lucas": 1.6180339887498949,
    "fib_prefix_sum": 1.6180339887498949,
    "tribonacci": 1.8392867552141611,      # tribonacci 常数
    "powers_of_two": 2.0,
    "mersenne": 2.0,
    "jacobsthal": 2.0,
    "perrin": 1.3247179572447460,          # 塑性数 ρ
    "padovan": 1.3247179572447460,
}
CHAR_ROOT_TOL = 1e-6


def _indep_check_linear(terms: List[int], coeffs, const) -> Optional[int]:
    """独立实现：把线性递推逐项代回，**不复用** sequences 的任何验证代码。

    返回第一个失败的下标；全部通过返回 None。全程精确有理数，无容差。
    """
    k = len(coeffs)
    cs = [Fraction(c) for c in coeffs]
    c0 = Fraction(const)
    for n in range(k, len(terms)):
        want = c0
        for i in range(k):
            want += cs[i] * terms[n - 1 - i]
        if want != Fraction(terms[n]):
            return n
    return None


def _indep_check_hyper(terms: List[int], P, Q) -> Tuple[Optional[int], int]:
    """独立实现：用**交叉相乘**验 a(n+1)·Q(n) == a(n)·P(n)，不做除法。

    避开除法有两个好处：分母为零处也有定义；全程整数比较，无浮点误差。
    返回 (第一个失败的下标, Q(n)==0 的下标个数)。
    """
    first_fail: Optional[int] = None
    n_zero_q = 0
    for n in range(len(terms) - 1):
        p = sum(int(P[i]) * n ** i for i in range(len(P)))
        q = sum(int(Q[i]) * n ** i for i in range(len(Q)))
        if q == 0:
            n_zero_q += 1
        if terms[n + 1] * q != terms[n] * p:
            if first_fail is None:
                first_fail = n
    return first_fail, n_zero_q


def audit_sequences(aud: Auditor, n_terms: int = 60) -> Dict[str, Any]:
    """序列引擎审计：教科书首项对照 + 递推独立重算 + 增长率类型对照。"""
    rec = aud.section(
        "sequences",
        "序列引擎：① 教科书/OEIS 首项对照（外部参照，不取自本仓库代码）"
        "；② 每条被报出的递推用**另一份实现**重算一遍全量项"
        "；③ 增长率类型与理论底数对照（只断言有把握的条目）")
    seqs = sq.build_sequences(n_terms)
    by_id = {s["id"]: s for s in seqs}

    # ---- ① 首项对照 ----
    n_ref_checked = 0
    for sid, want in sorted(SEQUENCE_REFERENCE_TERMS.items()):
        if sid not in by_id:
            aud.check(rec, f"参照表条目 {sid}", "序列库中不存在", "应存在")
            continue
        got = by_id[sid]["terms"][:len(want)]
        for i, w in enumerate(want):
            aud.check(rec, f"{sid}[{i}]", got[i] if i < len(got) else None, w)
            n_ref_checked += 1
    missing_ref = sorted(set(by_id) - set(SEQUENCE_REFERENCE_TERMS))
    for sid in missing_ref:
        aud.check(rec, f"{sid} 缺外部参照", False, True)

    # ---- ② 递推独立重算 ----
    n_cand = 0
    n_disagree = 0
    disagreements: List[Dict[str, Any]] = []
    for s in seqs:
        terms = s["terms"]
        for cand in sq.discover_linear(terms) + sq.discover_hypergeometric(terms):
            n_cand += 1
            if cand["channel"] == "linear":
                ff = _indep_check_linear(terms, cand["coeffs"], cand["const"])
                n_zero_q = 0
            else:
                ff, n_zero_q = _indep_check_hyper(terms, cand["P"], cand["Q"])
            mine = ff is None
            theirs = bool(cand.get("survived_extrapolation"))
            key = f"{s['id']}::{cand['channel']}::{cand['statement']}"
            aud.check(rec, f"独立重算 {key}", mine, theirs)
            if mine != theirs:
                n_disagree += 1
                disagreements.append({
                    "key": key,
                    "engine_says_survived": theirs,
                    "audit_first_failure": ff,
                    "engine_first_failure": cand.get("first_failure"),
                    "n_zero_denominator": n_zero_q,
                })
            # 若双方都说"有失败"，失败位置也必须一致
            if (not mine) and (not theirs) and ff != cand.get("first_failure"):
                disagreements.append({
                    "key": key, "kind": "首个失败位置不一致",
                    "audit_first_failure": ff,
                    "engine_first_failure": cand.get("first_failure"),
                })

    # ---- ③ 增长率对照 ----
    growth_seen: Dict[str, Any] = {}
    base_bias: Dict[str, Any] = {}
    n_warn_missing = 0
    growth_by_id: Dict[str, Any] = {}
    for s in seqs:
        g = sq.estimate_growth(s["terms"])
        gtype = g.get("type")
        growth_seen[s["id"]] = gtype
        growth_by_id[s["id"]] = g
        exp = SEQUENCE_GROWTH_EXPECT.get(s["id"])
        if exp is None:
            continue  # 没把握就不断言，只记录观测值
        want_type, want_base = exp
        aud.check(rec, f"增长类型 {s['id']}", gtype, want_type)
        if want_type == "exponential" and want_base is not None:
            lam = g.get("base_lambda")
            aud.check(rec, f"指数底 {s['id']}（容差 {GROWTH_BASE_TOL}）",
                      abs(lam - want_base) <= GROWTH_BASE_TOL, True)
        if want_type == "polynomial_like":
            deg = g.get("degree_estimate")
            aud.check(rec, f"多项式次数 {s['id']}（容差 {GROWTH_DEGREE_TOL}）",
                      abs(deg - 2.0) <= GROWTH_DEGREE_TOL, True)
        # 理论底数 vs 窗口估计：只记录，不判成败
        theo = SEQUENCE_THEORETICAL_BASE.get(s["id"])
        if theo is not None and g.get("base_lambda") is not None:
            base_bias[s["id"]] = {
                "theoretical": theo,
                "observed": g["base_lambda"],
                "relative_deficit": round((theo - g["base_lambda"]) / theo, 4),
            }
        # 次指数序列必须自带警告，否则算过度断言
        if s["id"] in SEQUENCE_MUST_WARN_SUBEXP:
            warned = bool(g.get("subexponential_warning"))
            if not warned:
                n_warn_missing += 1
            aud.check(rec, f"次指数警告 {s['id']}", warned, True)

    # ---- ④ 递推 → 特征根 → 增长率：双路径对账 + 主特征根对照经典常数 ----
    n_recon = 0
    n_recon_bad = 0
    char_roots: Dict[str, Any] = {}
    for s in seqs:
        lin = [c for c in sq.discover_linear(s["terms"])
               if c.get("survived_extrapolation")]
        if not lin:
            continue
        c = lin[0]
        rg = sq.growth_from_recurrence(c["coeffs"], c["const"])
        g = growth_by_id[s["id"]]
        n_recon += 1
        # (a) 类型必须一致
        if rg.get("type") != g.get("type"):
            n_recon_bad += 1
        aud.check(rec, f"双路径类型一致 {s['id']}", rg.get("type"), g.get("type"))
        # (b) 数值必须吻合（指数比底数，多项式比次数）
        if rg.get("type") == "exponential":
            exact = rg["base_exact_from_recurrence"]
            got = g.get("base_lambda")
            aud.check(rec, f"底数 特征根vs窗口 {s['id']}（相对 1%）",
                      abs(exact - got) / exact < 0.01 if got else False, True)
            char_roots[s["id"]] = round(exact, 10)
            want = SEQUENCE_CHAR_ROOT_EXPECT.get(s["id"])
            if want is not None:
                aud.check(rec, f"主特征根 {s['id']}（容差 {CHAR_ROOT_TOL}）",
                          abs(exact - want) <= CHAR_ROOT_TOL, True)
        elif rg.get("type") == "polynomial_like":
            aud.check(rec, f"次数 特征根vs窗口 {s['id']}（绝对 0.15）",
                      abs(rg["degree_from_recurrence"]
                          - g.get("degree_estimate", -99)) < 0.15, True)

    # ---- ⑤ 元检验：证伪机制会不会真的响 ----
    # 真实序列上"外推证伪"恒为 0，容易被误读成"没有过拟合"。
    # 实际是：不相容的序列根本报不出候选，走不到外推检验那一步。
    # 所以必须自己造必然破功的序列来验证这条通道可达。
    mt = sq.meta_test_falsification(n_terms=n_terms)
    for c in mt["cases"]:
        aud.check(rec, f"元检验·证伪定位 {c['case']}", c["located_exactly"], True)
    # 固定种子：审计结果必须可复现，否则"通过"没有意义。
    # （曾踩坑：在列表推导里每次都新建 Random(seed)，得到的是**常数序列**，
    #  常数序列当然满足 a(n)=a(n-1)，于是审计自己造出了一个假警报。）
    _rng = random.Random(20260919)
    noise = [_rng.randint(0, 50) for _ in range(n_terms)]
    n_noise = len(sq.discover_linear(noise)) + len(sq.discover_hypergeometric(noise))
    aud.check(rec, "元检验·随机噪声报 0 候选（不过度报告）", n_noise, 0)

    return aud.close(rec, {
        "n_terms": n_terms,
        "n_reference_terms_checked": n_ref_checked,
        "falsification_meta_test": mt,
        "noise_candidates": n_noise,
        "zero_falsified_note": (
            "真实序列上「外推证伪 0」的正确解读是**没有候选进入外推检验**"
            "（C1/C2 只报发现集上精确相容且解唯一的解），不是「没有过拟合」。"
            "证伪通道本身由 ⑤ 的合成序列元检验确认可达。"),
        "n_reconciled": n_recon,
        "n_reconcile_type_mismatch": n_recon_bad,
        "characteristic_roots": char_roots,
        "char_root_expect": SEQUENCE_CHAR_ROOT_EXPECT,
        "char_root_note": ("主特征根由递推系数经 Durand–Kerner 求根得到，与教科书常数"
                           "（φ、tribonacci 常数、塑性数）逐条对照。系数错一个数字，"
                           "特征根就会跑到别处，所以这条查的是**系数本身**而非拟合质量。"),
        "sequences_without_reference": missing_ref,
        "n_recurrence_candidates": n_cand,
        "n_independent_disagreements": n_disagree,
        "disagreements": disagreements,
        "growth_observed": growth_seen,
        "growth_base_bias": base_bias,
        "growth_base_bias_note": (
            "λ^n·n^α 型序列在有限窗口上拟合出的底数必然低于理论值（多项式因子被"
            "吸收进指数项）。这是**窗口偏差**，不是引擎缺陷；但读报告的人若把"
            "观测底数当结论用就会错，所以单列出来。"),
        "n_missing_subexp_warning": n_warn_missing,
        "unchecked_growth_ids": sorted(set(by_id) - set(SEQUENCE_GROWTH_EXPECT)),
        "unchecked_growth_note": (
            "这些序列的增长类型我不给出断言（真实增长属于中间型或我无把握），"
            "它们的类型由引擎给出但**未经审计确认**，见 growth_observed。"),
    })


def run_audit(n_max: int = 120) -> Dict[str, Any]:
    aud = Auditor()
    audit_arithmetic(aud, n_max=n_max)
    audit_primes(aud)
    audit_li(aud)
    audit_partitions(aud)
    audit_graphs(aud)
    audit_groups(aud)
    audit_homology(aud)
    audit_identity_verifier(aud)
    audit_sequences(aud)
    total = sum(s["checks"] for s in aud.sections)
    failed = sum(len(s["failures"]) for s in aud.sections)
    return {
        "scope": SCOPE_NOTE,
        "method": ("每个数字都用与被测代码不同的算法重算，或对照教科书已知值；"
                   "审计只报告差异，不修改被审对象。"),
        "summary": {
            "sections": len(aud.sections),
            "total_checks": total,
            "failed_checks": failed,
            "passed_checks": total - failed,
            "all_ok": failed == 0,
        },
        "sections": aud.sections,
    }


__all__ = [
    "SCOPE_NOTE", "run_audit", "Auditor",
    "audit_arithmetic", "audit_primes", "audit_li", "audit_partitions",
    "audit_graphs", "audit_groups", "audit_homology", "audit_identity_verifier",
    "audit_sequences", "SEQUENCE_REFERENCE_TERMS", "SEQUENCE_GROWTH_EXPECT",
    "SEQUENCE_CHAR_ROOT_EXPECT",
    "VERIFIER_TESTSET", "VERIFIER_REFUSALS",
    "indep_li", "indep_partitions",
]
