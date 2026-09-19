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


def indep_partitions_dp(n: int) -> int:
    """划分数 p(n) 的**第三种**算法：限制部分大小的 DP。

    `A[k][m]` = 只用不超过 k 的部分去分拆 m 的方法数；
    转移 `A[k][m] = A[k-1][m] + A[k][m-k]`（不用 k / 至少用一个 k）。
    答案 `A[n][n]`。与欧拉五边形数递推毫无共同 structural assumption，
    两条独立路径给出同一个数字时，写错一道递推也会被抓出来。
    """
    A = [[0] * (n + 1) for _ in range(n + 1)]
    A[0][0] = 1
    for k in range(1, n + 1):
        for m in range(0, n + 1):
            v = A[k - 1][m]
            if m >= k:
                v += A[k][m - k]
            A[k][m] = v
    return A[n][n]


def legendre_pi(x: int) -> int:
    """素数计数的**第二种**算法：Legendre 公式 π(x) = φ(x, a) + a − 1，
    其中 a = π(⌊√x⌋)，φ(x,a) = 不超过 x 且不被前 a 个素数整除的正整数个数，
    由递推 φ(x,a) = φ(x,a−1) − φ(⌊x/p_a⌋, a−1) 求得（全程整数，无浮点）。

    与筛法的共同点只有"素数"这个定义本身——筛法是标记合数，这里是容斥计剩余数。
    两者在 x=10^6 上必须给出同一个数字（本次实测：78498 = 78498）。

    注意：早期版本只递推了前 12 个素数就加 a−1，那是**错的**
    （a 必须是 π(√x) 的全部）；公式错但结果看着也像个数，所以必须拿它跟筛法对撞。
    """
    if x < 2:
        return 0
    primes = nt.sieve_primes(int(x ** 0.5) + 1)
    a = len(primes)
    memo: Dict[Tuple[int, int], int] = {}

    def phi(y: int, b: int) -> int:
        if b == 0:
            return y
        key = (y, b)
        if key in memo:
            return memo[key]
        v = phi(y, b - 1) - phi(y // primes[b - 1], b - 1)
        memo[key] = v
        return v

    return phi(x, a) + a - 1


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


def indep_subgroups_bounded(table) -> List[set]:
    """子群枚举的**第二种**暴力：只枚举"生成元不超过 ⌈log2 n⌉ 个"的子集闭包。

    完备性论证（不是启发式）：往一个真子群里加一个不属于它的元素，生成的子群
    规模**至少翻倍**（新子群包含旧子群与其陪集）。所以 |H| ≤ n 的子群必由
    ≤ ⌈log2 n⌉ 个元素生成。n=15 时只需枚举 C(15,1..4) ≈ 1940 个子集的闭包，
    而纯 2^n 穷举要 32768 个子集 × O(n²) 校验——慢一个量级以上。

    对 n ≤ 12 的群，本函数与 `indep_subgroups` 在审计里**逐群互检**：
    两条不同算法若不一致，说明至少一方的完备性论证有问题。
    """
    n = len(table)
    cap = 1
    while (1 << cap) < n:
        cap += 1

    def closure(seed: set) -> set:
        S = set(seed)
        changed = True
        while changed:
            changed = False
            for a in list(S):
                for b in list(S):
                    c = table[a][b]
                    if c not in S:
                        S.add(c)
                        changed = True
        return S

    seen: set = set()
    out: List[set] = []
    for r in range(1, cap + 1):
        for comb in itertools.combinations(range(n), r):
            S = closure(set(comb))
            key = frozenset(S)
            if key not in seen:
                seen.add(key)
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


def audit_arithmetic(aud: Auditor, n_max: int = 500) -> Dict[str, Any]:
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
    known = {10: 4, 100: 25, 1000: 168, 10000: 1229, 100000: 9592,
             # π(10^6) = 78498（教科书值，来源：素数计数表的标准列出值）
             1000000: 78498}
    for x, want in sorted(known.items()):
        aud.check(rec, f"pi({x})", len(nt.sieve_primes(x)), want)
    # 第二种算法：Legendre φ 递推 vs 筛法
    for x in (1000, 10000, 100000, 1000000):
        aud.check(rec, f"pi({x}) 筛法vsLegendre",
                  legendre_pi(x), len(nt.sieve_primes(x)))
    return aud.close(rec, {"known_values": known})


def audit_li(aud: Auditor, tol: float = 1e-9) -> Dict[str, Any]:
    rec = aud.section("logarithmic_integral", "li(x)：库内 Simpson 积分 vs Ei 幂级数（完全不同的算法）")
    for x in (2.5, 5.0, 10.0, 100.0, 1000.0, 1e4, 1e5, 1e6):
        got, want = nt.logarithmic_integral(x), indep_li(x)
        rel = abs(got - want) / max(1.0, abs(want))
        aud.check(rec, f"li({x:g}) rel_err<=1e-9", rel <= tol, True)
        rec.setdefault("details", []).append({"x": x, "li": got, "ei": want, "rel_err": rel})
    return aud.close(rec)


def audit_partitions(aud: Auditor, n_max: int = 200) -> Dict[str, Any]:
    rec = aud.section(
        "partitions",
        "划分数 p(n)：欧拉五边形数递推 vs 限制部分大小的 DP（第三种算法）；"
        "小 n 另用直接生成三路对照；并校验共轭是对合")
    # 直接生成只在小范围做：p(60) 已有近百万条分拆列表，继续往上不现实
    n_direct = min(n_max, 40)
    for n in range(0, n_direct + 1):
        aud.check(rec, f"p({n}) 直接生成", len(tf._partitions(n)),
                  Fraction(indep_partitions(n)))
    for n in range(0, n_max + 1):
        euler = indep_partitions(n)
        dp = indep_partitions_dp(n)
        aud.check(rec, f"p({n}) 欧拉vsDP", Fraction(dp), Fraction(euler))
    conj_bad = 0
    for n in range(1, 25):
        for lam in tf._partitions(n):
            if tf._conjugate(tf._conjugate(lam)) != lam:
                conj_bad += 1
    aud.check(rec, "conjugate 是对合 (n<=24)", conj_bad, 0)
    return aud.close(rec, {
        "n_max": n_max, "conjugate_failures": conj_bad,
        "n_direct_generation": n_direct + 1,
        "methods": ["欧拉五边形数递推", "限制部分大小 DP", "直接生成（仅 n<=%d）" % n_direct],
    })


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


def audit_groups(aud: Auditor, order_cap: int = 15) -> Dict[str, Any]:
    rec = aud.section("groups", "有限群：中心/共轭类/子群数 vs 独立暴力枚举；并逐元素核对元素阶")
    # extended 分支把库扩到 13–15 阶（默认的 S7 库仍是 ≤12 阶，不影响上游）
    lib = tf.build_group_library(extended=True)
    n_cross_bad = 0
    for o in lib:
        table = o["raw"]
        n = len(table)
        if n > order_cap:
            continue
        info = st.analyze_group(table, full_enum_cap=order_cap)
        subs = indep_subgroups(table)
        # 两种独立枚举互检（仅在 2^n 穷举还跑得动的规模上）
        if n <= 12:
            fast = indep_subgroups_bounded(table)
            if len(fast) != len(subs):
                n_cross_bad += 1
            aud.check(rec, f"{o['label']} 子群枚举两法一致",
                      len(fast), len(subs))
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
    # ---- 隐式乘法（2026-09-19 第五轮新增：解析器原生支持的回归护栏）----
    # 这几条同时也是**优先级约定**的护栏：一旦有人把紧贴乘法改回与 `*` 同优先级，
    # `/2i` 与 `x/2y` 两条会立刻变红。
    ("sin(x) = (exp(ix)-exp(-ix))/2i", "holds"),
    ("cos(x) = (exp(ix)+exp(-ix))/2", "holds"),
    ("x/2y = x/(2*y)", "holds"),
    ("2z = z+z", "holds"),
    ("(x+1)^2 = x^2 + 2x + 1", "holds"),
    ("-x^2 = -(x^2)", "holds"),
]

