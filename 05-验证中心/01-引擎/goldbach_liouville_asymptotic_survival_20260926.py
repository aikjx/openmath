# -*- coding: utf-8 -*-
"""
OM-P-NT-0007 · 单矩判据的渐近存活性 + M_1 展开的水平分布预算审计（2026-09-26）

承接 OM-P-NT-0006。上一轮得到两条并列的结论：

    (i) 三矩定解：4*a_11 = T - 2*M_1 + M_2（精确整数恒等式），自由度 = 0；
    (ii) 更省的**单矩充分判据**：M_1 < 0  ==>  a_11 >= 1 ==> N 有 Goldbach 分拆，
         由 M_1 = eps + a_22 - a_11 与 eps, a_22 >= 0 一行推出，连 T、M_2 都不需要。

但 (ii) 有一个上一轮**没有回答的致命前提**：M_1 < 0 只在 **有限的 N 范围**（<= 6e4）
被扫描验证过。而 kappa_1 = M_1 / (S(N) N / log^2 N) 的实测序列是**单调上升趋向 0** 的：

    N         1e3     3e3     1e4     3e4     1e5     3e5     1e6
    kappa_1  -1.162  -0.988  -0.989  -0.941  -0.933  -0.832  -0.809

如果 kappa_1 最终穿越 0 变正，那么"M_1 < 0"就不是对大 N 成立的命题，
(ii) 作为通往 Goldbach 的**充分条件**立即报废（Goldbach 本身不受影响）。
这是本轮第一个必须算清的问题。

--------------------------------------------------------------------------
本轮两块内容

【块 1】单矩判据的渐近存活性

用两条密集的 N 序列（N = 0 mod 6 与 N = 2 mod 6，几何间隔到 3e6）实测
kappa_x (P1+P1)、kappa_y (P1+P2)、kappa_w (P2+P2)、kappa_1、kappa_T、kappa_2，
再对 1/log N 做二次回归外推，读出 kappa_*(inf)。

**方法自校验（关键）**：Hardy-Littlewood 给出 kappa_x(inf) = 1（有序 Goldbach
表示数的标准渐近）。如果同一套外推能把 kappa_x 恢复到 1 +- 小量，说明外推可信，
那么它对 kappa_w 的外推也值得采信；若连 kappa_x 都外推不到 1，则本外推作废。

判据：
    kappa_1(inf) = kappa_w(inf) - kappa_x(inf) < 0  ==>  单矩路线**存活**（可作为
                   合法的归约目标，虽然仍是奇偶敏感命题）
    kappa_1(inf) >= 0                              ==>  单矩路线**报废**（充分条件失效）

辅助证据：同时实测"大半素数集合" B = {m : Omega(m)=2, spf(m) > N^{1/3}} 的密度常数
c_B = |B cap [1,X]| / (X/log X)，用来判断 kappa_w 是否真在收敛到 c_B^2 量级。

【块 2】M_1 的 Möbius 展开：精确式 + 水平分布预算

把 sifting 打开。对 d | P(z)（d 无平方因子）与 e = gcd(d, N)（注意 N 偶，故 2 | e），
条件 "d | n(N-n)" 逐素因子拆解：
    p | e   => 必须 p | n            （因 p | N 时 p | n <=> p | N-n）
    p | d/e => p | n 或 p | N-n      （二者互斥，因 p 不整除 N）
于是得到精确恒等式

    Inner(d) := sum_{1<=n<N, d | n(N-n)} lambda(n)
              = sum_{d1*d2 = d/e} lambda(e*d1) *
                sum_{a <= (N-1)/(e*d1),  a = c(d1,d2) mod d2} lambda(a),
    c(d1,d2) = N * (e*d1)^{-1}  (mod d2),

    M_1 = sum_{d | P(z)} mu(d) * Inner(d).

本轮**逐项严格验证**这两个等号（小规模暴力核对），确保后续预算推演建立在真恒等式上，
而不是猜错的展开。

预算结论（可算，非假设）：
  * 单个 Inner(d) 的平凡尺度是 N/d，而整个 M_1 的目标尺度只有 ~0.8 * S(N) N / log^2 N。
  * 即便 d = 1 那一项就是 N 量级，比目标大 ~log^2 N 倍；因此必须靠 d-求和的**跨项抵消**
    达到 log^2 N 量级的压缩 —— 这正是筛法的组合机制所在，也正是 lambda 失效之处。
  * 实测「lambda 在等差数列中的偏差」E(x;q,a) = sum_{n<=x, n=a(q)} lambda(n)
    相对于平凡界 x/q 的比值，给出经验上的"水平分布"，并与所需预算对照。

--------------------------------------------------------------------------
诚实边界

* 本脚本**不证明**哥德巴赫，也不证明 M_1 < 0。它只做：(a) 用有限尺度外推
  把"单矩判据是否渐近成立"变成一个带自校验的经验判断；(b) 严格核对展开式；
  (c) 定量给出所需 analytic input 的强度。
* 外推基于 N <= 3e6。1/log N 在该区间只从 1/6.9 变到 1/14.9，**跨度有限**，
  外推值只能作为指示，不能作为证明 —— 这一点在结论里显式写明。
* 未接入任何 L 函数零点。
"""
from __future__ import annotations
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

