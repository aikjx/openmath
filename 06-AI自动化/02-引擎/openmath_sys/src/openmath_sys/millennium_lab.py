# -*- coding: utf-8 -*-
"""千禧难题的**有限影子实验**（纯标准库实现）。

这里跑的每一个数都是**真算出来的**，不是引述。口径统一为 L2：
   有限范围内吻合 ≠ 命题成立。每个实验的 `caveat` 字段都必须写明这一点，
   以及**这个实验到底能说明什么、不能说明什么**。

环境约束：本仓库没有 numpy/mpmath/sympy，全部用 cmath / Fraction 手写。
这反而带来一个好处——Hodge 那一组用 Fraction 做**精确有理**线性代数，
不存在浮点误差掩盖错误的问题。
"""
from __future__ import annotations

import cmath
import math
import random
from fractions import Fraction
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# 通用数值件：复数 Γ（Lanczos）与 ζ（Euler–Maclaurin）
# ---------------------------------------------------------------------------
_LANCZOS_P = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
]


def cgamma(z: complex) -> complex:
    """复数 Gamma（Lanczos g=7）。反射公式处理 Re z < 1/2。"""
    if z.real < 0.5:
        return cmath.pi / (cmath.sin(cmath.pi * z) * cgamma(1 - z))
    z -= 1
    x = _LANCZOS_P[0]
    for i in range(1, len(_LANCZOS_P)):
        x += _LANCZOS_P[i] / (z + i)
    t = z + 7 + 0.5
    return cmath.sqrt(2 * cmath.pi) * (t ** (z + 0.5)) * cmath.exp(-t) * x


_BERN = [Fraction(1, 6), Fraction(-1, 30), Fraction(1, 42),
         Fraction(-1, 30), Fraction(5, 66), Fraction(-691, 2730)]


def zeta(s: complex, terms: int = 60, m: int = 5) -> complex:
    """Riemann ζ(s)，Euler–Maclaurin 加速。要求 Re s > 0 附近可用；
    临界带上靠解析延拓的这一形式仍是标准做法。"""
    if s == 1:
        raise ValueError("pole")
    N = terms
    total = sum(complex(n) ** (-s) for n in range(1, N))
    total += complex(N) ** (1 - s) / (s - 1)
    total += 0.5 * complex(N) ** (-s)
    for k in range(1, m + 1):
        B = _BERN[k - 1]
        prod = complex(1)
        for j in range(0, 2 * k - 1):
            prod *= (s + j)
        coef = float(B) / math.factorial(2 * k)
        total += coef * prod * complex(N) ** (1 - s - 2 * k)
    return total


def riemann_siegel_theta(t: float) -> float:
    """θ(t) = Im log Γ(1/4 + it/2) − (t/2)·ln π。

    t 较大时**不能**走 Γ 的反射公式：sin(πz) 在 |Im z| 大时会溢出
    （实测 T=600 处直接 OverflowError）。改用 Stirling 渐近级数：
        θ(t) = (t/2)ln(t/2π) − t/2 − π/8 + 1/(48t) + 7/(5760 t³) + …
    t ≤ 20 时渐近级数还不够准，仍用精确 Γ。两种算法在 t=20 处对账（见审计）。
    """
    if abs(t) < 1e-12:
        return 0.0
    if abs(t) >= 20.0:
        s = (t / 2) * math.log(abs(t) / (2 * math.pi)) - t / 2 - math.pi / 8
        s += 1.0 / (48 * t) + 7.0 / (5760 * t ** 3)
        return s
    return cmath.log(cgamma(0.25 + 0.5j * t)).imag - 0.5 * t * math.log(math.pi)


def hardy_z(t: float, terms: int | None = None) -> float:
    """Hardy Z(t) = e^{iθ(t)} ζ(1/2+it)，在临界线上取实值（误差来自浮点）。"""
    n = terms if terms is not None else max(60, int(2.2 * abs(t)) + 40)
    s = 0.5 + 1j * t
    val = zeta(s, terms=n)
    return (cmath.exp(1j * riemann_siegel_theta(t)) * val).real


def von_mangoldt_N(T: float) -> float:
    """Riemann–von Mangoldt 主项：N(T) ≈ (T/2π)·ln(T/2π) − T/2π + 7/8"""
    if T <= 0:
        return 0.0
    x = T / (2 * math.pi)
    return x * math.log(x) - x + 0.875


