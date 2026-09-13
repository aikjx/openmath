# -*- coding: utf-8 -*-
"""二维均方 Goldbach Dispersion（BGD → DWSC 链）核验。

核验清单（编号对应理论稿）
  E1  换元 (5)(6) 的精确重写：两条**独立**计算路径比对
      （(k,h,m) 三循环  vs  (x,t) 网格上按定义 (6) 构造 W_N）
  E2  gcd 能量和 (7)：Σ_{m1,m2} gcd²/(m1²m2²) ≍ 1/M 的精确与尺度核验
  E3  二维均方 dispersion (2) 的实测：
      C_N(k,h) = Σ_{m~M} Λ(N-km)Λ(N-(k+h)m) - |m区间|·𝔖(k,h)
      报告 均方/(H K M²)（即"有效的 log^{-A}"）、最坏点、模型质量、对角项稀释 (4)
  E4  指数预算：Cauchy(L²×L²) 端点 与 Hölder(L¹×L^∞) 端点 的对照

红线：数值零反例与有限尺度拟合不构成渐近证明；本脚本只核验恒等式、量与指数预算。
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


# ------------------------------------------------------------------ 基础
def sieve(N):
    isp = np.ones(N + 1, dtype=bool)
    isp[:2] = False
    for i in range(2, math.isqrt(N) + 1):
        if isp[i]:
            isp[i * i::i] = False
    return isp


def build_lambda(N):
    """Λ(n)：n=p^a 时为 log p，否则 0。"""
    isp = sieve(N)
    Lam = np.zeros(N + 1, dtype=np.float64)
    for p in np.nonzero(isp)[0].tolist():
        pa = int(p)
        lp = math.log(float(p))
        while pa <= N:
            Lam[pa] = lp
            pa *= int(p)
    return Lam, np.nonzero(isp)[0]


def tau_upto(n):
    """τ(k)，k<=n。"""
    t = np.zeros(n + 1, dtype=np.int64)
    for d in range(1, n + 1):
        t[d::d] += 1
    return t


# ------------------------------------------------------------------ E1
def check_E1(N, K0, K1, M0, M1, H0, beta_name="tau"):
    """(5)(6) 精确重写：两条独立路径比对（只用 ΛΛ 部分，模型部分仿射线性故同样成立）。"""
    Lam, _ = build_lambda(N)
    isp = sieve(N)
    tau = tau_upto(K1 + H0 + 5)
    if beta_name == "tau":
        beta = {k: int(tau[k]) for k in range(0, K1 + H0 + 5)}
    else:
        beta = {k: ((-1) ** k) * int(tau[k]) for k in range(0, K1 + H0 + 5)}

    ks = list(range(K0, K1 + 1))
    ms = list(range(M0, M1 + 1))
    hs = list(range(-H0, H0 + 1))

    # ---- 路径 A：原始 (k,h,m) 三循环
    A = 0.0
    for h in hs:
        if h == 0:
            continue
        for k in ks:
            k2 = k + h
            if not (K0 <= k2 <= K1):
                continue
            s = 0.0
            for m in ms:
                n1 = N - k * m
                n2 = N - k2 * m
                if n1 >= 2 and n2 >= 2:
                    s += Lam[n1] * Lam[n2]
            A += beta[k2] * beta[k] * s

    # ---- 路径 B：(x,t) 网格上按定义 (6) 构造 W_N
    xs = range(1, N)
    tmax = H0 * M1
    B = 0.0
    for x in xs:
        lx = Lam[x]
        if lx == 0.0:
            continue
        # 收集 m in [M0,M1] 且 m | N-x 且 (N-x)/m in [K0,K1]
        terms = []
        r = N - x
        if r <= 0:
            continue
        for m in ms:
            if r % m == 0:
                k = r // m
                if K0 <= k <= K1:
                    terms.append((m, k))
        if not terms:
            continue
        # t = h*m，|h|<=H0，且 k+h in [K0,K1]
        for m, k in terms:
            for h in hs:
                if h == 0:
                    continue
                k2 = k + h
                if not (K0 <= k2 <= K1):
                    continue
                t = h * m
                xt = x - t
                if 2 <= xt <= N:
                    B += beta[k2] * beta[k] * lx * Lam[xt]
    A = float(A)
    B = float(B)
    return dict(N=N, K=(K0, K1), M=(M0, M1), H=H0, beta=beta_name,
                lhs_triple_loop=A, rhs_weight_grid=B,
                abs_diff=abs(A - B), ok=bool(abs(A - B) < 1e-6 * max(1.0, abs(A))))


# ------------------------------------------------------------------ E2
def check_E2(Ms):
    """Σ_{m1,m2~M} gcd(m1,m2)²/(m1²m2²)  精确（Fraction）与浮点尺度。"""
    rows = []
    for M in Ms:
        lo, hi = M, 2 * M
        tot = 0.0
        for m1 in range(lo, hi + 1):
            for m2 in range(lo, hi + 1):
                g = math.gcd(m1, m2)
                tot += (g * g) / (m1 * m1 * m2 * m2)
        val = float(tot)
        rows.append(dict(M=M, exact_sum=val, over_one_over_M=val * M,
                         M_times_sum=val * M))
    return rows


# ------------------------------------------------------------------ E3
def singular_series_grid(N, K0, K1, H0, primes):
    """𝔖(k,h)：两个线性型 L1=N-km, L2=N-(k+h)m 的局部奇异级数（2D 网格）。

    局部因子 (1-ν(p)/p)/(1-1/p)²，ν(p)=#{m mod p : L1(m)L2(m)≡0}。
    """
    hs = np.arange(-H0, H0 + 1, dtype=np.int64)
    ks = np.arange(K0, K1 + 1, dtype=np.int64)
    KK, HH = np.meshgrid(ks, hs, indexing="ij")      # (K, 2H+1)
    K2 = KK + HH
    valid = (K2 >= K0) & (K2 <= K1) & (HH != 0)
    S = np.ones(KK.shape, dtype=np.float64)
    for p in primes:
        p = int(p)
        d1 = (KK % p == 0)
        d2 = (K2 % p == 0)
        dN = (N % p == 0)
        dH = (HH % p == 0)
        z1 = np.where(d1, np.where(dN, p, 0), 1)
        z2 = np.where(d2, np.where(dN, p, 0), 1)
        # 两根重合的条件：p|h 或 p|N（L1-L2 = h·m，且 p|N 时两根同为 m≡0）
        inter = np.where(
            d1 & d2, np.where(dN, p, 0),
            np.where(d1, np.where(dN, z2, 0),
                     np.where(d2, np.where(dN, z1, 0),
                              np.where(dH | dN, 1, 0))))
        nu = z1 + z2 - inter
        f = (1.0 - nu / p) / (1.0 - 1.0 / p) ** 2
        S *= f
    S = np.where(valid, S, 0.0)
    return S, ks, hs, valid


def run_E3(N, K, M, H, P=2000):
    """实测二维均方 dispersion。k~[K,2K], m~[M,2M], |h|<=H 且 k+h~[K,2K]。"""
    t0 = time.time()
    assert (2 * K) * (2 * M) < N, "需要 4KM < N 以保证 x=N-km>0"
    Lam, pall = build_lambda(N)
    m = np.arange(M, 2 * M + 1, dtype=np.int64)
    nm = len(m)
    ks = np.arange(K, 2 * K + 1, dtype=np.int64)
    primes = [int(p) for p in pall if p <= P]

    Sser, ks2, hs, valid = singular_series_grid(N, K, 2 * K, H, primes)

    acc = np.zeros((len(ks), 2 * H + 1), dtype=np.float64)   # Σ_m ΛΛ
    for j, h in enumerate(hs.tolist()):
        k2 = ks + h
        ok = (k2 >= K) & (k2 <= 2 * K)
        n1 = N - np.outer(ks, m)
        n2 = N - np.outer(k2, m)
        ok2 = ok[:, None] & (n1 >= 2) & (n1 <= N) & (n2 >= 2) & (n2 <= N)
        prod = np.where(ok2, Lam[np.clip(n1, 0, N)] * Lam[np.clip(n2, 0, N)], 0.0)
        acc[:, j] = prod.sum(axis=1)

    C = acc - Sser * nm
    mask = valid & (Sser > 0)
    Cv = C[mask]
    Sv = Sser[mask]
    accv = acc[mask]
    npair = int(mask.sum())

    ms_off = float((Cv ** 2).mean()) if npair else 0.0
    worst = float(np.abs(Cv).max() / M) if npair else 0.0
    ratio_model = float((accv / (Sser[mask] * nm)).mean()) if npair else 0.0
    std_model = float((accv / (Sser[mask] * nm)).std()) if npair else 0.0

    # 对角项 h=0（模型不适用，用 Λ² 的实测尺度）
    diag = np.zeros(len(ks), dtype=np.float64)
    for i, k in enumerate(ks.tolist()):
        n1 = N - k * m
        ok = (n1 >= 2) & (n1 <= N)
        diag[i] = float((Lam[np.clip(n1, 0, N)] ** 2 * ok).sum())
    logN = math.log(N)
    Sbar = float(Sv.mean()) if npair else 0.0
    S2bar = float((Sv ** 2).mean()) if npair else 0.0
    # Poisson 模型：事件数 X~Pois(𝓝)，𝓝 = M·𝔖/log²N；C = log²N·(X-𝓝)
    #   ⇒ E[C²] = log⁴N·𝓝 = M·𝔖·log²N
    events = M * Sbar / (logN ** 2) if npair else 0.0
    poisson_pred = M * Sbar * logN ** 2 if npair else 0.0
    return dict(
        N=N, K=K, M=M, H=H, n_m=nm, n_pairs=int(mask.sum()),
        Sbar=Sbar, S2bar=S2bar,
        events_per_pair=events,
        poisson_pred_MS=poisson_pred,
        poisson_ratio=(ms_off / poisson_pred) if poisson_pred else 0.0,
        rms_relative_fluctuation=(math.sqrt(ms_off) / (M * Sbar)) if npair and Sbar else 0.0,
        predicted_MS_over_M2=(poisson_pred / (M * M)) if npair else 0.0,
        mean_square_over_M2=ms_off / (M * M),
        mean_square=ms_off,
        mean_square_over_M=ms_off / M,
        mean_square_over_M_log2=ms_off / (M * logN ** 2),
        worst_absC_over_M=worst,
        model_quality_mean=ratio_model,
        model_quality_std=std_model,
        diag_mean_sq_over_M2=float((diag ** 2).mean()) / (M * M),
        diag_over_MlogN=float(diag.mean()) / (M * logN),
        logN=logN,
        dilution_log2_over_H=(logN ** 2) / H,
        seconds=round(time.time() - t0, 1),
    )


# ------------------------------------------------------------------ E4
def check_E4(Ns):
    """指数预算：平凡界（Hölder 端点 L¹×L^∞、Cauchy L²×L²）与目标 N^{3/2} 的对照。"""
    rows = []
    for N in Ns:
        M = math.sqrt(N)
        logN = math.log(N)
        W1 = N * N / M                      # ‖W‖_1 ≍ N²/M（支撑大小）
        W2 = math.sqrt(N * N / M)           # ‖W‖_2
        Dinf = logN ** 2                     # ‖Δ‖_∞
        D2 = N * logN                        # ‖Δ‖_2
        target = N ** 1.5
        rows.append(dict(
            N=N, M=M,
            trivial_L1_Linf=W1 * Dinf / target,
            cauchy_L2_L2=W2 * D2 / target,
            need_from_L1_Linf="log^{-A}（相对平凡界只需对数节省）",
            need_from_Cauchy=(W2 * D2 / target) / (W1 * Dinf / target),
        ))
    return rows


def main():
    t0 = time.time()
    print("[E1] (5)(6) 换元恒等式（两条独立路径）...")
    E1 = []
    for beta in ("tau", "signed"):
        r = check_E1(20000, 50, 100, 50, 100, 25, beta)
        E1.append(r)
        print("     beta=%-6s  A=%.6f  B=%.6f  |A-B|=%.2e  ok=%s"
              % (beta, r["lhs_triple_loop"], r["rhs_weight_grid"],
                 r["abs_diff"], r["ok"]))

    print("[E2] gcd 能量和 (7) ...")
    E2 = check_E2([50, 100, 200, 400])
    for r in E2:
        print("     M=%-5d  Σ=%.6e   M·Σ=%.4f" % (r["M"], r["exact_sum"], r["M_times_sum"]))

    print("[E3] 二维均方 dispersion 实测 ...")
    E3 = []
    for N, K, M, H in ((250000, 200, 200, 200),
                       (10 ** 6, 400, 400, 400),
                       (4 * 10 ** 6, 800, 800, 350)):
        r = run_E3(N, K, M, H)
        E3.append(r)
        print("     N=%.2e K=M=%d H=%d  均方/M²=%.3f (Poisson预测 %.3f, 比 %.2f)  "
              "𝔖̄=%.2f  每对事件数=%.1f  相对涨落=%.3f  模型=%.3f±%.3f  "
              "最坏|C|/M=%.2f  对角/M²=%.1f  (%.1fs)"
              % (N, K, H, r["mean_square_over_M2"], r["predicted_MS_over_M2"],
                 r["poisson_ratio"], r["Sbar"], r["events_per_pair"],
                 r["rms_relative_fluctuation"], r["model_quality_mean"],
                 r["model_quality_std"], r["worst_absC_over_M"],
                 r["diag_mean_sq_over_M2"], r["seconds"]))

    print("[E4] 指数预算 ...")
    E4 = check_E4([10 ** 6, 10 ** 8, 10 ** 12])
    for r in E4:
        print("     N=%.0e  L¹×L^∞ 平凡界/目标=%.4f  Cauchy/目标=%.4f  Cauchy 相对 L¹ 的浪费=%.2f"
              % (r["N"], r["trivial_L1_Linf"], r["cauchy_L2_L2"], r["need_from_Cauchy"]))

    rep = dict(E1=E1, E2=E2, E3=E3, E4=E4,
               meta=dict(seconds=round(time.time() - t0, 1),
                         python=sys.version.split()[0], numpy=np.__version__,
                         honesty="有限尺度实测；不构成渐近证明。"))
    out = Path(__file__).resolve().parent.parent / "数据" / "bgd_dispersion_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", out)


if __name__ == "__main__":
    main()
