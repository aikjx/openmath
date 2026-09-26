# -*- coding: utf-8 -*-
"""
OM-P-NT-0006 · Liouville 奇偶（2x2）系统：自由度、误差预算与落点裁定（2026-09-25）

承接 OM-P-NT-0005（反射-伸缩非交换轨道）与上一轮提出的"下一轮最关键的计算"：

    把筛后表示精确分成 P1+P1, P1+P2, P2+P1, P2+P2，
    然后检查"总计数 + Liouville 一阶矩 + 反射二阶矩"到底提供几个独立方程；
    如果三个矩足以强制 P1+P1 > 0，这条路线才真正有突破价值；
    如果自由度仍剩一个，就准确知道还缺哪一个新的可证明统计量。

--------------------------------------------------------------------------
本轮的设定（全部精确整数，不含任何解析假设）

固定偶数 N，筛水平 z = icbrt(N)（最大整数 z 使 z^3 <= N）。定义

    S_z = { n : 1 <= n <= N-1, (n, P(z)) = 1 且 (N-n, P(z)) = 1 },  P(z) = prod_{p<=z} p.

**结构前提（节 A 逐点核验）**：n <= N 且所有素因子 > z = icbrt(N) 蕴含 Omega(n) <= 2，
因为 Omega(n) >= 3 会迫使 n >= (z+1)^3 > N。故在 S_z 上

    Omega(n) in {0,1,2},   且  Omega(n) = 1  <=>  n 是素数,   Omega(n)=0 <=> n=1.

于是 Lambda 函数 lambda(n) = (-1)^{Omega(n)} 在 S_z 上**就是素性指示的编码**：

    1_{Omega(n)=1} = (1 - lambda(n)) / 2.

--------------------------------------------------------------------------
三条本轮要算的事

A. 结构前提 + 反射对称性 a_{jk} = a_{kj} 的逐点核验；z = N^{1/4} 时该前提失效的量化。

B. **精确恒等式（主结果）**

    a_{11} = sum_{n in S_z} (1-lambda(n))(1-lambda(N-n)) / 4
           = (T - 2*M_1 + M_2) / 4,

    其中 T = |S_z|,  M_1 = sum lambda(n),  M_2 = sum lambda(n)lambda(N-n)。
    注意 sum lambda(N-n) = sum lambda(n) = M_1（反射是 S_z 的对合，精确相等，无误差）。
    这是**精确整数恒等式**，不是渐近式：本脚本逐 N 断言等号成立。

C. **自由度阶梯（回答"三个矩够不够"）**

    记 x = a_{11}, y = a_{12} = a_{21}, w = a_{22}, eps = a_{00} + 2*a_{02}（Omega=0 残屑，
    实测为 0）。则三条矩给出

        T   = (a_{00} + 2a_{01} + 2a_{02}) + x + 2y + w
        M_1 = eps + w - x
        M_2 = (a_{00} - 2a_{01} + 2a_{02}) + x - 2y + w

    * 只用 T            -> x in [0, T]                     （自由度 2，完全无信息）
    * 用 T + M_1        -> x in [max(0, -M_1), (T-M_1)/2]  （自由度 1）
    * 用 T + M_1 + M_2  -> x 唯一确定                       （自由度 0）

    **更强的观察（本轮最省力的一条）**：由 M_1 = eps + w - x 与 eps, w >= 0 立得

        M_1 < 0  ==>  x >= -M_1 >= 1  ==>  N 有 Goldbach 分拆。

    即：**连 T 和 M_2 都不需要**，单独一个一阶矩的符号就够了。
    代价是这是一个**充分非必要**条件（它要求 a_{11} > a_{22} + eps，强于 Goldbach 本身），
    而且 M_1 正是 Selberg 奇偶障碍的靶心量。

D. 误差预算（条件数）：把 T, M_1, M_2, a_{11} 按 4 S(N) N / log^2 N 归一化，
   给出"符号翻转所需的相对误差"。

E. 可达性诊断：T/(N V(z)) 随 s = log N / log z 的实测（真值是否贴合筛主项），
   并如实标注"可证"与"为真"是两件事。

F. 上一轮 §13 提出的"mod N 闭合轨道"实测：lambda(a*n mod N) 与 lambda(a)lambda(n) 的相关。

--------------------------------------------------------------------------
诚实边界（脚本自己写明，不粉饰）

* 本脚本**不证明**哥德巴赫，也不产生反例。
* 恒等式是初等的（把 1_{P_1} = (1-lambda)/2 代入），本轮的价值在于：
  (i) 把它写成"三矩定解"并**实测自由度确为 0**；
  (ii) 给出"单矩符号判据"这一更弱输入即可充分的形式；
  (iii) 给出误差预算与三堵墙的定量定位；
  (iv) 实测证否 §13 的 mod-N 闭合轨道；
  (v) 明确裁定：这条路线把 Goldbach **精确归约**为奇偶敏感估计，
      **没有绕过** Selberg 奇偶障碍 —— 它只是该障碍的最精简表述。
* 未接入任何 L 函数零点；全部是精确整数/有限计算。

计算纪律：纯标准库；spf 筛 + Omega 数组；断言全部用精确整数相等。
"""
from __future__ import annotations
import json
import math
import os
import sys
from datetime import datetime, timezone