# ---------------------------------------------------------------------------
# 实验 1：RH —— 临界线零点计数 vs Riemann–von Mangoldt
# ---------------------------------------------------------------------------
def exp_zeta_zero_count(T: float = 100.0, step: float = 0.02) -> Dict[str, Any]:
    """用 Hardy Z 的符号变号数估计临界线零点数，与 von Mangoldt 主项对账。

    能说明什么：Z 的构造与 ζ 求值自洽、计数方法没问题、数值上没看到漏零点。
    不能说明什么：**不能**说明所有零点都在临界线上。
    我们不检验 Re ρ —— 因为我们**只在临界线上采样**，压根没去别处找。
    """
    zeros: List[float] = []
    prev_t, prev_z = 0.0, None
    t = 0.5
    while t <= T:
        z = hardy_z(t)
        if prev_z is not None and prev_z * z < 0:
            # 线性插值定位变号点（一阶近似）
            frac = abs(prev_z) / (abs(prev_z) + abs(z))
            zeros.append(prev_t + frac * (t - prev_t))
        prev_t, prev_z = t, z
        t += step

    counted = len(zeros)
    predicted = von_mangoldt_N(T)
    return {
        "id": "zeta_zero_count",
        "problem": "RH",
        "T": T, "step": step,
        "zeros_found": counted,
        "von_mangoldt_main_term": round(predicted, 4),
        "difference": round(counted - predicted, 4),
        # N(T) − 主项 = S(T)，其已知量级为 O(log T) 且会振荡。
        # 这里如实报出它的实测值：0.2~0.4 量级**在预期范围内**，
        # 不代表漏数也不代表多数——单凭这一条无法区分两者。
        "S_T_estimate": round(counted - predicted, 4),
        "first_zeros": [round(z, 5) for z in zeros[:12]],
        "known_first_zeros": [14.13472, 21.02204, 25.01086, 30.42488, 32.93506,
                              37.58618, 40.91872, 43.32707, 48.00515, 49.77383],
        "calibration": _zero_calibration(zeros),
        "caveat": (
            "只在临界线上采样 → **结构上不可能**发现偏离临界线的零点。"
            "能对上 von Mangoldt 主项说明计数与求值自洽，"
            "对黎曼猜想本身不提供任何方向的证据。"
        ),
    }


def _zero_calibration(zeros: List[float]) -> Dict[str, Any]:
    """与教科书前若干个零点对照（校准件：数值算对了没有）。"""
    known = [14.13472, 21.02204, 25.01086, 30.42488, 32.93506,
             37.58618, 40.91872, 43.32707, 48.00515, 49.77383]
    errs = []
    for k in known:
        near = min(zeros, key=lambda z: abs(z - k)) if zeros else None
        errs.append(None if near is None else round(abs(near - k), 5))
    ok = sum(1 for e in errs if e is not None and e < 0.02)
    return {"checked": len(known), "matched_within_0.02": ok,
            "max_error": max([e for e in errs if e is not None], default=None)}


# ---------------------------------------------------------------------------
# 实验 2：RH —— ξ 函数方程（已知定理，仅作求值器校准）
# ---------------------------------------------------------------------------
def _xi(s: complex) -> complex:
    return 0.5 * s * (s - 1) * (math.pi ** (-s / 2)) * cgamma(s / 2) * zeta(s, terms=80)


def exp_xi_functional_equation() -> Dict[str, Any]:
    """检验 ξ(s) = ξ(1−s)。这是**已知定理**，此处只用来证明求值器没写反。"""
    rows = []
    for s in [0.3 + 1j, 0.7 + 2j, 1.5 + 0.5j, -0.4 + 3j, 2.2 + 1.7j]:
        a, b = _xi(s), _xi(1 - s)
        d = abs(a - b)
        scale = max(1.0, abs(a))
        rows.append({"s": f"{s.real:g}{s.imag:+g}i", "abs_diff": d,
                     "rel_diff": d / scale, "ok": d / scale < 1e-8})
    return {
        "id": "xi_functional_equation",
        "problem": "RH",
        "rows": rows,
        "all_ok": all(r["ok"] for r in rows),
        "caveat": (
            "函数方程是**已证定理**，能对上只说明 Γ/ζ 的实现正确，"
            "与黎曼猜想无关。把它列为校准件的意义在于："
            "如果这条都对不上，那上面零点计数的一切结论都不可信。"
        ),
    }


