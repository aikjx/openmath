# -*- coding: utf-8 -*-
"""一次性补丁：用标准 ∂ 算子重写组合 Hodge 与同调球面两个实验。写完即删。"""
import io

P = (r"D:/a10/aikjx/code/my_lib/openmath/06-AI自动化/02-引擎/"
     r"openmath_sys/src/openmath_sys/millennium_lab.py")

NEW = '''def _faces_of(maximal: List[Tuple[int, ...]], dim_max: int) -> Dict[int, List[Tuple[int, ...]]]:
    """把极大单形展开成**全部面**（含空单形所在的 -1 维占位）。

    展开是必须的：只放极大单形会让低维链群为空，Betti 数直接算错
    （本模块初版就栽在这里，靠与教科书 Betti 数对账才发现）。
    """
    from itertools import combinations
    by_dim: Dict[int, List[Tuple[int, ...]]] = {d: [] for d in range(dim_max + 1)}
    for s in maximal:
        sup = tuple(sorted(s))
        for r in range(1, len(sup) + 1):
            for f in combinations(sup, r):
                by_dim[len(f) - 1].append(tuple(sorted(f)))
    out = {}
    for d in sorted(by_dim):
        seen, uniq = set(), []
        for f in by_dim[d]:
            if f not in seen:
                seen.add(f)
                uniq.append(f)
        out[d] = sorted(uniq)
    out[-1] = [()]          # C_{-1} ≅ Q，由空单形生成，用于 ∂_0
    return out


def _boundary(k_simps: List[Tuple[int, ...]],
              km1_simps: List[Tuple[int, ...]]) -> List[List[Fraction]]:
    """∂_k : C_k → C_{k-1}，(n_{k-1} × n_k) 矩阵。

    标准约定：∂(v_0<…<v_k) = Σ_i (−1)^i (v_0,…,v̂_i,…,v_k)。
    """
    idx = {f: i for i, f in enumerate(km1_simps)}
    m = [[Fraction(0)] * len(k_simps) for _ in km1_simps]
    for j, s in enumerate(k_simps):
        for i in range(len(s)):
            f = tuple(s[:i] + s[i + 1:])
            m[idx[f]][j] = Fraction((-1) ** i)
    return m


def _transpose(m: List[List[Fraction]]) -> List[List[Fraction]]:
    if not m:
        return []
    return [[m[r][c] for r in range(len(m))] for c in range(len(m[0]))]


def _matmul(a: List[List[Fraction]], b: List[List[Fraction]]) -> List[List[Fraction]]:
    if not a or not b:
        return []
    n, k, m = len(a), len(b), len(b[0])
    out = [[Fraction(0)] * m for _ in range(n)]
    for i in range(n):
        ai = a[i]
        for t in range(k):
            if ai[t]:
                bt = b[t]
                for j in range(m):
                    out[i][j] += ai[t] * bt[j]
    return out


def _chain_data(maximal: List[Tuple[int, ...]], dim_max: int) -> Dict[str, Any]:
    """返回各维单形、∂ 矩阵、Betti 数与调和维数（全部精确有理）。"""
    simps = _faces_of(maximal, dim_max)
    D = {k: _boundary(simps.get(k, []), simps.get(k - 1, []))
         for k in range(dim_max + 1)}
    betti, harm = [], []
    for k in range(dim_max + 1):
        nk = len(simps.get(k, []))
        if nk == 0:
            betti.append(0)
            harm.append(0)
            continue
        rk_down = _rank_fraction(D[k])                      # rank ∂_k
        rk_up = _rank_fraction(D[k + 1]) if (k + 1 <= dim_max and D.get(k + 1)) else 0
        betti.append((nk - rk_down) - rk_up)
        # Δ_k = ∂_{k+1} ∂_{k+1}^T + ∂_k^T ∂_k
        up = D.get(k + 1) or [[Fraction(0)] for _ in range(nk)]
        upT = _transpose(up)
        downT = _transpose(D[k])
        lap = _matmul(up, upT)
        lap2 = _matmul(downT, D[k])
        for i in range(nk):
            for j in range(nk):
                lap[i][j] += lap2[i][j]
        harm.append(_nullity(lap, nk))
    return {"simplices": simps, "boundary": D, "betti": betti, "harmonic_dim": harm}


def exp_combinatorial_hodge() -> Dict[str, Any]:
    """在两个复形上做组合 Hodge：b_k 与 dim ker Δ_k 对账（精确有理）。

    复形：① 四面体表面（≃ S²）② 三角环面（≃ T²）。
    b_k = dim ker Δ_k 是**离散 Hodge 同构**，属线性代数恒等式，
    与霍奇猜想**没有逻辑关系**——有限复形上既没有 (p,p) 分解也没有代数闭链。
    """
    cases = [
        ("tetrahedron boundary (= S²)", [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], 2, [1, 0, 1]),
        ("triangulated torus (= T²)", [
            (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5), (0, 5, 6), (0, 6, 1),
            (1, 2, 4), (2, 3, 5), (3, 4, 6), (4, 5, 1), (5, 2, 6), (6, 3, 1),
            (1, 4, 2), (2, 5, 3), (3, 6, 4), (4, 1, 5), (5, 2, 6), (6, 3, 1),
        ], 2, [1, 2, 1]),
    ]
    results = []
    for name, maximal, dim_max, expected in cases:
        cd = _chain_data(maximal, dim_max)
        results.append({
            "complex": name,
            "betti": cd["betti"],
            "harmonic_dim": cd["harmonic_dim"],
            "expected_betti": expected,
            "betti_matches_expected": cd["betti"] == expected,
            "hodge_identity_holds": cd["betti"] == cd["harmonic_dim"],
        })
    return {
        "id": "combinatorial_hodge",
        "problem": "HODGE",
        "results": results,
        "all_hodge_identity": all(r["hodge_identity_holds"] for r in results),
        "all_betti_as_expected": all(r["betti_matches_expected"] for r in results),
        "caveat": (
            "这是**离散类比**，不是霍奇猜想。有限单纯复形上没有 (p,p) 型分解，"
            "也没有代数闭链的概念；b_k = dim ker Δ_k 是线性代数恒等式（必成立）。"
            "能对上只说明链复形与拉普拉斯的代码正确。全部用 Fraction 做精确有理运算，"
            "故不存在'浮点刚好凑上'的可能。Betti 数与教科书值对账是硬校准件："
            "初版因忘记展开单形的面而算出 S² 的 b=(0,0,4)，就是靠这条对账抓出来的。"
        ),
    }


def exp_homology_sphere() -> Dict[str, Any]:
    """S³（4-单形边界，5 顶点）的同调：期望 b=(1,0,0,1)。

    **必要不充分**：存在同调球面（如 Poincaré 同调球面）其 H_* 与 S³ 相同
    但基本群非平凡。庞加莱猜想已由 Perelman 证明，此处**不重复证明**，
    只用它来校准同调计算代码。
    """
    from itertools import combinations
    maximal = [c for c in combinations(range(5), 4)]     # ∂Δ⁴ 的 5 个四面体
    cd = _chain_data(maximal, 3)
    return {
        "id": "homology_sphere_check",
        "problem": "POINCARE",
        "complex": "d⁴ boundary (5 vertices, S³)",
        "betti": cd["betti"],
        "harmonic_dim": cd["harmonic_dim"],
        "expected_betti": [1, 0, 0, 1],
        "matches": cd["betti"] == [1, 0, 0, 1],
        "hodge_identity_holds": cd["betti"] == cd["harmonic_dim"],
        "caveat": (
            "同调条件**只是必要不充分**：Poincaré 同调球面的 H_* 与 S³ 相同，"
            "但基本群非平凡（120 阶），因此不同胚于 S³。"
            "庞加莱猜想已由 Perelman（2002–2003，Ricci 流 + 手术）证明；"
            "本仓库不声称贡献，此实验只用于校准同调计算代码。"
        ),
    }


'''

s = io.open(P, encoding="utf-8").read()
start = s.index("def exp_combinatorial_hodge")
end = s.index("# ---------------------------------------------------------------------------\n# 实验 6")
s = s[:start] + NEW + s[end:]
io.open(P, "w", encoding="utf-8").write(s)
print("patched; new length", len(s))