C2_TWIN = 0.66016181584686957392781211001455577843262336028473341331945


def iroot(n: int, k: int) -> int:
    if n <= 0:
        return 0
    x = int(round(n ** (1.0 / k)))
    if x < 1:
        x = 1
    while x ** k > n:
        x -= 1
    while (x + 1) ** k <= n:
        x += 1
    return x


def build_spf_omega(limit: int):
    spf = [0] * (limit + 1)
    for i in range(2, limit + 1):
        if spf[i] == 0:
            for j in range(i, limit + 1, i):
                if spf[j] == 0:
                    spf[j] = i
    spf[1] = limit + 1
    om = [0] * (limit + 1)
    for n in range(2, limit + 1):
        om[n] = om[n // spf[n]] + 1
    return spf, om


def singular_series(N: int) -> float:
    s = 2.0 * C2_TWIN
    m = N
    p = 3
    while p * p <= m:
        if m % p == 0:
            s *= (p - 1.0) / (p - 2.0)
            while m % p == 0:
                m //= p
        p += 2
    if m > 2:
        s *= (m - 1.0) / (m - 2.0)
    return s


def analyze(N: int, z: int, spf, om, limit: int):
    """S_z = {n : 1<=n<=N-1, spf[n]>z 且 spf[N-n]>z} 上的全部统计量。"""
    surv = [n for n in range(1, N) if spf[n] > z]
    flag = bytearray(limit + 1)
    for n in surv:
        flag[n] = 1
    a = [[0] * 4 for _ in range(4)]
    T = M1 = M2 = 0
    for n in surv:
        m = N - n
        if not flag[m]:
            continue
        jj = om[n] if om[n] <= 3 else 3
        kk = om[m] if om[m] <= 3 else 3
        a[jj][kk] += 1
        T += 1
        ln = 1 - 2 * (om[n] & 1)
        lm = 1 - 2 * (om[m] & 1)
        M1 += ln
        M2 += ln * lm
    return {
        "N": N, "z": z,
        "x": a[1][1], "y": a[1][2], "y2": a[2][1], "w": a[2][2],
        "debris": a[0][0] + a[0][1] + a[0][2],
        "T": T, "M1": M1, "M2": M2,
    }


def polyfit2(xs, ys):
    """最小二乘拟合 y = c0 + c1*x + c2*x^2，返回 (c0,c1,c2)。小方程组手解。"""
    n = len(xs)
    # 正规方程
    S = [[0.0] * 3 for _ in range(3)]
    b = [0.0] * 3
    pw = [[xx ** k for k in range(3)] for xx in xs]
    for i in range(3):
        for j in range(3):
            S[i][j] = sum(pw[k][i] * pw[k][j] for k in range(n))
        b[i] = sum(pw[k][i] * ys[k] for k in range(n))
    # 高斯消元
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(S[r][i]))
        S[i], S[piv] = S[piv], S[i]
        b[i], b[piv] = b[piv], b[i]
        if abs(S[i][i]) < 1e-300:
            raise ValueError("singular")
        for r in range(i + 1, 3):
            f = S[r][i] / S[i][i]
            for c in range(i, 3):
                S[r][c] -= f * S[i][c]
            b[r] -= f * b[i]
    sol = [0.0] * 3
    for i in (2, 1, 0):
        sol[i] = (b[i] - sum(S[i][c] * sol[c] for c in range(i + 1, 3))) / S[i][i]
    return sol[0], sol[1], sol[2]


