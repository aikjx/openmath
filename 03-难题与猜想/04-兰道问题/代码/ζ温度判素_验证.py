# -*- coding: utf-8 -*-
"""ζ-温度判素体系（广义除数函数 τ_z 与 USSD 路线）核验。

核验清单（编号对应理论稿）
  A1  生成函数 (1-x)^{-z} = Σ_a τ_z(p^a) x^a，且 τ_z(p^a) 的 z-多项式系数
      = 无符号第一类 Stirling 数 [a k]/a!                              —— 式(1)
  A2  τ'_0(q^a) = 1/a，ω(n) >= 2 时 τ'_0(n) = 0                        —— 式(3)
  A3  F'_N(0) = Σ_{p+q^a=N} log p / a = G_θ(N) + E_pp(N)               —— 式(4)(5)
  A4  D_{s,t}(p) = 1；ω(n) >= 2 => D_{s,t}(n) <= 0；D~ <= 1_P          —— 式(9)(11)(13)
  A5  G_θ(N) >= [F_N(s) - ρ²F_N(t)]/(s(1-ρ)) - E_pp^{s,t}(N)           —— 式(14)
  B1  Ψ(ρ,c) := (e^{ρc} - ρ e^c)/(1-ρ) 的层级闭式与 Ψ < 1             —— 新结果
  B2  不移位：Σ_{n<=x} D_{s,t}(n) / (x/log x) -> Ψ(ρ,c)
  B3  移位：bracket 的 ω-层级 -> c^{r-1}(ρ^r-ρ²)/(ρ(1-ρ)(r-1)!)·主项
  B4  单变量 |z|-一致 Selberg–Delange：Σ_{n<=x}τ_z(n)/(x (log x)^{z-1}/Γ(z)) -> 1
  B5  临界曲线 c* = -log ρ/(1-ρ)：Ψ 的符号翻转（falsification 测试）

红线：数值零反例不构成渐近结论；本脚本只核验恒等式/不等式与主项形状，不证明哥德巴赫。
"""
from __future__ import annotations

import json
import math
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 孪生素数常数 C_2（用于 Goldbach 奇异级数）
C2 = 0.66016181584686957392781211001455577843262336028473341331945


# ----------------------------------------------------------------- 基础工具
def stirling1_unsigned(n, k):
    """无符号第一类 Stirling 数 [n k]（递推 [n k] = [n-1 k-1] + (n-1)[n-1 k]）。"""
    row = [0] * (n + 1)
    row[0] = 1
    for i in range(1, n + 1):
        new = [0] * (n + 1)
        for j in range(1, i + 1):
            new[j] = row[j - 1] + (i - 1) * row[j]
        row = new
    return row[k]


def tau_poly(a):
    """τ_z(p^a) 作为 z 的多项式：系数表（升幂，Fraction）。"""
    coeffs = [Fraction(0), Fraction(1)]          # z
    for j in range(1, a):                        # 乘 (z+j)
        new = [Fraction(0)] * (len(coeffs) + 1)
        for i, c in enumerate(coeffs):
            new[i] += c * j
            new[i + 1] += c
        coeffs = new
    den = math.factorial(a)
    return [c / den for c in coeffs]


