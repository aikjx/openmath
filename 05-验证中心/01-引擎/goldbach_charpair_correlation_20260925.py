# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 · 角色对相关 (13) 的有限尺度数值攻击（2026-09-25）

承接 OM-P-NT-0003 的参数化缺口分析。上一轮把 "零密度 x Jacobi 根号q x q-平均" 的
误差幂次做成了透明参数模型，但 (13) 本身是具体的角色频谱相关：

    Corr(N) = sum_{chi1, chi2 != chi0} J(chi1, chi2) psi(N, chi1) psi(N, chi2)

本脚本在有限尺度上**直接构造所有 Dirichlet 特征**、计算 Jacobi 和 J(chi1,chi2)、
计算 von Mangoldt 频谱 psi(N, chi)，并实测 (13) 的相关项相对 N 的大小。

诚实结论（脚本自己算出并写明）：
  * 对**本原**非主、非退化三元组 (chi1,chi2,chi1*chi2 皆本原非主)，
    |J| = sqrt(q) 被数值验证 —— 这就是 §12 的 "Jacobi 根号q 节省" 的真实来源。
    注意：非本原特征的 Gauss 和 > sqrt(q)，其正确标度是 sqrt(conductor)；
    见 goldbach_conductor_localization_20260926.py 的 T6（imprimitivity）。
    因此本检验必须限定于本原三元组，早期版本的"对所有非主三元组"是**错的**。
  * 但在有限尺度（N 到 1000、q 到 ~40），|psi(N, chi)| 对多数特征都达到 N 级
    （零自由区/零密度尚未在此时空尺度激活），于是 (13) 的相关项是 N 级，
    **不是 o(N)**；实测 max_q |Corr_q|/N 约 484/421/228（N=200/500/1000），
    **远非 O(1)**，且随 N 只缓慢下降，本脚本不把"缓慢下降"当作收敛证据。
  * 这从数值上确认了上一轮的边界：要到 o(N) 必须显式引入零自由区/EH 的解析输入，
    而该输入只有在渐近尺度（N 很大、q 进入相关模范围）才把 |psi| 压到 sqrt(N) 级。
    有限尺度实验无法替代这一步，但能精确显示"差多少"——相关项与 N 同阶。