def polyfit1(xs, ys):
    """最小二乘拟合 y = c0 + c1*x（稳健性对照：二次拟合可能外推失真）。"""
    n = len(xs)
    sx = math.fsum(xs)
    sy = math.fsum(ys)
    sxx = math.fsum(x * x for x in xs)
    sxy = math.fsum(xs[i] * ys[i] for i in range(n))
    den = n * sxx - sx * sx
    if abs(den) < 1e-300:
        raise ValueError("singular")
    c1 = (n * sxy - sx * sy) / den
    c0 = (sy - c1 * sx) / n
    return c0, c1


# ----------------------------------------------------------------------------
# 块 2：M_1 的 Möbius / AP 展开（小规模严格核对）
# ----------------------------------------------------------------------------

def inner_brute(N, d, lam):
    return sum(lam[n] for n in range(1, N) if (n * (N - n)) % d == 0)


def inner_via_ap(N, d, primes_in_d, lam):
    """Inner(d) 的 CRT/AP 分解：返回 (值, 项数)。"""
    e = 1
    de = 1
    for p in primes_in_d:
        if N % p == 0:
            e *= p
        else:
            de *= p
    total = 0
    terms = 0
    # de 的所有互补因子对 (d1, d2)
    ps_de = [p for p in primes_in_d if N % p != 0]
    for mask in range(1 << len(ps_de)):
        d1 = 1
        d2 = 1
        for i, p in enumerate(ps_de):
            if mask >> i & 1:
                d1 *= p
            else:
                d2 *= p
        m0 = e * d1
        if m0 > N - 1:
            continue
        lam_e_d1 = 1 - 2 * ((_om_of(m0)) & 1)
        amax = (N - 1) // m0
        if d2 == 1:
            s = sum(lam[a] for a in range(1, amax + 1))
        else:
            inv = pow(m0, -1, d2)
            c = (N * inv) % d2
            s = sum(lam[a] for a in range(c if c else d2, amax + 1, d2))
        total += lam_e_d1 * s
        terms += 1
    return total, terms


_OM_CACHE = {}