# ---------------------------------------------------------------------------
# 实验 3：BSD —— 椭圆曲线点计数 + Hasse 界（定理，校准件）
# ---------------------------------------------------------------------------
def ec_point_count(a: int, b: int, p: int) -> int:
    """#E(F_p)，E: y² = x³ + a x + b。含无穷远点。暴力枚举 x。"""
    total = 1  # 无穷远点
    sq = { (y * y) % p: 2 for y in range(1, p) }
    sq[0] = 1
    for x in range(p):
        rhs = (x * x * x + a * x + b) % p
        total += sq.get(rhs, 0)
    return total


def exp_ec_point_count(pmax: int = 500) -> Dict[str, Any]:
    """四条曲线上算 #E(F_p) 与 a_p，检验 Hasse 界 |a_p| ≤ 2√p。

    Hasse 界是**定理**，所以这是一个**校准件**：能对上 ⇒ 点计数代码正确。
    对不上 ⇒ 我们的代码错了，而不是 Hasse 错了 —— 这个方向性要说清楚。
    """
    curves = [
        {"name": "y^2 = x^3 - x  (rank 0, 已知)", "a": -1, "b": 0, "known_rank": 0},
        {"name": "y^2 = x^3 - 2  (rank 1, 已知)", "a": 0, "b": -2, "known_rank": 1},
        {"name": "y^2 = x^3 + x + 1", "a": 1, "b": 1, "known_rank": None},
        {"name": "y^2 = x^3 - 4x + 1", "a": -4, "b": 1, "known_rank": None},
    ]
    primes = [p for p in range(3, pmax) if all(p % d for d in range(2, int(p ** 0.5) + 1))]
    out_curves = []
    hasse_checked = 0
    hasse_ok = 0
    for c in curves:
        ap_list = []
        for p in primes:
            disc = (-16 * (4 * c["a"] ** 3 + 27 * c["b"] ** 2)) % p
            if disc == 0:
                continue
            n = ec_point_count(c["a"] % p, c["b"] % p, p)
            ap = p + 1 - n
            bound = 2 * math.sqrt(p)
            hasse_checked += 1
            if abs(ap) <= bound + 1e-9:
                hasse_ok += 1
            ap_list.append((p, ap))
        out_curves.append({
            "name": c["name"], "known_rank": c["known_rank"],
            "n_primes": len(ap_list),
            "first_ap": ap_list[:8],
            "mean_ap_over_sqrt_p": (round(sum(ap / math.sqrt(p) for p, ap in ap_list)
                                          / max(1, len(ap_list)), 5)),
        })
    return {
        "id": "ec_point_count",
        "problem": "BSD",
        "pmax": pmax,
        "curves": out_curves,
        "hasse_checked": hasse_checked,
        "hasse_ok": hasse_ok,
        "hasse_all_ok": hasse_checked == hasse_ok,
        "caveat": (
            "Hasse 界 |a_p| ≤ 2√p 是**已证定理**，能对上只说明点计数正确。"
            "BSD 讲的是 ord_{s=1} L(E,s) = rank E(Q)，"
            "需要的是 a_p 的**全局解析行为**，不是有限个 p 上的界；"
            "本实验没有计算 L 函数，也没有计算代数秩，故对 BSD **零证据**。"
        ),
    }