def poly_mul(p, q):
    r = [Fraction(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                if b:
                    r[i + j] += a * b
    return r


def sieve(N):
    isp = np.ones(N + 1, dtype=bool)
    isp[:2] = False
    for i in range(2, math.isqrt(N) + 1):
        if isp[i]:
            isp[i * i::i] = False
    return isp


def tau_array(N, z, plist):
    """τ_z(n)，n <= N（float64 数组）。0 < z，逐素数幂乘 (z+a-1)/a。"""
    T = np.ones(N + 1, dtype=np.float64)
    T[0] = 0.0
    for p in plist:
        pa = p
        a = 1
        while pa <= N:
            T[pa::pa] *= (z + a - 1) / a
            a += 1
            pa *= p
    return T


def omega_array(N, plist):
    om = np.zeros(N + 1, dtype=np.uint8)
    for p in plist:
        om[p::p] += 1
    return om


def mobius_array(N, plist):
    mu = np.ones(N + 1, dtype=np.int8)
    for p in plist:
        mu[p::p] *= -1
        p2 = p * p
        if p2 <= N:
            mu[p2::p2] = 0
    return mu


def singular_series(N):
    """Goldbach 奇异级数 𝔖(N) = 2 C_2 Π_{ℓ|N, ℓ odd} (ℓ-1)/(ℓ-2)。"""
    val = 2.0 * C2
    m = N
    d = 3
    while d * d <= m:
        if m % d == 0:
            val *= (d - 1.0) / (d - 2.0)
            while m % d == 0:
                m //= d
        d += 2
    if m > 2:
        val *= (m - 1.0) / (m - 2.0)
    return val


def psi(rho, c):
    """(e^{ρc} - ρ e^c)/(1-ρ) —— 主项系数（式(19)）。"""
    return (math.exp(rho * c) - rho * math.exp(c)) / (1.0 - rho)


def layer_pred(rho, c, rmax):
    """层级 r 的主项系数：c^{r-1}(ρ^r - ρ²)/(ρ(1-ρ)(r-1)!)。"""
    out = []
    for r in range(1, rmax + 1):
        out.append((c ** (r - 1)) * (rho ** r - rho ** 2)
                   / (rho * (1.0 - rho) * math.factorial(r - 1)))
    return out


# ----------------------------------------------------------------- A 段：代数
def check_A1():
    """(1-x)^{-z} = Σ_a τ_z(p^a)x^a；τ_z(p^a) 系数 = [a k]/a!。"""
    rows = []
    ok_poly = True
    for a in range(1, 9):
        cf = tau_poly(a)
        for k in range(1, a + 1):
            want = Fraction(stirling1_unsigned(a, k), math.factorial(a))
            if cf[k] != want:
                ok_poly = False
        rows.append(dict(a=a, coeffs=[str(c) for c in cf[1:]],
                          coeff_z1=str(cf[1])))
    ok_gen = True
    gen_rows = []
    for z in (0.37, 0.05, 1.0, 2.0, 0.5):
        for x in (0.1, 0.3):
            A = 40
            s = 0.0
            for a in range(0, A + 1):
                if a == 0:
                    s += 1.0
                else:
                    cf = tau_poly(a)
                    s += sum(float(c) * (z ** k) for k, c in enumerate(cf)) * (x ** a)
            exact = (1.0 - x) ** (-z)
            err = abs(s - exact)
            if err > 1e-9 * max(1.0, abs(exact)):
                ok_gen = False
            gen_rows.append(dict(z=z, x=x, partial=round(s, 12),
                                 exact=round(exact, 12), err=err))
    return dict(ok=bool(ok_poly and ok_gen), poly_rows=rows, gen_rows=gen_rows)


def check_A2():
    """τ'_0(q^a) = 1/a；ω(n) >= 2 => τ'_0(n) = 0（精确有理数）。"""
    rows = []
    ok = True
    for a in range(1, 10):
        d = tau_poly(a)[1]
        want = Fraction(1, a)
        rows.append(dict(a=a, tau0_prime=str(d), want=str(want), ok=(d == want)))
        ok = ok and (d == want)
    # 乘积律：n = Π q_i^{a_i}，r >= 2 时最低次 >= 2，故 z^1 系数为 0
    prod_rows = []
    for n, fac in ((6, [1, 1]), (12, [2, 1]), (72, [3, 2]), (30, [1, 1, 1]),
                   (210, [1, 1, 1]), (8, [3]), (49, [2]), (27, [3])):
        poly = [Fraction(1)]
        for a in fac:
            poly = poly_mul(poly, tau_poly(a))
        c1 = poly[1] if len(poly) > 1 else Fraction(0)
        r = len(fac)
        good = (c1 == 0) if r >= 2 else (c1 == Fraction(1, fac[0]))
        prod_rows.append(dict(n=n, exponents=fac, omega=r,
                              tau0_prime=str(c1), ok=good))
        ok = ok and good
    return dict(ok=bool(ok), prime_power_rows=rows, product_rows=prod_rows)


def check_A3(NLIST):
    """F_N(z) 作为 z 的多项式，其 z^1 系数 == Σ_{p+q^a=N} log p / a。"""
    rows = []
    ok = True
    for N in NLIST:
        isp = sieve(N)
        plist = np.nonzero(isp)[0].tolist()
        # 分解 n = N-p：用最小素因子表
        spf = np.zeros(N + 1, dtype=np.int32)
        for p in plist:
            m = np.arange(p, N + 1, p, dtype=np.int64)
            unset = spf[m] == 0
            spf[m[unset]] = p
        acc = None
        for p in plist:
            if p > N - 2:
                break
            n = N - p
            if n < 2:
                continue
            # n 的指数分解
            exps = []
            m = n
            while m > 1:
                q = int(spf[m])
                e = 0
                while m % q == 0:
                    m //= q
                    e += 1
                exps.append(e)
            poly = [Fraction(1)]
            for a in exps:
                poly = poly_mul(poly, tau_poly(a))
            if acc is None:
                acc = [0.0] * len(poly)
            while len(acc) < len(poly):
                acc.append(0.0)
            lp = math.log(float(p))
            for i, c in enumerate(poly):
                acc[i] += lp * float(c)
        Fprime = acc[1] if acc and len(acc) > 1 else 0.0
        # 直接按素数幂求和
        direct = 0.0
        a = 1
        while (2 ** a) <= N:
            for q in plist:
                qa = q ** a
                if qa > N - 2:
                    break
                m = N - qa
                if m >= 2 and isp[m]:
                    direct += math.log(float(m)) / a
            a += 1
        G = 0.0
        for p in plist:
            if p > N - 2:
                break
            m = N - p
            if m >= 2 and isp[m]:
                G += math.log(float(p))
        Epp = direct - G
        good = abs(Fprime - direct) < 1e-6 * max(1.0, abs(direct))
        ok = ok and good
        rows.append(dict(N=N, Fprime0_poly=Fprime, prime_power_sum=direct,
                         G_theta=G, E_pp=Epp, ok=good))
    return dict(ok=bool(ok), rows=rows)


def check_A4(nmax, cases):
    """D_{s,t}(p)=1；ω(n)>=2 => D<=0；n=p^a (a>=2) => D <= η_a。"""
    isp = sieve(nmax)
    plist = np.nonzero(isp)[0].tolist()
    om = omega_array(nmax, plist)
    out_rows = []
    ok = True
    for rho, c, L in cases:
        t = c / L
        s = rho * t
        Ts = tau_array(nmax, s, plist)
        Tt = tau_array(nmax, t, plist)
        D = (Ts - (rho ** 2) * Tt) / (s * (1.0 - rho))
        # η_a = max(D(p^a), 0)，与 p 无关：用最小素数幂 2^a 求值
        eta = {}
        a = 2
        while (2 ** a) <= nmax:
            eta[a] = float(D[2 ** a])
            a += 1
        idx = np.arange(2, nmax + 1)
        dom = om[idx]
        dval = D[idx]
        bad_prime = bad_multi = bad_pp = 0
        worst_multi = -1e18
        # 素数
        pmask = isp[idx]
        dev = np.abs(dval[pmask] - 1.0).max() if pmask.any() else 0.0
        bad_prime = int((np.abs(dval[pmask] - 1.0) > 1e-9).sum()) if pmask.any() else 0
        # ω >= 2
        mmask = dom >= 2
        if mmask.any():
            worst_multi = float(dval[mmask].max())
            bad_multi = int((dval[mmask] > 1e-12).sum())
        # 核的精确刻画：D(n)=0 <=> ω(n)=2 且 n 无平方因子
        mu = mobius_array(nmax, plist)[idx]
        sqfree2 = (dom == 2) & (mu != 0)
        zero = np.abs(dval) < 1e-12
        n_zero = int(zero.sum())
        n_sqfree2 = int(sqfree2.sum())
        kernel_bad = int((zero != sqfree2).sum())
        max_on_sqfree2 = float(np.abs(dval[sqfree2]).max()) if n_sqfree2 else 0.0
        max_on_nonsqfree_omega2 = float(
            dval[(dom == 2) & (mu == 0)].max()) if ((dom == 2) & (mu == 0)).any() else None
        max_on_omega_ge3 = float(
            dval[dom >= 3].max()) if (dom >= 3).any() else None
        # 素数幂 p^a, a>=2：D <= η_a
        ppmask = (~pmask) & (dom == 1)
        if ppmask.any():
            vals = dval[ppmask]
            nums = idx[ppmask]
            worst = -1e18
            bad = 0
            for v, nn in zip(vals, nums):
                aa = 2
                while (2 ** aa) <= nn:
                    r = round(nn ** (1.0 / aa))
                    if r >= 2 and r ** aa == nn and isp[r]:
                        break
                    aa += 1
                if aa in eta and v - eta[aa] > 1e-9:
                    bad += 1
                worst = max(worst, v - eta.get(aa, 0.0))
            bad_pp = bad
        good = (bad_prime == 0 and bad_multi == 0 and bad_pp == 0
                and kernel_bad == 0)
        ok = ok and good
        out_rows.append(dict(rho=rho, c=c, L=round(L, 6), s=s, t=t,
                             n_range=nmax,
                             max_abs_dev_on_primes=float(dev),
                             bad_primes=bad_prime,
                             max_D_on_omega_ge2=worst_multi,
                             bad_omega_ge2=bad_multi,
                             bad_prime_powers=bad_pp,
                             kernel_count_zero=n_zero,
                             kernel_count_squarefree_omega2=n_sqfree2,
                             kernel_mismatch=kernel_bad,
                             max_abs_D_on_squarefree_omega2=max_on_sqfree2,
                             max_D_on_nonsquarefree_omega2=max_on_nonsqfree_omega2,
                             max_D_on_omega_ge3=max_on_omega_ge3,
                             eta={str(k): v for k, v in eta.items()},
                             eta_limit_1_over_a={str(k): round(1.0 / k, 6)
                                                 for k in eta},
                             ok=good))
        del Ts, Tt, D
    return dict(ok=bool(ok), rows=out_rows)


# ----------------------------------------------------------------- B 段：尺度
def compute_shifted(N, rho, c, rmax=8):
    L = math.log(math.log(N))
    t = c / L
    s = rho * t
    isp = sieve(N)
    plist = np.nonzero(isp)[0].tolist()
    om = omega_array(N, plist)

    pr = np.array([p for p in plist if p <= N - 2], dtype=np.int64)
    n = N - pr
    w = np.log(pr.astype(np.float64))
    omn = om[n].astype(np.int64)

    Ts = tau_array(N, s, plist)
    sum_ts = float(Ts.sum())
    Tsn = Ts[n]
    Fs = float(np.dot(w, Tsn))
    ls = np.bincount(omn, weights=w * Tsn, minlength=rmax + 1)
    del Ts, Tsn

    Tt = tau_array(N, t, plist)
    sum_tt = float(Tt.sum())
    Ttn = Tt[n]
    Ft = float(np.dot(w, Ttn))
    lt = np.bincount(omn, weights=w * Ttn, minlength=rmax + 1)
    del Tt, Ttn

    denom = s * (1.0 - rho)
    bracket = (Fs - (rho ** 2) * Ft) / denom
    layers = (ls - (rho ** 2) * lt) / denom

    ispn = isp[n]
    G = float(w[ispn].sum())
    # E_pp^{s,t}：ω=1 层减去纯素数部分
    Epp_st = float(layers[1]) - G
    # 导数版 E_pp
    Epp_deriv = 0.0
    a = 2
    while (2 ** a) <= N:
        for q in plist:
            qa = q ** a
            if qa > N - 2:
                break
            m = N - qa
            if m >= 2 and isp[m]:
                Epp_deriv += math.log(float(m)) / a
        a += 1
    Fprime0 = G + Epp_deriv

    Sg = singular_series(N)
    main = Sg * N / math.log(N)
    # 不移位
    unshift_D = (sum_ts - (rho ** 2) * sum_tt) / denom
    # |z|-一致 Selberg–Delange（单变量，无移位）
    sd_s = sum_ts / (N * (math.log(N) ** (s - 1.0)) / math.gamma(s))
    sd_t = sum_tt / (N * (math.log(N) ** (t - 1.0)) / math.gamma(t))

    return dict(
        N=N, rho=rho, c=c, L=L, t=t, s=s,
        F_s=Fs, F_t=Ft, bracket=bracket,
        G_theta=G, E_pp_shifted=Epp_st, E_pp_deriv=Epp_deriv,
        Fprime0=Fprime0,
        singular_series=Sg, main_term=main,
        bracket_over_main=bracket / main,
        Fprime0_over_main=Fprime0 / main,
        G_over_main=G / main,
        E_pp_deriv_over_main=Epp_deriv / main,
        E_pp_shifted_over_main=Epp_st / main,
        layers_over_main=[float(layers[r]) / main for r in range(0, rmax + 1)],
        layer_pred=layer_pred(rho, c, rmax),
        tau_t_layers_over_main=[float(lt[r]) / main for r in range(0, rmax + 1)],
        poisson_pred=[(c ** r) / (L * math.factorial(r - 1)) if r >= 1 else 0.0
                      for r in range(0, rmax + 1)],
        psi=psi(rho, c),
        sum_layers_tail_ge2=float(sum(layers[2:rmax + 1])) / main,
        minorant_residual=(G - (bracket - Epp_st)) / main,
        unshift_D_over_NlogN=unshift_D / (N / math.log(N)),
        sd_ratio_z_s=sd_s, sd_ratio_z_t=sd_t,
    )


def check_C(NLIST, cs):
    """单变量 |z|-一致 Selberg–Delange：z = c/log log x，c 含负值。

    报告  ratio = Σ_{n<=x}τ_z(n) / [ x (log x)^{z-1} / Γ(z) ]
    以及  err_ratio = |Σ - main| / ( |z| x / log^2 x )   （USSD 误差形状，δ=1）
    """
    rows = []
    for N in NLIST:
        L = math.log(math.log(N))
        logN = math.log(N)
        isp = sieve(N)
        plist = np.nonzero(isp)[0].tolist()
        for c in cs:
            z = c / L
            T = tau_array(N, z, plist)
            s = float(T.sum())
            del T
            main = N * (logN ** (z - 1.0)) / math.gamma(z)
            denom = abs(z) * N / (logN ** 2)
            rows.append(dict(N=N, c=c, z=z, sum_tau=s, main=main,
                             ratio=s / main,
                             err_over_zN_log2=abs(s - main) / denom))
    return rows


def check_B5(N, rho, cs):
    rows = []
    for c in cs:
        r = compute_shifted(N, rho, c, rmax=6)
        rows.append(dict(c=c, psi=psi(rho, c),
                         bracket_over_main=r["bracket_over_main"],
                         critical_c=-math.log(rho) / (1.0 - rho)))
    return rows


def main():
    t0 = time.time()
    NMAX_A3 = [2000, 20000, 200000]
    NLIST = [10 ** 4, 10 ** 5, 10 ** 6, 10 ** 7]
    RHO, C = 1.0 / 3.0, 0.5

    print("[A1] τ_z(p^a) 多项式与生成函数 ...")
    A1 = check_A1()
    print("     ok =", A1["ok"])
    print("[A2] τ'_0 ...")
    A2 = check_A2()
    print("     ok =", A2["ok"])
    print("[A3] F'_N(0) 恒等式 ...")
    A3 = check_A3(NMAX_A3)
    print("     ok =", A3["ok"])
    print("[A4] 两温 detector 逐点 ...")
    Ls = [math.log(math.log(200000.0))]
    A4 = check_A4(200000, [(RHO, C, Ls[0]), (0.5, 0.5, Ls[0]), (0.2, 1.0, Ls[0])])
    print("     ok =", A4["ok"])

    rows = []
    for N in NLIST:
        r = compute_shifted(N, RHO, C)
        rows.append(r)
        print("[B]  N=%.0e  bracket/main=%.4f  psi=%.4f  F'_N(0)/main=%.4f  "
              "unshift=%.4f  SD(t)=%.4f" % (N, r["bracket_over_main"], r["psi"],
                                            r["Fprime0_over_main"],
                                            r["unshift_D_over_NlogN"],
                                            r["sd_ratio_z_t"]))
    print("[C] 单变量 |z|-一致 Selberg–Delange ...")
    Csec = check_C([10 ** 5, 10 ** 6, 10 ** 7], [-1.0, -0.5, 0.25, 0.5, 1.0, 2.0])
    for r in Csec:
        print("     N=%.0e c=%+.2f  ratio=%.4f  |err|/(|z|N/log^2N)=%.3f" %
              (r["N"], r["c"], r["ratio"], r["err_over_zN_log2"]))

    print("[B5] 临界曲线扫描 (rho=1/3) ...")
    B5 = check_B5(10 ** 6, RHO, [0.25, 0.5, 1.0, 1.647918, 2.5, 3.0])
    for r in B5:
        print("     c=%.6f  psi=%+.4f  bracket/main=%+.4f" %
              (r["c"], r["psi"], r["bracket_over_main"]))

    # Ψ < 1 与 sup
    grid = []
    best = (-1e9, None)
    for i in range(1, 99):
        rho = i / 100.0
        for j in range(1, 400):
            c = j / 100.0
            v = psi(rho, c)
            if v > best[0]:
                best = (v, (rho, c))
    grid = dict(max_psi=best[0], argmax_rho=best[1][0], argmax_c=best[1][1],
                psi_at_user_point=psi(RHO, C),
                note="Ψ(ρ,c) = (e^{ρc}-ρe^c)/(1-ρ)；理论证明 Ψ<1，sup=1（ρ→0 或 c→0）")

    rep = dict(
        A1=A1, A2=A2, A3=A3, A4=A4,
        shifted=rows, B5=B5, C=Csec, psi_grid=grid,
        meta=dict(seconds=round(time.time() - t0, 1),
                  python=sys.version.split()[0],
                  numpy=np.__version__,
                  rho=RHO, c=C,
                  honesty="数值恒等式与有限尺度主项拟合；不构成渐近证明。"))
    out = Path(__file__).resolve().parent.parent / "数据" / "zeta_temperature_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", out)


if __name__ == "__main__":
    main()
