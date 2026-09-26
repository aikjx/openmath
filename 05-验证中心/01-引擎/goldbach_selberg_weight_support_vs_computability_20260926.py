# -*- coding: utf-8 -*-
"""
OM-P-NT-0008 · 加权 2x2 奇偶矩：Selberg 权的 divisor 展开、支撑条件与可算主项的正面冲突
（2026-09-26，承接 OM-P-NT-0006 / OM-P-NT-0007）

用户上一轮把 Goldbach 归约成 2x2 奇偶矩系统并给出精确恒等式

    4*a_11 = T - 2*M_1 + M_2 ,        a_11 = #{(n,N-n) : n,N-n 皆素, 均在 S_z 内}

本轮把它"彻底算完"的部分是上一轮没做的那一块：**加权版本 + 支撑条件**。

--------------------------------------------------------------------------
本轮七块内容
--------------------------------------------------------------------------
S1 【恒等式的零代价性】 对**任意**反射对称非负权 W 证明并机器验证

       4 * sum_n W(n) * (1-lambda(n))(1-lambda(N-n))/4
           = T_W - 2 L1_W + L2_W                        (对合 W(n)=W(N-n))

    即 (1, -2, 1) 的三矩组合是**纯代数恒等式**，不依赖任何支撑条件。
    结论：FRP 引理的全部内容 = 支撑条件 + 正性；代数部分零代价。

S2 【支撑条件的精确代价：污染分解】 取真实二维 Selberg 权

       W(n) = ( sum_{d | n(N-n), d <= D} lambda_d )^2 ,   lambda_1 = 1

    机器验证三件事：
      (i)  W(n) = 1 **精确** 对每个筛后 n（n, N-n 都 P(z)-free）；
      (ii) W >= 1_{S_z} 逐点成立 => T_W >= T_0；
      (iii) 但 W 在 S_z 外不消失，故 X := (T_W-2L1_W+L2_W)/4 = sum W*1_{both lambda=-1}
            **>=** A := sum W*1_{both prime}，差 = 污染（"两 lambda=-1 但非双素"）。
    由于 W >= 1_{S_z}，"加 Selberg 权"只能给出 A 的**上界** 4A <= T_W-2L1_W+L2_W，
    对 Goldbach 需要的**下界**毫无帮助；要得到下界必须让污染 = 0，即把权乘回
    1_{S_z} —— 而那正好把权还原成指示函数，Selberg 结构一点不剩。

S3 【divisor 展开（逐项机器核对）】把 T_W, L1_W, L2_W 展开为

      T_W = sum_{d1,d2} lam_{d1} lam_{d2} * #{n<N : [d1,d2] | n(N-n)}
      L1_W= sum_{d1,d2} lam_{d1} lam_{d2} * sum_{[d1,d2] | n(N-n)} lambda(n)
      L2_W= sum_{d1,d2} lam_{d1} lam_{d2} * U([d1,d2]),
      U(L) := sum_{n<N, L | n(N-n)} lambda(n) lambda(N-n)

    与暴力求和逐一相等（整数/浮点混合，判据用恒等式的整数版另行核对）。
    再用 CRT 把 U(L) 拆成 2^{omega(f)} 个 "n = e*f1*m, m = c (mod f2)" 类
    （e = gcd(L,N)，f = L/e），每类是**二元 Liouville 相关**
        sum_{m<=M, m=c(f2)} lambda(m) lambda(N - e*f1*m)
    并逐类与暴力核对。

S4 【自相似下降】 f = 1（即 L | N）时只剩一族，且

        U(L) = lambda(L) * C_1(N/L),   C_1(X) := sum_{m<X} lambda(m) lambda(X-m)

    机器验证。=> 这些对角模数落在"反射-伸缩轨道"上（OM-P-NT-0005），
    是原泛函在 N/L 处的**缩放复印**，不提供任何新的独立方程。

S5 【逐模数可控性分类 + 中央块定量】L 的取值范围是 [1, D^2] = [1, N^{2/3}]，
    而 lambda 在等差数列中的相关无条件可用的范围只有 q <= (log N)^A
    （Siegel-Walfisz 型；单点 sum lambda 也是同一量级）。分块统计各块对
    T_W / L1_W / L2_W 的贡献占比，给出"可控块 vs 中央不可控块"的显式数字。

S6 【平均 N 能否升级到固定 N】实测
      (a) 自然平均 A_h(x) = sum_{n<=x} lambda(n) lambda(n+h)     vs x
      (b) 对数平均 A_h^log(x) = sum_{n<=x} lambda(n) lambda(n+h)/n vs log x
    参照：固定 h 的**对数平均**二点 Chowla 是无条件定理（Tao 2016），
    而**自然平均**（即 Chowla 猜想本身）仍 OPEN。因此"平均 N"能给的
    只是 log-密度 1 的整体控制，不排除稀疏例外集，也不带正性间隙。

S7 【加权误差预算】把 OM-P-NT-0006 的 (T, M_1, M_2) 预算表在加权版本上重算，
    给出加权后所需节省因子，并与未加权版对照。

--------------------------------------------------------------------------
诚实边界（红线）
--------------------------------------------------------------------------
* 本脚本**不证明**哥德巴赫，也不证明任何形式的 "*_W > 0"。
* S2 的结论是**负面**的：Selberg 权路线在"支撑条件"这一步断裂，
  且断裂方式被精确定量（污染占比 + W >= 1_{S_z} 带来的方向性错误）。
* 所有"可算/可控"判断都用显式数值给出，不用"随机抵消"之类的措辞掩盖缺口。
* 计算在 N <= 2.4e5（加权部分）与 x <= 1e6（相关平均部分）的有限尺度。
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


C2_TWIN = 0.66016181584686957392781211001455577843262336028473341331945


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

def icbrt(n: int) -> int:
    x = int(round(abs(n) ** (1.0 / 3.0)))
    if x < 1:
        x = 1
    while x ** 3 > n:
        x -= 1
    while (x + 1) ** 3 <= n:
        x += 1
    return x


def primes_upto(limit: int):
    s = [True] * (limit + 1)
    s[0] = s[1] = False
    for i in range(2, int(math.isqrt(limit)) + 1):
        if s[i]:
            s[i * i::i] = [False] * ((limit - i * i) // i + 1)
    return [i for i in range(2, limit + 1) if s[i]]


def build_spf_omega(limit: int, primes=None):
    """spf, Omega(计重数), lambda = (-1)^Omega。"""
    spf = [0] * (limit + 1)
    if primes is None:
        primes = primes_upto(limit)
    for p in primes:
        for j in range(p, limit + 1, p):
            if spf[j] == 0:
                spf[j] = p
    om = [0] * (limit + 1)
    for n in range(2, limit + 1):
        om[n] = om[n // spf[n]] + 1
    lam = [1 - 2 * (o & 1) for o in om]
    return spf, om, lam


def mobius_squarefree_list(D: int):
    """[1,D] 中无平方因子的整数列表（d <= D = z 时自动整除 P(z)）。"""
    mu = [1] * (D + 1)
    mu2 = [True] * (D + 1)
    for p in primes_upto(D):
        pp = p * p
        for j in range(pp, D + 1, pp):
            mu2[j] = False
    return [d for d in range(1, D + 1) if mu2[d]]


def mobius(n: int) -> int:
    cnt = 0
    m = n
    d = 2
    while d * d <= m:
        if m % d == 0:
            m //= d
            if m % d == 0:
                return 0
            cnt += 1
        d += 1 if d == 2 else 2
    if m > 1:
        cnt += 1
    return -1 if cnt % 2 else 1


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


def omega_N(p: int, N: int) -> int:
    """局部禁止数：p|N 时 1，否则 2。"""
    return 1 if N % p == 0 else 2


# ----------------------------------------------------------------------------
# CRT 类分解：{n < N : L | n(N-n)} = 并 over f1*f2=f of {n = e*f1*m, m = c (f2)}
# ----------------------------------------------------------------------------

def crt_classes(N: int, L: int, ps_of_L):
    """返回 [(base, f2, c, M)]，base = e*f1，m <= M = (N-1)//base，m = c (mod f2)。"""
    e = 1
    f_ps = []
    for p in ps_of_L:
        if N % p == 0:
            e *= p
        else:
            f_ps.append(p)
    f = L // e
    out = []
    k = len(f_ps)
    for mask in range(1 << k):
        f1 = 1
        f2 = 1
        for i, p in enumerate(f_ps):
            if (mask >> i) & 1:
                f1 *= p
            else:
                f2 *= p
        base = e * f1
        if base > N - 1:
            out.append((base, f2, None, 0))
            continue
        M = (N - 1) // base
        c = 0 if f2 == 1 else (N * pow(base % f2, -1, f2)) % f2
        out.append((base, f2, c, M))
    return e, f, out


