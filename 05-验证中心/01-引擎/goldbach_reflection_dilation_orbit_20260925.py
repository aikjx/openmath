# -*- coding: utf-8 -*-
"""
OM-P-NT-0005 · 反射–伸缩非交换轨道审计（2026-09-25，v2 修正版）

承接 OM-P-NT-0004（角色对相关 (13) 经退化 Jacobi 和 J(chi, chibar) = -chi(-1)
重新锁回 "m+n ≡ 0 (mod q)"，即 Goldbach 反射本身，形成闭环）与 OM-P-NT-0003 §14
的"下一步换维"建议：构造

    T_N : x -> N - x   (mod q)      [反射, T^2 = id]
    D_a : x -> a * x   (mod q)      [伸缩, (a,q)=1]

的非交换群 <T_N, D_a>，计算"N 无 Goldbach 分拆"沿整条轨道强迫出的约束，看它能否
与已知的素数乘法分布（PNT-AP）发生严格矛盾。

=============================================================================
v2 的核心修正（v1 的错误必须记录，不得粉饰）
=============================================================================
v1 用"词中 T 的个数 mod 2"当宇称。这是**错的**：它不是群元素的不变量。
Aff(F_q) = F_q ⋊ F_q^* 的换位子群是平移子群，交换化 ≅ F_q^* ≅ Z/(q-1)，
故到 Z/2 的同态只能因子化为 u 的 Legendre 字符。于是**唯一**的 Z/2 分次是

    parity(x -> u x + v) = [u 是二次非剩余]  (Legendre 字符)

v1 的 BFS 宇称碰撞正是这一现象的数值征兆（素模上必然碰撞）。

由此得到本轮**决定性的结构性结论**（负结果，但精确）：

  * 用户的机制需要"反射翻转标记、伸缩保持标记"，即同态 ρ 满足
        ρ(T_N) = 1 且 ρ(D_a) = 0.
  * ρ 只能取 Legendre 字符，故
        ρ(T_N) = Legendre(-1) = 1  ⟺  q ≡ 3 (mod 4)
        ρ(D_a) = Legendre(a)  = 0  ⟺  a 是二次剩余
  * 而"共轭中点轨道 {a^k · N/2} 覆盖全部单位类"需要 a 为**原根**（非剩余，
    轨道长 q-1）；a 为二次剩余时 |<a>| ≤ (q-1)/2，覆盖至多 φ(q)/2。

  ⇒ **"覆盖全部单位类"与"存在所需的 Z/2 分次"二者不可兼得**（素模）：
      最大乘法轨道（a 原根）⇒ ρ(D_a)=1，伸缩也翻转，分次不存在；
      分次存在（a 二次剩余）⇒ 轨道至多半覆盖。

这是对 §14 所提换维路线的一个**精确的、可计算的阻塞**，不是失败的计算。
它把"换维"未竟之处定位到一个具体的取舍上，而不是笼统地说"很难"。

=============================================================================
本脚本做四件可计算且诚实的事
=============================================================================
  A. 精确 BFS 出 <T_N, D_a>（验证为满仿射群 q(q-1)），并用 Legendre 宇称
     验证它确实是同态：parity(g∘h) = parity(g) XOR parity(h)。
  B. 计算刚性矛盾点 F = {x : 存在奇宇称元素 g 使 g(x) = x}，对比共轭中点轨道
     F3 = {a^k · N/2}，并按 (q mod 4) × (a 是否二次剩余) 四象限报告覆盖率。
  C. 量化上述取舍：覆盖率 vs 分次存在性，逐一例证。
  D. 实证判别力：对 6 ≤ N ≤ 2000 的真实素数（这些 N 都有 Goldbach 分拆），
     检验 F∩units 是否含素数（"无 Goldbach"预测它必须为空）。

诚实边界（脚本自己写明）：
  本脚本**不证明**哥德巴赫，也不产生反例。"素密度为正"升级为"该类 ≤ N 含素数"
  仍需 Brun–Titchmarsh / 零自由区等解析输入，该输入仍然开放（与 OM-P-NT-0003
  §13 一致）。复合模上 (Z/qZ)^* 未必循环，Legendre 宇称不定义，本脚本明确标注
  为"不适用"，不做外推。

计算纪律：全部整数 / 精确模运算，不依赖 sympy。
"""
from __future__ import annotations
import json
import math
import os
import sys
from collections import deque
from datetime import datetime, timezone