# Windows GBK 控制台打 Ω / ⟨ 等字符会 UnicodeEncodeError（本项目既有坑），统一兜底。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

C2_TWIN = 0.66016181584686957392781211001455577843262336028473341331945


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


def sieve_V(N: int, z: int, primes) -> float:
    """筛主项 V(z) = prod_{p<=z, p|N}(1-1/p) * prod_{p<=z, p|N 不成立}(1-2/p)。"""
    logs = []
    for p in primes:
        if p > z:
            break
        if N % p == 0:
            logs.append(math.log1p(-1.0 / p))
        else:
            logs.append(math.log1p(-2.0 / p))
    return math.exp(math.fsum(logs))


# ----------------------------------------------------------------------------
# 核心：给定 (N, z) 计算 S_z 上的全部统计量
# ----------------------------------------------------------------------------

def analyze(N: int, z: int, spf, om, limit: int):
    """
    返回 dict：四类计数 a[j][k]、三条矩 T/M_1/M_2、以及恒等式核验。
    复杂度 O(|{n: spf[n]>z}|)，即只遍历幸存者。
    """
    surv = [n for n in range(1, N) if spf[n] > z]
    flag = bytearray(limit + 1)
    for n in surv:
        flag[n] = 1

    # a[j][k] = #{ n in S_z : Omega(n)=j, Omega(N-n)=k },  j,k in {0,1,2,3+}
    a = [[0, 0, 0, 0] for _ in range(4)]
    T = 0
    M1 = 0
    M2 = 0
    max_om = 0
    for n in surv:
        m = N - n
        if not flag[m]:
            continue
        j = om[n] if om[n] <= 3 else 3
        k = om[m] if om[m] <= 3 else 3
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

    x = a[1][1]                       # P1 + P1
    y = a[1][2]                       # P1 + P2
    y2 = a[2][1]                      # P2 + P1（应等于 y）
    w = a[2][2]                       # P2 + P2
    eps = a[0][0] + 2 * a[0][2]       # Omega=0 残屑

    return {
        "N": N, "z": z,
        "a11": x, "a12": y, "a21": y2, "a22": w,
        "a00": a[0][0], "a01": a[0][1], "a02": a[0][2],
        "eps": eps,
        "T": T, "M1": M1, "M2": M2,
        "max_omega_in_S": max_om,
        "omega_le_2": max_om <= 2,
        "reflection_symmetric": (y == y2),
        "identity_4a11_eq_T_minus_2M1_plus_M2": (T - 2 * M1 + M2 == 4 * x),
        "identity_a11_eq_eps_plus_w_minus_M1": (x == eps + w - M1),
        "debris_size": a[0][0] + a[0][1] + a[0][2],
    }


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