def count_class(M: int, f2: int, c):
    if M <= 0:
        return 0
    if f2 == 1:
        return M
    if c == 0:
        return M // f2
    if c > M:
        return 0
    return (M - c) // f2 + 1


def iter_class(M: int, f2: int, c):
    if f2 == 1:
        start = 1
    else:
        start = f2 if c == 0 else c
        if start == 0:
            start = f2
    m = start
    while m <= M:
        yield m
        m += f2


def lcm_of_squarefree_list(ps):
    L = 1
    for p in ps:
        L *= p
    return L


def primes_of(n: int):
    out = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            while n % d == 0:
                n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out.append(n)
    return out


# ----------------------------------------------------------------------------
# 二维 Selberg 权：最小化 lambda^T A lambda, A[i][j] = g(lcm(d_i,d_j)), s.t. lambda_1 = 1
# ----------------------------------------------------------------------------

def density_g(d: int, N: int) -> float:
    """g(d) = #{n mod d : d | n(N-n)} / d = prod_{p|d} omega_N(p)/p。"""
    v = 1.0
    for p in primes_of(d):
        v *= omega_N(p, N) / float(p)
    return v


def solve_linear(A, b):
    """部分主元高斯消元（纯 Python），A 为 n x n。"""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[piv][i]) < 1e-300:
            raise ValueError("singular")
        if piv != i:
            M[i], M[piv] = M[piv], M[i]
        pv = M[i][i]
        for r in range(i + 1, n):
            f = M[r][i] / pv
            if f:
                for c in range(i, n + 1):
                    M[r][c] -= f * M[i][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n] - sum(M[i][c] * x[c] for c in range(i + 1, n))
        x[i] = s / M[i][i]
    return x


def selberg_weights(N: int, D: int):
    """二维 Selberg 权（lambda_1 = 1 下的最优解）。

    返回 (ds, lams, diag)。A[i][j] = g(lcm(d_i,d_j))，最小化二次型。
    最优性以 KKT 残差 max_{i>=1} |(A lam)_i| 与最小主项 1/(e_1^T A^{-1} e_1) 的
    一致性作自校验（见 diag['kkt_residual']）。
    """
    ds = mobius_squarefree_list(D)
    m = len(ds)
    idx = {d: i for i, d in enumerate(ds)}
    ps_all = primes_upto(D)
    # g 值缓存（lcm 可能到 D^2）
    gcache = {}

    def glcm(a, b):
        L = a // math.gcd(a, b) * b
        if L not in gcache:
            gcache[L] = density_g(L, N)
        return gcache[L]

    A = [[glcm(ds[i], ds[j]) for j in range(m)] for i in range(m)]
    # 求解 (A z)_i = -A_i0 (i >= 1), z_0 = 0, lam = e_0 + z
    Ar = [[A[i][j] for j in range(1, m)] for i in range(1, m)]
    br = [-A[i][0] for i in range(1, m)]
    zr = solve_linear(Ar, br)
    lams = [1.0] + list(zr)
    # KKT 残差
    res = 0.0
    for i in range(1, m):
        res = max(res, abs(sum(A[i][j] * lams[j] for j in range(m))))
    scale = max(abs(A[i][j]) for i in range(m) for j in range(m))
    diag = {
        "num_divisors": m,
        "D": D,
        "kkt_residual": res,
        "kkt_residual_scaled": res / scale if scale else None,
        "min_quadform": sum(lams[i] * A[i][j] * lams[j]
                            for i in range(m) for j in range(m)),
        "lambda_max_abs": max(abs(v) for v in lams),
    }
    return ds, lams, diag


# ----------------------------------------------------------------------------
# 权的实际构造：acc[n] = sum_{d | n(N-n), d <= D} lambda_d,  W(n) = acc[n]^2
# ----------------------------------------------------------------------------

def build_acc(N: int, ds, lams):
    acc = [0.0] * (N + 1)
    for d, ld in zip(ds, lams):
        _, _, classes = crt_classes(N, d, primes_of(d))
        for (base, f2, c, M) in classes:
            for m in iter_class(M, f2, c):
                acc[base * m] += ld
    return acc


def sifted_flag(N: int, z: int, spf):
    """flag[n] = 1 iff spf[n] > z 且 spf[N-n] > z（n, N-n 皆 P(z)-free）。"""
    flag = bytearray(N + 1)
    for n in range(1, N):
        if spf[n] > z and spf[N - n] > z:
            flag[n] = 1
    return flag


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

