# -*- coding: utf-8 -*-
"""模型项（G2）与奇异级数闭式分解的核验。

背景：S = Σ_m |Σ_k β_k Λ(N-km)|² 展开后 = 对角项 + 模型项 + 𝓔_N，
其中模型项为
        𝓣_β = Σ_{0<|h|<H} Σ_{k~K} β_{k+h} β̄_k · (m 区间长度) · 𝔖(k,h).
原文只估了 𝓔_N。本脚本做三件事：

  G1  给出并验证 𝔖(k,h) 的**闭式分解**（此前只有逐素数 ν(p) 算法）：
        𝔖(k,h) = 𝔖_0(N)·1_{(k(k+h),N)=1}·Π_{p∤N}(1 + (1_{p|k}+1_{p|k+h}+1_{p|h}-1_{p|gcd(k,h)})/(p-2))
        𝔖_0(N) = Π_{p∤N}(1-1/(p-1)²)·Π_{p|N} p/(p-1)
      —— 把 𝔖 展成"除数型权重"的基底，是处理模型项的前提。
  G2  实测不同 β 下模型项的**抵消因子**
        κ_β = (Σ β_{k+h}β_k 𝔖) / (Σ |β_{k+h}β_k| 𝔖)
      β = 1, τ, Λ, μ, λ(Liouville)。κ_β ≍ 1 表示**无抵消**（模型项 = 平凡界）。
  G3  模型项相对目标 N^{3/2} 的实际占比（在当前可算尺度）。

红线：有限尺度数值；不构成渐近证明。
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def sieve(N):
    isp = np.ones(N + 1, dtype=bool)
    isp[:2] = False
    for i in range(2, math.isqrt(N) + 1):
        if isp[i]:
            isp[i * i::i] = False
    return isp


def coeff_arrays(n):
    """返回 k=0..n 上的 β 系数表：1, τ, Λ, μ, λ。"""
    isp = sieve(n)
    pr = np.nonzero(isp)[0].tolist()
    one = np.ones(n + 1, dtype=np.float64)
    tau = np.zeros(n + 1, dtype=np.float64)
    for d in range(1, n + 1):
        tau[d::d] += 1.0
    Lam = np.zeros(n + 1, dtype=np.float64)
    for p in pr:
        pa = int(p)
        lp = math.log(float(p))
        while pa <= n:
            Lam[pa] = lp
            pa *= int(p)
    mu = np.ones(n + 1, dtype=np.float64)
    mu[0] = 0.0
    for p in pr:
        mu[p::p] *= -1.0
        p2 = int(p) * int(p)
        if p2 <= n:
            mu[p2::p2] = 0.0
    om = np.zeros(n + 1, dtype=np.int64)
    for p in pr:
        pa = int(p)
        while pa <= n:
            om[pa::pa] += 1
            pa *= int(p)
    liou = np.where(om > 0, (-1.0) ** om, 0.0)
    one[0] = 0.0
    tau[0] = 0.0
    return dict(one=one, tau=tau, Lam=Lam, mu=mu, liou=liou)


def sser_nu(N, K0, K1, H, primes):
    """逐素数 ν(p) 算法（既有实现，作为对照）。"""
    ks = np.arange(K0, K1 + 1, dtype=np.int64)
    hs = np.arange(-H, H + 1, dtype=np.int64)
    KK, HH = np.meshgrid(ks, hs, indexing="ij")
    K2 = KK + HH
    valid = (K2 >= K0) & (K2 <= K1) & (HH != 0)
    S = np.ones(KK.shape, dtype=np.float64)
    for p in primes:
        d1 = (KK % p == 0)
        d2 = (K2 % p == 0)
        dN = (N % p == 0)
        dH = (HH % p == 0)
        z1 = np.where(d1, np.where(dN, p, 0), 1)
        z2 = np.where(d2, np.where(dN, p, 0), 1)
        inter = np.where(
            d1 & d2, np.where(dN, p, 0),
            np.where(d1, np.where(dN, z2, 0),
                     np.where(d2, np.where(dN, z1, 0),
                              np.where(dH | dN, 1, 0))))
        nu = z1 + z2 - inter
        S *= (1.0 - nu / p) / (1.0 - 1.0 / p) ** 2
    return np.where(valid, S, 0.0), ks, hs, valid


def sser_closed(N, K0, K1, H, primes):
    """闭式分解（G1）：𝔖_0(N)·1_{(k(k+h),N)=1}·Π_{p∤N}(1+(u+v+w-uvw)/(p-2))。"""
    ks = np.arange(K0, K1 + 1, dtype=np.int64)
    hs = np.arange(-H, H + 1, dtype=np.int64)
    KK, HH = np.meshgrid(ks, hs, indexing="ij")
    K2 = KK + HH
    valid = (K2 >= K0) & (K2 <= K1) & (HH != 0)
    S0 = 1.0
    adm = np.ones(KK.shape, dtype=bool)
    R = np.ones(KK.shape, dtype=np.float64)
    for p in primes:
        if N % p == 0:
            S0 *= p / (p - 1.0)
            adm &= (KK % p != 0) & (K2 % p != 0)
        else:
            S0 *= (1.0 - 1.0 / (p - 1.0) ** 2)
            u = (KK % p == 0)
            v = (K2 % p == 0)
            w = (HH % p == 0)
            R *= 1.0 + (u.astype(np.float64) + v.astype(np.float64)
                        + w.astype(np.float64)
                        - (u & v & w).astype(np.float64)) / (p - 2.0)
    S = np.where(valid & adm, S0 * R, 0.0)
    return S, S0, ks, hs, valid & adm


def run(N, K, H, P=4000):
    isp = sieve(max(N, 2 * K + H + 5))
    primes = [int(p) for p in np.nonzero(isp)[0] if p <= P]
    K0, K1 = K, 2 * K
    Snu, ks, hs, vnu = sser_nu(N, K0, K1, H, primes)
    Scl, S0, ks2, hs2, adm = sser_closed(N, K0, K1, H, primes)

    # G1：两种算法是否逐点一致
    diff = np.abs(Snu - Scl).max()
    rel = diff / max(1e-12, np.abs(Snu).max())

    betas = coeff_arrays(2 * K + H + 5)
    KK, HH = np.meshgrid(ks, hs, indexing="ij")
    K2 = KK + HH
    rows = []
    npair = int(adm.sum())
    Sbar = float(Scl[adm].mean()) if npair else 0.0
    for name in ("one", "tau", "Lam", "mu", "liou"):
        b = betas[name]
        B1 = b[KK]
        B2 = b[K2]
        num = float((B1 * B2 * Scl)[adm].sum())
        den = float((np.abs(B1 * B2) * Scl)[adm].sum())
        rows.append(dict(beta=name,
                         signed_sum=num,
                         abs_sum=den,
                         kappa=(num / den) if den else 0.0))
    # G3：模型项相对 N^{3/2}（m 区间长度取 K 尺度下的 M；此处用 M=K 的可比尺度）
    mlen = 2 * K + 1
    model_over_target = {}
    for r in rows:
        model_over_target[r["beta"]] = abs(r["signed_sum"]) * mlen / (N ** 1.5)
    return dict(N=N, K=K, H=H, S0=S0,
                max_abs_diff_nu_vs_closed=float(diff),
                rel_diff=float(rel),
                closed_form_ok=bool(rel < 1e-9),
                n_admissible_pairs=npair,
                n_all_pairs=int(((K2 >= K0) & (K2 <= K1) & (HH != 0)).sum()),
                Sbar=Sbar,
                betas=rows,
                model_over_N32=model_over_target)


def main():
    t0 = time.time()
    out = []
    for N, K, H in ((10 ** 6, 400, 400), (4 * 10 ** 6, 800, 400)):
        r = run(N, K, H)
        out.append(r)
        print("[G1] N=%.0e K=%d H=%d  闭式 vs ν(p) 算法: max|Δ|=%.3e  rel=%.2e  ok=%s"
              % (N, K, H, r["max_abs_diff_nu_vs_closed"], r["rel_diff"], r["closed_form_ok"]))
        print("     𝔖_0(N)=%.5f  可容许对数=%d / %d  𝔖̄=%.3f"
              % (r["S0"], r["n_admissible_pairs"], r["n_all_pairs"], r["Sbar"]))
        for b in r["betas"]:
            print("     β=%-5s  κ=%.5f   模型项/N^{3/2}=%.4f"
                  % (b["beta"], b["kappa"], r["model_over_N32"][b["beta"]]))
    rep = dict(runs=out, meta=dict(seconds=round(time.time() - t0, 1),
                                   python=sys.version.split()[0],
                                   numpy=np.__version__))
    p = Path(__file__).resolve().parent.parent / "数据" / "model_term_verification.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", p)


if __name__ == "__main__":
    main()