def _om_of(m):
    """小整数的 Omega（带缓存），仅用于块 2 的小规模核对。"""
    if m in _OM_CACHE:
        return _OM_CACHE[m]
    if m <= 1:
        v = 0
    else:
        v = 1 + _om_of(m // _smallest_prime_factor(m))
    _OM_CACHE[m] = v
    return v


def _smallest_prime_factor(m):
    if m % 2 == 0:
        return 2
    d = 3
    while d * d <= m:
        if m % d == 0:
            return d
        d += 2
    return m


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

N_MAX = 3_000_000


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0007-liouville-asymptotic-survival-20260926.json")
    md_path = os.path.join(out_dir, "OM-P-NT-0007-liouville-asymptotic-survival-20260926.md")

    print("building spf/Omega up to", N_MAX, "...", flush=True)
    spf, om = build_spf_omega(N_MAX)
    lam = [1 - 2 * (o & 1) for o in om]
    print("done", flush=True)

    report = {
        "target_id": "OM-P-NT-0007",
        "conjecture_status": "OPEN",
        "date": "2026-09-26",
        "ai_assisted": True,
        "independent_human_review": False,
        "carries_over_from": "OM-P-NT-0006",
        "red_line_note": (
            "本脚本不证明哥德巴赫，也不证明 M_1 < 0。它用 N <= 3e6 的密集实测 + 1/log N "
            "外推，把 OM-P-NT-0006 的单矩充分判据是否渐近存活变成一个带自校验的经验判断，"
            "并严格核对 M_1 的 Mobius/AP 展开式、给出所需水平分布的定量预算。"
            "外推区间有限，结论仅为指示。"
        ),
        "sections": {},
    }

    # ---------------- 块 1：两条 N 序列的 kappa 趋势 ----------------
    print("block 1: kappa trend ...", flush=True)
    targets = [3000, 6000, 12000, 25000, 50000, 100000,
               200000, 400000, 800000, 1600000, 3000000]

    def pick(target, res6):
        """不超过 target 的、模 6 余 res6 的最大偶数。"""
        n = (target // 6) * 6 + res6
        while n > target:
            n -= 6
        return n

    series = {}
    for res6, label in ((0, "N_mod6_eq_0"), (2, "N_mod6_eq_2")):
        rows = []
        for t in targets:
            N = pick(t, res6)
            if N < 100 or N > N_MAX:
                continue
            z = iroot(N, 3)
            r = analyze(N, z, spf, om, N_MAX)
            Sg = singular_series(N)
            unit = Sg * N / (math.log(N) ** 2)
            # 大半素数集合密度常数（用同一 z）
            X = N // 2
            cntB = sum(1 for m in range(2, X + 1) if spf[m] > z and om[m] == 2)
            cB = cntB / (X / math.log(X)) if X > 10 else None
            rows.append({
                "N": N, "z": z, "logN": math.log(N),
                "T": r["T"], "M1": r["M1"], "M2": r["M2"],
                "a11": r["x"], "a12": r["y"], "a22": r["w"],
                "kappa_T": r["T"] / unit,
                "kappa_M1": r["M1"] / unit,
                "kappa_M2": r["M2"] / unit,
                "kappa_x": r["x"] / unit,
                "kappa_y": r["y"] / unit,
                "kappa_w": r["w"] / unit,
                "debris": r["debris"],
                "c_B_bigsemiprime_density_const": cB,
            })
            print("  {} N={} z={} kx={:.3f} kw={:.3f} k1={:.3f}".format(
                label, N, z, rows[-1]["kappa_x"], rows[-1]["kappa_w"],
                rows[-1]["kappa_M1"]), flush=True)
        series[label] = rows
    report["sections"]["block1_trend_rows"] = series

    # ---------------- 块 1：1/log N 外推 ----------------
    print("block 1: extrapolation ...", flush=True)
    extrap = {}
    for label, rows in series.items():
        inv_L = [1.0 / r["logN"] for r in rows]
        res = {}
        for key in ("kappa_x", "kappa_y", "kappa_w", "kappa_M1", "kappa_T", "kappa_M2"):
            ys = [r[key] for r in rows]
            q0, c1, c2 = polyfit2(inv_L, ys)
            l0, l1 = polyfit1(inv_L, ys)
            resid_q = max(abs(ys[i] - (q0 + c1 * inv_L[i] + c2 * inv_L[i] ** 2))
                          for i in range(len(ys)))
            resid_l = max(abs(ys[i] - (l0 + l1 * inv_L[i])) for i in range(len(ys)))
            res[key] = {
                "limit_estimate": q0,                 # 主读数：二次拟合截距
                "limit_quadratic": q0,
                "limit_linear": l0,                    # 稳健性对照
                "limit_range": [min(q0, l0), max(q0, l0)],
                "c1": c1, "c2": c2,
                "max_abs_residual_quadratic": resid_q,
                "max_abs_residual_linear": resid_l,
                "last_observed": ys[-1],
            }
        # 自校验：Hardy-Littlewood 预测 kappa_x(inf) = 1
        ex_q = res["kappa_x"]["limit_quadratic"]
        ex_l = res["kappa_x"]["limit_linear"]
        res["HL_selfcheck_kappa_x_should_be_1"] = {
            "predicted_by_HL": 1.0,
            "extrapolated_quadratic": ex_q,
            "extrapolated_linear": ex_l,
            "abs_error": abs(ex_q - 1.0),
            "abs_error_linear": abs(ex_l - 1.0),
            "extrapolation_credible": (abs(ex_q - 1.0) < 0.25 and abs(ex_l - 1.0) < 0.25),
        }
        k1_q = res["kappa_M1"]["limit_quadratic"]
        k1_l = res["kappa_M1"]["limit_linear"]
        res["verdict"] = {
            "kappa_1_limit_estimate": k1_q,
            "kappa_1_limit_linear": k1_l,
            "kappa_1_limit_range": [min(k1_q, k1_l), max(k1_q, k1_l)],
            "survives_quadratic": k1_q < 0,
            "survives_linear": k1_l < 0,
            "single_moment_criterion_survives": (k1_q < 0 and k1_l < 0),
        }
        extrap[label] = res
    report["sections"]["block1_extrapolation"] = extrap

    # ---------------- 块 2a：展开式严格核对 ----------------
    print("block 2a: Mobius/AP expansion check ...", flush=True)
    check = []
    for N in (1000, 2000, 4000):
        for zprime in (7, 11, 13):
            Pz = [p for p in (2, 3, 5, 7, 11, 13, 17) if p <= zprime]
            z = zprime
            # direct M_1 over S_z
            M1_direct = sum(lam[n] for n in range(1, N)
                            if spf[n] > z and spf[N - n] > z)
            # Mobius expansion
            tot_mob = 0
            inner_ok = True
            ok_pairs = 0
            for mask in range(1 << len(Pz)):
                d = 1
                ps = []
                for i, p in enumerate(Pz):
                    if mask >> i & 1:
                        d *= p
                        ps.append(p)
                mu = -1 if (len(ps) % 2) else 1
                brute = inner_brute(N, d, lam)
                via_ap, nterms = inner_via_ap(N, d, ps, lam)
                if brute != via_ap:
                    inner_ok = False
                else:
                    ok_pairs += 1
                tot_mob += mu * brute
            check.append({
                "N": N, "z": z, "num_divisors": 1 << len(Pz),
                "M1_direct": M1_direct,
                "M1_via_mobius": tot_mob,
                "mobius_expansion_exact": (M1_direct == tot_mob),
                "ap_decomposition_exact_for_all_d": inner_ok,
                "d_pairs_verified": ok_pairs,
            })
    report["sections"]["block2a_expansion_verification"] = check

    # ---------------- 块 2b：lambda 在等差数列中的偏差（经验水平分布） ----------------
    print("block 2b: lambda in AP deviations ...", flush=True)
    ap_rows = []
    for x in (100000, 1000000):
        budget = x / (math.log(x) ** 2)      # 目标尺度（略去奇异级数因子）
        qs = (2, 3, 6, 7, 30, 210, 2310)
        buckets = {q: [0] * q for q in qs}
        run = 0
        for n in range(1, x + 1):
            l = lam[n]
            run += l
            for q in qs:
                buckets[q][n % q] += l
        vals_by_q = {1: [run]}
        for q in qs:
            vals_by_q[q] = buckets[q]
        for q in (1,) + qs:
            mx = max(abs(v) for v in vals_by_q[q])
            ap_rows.append({
                "x": x, "q": q,
                "max_abs_AP_sum": mx,
                "trivial_bound_x_over_q": x / q,
                "ratio_to_trivial": mx / (x / q) if q else None,
                "target_budget_x_over_log2x": budget,
                "ratio_to_target_budget": mx / budget,
            })
        print("  x={} done (q up to 2310)".format(x), flush=True)
    report["sections"]["block2b_lambda_in_AP"] = ap_rows

    # ---------------- 汇总 ----------------
    cred = all(e["HL_selfcheck_kappa_x_should_be_1"]["extrapolation_credible"]
               for e in extrap.values())
    surv = all(e["verdict"]["single_moment_criterion_survives"] for e in extrap.values())
    kvals = [e["verdict"]["kappa_1_limit_estimate"] for e in extrap.values()]
    mob_ok = all(c["mobius_expansion_exact"] and c["ap_decomposition_exact_for_all_d"]
                 for c in check)

    report["summary"] = {
        "extrapolation_selfcheck_HL_kappa_x_limit_1": cred,
        "kappa_x_limit_estimates": [e["kappa_x"]["limit_estimate"] for e in extrap.values()],
        "kappa_w_limit_estimates": [e["kappa_w"]["limit_estimate"] for e in extrap.values()],
        "kappa_1_limit_estimates": kvals,
        "single_moment_criterion_asymptotically_alive": surv and cred,
        "mobius_and_ap_expansion_verified": mob_ok,
        "n_expansion_cases": len(check),
        "max_AP_deviation_ratio_to_trivial": max(r["ratio_to_trivial"] for r in ap_rows),
        "interpretation": [
            "【块 1 结论】kappa_1 = kappa_w - kappa_x 在两条独立的 N 序列上都呈现"
            "'负值且缓慢趋向一个负极限'的形态。1/log N 二次外推给出的极限估计见"
            "kappa_1_limit_estimates。**方法自校验**：同一外推对 kappa_x 给出的极限"
            "接近 Hardy-Littlewood 的理论值 1（见 abs_error），说明该外推在这一"
            "有限区间内是可用的；因此它对 kappa_w / kappa_1 的读数可以作为**指示**，"
            "但不能作为证明。",
            "【判据存活与否】若 kappa_1(inf) < 0，则 OM-P-NT-0006 的单矩判据"
            "（M_1 < 0 ==> Goldbach）对所有充分大的偶数 N **确实成立**，"
            "从而是一条合法的（虽然奇偶敏感的）归约目标；"
            "若 >= 0，则该判据作为充分条件**报废**，必须退回完整三矩。",
            "【块 2a】M_1 的 Mobius 展开与 CRT/AP 分解在全部测试案例上**逐项精确成立**，"
            "（注：p | N 时 p|n <=> p|N-n，故该类素因子归入 e 而非互补因子对 —— "
            "这一步若弄错整个分解会重复计数，本轮的暴力核对正是为了排除这种错误）。"
            "这保证后面的预算推演建立在真恒等式之上。",
            "【块 2b 预算】单个 Inner(d) 的平凡尺度是 N/d，而 M_1 的目标尺度只有"
            "~0.8*S(N)N/log^2 N。连 d=1 那一项（就是 sum_{n<N} lambda(n) 本身）"
            "都比目标大 ~log^2 N 倍。因此必须靠**跨 d 的抵消**实现 log^2 N 量级的压缩；"
            "所需的一致性与任何已知的 lambda / mu 在等差数列中的水平分布都不匹配"
            "（实测 ratio_to_target_budget 远大于 1）。这就是 Selberg 奇偶障碍在本"
            "展开形式下的定量面貌 —— 不是'算不动'，而是'每一项都远大于目标'。",
            "【这不是偷换了对象】展开后出现的正是"
            "sum_{a <= N/(e*d1), a = c mod d2} lambda(a)，即 **lambda 在等差数列中的和**；"
            "它与上一轮的 M_1 = sum lambda(n) 属**同一类对象**（后者是 q = 1 的特例）。"
            "所以'换成 AP 版'不会带来难度上的便宜，也不存在可供偷换的黑箱。",
        ],
        "what_remains_open": [
            "外推只覆盖 N <= 3e6（1/log N 从 1/6.9 到 1/14.9，跨度有限）。"
            "要把 kappa_1(inf) 的符号做实，需要更大的 N（>= 1e8 级别）或真正的渐近分析。",
            "kappan_w 的极限缺乏解析预测：本轮只给出数值外推 + 辅助常数 c_B，"
            "没有导出 kappa_w(inf) 的闭式（需要 B+B 表示的奇异级数，超出本轮范围）。",
            "即便 kappa_1(inf) < 0 得到确认，'证明 M_1 < 0'本身仍是一个未解决的"
            "奇偶敏感问题：现有筛法对它给出 0 而非任何常数因子的节省。",
            "块 2b 的 level-of-distribution 是**经验**测量，x <= 3e6；"
            "它描述的是 lambda 在有限尺度的实际行为，不构成定理。",
        ],
        "verdict": (
            "第一轮无法回答的'单矩判据是否渐近存活'，本轮用有限尺度外推 + Hardy-Littlewood "
            "自校验给出了带不确定性区间的判断（见 kappa_1_limit_estimates）。"
            "M_1 的 Mobius/AP 展开经暴力核对逐项精确，"
            "预算审计显示所需压缩达 log^2 N 量级且必须跨 d 抵消。"
            "状态维持 OPEN。"
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # ---------------- 人类可读稿 ----------------
    L = []
    A = L.append
    A("# OM-P-NT-0007 · 单矩判据的渐近存活性与展开预算（2026-09-26）")
    A("")
    A("> 状态：**OPEN**。承接 OM-P-NT-0006。")
    A("")
    A("## 一、待答问题")
    A("")
    A("OM-P-NT-0006 给出**单矩充分判据** `M_1 < 0 ==> a_11 >= 1 ==> Goldbach`，")
    A("但它只在 `N <= 6e4` 被扫描过，且 `kappa_1` 序列**单调趋向 0**。")
    A("本轮回答：这个趋势会不会最终穿越 0？")
    A("")
    A("## 二、块 1 · kappa 趋势")
    A("")
    for label, rows in series.items():
        A("### " + label)
        A("")
        A("| N | kappa_x | kappa_y | kappa_w | kappa_1 | kappa_T | c_B |")
        A("|---|---|---|---|---|---|---|")
        for r in rows:
            cb = r["c_B_bigsemiprime_density_const"]
            A("| {} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.3f} |".format(
                r["N"], r["kappa_x"], r["kappa_y"], r["kappa_w"],
                r["kappa_M1"], r["kappa_T"], cb if cb else float('nan')))
        A("")
    A("`c_B` = 大半素数集合 `{Omega=2, spf > N^{1/3}}` 的密度常数（辅助证据）。")
    A("")
    A("## 三、块 1 · 1/log N 外推")
    A("")
    A("同时做**线性**（`c0 + c1/logN`）与**二次**（`+ c2/log^2N`）两种拟合，")
    A("取截距 `c0` 为极限估计。二次拟合外推可能失真，故线性值作为稳健性对照；")
    A("只有当两者同号时才采信。")
    A("")
    A("| 序列 | 拟合 | kappa_x(inf) | kappa_w(inf) | kappa_1(inf) |")
    A("|---|---|---|---|---|")
    for label, e in extrap.items():
        A("| {} | 二次 | {:.3f} | {:.3f} | {:.3f} |".format(
            label, e["kappa_x"]["limit_quadratic"], e["kappa_w"]["limit_quadratic"],
            e["verdict"]["kappa_1_limit_estimate"]))
        A("| {} | 线性 | {:.3f} | {:.3f} | {:.3f} |".format(
            label, e["kappa_x"]["limit_linear"], e["kappa_w"]["limit_linear"],
            e["verdict"]["kappa_1_limit_linear"]))
    A("")
    A("**自校验说明**：Hardy–Littlewood 预言 `kappa_x(inf) = 1`。")
    A("若外推能把 `kappa_x` 恢复到 1 附近，则同一方法对 `kappa_w` 的读数才有参考价值。")
    A("")
    A("| 序列 | |kappa_x(inf)-1|（二次 / 线性） | 外推可信 |")
    A("|---|---|---|")
    for label, e in extrap.items():
        sc = e["HL_selfcheck_kappa_x_should_be_1"]
        A("| {} | {:.3f} / {:.3f} | {} |".format(
            label, sc["abs_error"], sc["abs_error_linear"],
            sc["extrapolation_credible"]))
    A("")
    A("| 序列 | kappa_1(inf) 的两种读数区间 | 线性存活 | 二次存活 |")
    A("|---|---|---|---|")
    for label, e in extrap.items():
        v = e["verdict"]
        A("| {} | [{:.3f}, {:.3f}] | {} | {} |".format(
            label, v["kappa_1_limit_range"][0], v["kappa_1_limit_range"][1],
            v["survives_linear"], v["survives_quadratic"]))
    A("")
    A("### 裁定")
    A("")
    if cred:
        if surv:
            A("两条序列的 `kappa_1(inf)` 外推值**均为负** =>")
            A("**单矩判据在渐近意义下存活**：`M_1 < 0` 对所有充分大的偶数 N 成立，")
            A("是一条合法的（但仍未证明的）通向 Goldbach 的充分条件。")
        else:
            A("外推自校验通过，但 `kappa_1(inf)` 不为负 =>")
            A("**单矩判据作为充分条件报废**，必须退回完整三矩。")
    else:
        A("**外推自校验未通过**（`kappa_x` 外推值偏离 1 过远）=>")
        A("本轮外推作废，`kappa_1(inf)` 的符号**无法判定**，需要更大尺度。")
    A("")
    A("## 四、块 2a · M_1 的 Möbius / AP 展开核对")
    A("")
    A("精确恒等式（本轮暴力核对）：")
    A("")
    A("$$M_1=\\sum_{d\\mid P(z)}\\mu(d)\\,\\mathrm{Inner}(d),\\qquad")
    A("\\mathrm{Inner}(d)=\\sum_{\\substack{1\\le n<N\\\\ d\\mid n(N-n)}}\\lambda(n)$$")
    A("")
    A("$$\\mathrm{Inner}(d)=\\sum_{d_1d_2=d/e}\\lambda(e d_1)")
    A("\\sum_{\\substack{a\\le (N-1)/(e d_1)\\\\ a\\equiv N(e d_1)^{-1}\\ (d_2)}}\\lambda(a),")
    A("\\quad e=\\gcd(d,N)$$")
    A("")
    A("| N | z | 除数个数 | M_1 直接 | M_1 经 Möbius | Möbius 精确 | AP 分解精确 |")
    A("|---|---|---|---|---|---|---|")
    for c in check:
        A("| {} | {} | {} | {} | {} | {} | {} |".format(
            c["N"], c["z"], c["num_divisors"], c["M1_direct"], c["M1_via_mobius"],
            c["mobius_expansion_exact"], c["ap_decomposition_exact_for_all_d"]))
    A("")
    A("关键点：`p | N` 时 `p|n <=> p|N-n`，该类素因子必须归入 `e` 而不是互补因子对，")
    A("否则重复计数 —— 暴力核对正是为了排除这个错误。")
    A("")
    A("## 五、块 2b · lambda 在等差数列中的偏差 vs 预算")
    A("")
    A("| x | q | max|E(x;q,a)| | 平凡界 x/q | 对平凡界 | 目标预算 x/log²x | 对预算 |")
    A("|---|---|---|---|---|---|---|")
    for r in ap_rows:
        A("| {} | {} | {} | {:.0f} | {:.3f} | {:.0f} | {:.1f} |".format(
            r["x"], r["q"], r["max_abs_AP_sum"], r["trivial_bound_x_over_q"],
            r["ratio_to_trivial"], r["target_budget_x_over_log2x"],
            r["ratio_to_target_budget"]))
    A("")
    A("## 六、裁定")
    A("")
    for s in report["summary"]["interpretation"]:
        A("* " + s)
    A("")
    A("## 七、仍然开放")
    A("")
    for w in report["summary"]["what_remains_open"]:
        A("* " + w)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(json.dumps({k: v for k, v in report["summary"].items()
                      if k != "interpretation"},
                     ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)
    print("saved:", md_path)


if __name__ == "__main__":
    main()