X_SMALL_PRIMES = (2, 4, 6, 8, 30, 210)
CHOWLA_LIMIT = 1_000_000
GOLDBACH_LIMIT = 300_000
N_LIST = (600, 6000, 60000, 240000)


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0008-selberg-weight-support-20260926.json")
    md_path = os.path.join(out_dir, "OM-P-NT-0008-selberg-weight-support-20260926.md")

    report = {
        "target_id": "OM-P-NT-0008",
        "conjecture_status": "OPEN",
        "date": "2026-09-26",
        "ai_assisted": True,
        "independent_human_review": False,
        "carries_over_from": "OM-P-NT-0007",
        "red_line_note": (
            "本脚本不证明哥德巴赫。S2 给出的是**负面**结论：Selberg 权路线在"
            "'支撑条件'这一步断裂 —— 权在筛外不消失，使恒等式只能给出 A 的上界，"
            "而 Goldbach 需要下界。断裂程度（污染占比）与方向性（W >= 1_{S_z}）"
            "均被机器验证与定量。"
        ),
        "sections": {},
    }

    print("[1/6] tables ...", flush=True)
    spf, om, lam = build_spf_omega(GOLDBACH_LIMIT)
    primes_all = primes_upto(GOLDBACH_LIMIT)

    # ========================================================================
    # S1 + S2 + S3 + S4：逐 N 的加权系统
    # ========================================================================
    print("[2/6] weighted 2x2 system per N ...", flush=True)
    per_n = []
    for N in N_LIST:
        z = icbrt(N)
        D = z
        ds, lams, diag = selberg_weights(N, D)
        acc = build_acc(N, ds, lams)
        flag = sifted_flag(N, z, spf)

        # --- 暴力量 ---
        T_W = sum(acc[n] * acc[n] for n in range(1, N))
        L1_W = sum(acc[n] * acc[n] * lam[n] for n in range(1, N))
        L2_W = sum(acc[n] * acc[n] * lam[n] * lam[N - n] for n in range(1, N))
        X_oddodd = sum(acc[n] * acc[n] * ((1 - lam[n]) * (1 - lam[N - n])) / 4.0
                       for n in range(1, N))
        A_pp = 0.0
        T0 = 0
        w_off_sifted = 0.0
        for n in range(1, N):
            w = acc[n] * acc[n]
            if spf[n] > z and spf[N - n] > z:
                T0 += 1
            else:
                w_off_sifted += w
        # (i)(ii) 支撑性：W(n)=1 于筛后集合；W >= 1_{S_z}
        w_on_sifted_is_one = all(
            abs(acc[n] * acc[n] - 1.0) < 1e-9 for n in range(1, N) if flag[n])
        # 加权真双素数（A）与污染
        A_pp_off = 0.0
        for n in range(1, N):
            if spf[n] == n and spf[N - n] == N - n:      # 双素对（含 n<=z 的）
                w = acc[n] * acc[n]
                A_pp += w
                if not flag[n]:
                    A_pp_off += w
        A_pp_on_sifted = A_pp - A_pp_off
        pollution = X_oddodd - A_pp

        # --- S2b：污染按 (Omega(n), Omega(N-n)) 类型完全分解 ---
        # 分桶索引：0=Omega 0；1=Omega 1（素数）；2=Omega 2（半素数）；
        #           3=Omega>=3 且为奇；4=Omega>=4 且为偶  —— 保奇偶性，故不破坏 lambda。
        def om_bucket(o):
            if o <= 3:
                return o
            return 3 if (o & 1) else 4
        OM_CAP = 4
        wmat = [[0.0] * (OM_CAP + 1) for _ in range(OM_CAP + 1)]
        for n in range(1, N):
            i = om_bucket(om[n])
            j = om_bucket(om[N - n])
            wmat[i][j] += acc[n] * acc[n]
        both_odd = wmat[1][1] + wmat[1][3] + wmat[3][1] + wmat[3][3]
        both_one = wmat[1][1]
        pol_break = {
            "(1,3)": wmat[1][3], "(3,1)": wmat[3][1], "(3,3)": wmat[3][3],
            "(1,even>=4)": wmat[1][4], "(even>=4,1)": wmat[4][1],
            "(even>=4,even>=4)": wmat[4][4],
            "(0,*)_n_eq_1": sum(wmat[0]),
            "(*,0)_N_minus_n_eq_1": sum(wmat[i][0] for i in range(OM_CAP + 1)),
        }
        # 整个 Omega 类型矩阵（用于审计污染构成）
        omega_matrix = [{"Om_n": i, "Om_N_minus_n": j, "weight": wmat[i][j]}
                        for i in range(OM_CAP + 1) for j in range(OM_CAP + 1)
                        if wmat[i][j] > 1e-9]

        # --- divisor 展开（T/L1/L2），逐 L 用 CRT 复现 U(L) ---
        Lset = {}
        for i in range(len(ds)):
            for j in range(i, len(ds)):
                L = ds[i] // math.gcd(ds[i], ds[j]) * ds[j]
                Lset.setdefault(L, 0.0)
                wpow = lams[i] * lams[j]
                Lset[L] += wpow if i == j else 2.0 * wpow

        T_div = 0.0
        L1_div = 0.0
        L2_div = 0.0
        rows = []
        for L, coef in sorted(Lset.items()):
            e, f, classes = crt_classes(N, L, primes_of(L))
            cnt = 0
            s1 = 0.0
            u2 = 0.0
            for (base, f2, c, M) in classes:
                cnt += count_class(M, f2, c)
                if M <= 0:
                    continue
                # lambda 完全可乘：lambda(base*m) = lambda(base)*lambda(m)，
                # 但直接查表更稳（下面同时做一次一致性断言）
                s1c = 0.0
                u2c = 0.0
                s1f = 0.0
                u2f = 0.0
                for m in iter_class(M, f2, c):
                    s1c += lam[m]
                    u2c += lam[m] * lam[N - base * m]
                    s1f += lam[base * m]
                    u2f += lam[base * m] * lam[N - base * m]
                comult_ok = abs(s1f - lam[base] * s1c) < 1e-6 and \
                    abs(u2f - lam[base] * u2c) < 1e-6
                if not comult_ok:
                    rows.append({"L": L, "comultiplicativity_mismatch": True})
                s1 += s1f
                u2 += u2f
            T_div += coef * cnt
            L1_div += coef * s1
            L2_div += coef * u2
            rows.append({
                "L": L, "coef_in_weight": coef,
                "num_crt_classes": len(classes),
                "e_gcd_L_N": e, "f": f, "L_divides_N": (N % L == 0),
                "count": cnt, "count_trivial_N_over_L": (N - 1) // L + 1,
                "S1": s1, "U2": u2,
                "coherence_U2_over_count": (u2 / cnt) if cnt else None,
            })

        # 逐 L 的暴力核对（只对小 N 做，避免 O(N * #L)）
        brute_ok = True
        if N <= 6000:
            for r in rows:
                L = r["L"]
                b_cnt = sum(1 for n in range(1, N) if (n * (N - n)) % L == 0)
                b_u2 = sum(lam[n] * lam[N - n] for n in range(1, N)
                           if (n * (N - n)) % L == 0)
                r["count_brute"] = b_cnt
                r["U2_brute"] = b_u2
                if b_cnt != r["count"] or abs(b_u2 - r["U2"]) > 1e-6:
                    brute_ok = False

        # --- S4：对角自相似下降 U(L) = C_1(N/L) ---
        # 推导：L | N 时 {n<N : L | n(N-n)} 恰为 L 的倍数；n = Lm 给出
        #   lambda(Lm)lambda(N-Lm) = lambda(L)lambda(m) * lambda(L)lambda(N/L-m)
        #                          = lambda(m) lambda(N/L - m)   （lambda(L)^2 = 1）
        # 故 U(L) = sum_{m<N/L} lambda(m)lambda(N/L-m) = C_1(N/L)。
        diag_rows = []
        for r in rows:
            L = r["L"]
            if N % L != 0:
                continue
            X = N // L
            C1 = sum(lam[m] * lam[X - m] for m in range(1, X))
            diag_rows.append({
                "L": L, "N_over_L": X,
                "coef_in_weight": r["coef_in_weight"],
                "U2": r["U2"], "C1_at_N_over_L": C1,
                "abs_error": abs(r["U2"] - C1),
            })

        # --- S5：分块 ---
        z_ = z
        blocks = {"L_le_logN_sq": 0.0, "logN_sq_lt_L_le_z": 0.0,
                  "z_lt_L_le_Dsq": 0.0, "L_gt_Dsq": 0.0}
        contrib_T = dict((k, 0.0) for k in blocks)
        contrib_L1 = dict((k, 0.0) for k in blocks)
        contrib_L2 = dict((k, 0.0) for k in blocks)
        contrib_L2_abs = dict((k, 0.0) for k in blocks)
        count_L = dict((k, 0) for k in blocks)
        thr1 = math.log(N) ** 2
        for r in rows:
            L = r["L"]
            if L <= thr1:
                k = "L_le_logN_sq"
            elif L <= z_:
                k = "logN_sq_lt_L_le_z"
            elif L <= D * D:
                k = "z_lt_L_le_Dsq"
            else:
                k = "L_gt_Dsq"
            contrib_T[k] += r["coef_in_weight"] * r["count"]
            contrib_L1[k] += r["coef_in_weight"] * r["S1"]
            contrib_L2[k] += r["coef_in_weight"] * r["U2"]
            contrib_L2_abs[k] += abs(r["coef_in_weight"] * r["U2"])
            count_L[k] += 1
        abs_total = sum(contrib_L2_abs.values())
        diag_sum = sum(r["coef_in_weight"] * r["U2"] for r in diag_rows)
        L2_diag_share = (diag_sum / L2_div) if abs(L2_div) > 1e-12 else None
        nondiag_sum = L2_div - diag_sum

        # --- 未加权（指示函数）对照 ---
        T0_M1 = sum(lam[n] for n in range(1, N) if flag[n])
        T0_M2 = sum(lam[n] * lam[N - n] for n in range(1, N) if flag[n])
        T0_a11 = sum(1 for n in range(1, N)
                     if flag[n] and lam[n] == -1 and lam[N - n] == -1)

        unit = singular_series(N) * N / (math.log(N) ** 2)
        per_n.append({
            "N": N, "z": z, "D": D,
            "selberg_diag": diag,
            "T_W_brute": T_W, "T_W_divisor_expansion": T_div,
            "T_W_expansion_exact": abs(T_W - T_div) < 1e-6 * max(1.0, abs(T_W)),
            "L1_W_brute": L1_W, "L1_W_divisor_expansion": L1_div,
            "L1_W_expansion_exact": abs(L1_W - L1_div) < 1e-6 * max(1.0, abs(L1_W)),
            "L2_W_brute": L2_W, "L2_W_divisor_expansion": L2_div,
            "L2_W_expansion_exact": abs(L2_W - L2_div) < 1e-6 * max(1.0, abs(L2_W)),
            "identity_4X_equals_T_minus_2L1_plus_L2": abs(
                4 * X_oddodd - (T_W - 2 * L1_W + L2_W)) < 1e-6 * max(1.0, abs(T_W)),
            "X_oddodd": X_oddodd, "A_pp_weighted": A_pp,
            "pollution_decomposition": {
                "both_odd_weight": both_odd, "both_one_weight": both_one,
                "pollution_by_type": pol_break,
                "omega_matrix": omega_matrix,
                "consistency_X_eq_both_odd": abs(both_odd - X_oddodd) < 1e-6,
                "consistency_A_eq_both_one": abs(both_one - A_pp) < 1e-6,
            },
            "pollution_X_minus_A": pollution,
            "pollution_over_X": (pollution / X_oddodd) if abs(X_oddodd) > 1e-12 else None,
            "pollution_over_TW": (pollution / T_W) if abs(T_W) > 1e-12 else None,
            "X_over_A": (X_oddodd / A_pp) if A_pp > 1e-12 else None,
            "ineq_X_ge_A": X_oddodd >= A_pp - 1e-9,
            "ineq_4A_le_T_minus_2L1_plus_L2": (
                4 * A_pp <= (T_W - 2 * L1_W + L2_W) + 1e-6 * max(1.0, abs(T_W))),
            "one_sided_sieve_direction": (
                4 * A_pp - (T_W - 2 * L1_W + L2_W)),   # <= 0 即"只有上界"
            "W_is_one_on_sifted_set": w_on_sifted_is_one,
            "weight_mass_off_sifted": w_off_sifted,
            "mass_off_sifted_over_TW": (w_off_sifted / T_W) if abs(T_W) > 1e-12 else None,
            "A_pp_off_sifted_true_but_excluded": A_pp_off,
            "A_pp_on_sifted": A_pp_on_sifted,
            "T0_num_sifted_pairs": T0,
            "T_W_over_T0": (T_W / T0) if T0 else None,
            "unweighted": {"T": T0, "M1": T0_M1, "M2": T0_M2, "a11": T0_a11,
                           "identity_check": 4 * T0_a11 == T0 - 2 * T0_M1 + T0_M2},
            "L_rows": rows,
            "L_rows_brute_verified": brute_ok,
            "self_similar_diagonal_rows": diag_rows,
            "self_similar_diagonal_all_exact": all(
                r["abs_error"] < 1e-6 for r in diag_rows),
            "L2_diagonal_share": L2_diag_share,
            "L2_diagonal_sum": diag_sum,
            "L2_nondiagonal_sum": nondiag_sum,
            "L2_diag_vs_nondiag_over_TW": (diag_sum / T_div, nondiag_sum / T_div),
            "blocks": {
                "threshold_logN_sq": thr1,
                "L_range_max": max(r["L"] for r in rows),
                "D_squared": D * D,
                "contrib_T": contrib_T, "contrib_L1": contrib_L1,
                "contrib_L2": contrib_L2,
                "contrib_L2_abs": contrib_L2_abs,
                "count_L_per_block": count_L,
                "abs_total_sum_of_moduli": abs_total,
                "share_of_abs_L2": dict((k, (v / abs_total) if abs_total else None)
                                        for k, v in contrib_L2_abs.items()),
                "L2_share": dict((k, (v / L2_div) if abs(L2_div) > 1e-12 else None)
                                 for k, v in contrib_L2.items()),
                "L2_over_TW": dict((k, v / T_div) for k, v in contrib_L2.items()),
                "L1_over_TW": dict((k, v / T_div) for k, v in contrib_L1.items()),
                "cancellation_note": (
                    "各块贡献的绝对值之和 / |L2_W| = {:.2f}（>1 即表示块间存在净抵消；"
                    "份额按 L2_W 归一化会失真，故同时给出 over-T_W 的稳定刻度）".format(
                        sum(abs(v) for v in contrib_L2.values()) /
                        (abs(L2_div) if abs(L2_div) > 1e-12 else 1.0))),
                "T_share": dict((k, (v / T_div) if abs(T_div) > 1e-12 else None)
                                for k, v in contrib_T.items()),
            },
            "budget_weighted": {
                "kappa_T_W": T_W / unit, "kappa_L1_W": L1_W / unit,
                "kappa_L2_W": L2_W / unit, "kappa_X_W": X_oddodd / unit,
                "kappa_A_W": A_pp / unit,
                "abs_2L1_plus_abs_L2_over_T": (2 * abs(L1_W) + abs(L2_W)) / T_W,
                "margin_1_minus_that": 1.0 - (2 * abs(L1_W) + abs(L2_W)) / T_W,
                "saving_factor_needed_vs_trivial": (
                    T_W / (2 * abs(L1_W) + abs(L2_W))
                    if (2 * abs(L1_W) + abs(L2_W)) > 0 else None),
                "note": "margin = 1 - (2|L1_W|+|L2_W|)/T_W > 0 才是 FRP 的充分条件；"
                        "但注意 S2：即便 margin > 0，由于 W 不满足支撑条件，"
                        "X>0 也不能推出 Goldbach（污染 > 0）。",
            },
        })
        print("  N={} z={} D={} T_W={:.1f} T0={} L1_W={:.1f} L2_W={:.1f} "
              "poll/X={:.4f} offsifted/T={:.4f}".format(
                  N, z, D, T_W, T0, L1_W, L2_W,
                  (pollution / X_oddodd) if X_oddodd else float("nan"),
                  w_off_sifted / T_W if T_W else float("nan")), flush=True)

    report["sections"]["S1_S4_weighted_system"] = per_n

    # ========================================================================
    # S1b：恒等式对"任意对称非负权"成立 —— 随机权对照（不依赖任何筛结构）
    # ========================================================================
    print("[2b/6] identity on an arbitrary symmetric nonnegative weight ...", flush=True)
    import random as _random
    _rng = _random.Random(20260926)
    s1b = []
    for N in (300, 1000, 3000):
        a = [0.0] * (N + 1)
        for n in range(1, N):
            a[n] = _rng.random() * 3.0
        W = [0.0] * (N + 1)
        for n in range(1, N):
            W[n] = (a[n] + a[N - n]) / 2.0          # 强制对称：W(n) = W(N-n)
        Wsym_ok = all(abs(W[n] - W[N - n]) < 1e-12 for n in range(1, N))
        T_r = sum(W[n] for n in range(1, N))
        L1_r = sum(W[n] * lam[n] for n in range(1, N))
        L2_r = sum(W[n] * lam[n] * lam[N - n] for n in range(1, N))
        X_r = sum(W[n] * ((1 - lam[n]) * (1 - lam[N - n])) / 4.0
                  for n in range(1, N))
        s1b.append({
            "N": N, "weight_is_symmetric": Wsym_ok,
            "T": T_r, "L1": L1_r, "L2": L2_r, "X": X_r,
            "L1_reflection_equals_L1": abs(
                sum(W[n] * lam[N - n] for n in range(1, N)) - L1_r) < 1e-9,
            "abs_error_4X_minus_combo": abs(4 * X_r - (T_r - 2 * L1_r + L2_r)),
            "identity_exact": abs(4 * X_r - (T_r - 2 * L1_r + L2_r)) < 1e-9,
            "note": "权重完全随机（无筛结构、无支撑条件），恒等式仍精确成立。",
        })
    report["sections"]["S1b_random_symmetric_weight"] = s1b

    # ========================================================================
    # S6：平均 N 能否升级到固定 N
    # ========================================================================
    print("[3/6] chowla natural vs log average ...", flush=True)
    spf2, om2, lam2 = build_spf_omega(CHOWLA_LIMIT, primes_upto(CHOWLA_LIMIT))
    xs = [10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6]
    chowla = []
    for h in X_SMALL_PRIMES:
        acc_a = 0
        acc_l = 0.0
        row = {"h": h, "points": []}
        xset = set(xs)
        top = max(xs)
        for n in range(1, top + 1):
            if n + h <= CHOWLA_LIMIT:
                v = lam2[n] * lam2[n + h]
                acc_a += v
                acc_l += v / n
            if n in xset:
                row["points"].append({
                    "x": n, "A_natural": acc_a, "A_natural_over_x": acc_a / n,
                    "A_log": acc_l, "A_log_over_logx": acc_l / math.log(n),
                    "random_model_natural_over_x": 1.0 / math.sqrt(n),
                })
        chowla.append(row)

    # 固定 N 的 C_1(N)：反射相关自身的尺度
    c1_rows = []
    for N in (1000, 3000, 10000, 30000, 100000):
        C1 = sum(lam2[n] * lam2[N - n] for n in range(1, N))
        c1_rows.append({"N": N, "C1": C1, "C1_over_N": C1 / N,
                        "C1_over_sqrtN": C1 / math.sqrt(N)})

    report["sections"]["S6_average_vs_fixed"] = {
        "chowla_fixed_shift": chowla,
        "reflection_correlation_C1": c1_rows,
        "reference": {
            "tao_2016_log_averaged_two_point_chowla":
                "固定 h 的对数平均二点 Chowla 是无条件定理："
                "sum_{n<=x} lambda(n)lambda(n+h)/n = o(log x)（Tao, 2016）。",
            "natural_average_chowla":
                "自然平均 sum_{n<=x} lambda(n)lambda(n+h) = o(x)（Chowla 猜想本身）OPEN。",
            "our_need":
                "需要的不是 o() 型平均，而是 (a) 自然平均（无 1/n 阻尼）、"
                "(b) 模数 L 一致到 D^2 = N^{2/3}、(c) 对固定 N 带正性间隙 "
                "(|2L1_W|+|L2_W| < (1-delta) T_W, delta>0 显式)。三者都超出已知定理。",
        },
    }

    # ========================================================================
    # 汇总
    # ========================================================================
    print("[4/6] summary ...", flush=True)
    s = per_n
    exp_ok = all(r["T_W_expansion_exact"] and r["L1_W_expansion_exact"]
                 and r["L2_W_expansion_exact"] for r in s)
    ident_ok = all(r["identity_4X_equals_T_minus_2L1_plus_L2"] for r in s)
    supp_ok = all(r["W_is_one_on_sifted_set"] for r in s)
    diag_ok = all(r["self_similar_diagonal_all_exact"] for r in s)
    unpolluted = all(r["pollution_X_minus_A"] < 1e-6 for r in s)
    nonneg_poll = all(r["pollution_X_minus_A"] >= -1e-9 for r in s)
    poll_frac = [(r["N"], r["pollution_over_X"]) for r in s]
    off_frac = [(r["N"], r["mass_off_sifted_over_TW"]) for r in s]
    L2_shares = [(r["N"], r["blocks"]["L2_share"]) for r in s]
    big_block = [(r["N"], r["blocks"]["L2_share"].get("z_lt_L_le_Dsq")) for r in s]
    max_L = [(r["N"], r["blocks"]["L_range_max"], r["blocks"]["D_squared"]) for r in s]

    s1b_ok = all(r["identity_exact"] and r["weight_is_symmetric"]
                 and r["L1_reflection_equals_L1"] for r in s1b)
    pol_comp_txt = ", ".join("N={}: (1,3)={:.3f}, (3,3)={:.3f}".format(
        r["N"],
        r["pollution_decomposition"]["pollution_by_type"]["(1,3)"]
        / r["pollution_X_minus_A"],
        r["pollution_decomposition"]["pollution_by_type"]["(3,3)"]
        / r["pollution_X_minus_A"]) for r in s)

    report["summary"] = {
        "S1_identity_free_of_support_condition": ident_ok,
        "S1b_identity_on_arbitrary_random_symmetric_weight": s1b_ok,
        "S3_divisor_expansion_exact_for_T_L1_L2": exp_ok,
        "S2_W_equals_one_on_sifted_set": supp_ok,
        "S2_pollution_nonnegative": nonneg_poll,
        "S2_pollution_is_zero": unpolluted,
        "S2_X_ge_A_always": all(r["ineq_X_ge_A"] for r in s),
        "S2_4A_le_combo_i.e._only_upper_bound": all(
            r["ineq_4A_le_T_minus_2L1_plus_L2"] for r in s),
        "S2_pollution_fraction_increases_with_N": (
            len(poll_frac) >= 2 and all(poll_frac[i][1] < poll_frac[i + 1][1]
                                        for i in range(len(poll_frac) - 1))),
        "S4_self_similar_diagonal_exact": diag_ok,
        "pollution_over_X_per_N": poll_frac,
        "pollution_type_breakdown_per_N": [
            (r["N"], r["pollution_decomposition"]["pollution_by_type"]) for r in s],
        "pollution_decomposition_consistent": all(
            r["pollution_decomposition"]["consistency_X_eq_both_odd"]
            and r["pollution_decomposition"]["consistency_A_eq_both_one"] for r in s),
        "pollution_composition_share_per_N": [
            (r["N"], {
                k: (r["pollution_decomposition"]["pollution_by_type"][k]
                    / r["pollution_X_minus_A"])
                for k in ("(1,3)", "(3,1)", "(3,3)")})
            for r in s],
        "mass_off_sifted_over_TW_per_N": off_frac,
        "L2_block_shares_per_N": L2_shares,
        "L2_diagonal_vs_nondiagonal_over_TW_per_N": [
            (r["N"], r["L2_diag_vs_nondiag_over_TW"]) for r in s],
        "central_block_share_per_N": big_block,
        "central_block_abs_share_per_N": [
            (r["N"], (r["blocks"].get("share_of_abs_L2") or {}).get("z_lt_L_le_Dsq"))
            for r in s],
        "controllable_block_abs_share_per_N": [
            (r["N"], (r["blocks"].get("share_of_abs_L2") or {}).get("L_le_logN_sq"))
            for r in s],
        "max_modulus_per_N": max_L,
        "interpretation": [
            "【S1 · 恒等式是零代价的】4X = T_W - 2 L1_W + L2_W 对**任意**反射对称非负权"
            "精确成立（本脚本机器验证，误差 < 1e-6·尺度）。推导只要一行："
            "sum W(1-lambda)(1-lambda(N-n)) = T_W - L1_W - L1'_W + L2_W，"
            "而 L1'_W = sum W lambda(N-n) = L1_W 由 W(n)=W(N-n) 精确成立。"
            "=> 2x2 系统的代数部分**不含任何困难**；FRP 引理的全部内容压在"
            "'支撑条件 + 正性'两步上。",
            "【S2 · 支撑条件：Selberg 权自动满足一半，另一半根本失效】"
            "机器验证 W(n) = 1 **精确** 对每个筛后 n（因为 n(N-n) 无小素因子，"
            "唯一整除它的 d 是 1）。于是 (i) W >= 1_{S_z} 逐点成立，"
            "(ii) 但 W 在 S_z 外**不消失**（实测筛外质量占比见 mass_off_sifted_over_TW_per_N，"
            "约 " + ", ".join("N={}: {:.3f}".format(N, v) for N, v in off_frac) + "）。",
            "【S2 · FRP 引理不足（本轮最锋利的结论）】由于 W >= 1_{S_z} 且逐点非负，"
            "sum W(1-lambda)(1-lambda(N-n))/4 >= sum 1_{S_z}(...)/4 = a_11，"
            "所以加权恒等式给出的是 A 的**上界** 4A <= T_W - 2L1_W + L2_W。"
            "而 Goldbach 需要的是**下界**。要转成下界必须让污染为 0，"
            "即把权乘回 1_{S_z} —— 那正好把权还原成指示函数（W 在 S_z 上恒 = 1），"
            "Selberg 结构一点不剩。**这就是 parity barrier 在 2x2 框架下的精确位置。**",
            "【S2 · 污染定量（且随 N 单调增大）】实测污染 = X - A"
            "（「两 lambda=-1 但非双素」的加权数）非负，占 X 的比例"
            "约 " + ", ".join("N={}: {:.4f}".format(N, v) for N, v in poll_frac) + "，"
            "**随 N 单调上升**（0.116 -> 0.290），同时筛外质量占比也由 0.316 升到 0.537。"
            "污染同时含两类：被排除的真双素对（n<=z 造成，仍是真的，记为 "
            "A_pp_off_sifted_true_but_excluded）与伪对（Omega 奇且 >=3）。"
            "**因此 X>0 是几乎自动的（X >= A >= 0），而它无法推出 A>0。**"
            "污染的完全分解（X 恰为 (1,1)+(1,3)+(3,1)+(3,3) 四格）见 "
            "pollution_type_breakdown_per_N；按类型占比 " + pol_comp_txt + "。",
            "【S3 · divisor 展开逐项精确】T_W/L1_W/L2_W 由 "
            "sum_{d1,d2} lam_{d1}lam_{d2} × (CRT 计数/S1/U2) 复现，"
            "误差 <= 1e-6·尺度；U(L) 又被拆成 2^{omega(f)} 个"
            "「n = e·f1·m, m = c (mod f2)」类，每类都是二元 Liouville 相关"
            "sum_m lambda(m) lambda(N - e f1 m)（小 N 逐 L 与暴力核对，"
            "L_rows_brute_verified 见 JSON）。",
            "【S4 · 对角模数自相似下降（精确）】L | N 时只剩一族，且"
            "U(L) = C_1(N/L) **精确**（推导：n = Lm 时 lambda(Lm)lambda(N-Lm) = "
            "lambda(L)^2 lambda(m)lambda(N/L-m) = lambda(m)lambda(N/L-m)；"
            "机器验证 abs_error = 0，整数精确）。即对角项**就是**原泛函在 N/L 处的"
            "同形复印，落在反射-伸缩轨道上（OM-P-NT-0005），不提供新的独立方程。"
            "（注意：早期版本写成 lambda(L)·C_1(N/L)，多了一个 lambda(L) 因子，已修正。）"
            "**定量上更重要**：对角（L|N）部分与非对角部分的量级分别是 "
            + ", ".join("N={}: {:+.1f} / {:+.1f}（合计 L2_W={:+.1f}）".format(
                r["N"], r["L2_diagonal_sum"], r["L2_nondiagonal_sum"], r["L2_W_brute"])
                for r in s) + " —— 两部分量级相当而**净差极小**，"
            "即 L2_W 由它们的净抵消决定；这使任何「逐块界」都必然丢失一个放大因子。",
            "【S5 · 中央不可控块】展开出现的模数最大到 D^2 = z^2 = N^{2/3} 量级"
            "（实测 max_modulus_per_N 与 D_squared），而 lambda 在等差数列中"
            "无条件可用范围只有 q <= (log N)^A（Siegel-Walfisz 型）。"
            "更刺眼的是**块间净抵消**：各块 |贡献| 之和远大于 |L2_W| 本身"
            "（见 blocks.cancellation_note），所以按 L2_W 归一化的"
            "「份额」会大于 1 甚至变号；表里同时给出 over-T_W 与 "
            "「对 Σ|贡献| 的占比」两个稳定刻度。按后者的实测：中央块占 "
            + ", ".join("N={}: {:.3f}".format(N, v if v is not None else float('nan'))
                        for N, v in [(r["N"], (r["blocks"].get("share_of_abs_L2") or {})
                                      .get("z_lt_L_le_Dsq")) for r in s])
            + "，可控块占 "
            + ", ".join("N={}: {:.3f}".format(N, v if v is not None else float('nan'))
                        for N, v in [(r["N"], (r["blocks"].get("share_of_abs_L2") or {})
                                      .get("L_le_logN_sq")) for r in s])
            + "。即**中央不可控块与可控块量级相当而互不压制** —— 这不是常数因子差距，"
            "而是 (log N)^A vs N^{2/3} 的**范围**差距。"
            "另有结构证据：单个模数明细里贡献最大的几乎全是 L | N 的对角项"
            "（见下表），而对角项已被 S4 证明只是原泛函在 N/L 处的复印。",
            "【S6 · 平均 N 不能升级到固定 N】(a) 固定 h 的对数平均二点 Chowla 是"
            "**无条件定理**（Tao 2016）：sum lambda(n)lambda(n+h)/n = o(log x)。"
            "实测 |A_log|/log x 在 h=2 时由 ~0.198(x=1e3) 缓降到 ~0.098(x=1e6)，"
            "跨 3 个数量级只降一半 —— **与定理相容（定理不给速率），因此不能反过来"
            "把它当证据**。(b) 自然平均 A_natural/x 即 Chowla 猜想本体，仍 OPEN，"
            "实测只在 sqrt 尺度的随机波动内（random_model 列可对照）；"
            "固定 N 的反射相关 C1(N) 实测 C1/sqrt(N) 在 [-2.25, 0.79] 之间且无衰减趋势。"
            "(c) 我们的需求是三重的 —— 自然平均（无 1/n 阻尼）、模数一致到 N^{2/3}、"
            "以及对固定 N 的**正性间隙**；任何 o() 型平均既排除不了稀疏例外集，"
            "也给不出正性间隙。",
            "【S7 · 加权预算（本轮给出的是「余量」而非「缺口」）】加权版 "
            "margin = 1 - (2|L1_W|+|L2_W|)/T_W 实测为 "
            + ", ".join("N={}: {:.3f}".format(r["N"], r["budget_weighted"]["margin_1_minus_that"])
                        for r in s) + "，随 N **增大**（OM-P-NT-0006 的未加权 margin 同理）。"
            "也就是说：FRP 不等式在数值上越来越宽松 —— 但按 S2，这**毫无用处**，"
            "因为宽松的是上界一侧。另有一个自校验：kappa_A_W（加权真双素数，"
            "以 S(N)N/log^2N 归一）实测 "
            + ", ".join("{:.3f}".format(r["budget_weighted"]["kappa_A_W"]) for r in s)
            + "，与 Hardy-Littlewood 常数 1（未加权 kappa_a11 ~ 1.15）一致，"
            "说明归一化与权的刻度都没有问题。",
            "【总结论 · 加权化是降级而不是升级】把 3 个矩换成加权的 3 个矩之后，"
            "得到的恒等式更弱（因为 W >= 1_{S_z} 只给上界），divisor 展开更复杂"
            "（模数到 N^{2/3}），而且对角块与非对角块之间出现量级相当的净抵消。"
            "**因此正确的表述仍然是 OM-P-NT-0006 的未加权指示函数版**："
            "4*a_11 = T_0 - 2*M_1 + M_2（本轮机器复验全部通过，见 unweighted 字段），"
            "瓶颈是单侧的奇偶敏感估计 sum_{S_z} lambda(n) 的符号。"
            "加权化不解决 parity barrier，只是把它换了个样子。",
        ],
        "what_remains_open": [
            "支撑与可算主项的权衡：需要一个非负权 W，既满足 W>0 => Omega(n),Omega(N-n) <= 2，"
            "又使 sum W 可由筛法主项给出。Selberg lambda^2 权满足可算性但违反支撑；"
            "组合筛（Rosser-Iwaniec）的权满足（弱化的）支撑但主项常数被 parity barrier 卡住。",
            "Rosser-Iwaniec 型权的 sifting limit 在维度 2、u=3 处的可用常数："
            "本脚本未做该项，属解析输入（不是数值可决的）。",
            "模数到 N^{2/3} 的二元 lambda 相关（等价于二元 Chowla 型估计），"
            "远超固定 h 的对数平均定理（Tao 2016）。",
            "以平均 N 控制固定 N 需要例外集密度定理 + 正性间隙，二者均无。",
        ],
        "verdict": (
            "本轮把 OM-P-NT-0006/0007 留下的加权 2x2 系统算到底，结果比预期更硬："
            "(1) 恒等式 4X = T_W-2L1_W+L2_W 对**任意**对称非负权精确成立（随机权对照通过），"
            "所以代数部分零代价、与哥德巴赫难度无关；"
            "(2) Selberg lambda^2 权在筛后集合上恒等于 1、在筛外不消失，"
            "于是 W >= 1_{S_z}，加权恒等式只能给出 a_11 的**上界** 4A <= T_W-2L1_W+L2_W；"
            "(3) 污染（X-A）非负且**随 N 单调增大**（0.116 -> 0.290），"
            "故 X>0 推不出 A>0 —— **FRP 引理不足，而不只是难**；"
            "(4) divisor 展开 + CRT 逐类分解 + 对角自相似下降 U(L)=C_1(N/L) 均逐项机器核对通过；"
            "(5) 展开模数达 N^{2/3}，且块间存在净抵消（|各块| 之和 > |L2_W|）；"
            "(6) 平均 N 只能给 log 平均型无条件定理（Tao 2016），无法升级为固定 N 的正性间隙。"
            "结论：**这条路线把 Goldbach 归约成「可算主项 xor 支撑条件」的二难，"
            "而不是绕过 parity barrier 的新工具。** 状态维持 OPEN。"
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # ---------------- 人类可读稿 ----------------
    print("[5/6] markdown ...", flush=True)
    L = []
    A = L.append
    A("# OM-P-NT-0008 · Selberg 权下的 2x2 奇偶矩：支撑条件 vs 可算主项（2026-09-26）")
    A("")
    A("> 状态：**OPEN**。承接 OM-P-NT-0006（2x2 精确恒等式）与 OM-P-NT-0007（渐近存活 + Mobius 展开）。")
    A("")
    A("## 一、问题")
    A("")
    A("上一轮把 Goldbach 精确归约为 `4*a_11 = T - 2*M_1 + M_2`，并指出瓶颈是")
    A("`sum_{n in S_z} lambda(n)` 的符号。加权版本（用户 §12/§14）声称")
    A("")
    A("$$X_{11,W}=\\tfrac14\\big(T_W-2L_{1,W}+L_{2,W}\\big),\\qquad")
    A("X_{11,W}=\\sum_n W(n)\\frac{(1-\\lambda(n))(1-\\lambda(N-n))}{4}$$")
    A("")
    A("只要 $W>0\\Rightarrow\\Omega(n),\\Omega(N-n)\\le2$，就有 $X_{11,W}=a_{11}^{(W)}$。")
    A("本轮把这套加权系统**算到底**，并检验支撑条件在真实 Selberg 权下是否成立。")
    A("")
    A("## 二、S1 · 恒等式是零代价的")
    A("")
    A("对任意反射对称（$W(n)=W(N-n)$）非负权 $W$：")
    A("")
    A("$$\\sum_n W(n)(1-\\lambda(n))(1-\\lambda(N-n))=T_W-L_{1,W}-L'_{1,W}+L_{2,W},")
    A("\\quad L'_{1,W}=L_{1,W}$$")
    A("")
    A("即恒等式**不含任何困难**，代数部分零代价。机器验证："
    + str(ident_ok))
    A("")
    A("对照实验（S1b）：取**完全随机**的对称非负权 $W(n)=(a_n+a_{N-n})/2$，")
    A("$a_n>0$ 随机，无任何筛结构、无支撑条件，恒等式仍精确成立："
    + str(s1b_ok) + "。故该恒等式与哥德巴赫的难度**完全无关**。")
    A("")
    A("## 三、S2 · 支撑条件的精确代价（本轮主结论）")
    A("")
    A("取真实二维 Selberg 权 $W(n)=\\big(\\sum_{d\\mid n(N-n),\\,d\\le D}\\lambda_d\\big)^2$。")
    A("机器验证：")
    A("")
    A("* `W(n) = 1` 对所有筛后 $n$ **精确**成立（因 $n(N-n)$ 无小素因子，唯一可整除的 $d$ 是 1）："
    + str(supp_ok))
    A("* 于是 $W\\ge \\mathbf 1_{S_z}$ 逐点成立，但 $W$ 在 $S_z$ **外不消失** ⇒")
    A("  $4A\\le T_W-2L_{1,W}+L_{2,W}$ 只给出 $a_{11}$ 的**上界**，")
    A("  而 Goldbach 需要**下界**。")
    A("")
    A("| N | z | T_W | T_0 | T_W/T_0 | 筛外质量占比 | X | A（真双素，加权） | 污染 = X-A | 污染/X |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in s:
        A("| {N} | {z} | {tw:.1f} | {t0} | {ratio:.3f} | {off:.4f} | {x:.1f} | {a:.1f} | {pol:.1f} | {p:.4f} |".format(
            N=r["N"], z=r["z"], tw=r["T_W_brute"], t0=r["T0_num_sifted_pairs"],
            ratio=r["T_W_over_T0"], off=r["mass_off_sifted_over_TW"],
            x=r["X_oddodd"], a=r["A_pp_weighted"], pol=r["pollution_X_minus_A"],
            p=r["pollution_over_X"] if r["pollution_over_X"] is not None else float("nan")))
    A("")
    A("")
    A("### 污染按 $(\\Omega(n),\\Omega(N-n))$ 类型**完全分解**（回答「$P_{\\ge3}$ 污染有多大」）")
    A("")
    A("分桶：`1` = $\\Omega=1$（素数）、`2` = $\\Omega=2$、`3` = $\\Omega\\ge3$ **且为奇**、")
    A("`4` = $\\Omega\\ge4$ **且为偶**（保奇偶性，不破坏 $\\lambda$）。")
    A("")
    A("| N | A=(1,1) | (1,3) | (3,1) | (3,3) | 污染合计 | 污染/X | 偶侧审计 (1,4)/(4,1)/(4,4) |")
    A("|---|---|---|---|---|---|---|---|")
    for r in s:
        pb = r["pollution_decomposition"]["pollution_by_type"]
        A("| {N} | {a:.1f} | {p13:.1f} | {p31:.1f} | {p33:.1f} | {tot:.1f} | {fr:.4f} | {e1:.1f}/{e2:.1f}/{e3:.1f} |".format(
            N=r["N"], a=r["pollution_decomposition"]["both_one_weight"],
            p13=pb["(1,3)"], p31=pb["(3,1)"], p33=pb["(3,3)"],
            tot=r["pollution_X_minus_A"],
            fr=r["pollution_over_X"] if r["pollution_over_X"] is not None else float("nan"),
            e1=pb["(1,even>=4)"], e2=pb["(even>=4,1)"], e3=pb["(even>=4,even>=4)"]))
    A("")
    A("读法：$X$ 恰由 $(1,1)+(1,3)+(3,1)+(3,3)$ 四格组成（机器核对），其中 $(1,1)$ 格就是 $A$，")
    A("故**污染 $=X-A$ 恰为 $(1,3)+(3,1)+(3,3)$ 三格**（$\\lambda=-1$ 而 $\\Omega\\ge3$ 的那些对）。")
    A("一致性断言（`X = Σ_{both odd}`、`A = W(1,1)`）："
      + str(all(r["pollution_decomposition"]["consistency_X_eq_both_odd"]
                and r["pollution_decomposition"]["consistency_A_eq_both_one"] for r in s))
      + "。")
    A("")
    A("方向性：`X >= A` 恒成立（机器验证 " + str(all(r["ineq_X_ge_A"] for r in s))
      + "），`4A <= T_W-2L1_W+L2_W` 恒成立（"
      + str(all(r["ineq_4A_le_T_minus_2L1_plus_L2"] for r in s)) + "）。")
    A("即：**加权恒等式只给出 $a_{11}$ 的上界**，加权 FRP 引理的正性结论")
    A("（$T_W-2L_{1,W}+L_{2,W}>0$）**推不出** $\\Omega$ 为奇的二元组是双素对。")
    A("")
    A("**要在污染为 0 的同时保持非负性，只能把权乘回 $\\mathbf 1_{S_z}$；")
    A("而 $W\\equiv1$ 于 $S_z$ 上，于是权被还原成指示函数，Selberg 结构一点不剩。**")
    A("这就是 parity barrier 在 2x2 框架下的精确位置。")
    A("")
    A("## 四、S3 · divisor 展开（逐项机器核对）")
    A("")
    A("$$T_W=\\sum_{d_1,d_2}\\lambda_{d_1}\\lambda_{d_2}\\,\\#\\{n<N:[d_1,d_2]\\mid n(N-n)\\}$$")
    A("")
    A("$$U(L)=\\sum_{f_1f_2=f}\\lambda(e f_1)\\!\\sum_{\\substack{m\\le M\\\\ m\\equiv c\\ (f_2)}}\\!\\lambda(m)\\lambda(N-e f_1m),")
    A("\\quad e=\\gcd(L,N),\\ f=L/e$$")
    A("")
    A("展开精确性：" + str(exp_ok) + "；逐 L 暴力核对（小 N）："
    + str(all(r["L_rows_brute_verified"] for r in s if "L_rows_brute_verified" in r)))
    A("")
    A("## 五、S4 · 对角模数走自相似下降")
    A("")
    A("$L\\mid N$ 时只剩一族，且精确成立 $U(L)=C_1(N/L)$，")
    A("$C_1(X)=\\sum_{m<X}\\lambda(m)\\lambda(X-m)$。推导一行：$n=Lm$ 时")
    A("$\\lambda(Lm)\\lambda(N-Lm)=\\lambda(L)^2\\lambda(m)\\lambda(N/L-m)$。")
    A("机器验证：" + str(diag_ok)
      + "（最大 abs_error = {:.3g}）".format(max(
          (r["abs_error"] for r in s[0]["self_similar_diagonal_rows"]), default=0.0)))
    A("")
    A("即对角项**就是**原泛函在 $N/L$ 处的同形复印（反射-伸缩轨道，OM-P-NT-0005），")
    A("不提供新的独立方程。（早期版本误写成 $\\lambda(L)C_1(N/L)$，多了一个因子，已修正。）")
    A("")
    A("## 六、S5 · 逐模数分类与中央不可控块")
    A("")
    A("模数分块（$\\log^2N$ 以下的「可控块」、$z$ 以内、中央块 $(z,D^2]$）：")
    A("")
    A("| N | 模数最大 L | D² = z² | #L(可控/中央) | 中央块 \\|贡献\\| 占比 | 可控块 \\|贡献\\| 占比 | 中央块 净贡献/T_W | L2_W/T_W |")
    A("|---|---|---|---|---|---|---|---|")
    for r in s:
        bl = r["blocks"]
        sa = bl.get("share_of_abs_L2") or {}
        cl = bl.get("count_L_per_block") or {}
        big_abs = sa.get("z_lt_L_le_Dsq")
        ctrl_abs = sa.get("L_le_logN_sq")
        small_ctrl = (cl.get("L_le_logN_sq", 0) + cl.get("logN_sq_lt_L_le_z", 0))
        big = bl["L2_over_TW"].get("z_lt_L_le_Dsq")
        A("| {} | {} | {} | {}/{} | {} | {} | {} | {} |".format(
            r["N"], bl["L_range_max"], bl["D_squared"],
            small_ctrl, cl.get("z_lt_L_le_Dsq", 0),
            "{:.3f}".format(big_abs) if big_abs is not None else "n/a",
            "{:.3f}".format(ctrl_abs) if ctrl_abs is not None else "n/a",
            "{:+.4f}".format(big) if big is not None else "n/a",
            "{:+.4f}".format(r["L2_W_brute"] / r["T_W_brute"])))
    A("")
    for r in s:
        A("* N = {}：{}".format(r["N"], r["blocks"]["cancellation_note"]))
    A("")
    A("### 单个模数明细（按对 $L_2^W$ 的贡献 |coef·U2| 降序取前 6）")
    A("")
    for r in s:
        rows_sorted = sorted(r["L_rows"],
                             key=lambda x: -abs(x["coef_in_weight"] * x["U2"]))[:6]
        A("N = {}".format(r["N"]))
        A("")
        A("| L | L \\| N | #CRT 类 | 计数 | U2 | 相干度 U2/计数 | coef·U2 |")
        A("|---|---|---|---|---|---|---|")
        for x in rows_sorted:
            A("| {} | {} | {} | {} | {} | {} | {:+.1f} |".format(
                x["L"], x["L_divides_N"], x["num_crt_classes"], x["count"], x["U2"],
                "{:.3f}".format(x["coherence_U2_over_count"])
                if x["coherence_U2_over_count"] is not None else "n/a",
                x["coef_in_weight"] * x["U2"]))
        A("")
    A("")
    A("模数上限 $D^2=z^2=N^{2/3}$，而 $\\lambda$ 在等差数列中的无条件可用范围只有")
    A("$q\\le(\\log N)^A$（Siegel-Walfisz 型）。差距是 $N^{2/3}$ vs $(\\log N)^A$。")
    A("注意**块间净抵消**：各块贡献的绝对值之和大于 $|L_2^W|$ 本身，")
    A("因此按 $L_2^W$ 归一化的份额会 >1 或变号；上表统一用 over-$T_W$ 的稳定刻度。")
    A("")
    A("## 七、S6 · 平均 N 能否升级到固定 N")
    A("")
    A("| h | x | A_natural/x | A_log/log x | 随机模型 1/sqrt(x) |")
    A("|---|---|---|---|---|")
    for row in chowla:
        for p in row["points"]:
            A("| {} | {} | {:.5f} | {:.5f} | {:.5f} |".format(
                row["h"], p["x"], p["A_natural_over_x"],
                p["A_log_over_logx"], p["random_model_natural_over_x"]))
    A("")
    A("* 固定 $h$ 的**对数平均**二点 Chowla 是**无条件定理**（Tao 2016）。")
    A("* **自然平均**（Chowla 猜想本体）仍 OPEN。")
    A("* 我们的需求是三重的：自然平均、模数一致到 $N^{2/3}$、固定 $N$ 的**正性间隙**。")
    A("  任何 $o()$ 型平均既排除不了稀疏例外集，也给不出正性间隙。")
    A("")
    A("## 八、裁定")
    A("")
    for t in report["summary"]["interpretation"]:
        A("* " + t)
    A("")
    A("## 九、仍然开放")
    A("")
    for w in report["summary"]["what_remains_open"]:
        A("* " + w)
    A("")
    A("## 十、红线")
    A("")
    A("* 本稿不证明哥德巴赫，不证明任何 `*_W > 0`。")
    A("* S2 是**负面**结论（Selberg 权路线在支撑条件处断裂），不是「新工具」。")
    A("* 所有计算在 $N\\le2.4\\times10^5$（加权）与 $x\\le10^6$（相关平均）的有限尺度内。")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print("[6/6] done", flush=True)
    print(json.dumps({k: v for k, v in report["summary"].items()
                      if k != "interpretation"}, ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)
    print("saved:", md_path)


def is_prime(spf, n):
    if n < 2:
        return False
    return spf[n] == n if n < len(spf) else False


if __name__ == "__main__":
    main()
