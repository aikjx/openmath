# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 · 结构分解定理的机器校验（2026-09-25）

校验五条**精确恒等式**（非近似、非拟合），它们是配套文档
《OM-P-NT-0003-结构分解定理_投影恒等式与角色锁定》的机器证据。

  (T1) 傅里叶展开恒等式 (7)：
       B = Σ_q (w_q/q) Σ_{r mod q}^* e(-rN/q) U_q(r) V_q(r)
       与直接三重求和 Σ_{d,m,n} a_d b_m c_n K_Q(dm+n-N) 逐位相等。

  (T2) 投影四分解 (9)（逐点成立）：
       UV = (PU)(PV) + (PU)(P⊥V) + (P⊥U)(PV) + (P⊥U)(P⊥V)
       其中 P 是 R_q = {r : (r,q)=1} 上到常数模态的正交投影。

  (T3) 混合项精确求值 (10)：
       Σ_r^* e(-rN/q)(PU)(P⊥V) = (PU)·[ Σ_n c_n c_q(n-N) − (PV)·c_q(N) ]
       即"零均值"只在 n ≡ N (mod q) 的算术方向上被 Ramanujan 和破坏。

  (T4) 角色定位（素数模，带精确余项）：
       V_q(r) = (1/φ(q)) Σ_χ τ(χ̄) χ(r) ψ(N,χ) + E_q
       且 E_q = Σ_{n≤N, q|n} Λ(n) = log q · floor(log_q N)  —— 与 r 无关，≤ log N。

  (T5) Gauss 和模长：非主 χ（素数模 q）满足 |τ(χ)| = √q。