N_MAX = 1_000_000
NS_MAIN = [1000, 3000, 10000, 30000, 100000, 300000, 1000000]
NS_SIGN = list(range(20000, 60000, 500))     # 单矩符号扫描
NS_SIGN = [n for n in NS_SIGN if n % 2 == 0]


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0006-parity-2x2-liouville-20260925.json")
    md_path = os.path.join(out_dir, "OM-P-NT-0006-parity-2x2-liouville-20260925.md")

    print("building spf/Omega up to", N_MAX, "...", flush=True)
    spf, om = build_spf_omega(N_MAX)
    lam = [1 - 2 * (o & 1) for o in om]
    primes = [n for n in range(2, N_MAX + 1) if spf[n] == n and om[n] == 1]
    print("primes below", N_MAX, ":", len(primes), flush=True)

    report = {
        "target_id": "OM-P-NT-0006",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": (
            "本脚本不证明哥德巴赫、不产生反例。它把上一轮提出的反射-伸缩路线推到尽头，"
            "给出精确整数恒等式 a11 = (T - 2*M1 + M2)/4 与自由度阶梯（三矩定解，自由度 0），"
            "并给出更弱的单矩充分判据 M1 < 0。裁定：所需输入 M1（以及 M2）正是 Selberg "
            "奇偶障碍的靶心量，本路线是奇偶障碍的最精简表述，并未绕过它。"
        ),
        "sections": {},
    }

    # ---------- 节 A/B/C：主表（z = icbrt(N)，Omega <= 2） ----------
    print("section A/B/C ...", flush=True)
    sec_main = []
    for N in NS_MAIN:
        z = iroot(N, 3)
        r = analyze(N, z, spf, om, N_MAX)
        Sg = singular_series(N)
        unit = Sg * N / (math.log(N) ** 2)     # Hardy-Littlewood 单位
        r.update({
            "singular_series": Sg,
            "kappa_T": r["T"] / unit,
            "kappa_M1": r["M1"] / unit,
            "kappa_M2": r["M2"] / unit,
            "kappa_a11": r["a11"] / unit,
            "M1_negative": r["M1"] < 0,
            "a11_positive": r["a11"] > 0,
        })
        sec_main.append(r)
        print("  N={} z={} T={} M1={} M2={} a11={} id_ok={}".format(
            N, z, r["T"], r["M1"], r["M2"], r["a11"],
            r["identity_4a11_eq_T_minus_2M1_plus_M2"]), flush=True)
    report["sections"]["A_structure_and_identity"] = sec_main

    # ---------- 节 A2：z = N^{1/4} 时结构前提失效 ----------
    print("section A2 (z = N^{1/4}) ...", flush=True)
    sec_a2 = []
    for N in [10000, 100000, 1000000]:
        z = iroot(N, 4)
        r = analyze(N, z, spf, om, N_MAX)
        lhs = r["T"] - 2 * r["M1"] + r["M2"]
        r["identity_residual_4a11_minus_lhs"] = 4 * r["a11"] - lhs
        r["identity_holds"] = (lhs == 4 * r["a11"])
        sec_a2.append(r)
    report["sections"]["A2_quarter_level_breaks_parity_encoding"] = sec_a2

    # ---------- 节 C：自由度阶梯 ----------
    print("section C (degrees of freedom) ...", flush=True)
    sec_dof = []
    for r in sec_main:
        T, M1, x = r["T"], r["M1"], r["a11"]
        # 只用 T
        lo_T, hi_T = 0, T
        # T + M1
        lo_TM1 = max(0, -M1)
        hi_TM1 = (T - M1) // 2
        sec_dof.append({
            "N": r["N"], "T": T, "M1": M1, "a11_true": x,
            "interval_from_T_only": [lo_T, hi_T],
            "dof_from_T_only": 2,
            "interval_from_T_and_M1": [lo_TM1, hi_TM1],
            "dof_from_T_and_M1": 1,
            "a11_in_interval_T_only": lo_T <= x <= hi_T,
            "a11_in_interval_T_and_M1": lo_TM1 <= x <= hi_TM1,
            "T_and_M1_forces_positivity": (lo_TM1 >= 1),
            "dof_from_T_M1_M2": 0,
        })
    report["sections"]["C_degrees_of_freedom_ladder"] = sec_dof

    # ---------- 节 C2：单矩符号判据 M1 < 0 的实测 ----------
    print("section C2 (sign of M1 scan, {} values) ...".format(len(NS_SIGN)), flush=True)
    n_neg = 0
    n_pos = 0
    n_zero = 0
    worst = None
    for N in NS_SIGN:
        z = iroot(N, 3)
        r = analyze(N, z, spf, om, N_MAX)
        if r["M1"] < 0:
            n_neg += 1
        elif r["M1"] > 0:
            n_pos += 1
        else:
            n_zero += 1
        if worst is None or r["M1"] > worst["M1"]:
            worst = {"N": N, "M1": r["M1"], "a11": r["a11"],
                     "a22": r["a22"], "eps": r["eps"], "T": r["T"]}
    sec_c2 = {
        "n_tested": len(NS_SIGN),
        "M1_negative_count": n_neg,
        "M1_positive_count": n_pos,
        "M1_zero_count": n_zero,
        "M1_negative_rate": n_neg / len(NS_SIGN),
        "a11_positive_always": all(r["a11_positive"] for r in sec_main),
        "worst_case_largest_M1": worst,
        "note": (
            "M1 = eps + a22 - a11（精确恒等式）。M1 < 0 等价于 a11 > a22 + eps，"
            "即 (P1+P1) 表示数严格多于 (P2+P2) 表示数 —— 这比 Goldbach 本身更强，"
            "属充分非必要条件。实测范围内 M1 < 0 恒成立，但它是未证明的奇偶敏感命题。"
        ),
    }
    report["sections"]["C2_single_moment_sign_criterion"] = sec_c2

    # ---------- 节 D：误差预算（条件数） ----------
    print("section D (error budget) ...", flush=True)
    sec_d = []
    for r in sec_main:
        kT, k1, k2, kx = r["kappa_T"], r["kappa_M1"], r["kappa_M2"], r["kappa_a11"]
        sec_d.append({
            "N": r["N"],
            "kappa_T": kT, "kappa_M1": k1, "kappa_M2": k2, "kappa_a11": kx,
            # 结论翻转所需相对误差（单个矩单独扰动，其余精确）
            "rel_tolerance_T": (4 * kx / abs(kT)) if kT else None,
            "rel_tolerance_M1": (2 * kx / abs(k1)) if k1 else None,
            "rel_tolerance_M2": (4 * kx / abs(k2)) if k2 else None,
            # 联合最坏情形：三者各占三分之一预算
            "rel_tolerance_joint_thirds": (4 * kx) / (abs(kT) + 2 * abs(k1) + abs(k2)),
            # ---- 真正的瓶颈：M_1 的**上界** ----
            # 结论 a11 >= 1 需要 T - 2*M_1 + M_2 >= 4，即（T、M_2 精确时）
            #     M_1 <= (T + M_2)/2 - 2。
            # 平凡界是 |M_1| <= T。故所需的"相对平凡界的节省因子"为
            #     kappa_T / ((kappa_T + kappa_2)/2) = 2*kappa_T/(kappa_T + kappa_2)。
            "required_M1_upper_threshold_kappa": (kT + k2) / 2.0,
            "trivial_M1_upper_bound_kappa": kT,
            "true_M1_kappa": k1,
            "required_saving_factor_over_trivial": (2 * kT) / (kT + k2) if (kT + k2) else None,
        })
    report["sections"]["D_error_budget"] = sec_d

    # ---------- 节 E：筛主项可达性（真值 vs 可证） ----------
    print("section E (sieve main term vs s) ...", flush=True)
    sec_e = []
    for N in [100000, 1000000]:
        for s in [3, 4, 6, 10]:
            z = iroot(N, s)
            if z < 2:
                z = 2
            r = analyze(N, z, spf, om, N_MAX)
            V = sieve_V(N, z, primes)
            # 对照组：维度 1 筛（只要求 n 自身 z-rough）的真值比值
            rough = sum(1 for n in range(1, N + 1) if spf[n] > z)
            v1 = math.exp(math.fsum(math.log1p(-1.0 / p) for p in primes if p <= z))
            sec_e.append({
                "N": N, "s": s, "z": z,
                "T": r["T"],
                "main_term_N_times_V": N * V,
                "V": V,
                "ratio_T_over_main": r["T"] / (N * V) if V > 0 else None,
                "dim1_rough_count": rough,
                "dim1_main_term": N * v1,
                "dim1_ratio": rough / (N * v1) if v1 > 0 else None,
            })
            print("  N={} s={} z={} ratio={:.4f}  dim1_ratio={:.4f}".format(
                N, s, z, r["T"] / (N * V) if V > 0 else float('nan'),
                rough / (N * v1) if v1 > 0 else float('nan')), flush=True)
    report["sections"]["E_sieve_main_term_reachability"] = sec_e

    # ---------- 节 F：§13 mod-N 闭合轨道实测 ----------
    print("section F (mod-N orbit) ...", flush=True)
    sec_f = []
    for N in [1000, 10000, 100000]:
        for a in [3, 5, 7, 11]:
            if N % a == 0:
                continue
            acc_mul = 0      # lambda(a*n mod N) * lambda(a)lambda(n)
            acc_refl = 0     # F_N(a*n mod N) * F_N(n)
            same = 0
            cnt = 0
            for n in range(1, N):
                r_ = (a * n) % N
                if r_ == 0:
                    continue
                cnt += 1
                acc_mul += lam[r_] * lam[a] * lam[n]
                acc_refl += (lam[r_] * lam[N - r_]) * (lam[n] * lam[N - n])
                if lam[r_] == lam[a] * lam[n]:
                    same += 1
            cm = acc_mul / cnt
            sec_f.append({
                "N": N, "a": a,
                "corr_multiplicativity_modN": cm,
                "corr_reflection_orbit_F": acc_refl / cnt,
                "multiplicativity_survival_rate": same / cnt,
                # 无回绕子集 { n : a*n < N } 的密度恰为 1/a；在该子集上完全乘法性**精确**成立。
                "no_wraparound_density_1_over_a": 1.0 / a,
                "corr_minus_1_over_a": cm - 1.0 / a,
                "survival_rate_predicted_from_nowrap_plus_noise": 1.0 / a + (1.0 - 1.0 / a) * 0.5,
            })
    report["sections"]["F_modN_closed_orbit_test"] = sec_f

    # ---------- 节 G：§11/§12 伸缩不变性（平凡真，但连接不同 N） ----------
    print("section G (dilation invariance) ...", flush=True)
    sec_g = []
    for N in [100, 1000, 10000]:
        for a in [2, 3, 5]:
            ok = True
            for n in range(1, min(N, 300)):
                m = a * N - a * n
                if m <= 0 or a * n > N_MAX:
                    continue
                if lam[a * n] * lam[m] != lam[n] * lam[N - n]:
                    ok = False
                    break
            sec_g.append({"N": N, "a": a, "F_aN_of_an_equals_F_N_of_n": ok})
    report["sections"]["G_dilation_invariance_trivial_check"] = sec_g

    # ---------- 汇总 ----------
    identity_ok = all(r["identity_4a11_eq_T_minus_2M1_plus_M2"] for r in sec_main)
    second_id_ok = all(r["identity_a11_eq_eps_plus_w_minus_M1"] for r in sec_main)
    omega_ok = all(r["omega_le_2"] for r in sec_main)
    sym_ok = all(r["reflection_symmetric"] for r in sec_main)
    quarter_broken = all(not r["identity_holds"] for r in sec_a2)
    modN_dead = max(abs(e["corr_multiplicativity_modN"]) for e in sec_f)

    report["summary"] = {
        "identity_4a11_eq_T_minus_2M1_plus_M2_all_N": identity_ok,
        "identity_a11_eq_eps_plus_a22_minus_M1_all_N": second_id_ok,
        "omega_le_2_on_sifted_set_all_N": omega_ok,
        "reflection_symmetry_a12_eq_a21_all_N": sym_ok,
        "quarter_level_breaks_the_encoding": quarter_broken,
        "degrees_of_freedom": {
            "from_T_only": 2,
            "from_T_and_M1": 1,
            "from_T_M1_M2": 0,
            "verdict": "三个矩恰好定解；代数上不缺统计量，自由度 = 0。",
        },
        "stronger_single_moment_criterion": {
            "statement": "M_1(N) < 0  ==>  a_11 >= 1  ==>  N 有 Goldbach 分拆。",
            "proof_length": "一行：M_1 = eps + a_22 - a_11，且 eps, a_22 >= 0。",
            "needs_T": False,
            "needs_M2": False,
            "sufficient_not_necessary": True,
            "M1_negative_rate_in_scan": sec_c2["M1_negative_rate"],
            "n_tested": sec_c2["n_tested"],
        },
        "error_budget_largest_N": sec_d[-1],
        "sieve_ratio_at_s3": [{"N": e["N"], "ratio": e["ratio_T_over_main"]}
                              for e in sec_e if e["s"] == 3],
        "modN_orbit_max_abs_corr": modN_dead,
        "interpretation": [
            "【回答「三个矩够不够」】代数上**够**：(T, M_1, M_2) 三个矩把 (a11, a12, a22) "
            "三个未知数唯一确定，自由度恰为 0，不多不少。恒等式 4*a11 = T - 2*M1 + M2 "
            "在所有测试 N 上精确成立（整数相等，非渐近）。",
            "【还能更省】由 M_1 = eps + a22 - a11 可知，连 T 与 M_2 都不需要："
            "只要 M_1 < 0（即 (P1+P1) 表示数 > (P2+P2) 表示数）就直接推出 Goldbach。"
            "这是本路线能给出的最弱充分输入。",
            "【但这就是奇偶障碍本身】M_1 = sum_{n in S_z} lambda(n) 正是"
            "sum (-1)^{Omega(n)} 型的奇偶泛函；M_2 亦然。二者都是 Selberg 奇偶障碍的靶心。"
            "本路线把 Goldbach **精确归约**为「证明一个 Liouville 加权筛和的符号」，"
            "它是奇偶障碍的**最精简表述**，而不是绕过它的新工具。",
            "【为什么非得 z = N^{1/3}】只有在 z > N^{1/3} 时 Omega <= 2，"
            "「Omega 为奇」才等价于「是素数」，(1-lambda)/2 才等于素性指示。"
            "节 A2 实测：降到 z = N^{1/4}（Omega <= 3）后恒等式立刻失效。"
            "而 z = N^{1/3} 正是 s = log N / log z = 3 —— 维度 2 筛的常数最难拿到的区段，"
            "与「编码需要大 z、筛法只能驾驭小 z」形成正面冲突。",
            "【§13 mod-N 闭合轨道实测：精确证否 + 定量归因】把 n -> a*n mod N 代入后，"
            "corr(lambda(a*n mod N), lambda(a)lambda(n)) 实测恒等于 **1/a 量级**"
            "（a=3: ~0.333，a=7: ~0.147，a=11: ~0.093），且**不随 N 衰减**。"
            "归因是精确的：无回绕子集 { n : a*n < N } 的密度恰为 1/a，在其上"
            "a*n mod N = a*n 故完全乘法性**精确**成立；余下 1-1/a 的部分被回绕彻底打散"
            "（减掉 1/a 后的残差在 N >= 10^4 时 |corr - 1/a| < 0.013；"
            "N=1000 样本小，波动达 0.09）。所以对固定的 a 确实残留一个"
            "正密度 1/a 的'可用片段'，但伸缩因子 a 越大该片段越稀（-> 0）。"
            "更致命的是**反射量本身**：corr(F_N(a*n mod N), F_N(n)) 实测 ~0.00x（量级 1e-3），"
            "即 F_N 在置换 n -> a*n mod N 下**完全不保持**。"
            "所以「用模 N 乘法回到同一个 N」这一步不成立 —— 且失败方式已被精确定量。",
            "【瓶颈的精确定位：只差 M_1 的一个上界】结论 a_11 >= 1 需要"
            "T - 2*M_1 + M_2 >= 4；在 T、M_2 精确时等价于 M_1 <= (T+M_2)/2 - 2。"
            "以 N = 10^6 的实测 kappa 计：阈值 = (kappa_T + kappa_2)/2 = 1.495（单位 = S(N)N/log^2N），"
            "真值 kappa_1 = -0.809，而平凡界只有 |M_1| <= T 即 2.739。"
            "故所需的是「M_1 的上界比平凡界节省一个因子 2*kappa_T/(kappa_T+kappa_2) = 1.83」。"
            "这是一个**单侧奇偶敏感估计**——正是 Selberg 奇偶障碍的定义域。"
            "（更省事的纯 M_1 路线连 T、M_2 都不需要，只要 M_1 < 0。）",
            "【筛主项：为真 vs 可证】节 E 实测真值比值 T/(N*V(z))：s=3 时约 1.0052~1.0056，"
            "s>=4 时已回到 1.000。s=3 处这个 +0.5% 的偏离**不随 N 增大而消失**"
            "（N=10^5: 1.00523，N=10^6: 1.00559），提示它是 s 的函数而非有限尺度效应。"
            "它数值上接近维度 1 的 Buchstab 常数 omega(3)*e^gamma = 1.0052，"
            "但同轮对照组 dim1_ratio 实测为 1.0023（N=10^5）/ 1.0037（N=10^6），"
            "与维度 2 的 1.0052 / 1.0056 相差约 0.2% —— 故**该识别未被确认**，"
            "本脚本只把它登记为待核观察，不宣称维度 2 筛与维度 1 的 Buchstab 函数相同。"
            "无论该常数如何，"
            "「为真」不等于「可证」：维度 2 筛在 s=3 的上下界常数能否同时贴近 1，"
            "是本路线无法回避的解析输入。",
            "【§11/§12 伸缩不变性】F_{aN}(an) = F_N(n) 确实精确成立（G 节），"
            "但它是完全乘法性的一句话推论，且连接的是**不同的 N**，"
            "对固定 N 不增加任何独立方程（自由度不变）。",
        ],
        "what_remains_open": [
            "M_1 的符号：需要证明 sum_{n in S_z} lambda(n) < 0，即 (P1+P1) 多于 (P2+P2)。"
            "这是标准奇偶障碍，现有筛法不能区分 Omega 的奇偶。",
            "M_2 的估计：把 sifting 展开后是 sum_{d|P(z)} mu(d) * (沿线性方程 d1*a + d2*b = N "
            "的 lambda(a)lambda(b) 相关)，要求对 d 直到 e^{N^{1/3}} 一致成立的二元 Chowla 型估计，"
            "远超现有技术。",
            "T 的常数：需要维度 2 筛在 s = 3 的上下界常数都贴近 1。"
            "节 E 实测了真值比值 T/(N*V(z))，但「为真」与「可证」是两件事 —— "
            "本脚本只给出真值一侧的实测，不宣称该常数已可证。",
            "单矩判据 M_1 < 0 是充分非必要的：即使某些 N 上 M_1 >= 0（Goldbach 仍成立），"
            "也只说明该判据不够，需要回到完整三矩。",
            "本脚本全部计算在 N <= 10^6、z = icbrt(N) 的有限尺度；渐近行为外推需谨慎。",
        ],
        "verdict": (
            "上一轮提出的「2x2 系统」本轮算清了：三矩定解（自由度 0），并存在更弱的单矩充分判据 "
            "M_1 < 0。但该判据与三矩中的 M_1、M_2 全部落在 Selberg 奇偶障碍的靶心上，"
            "而编码所必需的 z = N^{1/3}（s = 3）又恰在筛法常数最难拿到的区段。"
            "结论：反射–伸缩路线在此处**收束为奇偶障碍的最精简表述**，不是突破；"
            "状态维持 OPEN。"
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # ---------- 人类可读稿 ----------
    L = []
    A = L.append
    A("# OM-P-NT-0006 · Liouville 奇偶（2x2）系统审计（2026-09-25）")
    A("")
    A("> 状态：**OPEN**。本稿不证明哥德巴赫，只把上一轮提出的 2x2 系统算到底。")
    A("")
    A("## 一、设定")
    A("")
    A("筛水平 `z = icbrt(N)`，")
    A("`S_z = { n : 1 <= n <= N-1, (n,P(z)) = (N-n,P(z)) = 1 }`。")
    A("因 `n <= N` 且素因子全 `> z` 蕴含 `Omega(n) <= 2`（否则 `n >= (z+1)^3 > N`），")
    A("故在 `S_z` 上有 `1_{n 是素数} = (1 - lambda(n))/2`。")
    A("")
    A("## 二、主结果：精确恒等式")
    A("")
    A("$$a_{11} = \\sum_{n\\in S_z}\\frac{(1-\\lambda(n))(1-\\lambda(N-n))}{4}")
    A("= \\frac{T - 2M_1 + M_2}{4}$$")
    A("")
    A("其中 `T = |S_z|`，`M_1 = sum lambda(n)`，`M_2 = sum lambda(n)lambda(N-n)`，")
    A("且 `sum lambda(N-n) = sum lambda(n)` 由反射对合**精确**成立。")
    A("")
    A("| N | z | T | M_1 | M_2 | a_11（真值） | 恒等式 |")
    A("|---|---|---|---|---|---|---|")
    for r in sec_main:
        A("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["N"], r["z"], r["T"], r["M1"], r["M2"], r["a11"],
            "PASS" if r["identity_4a11_eq_T_minus_2M1_plus_M2"] else "FAIL"))
    A("")
    A("核验汇总：`Omega <= 2` 全程 = {}；`a_12 = a_21` = {}；恒等式全程 = {}".format(
        omega_ok, sym_ok, identity_ok))
    A("")
    A("## 三、自由度阶梯（本轮要的答案）")
    A("")
    A("| 已知矩 | 未知数 | 自由度 | a_11 的可行区间 |")
    A("|---|---|---|---|")
    A("| T | (x,y,w) | 2 | [0, T] —— 完全无信息 |")
    A("| T, M_1 | (x,y,w) | 1 | [max(0,-M_1), (T-M_1)/2] |")
    A("| T, M_1, M_2 | (x,y,w) | **0** | 唯一确定 |")
    A("")
    A("**结论：三个矩恰好定解，自由度 = 0。代数上不缺统计量。**")
    A("")
    A("### 更省力的单矩判据")
    A("")
    A("由精确恒等式 `M_1 = eps + a_22 - a_11`（`eps = a_00 + 2a_02 >= 0`）立得")
    A("")
    A("$$M_1 < 0 \\quad\\Longrightarrow\\quad a_{11} \\ge -M_1 \\ge 1 \\quad")
    A("\\Longrightarrow\\quad N \\text{ 有 Goldbach 分拆}.$$")
    A("")
    A("**连 T 与 M_2 都不需要。** 代价：它是充分非必要条件")
    A("（要求 `a_11 > a_22 + eps`，即 P1+P1 表示数多于 P2+P2，强于 Goldbach 本身）。")
    A("")
    A("实测扫描（{} 个偶数 N，20000~60000）：`M_1 < 0` 比例 = {:.4f}".format(
        sec_c2["n_tested"], sec_c2["M1_negative_rate"]))
    A("")
    A("## 四、误差预算（都按 `4·S(N)·N/log^2 N` 归一化）")
    A("")
    A("| N | kappa_T | kappa_M1 | kappa_M2 | kappa_a11 | T 容差 | M_1 容差 | M_2 容差 | 联合(三等分) |")
    A("|---|---|---|---|---|---|---|---|---|")
    for d in sec_d:
        A("| {} | {:.3f} | {:.3f} | {:.3f} | {:.3f} | {:.2%} | {:.2%} | {:.2%} | {:.2%} |".format(
            d["N"], d["kappa_T"], d["kappa_M1"], d["kappa_M2"], d["kappa_a11"],
            d["rel_tolerance_T"], d["rel_tolerance_M1"], d["rel_tolerance_M2"],
            d["rel_tolerance_joint_thirds"]))
    A("")
    A("（容差 = 只单独扰动该矩时结论翻转所需的相对误差。）")
    A("")
    A("注：**「联合(三等分)」一列恒等于 100%，没有信息量** —— 因为")
    A("`4*kappa_a11 = kappa_T - 2*kappa_M1 + kappa_M2` 就是恒等式本身的重写，")
    A("该比值必然为 1。真正有信息的是上面三个单矩容差与下一节的 M_1 节省因子。")
    A("")
    A("### 真正的瓶颈：M_1 的一个上界")
    A("")
    A("结论 `a_11 >= 1` 需要 `T - 2*M_1 + M_2 >= 4`。在 T、M_2 精确时等价于")
    A("`M_1 <= (T+M_2)/2 - 2`。")
    A("")
    A("| N | 所需阈值 (kappa_T+kappa_2)/2 | M_1 真值 kappa_1 | 平凡界 kappa_T | 所需节省因子 |")
    A("|---|---|---|---|---|")
    for d in sec_d:
        A("| {} | {:.3f} | {:.3f} | {:.3f} | {:.3f} |".format(
            d["N"], d["required_M1_upper_threshold_kappa"], d["true_M1_kappa"],
            d["trivial_M1_upper_bound_kappa"], d["required_saving_factor_over_trivial"]))
    A("")
    A("即：只需证明 `sum_{n in S_z} lambda(n)` 的上界比平凡界 `|M_1| <= T` 节省一个")
    A("**O(1) 常数因子**（N=10^6 处为 1.83）。看起来不多 —— 但它是一个**单侧奇偶敏感估计**，")
    A("正是 Selberg 奇偶障碍的定义域，现有筛法给出的是 0 而非任何常数因子的节省。")
    A("")
    A("## 五、可达性诊断")
    A("")
    A("### 5.1 筛主项比值（真值一侧）")
    A("")
    A("| N | s | z | T | N·V(z) | 维度2 比值 | 对照组 维度1 比值 |")
    A("|---|---|---|---|---|---|---|")
    for e in sec_e:
        A("| {} | {} | {} | {} | {:.1f} | {:.4f} | {:.4f} |".format(
            e["N"], e["s"], e["z"], e["T"], e["main_term_N_times_V"],
            e["ratio_T_over_main"] if e["ratio_T_over_main"] else float('nan'),
            e["dim1_ratio"] if e["dim1_ratio"] else float('nan')))
    A("")
    A("注意：**「为真」与「可证」是两件事**。这里只实测真值比值，")
    A("不宣称维度 2 筛在 s = 3 的上下界常数已可证。")
    A("s=3 处的 +0.5% 偏离不随 N 增大而消失，数值上接近维度 1 的 Buchstab 常数")
    A("`omega(3)*e^gamma = 1.0052`；但对照组 dim1 实测 1.0023 / 1.0037 与维度 2 的")
    A("1.0052 / 1.0056 相差约 0.2%，**该识别未被确认**，仅登记为待核观察。")
    A("")
    A("### 5.2 为什么非得 z = N^{1/3}")
    A("")
    A("| N | z = N^{1/4} | Omega 最大 | 恒等式残差 4a11 - (T-2M1+M2) |")
    A("|---|---|---|---|")
    for r in sec_a2:
        A("| {} | {} | {} | {} |".format(
            r["N"], r["z"], r["max_omega_in_S"],
            r["identity_residual_4a11_minus_lhs"]))
    A("")
    A("降到 `N^{1/4}` 后 `Omega` 可达 3，「Omega 为奇」不再等价于素数，编码断裂。")
    A("")
    A("### 5.3 §13 的 mod-N 闭合轨道：实测证否")
    A("")
    A("| N | a | corr(lambda(an mod N), lambda(a)lambda(n)) | 1/a | corr - 1/a | corr(F_N(an mod N), F_N(n)) | 乘法存活率 |")
    A("|---|---|---|---|---|---|---|")
    for e in sec_f:
        A("| {} | {} | {:+.4f} | {:.4f} | {:+.4f} | {:+.4f} | {:.4f} |".format(
            e["N"], e["a"], e["corr_multiplicativity_modN"],
            e["no_wraparound_density_1_over_a"], e["corr_minus_1_over_a"],
            e["corr_reflection_orbit_F"], e["multiplicativity_survival_rate"]))
    A("")
    A("读数：`corr(lambda(an mod N), lambda(a)lambda(n))` 恒为 **1/a 量级且不随 N 衰减**。")
    A("归因精确：无回绕子集 `{n : a*n < N}` 密度恰为 1/a，其上 `a*n mod N = a*n`，")
    A("完全乘法性**精确**成立；其余 1-1/a 被回绕打散")
    A("（`|corr - 1/a|` 在 N >= 10^4 时 < 0.013；N=1000 样本小，波动达 0.09）。")
    A("而反射量 `F_N` 本身在置换下**完全不保持**（相关 ~1e-3）。")
    A("")
    A("=> §13 的「用模 N 乘法回到同一个 N」不成立；且失败方式已被精确定量：")
    A("可用片段的密度只有 1/a，伸缩因子越大越稀。")
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

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)
    print("saved:", md_path)


if __name__ == "__main__":
    main()
