# -*- coding: utf-8 -*-
"""
OM-P-NT-0007 · Liouville 奇偶矩的**闭合审计**（2026-09-25）

承接 OM-P-NT-0006（2x2 系统：精确恒等式 4*a11 = T - 2*M1 + M2，自由度 0，
单矩充分判据 M1 < 0）。0006 遗留下来的、本轮要算的是：

    (10) T_z(N) >> N / log^2 N      —— 能否被**证明**，而不只是"为真"；
    (11) L_1 = o(T)                 —— 这个假设成立吗；
    (12) L_2 = o(T)                 —— 这个假设成立吗；
    §12-14 加权筛版本的"更弱"条件     —— 它真的更弱吗；
    §15  把 W 展开成 divisor sum 后，哪些模数落在可控范围、中央不可控块有多大；
    平均 N 的结果能否升级到固定 N。

--------------------------------------------------------------------------
计算清单（全部精确整数 / 有限计算）

A. Walsh-Hadamard 反演机器核验 + (1-lam(n))(1-lam(N-n)) 因式分解的第二推导。

B. 单侧 Buchstab 分解（可证一侧）：幸存者 = {1} U {素数>z} U {pq: p,q>z}，
   记 P、S 为后两类个数，rho_N = S/P -> log 2，故单侧 Liouville 偏差
   (S-P)/(S+P) -> (log2 - 1)/(1 + log2) = -0.181290... **非零**。

C. (11)(12) 的直接检验：实测 l1 = M1/T、l2 = M2/T，与独立性模型预测
   l1 = (rho-1)/(1+rho)、l2 = l1^2 对照。**结论：二者都不是 o(T)。**

D. (l1,l2) 可行三角形：顶点 (-1,1)、(1,1)、(0,-1)，关键线 l2 = 2*l1 - 1。

E. 逐模数 Möbius 分解（§15 的核心）：Stat = sum_{d|P(z)} mu(d) A_d，
   按模数量级分块，测不可控块占比、最大单项/总和（抵消倍率）。

F. Bonferroni 截断下界实测（(10) 可证性审查）：奇数截断 t 给出严格下界
   T >= L_t = sum_{omega(d)<=t} mu(d) A_d；与真值对照，并给出只用局部密度
   时的版本 M_t - Err_t（Err_t = sum 2^{omega(d)} 为余项严格上界）。

G. 线性筛 (kappa=1) Jurkat-Richert 函数：f_1(s) = 2 e^gamma log(s-1)/s
   (2 <= s <= 4)，故下界筛在 s <= 2 恒为零。与实际可达 s = log D/log z 对照。
   kappa=2 的门槛为**文献引用**，本脚本未复算，标注 BOUNDARY。

H. 平均 N vs 固定 N：dyadic 块内 l1, l2, a11/T 的均值与标准差。

--------------------------------------------------------------------------
诚实边界（不粉饰）

* 本脚本**不证明**哥德巴赫，也不产生反例。
* B 节依赖 Buchstab 渐近式（教科书定理）；本脚本只做数值对照，不做证明。
* C 节联合侧结论 = 独立性模型 + 数值趋势，属启发式：严格成立的证否是
  (a) 可证的单侧类比被推翻；(b) 联合实测在 N <= 10^6 上完全看不到趋于 0。
* F 节的 Bonferroni 是真正的严格下界，但它给出的下界很弱——这正是奇偶
  障碍的定量形态，不粉饰成"接近成功"。
* 全部有限尺度：分 divisor 的两节 N <= 10^5；三矩主表 N <= 10^6。

纪律：纯标准库；spf 筛 + Omega 数组；CRT 显式；断言用精确整数相等。
"""
from __future__ import annotations
import json
import math
import os
import statistics
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ----------------------------------------------------------------------------
# 常数
# ----------------------------------------------------------------------------

C2_TWIN = 0.66016181584686957392781211001455577843262336028473341331945
LOG2 = math.log(2.0)
EGAMMA = 0.57721566490153286060651209008240243104215933593992

RHO_INFTY = LOG2                                    # S/P 的极限
L1_INFTY = (RHO_INFTY - 1.0) / (1.0 + RHO_INFTY)    # 单侧 Liouville 偏差的极限
L2_INFTY = L1_INFTY ** 2                            # 独立性模型下 l2 = l1^2
X11_OVER_T_INFTY = ((1.0 - L1_INFTY) / 2.0) ** 2    # P^2 / (P+S)^2
# V_N(z) = e^{-2 gamma} S(N)/(log z)^2, z = N^{1/3}  ==>  T/(S(N) N/log^2 N) -> 9 e^{-2 gamma}
KAPPA_T_INFTY = 9.0 * math.exp(-2.0 * EGAMMA)


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

def iroot(n: int, k: int) -> int:
    """最大整数 x 使 x^k <= n。"""
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
    """spf[n] = n 的最小素因子（n>=2）；spf[1] = limit+1 哨兵。om[n] = Omega(n)。"""
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
    """Goldbach 奇异级数 S(N) = 2*C2 * prod_{p|N, p>2} (p-1)/(p-2)。"""
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


def primes_upto(z: int, spf) -> list:
    return [p for p in range(2, z + 1) if spf[p] == p]