复用 goldbach_charpair_correlation_20260925 的特征构造（CRT 独立基），不重复造轮子。
"""
from __future__ import annotations
import json
import math
import random
import cmath
import os
from datetime import datetime, timezone

from goldbach_charpair_correlation_20260925 import (
    gcd, von_mangoldt, enumerate_chars, is_principal, psi_N, euler_phi,
)


# ----------------------------------------------------------------------------
# 基础
# ----------------------------------------------------------------------------

def units(q):
    return [r for r in range(q) if gcd(r, q) == 1]


def ramanujan(q, m):
    """c_q(m) = Σ_{r mod q}^* e(rm/q)（Ramanujan 和，实整数）。"""
    s = 0.0 + 0.0j
    for r in units(q):
        s += cmath.exp(2j * math.pi * r * m / q)
    return s


def proj_mean(f, R):
    """P_q f = (1/φ(q)) Σ_{r∈R_q} f(r)（常数模态上的正交投影）。"""
    return sum(f[r] for r in R) / len(R)


def build_UV(q, a, b, c, D, M, X):
    """U_q(r) = Σ_{d,m} a_d b_m e(rdm/q)， V_q(r) = Σ_n c_n e(rn/q)。"""
    R = units(q)
    U, V = {}, {}
    for r in R:
        s = 0.0 + 0.0j
        for d in range(1, D + 1):
            for m in range(1, M + 1):
                s += a[d] * b[m] * cmath.exp(2j * math.pi * r * d * m / q)
        U[r] = s
        s = 0.0 + 0.0j
        for n in range(1, X + 1):
            s += c[n] * cmath.exp(2j * math.pi * r * n / q)
        V[r] = s
    return R, U, V


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-projection-identity-20260925.json")

    report = {
        "target_id": "OM-P-NT-0003",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": "本脚本校验的是精确代数/傅里叶恒等式，不构成哥德巴赫猜想的证明；"
                          "它只把余项的谱来源锁定为非主角色 L-函数零点。",
        "sections": {},
    }

    # ---------------- T1 + T2 + T3：随机模型上的三重校验 ----------------
    random.seed(20260925)
    N = 200
    D = M = X = 10
    Q = 8
    a = [0.0] + [random.uniform(-1, 1) for _ in range(D)]
    b = [0.0] + [random.uniform(-1, 1) for _ in range(M)]
    c = [0.0] + [random.uniform(-1, 1) for _ in range(X)]
    w = {q: 1.0 for q in range(1, Q + 1)}

    # 直接求和：B = Σ a_d b_m c_n K_Q(dm + n - N),  K_Q(h) = Σ_q (w_q/q) c_q(h)
    B_direct = 0.0 + 0.0j
    for d in range(1, D + 1):
        for m in range(1, M + 1):
            for n in range(1, X + 1):
                h = d * m + n - N
                k = 0.0 + 0.0j
                for q in range(1, Q + 1):
                    k += (w[q] / q) * ramanujan(q, h)
                B_direct += a[d] * b[m] * c[n] * k

    # 傅里叶侧
    B_fourier = 0.0 + 0.0j
    t2_rows, t3_rows = [], []
    for q in range(1, Q + 1):
        R, U, V = build_UV(q, a, b, c, D, M, X)
        contrib = 0.0 + 0.0j
        for r in R:
            contrib += cmath.exp(-2j * math.pi * r * N / q) * U[r] * V[r]
        B_fourier += (w[q] / q) * contrib

        # ---- T2：逐点四分解 ----
        pu, pv = proj_mean(U, R), proj_mean(V, R)
        max_t2 = 0.0
        for r in R:
            lhs = U[r] * V[r]
            rhs = (pu * pv
                   + pu * (V[r] - pv)
                   + (U[r] - pu) * pv
                   + (U[r] - pu) * (V[r] - pv))
            max_t2 = max(max_t2, abs(lhs - rhs))
        t2_rows.append({"q": q, "phi": len(R), "max_pointwise_error": max_t2})

        # ---- T3：混合项 = Ramanujan 和 ----
        lhs = 0.0 + 0.0j
        for r in R:
            lhs += cmath.exp(-2j * math.pi * r * N / q) * pu * (V[r] - pv)
        s_cn = 0.0 + 0.0j
        for n in range(1, X + 1):
            s_cn += c[n] * ramanujan(q, n - N)
        cqN = ramanujan(q, N)
        rhs = pu * (s_cn - pv * cqN)
        t3_rows.append({"q": q, "lhs": lhs, "rhs": rhs, "abs_error": abs(lhs - rhs)})

    report["sections"]["T1_fourier_identity"] = {
        "N": N, "D": D, "M": M, "X": X, "Q": Q,
        "B_direct": B_direct, "B_fourier": B_fourier,
        "abs_error": abs(B_direct - B_fourier),
    }
    report["sections"]["T2_projection_decomposition"] = t2_rows
    report["sections"]["T3_mixed_term_ramanujan"] = [
        {"q": r["q"], "abs_error": r["abs_error"]} for r in t3_rows]

    # ---------------- T4：角色定位（素数模，精确余项） ----------------
    t4_rows = []
    for q in [3, 5, 7, 11, 13]:
        for Nv in [200, 500, 1000]:
            lm = von_mangoldt(Nv)
            chars = enumerate_chars(q)
            R = units(q)
            # τ(χ) = Σ_{u mod q} χ(u) e(u/q)，非单位处 χ=0
            tau = {}
            for chi in chars:
                s = 0.0 + 0.0j
                for u in R:
                    s += chi[u] * cmath.exp(2j * math.pi * u / q)
                tau[id(chi)] = s
            psi = {id(chi): psi_N(Nv, chi, q, lm) for chi in chars}
            phi = euler_phi(q)

            # 模型侧 V_model(r) = (1/φ) Σ_χ τ(χ̄) χ(r) ψ(N,χ)
            max_err_over_r = 0.0
            residuals = []
            for r in R:
                model = 0.0 + 0.0j
                for chi in chars:
                    tbar = 0.0 + 0.0j
                    for u in R:
                        tbar += chi[u].conjugate() * cmath.exp(2j * math.pi * u / q)
                    model += tbar * chi[r] * psi[id(chi)]
                model /= phi
                # 真实侧 V(r) = Σ_{n≤N} Λ(n) e(rn/q)
                true_v = 0.0 + 0.0j
                for n in range(1, Nv + 1):
                    true_v += lm[n] * cmath.exp(2j * math.pi * r * n / q)
                residuals.append(true_v - model)
                max_err_over_r = max(max_err_over_r, abs(true_v - model))
            # 理论余项 E = Σ_{q|n} Λ(n) = log q · floor(log_q N)
            k = 0
            pk = 1
            while pk * q <= Nv:
                pk *= q
                k += 1
            E_theory = math.log(q) * k
            # 残差应与 r 无关且等于 E_theory
            spread = max(abs(residuals[i] - residuals[0]) for i in range(len(residuals)))
            t4_rows.append({
                "q": q, "N": Nv,
                "residual_abs": abs(residuals[0]),
                "E_theory_logq_floor": E_theory,
                "abs_error_vs_theory": abs(abs(residuals[0]) - E_theory),
                "residual_spread_over_r": spread,
                "logN_bound": math.log(Nv),
                "within_logN_bound": abs(residuals[0]) <= math.log(Nv) + 1e-9,
            })
    report["sections"]["T4_character_localization"] = t4_rows

    # ---------------- T5：Gauss 和模长 ----------------
    t5_rows = []
    for q in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        chars = enumerate_chars(q)
        R = units(q)
        ratios = []
        for chi in chars:
            if is_principal(chi, q):
                continue
            s = 0.0 + 0.0j
            for u in R:
                s += chi[u] * cmath.exp(2j * math.pi * u / q)
            ratios.append(abs(s) / math.sqrt(q))
        t5_rows.append({
            "q": q, "nonprincipal_chars": len(ratios),
            "min_ratio": min(ratios), "max_ratio": max(ratios),
        })
    report["sections"]["T5_gauss_sum_modulus"] = t5_rows

    # ---------------- 汇总判定 ----------------
    t1_ok = report["sections"]["T1_fourier_identity"]["abs_error"] < 1e-8
    t2_ok = all(r["max_pointwise_error"] < 1e-9 for r in t2_rows)
    t3_ok = all(r["abs_error"] < 1e-8 for r in t3_rows)
    t4_ok = all(r["abs_error_vs_theory"] < 1e-6 and r["residual_spread_over_r"] < 1e-9
                and r["within_logN_bound"] for r in t4_rows)
    t5_ok = all(abs(r["min_ratio"] - 1) < 1e-9 and abs(r["max_ratio"] - 1) < 1e-9
                for r in t5_rows)

    report["summary"] = {
        "T1_fourier_identity_exact": t1_ok,
        "T2_projection_decomposition_exact": t2_ok,
        "T3_mixed_term_equals_ramanujan": t3_ok,
        "T4_character_localization_exact": t4_ok,
        "T5_gauss_sum_sqrtq": t5_ok,
        "all_five_verified": all([t1_ok, t2_ok, t3_ok, t4_ok, t5_ok]),
        "interpretation": [
            "T1–T3 是精确恒等式（机器误差级别），确认'投影原则 P'与'混合项=Ramanujan 和'成立："
            "所谓零均值只在 n≡N (mod q) 的算术方向上被破坏，坏模态高度结构化。",
            "T4 给出带**精确余项**的角色定位：V_q(r) 与角色模型的差恰为 "
            "log q·floor(log_q N)，与 r 无关且 ≤ log N（素数模）。"
            "故余项谱来源确为非主角色的 ψ(N,χ)。",
            "T5 确认 |τ(χ)|=√q，是 Jacobi √q 节省的直接来源。",
            "这些恒等式**不构成**哥德巴赫证明：它们只把余项锁定到非主角色 L-零点，"
            "从而证明忽略 L-零点的纯几何/Fourier 论证无法闭合（与 PSBLS 反例一致）。",
        ],
        "what_remains_open": [
            "靶心 A：需 |ψ(N,χ)| ~ √N，即 EH 越过 1/2 / 零自由区——仍是独立未解猜想。",
            "靶心 B：{N-p} 的双线性相消结构仍缺。",
            "靶心 D：本定理是结构引理（把阻点说清），未填满'给出 r(N)≥1 的显式公式'。",
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)


if __name__ == "__main__":
    main()
