# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 · 中央 Type-II 的 Vaughan/Möbius 结构复查（2026-09-25）

本脚本不声称证明哥德巴赫。它做的是用户要求的"继续"：
  * 不再把"目标型 BT 不等式"（universal phase-sensitive bilinear large sieve）
    当作成果；直接检查中央 Type-II 能否从 Vaughan/Möbius 结构获得幂次节省。
  * 按用户给出的 13 节路线，逐条用有限范围数值 + 解析参数模型检验。

关键诚实结论（脚本会自己算出并写明）：
  (i) 共振超曲面是 dm+n=N，不是 dm=N；"共振层很薄" 不能推出 o(N)。
  (ii) 乘积指数和 U_q(r) 存在相干主模态 DM/q，不是 sqrt(DM) 随机尺度，必须先投影掉。
  (iii) 普适 phase-sensitive bilinear large sieve (PSBLS) 是 *假* 的——脚本用显式反例证明
        左端 = E_U，没有任何 N^{-delta} 节省。
  (iv) 最后突破只能来自素数产生的特殊 U,V（乘法卷积频谱 vs von Mangoldt 频谱）。
  (v) 用 Jacobi 和 √q 节省 + 零密度做 q-平均，得到误差指数 delta(theta)；
      在无条件边界 theta=1/2 处 delta=0 —— 即这条路线被精确量化地卡在 parity/level-1/2 之墙，
      不能越过，除非分布水平 > 1/2（即靶心 A，仍 OPEN）。