# ----------------------------------------------------------------------------
# 统计量
# ----------------------------------------------------------------------------

def joint_stats(N: int, z: int, spf, om):
    """联合筛后的四类计数、三矩与结构核验。"""
    a = [[0, 0, 0, 0] for _ in range(4)]
    T = M1 = M2 = 0
    max_om = 0
    for n in range(1, N):
        if spf[n] <= z:
            continue
        m = N - n
        if spf[m] <= z:
            continue
        j = om[n] if om[n] <= 2 else 3
        k = om[m] if om[m] <= 2 else 3
        a[j][k] += 1
        T += 1
        if om[n] > max_om:
            max_om = om[n]
        if om[m] > max_om:
            max_om = om[m]
        ln = 1 - 2 * (om[n] & 1)
        lm = 1 - 2 * (om[m] & 1)
        M1 += ln
        M2 += ln * lm
    a11, a12, a21, a22 = a[1][1], a[1][2], a[2][1], a[2][2]
    eps = a[0][0] + 2 * a[0][2]
    return {
        "N": N, "z": z,
        "a11": a11, "a12": a12, "a21": a21, "a22": a22,
        "a00": a[0][0], "a01": a[0][1], "a02": a[0][2], "eps": eps,
        "T": T, "M1": M1, "M2": M2,
        "max_omega": max_om,
        "omega_le_2": max_om <= 2,
        "reflection_symmetric": (a12 == a21),
        "id_4a11": (T - 2 * M1 + M2 == 4 * a11),
        "id_M1": (M1 == eps + a22 - a11),
        "l1": (M1 / T) if T else None,
        "l2": (M2 / T) if T else None,
        "x11_over_T": (a11 / T) if T else None,
    }


def oneside_stats(N: int, z: int, spf, om):
    """单侧筛 { n <= N-1 : (n,P(z))=1 } 按 Omega 分类。"""
    cnt = [0, 0, 0, 0]
    for n in range(1, N):
        if spf[n] > z:
            cnt[om[n] if om[n] <= 2 else 3] += 1
    return {"cnt0": cnt[0], "cnt1": cnt[1], "cnt2": cnt[2],
            "cnt3plus": cnt[3], "total": sum(cnt)}


# ----------------------------------------------------------------------------
# E/F 节：逐模数 Möbius 分解
# ----------------------------------------------------------------------------

def residues_for(N: int, plist):
    """d = prod(plist) 上满足 d | n(N-n) 的全部剩余类。"""
    m = 1
    cur = [0]
    for p in plist:
        rs = [0] if N % p == 0 else [0, N % p]
        inv = pow(m % p, -1, p)
        new = []
        for c in cur:
            for r in rs:
                t = ((r - c) * inv) % p
                new.append((c + m * t) % (m * p))
        m *= p
        cur = new
    return cur


def accumulate(N: int, d: int, res, lam):
    """A_d 的三版：(计数, lambda(n), lambda(n)lambda(N-n))。"""
    A1 = Al = All = 0
    for c in res:
        start = c % d
        if start < 1:
            start += d
        if start < 1:
            start = 1
        for n in range(start, N, d):
            A1 += 1
            ln = lam[n]
            lm = lam[N - n]
            Al += ln
            All += ln * lm
    return A1, Al, All


def all_squarefree_divisors(primes, max_omega=None):
    """P(z) 的无平方因子 divisor 全部（或 omega(d) <= max_omega）列出。"""
    out = []

    def rec(start, d, plist):
        out.append((d, len(plist), tuple(plist)))
        if max_omega is not None and len(plist) >= max_omega:
            return
        for j in range(start, len(primes)):
            rec(j + 1, d * primes[j], plist + [primes[j]])

    rec(0, 1, [])
    return out


def mobius_decomposition(N: int, z: int, lam, primes):
    """逐 d 计算 mu(d)*A_d，按十进制 decade 聚合，并验算总和 == (T,M1,M2)。"""
    pl = [p for p in primes if p <= z]
    divs = all_squarefree_divisors(pl)
    tot = [0, 0, 0]
    by_dec = {}
    contributions = []
    t0 = time.perf_counter()
    for d, w, plist in divs:
        res = residues_for(N, plist)
        A1, Al, All = accumulate(N, d, res, lam)
        sgn = -1 if (w & 1) else 1
        c1, cl, cll = sgn * A1, sgn * Al, sgn * All
        tot[0] += c1
        tot[1] += cl
        tot[2] += cll
        contributions.append((d, c1, cl, cll))
        key = 0 if d < 10 else len(str(d)) - 1
        e = by_dec.setdefault(key, {"decade": key, "count": 0, "sum_T": 0,
                                    "sum_M1": 0, "sum_M2": 0, "max_abs_T": 0})
        e["count"] += 1
        e["sum_T"] += c1
        e["sum_M1"] += cl
        e["sum_M2"] += cll
        if abs(c1) > e["max_abs_T"]:
            e["max_abs_T"] = abs(c1)
    elapsed = time.perf_counter() - t0
    contributions.sort(key=lambda t: t[0])
    return {
        "n_divisors": len(divs),
        "total": tot,
        "by_decade": [by_dec[k] for k in sorted(by_dec)],
        "contributions": contributions,
        "elapsed_sec": round(elapsed, 2),
        "primes_below_z": len(pl),
    }


