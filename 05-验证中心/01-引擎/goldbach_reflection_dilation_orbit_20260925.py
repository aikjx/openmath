# -*- coding: utf-8 -*-
"""
OM-P-NT-0005 · 反射–伸缩非交换轨道审计（2026-09-25）

承接 OM-P-NT-0004（角色对相关 (13) 经 Jacobi 退化 J(chi,chibar) = -chi(-1) 重新锁回
"m+n = 0 mod q"，即 Goldbach 反射本身，形成闭环）与 OM-P-NT-0003 §14 的"下一步换维"建议。

本轮构造
    T_N : x -> N - x   (mod q)          [反射, T^2 = id]
    D_a : x -> a * x   (mod q)          [伸缩, (a,q)=1, 阶 = ord_q(a)]
生成的非交换群 <T_N, D_a>，并计算"N 无 Goldbach 分拆"这一假设沿整条轨道强迫出的约束。

为什么这是"换维"而不是又绕回闭环 —— 本脚本给出的可计算判据：

  * 当 q | N：T_N(x) = N - x = -x (mod q)，反射退化为"乘以 -1"这一纯伸缩。
    此时 T 落在伸缩子群内，宇称（含 T 个数的奇偶）不再是良定义的同态，
    <T_N, D_a> 塌缩回乘法群 —— 这**正是** §13/§14 的 chi(-1) / 角色奇偶能量差闭环。
  * 当 q ∤ N：反射不是伸缩，<T_N, D_a> 是真正的非交换仿射群，宇称良定义，
    轨道逃出了角色 Fourier 闭环。这是真正的新维度。

本脚本做四件可计算且诚实的事：

  A. 精确 BFS 出 <T_N, D_a> 在 Z/qZ 上的作用，报告群阶、宇称子集大小、
     **退化性探测**（宇称碰撞次数，以及 T 是否已落在伸缩子群内）。
  B. 计算"刚性矛盾点" F = {x : 存在奇宇称元素 g 使 g(x) = x}，
     并验证共轭反射族 F3 = { a^k * (N/2) mod q } ⊆ F。
     —— 这就是把"单一中点 N/2"放大成"一整条伸缩轨道"的具体机制。
  C. 过定度：|F ∩ (Z/qZ)^*| / phi(q)。非退化情形下常常 = 1
     （整条单位类群都被强迫为"配对自由"）。
  D. 实证判别力：对 6 <= N <= N_MAX 的真实素数（这些 N 都有 Goldbach 分拆），
     检验 F ∩ units 是否含素数。"无 Goldbach"预测它必须为空；真相是它总含素数，
     故该方法确实能"抓住"真相 —— 这是对方法的正向校验，不是对猜想的反证。

诚实边界（脚本自己写明，不粉饰）：
  本脚本**不证明**哥德巴赫，也不产生反例。它把 §14 的闭环定位为一个精确的
  可计算条件（q | N 退化），并给出非退化情形下的过定结构。把"素密度为正"
  升级为"该类 <= N 含至少一个素数"仍需 Brun–Titchmarsh / 零自由区等解析输入，
  这与 OM-P-NT-0003 §13 的诊断一致，是仍然开放的一步。

计算纪律：全部整数 / 精确模运算，不依赖 sympy；宇称由 BFS 词长给出并做碰撞检测。
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
    """素模 q 的最小原根（非素模返回 None）。"""
    if q <= 2:
        return None
    # 素性粗筛
    if any(q % d == 0 for d in range(2, math.isqrt(q) + 1)):
        return None
    for a in range(2, q):
        if mult_order(a, q) == q - 1:
            return a
    return None


def units_mod(q: int):
    return [x for x in range(q) if gcd(x, q) == 1]


# ----------------------------------------------------------------------------
# 群 <T_N, D_a> 的精确构造
# ----------------------------------------------------------------------------

def compose(f, g, q):
    """(f ∘ g)(x) = f(g(x))，元素为长度 q 的置换元组。"""
    return tuple(f[g[x]] for x in range(q))


def build_group(N: int, q: int, a: int):
    """
    BFS 构造 <T_N, D_a> 在 Z/qZ 上的置换表示。

    返回 dict：
      elements  : list[(perm, parity)]  parity = 词中 T 的个数 mod 2
      size      : 群阶
      collisions: 宇称碰撞次数（>0 表示宇称非良定义 => 退化）
      degenerate: T 本身是否落在伸缩子群 <D_a> 内
      n_odd     : 奇宇称元素个数
    """
    ident = tuple(range(q))
    T = tuple((N - x) % q for x in range(q))
    D = tuple((a * x) % q for x in range(q))

    # 伸缩子群 <D_a> 的全部元素（用于退化探测）
    ord_a = mult_order(a, q)
    dil_subgroup = set()
    if ord_a:
        for k in range(ord_a):
            dil_subgroup.add(tuple((pow(a, k, q) * x) % q for x in range(q)))
    degenerate = (T in dil_subgroup)

    seen = {ident: 0}
    queue = deque([(ident, 0)])
    collisions = 0
    while queue:
        perm, par = queue.popleft()
        for gen, gpar in ((T, 1), (D, 0)):
            newperm = compose(gen, perm, q)
            newpar = (par + gpar) % 2
            if newperm in seen:
                if seen[newperm] != newpar:
                    collisions += 1
            else:
                seen[newperm] = newpar
                queue.append((newperm, newpar))

    elements = list(seen.items())
    n_odd = sum(1 for _, p in elements if p == 1)
    return {
        "elements": elements,
        "size": len(elements),
        "collisions": collisions,
        "degenerate_T_in_dilation_subgroup": degenerate,
        "n_odd": n_odd,
        "ord_a": ord_a,
    }


def fixed_points(perm):
    """置换的不动点集合。"""
    return {x for x in range(len(perm)) if perm[x] == x}


def rigid_set(info):
    """F = 所有奇宇称元素的不动点之并（刚性矛盾点）。"""
    F = set()
    for perm, par in info["elements"]:
        if par == 1:
            F |= fixed_points(perm)
    return F


def conjugate_midpoint_orbit(N: int, q: int, a: int):
    """
    F3 = { a^k * (N/2) mod q }：共轭反射 D_a^k T D_a^{-k} 的中点轨道。
    2 在模 q 下可逆时用逆元；不可逆时（q 偶）返回 None 表示不适用。
    """
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
        "conjecture_status": "OPEN",
        "date": "2026-09-25",
        "ai_assisted": True,
        "independent_human_review": False,
        "red_line_note": (
            "本脚本不证明哥德巴赫、不产生反例。它把 OM-P-NT-0003 §14 的角色"
            "Fourier 闭环定位为一个精确可计算条件（q | N 时反射退化为伸缩 => 闭环），"
            "并给出非退化情形下的过定结构。把素密度正性升级为'该类 <= N 含素数'仍需"
            "Brun–Titchmarsh / 零自由区等解析输入，该输入仍然开放。"
        ),
        "sections": {},
    }

    # ---- 节 A：群结构与退化性探测 ----
    sec_a = []
    for q in PRIME_Q + COMPOSITE_Q:
        a = smallest_primitive_root(q)
        if a is None:
            a = 2 if gcd(2, q) == 1 else 3
        for N in SAMPLE_N:
            info = build_group(N, q, a)
            sec_a.append({
                "q": q, "a": a, "N": N,
                "N_mod_q": N % q,
                "q_divides_N": (N % q == 0),
                "group_size": info["size"],
                "n_odd": info["n_odd"],
                "ord_a": info["ord_a"],
                "parity_collisions": info["collisions"],
                "T_in_dilation_subgroup": info["degenerate_T_in_dilation_subgroup"],
                "parity_well_defined": (info["collisions"] == 0
                                        and not info["degenerate_T_in_dilation_subgroup"]),
            })
    report["sections"]["A_group_structure"] = sec_a

    # ---- 节 B：刚性矛盾点 F 与中点轨道 F3（按真实不变量分类） ----
    #
    # 分类依据（重要修正）：宇称是否为**群元素的不变量**，由 BFS 词宇称碰撞判定，
    # 而不是由 q | N 判定。三分支：
    #   degenerate_loop : q | N           —— 几何上 T = D_{-1}，所有反射中点 = 0（非单位）
    #   escape          : q∤N 且宇称良定义 —— 真正的非交换仿射群，F 覆盖全部单位类
    #   illdefined      : q∤N 但宇称碰撞   —— 宇称不是群元素不变量，F 只是部分覆盖
    def regime_of(q, N, info):
        if N % q == 0:
            return "degenerate_loop"
        return "escape" if info["collisions"] == 0 else "illdefined"

    sec_b = []
    for q in PRIME_Q + COMPOSITE_Q:
        a = smallest_primitive_root(q)
        if a is None:
            a = 2 if gcd(2, q) == 1 else 3
        units = set(units_mod(q))
        phi_q = len(units)
        for N in SAMPLE_N:
            info = build_group(N, q, a)
            F = rigid_set(info)
            F3 = conjugate_midpoint_orbit(N, q, a)
            F_units = F & units
            entry = {
                "q": q, "a": a, "N": N,
                "q_divides_N": (N % q == 0),
                "regime": regime_of(q, N, info),
                "parity_collisions": info["collisions"],
                "phi_q": phi_q,
                "size_F": len(F),
                "size_F_units": len(F_units),
                "F_units_ratio": (len(F_units) / phi_q) if phi_q else None,
                "F_units_equals_all_units": (F_units == units),
                "F3_size": (len(F3) if F3 is not None else None),
                "F3_subset_of_F": (F3 <= F) if F3 is not None else None,
                "F3_equals_all_units": (F3 == units) if F3 is not None else None,
            }
            sec_b.append(entry)
    report["sections"]["B_rigid_fixed_points"] = sec_b

    # ---- 节 C：过定度（三分支） ----
    def agg(reg):
        rs = [e["F_units_ratio"] for e in sec_b
              if e["regime"] == reg and e["F_units_ratio"] is not None]
        full = [e for e in sec_b if e["regime"] == reg and e["F_units_ratio"] == 1.0]
        return {
            "count": len(rs),
            "ratio_mean": (sum(rs) / len(rs)) if rs else None,
            "ratio_min": (min(rs) if rs else None),
            "ratio_max": (max(rs) if rs else None),
            "full_cover_count": len(full),
            "empty_count": sum(1 for r in rs if r == 0.0),
        }

    escape = [e for e in sec_b if e["regime"] == "escape"]
    sec_c = {
        "n_cases": len(sec_b),
        "degenerate_loop": agg("degenerate_loop"),
        "escape": agg("escape"),
        "illdefined": agg("illdefined"),
        # 定理只在 escape 分支上断言（宇称良定义时共轭反射必为奇宇称）
        "theorem_F3_equals_all_units_in_escape": all(
            e["F3_equals_all_units"] is True for e in escape
            if e["F3_equals_all_units"] is not None),
        "theorem_F3_subset_F_in_escape": all(
            e["F3_subset_of_F"] is True for e in escape
            if e["F3_subset_of_F"] is not None),
        "theorem_F_units_equals_all_units_in_escape": all(
            e["F_units_equals_all_units"] for e in escape
            if e["F_units_ratio"] is not None),
        "illdefined_moduli_seen": sorted({e["q"] for e in sec_b if e["regime"] == "illdefined"}),
        "escape_moduli_seen": sorted({e["q"] for e in sec_b if e["regime"] == "escape"}),
    }
    report["sections"]["C_overdetermination"] = sec_c

    # ---- 节 D：实证判别力（对真实素数） ----
    isp = sieve(N_MAX + 1)
    primes = [p for p in range(2, N_MAX + 1) if isp[p]]
    sec_d_rows = []
    for q in [3, 5, 7, 11, 13]:
        a = smallest_primitive_root(q)
        if a is None:
            a = 2
        units = set(units_mod(q))
        # 群 / F 只依赖 N mod q，按剩余类缓存
        cache = {}
        for r in range(q):
            info = build_group(r, q, a)
            regime = "degenerate_loop" if r == 0 else (
                "escape" if info["collisions"] == 0 else "illdefined")
            cache[r] = {
                "F_units": rigid_set(info) & units,
                "regime": regime,
            }
        hits = 0
        total = 0
        per_regime = {k: {"total": 0, "hits": 0} for k in
                      ("degenerate_loop", "escape", "illdefined")}
        for N in range(6, N_MAX + 1, 2):
            r = N % q
            c = cache[r]
            # "无 Goldbach"预测：F_units 中不含任何素数
            has_prime = False
            for p in primes:
                if p > N:
                    break
                if (p % q) in c["F_units"]:
                    has_prime = True
                    break
            total += 1
            if has_prime:
                hits += 1
            per_regime[c["regime"]]["total"] += 1
            if has_prime:
                per_regime[c["regime"]]["hits"] += 1
        row = {
            "q": q, "a": a,
            "even_N_count": total,
            "F_units_contains_a_prime_count": hits,
            "discriminator_rate": (hits / total) if total else None,
        }
        for k, v in per_regime.items():
            row[k + "_count"] = v["total"]
            row[k + "_discriminator_rate"] = (
                v["hits"] / v["total"]) if v["total"] else None
        sec_d_rows.append(row)
    report["sections"]["D_empirical_discriminator"] = sec_d_rows

    # ---- 诚实汇总 ----
    degenerate_note = (
        "退化分支 q | N：T_N(x) = N - x = -x (mod q)，反射退化为'乘以 -1'的纯伸缩，"
        "<T_N, D_a> 塌回乘法群。更强的几何事实是 N≡0 使**每一个**共轭反射"
        "D_a^k T_N D_a^{-k} 的中心 a^k·N 都 ≡ 0，其中点恒为 0（非单位），"
        "故 F ∩ (Z/qZ)^* = ∅，过定度为 0 —— 反射–伸缩轨道在此分支不携带任何加法信息。"
        "这**正是** §13/§14 的 chi(-1) 奇偶角色能量差闭环所在之处。"
    )
    nondegenerate_note = (
        "逃逸分支 q ∤ N（且宇称良定义）：反射不是伸缩，<T_N, D_a> 为真正的非交换"
        "仿射群。共轭反射 D_a^k T_N D_a^{-k} 的中点轨道 {a^k · N/2 mod q} 在素模 + "
        "原根下等于**整条单位类群**（本脚本逐例验证），于是'无 Goldbach'被迫把全部"
        "φ(q) 个单位类同时钉为配对自由 —— 单一中点 N/2 的障碍被伸缩轨道"
        "放大为 φ(q) 重过定。"
    )
    report["summary"] = {
        "trichotomy": {
            "degenerate_loop_q_divides_N": sec_c["degenerate_loop"],
            "escape_q_not_divides_N_parity_ok": sec_c["escape"],
            "illdefined_parity_collision": sec_c["illdefined"],
        },
        "theorems_verified": {
            "F3_equals_all_units_in_escape": sec_c["theorem_F3_equals_all_units_in_escape"],
            "F3_subset_of_F_in_escape": sec_c["theorem_F3_subset_F_in_escape"],
            "F_units_equals_all_units_in_escape": sec_c["theorem_F_units_equals_all_units_in_escape"],
        },
        "escape_moduli_seen": sec_c["escape_moduli_seen"],
        "illdefined_moduli_seen": sec_c["illdefined_moduli_seen"],
        "empirical_discriminator_rates": {
            str(r["q"]): {
                "overall": r["discriminator_rate"],
                "escape": r.get("escape_discriminator_rate"),
                "degenerate_loop": r.get("degenerate_loop_discriminator_rate"),
                "illdefined": r.get("illdefined_discriminator_rate"),
            } for r in sec_d_rows
        },
        "interpretation": [
            degenerate_note,
            nondegenerate_note,
            "三分支：q|N 时 F∩units = ∅（过定度 0，轨道塌回乘法群 = §13/§14 闭环）；"
            "q∤N 且宇称良定义时 F∩units = 全部单位类（过定度 φ(q)，逃逸）；"
            "q∤N 但宇称发生碰撞时只部分覆盖（宇称不是群元素的不变量，属真实现象）。",
            "实证节 D：在 escape 分支上，'无 Goldbach'所预测的'F 中无素数'对"
            "6<=N<=2000 的每一个偶数都被真实素数否证（判别率 1.0）；"
            "整体判别率恰为 1-1/q，差额全部来自 q|N 的退化分支——该分支 F 为空，"
            "检验是**空真式（vacuous）**而非反例，必须如实区分。",
            "与 §14 的关系：上一轮 E_odd - E_even ⇔ m+n≡0 (mod q) 的闭环，"
            "本轮被定位为恰好是 q|N 这一退化分支；而在 q∤N 的逃逸分支，"
            "对象变成了非交换仿射轨道 + 整条单位类的 φ(q) 重过定，不再自动回到角色 Fourier。",
        ],
        "what_remains_open": [
            "把'单位类素密度为正（PNT-AP）'升级为'该类 <= N 含至少一个素数'需要"
            "Brun–Titchmarsh / 显式零自由区；这一步是解析输入，本脚本未提供。",
            "即便 F 覆盖全部单位类，'无 Goldbach'仍可通过让素数在每一类中"
            "恰好避开配对来实现（Selberg 奇偶障碍的同族现象）——本脚本量化了这种"
            "合谋的代价（φ(q) 重同时成立），但没有排除它。",
            "宇称碰撞分支（实测 q∈{3,5,9,21}）说明'奇宇称元素'这一概念"
            "只在宇称同态良定义时成立；小模数上必须单独处理，不能套用过定结论。",
            "q 的取值范围：本审计只到 q<=37、N<=2000（节 D）。渐近 q ~ sqrt(N) 区域"
            "（OM-P-NT-0003 §13 的临界尺度）的轨道过定度未经本脚本检验。",
            "未接入真实 Dirichlet L 零点；宇称/轨道是纯结构性诊断。",
        ],
        "verdict": (
            "换维成功地把 §14 的闭环定位为'q | N 退化'这一可计算条件（过定度 0），"
            "并在 q∤N 的逃逸分支给出 φ(q) 重过定与判别率 1.0 的正向校验；"
            "但仍未产生 Goldbach 的证明。状态维持 OPEN。"
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # 人类可读稿
    lines = [
        "# OM-P-NT-0005 · 反射–伸缩非交换轨道审计（2026-09-25）",
        "",
        "> 状态：**OPEN**。本稿不证明哥德巴赫，只做结构诊断。",
        "",
        "## 结论（三分支）",
        "",
        "* **退化 / 闭环分支 q | N**：T_N(x)=N-x=-x (mod q)，反射退化为乘以 -1 的纯伸缩，"
        "  <T_N, D_a> 塌回乘法群；且 N≡0 使每个共轭反射的中心 a^k·N 都 ≡0，中点恒为 0（非单位），"
        "  故 F∩(Z/qZ)^* = ∅，**过定度 0**。这正是 §13/§14 的 χ(-1) 奇偶角色能量差闭环所在。",
        "* **逃逸分支 q ∤ N（宇称良定义）**：<T_N, D_a> 为真正的非交换仿射群；共轭反射中点轨道"
        "  {a^k·N/2} 在素模+原根下**等于整条单位类群**，把单一中点 N/2 的障碍放大为 φ(q) 重过定。",
        "* **宇称碰撞分支 q ∤ N 但宇称非良定义**（实测 q∈{3,5,9,21}）：宇称不是群元素的不变量，"
        "  只部分覆盖，不能套用过定结论。",
        "",
        "## 数据",
        "",
        "| 指标 | 值 |",
        "|---|---|",
    ]
    for reg in ("degenerate_loop", "escape", "illdefined"):
        agg = sec_c[reg]
        lines.append("| {} 分支：样本数 / F_units 占比均值 / 全覆盖数 / 空集数 | {} / {} / {} / {} |".format(
            reg, agg["count"], agg["ratio_mean"], agg["full_cover_count"], agg["empty_count"]))
    lines.append("| 定理：escape 分支 F3 = 全部单位类 | {} |".format(
        sec_c["theorem_F3_equals_all_units_in_escape"]))
    lines.append("| 定理：escape 分支 F3 ⊆ F | {} |".format(
        sec_c["theorem_F3_subset_F_in_escape"]))
    lines.append("| 定理：escape 分支 F∩units = 全部单位类 | {} |".format(
        sec_c["theorem_F_units_equals_all_units_in_escape"]))
    for r in sec_d_rows:
        lines.append("| 实证判别率 q={}：整体 / escape 分支 | {} / {} |".format(
            r["q"], r["discriminator_rate"], r.get("escape_discriminator_rate")))
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