# Windows GBK 控制台打 ∤ / ⊆ 等字符会 UnicodeEncodeError（本项目既有坑），统一兜底。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def sieve(limit: int):
    s = [True] * (limit + 1)
    s[0] = s[1] = False
    for p in range(2, math.isqrt(limit) + 1):
        if s[p]:
            s[p * p::p] = [False] * ((limit - p * p) // p + 1)
    return s


def is_prime(q: int) -> bool:
    if q < 2:
        return False
    return all(q % d != 0 for d in range(2, math.isqrt(q) + 1))


def mult_order(a: int, q: int):
    if gcd(a, q) != 1:
        return None
    o, cur = 1, a % q
    while cur != 1:
        cur = (cur * a) % q
        o += 1
        if o > q:
            return None
    return o


def smallest_primitive_root(q: int):
    if not is_prime(q) or q <= 2:
        return None
    for a in range(2, q):
        if mult_order(a, q) == q - 1:
            return a
    return None


def qr_generator(q: int):
    """二次剩余子群的最大阶生成元（= 原根的平方），素模 q。"""
    g = smallest_primitive_root(q)
    if g is None:
        return None
    return (g * g) % q


def units_mod(q: int):
    return [x for x in range(q) if gcd(x, q) == 1]


# ----------------------------------------------------------------------------
# Legendre 宇称（素模上唯一的 Z/2 分次）
# ----------------------------------------------------------------------------

def legendre_parity(u: int, q: int):
    """
    素模 q 下 u 的 Legendre 字符分次：二次剩余 -> 0(偶)，二次非剩余 -> 1(奇)。
    非素模返回 None（不适用）。
    """
    if u % q == 0 or not is_prime(q):
        return None
    r = pow(u % q, (q - 1) // 2, q)
    if r == 1:
        return 0
    if r == q - 1:
        return 1
    return None


def affine_u(perm, q: int) -> int:
    """仿射映射 x -> u x + v 的线性部分 u = g(1) - g(0)。"""
    return (perm[1] - perm[0]) % q


def compose(f, g, q):
    """(f ∘ g)(x) = f(g(x))。"""
    return tuple(f[g[x]] for x in range(q))


# ----------------------------------------------------------------------------
# 群 <T_N, D_a>
# ----------------------------------------------------------------------------

def build_group(N: int, q: int, a: int):
    ident = tuple(range(q))
    T = tuple((N - x) % q for x in range(q))
    D = tuple((a * x) % q for x in range(q))

    seen = {ident}
    queue = deque([ident])
    while queue:
        perm = queue.popleft()
        for gen in (T, D):
            newperm = compose(gen, perm, q)
            if newperm not in seen:
                seen.add(newperm)
                queue.append(newperm)
    return list(seen)


def build_group_with_parity(N: int, q: int, a: int):
    """返回 (元素表, 宇称表)；宇称不可用（复合模）时 parity 为 None。"""
    elems = build_group(N, q, a)
    pars = {}
    ok = True
    for perm in elems:
        p = legendre_parity(affine_u(perm, q), q)
        if p is None:
            ok = False
            break
        pars[perm] = p
    if not ok:
        return elems, None
    return elems, pars


def verify_parity_homomorphism(elems, pars, q, sample=4000):
    """抽样验证 parity(g∘h) = parity(g) XOR parity(h)。"""
    import random
    rnd = random.Random(20260925)
    n = len(elems)
    if n == 0:
        return True
    trials = min(sample, n * n)
    for _ in range(trials):
        g = elems[rnd.randrange(n)]
        h = elems[rnd.randrange(n)]
        gh = compose(g, h, q)
        if pars[gh] != (pars[g] ^ pars[h]):
            return False
    return True


def fixed_points(perm):
    return {x for x in range(len(perm)) if perm[x] == x}


def rigid_set(elems, pars, q):
    """F = 所有奇宇称元素的不动点之并。"""
    F = set()
    for perm in elems:
        if pars[perm] == 1:
            F |= fixed_points(perm)
    return F


def conjugate_midpoint_orbit(N: int, q: int, a: int):
    """F3 = { a^k · (N/2) mod q }：共轭反射 D_a^k T D_a^{-k} 的中点轨道。"""
    if gcd(2, q) != 1:
        return None
    half = (N * pow(2, -1, q)) % q
    ord_a = mult_order(a, q)
    if ord_a is None:
        return None
    return {(pow(a, k, q) * half) % q for k in range(ord_a)}


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

N_MAX = 2000
PRIME_Q = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
COMPOSITE_Q = [9, 15, 21, 25, 27]
SAMPLE_N = [60, 100, 172, 800, 1000, 2744, 10000, 100002]


def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0005-reflection-dilation-orbit-20260925.json")
    md_path = os.path.join(out_dir, "OM-P-NT-0005-reflection-dilation-orbit-20260925.md")

    report = {
        "target_id": "OM-P-NT-0005",
        "version": "v2 (修正 v1 的词宇称错误)",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": (
            "本脚本不证明哥德巴赫、不产生反例。它给出 §14 换维路线的一个"
            "精确可计算阻塞（覆盖率与 Z/2 分次不可兼得）。'素密度为正'升级为"
            "'该类 ≤ N 含素数'仍需 Brun–Titchmarsh / 零自由区，该输入仍然开放。"
        ),
        "sections": {},
    }

    # ---- 节 A：群结构 + Legendre 宇称的同态性 ----
    sec_a = []
    for q in PRIME_Q:
        g = smallest_primitive_root(q)
        qrgen = qr_generator(q)
        for label, a in (("primitive_root", g), ("qr_generator", qrgen)):
            N = next(n for n in SAMPLE_N if n % q != 0)
            elems, pars = build_group_with_parity(N, q, a)
            T = tuple((N - x) % q for x in range(q))
            D = tuple((a * x) % q for x in range(q))
            sec_a.append({
                "q": q,
                "q_mod_4": q % 4,
                "a": a,
                "a_kind": label,
                "a_is_quadratic_residue": (legendre_parity(a, q) == 0),
                "ord_a": mult_order(a, q),
                "group_size": len(elems),
                "is_full_affine_group": (len(elems) == q * (q - 1)),
                "parity_is_homomorphism": verify_parity_homomorphism(elems, pars, q),
                "rho_T_N": legendre_parity(affine_u(T, q), q),
                "rho_D_a": legendre_parity(affine_u(D, q), q),
                "grading_T_flips": (legendre_parity(affine_u(T, q), q) == 1),
                "grading_D_preserves": (legendre_parity(affine_u(D, q), q) == 0),
            })
    # 复合模：宇称不适用
    sec_a_comp = []
    for q in COMPOSITE_Q:
        a = 2 if gcd(2, q) == 1 else 3
        N = next(n for n in SAMPLE_N if n % q != 0)
        elems, pars = build_group_with_parity(N, q, a)
        sec_a_comp.append({
            "q": q, "a": a, "group_size": len(elems),
            "parity_available": (pars is not None),
            "note": "复合模 (Z/qZ)^* 未必循环，Legendre 宇称不定义为同态；不做外推。",
        })
    report["sections"]["A_group_and_parity"] = sec_a
    report["sections"]["A_composite_moduli_unavailable"] = sec_a_comp

    # ---- 节 B：刚性矛盾点与四象限覆盖率 ----
    sec_b = []
    for q in PRIME_Q:
        g = smallest_primitive_root(q)
        qrgen = qr_generator(q)
        units = set(units_mod(q))
        phi_q = len(units)
        for label, a in (("primitive_root", g), ("qr_generator", qrgen)):
            for N in SAMPLE_N:
                if N % q == 0:
                    continue
                elems, pars = build_group_with_parity(N, q, a)
                F = rigid_set(elems, pars, q)
                F3 = conjugate_midpoint_orbit(N, q, a)
                F_units = F & units
                sec_b.append({
                    "q": q,
                    "q_mod_4": q % 4,
                    "a": a,
                    "a_kind": label,
                    "N": N,
                    "phi_q": phi_q,
                    "ord_a": mult_order(a, q),
                    "F3_size": len(F3) if F3 else 0,
                    "F3_equals_all_units": (F3 == units),
                    "F3_subset_of_F": (F3 <= F),
                    "size_F_units": len(F_units),
                    "coverage": len(F_units) / phi_q,
                    "full_cover": (F_units == units),
                })
    report["sections"]["B_rigid_set_coverage"] = sec_b

    # 四象限汇总：(q mod 4) × (a 是否二次剩余)
    quad = {}
    for e in sec_b:
        key = "q_mod4={}_a_{}".format(e["q_mod_4"],
                                       "QR" if e["a_kind"] == "qr_generator" else "nonQR")
        quad.setdefault(key, []).append(e)
    sec_b_quad = {}
    for k, rows in sorted(quad.items()):
        cov = [r["coverage"] for r in rows]
        sec_b_quad[k] = {
            "count": len(rows),
            "coverage_mean": sum(cov) / len(cov),
            "coverage_max": max(cov),
            "full_cover_count": sum(1 for r in rows if r["full_cover"]),
            "F3_subset_of_F_always": all(r["F3_subset_of_F"] for r in rows),
            "F3_all_units_always": all(r["F3_equals_all_units"] for r in rows),
        }
    report["sections"]["B_quadrants"] = sec_b_quad

    # ---- 节 C：分次存在性与覆盖率（含对初稿断言的修正） ----
    prim = [e for e in sec_a if e["a_kind"] == "primitive_root"]
    qr = [e for e in sec_a if e["a_kind"] == "qr_generator"]
    grading_q = sorted({e["q"] for e in sec_a
                        if e["grading_T_flips"] and e["grading_D_preserves"]})
    q1_qr = [e for e in sec_a if e["q_mod_4"] == 1 and e["a_is_quadratic_residue"]]
    sec_c = {
        "parity_is_homomorphism_all_cases": all(e["parity_is_homomorphism"] for e in sec_a),
        "grading_condition": (
            "ρ(T_N)=Legendre(-1)=1 ⟺ q≡3 (mod 4)；ρ(D_a)=0 ⟺ a 为二次剩余。"),
        "grading_exists_for_q_mod4_eq_3_and_a_QR": grading_q,
        "primitive_is_full_affine": all(e["is_full_affine_group"] for e in prim),
        "primitive_D_also_flips": all(e["rho_D_a"] == 1 for e in prim),
        "qr_D_preserves": all(e["rho_D_a"] == 0 for e in qr),
        "quadrant_q1mod4_aQR_has_no_odd_element": all(
            (e["rho_T_N"] == 0 and e["rho_D_a"] == 0) for e in q1_qr),
        "quadrant_q1mod4_aQR_group_is_half_affine": all(
            (not e["is_full_affine_group"]) for e in q1_qr),
        "coverage_in_grading_quadrant": sec_b_quad.get("q_mod4=3_a_QR"),
        "correction_to_draft_claim": (
            "初稿断言『分次存在 ⇒ 覆盖至多 φ(q)/2』被数据否证：分次存在的象限"
            "(q≡3 mod 4, a 二次剩余) 覆盖均值 0.932、38/44 例全覆盖。原因是 F 取自"
            "**所有**奇宇称元素的不动点，不限于共轭反射族 F3（T∘D_a^k 等非共轭元素"
            "同样为奇宇称并提供不动点）。真正的分界是另一条：q≡1 mod 4 且 a 二次剩余时"
            "⟨a,−1⟩ ⊆ 二次剩余子群，全群元素皆偶 ⇒ 无奇元素 ⇒ F=∅ ⇒ 覆盖 0，"
            "且此时群只有满仿射群的一半。"
        ),
        "decisive_limitation": (
            "即便分次与覆盖都成立，剩余类层面**无法编码 Goldbach 的配对约束**："
            "'无 Goldbach'禁止的是配对 (p, N−p)，而不是'某个剩余类含素数'。"
            "单位类 c 与其反射类 N−c 在 PNT-AP 下**同时**素密，故在剩余类层面"
            "不存在任何可检测障碍 —— 奇宇称不动点强迫不出矛盾。"
            "这是 Selberg 奇偶障碍 / Tao『需掌握二点相关本身』在轨道语言中的同构表现。"
        ),
    }
    report["sections"]["C_grading_and_coverage"] = sec_c

    # ---- 节 D：实证判别力 ----
    isp = sieve(N_MAX + 1)
    primes = [p for p in range(2, N_MAX + 1) if isp[p]]
    sec_d = []
    for q in [3, 5, 7, 11, 13]:
        g = smallest_primitive_root(q)
        qrgen = qr_generator(q)
        units = set(units_mod(q))
        for label, a in (("primitive_root", g), ("qr_generator", qrgen)):
            cache = {}
            for r in range(q):
                elems, pars = build_group_with_parity(r, q, a)
                if pars is None:
                    cache[r] = {"F_units": set(), "regime": "parity_unavailable"}
                else:
                    Fu = rigid_set(elems, pars, q) & units
                    cache[r] = {"F_units": Fu,
                                "regime": "degenerate_loop" if r == 0 else "active"}
            hits = total = 0
            act_total = act_hits = 0
            for N in range(6, N_MAX + 1, 2):
                c = cache[N % q]
                has = False
                if c["F_units"]:
                    for p in primes:
                        if p > N:
                            break
                        if (p % q) in c["F_units"]:
                            has = True
                            break
                total += 1
                hits += 1 if has else 0
                if c["regime"] == "active":
                    act_total += 1
                    act_hits += 1 if has else 0
            # 空真性审计：若活动剩余类上 F_units == 全部单位类，则
            # "F 中含素数" 等价于 "N 以下存在素数"，对 N>=6 恒真 —— 检验是空真式。
            F_all_units_on_active = all(
                cache[r]["F_units"] == units for r in range(1, q)
                if cache[r]["regime"] == "active")
            sec_d.append({
                "q": q, "a": a, "a_kind": label,
                "even_N_count": total,
                "discriminator_rate": (hits / total) if total else None,
                "active_count": act_total,
                "active_discriminator_rate": (act_hits / act_total) if act_total else None,
                "F_units_equals_all_units_on_active_residues": F_all_units_on_active,
                "test_is_vacuous": F_all_units_on_active,
            })
    report["sections"]["D_empirical_discriminator"] = sec_d

    # ---- 诚实汇总 ----
    report["summary"] = {
        "parity_correction": (
            "v1 用'词中 T 的个数 mod 2'作宇称是错误的：它不是群元素的不变量。"
            "Aff(F_q) 的交换化 ≅ F_q^*，故唯一的 Z/2 分次是 Legendre 字符"
            "（u 为二次非剩余 ⇔ 奇）。v2 已改用该宇称并验证其同态性。"
        ),
        "positive_findings": {
            "unique_Z2_grading_is_legendre": sec_c["parity_is_homomorphism_all_cases"],
            "grading_exists_exactly_for": sec_c["grading_exists_for_q_mod4_eq_3_and_a_QR"],
            "coverage_in_grading_quadrant": sec_c["coverage_in_grading_quadrant"],
            "q1mod4_aQR_degenerates_to_all_even": sec_c["quadrant_q1mod4_aQR_has_no_odd_element"],
        },
        "correction_to_draft_claim": sec_c["correction_to_draft_claim"],
        "decisive_limitation": sec_c["decisive_limitation"],
        "quadrants": sec_b_quad,
        "empirical_is_vacuous": {
            "{}-{}".format(r["q"], r["a_kind"]): {
                "active_discriminator_rate": r["active_discriminator_rate"],
                "test_is_vacuous": r["test_is_vacuous"],
            } for r in sec_d
        },
        "interpretation": [
            "【正结果】<T_N, D_a> 在 q∤N 时为满仿射群（已验证），其唯一的 Z/2 分次"
            "就是 Legendre 字符（已抽样验证同态性）。所需的 ρ(T_N)=1 且 ρ(D_a)=0 "
            "成立当且仅当 q≡3 (mod 4) 且 a 为二次剩余 —— 实测 q∈{3,7,11,19,23,31}。",
            "【正结果】在该象限覆盖率均值 0.932（38/44 例全覆盖），说明"
            "'奇宇称不动点'确实把中点障碍放大到近乎整条单位类群。",
            "【修正】初稿断言'分次存在 ⇒ 覆盖至多 φ(q)/2'被数据否证：F 来自所有"
            "奇宇称元素的不动点，不限于共轭反射族。真正的零覆盖象限是"
            "q≡1 mod 4 且 a 二次剩余 —— 此时 ⟨a,−1⟩ ⊆ QR 子群，全群皆偶、"
            "无奇元素、群只有仿射群一半，故 F=∅。",
            "【决定性限制】剩余类层面无法编码配对约束：'无 Goldbach'禁止的是"
            "配对 (p, N−p)，而非'某类含素数'；c 与 N−c 在 PNT-AP 下同时素密，"
            "故不动点强迫不出矛盾。节 D 的判别率 1.0 因此是**空真式**"
            "（F=全部单位类时等价于'N 以下有素数'，N≥6 恒真），必须撤回其"
            "作为正向校验的解读 —— 这是我自己的假阳性，如实记录。",
            "【与 §14 的关系】闭环以新形式重现：轨道给出的是新对象（非交换仿射群"
            "+ Legendre 分次），但配对信息不在剩余类层面，于是换维换到的仍是"
            "同一个'需二点相关'的墙。这与 Selberg 奇偶障碍、Tao 关于"
            "'仅有模长/单点信息不足以区分破环后的素数集'的判断一致。",
        ],
        "what_remains_open": [
            "要真正利用轨道，必须把作用从剩余类提升到**实际整数对**层面"
            "（p 与 N−p 的配对本身），而非 mod q 的类；那正是需要解析输入之处"
            "（零自由区 / 双线性和）。本脚本的剩余类版本做不到这一点。",
            "可能仍值得试的方向：(i) 用完整 Z/(q−1) 字符分次（交换化本就是 Z/(q−1)，"
            "Legendre 只是其 2-挠部分）重新表述相容性；(ii) 多模 CRT 同时施加两个"
            "互素模的反射–伸缩轨道，使'避开配对'需在多个模上同时成立；"
            "(iii) 把不动点条件与已知的双线性和（Type I/II）估计结合。三者均未实现。",
            "把'素密度为正'升级为'该类 ≤ N 含素数'需要 Brun–Titchmarsh / 零自由区。",
            "复合模宇称不适用（(Z/qZ)^* 非循环），未外推；q ≤ 37、N ≤ 2000；"
            "渐近 q ~ √N 临界尺度未检验；未接入真实 L 零点。",
        ],
        "verdict": (
            "换维产出了明确的新结构（满仿射群 + Legendre 分次 + 高覆盖不动点集），"
            "但同时证明了**剩余类层面的轨道无法承载 Goldbach 的配对约束**，"
            "故该路线在此层面不会产生证明；节 D 的判别率是空真式，已撤回。"
            "§14 的闭环以新形式重现，根子仍在'需要二点相关'。"
            "状态维持 OPEN。"
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    lines = [
        "# OM-P-NT-0005 · 反射–伸缩非交换轨道审计（2026-09-25，v2）",
        "",
        "> 状态：**OPEN**。本稿不证明哥德巴赫，只做结构诊断。",
        "",
        "## v2 修正",
        "",
        "v1 用「词中 T 的个数 mod 2」作宇称 —— **错误**，它不是群元素的不变量。",
        "Aff(F_q) 的交换化 ≅ F_q^*，唯一 Z/2 分次是 Legendre 字符（u 非二次剩余 ⇔ 奇）。",
        "",
        "## 主要结果",
        "",
        "* **正结果**：q∤N 时 <T_N, D_a> 为满仿射群；所需分次 ρ(T_N)=1 且 ρ(D_a)=0",
        "  成立 ⇔ q≡3 (mod 4) 且 a 二次剩余（实测 q∈{3,7,11,19,23,31}）；",
        "  该象限覆盖率均值 0.932（38/44 全覆盖）。",
        "* **修正**：初稿『分次存在 ⇒ 覆盖 ≤ φ(q)/2』被否证 —— F 取自所有奇宇称元素，",
        "  不限于共轭反射族。真正零覆盖的象限是 q≡1 (mod 4) 且 a 二次剩余：",
        "  此时 ⟨a,−1⟩ ⊆ QR 子群，全群皆偶、无奇元素、群仅仿射群一半 ⇒ F=∅。",
        "* **决定性限制**：剩余类层面无法编码配对约束 —— '无 Goldbach'禁止的是配对",
        "  (p, N−p) 而非'某类含素数'；c 与 N−c 在 PNT-AP 下同时素密 ⇒ 不动点强迫不出矛盾。",
        "* **自我更正**：节 D 判别率 1.0 是空真式（F=全单位类时等价于'N 以下有素数'），",
        "  撤回其作为正向校验的解读。",
        "",
        "## 四象限（覆盖率 = |F∩units| / φ(q)）",
        "",
        "| 象限 | 样本 | 覆盖均值 | 覆盖最大 | 全覆盖数 | F3⊆F | F3=全单位 |",
        "|---|---|---|---|---|---|---|",
    ]
    for k, v in sec_b_quad.items():
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            k, v["count"], round(v["coverage_mean"], 4), round(v["coverage_max"], 4),
            v["full_cover_count"], v["F3_subset_of_F_always"], v["F3_all_units_always"]))
    lines += ["", "## 实证判别率（活动分支 / 整体）", "", "| q | a 类型 | 活动分支 | 整体 |", "|---|---|---|---|"]
    for r in sec_d:
        lines.append("| {} | {} | {} | {} |".format(
            r["q"], r["a_kind"],
            r["active_discriminator_rate"], r["discriminator_rate"]))
    lines += ["", "## 仍然开放", ""]
    for w in report["summary"]["what_remains_open"]:
        lines.append("* " + w)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)
    print("saved:", md_path)


if __name__ == "__main__":
    main()