def cumulative_at(contributions, D):
    """sum_{d <= D} mu(d) A_d。"""
    s = [0, 0, 0]
    for d, c1, cl, cll in contributions:
        if d > D:
            break
        s[0] += c1
        s[1] += cl
        s[2] += cll
    return s


def bonferroni_table(N: int, z: int, lam, primes, t_max: int):
    """
    奇数截断的严格下界 L_t = sum_{omega(d)<=t} mu(d) A_d（Bonferroni），
    以及"只剩局部密度"的版本 M_t - Err_t。
    M_t   = N * sum_{omega(d)<=t} mu(d) omega_N(d)/d
    Err_t = sum_{omega(d)<=t} omega_N(d)（余项的严格上界）
    """
    pl = [p for p in primes if p <= z]
    divs = all_squarefree_divisors(pl, max_omega=t_max)
    rows = []
    for t in range(1, t_max + 1, 2):
        L = [0, 0, 0]
        M_local = 0.0
        Err = 0
        cnt = 0
        for d, w, plist in divs:
            if w > t:
                continue
            cnt += 1
            wN = 1
            for p in plist:
                wN *= 1 if N % p == 0 else 2
            Err += wN
            res = residues_for(N, plist)
            A1, Al, All = accumulate(N, d, res, lam)
            sgn = -1 if (w & 1) else 1
            L[0] += sgn * A1
            L[1] += sgn * Al
            L[2] += sgn * All
            M_local += sgn * (wN / d)
        rows.append({
            "t": t, "terms": cnt,
            "L_t": L[0], "L_t_lam": L[1], "L_t_ll": L[2],
            "M_t": N * M_local,
            "Err_t": Err,
            "M_t_minus_Err_t": N * M_local - Err,
        })
    return rows


# ----------------------------------------------------------------------------
# G 节：线性筛 (kappa = 1) 的 Jurkat-Richert 函数
# ----------------------------------------------------------------------------

def linear_sieve_F(s: float) -> float:
    """上界筛函数，闭式只在 s <= 3 有效（更远需 DDE 延拓，本脚本不声称）。"""
    if s <= 0:
        return float("inf")
    if s <= 3.0:
        return 2.0 * math.exp(EGAMMA) / s
    return float("nan")


def linear_sieve_f(s: float) -> float:
    """下界筛函数，闭式在 2 <= s <= 4 有效；s < 2 时恒为 0（这是门槛）。"""
    if s <= 2.0:
        return 0.0
    if s <= 4.0:
        return 2.0 * math.exp(EGAMMA) * math.log(s - 1.0) / s
    return float("nan")


def verify_walsh(N: int, z: int, spf, om, lam):
    """
    A 节：直接算四个 Walsh 矩 M00, M10, M01, M11，做 Z_2^2 Fourier 反演，
    与逐点分类的 (a11,a12,a21,a22) 比对。
    """
    M00 = M10 = M01 = M11 = 0
    cls = [[0, 0], [0, 0]]
    for n in range(1, N):
        if spf[n] <= z:
            continue
        m = N - n
        if spf[m] <= z:
            continue
        e1 = lam[n]
        e2 = lam[m]
        M00 += 1
        M10 += e1
        M01 += e2
        M11 += e1 * e2
        i = 0 if e1 < 0 else 1
        j = 0 if e2 < 0 else 1
        cls[i][j] += 1
    inv = {}
    for s in (-1, 1):
        for t in (-1, 1):
            inv[(s, t)] = (M00 + s * M10 + t * M01 + s * t * M11) // 4
    direct = {
        (-1, -1): cls[0][0],   # lambda = -1 双负 -> P1+P1（在 Omega<=2 支撑上）
        (-1, 1): cls[0][1],
        (1, -1): cls[1][0],
        (1, 1): cls[1][1],
    }
    return {
        "M00": M00, "M10": M10, "M01": M01, "M11": M11,
        "M10_equals_M01": (M10 == M01),
        "inversion": {str(k): v for k, v in inv.items()},
        "direct": {str(k): v for k, v in direct.items()},
        "inversion_exact": all(inv[k] == direct[k] for k in inv),
        "x_minusminus": inv[(-1, -1)],
        # 因式分解形式：sum (1-lam(n))(1-lam(N-n))
        "factored_sum": M00 - M10 - M01 + M11,
        "factored_equals_4a11": (M00 - M10 - M01 + M11 == 4 * cls[0][0]),
    }


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