# 这些式子**超出**随机抽样验证的能力范围，验证器必须拒答（not_decidable）
VERIFIER_REFUSALS: List[str] = [
    "e = the sum as j ranges from 0 to infinity of 1/(j!)",
    "sin A cos B + cos A sin B = sin(A + B)",
    "grad(F) = (\\partial(F)/\\partial(x_1), ...)",
    "a*x^2 + b*x + c = 0",
    # 散文即使能被拆成单字母乘积也必须拒答（`the` 不应被当成 t*h*e）
    "the sum of x = x",
]


def _audit_parser_structures(aud: Auditor, rec: Dict[str, Any]) -> Dict[str, Any]:
    """解析器结构核对（2026-09-19 第五轮新增）。

    为什么单独设一组：**优先级错配不会抛异常**。把 `/2i` 当成 `(/2)*i` 时，
    程序全程正常运行，只是结论反了一个负号——真恒等式被判成假，且没人会怀疑
    求值器。这类错误只能靠成对对照抓。
    """
    from . import parser as ps

    def _val(text: str, env: Dict[str, Any], ctx: set | None = None):
        m = ps.parse_text(text, ctx)
        return None if not m.parse_ok else complex(ps.evaluate(m.ast, env))

    tight = _val("1/2i", {"i": 1j})
    paren = _val("1/(2*i)", {"i": 1j})
    loose = _val("1/2*i", {"i": 1j})
    aud.check(rec, "紧贴乘法 `1/2i` 等价于 `1/(2*i)`",
              abs(tight - paren) < 1e-12, True)
    aud.check(rec, "紧贴乘法 `1/2i` 不等价于 `(1/2)*i`",
              abs(tight - loose) > 1e-6, True)
    spaced = _val("6/2 x", {"x": 7.0})
    explicit = _val("6/2*x", {"x": 7.0})
    aud.check(rec, "隔空白乘法与显式 `*` 同优先级",
              abs(spaced - explicit) < 1e-12, True)

    # 连写必须拆开；散文**不能**被拆开（否则 the -> t*h*e 会凭空造出恒等式）
    aud.check(rec, "连写 `exp(ix)` 拆成两个变量",
              sorted(ps.parse_text("exp(ix)", {"x"}).variables), ["i", "x"])
    aud.check(rec, "散文词 `the` 不被拆成乘积",
              ps.parse_text("the").variables, ["the"])
    aud.check(rec, "散文序列整体无法解析", ps.parse_text("the sum of x").parse_ok, False)

    # 旧行为会把未消费的尾巴静默丢掉，于是 `2 ln(x+...)` 被截断成常数 2
    aud.check(rec, "未消费的尾部记号必须报错",
              ps.parse_text("pi r^2").parse_ok, False)

    # 内置函数名清单必须覆盖 _call_func 的全部分支：漏登记会让 `sin` 被当作连写
    # 拆成 s*i*n。用源码反查而不是再抄一遍清单，抄的那份永远会和实现对不上。
    import inspect
    import re as _re
    src = inspect.getsource(ps._call_func)
    handled: set = set()
    for m in _re.finditer(r'name (?:in \([^)]*\)|== "([A-Za-z_]+)")', src):
        if m.group(1):
            handled.add(m.group(1))
        else:
            handled |= set(_re.findall(r'"([A-Za-z_]+)"', m.group(0)))
    missing = sorted(x for x in handled
                     if x and x[0].isalpha() and x not in ps._BUILTIN_FUNC_NAMES)
    aud.check(rec, "_BUILTIN_FUNC_NAMES 覆盖 _call_func 全部分支", missing, [])
    unknown_extra = sorted(x for x in ps._BUILTIN_FUNC_NAMES - handled
                           if x not in ("plus", "minus", "times", "divide", "power"))
    aud.check(rec, "_BUILTIN_FUNC_NAMES 无凭空多出的名字", unknown_extra, [])

    return {
        "tight_vs_parenthesized": str(tight) + " vs " + str(paren),
        "tight_vs_loose": str(tight) + " vs " + str(loose),
        "builtin_names_handled": len(handled),
        "builtin_names_declared": len(ps._BUILTIN_FUNC_NAMES),
        "note": ("紧贴乘法（无空白）比 `*` 和 `/` 结合更紧，隔空白乘法与显式 `*` 同优先级。"
                 "这是 `1/2x` 的经典歧义，本仓库选这条约定是因为它让欧拉公式那条真恒等式"
                 "判对；持有相反约定的人应直接改这里，测试集会立刻变红。"),
    }


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

    # ---- 解析器层：隐式乘法 / 连写切分 / 尾巴未消费 / 名称清单自洽 ----
    # 查的是**求值前的结构**：优先级错配不会报错，只会让真恒等式变假。
    parser_checks = _audit_parser_structures(aud, rec)
    return aud.close(rec, {
        "true_identities_correct": f"{tp}/{n_true}",
        "false_identities_correct": f"{tn}/{n_false}",
        "note": ("判准率只统计'在能力范围内'的式子；"
                 "对超出范围的式子，正确的行为是**拒答**而不是给出 holds/fails。"),
        "parser": parser_checks,
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


def _indep_check_prec(terms: List[int], polys) -> Optional[int]:
    """独立实现：逐项代入 Σ_i p_i(n)·a(n-i) 看是否恰为 0。

    与引擎的差异：引擎在**发现集内**用矩阵零空间定系数、发现集外只做外推；
    这里对**全量项**从第一项起独立验算一遍，两边口径不同。
    """
    k = len(polys) - 1
    for n in range(k, len(terms)):
        s = 0
        for i in range(k + 1):
            # 用 Horner 求值，与引擎的幂次求和写法不同
            pv = 0
            for coef in reversed(polys[i]):
                pv = pv * n + coef
            s += pv * terms[n - i]
        if s != 0:
            return n
    return None


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
        for cand in (sq.discover_linear(terms)
                     + sq.discover_hypergeometric(terms)
                     + sq.discover_polynomial_recurrence(terms)):
            n_cand += 1
            if cand.get("skipped"):
                continue   # 引擎自己声明跳过（项太大），不是一条可复核的断言
            if cand["channel"] == "linear":
                ff = _indep_check_linear(terms, cand["coeffs"], cand["const"])
                n_zero_q = 0
            elif cand["channel"] == "hyper":
                ff, n_zero_q = _indep_check_hyper(terms, cand["P"], cand["Q"])
            else:
                ff = _indep_check_prec(terms, cand["polys"])
                n_zero_q = 0
                # C4 还要额外查一条：教科书已知形式是否**逐项**成立
                known_id = (cand.get("recognition") or {}).get("known_id")
                if known_id:
                    aud.check(rec, f"C4 已知形式逐项成立 {s['id']}::{known_id}",
                              ff is None, True)
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

    # ---- ⑥ C4 求解器交叉验证 ----
    # 引擎的 C4 已从「精确有理高斯消元」换成「模素数消元 + 有理重建 + 精确复核」。
    # 换求解器是**可以用注意力掩饰过去的**改动：结果不变看起来就没事。所以这里
    # 用**被换掉的那套**（精确 Fraction 消元）当参照，两边必须给出同一组递推。
    def _ref_rref(mat: List[List[Fraction]]) -> Tuple[int, List[int],
                                                     List[List[Fraction]]]:
        m = [[Fraction(x) for x in row] for row in mat]
        rows, cols = len(m), len(m[0])
        piv: List[int] = []
        r = 0
        for c in range(cols):
            sel = None
            for i in range(r, rows):
                if m[i][c] != 0:
                    sel = i
                    break
            if sel is None:
                continue
            m[r], m[sel] = m[sel], m[r]
            pv = m[r][c]
            m[r] = [x / pv for x in m[r]]
            for i in range(rows):
                if i != r and m[i][c] != 0:
                    f = m[i][c]
                    m[i] = [a - f * b for a, b in zip(m[i], m[r])]
            piv.append(c)
            r += 1
            if r == rows:
                break
        return r, piv, m

    def _ref_prec_nullspace(A: List[List[Fraction]]) -> List[List[Fraction]]:
        if not A:
            return []
        cols = len(A[0])
        _rank, piv, R = _ref_rref(A)
        free = [c for c in range(cols) if c not in piv]
        basis: List[List[Fraction]] = []
        for fc in free:
            v = [Fraction(0)] * cols
            v[fc] = Fraction(1)
            for i, c in enumerate(piv):
                v[c] = -R[i][fc]
            basis.append(v)
        return basis

    def _ref_prec_key(terms: List[int], k: int, deg: int,
                      v: List[Fraction]) -> Optional[Tuple[int, ...]]:
        den = 1
        for x in v:
            den = den * x.denominator // math.gcd(den, x.denominator)
        ints = [int(x * den) for x in v]
        g = 0
        for x in ints:
            g = math.gcd(g, abs(x))
        if g == 0:
            return None
        ints = [x // g for x in ints]
        first_nz = next((x for x in ints if x != 0), 0)
        if first_nz < 0:
            ints = [-x for x in ints]
        polys = [ints[i * (deg + 1):(i + 1) * (deg + 1)] for i in range(k + 1)]
        if all(x == 0 for x in polys[0]):
            return None
        # 规范化：去尾零后展平成元组，使 (k,deg) 与 (k,deg+1) 的重复报法可比
        norm: List[List[int]] = []
        for p in polys:
            t = list(p)
            while len(t) > 1 and t[-1] == 0:
                t.pop()
            norm.append(t)
        return tuple(x for p in norm for x in p)

    def _ref_prec_exact(terms: List[int], discovery_len: Optional[int] = None,
                        max_order: int = sq.P_ORDER_MAX,
                        max_deg: int = sq.P_DEG_MAX) -> set:
        """参照实现：精确有理高斯消元（C4 换掉的那套）。返回规范化的多项式键集合。"""
        n_total = len(terms)
        if discovery_len is None:
            discovery_len = sq.DISCOVERY_LEN
        if discovery_len >= n_total:
            discovery_len = max(max_order + 6, n_total - 6)
        found: set = set()
        for k in range(1, max_order + 1):
            for deg in range(0, max_deg + 1):
                n_unk = (k + 1) * (deg + 1)
                n_eq = discovery_len - k
                if n_eq < n_unk + 4:
                    continue
                A = [[Fraction(terms[n - i]) * Fraction(n) ** j
                      for i in range(k + 1) for j in range(deg + 1)]
                     for n in range(k, discovery_len)]
                basis = _ref_prec_nullspace(A)
                if len(basis) != 1:
                    continue
                key = _ref_prec_key(terms, k, deg, basis[0])
                if key is None:
                    continue
                polys = [list(key[i * (deg + 1):(i + 1) * (deg + 1)])
                         for i in range(k + 1)]
                # 参照实现也只认在全量项上精确成立的（口径向引擎对齐）
                ok = True
                for n in range(k, n_total):
                    s = 0
                    for i in range(k + 1):
                        pv = 0
                        for co in reversed(polys[i]):
                            pv = pv * n + co
                        s += pv * terms[n - i]
                    if s != 0:
                        ok = False
                        break
                if ok:
                    found.add(key)
        return found

    # ⑥-a 有理重建单测：已知有理数 → mod p → 重建回来必须完全一致
    rp = sq.mod_primes()[0]
    for _num, _den in ((3, 7), (-5, 3), (17, 19), (-1234, 4321), (1, 2)):
        _x = (_num * pow(_den, rp - 2, rp)) % rp
        aud.check(rec, f"有理重建 {_num}/{_den}",
                  sq.rational_reconstruct(_x, rp), Fraction(_num, _den))

    # ⑥-b 素数合法性：引擎用的模数必须是素数（用自己的 Miller–Rabin 之外的路子再验一遍）
    for p in sq.mod_primes():
        aud.check(rec, f"模数 {p.bit_length()} 位为素数",
                  pow(2, p - 1, p) == 1 and pow(3, p - 1, p) == 1, True)

    # ⑥-c 精确 Fraction 消元 vs 模素数消元：在同一批序列上必须给出同一组递推。
    #     只在项不太大的序列上跑参照实现（否则 Fraction 分母爆炸到不可用时）。
    CROSS_SIZE_BOUND = 10 ** 25
    n_cross = 0
    n_cross_diff = 0
    cross_details: List[Dict[str, Any]] = []
    for s in seqs:
        terms = s["terms"]
        dl = sq.DISCOVERY_LEN
        if max(abs(t) for t in terms[:dl]) > CROSS_SIZE_BOUND:
            continue
        n_cross += 1
        ref = _ref_prec_exact(terms, dl)
        got = set()
        for c in sq.discover_polynomial_recurrence(terms, discovery_len=dl):
            if not c.get("survived_extrapolation"):
                continue
            key = _ref_prec_key(terms, c["order"], c["deg"],
                                [Fraction(x) for x in
                                 sum(c["polys"], [])])
            if key is not None:
                got.add(key)
        if ref != got:
            n_cross_diff += 1
            cross_details.append({
                "id": s["id"],
                "only_in_reference": sorted(set(ref) - got)[:3],
                "only_in_engine": sorted(got - set(ref))[:3],
            })
        aud.check(rec, f"C4 双求解器一致 {s['id']}", sorted(got), sorted(ref))

    # ⑥-d 每条报出的 C4 候选必须有 ≥2 个独立素数共同重建出来
    for s in seqs:
        for c in sq.discover_polynomial_recurrence(s["terms"]):
            if c.get("survived_extrapolation"):
                aud.check(rec, f"C4 多素数一致 {s['id']} 阶{c['order']}次{c['deg']}",
                          c.get("n_primes_agreeing", 0) >= 2, True)

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
        "c4_solver_crosscheck": {
            "engine_solver": ("modular-elimination + rational-reconstruction "
                              "+ exact-integer-recheck"),
            "reference_solver": ("exact Fraction Gaussian elimination "
                                 "（即 C4 换掉的那套，保留为参照）"),
            "n_sequences_compared": n_cross,
            "n_disagreements": n_cross_diff,
            "disagreement_details": cross_details,
            "size_bound_used": CROSS_SIZE_BOUND,
            "note": ("换求解器是**可以用注意力掩饰过去**的改动：结果不变看起来就没事。"
                     "所以这里用被换掉的那套当参照，两边必须给出同一组递推。"
                     "项太大的序列不参与（Fraction 分母会爆），这部分由 ⑥-d 的"
                     "多素数一致 + ② 的全量精确复核兜底。"),
        },
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


def run_audit(n_max: int = 500, order_cap: int = 15) -> Dict[str, Any]:
    aud = Auditor()
    audit_arithmetic(aud, n_max=n_max)
    audit_primes(aud)
    audit_li(aud)
    audit_partitions(aud)
    audit_graphs(aud)
    audit_groups(aud, order_cap=order_cap)
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
