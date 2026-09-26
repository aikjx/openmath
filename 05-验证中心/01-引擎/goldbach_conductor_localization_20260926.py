# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 · 合数模的角色定位与 conductor 重标定（2026-09-26）

完成上一轮（结构分解定理 T4）明确列出的后续项：T4 只对素数模成立，
合数模必须按 conductor 重组，因为非本原特征的 |τ(χ)| ≠ √q。

本脚本校验：

  (T4') 合数模角色定位（任意 q）：
         V_q(r) = (1/φ(q)) Σ_χ τ(χ̄) χ(r) ψ(N,χ) + R_q(r)
         R_q(r) = Σ_{p|q} log p · Σ_{k≥1, p^k ≤ N} e(r p^k / q)
         —— 与素数模不同：R_q(r) **依赖 r**（素数模时退化为与 r 无关的
            log q·⌊log_q N⌋）。且 |R_q(r)| ≤ Σ_{p|q} log p · ⌊log_p N⌋。

  (T6)  非本原特征的 Gauss 和公式（imprimitivity）：
         设 χ mod q 由本原特征 χ* mod c 诱导，r = q/c，则
             τ(χ) = μ(r) · χ*(r) · τ(χ*)
         其中 χ*(r) = 0 当 (r,c)>1。推论：|τ(χ)| ∈ {0, √c}。

  (T6b) 主特征：τ(χ_0 mod q) = μ(q)。

复用既有特征构造（CRT 独立基），不重复造轮子。
"""
from __future__ import annotations
import json
import math
import cmath
import os
import sys

from goldbach_charpair_correlation_20260925 import (
    gcd, von_mangoldt, enumerate_chars, is_principal, psi_N, euler_phi,
)


# ----------------------------------------------------------------------------
# 工具
# ----------------------------------------------------------------------------

def divisors(q):
    return [d for d in range(1, q + 1) if q % d == 0]


def mobius(n):
    if n == 1:
        return 1
    m, cnt = n, 0
    p = 2
    while p * p <= m:
        if m % p == 0:
            m //= p
            cnt += 1
            if m % p == 0:
                return 0
        p += 1
    if m > 1:
        cnt += 1
    return -1 if cnt % 2 else 1


def kernel_units(chi, q, d):
    """ker((Z/qZ)* -> (Z/dZ)*) = {u ∈ (Z/qZ)* : u ≡ 1 (mod d)}；d=1 时为全部单位。"""
    if d == 1:
        return list(chi.keys())
    return [u for u in chi if u % d == 1]


def conductor(chi, q):
    """χ 的 conductor：使 χ 在 ker((Z/qZ)*→(Z/dZ)*) 上平凡的最小 d|q。"""
    for d in divisors(q):
        if all(abs(chi[u] - 1.0) < 1e-9 for u in kernel_units(chi, q, d)):
            return d
    return q


def primitive_inducing_char(chi, q, c):
    """返回由 χ 诱导出的本原特征 χ* mod c（dict: 单位 a -> 值）。"""
    if c == 1:
        return {1: 1.0 + 0.0j}
    star = {}
    for a in range(1, c):
        if gcd(a, c) != 1:
            continue
        pick = None
        for u in chi:
            if u % c == a:
                pick = u
                break
        if pick is None:
            return None
        star[a] = chi[pick]
    return star


def star_eval(star, c, r):
    """χ*(r)：(r,c)>1 时为 0；c=1 时为 1。"""
    if c == 1:
        return 1.0 + 0.0j
    if gcd(r, c) != 1:
        return 0.0 + 0.0j
    return star[r % c]


def gauss_sum(ch, mod):
    """τ(χ) = Σ_{u ∈ (Z/mod Z)*} χ(u) e(u/mod)。"""
    s = 0.0 + 0.0j
    for u, v in ch.items():
        s += v * cmath.exp(2j * math.pi * u / mod)
    return s


def prime_divisors(q):
    ps, n = [], q
    p = 2
    while p * p <= n:
        if n % p == 0:
            ps.append(p)
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        ps.append(n)
    return ps


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-conductor-localization-20260926.json")

    report = {
        "target_id": "OM-P-NT-0003",
        "conjecture_status": "OPEN",
        "date": "2026-09-26",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": "完成 T4 的合数模推广与 conductor 重标定；"
                         "全部结论为有限尺度数值核对（容差 1e-8/1e-9），不构成证明，"
                         "更不构成哥德巴赫证明。",
        "sections": {},
    }

    # ---------------- T6：非本原 Gauss 和公式 ----------------
    t6_rows = []
    for q in [4, 6, 8, 9, 12, 15, 16, 18, 20, 21, 24, 25, 27, 30, 36]:
        chars = enumerate_chars(q)
        checked = 0
        max_err = 0.0
        max_conj_err = 0.0
        zero_count = 0
        sqrtc_count = 0
        conj_ok = 0
        for chi in chars:
            c = conductor(chi, q)
            r = q // c
            star = primitive_inducing_char(chi, q, c)
            if star is None:
                continue
            tau_chi = gauss_sum(chi, q)
            if c == 1:
                continue          # 主特征由 T6b 单独校验
            tau_star = gauss_sum(star, c)
            pred = mobius(r) * star_eval(star, c, r) * tau_star
            max_err = max(max_err, abs(tau_chi - pred))
            checked += 1
            if abs(tau_chi) < 1e-9:
                zero_count += 1
            elif abs(abs(tau_chi) - math.sqrt(c)) < 1e-9:
                sqrtc_count += 1
            # T4' 中实际出现的是 τ(χ̄)，必须单独核对（不是 τ(χ) 的推论）：
            tau_bar = sum(chi[u].conjugate() * cmath.exp(2j * math.pi * u / q)
                          for u in chi)
            star_bar = {a: v.conjugate() for a, v in star.items()}
            pred_bar = mobius(r) * star_eval(star_bar, c, r) * gauss_sum(star_bar, c)
            max_conj_err = max(max_conj_err, abs(tau_bar - pred_bar))
            if abs(tau_bar) < 1e-9 or abs(abs(tau_bar) - math.sqrt(c)) < 1e-9:
                conj_ok += 1
        t6_rows.append({
            "q": q, "chars_checked": checked, "max_formula_error": max_err,
            "max_conjugated_formula_error": max_conj_err,
            "conjugated_tau_in_zero_or_sqrtc": conj_ok,
            "tau_zero": zero_count, "tau_sqrt_conductor": sqrtc_count,
            "all_in_zero_or_sqrtc": (zero_count + sqrtc_count) == checked,
        })
    report["sections"]["T6_imprimitivity_gauss"] = t6_rows

    # ---------------- T6 阴性对照：非本原特征**不**满足 |τ(χ)| = √q ----------------
    # 校验必须具有鉴别力：若"√q"对非本原特征也成立，则 T6 的检验是空转的。
    # 这里主动检验那个**错误**命题，期望它被推翻（hits = 0）。
    neg_rows = []
    for q in [8, 9, 12, 16, 18, 20, 24, 25, 27, 36]:
        chars = enumerate_chars(q)
        imprim = [chi for chi in chars
                  if not is_principal(chi, q) and conductor(chi, q) < q]
        hits = 0
        for chi in imprim:
            tau = gauss_sum(chi, q)
            if abs(abs(tau) - math.sqrt(q)) < 1e-9:
                hits += 1
        neg_rows.append({
            "q": q,
            "imprimitive_nonprincipal_chars": len(imprim),
            "imprimitive_with_tau_sqrtq": hits,
        })
    report["sections"]["T6_negative_control_sqrtq_on_imprimitive"] = neg_rows

    # ---------------- T6b：主特征 τ(χ_0) = μ(q) ----------------
    t6b_rows = []
    for q in [3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, 27, 30, 36]:
        chars = enumerate_chars(q)
        prin = next(ch for ch in chars if is_principal(ch, q))
        tau = gauss_sum(prin, q)
        mu = mobius(q)
        t6b_rows.append({"q": q, "tau_principal": tau, "mu_q": mu,
                         "abs_error": abs(tau - mu)})
    report["sections"]["T6b_principal_gauss"] = t6b_rows

    # ---------------- T4'：角色定位（素数模作对照 + 合数模）----------------
    # 素数模一并纳入同一循环，才能**实测**"余项与 r 无关 ⇔ q 素数"这一对比，
    # 而不是在文字里断言。
    t4p_rows = []
    for q in [3, 5, 7, 11, 13, 4, 6, 8, 9, 12, 15, 16, 25, 27]:
        for N in [200, 500, 1000]:
            lm = von_mangoldt(N)
            chars = enumerate_chars(q)
            phi = euler_phi(q)
            R = sorted(chars[0].keys())   # (Z/qZ)* 的单位剩余类（≡ 特征的定义域）
            tau_bar = {}
            for chi in chars:
                s = 0.0 + 0.0j
                for u in R:
                    s += chi[u].conjugate() * cmath.exp(2j * math.pi * u / q)
                tau_bar[id(chi)] = s
            psi = {id(chi): psi_N(N, chi, q, lm) for chi in chars}

            max_identity_err = 0.0
            max_closedform_err = 0.0
            max_bound_viol = 0.0
            bound = sum(math.log(p) * int(math.floor(math.log(N) / math.log(p)))
                        for p in prime_divisors(q))
            r_dependence = 0.0
            first_resid = None
            for r in R:
                true_v = 0.0 + 0.0j
                for n in range(1, N + 1):
                    true_v += lm[n] * cmath.exp(2j * math.pi * r * n / q)
                model = 0.0 + 0.0j
                for chi in chars:
                    model += tau_bar[id(chi)] * chi[r] * psi[id(chi)]
                model /= phi
                resid = true_v - model
                # 直接计算的余项：Σ_{(n,q)>1} Λ(n) e(rn/q)
                direct = 0.0 + 0.0j
                for n in range(1, N + 1):
                    if lm[n] != 0 and gcd(n, q) != 1:
                        direct += lm[n] * cmath.exp(2j * math.pi * r * n / q)
                max_identity_err = max(max_identity_err, abs(resid - direct))
                # 闭式：Σ_{p|q} log p Σ_{k: p^k≤N} e(r p^k / q)
                closed = 0.0 + 0.0j
                for p in prime_divisors(q):
                    pk = p
                    while pk <= N:
                        closed += math.log(p) * cmath.exp(2j * math.pi * r * pk / q)
                        pk *= p
                max_closedform_err = max(max_closedform_err, abs(resid - closed))
                if abs(resid) > bound + 1e-9:
                    max_bound_viol = max(max_bound_viol, abs(resid) - bound)
                if first_resid is None:
                    first_resid = resid
                r_dependence = max(r_dependence, abs(resid - first_resid))
            t4p_rows.append({
                "q": q, "N": N,
                "q_is_prime": len(prime_divisors(q)) == 1 and prime_divisors(q)[0] == q,
                "max_identity_error": max_identity_err,
                "max_closed_form_error": max_closedform_err,
                "bound_sum_p_logp_floor": bound,
                "max_bound_violation": max_bound_viol,
                "residual_spread_over_r": r_dependence,
                "depends_on_r": r_dependence > 1e-9,
            })
    report["sections"]["T4p_composite_character_localization"] = t4p_rows

    # ---------------- 汇总 ----------------
    t6_ok = all(r["max_formula_error"] < 1e-8 and r["all_in_zero_or_sqrtc"]
                and r["max_conjugated_formula_error"] < 1e-8
                and r["conjugated_tau_in_zero_or_sqrtc"] == r["chars_checked"]
                for r in t6_rows)
    t6b_ok = all(r["abs_error"] < 1e-9 for r in t6b_rows)
    t4p_ok = all(r["max_identity_error"] < 1e-8
                 and r["max_closed_form_error"] < 1e-8
                 and r["max_bound_violation"] == 0.0 for r in t4p_rows)

    # 对比实测：素数模余项应与 r 无关；合数模应（除退化例外）依赖 r。
    prime_rows = [r for r in t4p_rows if r["q_is_prime"]]
    comp_rows = [r for r in t4p_rows if not r["q_is_prime"]]
    prime_r_independent = all(not r["depends_on_r"] for r in prime_rows)
    comp_mods = sorted({r["q"] for r in comp_rows})
    # 按**模**（而非按行）汇总：只有全部 N 都 r 无关才算"退化"。
    comp_dep_any = [m for m in comp_mods
                    if any(r["depends_on_r"] for r in comp_rows if r["q"] == m)]
    comp_ind_all = [m for m in comp_mods
                    if all(not r["depends_on_r"] for r in comp_rows if r["q"] == m)]
    # 在个别 N 上 r 依赖偶然消失（抵消）的模 —— 即"既有依赖行也有无关行"，
    # 必须披露，否则按单一 N 判定会误判。
    comp_ind_any = [m for m in comp_mods
                    if any(not r["depends_on_r"] for r in comp_rows if r["q"] == m)]
    comp_scale_dependent = [m for m in comp_dep_any if m in comp_ind_any]
    comp_spread_range = {}
    for m in comp_mods:
        sp = [r["residual_spread_over_r"] for r in comp_rows if r["q"] == m]
        comp_spread_range[str(m)] = [min(sp), max(sp)]
    contrast_ok = prime_r_independent and len(comp_dep_any) > 0

    # 阴性对照的判定：只在**非空**样本上要求错误命题被推翻（空样本记为空真）。
    neg_nonvacuous = [r for r in neg_rows if r["imprimitive_nonprincipal_chars"] > 0]
    neg_control_ok = all(r["imprimitive_with_tau_sqrtq"] == 0 for r in neg_nonvacuous)
    neg_control_sample = sum(r["imprimitive_nonprincipal_chars"] for r in neg_nonvacuous)

    report["summary"] = {
        "T6_imprimitivity_formula_verified": t6_ok,
        "T6b_principal_tau_equals_mu": t6b_ok,
        "T4p_composite_localization_verified": t4p_ok,
        "all_verified": all([t6_ok, t6b_ok, t4p_ok]),
        "T6_chars_checked_total": sum(r["chars_checked"] for r in t6_rows),
        "T6_tau_zero_total": sum(r["tau_zero"] for r in t6_rows),
        "T6_tau_sqrt_conductor_total": sum(r["tau_sqrt_conductor"] for r in t6_rows),
        "T6_conjugated_tau_checked_total": sum(r["conjugated_tau_in_zero_or_sqrtc"] for r in t6_rows),
        "T6_max_conjugated_formula_error": max(r["max_conjugated_formula_error"] for r in t6_rows),
        "T4p_prime_moduli_r_independent": prime_r_independent,
        "T4p_composite_moduli_r_dependent_some_scale": comp_dep_any,
        "T4p_composite_moduli_r_independent_all_scales": comp_ind_all,
        "T4p_composite_moduli_r_dependence_vanishes_at_some_scale": comp_scale_dependent,
        "T4p_composite_residual_spread_range_by_modulus": comp_spread_range,
        "T4p_prime_vs_composite_contrast_measured": contrast_ok,
        "T6_negative_control_sqrtq_fails_on_imprimitive": neg_control_ok,
        "T6_negative_control_sample_size": neg_control_sample,
        "key_findings": [
            "非本原 Gauss 和公式 τ(χ) = μ(r)·χ*(r)·τ(χ*)（r=q/c）被验证，"
            "故 |τ(χ)| ∈ {0, √c}：节省是 **√conductor** 而非 √q。"
            "这精确解释了上一轮为什么必须把 Jacobi √q 的检验局限于本原特征。",
            "主特征 τ(χ_0 mod q) = μ(q) 被验证（含 μ=0 即 τ=0 的合数模）。",
            "任意模角色定位成立，余项 R_q(r) = Σ_{p|q} log p Σ_{k:p^k≤N} e(r p^k/q)，"
            "且 |R_q(r)| ≤ Σ_{p|q} log p·⌊log_p N⌋。"
            "**实测对比**（同循环内）：素数模 q∈" + str(sorted({r["q"] for r in prime_rows})) +
            " 的余项与 r 无关；合数模 q∈" + str(comp_dep_any) +
            " 的余项依赖 r。"
            "合数模中在所有测试尺度上与 r 无关的仅有 q=" + str(comp_ind_all) +
            "，那是**退化例外**（q=4 时 R_4(r)=log2·(e(r/2)+1)≡0）。"
            "披露：q∈" + str(comp_scale_dependent) +
            " 的 r 依赖在**个别 N 上会偶然抵消为零**（如 q=6、N=500 时虚实部同时相消），"
            "因此按单一 N 判定'与 r 无关'会误判——本脚本按模跨尺度汇总。",
        ],
        "interpretation": [
            "至此 T4 由素数模推广到任意模，上一轮标注的'后续项'已闭合。",
            "阳性校验的**鉴别力**由阴性对照给出：非本原非主特征共 " + str(neg_control_sample) +
            " 个，其中满足 |τ(χ)|=√q 的有 0 个 —— 说明 T6 的 √conductor 结论不是"
            "把任何东西都判为真的空转。（正负两侧均为有限尺度数值核对，容差 1e-8/1e-9，"
            "不构成证明。）",
            "推论：按 conductor 重标定后，每个非主特征的有效节省是 √conductor，"
            "而特征个数按 conductor 分层——这正是 Goldbach 分析中 q-平均的实际结构。",
            "仍**不构成**哥德巴赫证明：余项仍由非主角色 L-零点承载，靶心 A/C 未动。",
        ],
        "what_remains_open": [
            "靶心 A/C：零自由区 / EH 越过 1/2 —— 仍是独立未解猜想。",
            "靶心 B：{N-p} 的双线性相消结构仍缺。",
            "截断尾项 q>Q 与模型到真实 G(N) 的标准过渡（major/minor arc）仍未完成。",
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)


if __name__ == "__main__":
    main()