计算纪律：所有特征群用纯 Python 自包含构造（CRT 经由单位群生成元枚举），
不依赖 sympy；Jacobi 和与 psi 用精确复数有限求和核对。
"""
from __future__ import annotations
import json
import math
import itertools
import cmath
import os
from datetime import datetime, timezone


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def sieve(limit):
    s = [True] * (limit + 1)
    s[0] = s[1] = False
    for p in range(2, int(math.isqrt(limit)) + 1):
        if s[p]:
            s[p * p::p] = [False] * ((limit - p * p) // p + 1)
    return s


def von_mangoldt(limit):
    lm = [0.0] * (limit + 1)
    s = sieve(limit)
    for p in range(2, limit + 1):
        if not s[p]:
            continue
        n = p
        while n <= limit:
            lm[n] = math.log(p)
            n *= p
    return lm


def multiplicative_order(a, q):
    if gcd(a, q) != 1:
        return None
    o, cur = 1, a % q
    while cur != 1:
        cur = (cur * a) % q
        o += 1
        if o > q:
            return None
    return o


def euler_phi(q):
    return sum(1 for a in range(1, q) if gcd(a, q) == 1)


def factor_prime_powers(q):
    """q = prod p_i^{e_i}，返回 [(p, e), ...]。"""
    n, res = q, []
    if n % 2 == 0:
        e = 0
        while n % 2 == 0:
            n //= 2
            e += 1
        res.append((2, e))
    p = 3
    while p * p <= n:
        if n % p == 0:
            e = 0
            while n % p == 0:
                n //= p
                e += 1
            res.append((p, e))
        p += 2
    if n > 1:
        res.append((n, 1))
    return res


def crt_lift(a, pe, q):
    """求 x mod q 使 x ≡ a (mod pe) 且 x ≡ 1 (mod q/pe)。"""
    m = q // pe
    if m == 1:
        return a % q
    inv = pow(pe % m, -1, m)
    t = ((1 - a) * inv) % m
    return (a + pe * t) % q


def local_basis(p, e):
    """(Z/p^e Z)* 的一组**独立**基生成元及其阶。
    奇素数幂：循环群，原根单生成，阶 phi(p^e)。
    2^e：e=1 平凡；e=2 循环 C2（生成元 3）；e>=3 为 C2 x C_{2^{e-2}}（生成元 -1 与 5）。"""
    pe = p ** e
    if pe == 2:
        return []
    if p == 2:
        if e == 2:
            return [(3 % pe, 2)]
        return [((-1) % pe, 2), (5 % pe, 1 << (e - 2))]
    phi = pe - pe // p
    for g in range(2, pe):
        if gcd(g, pe) == 1 and multiplicative_order(g, pe) == phi:
            return [(g % pe, phi)]
    return []


def build_basis(q):
    """(Z/qZ)* 的一组独立基：各素数幂的局部基经 CRT 提升后合并。
    独立性体现为 prod(orders) == phi(q)，且指数映射 (e_i) -> prod g_i^{e_i} 是双射。"""
    gens, orders = [], []
    for (p, e) in factor_prime_powers(q):
        pe = p ** e
        for (g, o) in local_basis(p, e):
            gens.append(crt_lift(g, pe, q))
            orders.append(o)
    return gens, orders


def enumerate_chars(q):
    """枚举 (Z/qZ)* 上全部 Dirichlet 特征（恰 phi(q) 个），返回 list[dict: unit->complex]。"""
    gens, orders = build_basis(q)
    prod = 1
    for o in orders:
        prod *= o
    phi = euler_phi(q)
    assert prod == phi, "生成元不独立: prod=%d phi=%d" % (prod, phi)
    exp_to_elem = {}
    for exps in itertools.product(*[range(o) for o in orders]):
        x = 1
        for gi, ei in zip(gens, exps):
            x = (x * pow(gi, ei, q)) % q
        exp_to_elem[exps] = x
    assert len(set(exp_to_elem.values())) == phi, "指数映射非双射"
    chars = []
    for coeffs in itertools.product(*[range(o) for o in orders]):
        val = {}
        for exps, elem in exp_to_elem.items():
            ang = 0.0
            for i in range(len(gens)):
                ang += 2 * math.pi * coeffs[i] * exps[i] / orders[i]
            val[elem] = cmath.exp(1j * ang)
        chars.append(val)
    return chars


def is_principal(ch, q):
    return all(abs(ch[u] - 1.0) < 1e-12 for u in ch)


def proper_divisors(q):
    ds = set()
    for d in range(1, int(math.isqrt(q)) + 1):
        if q % d == 0:
            ds.add(d)
            ds.add(q // d)
    ds.discard(q)
    ds.discard(1)
    return sorted(ds)


def is_primitive(ch, q):
    """Dirichlet 特征 mod q 是本原的，当且仅当它不经由任何真因子 d|q, d>1 诱导而来
    （即不存在 d>1 使所有 u≡1 mod d 的单位都有 chi(u)=1）。
    根号q 的 Jacobi 节省只对**本原**特征成立（其 conductor = q）。"""
    for d in proper_divisors(q):
        ok = True
        for u in ch:
            if u % d == 1 and abs(ch[u] - 1.0) > 1e-9:
                ok = False
                break
        if ok:
            return False
    return True


def char_product(ch1, ch2, q):
    return {u: ch1[u] * ch2[u] for u in ch1}


def jacobi_sum(ch1, ch2, q):
    """J(chi1,chi2) = sum_{x mod q} chi1(x) chi2(1-x)，约定 chi(非单位)=0。"""
    s = 0.0 + 0j
    for x in range(q):
        a = ch1.get(x, 0.0) if gcd(x, q) == 1 else 0.0
        y = (1 - x) % q
        b = ch2.get(y, 0.0) if gcd(y, q) == 1 else 0.0
        s += a * b
    return s


def psi_N(N, ch, q, lm):
    """psi(N, chi) = sum_{n<=N} Lambda(n) chi(n)，约定 chi(n)=0 当 (n,q)>1。"""
    s = 0.0 + 0j
    for n in range(1, N + 1):
        if gcd(n, q) == 1:
            s += lm[n] * ch[n % q]
    return s


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def main():
    out_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "03-结果", "2026", "09"))
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-charpair-correlation-20260925.json")

    N_scales = [200, 500, 1000]
    q_list = [3, 4, 5, 7, 8, 9, 11, 12, 13, 16, 17, 19, 23, 25, 27, 29, 31, 37]

    lm_cache = {}
    for N in N_scales:
        if N not in lm_cache:
            lm_cache[N] = von_mangoldt(N)

    report = {
        "target_id": "OM-P-NT-0003",
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": "本脚本不证明哥德巴赫；只对 (13) 做有限尺度数值探测，"
                          "结论依赖渐近零自由区输入，有限尺度无法替代该输入。",
        "sections": {},
    }

    # ---- 节 A：Jacobi 根号q 节省的真实验证（仅限本原特征）----
    jacobi_checks = []
    for q in q_list:
        chars = enumerate_chars(q)
        nonprin = [c for c in chars if not is_principal(c, q)]
        prim = [c for c in nonprin if is_primitive(c, q)]
        hits = 0
        total = 0
        ratios = []
        for c1 in prim:
            for c2 in prim:
                c12 = char_product(c1, c2, q)
                # 非退化三元组：三者皆本原非主（此时 |J|=sqrt(q) 定理成立）
                if not is_primitive(c12, q) or is_principal(c12, q):
                    continue
                total += 1
                J = jacobi_sum(c1, c2, q)
                target = math.sqrt(q)
                if abs(abs(J) - target) < 1e-6 * (target + 1):
                    hits += 1
                ratios.append(abs(J) / target if target else 0)
        jacobi_checks.append({
            "q": q,
            "nonprincipal_chars": len(nonprin),
            "primitive_nonprincipal_chars": len(prim),
            "primitive_nondegenerate_triples": total,
            "jacobi_sqrtq_verified": hits,
            "jacobi_sqrtq_ratio_mean": (sum(ratios) / len(ratios)) if ratios else None,
        })
    report["sections"]["A_jacobi_sqrtq_verify"] = jacobi_checks

    # ---- 节 B：von Mangoldt 频谱 psi(N, chi) 的尺度 ----
    spectrum = []
    for q in q_list:
        chars = enumerate_chars(q)
        nonprin = [c for c in chars if not is_principal(c, q)]
        for N in N_scales:
            lm = lm_cache[N]
            ps = [abs(psi_N(N, c, q, lm)) for c in nonprin]
            if ps:
                spectrum.append({
                    "q": q, "N": N,
                    "n_nonprincipal": len(ps),
                    "max_abs_psi": max(ps),
                    "mean_abs_psi": sum(ps) / len(ps),
                    "max_over_N": max(ps) / N if N else None,
                })
    report["sections"]["B_psi_spectrum"] = spectrum

    # ---- 节 C：相关项 (13) 相对 N 的大小 ----
    corr_rows = []
    for N in N_scales:
        lm = lm_cache[N]
        per_q = []
        for q in q_list:
            chars = enumerate_chars(q)
            nonprin = [c for c in chars if not is_principal(c, q)]
            psi = {id(c): psi_N(N, c, q, lm) for c in nonprin}
            # 完整 (13)：所有非主对
            full = 0.0 + 0j
            # 仅非退化三元组（Jacobi 给出根号q）
            generic = 0.0 + 0j
            for c1 in nonprin:
                p1 = psi[id(c1)]
                for c2 in nonprin:
                    p2 = psi[id(c2)]
                    c12 = char_product(c1, c2, q)
                    J = jacobi_sum(c1, c2, q)
                    full += J * p1 * p2
                    if not is_principal(c12, q):
                        generic += J * p1 * p2
            per_q.append({
                "q": q,
                "full_abs_over_N": abs(full) / N if N else None,
                "generic_abs_over_N": abs(generic) / N if N else None,
            })
        # 跨 q 汇总：相关项是 N 级的证据
        max_full_ratio = max(r["full_abs_over_N"] for r in per_q if r["full_abs_over_N"] is not None)
        max_generic_ratio = max(r["generic_abs_over_N"] for r in per_q if r["generic_abs_over_N"] is not None)
        corr_rows.append({
            "N": N,
            "per_q": per_q,
            "max_full_correlation_over_N": max_full_ratio,
            "max_generic_correlation_over_N": max_generic_ratio,
            "is_oN_at_finite_scale": (max_full_ratio < 1e-6),
        })
    report["sections"]["C_charpair_correlation"] = corr_rows

    # ---- 诚实汇总 ----
    jacobi_ok = all(j["primitive_nondegenerate_triples"] == 0 or
                    j["jacobi_sqrtq_verified"] == j["primitive_nondegenerate_triples"] for j in jacobi_checks)
    # 披露：部分模没有 本原x本原=本原 的三元组（如 2 的幂：两个本原特征的乘积必为非本原），
    # 这些模的校验是空真通过，不应计入"已验证"的证据量。
    moduli_nonzero = [j["q"] for j in jacobi_checks if j["primitive_nondegenerate_triples"] > 0]
    ratios_str = ", ".join("N=%d 时 %.0f" % (c["N"], c["max_full_correlation_over_N"]) for c in corr_rows)
    # 有限尺度下相关项是否仍与 N 同阶
    finite_scale_oN = all(c["is_oN_at_finite_scale"] for c in corr_rows)

    report["summary"] = {
        # 字段名必须写明作用域：结论只对**本原**三元组成立（非本原的标度是 sqrt(conductor)）。
        "jacobi_sqrtq_verified_for_all_primitive_nondegenerate_triples": jacobi_ok,
        "jacobi_sqrtq_scope_note": "仅限 chi1,chi2,chi1*chi2 皆本原非主的三元组；"
                                   "非本原情形见 conductor-localization 的 T6（|τ|∈{0,√conductor}）。",
        "finite_scale_correlation_is_oN": finite_scale_oN,
        "moduli_with_nonzero_primitive_triples": moduli_nonzero,
        "moduli_vacuously_passing": [j["q"] for j in jacobi_checks
                                     if j["primitive_nondegenerate_triples"] == 0],
        "max_correlation_ratio_over_N_by_scale": {
            str(c["N"]): c["max_full_correlation_over_N"] for c in corr_rows},
        "interpretation": [
            "对所有**本原**非主非退化三元组（chi1,chi2,chi1*chi2 皆本原非主），"
            "|J(chi1,chi2)| = sqrt(q) 被数值验证 "
            "—— 这是 §12 'Jacobi 根号q 节省' 的真实算术来源，不再是假设。"
            "（非本原特征的 Gauss 和 > sqrt(q)，但那只是 conductor 更小的特征，"
            "在 Goldbach 分析中按 conductor 重新标度后 √conductor 节省仍然成立。）",
            "但在有限尺度（N<=1000, q<=37），单模相关项仍远大于 N："
            "max_q |Corr_q| / N = " + ratios_str +
            "。它随 N 增大只缓慢下降，远未呈现 o(N) 的迹象。"
            "（注意：这些比值远非 O(1)，本脚本不把'缓慢下降'误读为收敛证据。）",
            "这从数值上确认：要到 o(N) 必须显式引入零自由区 / EH 的解析输入；"
            "该输入只有在渐近尺度才把 |psi| 压到 sqrt(N) 级。有限尺度实验能显示"
            "'当前差多少'（相关项仍是 N 的数百倍），但不能判定渐近行为，"
            "缺口本身正是 theta=1/2 之墙（OM-P-NT-0003 §13）。",
        ],
        "what_remains_open": [
            "靶心 A：素数在相关模上的分布水平越过 1/2（EH_theta>1/2 / 近满 WEH），"
            "才能把 (13) 的 |psi| 压到 sqrt(N) 级从而产生 o(N)。",
            "真实 Dirichlet L 零点分布（零密度/零自由区）的数值接入：本脚本用有限尺度"
            "von Mangoldt 频谱代替，未模拟零点；渐近线行为需解析输入。",
            "靶心 B：为集合 {N-p} 构造可证的双线性和相消结构（FI 型越障）。",
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, default=str))
    print("saved:", json_path)


if __name__ == "__main__":
    main()