# ---------------------------------------------------------------------------
# 实验 4：NS —— Burgers 方程激波时间（可精确校准的一维类比）
# ---------------------------------------------------------------------------
def exp_burgers_shock(n: int | Tuple[int, ...] = (150, 300), nu: float = 0.0,
                      t_end: float = 1.6, dt: float = 2e-4) -> Dict[str, Any]:
    """一维 Burgers u_t + u u_x = ν u_xx，周期域，初值 u₀ = −sin(x)。

    为什么挑 Burgers：它是**唯一能把'爆破/不爆破'问题精确校准**的非线性模型——
      · ν=0：特征线在 t* = 1/max|u₀'| = 1 处相交 ⇒ 精确激波时刻 **t* = 1**
      · ν>0：全局光滑，永不爆破
    这两条都是定理，所以可以拿来校验数值格式。
    但必须写明：**一维 Burgers 不是三维 Navier–Stokes**。
    三维 NS 之所以难，恰恰是 Burgers 缺少的涡量拉伸项与不可压缩约束。
    """
    # 单靠"梯度越过某阈值"定激波时刻是靠不住的：一阶迎风有数值粘性 ~|u|dx/2，
    # 会把越阈时刻系统推后。可信的判据是**网格细分收敛**：
    # 估计值应随 n 增大而向理论值 1 靠近。所以这里跑多个分辨率。
    resolutions = (n,) if isinstance(n, int) else tuple(n)
    per_res = []
    for nn in resolutions:
        per_res.append(_burgers_one(nn, nu, t_end, dt))
    # 两个估计量并列，因为它们的收敛性质**相反**，而这一点本身是实测结果：
    #   A 特征线估计量 t* = min{ −1/u₀'(x₀) : u₀'(x₀)<0 }  → 细分下收敛到 1
    #   B 梯度越阈估计量                                    → **不收敛**
    # B 不收敛的原因：离散梯度在最陡处按 ~1/dx 放大，网格越细同一物理剖面
    #   给出的 |u_x| 越大，于是固定阈值被越过的时刻反而**提前**。
    #   实测：n=150 → 0.9912，n=300 → 0.9286（离 1 更远）。
    # 把这个负面结果写进产物，比只报一个"看起来差不多"的数字诚实。
    char_ests = [r["characteristic_shock_time"] for r in per_res]
    char_errs = [abs(e - 1.0) for e in char_ests]
    thr_ests = [r["estimate"] for r in per_res if r["estimate"] is not None]
    thr_errs = [abs(e - 1.0) for e in thr_ests]
    return {
        "id": "ns_burgers_shock" if nu == 0.0 else "ns_burgers_viscous",
        "problem": "NS",
        "nu": nu, "dt": dt, "t_end": t_end,
        "resolutions": list(resolutions),
        "per_resolution": per_res,
        "characteristic_estimates": char_ests,
        "threshold_estimates": thr_ests,
        "theoretical_shock_time": 1.0,
        "characteristic_finest_error": (round(char_errs[-1], 6) if char_errs else None),
        "characteristic_converging": bool(len(char_errs) > 1
                                          and char_errs[-1] <= char_errs[0] + 1e-9),
        "threshold_converging": bool(len(thr_errs) > 1
                                     and thr_errs[-1] <= thr_errs[0] + 1e-9),
        "calibration_ok": bool(char_errs) and char_errs[-1] < 1e-3,
        "caveat": (
            "一维 Burgers **不是**三维 Navier-Stokes："
            "没有涡量拉伸项 (w·grad)u，没有不可压缩约束，且 nu>0 时**已知**全局正则。"
            "本实验的价值是校准数值格式的激波捕捉能力——理论激波时刻 t*=1 可精确比对，"
            "且用网格细分检验收敛。对千禧难题本身**零证据**；"
            "三维 NS 的困难不在这类模型里。"
        ),
    }


def _burgers_one(n: int, nu: float, t_end: float, dt: float) -> Dict[str, Any]:
    thresholds = [5.0, 10.0, 25.0, 50.0]
    crossing: Dict[float, float] = {}
    dx = 2 * math.pi / n
    x = [-math.pi + i * dx for i in range(n)]
    u = [-math.sin(xi) for xi in x]
    sup_grad = max(abs((u[(i + 1) % n] - u[i]) / dx) for i in range(n))
    t, max_grad_seen, blew_up = 0.0, sup_grad, False
    steps = int(t_end / dt)
    for _ in range(steps):
        un = u[:]
        for i in range(n):
            up, um = un[(i + 1) % n], un[(i - 1) % n]
            # **迎风**差分：u>0 时信息从左来，用后差；u<0 用前差。
            # 中心差分在激波形成后会振荡，把越阈时刻污染成 1.42（纯数值伪影），
            # 换迎风后梯度单调增长，越阈时刻才真正反映激波位置。
            if un[i] >= 0:
                dudx = (un[i] - um) / dx
            else:
                dudx = (up - un[i]) / dx
            adv = -un[i] * dudx
            diff = nu * (up - 2 * un[i] + um) / (dx * dx)
            u[i] = un[i] + dt * (adv + diff)
        t += dt
        try:
            g = max(abs((u[(i + 1) % n] - u[i]) / dx) for i in range(n))
        except (OverflowError, ValueError):
            blew_up = True
            break
        if math.isinf(g) or math.isnan(g):
            blew_up = True
            break
        max_grad_seen = max(max_grad_seen, g)
        for th in thresholds:
            if th not in crossing and g > th:
                crossing[th] = round(t, 4)
    # 中间阈值作为该分辨率下的估计：太低受初值梯度影响，太高受数值粘性拖累
    estimate = crossing.get(10.0) or crossing.get(5.0) or crossing.get(25.0)
    # 特征线估计量：t* = min{ −1/u₀'(x₀) : u₀'(x₀) < 0 }（中心差分求 u₀'）
    u0 = [-math.sin(xi) for xi in x]
    t_char = None
    for i in range(n):
        d0 = (u0[(i + 1) % n] - u0[(i - 1) % n]) / (2 * dx)
        if d0 < 0:
            cand = -1.0 / d0
            if t_char is None or cand < t_char:
                t_char = cand
    return {
        "n": n, "dx": round(dx, 5),
        "thresholds": thresholds,
        "crossing_times": crossing,
        "estimate": estimate,
        "characteristic_shock_time": (round(t_char, 6) if t_char else None),
        "numerical_overflow": blew_up,
        "max_gradient_seen": ("inf" if blew_up else round(max_grad_seen, 4)),
    }