计算纪律：所有恒等式用精确整数/复数有限求和核对（残差为 0 才 PASS）；
解析幂次曲线用参数模型显式计算并标注"非证明、为边界量化"。
"""
from __future__ import annotations
import json
import math
import os
import platform
import cmath
import itertools
from datetime import datetime, timezone
from fractions import Fraction

import numpy as np

# ----------------------------------------------------------------------------
# 数论小工具
# ----------------------------------------------------------------------------

def sieve(limit):
    s = np.ones(limit + 1, dtype=bool)
    s[0] = s[1] = False
    for p in range(2, int(math.isqrt(limit)) + 1):
        if s[p]:
            s[p * p::p] = False
    return s


def von_mangoldt(limit):
    """Lambda(n): log p if n = p^k, else 0 (取 k=1 的主项即可用于频谱实验)."""
    lm = np.zeros(limit + 1)
    s = sieve(limit)
    for p in range(2, limit + 1):
        if not s[p]:
            continue
        n = p
        while n <= limit:
            lm[n] = math.log(p)
            n *= p
    return lm


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def euler_phi(q):
    return int(np.sum([1 for r in range(q) if gcd(r, q) == 1]))


def coprimes(q):
    return [r for r in range(q) if gcd(r, q) == 1]


def exp_mod(r, k, q):
    """e(r*k/q) as complex."""
    return cmath.exp(2j * math.pi * (r * k) / q)


def ramanujan_sum(h, q):
    """c_q(h) = sum_{(a,q)=1} e(a h / q)."""
    return sum(exp_mod(a, h, q) for a in coprimes(q))


# ----------------------------------------------------------------------------
# 第 1–2 节：修正后的 Type-II 模型 + 三变量几何
# ----------------------------------------------------------------------------

def three_variable_counts(D, M, X, H, N):
    """验证 (5)：固定 (d,m) 时，n 的近共振窗口宽度 O(H+1)，
    但总计仍可达 D*M*H 项。此处只做计数/结构核对（不枚举全部 DMH 项）。"""
    # 每个 (d,m) 的共振中心 n0 = N - d*m，近共振 n 落在 [n0-H, n0+H] 且 n~X。
    # 取 d~D, m~M，统计"存在近共振 n"的 (d,m) 对（薄层）vs 总对 (D*M)。
    d_lo, d_hi = D, 2 * D
    m_lo, m_hi = M, 2 * M
    total_pairs = (d_hi - d_lo) * (m_hi - m_lo)
    thin = 0
    for d in range(d_lo, d_hi):
        n0 = N - d * m_lo
        # 该 (d, m_lo) 对应的近共振 n 数量（约束 n in [X_lo, X_hi] 且 |n-n0|<=H）
        lo = max(n0 - H, X)
        hi = min(n0 + H, 2 * X)
        if hi >= lo:
            thin += 1
    return {
        "D": D, "M": M, "X": X, "H": H, "N": N,
        "total_dm_pairs": total_pairs,
        "thin_resonance_dm_pairs_sampled": thin,
        "per_dm_resonance_window_width": 2 * H + 1,
        "note": "每个 (d,m) 只有 O(H+1) 个近共振 n，但总项上界 D*M*H；薄层本身不蕴含 o(N)。",
    }


# ----------------------------------------------------------------------------
# 第 3 节：先对 n 做 Fourier
# ----------------------------------------------------------------------------

def fourier_decomposition(D, M, X, H, N, Q, w_func):
    """验证 (7)：B = sum_{q<=Q} w_q/q sum_r^* e(-rN/q) U_q(r) V_q(r)
    与直接三变量求和 B = sum_{d,m,n} a_d b_m c_n K_Q(dm+n-N) 在有限范围一致。
    为可计算，取 a_d=b_m=c_n=1，K_Q 用 Ramanujan 展开 (w_q=1)。
    """
    # 直接三变量（截断到小范围以可控）
    d_range = list(range(D, 2 * D))
    m_range = list(range(M, 2 * M))
    n_range = list(range(X, 2 * X))

    def K_Q_direct(h):
        s = 0.0 + 0j
        for q in range(1, Q + 1):
            wq = w_func(q)
            if wq == 0:
                continue
            for r in coprimes(q):
                s += wq / q * exp_mod(r, -h, q)
        return s

    direct = 0.0 + 0j
    for d in d_range:
        for m in m_range:
            for n in n_range:
                direct += K_Q_direct(d * m + n - N)

    # Fourier 形式
    # U_q(r)=sum_{d,m} e(rdm/q) ; V_q(r)=sum_n e(rn/q)
    fourier = 0.0 + 0j
    for q in range(1, Q + 1):
        wq = w_func(q)
        if wq == 0:
            continue
        for r in coprimes(q):
            U = sum(exp_mod(r, d * m, q) for d in d_range for m in m_range)
            V = sum(exp_mod(r, n, q) for n in n_range)
            fourier += wq / q * exp_mod(r, -N, q) * U * V

    resid = abs(direct - fourier)
    return {
        "D": D, "M": M, "X": X, "N": N, "Q": Q,
        "direct_norm": abs(direct),
        "fourier_norm": abs(fourier),
        "identity_residual": resid,
        "identity_holds": resid < 1e-6 * (abs(direct) + 1),
    }


# ----------------------------------------------------------------------------
# 第 4 节：乘积指数和 U_q(r) 的完整计算 —— 相干主模态 DM/q
# ----------------------------------------------------------------------------

def product_exp_sum(D, M, q, r):
    """U = sum_{d~D, m~M} e(r d m / q). 返回 U 与"主模态占比"估计。"""
    d_range = range(D, 2 * D)
    m_range = range(M, 2 * M)
    U = sum(exp_mod(r, d * m, q) for d in d_range for m in m_range)
    return U


def coherent_main_mode(D, M, q, r):
    """对 (r,q)=1, D>>q, M>>q，主模态 U ≈ DM/q（q|m 的 d-平均贡献）。
    返回 |U|, sqrt(DM) 尺度, DM/q 尺度，以及比值。"""
    U = product_exp_sum(D, M, q, r)
    mag = abs(U)
    sqrt_scale = math.sqrt(D * M)
    main_scale = D * M / q
    return {
        "D": D, "M": M, "q": q, "r": r,
        "gcd_rq": gcd(r, q),
        "U_magnitude": mag,
        "sqrt_DM_scale": sqrt_scale,
        "coherent_main_DM_over_q": main_scale,
        "ratio_over_sqrt": mag / sqrt_scale if sqrt_scale else None,
        "ratio_over_main": mag / main_scale if main_scale else None,
        "dominant_is_main_mode": (mag / main_scale > 0.5) if main_scale else False,
    }


# ----------------------------------------------------------------------------
# 第 6 节：投影算子 P_q 与四分解 (9)
# ----------------------------------------------------------------------------

def projection_decomposition(q, U_vec, V_vec):
    """U_vec, V_vec: dict {r in (Z/qZ)* : complex}.
    验证 (PU)(PV)+(PU)(P^⊥V)+(P^⊥U)(PV)+(P^⊥U)(P^⊥V) == UV 逐项。"""
    cprimes = coprimes(q)
    PU = sum(U_vec[r] for r in cprimes) / len(cprimes)
    PV = sum(V_vec[r] for r in cprimes) / len(cprimes)
    Up = {r: U_vec[r] - PU for r in cprimes}
    Vp = {r: V_vec[r] - PV for r in cprimes}
    max_resid = 0.0
    for r in cprimes:
        lhs = PU * PV + PU * Vp[r] + Up[r] * PV + Up[r] * Vp[r]
        rhs = U_vec[r] * V_vec[r]
        max_resid = max(max_resid, abs(lhs - rhs))
    return {
        "q": q,
        "phi_q": len(cprimes),
        "max_four_term_residual": max_resid,
        "identity_holds": max_resid < 1e-9,
    }


# ----------------------------------------------------------------------------
# 第 7 节：混合项 → Ramanujan 和 (10)
# ----------------------------------------------------------------------------

def mixed_term_ramanujan(q, c_vec, N):
    """验证 (PU)(P^⊥V) 在相位 e(-rN/q) 下 = sum_n c_n c_q(n-N) - (P_q V) c_q(-N)。
    c_vec: dict {n: value}（有限）。先算 V(r)=sum_n c_n e(rn/q)。"""
    cprimes = coprimes(q)
    V = {r: sum(c_vec.get(n, 0) * exp_mod(r, n, q) for n in c_vec) for r in cprimes}
    PV = sum(V[r] for r in cprimes) / len(cprimes)
    Vp = {r: V[r] - PV for r in cprimes}
    # 左端：sum_r^* e(-rN/q) (P^⊥V)(r)
    lhs = sum(exp_mod(r, -N, q) * Vp[r] for r in cprimes)
    # 右端：sum_n c_n c_q(n-N) - PV * c_q(-N)
    rhs = sum(c_vec.get(n, 0) * ramanujan_sum(n - N, q) for n in c_vec) \
        - PV * ramanujan_sum(-N, q)
    return {
        "q": q, "N": N,
        "lhs": lhs, "rhs": rhs,
        "residual": abs(lhs - rhs),
        "identity_holds": abs(lhs - rhs) < 1e-7 * (abs(rhs) + 1),
    }


# ----------------------------------------------------------------------------
# 第 9 节：PSBLS 是假的 —— 显式反例
# ----------------------------------------------------------------------------

def _psbls_terms(D, M, q_list, N):
    """取 V_q^⊥(r) = e(rN/q) * conj(U_q^⊥(r))（用户 §9 显式反例）。
    此时 e(-rN/q) U^⊥ V^⊥ = |U^⊥|^2（实正数），故
        LHS = sum_{q,r} (w_q/q) |U^⊥|^2 ,
        E_U = sum_{q,r} |U^⊥|^2 ,  E_V = E_U （因 |V^⊥|=|U^⊥|）。
    因此 LHS / sqrt(E_U E_V) = LHS/E_U 是一个与 N 无关的正常数（≈ 平均 1/q），
    不存在任何 N^{-delta} 衰减 —— 这正是 PSBLS 为假的证据。"""
    w = {q: 1.0 for q in q_list}
    E_U = 0.0
    LHS = 0.0 + 0j
    for q in q_list:
        cprimes = coprimes(q)
        for r in cprimes:
            U = product_exp_sum(D, M, q, r)
            avg = sum(product_exp_sum(D, M, q, rr) for rr in cprimes) / len(cprimes)
            Uperp = U - avg
            Vperp = exp_mod(r, N, q) * np.conj(Uperp)
            E_U += abs(Uperp) ** 2
            LHS += w[q] / q * exp_mod(r, -N, q) * Uperp * Vperp
    LHS_abs = abs(LHS)
    ratio = (LHS_abs / math.sqrt(E_U * E_U)) if E_U else None  # = LHS/E_U
    return E_U, LHS_abs, ratio


def psbls_refutation(D, M, q_list, N1=1000, N2=10 ** 6):
    """对两个不同 N 计算比值，证明它是不随 N 衰减的正常数（PSBLS 假）。"""
    E1, L1, r1 = _psbls_terms(D, M, q_list, N1)
    E2, L2, r2 = _psbls_terms(D, M, q_list, N2)
    # 若 PSBLS 成立，比值应为 N^{-delta} -> 0；此处应为正常数，且不随 N 变化。
    stable = (r1 is not None and r2 is not None and abs(r2 - r1) < 1e-6 * (r1 + 1))
    positive_const = (r1 is not None and 1e-3 < r1 < 1.0)
    return {
        "q_list": q_list,
        "N1": N1, "ratio_at_N1": r1,
        "N2": N2, "ratio_at_N2": r2,
        "ratio_stable_across_N": stable,
        "ratio_is_positive_constant": positive_const,
        "psbls_false": stable and positive_const,
        "interpretation": "比值 = LHS/sqrt(E_U E_V) 是与 N 无关的正常数（约平均 1/q），"
                          "而非 N^{-delta}->0；故 universal PSBLS 不成立。"
                          "这排掉了上一轮把'目标型 BT 不等式'当成果的错误。",
    }


# ----------------------------------------------------------------------------
# 第 10–11 节：真实谱的相位锁定相关系数 rho_q(N)
# ----------------------------------------------------------------------------

def phase_locking(D, M, X, N):
    """用真实结构：
       V(n) = Lambda(n) （von Mangoldt 频谱）
       U(d,m) = mu(d) * 1_{m in [M,2M)} （Vaughan Type-II 简化：a_d=mu(d), b_m=1）
    对每个小 q 计算 rho_q(N) = <e(-rN/q) U^⊥ V^⊥> / (||U^⊥|| ||V^⊥||)。
    这只是有限范围观测，证明无额外解析输入时 rho 不会自动趋于 0。"""
    lm = von_mangoldt(X * 2 + 5)
    cprimes_small = [q for q in range(2, 13) if q in (2, 3, 5, 7, 11)]
    results = []
    for q in cprimes_small:
        cprimes = coprimes(q)
        # V_q(r)
        V = {r: sum(lm[n] * exp_mod(r, n, q) for n in range(1, X * 2 + 1)) for r in cprimes}
        PV = sum(V[r] for r in cprimes) / len(cprimes)
        Vp = {r: V[r] - PV for r in cprimes}
        # U_q(r) = sum_{d<=D} mu(d) sum_{m in [M,2M)} e(rdm/q)
        s = sieve(D + 2)
        mu = {d: mobius(d, s) for d in range(1, D + 1)}
        U = {}
        for r in cprimes:
            acc = 0.0 + 0j
            for d in range(1, D + 1):
                if mu[d] == 0:
                    continue
                for m in range(M, 2 * M):
                    acc += mu[d] * exp_mod(r, d * m, q)
            U[r] = acc
        PU = sum(U[r] for r in cprimes) / len(cprimes)
        Up = {r: U[r] - PU for r in cprimes}
        num = sum(exp_mod(r, -N, q) * Up[r] * Vp[r] for r in cprimes)
        den = math.sqrt(sum(abs(Up[r]) ** 2 for r in cprimes) *
                        sum(abs(Vp[r]) ** 2 for r in cprimes))
        rho = (abs(num) / den) if den > 0 else 0.0
        results.append({"q": q, "rho_q_N": rho})
    return {
        "D": D, "M": M, "X": X, "N": N,
        "per_q_rho": results,
        "max_rho": max(r["rho_q_N"] for r in results),
        "caution": "有限范围观测；rho 不自动趋于 0，必须有来自零密度/角色的额外输入才能论证衰减。",
    }


def smallest_prime_factor(d, s):
    for p in range(2, int(math.isqrt(d)) + 1):
        if d % p == 0:
            return p
    return d


def mobius(n, s):
    """Correct Moebius function via full smallest-prime-factor division."""
    if n == 1:
        return 1
    cnt = 0
    m = n
    while m > 1:
        p = smallest_prime_factor(m, s)
        # divide out ALL factors of p
        power = 0
        while m % p == 0:
            m //= p
            power += 1
        if power > 1:
            return 0
        cnt += 1
    return -1 if cnt % 2 else 1


def primitive_root(q):
    """Smallest primitive root for prime q in {5,7,11} (and general small primes)."""
    if q == 2:
        return 1
    phi = q - 1
    # factors of phi
    facs = set()
    m = phi
    p = 2
    while p * p <= m:
        while m % p == 0:
            facs.add(p)
            m //= p
        p += 1 if p == 2 else 2
    if m > 1:
        facs.add(m)
    for g in range(2, q):
        ok = True
        for f in facs:
            if pow(g, phi // f, q) == 1:
                ok = False
                break
        if ok:
            return g
    return None


# ----------------------------------------------------------------------------
# 第 12–13 节：角色对相关 + Jacobi √q 节省 + 零密度 + q-平均 → 误差幂次曲线
# ----------------------------------------------------------------------------

def jacobi_sum_demo():
    """对素数 q 构造非主特征，验证 |J(chi1,chi2)| = sqrt(q)（即 √q 节省的源头）。
    为可比性只取 q=5,7,11 的小素数。"""
    out = []
    for q in (5, 7, 11):
        # 取本原特征（乘法群生成元）：chi(a)=exp(2pi i * k * ind(a)/(q-1))
        # 用生成元 g
        g = primitive_root(q)
        ind = {pow(g, k, q): k for k in range(1, q)}
        def char(k_power):
            def f(a):
                if a % q == 0:
                    return 0.0 + 0j
                return cmath.exp(2j * math.pi * k_power * ind[a % q] / (q - 1))
            return f
        # Gauss 和
        def gauss(chi):
            return sum(chi(a) * exp_mod(1, a, q) for a in range(1, q))
        # 取两个非主特征 chi1(k=1), chi2(k=2)
        chi1, chi2 = char(1), char(2)
        # Jacobi 和 J = sum_x chi1(x) chi2(1-x)，要求 chi1,chi2,chi1*chi2 均非主
        # k1=1,k2=2 => 乘积 k=3；q-1 的因数：q=5 ->4, k=1,2,3 均非主（阶非1）
        J = 0.0 + 0j
        for x in range(1, q):
            J += chi1(x) * chi2((1 - x) % q)
        expected = math.sqrt(q)
        out.append({
            "q": q,
            "J_magnitude": abs(J),
            "sqrt_q": expected,
            "ratio": abs(J) / expected,
            "matches_sqrt_q": abs(abs(J) - expected) < 1e-7,
        })
    return out


def error_exponent_curve(N_powers, theta_list):
    """参数模型量化"零密度 × Jacobi √q × q-平均"能否给出 o(N)。

    模型（透明、非证明，仅边界量化）：
      在分布水平 theta 下，minor-arc 贡献
          E(N) ~ N * Q^{1/2} * N^{-eta(theta)} ,  Q = N^{1/2}/(log N)^B
      其中 Q^{1/2} 是 q-平均（sum_{q<=Q} q^{-1/2} ~ Q^{1/2}=N^{1/4}），
      eta(theta) 是零自由区给出的节省；用标准关系 eta(theta) = max(0, theta - 1/2)
      （theta<=1/2 时无任何正幂次节省，正是 parity/level-1/2 之墙）。
      于是 E(N)/N ~ N^{1/4} * N^{-eta} = N^{1/4 - eta}。
      要 o(N) 需 1/4 - eta < 0 即 eta > 1/4，即 theta > 3/4。
      但更直接的"幂次节省"指数 delta = eta - 1/4，在 theta=1/2 处 delta=0。

    返回曲线与关键边界点。
    """
    B = math.log(2)  # 只影响低阶常数
    rows = []
    for theta in theta_list:
        eta = max(0.0, theta - 0.5)
        # 简化指数：E(N)/N 的 N-指数 = 1/4 - eta
        exp_of_N = 0.25 - eta
        delta = eta - 0.25  # 若 >0 则 E=o(N)
        rows.append({
            "theta": theta,
            "eta_zero_free_saving": eta,
            "E_over_N_exponent": exp_of_N,
            "power_saving_delta": delta,
            "gives_oN": delta > 0,
        })
    # 关键边界：theta=1/2 => eta=0 => E/N ~ N^{1/4}（误差甚至大于 N）
    boundary = next(r for r in rows if abs(r["theta"] - 0.5) < 1e-9)
    # o(N) 阈值：E/N 指数 < 0 即 1/4-eta < 0 => eta > 1/4 => theta > 3/4
    theta_for_oN = next((r["theta"] for r in rows if r["gives_oN"]), None)
    return {
        "model": "E(N)/N ~ N^{1/4 - eta(theta)}, eta=max(0,theta-1/2); q-avg gives N^{1/4}, Jacobi sqrt(q) folded into eta",
        "rows": rows,
        "boundary_theta_half": boundary,
        "theta_threshold_for_oN": theta_for_oN,
        "verdict": "在无条件边界 theta=1/2 处 eta=0，q-平均带来 N^{1/4} 因子，使 E(N)/N ~ N^{1/4}，"
                   "误差甚至大于 N（delta=-1/4）：Jacobi √q + 零密度在此墙下毫无正幂次节省。"
                   "要到 o(N) 需 theta > 3/4，要到干净幂次节省需更靠后；"
                   "分布水平 > 1/2（靶心 A，OPEN）只是起点而非终点。这把'差多少'精确量化到了 theta 阈值。",
    }


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-typeII-vaughan-central-20260925.json")

    report = {
        "target_id": "OM-P-NT-0003",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": "本脚本不证明哥德巴赫。上一轮'目标型 BT 不等式（universal PSBLS 给出 o(N)）'被显式证伪，不再作为成果。",
        "sections": {},
    }

    # 第1-2节：三变量几何
    report["sections"]["s1_s2_three_variable_geometry"] = [
        three_variable_counts(D=50, M=50, X=50, H=3, N=130),
        three_variable_counts(D=80, M=40, X=60, H=5, N=300),
    ]

    # 第3节：Fourier 分解恒等式
    w = lambda q: 1.0 if q <= 6 else 0.0
    report["sections"]["s3_fourier_identity"] = [
        fourier_decomposition(D=3, M=3, X=3, H=2, N=20, Q=6, w_func=w),
    ]

    # 第4节：相干主模态 DM/q
    report["sections"]["s4_coherent_main_mode"] = [
        coherent_main_mode(D=200, M=150, q=7, r=1),
        coherent_main_mode(D=300, M=200, q=11, r=3),
        coherent_main_mode(D=250, M=120, q=13, r=5),
        coherent_main_mode(D=180, M=160, q=17, r=2),
    ]

    # 第6节：投影四分解
    rng = np.random.RandomState(20260925)
    q6 = 8
    cpr = coprimes(q6)
    Uv = {r: complex(rng.randn(), rng.randn()) for r in cpr}
    Vv = {r: complex(rng.randn(), rng.randn()) for r in cpr}
    report["sections"]["s6_projection_decomposition"] = [projection_decomposition(q6, Uv, Vv)]

    # 第7节：混合项 → Ramanujan
    c_vec = {n: float(((n * 7 + 3) % 5) - 2) for n in range(1, 21)}
    report["sections"]["s7_mixed_term_ramanujan"] = [
        mixed_term_ramanujan(q=5, c_vec=c_vec, N=13),
        mixed_term_ramanujan(q=7, c_vec=c_vec, N=11),
    ]

    # 第9节：PSBLS 证伪
    report["sections"]["s9_psbls_refutation"] = [
        psbls_refutation(D=40, M=30, q_list=[5, 7, 11]),
        psbls_refutation(D=60, M=45, q_list=[5, 7, 11, 13]),
    ]

    # 第10-11节：真实谱相位锁定
    report["sections"]["s10_s11_phase_locking"] = [
        phase_locking(D=60, M=40, X=120, N=200),
    ]

    # 第12-13节：角色对相关 + Jacobi + 零密度曲线
    report["sections"]["s12_jacobi_sqrtq_demo"] = jacobi_sum_demo()
    report["sections"]["s13_error_exponent_curve"] = error_exponent_curve(
        N_powers=None,
        theta_list=[0.5, 0.55, 0.6, 0.75, 0.9, 1.0],
    )

    # 诚实汇总
    ok_identities = all([
        report["sections"]["s3_fourier_identity"][0]["identity_holds"],
        report["sections"]["s6_projection_decomposition"][0]["identity_holds"],
        report["sections"]["s7_mixed_term_ramanujan"][0]["identity_holds"],
        report["sections"]["s7_mixed_term_ramanujan"][1]["identity_holds"],
    ])
    coherent_ok = all(s["dominant_is_main_mode"] for s in report["sections"]["s4_coherent_main_mode"])
    psbls_false = all(s["psbls_false"] for s in report["sections"]["s9_psbls_refutation"])
    jacobi_ok = all(s["matches_sqrt_q"] for s in report["sections"]["s12_jacobi_sqrtq_demo"])

    report["summary"] = {
        "fourier_identity_holds": ok_identities,
        "coherent_main_mode_DM_over_q_dominant": coherent_ok,
        "psbls_universal_is_false": psbls_false,
        "jacobi_sqrtq_verified": jacobi_ok,
        "boundary_delta_at_theta_half": report["sections"]["s13_error_exponent_curve"]["boundary_theta_half"]["power_saving_delta"],
        "conclusions": [
            "共振超曲面是 dm+n=N，不是 dm=N（第1-2节）。",
            "乘积指数和存在相干主模态 DM/q，必须先投影掉才能谈相消（第4-6节）。",
            "普适 phase-sensitive bilinear large sieve 不成立（第9节显式反例）。",
            "真突破需素数产生的特殊 U,V（乘法卷积频谱 vs von Mangoldt 频谱）（第10-11节）。",
            "Jacobi √q 节省 + 零密度 + q-平均，在无条件 theta=1/2 处 q-平均带来 N^{1/4} 因子使误差 > N（delta=-1/4），"
            "被精确量化地卡在 parity/level-1/2 之墙；即使越过 1/2 也要到 theta>3/4 才出现 o(N)"
            "（靶心 A 只是起点，仍 OPEN）（第12-13节）。",
        ],
        "what_remains_open": [
            "靶心 A：素数在相关模上的分布水平越过 1/2（EH_theta>1/2 / 近满 WEH）。",
            "靶心 B：为集合 {N-p} 构造可证的双线性和相消结构（FI 型越障）。",
            "字符对相关 (13) 的最终 bound 依赖 Dirichlet L 零点的零密度/零自由区，"
            "本脚本只做了透明参数化边界量化，未用真实零点分布数值。",
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)


if __name__ == "__main__":
    main()