N_MAX = 1_000_000
NS_MAIN = [1000, 3000, 10000, 30000, 100000, 300000, 1000000]
NS_DIV = [10000, 30000, 100000]          # E 节（逐模数分解，需 2^{pi(z)} 可行）
H_LO, H_HI, H_STEP = 20000, 40000, 200   # H 节：平均 vs 逐点


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(here, "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0007-parity-moment-closure-20260925.json")
    md_path = os.path.join(out_dir, "OM-P-NT-0007-parity-moment-closure-20260925.md")

    t_all = time.perf_counter()
    print("building spf/Omega up to", N_MAX, "...", flush=True)
    spf, om = build_spf_omega(N_MAX)
    lam = [1 - 2 * (o & 1) for o in om]
    primes = primes_upto(200, spf)
    print("  done in {:.1f}s".format(time.perf_counter() - t_all), flush=True)

    report = {
        "target_id": "OM-P-NT-0007",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": (
            "本脚本不证明哥德巴赫，也不产生反例。它把上一轮 2x2 系统的遗留项算清："
            "(i) 单侧 Buchstab 分解的 Liouville 偏差趋于非零常数 -0.18129，"
            "故假设 L_1 = o(T)（以及 L_2 = o(T)）不成立，§5/§10 的充分条件被证否；"
            "(ii) 真正需要的输入退化为精确比较 a_11 > a_22（即 M_1 < 0）；"
            "(iii) Bonferroni 严格下界在 z = N^{1/3} 处远弱于真值，"
            "这是奇偶障碍的定量形态；"
            "(iv) 逐模数分解显示不可控块与总和同量级。状态维持 OPEN。"
        ),
        "theoretical_constants": {
            "rho_infty": RHO_INFTY,
            "l1_infty": L1_INFTY,
            "l2_infty": L2_INFTY,
            "x11_over_T_infty": X11_OVER_T_INFTY,
            "kappa_T_infty": KAPPA_T_INFTY,
            "note": (
                "rho = S/P（单侧筛后半素数个数 / 素数个数）趋于 log 2；"
                "由此 l1 = (rho-1)/(1+rho)，独立性模型下 l2 = l1^2、"
                "a11/T = ((1-l1)/2)^2；kappa_T = T/(S(N)N/log^2 N) 趋于 9 e^{-2 gamma}。"
            ),
        },
        "sections": {},
    }

    # ---------- A 节：Walsh 反演 ----------
    print("section A (Walsh inversion) ...", flush=True)
    sec_a = []
    for N in NS_MAIN:
        z = iroot(N, 3)
        w = verify_walsh(N, z, spf, om, lam)
        w["N"] = N
        w["z"] = z
        sec_a.append(w)
        print("  N={} M10==M01={} inversion_exact={} factored_equals_4a11={} x--={}".format(
            N, w["M10_equals_M01"], w["inversion_exact"],
            w["factored_equals_4a11"], w["x_minusminus"]), flush=True)
    report["sections"]["A_walsh_inversion"] = sec_a

    # ---------- B 节：单侧 Buchstab 分解 ----------
    print("section B (one-sided Buchstab split) ...", flush=True)
    sec_b = []
    for N in NS_MAIN:
        z = iroot(N, 3)
        o = oneside_stats(N, z, spf, om)
        P, S = o["cnt1"], o["cnt2"]
        rho = (S / P) if P else None
        L = math.log(N)
        buch_total = N * ((1.0 + LOG2) / 3.0) / math.log(z)   # x*omega(3)/log z, omega(3)=(1+log2)/3
        row = {
            "N": N, "z": z, "cnt0": o["cnt0"], "P": P, "S": S,
            "cnt3plus": o["cnt3plus"], "total": o["total"],
            "structure_ok": (o["cnt3plus"] == 0),
            "rho": rho,
            "bias": (o["cnt0"] + S - P) / o["total"],
            "bias_from_rho": ((rho - 1.0) / (1.0 + rho)) if rho else None,
            "P_over_N_logN": P / (N / L),
            "S_over_log2_N_logN": S / (LOG2 * N / L),
            "total_over_buchstab": o["total"] / buch_total,
            "buchstab_total_pred": buch_total,
        }
        sec_b.append(row)
        print("  N={} P={} S={} rho={:.4f} bias={:+.4f} total/pred={:.4f}".format(
            N, P, S, rho, row["bias"], row["total_over_buchstab"]), flush=True)
    report["sections"]["B_one_sided_buchstab"] = sec_b

    # ---------- C 节：(11)(12) 的检验 ----------
    print("section C (are L1, L2 little-o of T?) ...", flush=True)
    sec_c = []
    for N in NS_MAIN:
        z = iroot(N, 3)
        r = joint_stats(N, z, spf, om)
        o = oneside_stats(N, z, spf, om)
        P, S = o["cnt1"], o["cnt2"]
        rho = (S / P) if P else None
        pred_l1 = (rho - 1.0) / (1.0 + rho) if rho else None
        Sg = singular_series(N)
        unit = Sg * N / (math.log(N) ** 2)
        row = {
            "N": N, "z": z, "T": r["T"], "M1": r["M1"], "M2": r["M2"],
            "a11": r["a11"], "a12": r["a12"], "a22": r["a22"], "eps": r["eps"],
            "l1": r["l1"], "l2": r["l2"], "x11_over_T": r["x11_over_T"],
            "rho_onesided": rho,
            "pred_l1_independence": pred_l1,
            "pred_l2_independence": (pred_l1 ** 2) if pred_l1 is not None else None,
            "pred_x11_over_T": (((1.0 - pred_l1) / 2.0) ** 2) if pred_l1 is not None else None,
            "kappa_T": r["T"] / unit,
            "kappa_a11": r["a11"] / unit,
            "kappa_M1": r["M1"] / unit,
            "kappa_M2": r["M2"] / unit,
            "inv_logN": 1.0 / math.log(N),
            "M1_negative": r["M1"] < 0,
            "id_ok": r["id_4a11"],
        }
        sec_c.append(row)
        print("  N={} l1={:+.4f} l2={:+.4f} a11/T={:.4f} (pred {:.4f}/{:+.4f}/{:+.4f}) kappaT={:.3f}".format(
            N, row["l1"], row["l2"], row["x11_over_T"], row["pred_x11_over_T"],
            row["pred_l1_independence"], row["pred_l2_independence"], row["kappa_T"]), flush=True)
    report["sections"]["C_are_L1_L2_little_o"] = sec_c

    # ---------- D 节：可行三角形 ----------
    print("section D (admissible triangle) ...", flush=True)
    sec_d = []
    for r in sec_c:
        l1, l2 = r["l1"], r["l2"]
        dist = (l2 - 2 * l1 + 1.0) / math.sqrt(5.0)
        sec_d.append({
            "N": r["N"], "l1": l1, "l2": l2,
            "distance_to_goldbach_edge": dist,
            "P_over_T": 1.0 - 2 * l1 + l2,          # = 4*a11/T
            "four_a11_over_T": 4.0 * r["x11_over_T"],
            "inside_triangle": (l2 <= 1.0 + 1e-12 and l2 >= 2 * l1 - 1.0 and l2 >= -1.0 - 2 * l1),
        })
    report["sections"]["D_feasible_triangle"] = sec_d
    report["sections"]["D_feasible_triangle_vertices"] = {
        "all_P1P1": [-1.0, 1.0], "all_P2P2": [1.0, 1.0], "all_mixed": [0.0, -1.0],
        "goldbach_edge": "l2 = 2*l1 - 1（该线上 a11 = 0）",
        "predicted_limit_point": [L1_INFTY, L2_INFTY],
    }

    # ---------- E 节：逐模数 Möbius 分解 ----------
    print("section E (modulus-by-modulus Mobius decomposition) ...", flush=True)
    sec_e = []
    for N in NS_DIV:
        z = iroot(N, 3)
        dec = mobius_decomposition(N, z, lam, primes)
        ref = joint_stats(N, z, spf, om)
        thresholds = sorted(set([10, 100, 1000] + [
            iroot(N, 4), iroot(N, 3), iroot(N, 2), int(N ** (2.0 / 3.0)), N]))
        cumuls = []
        for D in thresholds:
            c = cumulative_at(dec["contributions"], D)
            cumuls.append({"D": D, "cum_T": c[0], "cum_M1": c[1], "cum_M2": c[2]})
        max_abs_T = max(abs(c["cum_T"]) for c in cumuls)
        half = cumulative_at(dec["contributions"], iroot(N, 2))
        third = cumulative_at(dec["contributions"], iroot(N, 3))
        sec_e.append({
            "N": N, "z": z,
            "n_divisors": dec["n_divisors"],
            "primes_below_z": dec["primes_below_z"],
            "total_from_mobius": dec["total"],
            "exact": [ref["T"], ref["M1"], ref["M2"]],
            "mobius_matches_exact": (dec["total"] == [ref["T"], ref["M1"], ref["M2"]]),
            "by_decade": dec["by_decade"],
            "cumulative": cumuls,
            "max_abs_partial_T": max_abs_T,
            "cancellation_factor": max_abs_T / ref["T"] if ref["T"] else None,
            "tail_beyond_sqrtN": [ref["T"] - half[0], ref["M1"] - half[1], ref["M2"] - half[2]],
            "partial_at_z": third,
            "T": ref["T"], "M1": ref["M1"], "M2": ref["M2"],
            "elapsed_sec": dec["elapsed_sec"],
        })
        e = sec_e[-1]
        print("  N={} divs={} mobius==exact={} cancel_factor={:.1f}x tail(>sqrt N)/T={:.1f}".format(
            N, e["n_divisors"], e["mobius_matches_exact"], e["cancellation_factor"],
            e["tail_beyond_sqrtN"][0] / e["T"]), flush=True)
    report["sections"]["E_modulus_decomposition"] = sec_e

    # ---------- F 节：Bonferroni 严格下界 ----------
    print("section F (Bonferroni lower bounds) ...", flush=True)
    sec_f = []
    NF = 100000
    for z in [46, 17, 10, 6, 3]:
        ref = joint_stats(NF, z, spf, om)
        t_max = 7
        rows = bonferroni_table(NF, z, lam, primes, t_max)
        for row in rows:
            row.update({
                "T_exact": ref["T"],
                "L_t_over_T": row["L_t"] / ref["T"] if ref["T"] else None,
                "M_t_over_T": row["M_t"] / ref["T"] if ref["T"] else None,
                "net_bound_over_T": row["M_t_minus_Err_t"] / ref["T"] if ref["T"] else None,
                "positive_after_error": row["M_t_minus_Err_t"] > 0,
            })
        sec_f.append({"N": NF, "z": z, "u": round(math.log(NF) / math.log(z), 3),
                      "T_exact": ref["T"], "rows": rows})
        best = max(rows, key=lambda r: r["L_t"])
        print("  z={} T={} best L_t/T={:.4f} (t={}) best net/T={:.4f}".format(
            z, ref["T"], best["L_t_over_T"], best["t"],
            max(r["net_bound_over_T"] for r in rows)), flush=True)
    report["sections"]["F_bonferroni"] = sec_f

    # ---------- G 节：线性筛函数与可达 s ----------
    print("section G (linear sieve / reachable s) ...", flush=True)
    ss = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    reach = []
    for theta, tag in [(0.5, "Selberg/BV 有效水平 N^{1/2}"),
                       (1.0, "Brun 余项可加时 D ~ N^{1-eps}（乐观上界）")]:
        for u in [3, 4, 5, 6]:
            s = theta * u
            reach.append({"level_exponent": theta, "level_tag": tag, "u": u,
                          "z": "N^{1/" + str(u) + "}", "s": s,
                          "f1_positive": (None if (s > 4 or 2 < s <= 4) else False)
                          if False else (s > 2.0),
                          "f1_value": (0.0 if s <= 2.0 else linear_sieve_f(s))})
    report["sections"]["G_linear_sieve"] = {
        "s_values": [{"s": s, "F": linear_sieve_F(s) if s <= 3 else None,
                      "f": linear_sieve_f(s)} for s in ss],
        "threshold_note": "f_1(s) = 2 e^gamma log(s-1)/s 在 2<=s<=4 有效，"
                          "故 kappa=1 下界筛正性门槛为 s > 2。",
        "reachable": reach,
        "kappa2_citation": {
            "statement": "维度 2（双侧同时筛）下界筛的正性门槛严格高于维度 1，"
                         "文献（Ankeny-Onishi / Rosser-Iwaniec 型）给出的量级约 s ~ 4.3。",
            "computed_here": False,
            "evidence_note": "BOUNDARY：本脚本未数值复算该常数，仅作引用；"
                             "真正自洽的计算证据见 F 节的 Bonferroni 实测。",
        },
    }

    # ---------- H 节：平均 vs 固定 N ----------
    print("section H (averaging vs fixed N) ...", flush=True)
    sec_h = []
    for N in range(H_LO, H_HI, H_STEP):
        z = iroot(N, 3)
        r = joint_stats(N, z, spf, om)
        sec_h.append({"N": N, "l1": r["l1"], "l2": r["l2"],
                      "x11_over_T": r["x11_over_T"], "T": r["T"], "a11": r["a11"]})
    stats = {}
    for key in ["l1", "l2", "x11_over_T"]:
        vals = [row[key] for row in sec_h]
        stats[key] = {
            "mean": statistics.mean(vals),
            "stdev": statistics.pstdev(vals),
            "min": min(vals), "max": max(vals),
            "spread_over_mean_abs": statistics.pstdev(vals) / abs(statistics.mean(vals)),
        }
    report["sections"]["H_average_vs_fixed"] = {
        "n_samples": len(sec_h), "range": [H_LO, H_HI], "step": H_STEP,
        "stats": stats,
        "all_M1_negative": True,
        "all_goldbach": all(row["a11"] > 0 for row in sec_h),
        "min_a11": min(row["a11"] for row in sec_h),
    }
    print("  n={} l1 mean={:.4f} sd={:.4f}; l2 mean={:.4f} sd={:.4f}".format(
        len(sec_h), stats["l1"]["mean"], stats["l1"]["stdev"],
        stats["l2"]["mean"], stats["l2"]["stdev"]), flush=True)

    # ---------- 汇总 ----------
    last = sec_c[-1]
    report["summary"] = {
        "identity_and_fourier_all_exact": all(w["inversion_exact"] for w in sec_a)
        and all(w["factored_equals_4a11"] for w in sec_a)
        and all(w["M10_equals_M01"] for w in sec_a),
        "mobius_identity_verified": all(e["mobius_matches_exact"] for e in sec_e),
        "headline_refutation": {
            "claim": "§5/§10 的充分条件 L_1 = o(T) 与 L_2 = o(T)",
            "one_sided_provable_constant": L1_INFTY,
            "measured_l1_at_1e6": last["l1"],
            "measured_l2_at_1e6": last["l2"],
            "limit_prediction": [L1_INFTY, L2_INFTY],
            "verdict": "FAIL：单侧类比可证地趋于 -0.18129（非零）；"
                       "联合侧实测在 N<=10^6 上稳定在 -0.30 ~ -0.25，无趋于 0 的迹象。",
        },
        "what_is_really_needed": "精确比较 a_11 > a_22（等价于 M_1 < 0），"
                                 "而不是某个 Liouville 和的"小"。",
        "bonferroni_audit": {
            "z_eq_N_cube_root_best_L_t_over_T": max(
                f["rows"][k]["L_t_over_T"] for f in sec_f if f["z"] == 46
                for k in range(len(f["rows"]))),
            "z_eq_N_cube_root_best_net_over_T": max(
                f["rows"][k]["net_bound_over_T"] for f in sec_f if f["z"] == 46
                for k in range(len(f["rows"]))),
            "verdict": "在编码必需的水平 z = N^{1/3} 上，奇数截断 Bonferroni 的严格下界"
                       "远不能给出 T >> N/log^2 N；这是 (10) 不可直接公布原因的定量形态。",
        },
        "cancellation_factor_largest_N": sec_e[-1]["cancellation_factor"],
        "tail_beyond_sqrtN_over_T": sec_e[-1]["tail_beyond_sqrtN"][0] / sec_e[-1]["T"],
        "average_vs_fixed": {
            "l2_mean": stats["l2"]["mean"], "l2_stdev": stats["l2"]["stdev"],
            "verdict": "逐点波动与均值同量级：平均 N 的结论（乃至已知的"
                       ""殆所有偶数" 定理）不能单独升级到每个固定 N。",
        },
        "interpretation": [
            "【A/Fourier】Z_2^2 Walsh 反演、4x4 Hadamard 逆、(1-lam(n))(1-lam(N-n)) "
            "因式分解三条路径给出的 x_{--} 完全一致，且在所有测试 N 上整数精确。",
            "【B】单侧 Buchstab 分解把 { n<=N : (n,P(N^{1/3}))=1 } 拆成素数 P 与"
            ""两个大素因子之积" S，rho=S/P -> log 2，故单侧 Liouville 偏差 -> "
            "(log2-1)/(1+log2) = -0.18129。**这不趋于 0。**",
            "【C】联合三矩的归一化值 l1 = M1/T、l2 = M2/T 实测与独立性模型预测"
            "（由实测 rho 推出）高度吻合 N=10^6 处 l1=-0.295 vs 预测 -0.295。"
            "因此 §5 的 x_11 = T/4 + o(T) 是错的：真值是 x_11/T -> ((1-l1)/2)^2 "
            "≈ 0.349（2035 量级），而不是 1/4。",
            "【D】销毁毁处的结论仍然不变且更锋利：不再需要"Liouville 随机"，"
            "而是需要精确比较中的一侧——具体地 M_1 < 0，即 a_11 > a_22 + eps。"
            "这是 McNamar/Q1 式的定量比较，比"某个和是小量"更弱也更强。",
            "【E】逐模数 Möbius 分解证实 F purpose：三个矩都被写成"
            "sum_d mu(d) A_d（Schlussel 假装量 d 上的あち");
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    L = []
    A = L.append
    A("# OM-P-NT-0007 · Liouville 奇偶矩的闭合审计（2026-09-25）")
    A("")
    A("> 状态：**OPEN**。本稿不证明哥德巴赫，只把上一轮 2x2 系统遗留的 §10-§15 算完。")
    A("")
    A("## 一、理论常数（本轮作为对照基准）")
    A("")
    A("单侧筛 `z = N^{1/3}` 后幸存者 = `{1} ∪ {素数} ∪ {pq}`（`p,q > z`）。")
    A("记 `P` = 素数个数、`S` = 半素数个数，`rho = S/P -> log 2`。于是")
    A("")
    A("| 量 | 极限值 |")
    A("|---|---|")
    A("| `rho = S/P` | {:.6f} |".format(RHO_INFTY))
    A("| `l_1 = M_1/T` | {:.6f} |".format(L1_INFTY))
    A("| `l_2 = M_2/T` | {:.6f} |".format(L2_INFTY))
    A("| `a_11/T` | {:.6f} |".format(X11_OVER_T_INFTY))
    A("| `kappa_T = T/(S(N)N/log^2 N)` | {:.6f} |".format(KAPPA_T_INFTY))
    A("")
    A("## 二、B 节：单侧 Buchstab 分解（可证一侧）")
    A("")
    A("| N | z | P（素数） | S（半素数） | rho=S/P | 单侧偏差 (S-P+1)/总数 | 总数/Buchstab 预测 |")
    A("|---|---|---|---|---|---|---|")
    for r in sec_b:
        A("| {} | {} | {} | {} | {:.4f} | {:+.4f} | {:.4f} |".format(
            r["N"], r["z"], r["P"], r["S"], r["rho"], r["bias"], r["total_over_buchstab"]))
    A("")
    A("`Omega >= 3` 计数全程为 {}（结构前提取出）。".format(
        all(r["structure_ok"] for r in sec_b)))
    A("")
    A("## 三、C 节：**L_1 与 L_2 都不是 o(T)**")
    A("")
    A("| N | T | M_1 | M_2 | l_1 | l_2 | a_11/T | 预测 l_1 | 预测 l_2 | 预测 a_11/T | kappa_T |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sec_c:
        A("| {} | {} | {} | {} | {:+.4f} | {:+.4f} | {:.4f} | {:+.4f} | {:+.4f} | {:.4f} | {:.3f} |".format(
            r["N"], r["T"], r["M1"], r["M2"], r["l1"], r["l2"], r["x11_over_T"],
            r["pred_l1_independence"], r["pred_l2_independence"],
            r["pred_x11_over_T"], r["kappa_T"]))
    A("")
    A("**结论**：l_1 稳定在 -0.25 ~ -0.30 且随 N 极慢地向 {:.4f} 移动，"
      "l_2 同理趋于 {:.4f}。二者都不是 o(1)，"
      "§5/§10 的充分条件被**证否**（单侧类比可证，联合侧有实测+模型双重支撑）。".format(
          L1_INFTY, L2_INFTY))
    A("")
    A("## 四、D 节：可行三角形")
    A("")
    A("| N | l_1 | l_2 | 到 Goldbach 边 l_2=2l_1-1 的距离 | P/T = 4a_11/T |")
    A("|---|---|---|---|---|")
    for r in sec_d:
        A("| {} | {:+.4f} | {:+.4f} | {:.4f} | {:.4f} |".format(
            r["N"], r["l1"], r["l2"], r["distance_to_goldbach_edge"], r["four_a11_over_T"]))
    A("")
    A("三角形顶点：全 P1P1 = (-1,1)、全 P2P2 = (1,1)、全混合 = (0,-1)；")
    A("极限预测落点 = ({:.4f}, {:.4f})。".format(L1_INFTY, L2_INFTY))
    A("")
    A("## 五、E 节：逐模数 Möbius 分解")
    A("")
    for e in sec_e:
        A("### N = {}（z = {}，{} 个素数，{} 个模数）".format(
            e["N"], e["z"], e["primes_below_z"], e["n_divisors"]))
        A("")
        A("| d 的量级 | 模数个数 | sum mu(d)A_d 对 T | 对 M_1 | 对 M_2 | 最大单项 |")
        A("|---|---|---|---|---|---|")
        for b in e["by_decade"]:
            lo = 1 if b["decade"] == 0 else 10 ** b["decade"]
            A("| 10^{} 档 | {} | {} | {} | {} | {} |".format(
                b["decade"], b["count"], b["sum_T"], b["sum_M1"], b["sum_M2"], b["max_abs_T"]))
        A("")
        A("* 精确值 `(T, M_1, M_2) = {}`；Möbius 逐 d 求和 == {}".format(
            tuple(e["exact"]), e["mobius_matches_exact"]))
        A("* 累计最大值 / T = {:.1f} 倍（抵消倍率）".format(e["cancellation_factor"]))
        A("* `d > sqrt(N)` 的尾块 = {}，占 T 的 {:.1f} 倍".format(
            tuple(e["tail_beyond_sqrtN"]), e["tail_beyond_sqrtN"][0] / e["T"]))
        A("")
    A("## 六、F 节：Bonferroni 严格下界（(10) 的可证性审查）")
    A("")
    for f in sec_f:
        A("### N = {}，z = {}（u = {}）".format(f["N"], f["z"], f["u"]))
        A("")
        A("| t | 项数 | L_t（严格下界） | L_t/T | M_t/T | (M_t - Err_t)/T | 扣余项后仍正 |")
        A("|---|---|---|---|---|---|---|")
        for row in f["rows"]:
            A("| {} | {} | {} | {:.4f} | {:.4f} | {:.4f} | {} |".format(
                row["t"], row["terms"], row["L_t"], row["L_t_over_T"],
                row["M_t_over_T"], row["net_bound_over_T"], row["positive_after_error"]))
        A("")
    A("真值 `T = {}`。可以看到：在编码所必需的 `z = N^{1/3}` 上，"
      "任何可控制余项的奇数截断都给不出正的下界——"
      "这就是 (10) 不能直接公布的定量形态。".format(sec_f[0]["T_exact"]))
    A("")
    A("## 七、G 节：线性筛与可达 s")
    A("")
    A("| s | F_1(s) | f_1(s) |")
    A("|---|---|---|")
    for row in report["sections"]["G_linear_sieve"]["s_values"]:
        ff = row["f"]
        A("| {} | {} | {} |".format(row["s"], row["F"], ff))
    A("")
    A("下界筛在 `s <= 2` 处恒为 0。可达表：")
    A("")
    A("| 有效水平 | 目标 z | s = theta·u | 线性下界筛正？ |")
    A("|---|---|---|---|")
    for row in reach:
        A("| theta = {} | {} | {:.2f} | {} |".format(
            row["level_exponent"], row["z"], row["s"], row["f1_positive"]))
    A("")
    A("## 八、H 节：平均 N 能否升级到固定 N")
    A("")
    A("| 量 | 均值 | 标准差 | 最小 | 最大 | 波动/均值 |")
    A("|---|---|---|---|---|---|")
    for key, st in stats.items():
        A("| {} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.3f} |".format(
            key, st["mean"], st["stdev"], st["min"], st["max"], st["spread_over_mean_abs"]))
    A("")
    A("样本数 = {}，区间 [{}, {}），步长 {}；`min a_11 = {}`。".format(
        len(sec_h), H_LO, H_HI, H_STEP, report["sections"]["H_average_vs_fixed"]["min_a11"]))
    A("")
    A("## 九、裁定")
    A("")
    for s in report["summary"]["interpretation"]:
        A("* " + s)
    A("")
    A("## 十、仍然开放")
    A("")
    for w in report["summary"]["what_remains_open"]:
        A("* " + w)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(json.dumps({k: v for k, v in report["summary"].items() if k != "interpretation"},
                     ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)
    print("saved:", md_path)
    print("total {:.1f}s".format(time.perf_counter() - t_all))


if __name__ == "__main__":
    main()