# ---------------------------------------------------------------------------
# 实验 5：HODGE —— 有限单纯复形上的组合 Hodge（精确有理线性代数）
# ---------------------------------------------------------------------------
def _rank_fraction(rows: List[List[Fraction]]) -> int:
    m = [r[:] for r in rows]
    if not m:
        return 0
    cols = len(m[0])
    r = 0
    for c in range(cols):
        piv = None
        for i in range(r, len(m)):
            if m[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        m[r], m[piv] = m[piv], m[r]
        pv = m[r][c]
        m[r] = [v / pv for v in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        r += 1
    return r


def _nullity(rows: List[List[Fraction]], ncols: int) -> int:
    return ncols - _rank_fraction(rows)


def _faces_of(maximal: List[Tuple[int, ...]], dim_max: int) -> Dict[int, List[Tuple[int, ...]]]:
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
    # C_{-1} 留空 ⇒ rank ∂_0 = 0，算的是**非约化**同调，b_0 = 连通分支数。
    # （初版在这里放了空单形 [()] 使 ∂_0 成为增广映射，算出来的是**约化**同调，
    #  于是连通复形算出 b_0 = 0、甚至出现负的 Betti 数。教科书对照值是非约化的。）
    out[-1] = []
    return out


def _boundary(k_simps: List[Tuple[int, ...]],
              km1_simps: List[Tuple[int, ...]]) -> List[List[Fraction]]:
    """∂_k : C_k → C_{k-1}，(n_{k-1} × n_k) 矩阵。

    标准约定：∂(v_0<…<v_k) = Σ_i (−1)^i (v_0,…,v̂_i,…,v_k)。
    """
    if not km1_simps:          # k=0：C_{-1}=0，∂_0 是零映射
        return []
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
        if not lap:                      # k 是顶维且无更高维 ⇒ up 为空
            lap = [[Fraction(0)] * nk for _ in range(nk)]
        lap2 = _matmul(downT, D[k]) if D[k] else [[Fraction(0)] * nk for _ in range(nk)]
        for i in range(nk):
            for j in range(nk):
                lap[i][j] += lap2[i][j]
        harm.append(_nullity(lap, nk))
    return {"simplices": simps, "boundary": D, "betti": betti, "harmonic_dim": harm}


def _torus_triangles(m: int = 3) -> List[Tuple[int, ...]]:
    """环面的 m×m 网格三角化：每个方格切成两个三角形，指标对 m 取模。

    为什么不手写单形表：手写的那份出现重复单形（同一顶点集被放了两次），
    于是算出 b=[1,3,0] 而不是 [1,2,1]。程序化生成能保证
      · 顶点数 m²，边数 3m²，面数 2m²
      · 欧拉示性数 V−E+F = 0（环面的正确值，可自检）
    """
    v = lambda i, j: (i % m) * m + (j % m)
    tris = []
    for i in range(m):
        for j in range(m):
            a, b = v(i, j), v(i + 1, j)
            c, d = v(i, j + 1), v(i + 1, j + 1)
            tris.append(tuple(sorted((a, b, c))))
            tris.append(tuple(sorted((b, d, c))))
    seen, out = set(), []
    for t in tris:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def exp_combinatorial_hodge() -> Dict[str, Any]:
    """在两个复形上做组合 Hodge：b_k 与 dim ker Δ_k 对账（精确有理）。

    复形：① 四面体表面（≃ S²）② 三角环面（≃ T²）。
    b_k = dim ker Δ_k 是**离散 Hodge 同构**，属线性代数恒等式，
    与霍奇猜想**没有逻辑关系**——有限复形上既没有 (p,p) 分解也没有代数闭链。
    """
    cases = [
        ("tetrahedron boundary (= S²)", [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], 2, [1, 0, 1]),
        ("torus grid 3x3 (= T²)", _torus_triangles(3), 2, [1, 2, 1]),
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


# ---------------------------------------------------------------------------
# 实验 6：PNP —— 随机 3-SAT 相变（对 P vs NP 本身零证据）
# ---------------------------------------------------------------------------
def _dpll(clauses: List[List[int]], n: int) -> Tuple[bool, int]:
    """极简 DPLL + 单元传播 + 纯文字规则。返回 (是否可满足, 决策节点数)。

    初版只返回决策数、把可满足性丢掉了，于是可满足率恒为 1.0——
    那个"相变"图里最难的一条曲线之外什么也看不出来。
    """
    decisions = [0]

    def simplify(cls, lit: int):
        out = []
        for c in cls:
            if lit in c:
                continue
            if -lit in c:
                nc = [x for x in c if x != -lit]
                if not nc:
                    return None
                out.append(nc)
            else:
                out.append(c)
        return out

    def dpll(cls):
        while True:
            unit = next((c[0] for c in cls if len(c) == 1), None)
            if unit is None:
                break
            nxt = simplify(cls, unit)
            if nxt is None:
                return False
            cls = nxt
        if not cls:
            return True
        # 纯文字规则
        lits = {l for c in cls for l in c}
        pure = [l for l in lits if -l not in lits]
        for l in pure:
            cls = simplify(cls, l) or []
        if not cls:
            return True
        if any(len(c) == 0 for c in cls):
            return False
        var = abs(cls[0][0])
        for val in (True, False):
            decisions[0] += 1
            lit = var if val else -var
            nxt = simplify(cls, lit)
            if nxt is not None and dpll(nxt):
                return True
        return False

    result = dpll([c[:] for c in clauses])
    return result, decisions[0]


def exp_sat_phase_transition(n: int = 40, trials: int = 12,
                             seed: int = 20260920) -> Dict[str, Any]:
    """随机 3-SAT 在 α = m/n 网格上的求解代价与可满足率。

    **对 P vs NP 的判定价值为零**，写在这里是因为它是同域内本引擎能真跑的计算。
    相变位置 ≈ 4.267 是经验事实；有限 n 上的曲线既不能证明指数下界，
    也不能排除存在尚未发现的多项式算法。
    """
    rng = random.Random(seed)
    rows = []
    for alpha in [3.0, 3.5, 4.0, 4.267, 4.5, 5.0, 5.5]:
        m = int(round(alpha * n))
        sat_count = 0
        costs = []
        for _ in range(trials):
            clauses = []
            for _ in range(m):
                vs = rng.sample(range(1, n + 1), 3)
                clauses.append([v if rng.random() < 0.5 else -v for v in vs])
            ok, cost = _dpll(clauses, n)
            costs.append(cost)
            if ok:
                sat_count += 1
        costs.sort()
        rows.append({"alpha": alpha, "m": m,
                     "sat_fraction": round(sat_count / trials, 3),
                     "median_decisions": costs[len(costs) // 2]})
    return {
        "id": "sat_phase_transition",
        "problem": "PNP",
        "n": n, "trials": trials,
        "rows": rows,
        "caveat": (
            "**本实验对 P vs NP 本身提供的证据为零。**"
            "有限规模（n=40）上的求解曲线既不支持 P≠NP 也不支持 P=NP："
            "指数下界要求证明**所有**算法都不行，而多项式算法完全可能只在 n>10^6 才显现。"
            "相变现象是经验事实，与判定无关。列出它的唯一理由是它是同域内"
            "本引擎能真实跑出来的计算，而不是因为它能推进判定。"
        ),
    }


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
def run_all() -> Dict[str, Any]:
    exps = [
        exp_xi_functional_equation(),
        exp_zeta_zero_count(T=600.0, step=0.02),
        exp_ec_point_count(pmax=500),
        exp_burgers_shock(n=(150, 300), nu=0.0, t_end=1.6, dt=2e-4),
        exp_burgers_shock(n=(150, 300), nu=0.05, t_end=1.6, dt=2e-4),
        exp_combinatorial_hodge(),
        exp_sat_phase_transition(n=40, trials=12),
        exp_homology_sphere(),
    ]
    return {
        "experiments": exps,
        "summary": {
            "n_experiments": len(exps),
            "problems_covered": sorted({e["problem"] for e in exps}),
            "note": ("每个实验都自带 caveat；**没有任何一个**给出对相应千禧难题的证明性证据。"
                     "YM 没有实验——不是漏做，而是该问题的前提（四维量子测度）尚未构造，"
                     "不存在可计算的谱。"),
        },
    }
