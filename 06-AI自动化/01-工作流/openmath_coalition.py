# -*- coding: utf-8 -*-
"""
算法联盟 · 量化与突破路线图
===========================

在 openmath_analyze.py 产出的方法体系（method_system.json）与 openmath_sys
调度器（scheduler.py）基础上，做三件事：

  G. 算法联盟统一注册表 —— 把「调度器内置算法」与「数学方法体系」合并为一份
     联盟成员清单，统一标注权限层级(tier)、安全标记(safe)、可实现性(implemented)、
     能力标签(tags) 与其所解锁的猜想方向。

  H. 突破量化评分 —— 对每条**尚未实现**的方法，量化其「需求度 / 实现成本 /
     优先级」，并对未解猜想计算方向覆盖率，输出按收益排序的突破路线图。

  I. 可能性空间的诚实用量化 —— 计算可实现方法的组合管道空间，并给出
     「语义有效管道」的保守上界，明确区分「组合空间庞大」与「实际能力强大」。

诚实红线（openmath/00-宪章/02-诚实红线.md）：
  - 本文件为 L0/L2 级整理与计算产物，**不构成任何证明**。
  - 「方向覆盖率」≠「解决率」：实现某方法只意味着多了一条可下手的
    计算/验证路径，绝不意味着猜想被解决；can_resolve 恒为评估值而非断言。
  - 实现成本(cost)是**启发式主观估计**，非实测工时，仅用于相对排序。
  - 组合管道计数是**数学上的计数事实**，不代表实际解题能力。
"""
from __future__ import annotations

import json
import math
import os
import sys
import datetime

# ---- 路径 -------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):  # 06-AI自动化/01-工作流 -> openmath 仓库根
    REPO = os.path.dirname(REPO)

# openmath_sys 与 openmath 同级，位于 my_lib 下
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "openmath_sys", "src"))

DATA_DIR = os.path.join(REPO, "09-数据")
OUT_DIR = DATA_DIR
REPORT = os.path.join(_HERE, "COALITION_REPORT.md")

GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理基于 openmath_sys 引擎与已下载 OpenMath/arXiv 数据自动生成，"
            "未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = ("本系列文件为 L0/L2 级数据处理与计算校验产物，非证明。"
           "方法实现状态、成本估计、覆盖率均为工程性评估，不构成数学结论。")


def _json_default(o):
    if isinstance(o, complex):
        return {"re": o.real, "im": o.imag, "_type": "complex"}
    return str(o)


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _dump(obj, name):
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=_json_default)


# ===========================================================================
# G. 算法联盟统一注册表
# ===========================================================================

# 权限层级：READ(1) < COMPUTE(2) < TRANSFORM(3) < SUPREME(4)
TIER_ORDER = {"READ": 1, "COMPUTE": 2, "TRANSFORM": 3, "SUPREME": 4}


def _tier_for_method(m: dict) -> str:
    """按方法性质推断其在调度器中的权限层级（保守：够用即止）。"""
    dom = (m.get("domain") or "") + " " + (m.get("name") or "")
    mid = m.get("id", "")
    # 涉及改写/变换/求解输出新结构的 -> TRANSFORM
    if any(k in mid for k in ("solve", "transform", "factor", "groebner",
                              "simplif", "integrat", "differentiat")):
        return "TRANSFORM"
    if any(k in dom for k in ("变换", "求解", "分解", "化简", "积分", "微分", "代数")):
        return "TRANSFORM"
    # 纯数值/求值/判定 -> COMPUTE
    if any(k in dom for k in ("数值", "计算", "求值", "验证", "判定", "统计")):
        return "COMPUTE"
    # 句法/语义/检索 -> READ
    if any(k in dom for k in ("句法", "语义", "解析", "检索", "索引", "通用")):
        return "READ"
    return "COMPUTE"


def _tags_for_method(m: dict) -> list[str]:
    mid = m.get("id", "")
    dom = m.get("domain", "")
    tags = []
    if any(k in dom for k in ("句法", "解析")) or "parse" in mid:
        tags.append("syntax")
    if any(k in dom for k in ("语义", "符号")) or "semantic" in mid or "symbol" in mid:
        tags.append("semantic")
    if any(k in dom for k in ("数值", "计算", "求值")) or any(
            k in mid for k in ("numeric", "eval", "compute")):
        tags.append("compute")
    if any(k in dom for k in ("变换", "代数", "求解")) or any(
            k in mid for k in ("transform", "solve", "factor")):
        tags.append("transform")
    if any(k in dom for k in ("验证", "判定")) or "verify" in mid:
        tags.append("verification")
    return tags or ["analysis"]


# 调度器内置算法 → 其所包装的底层能力方法。
# 这些调度器算法是**编排层适配器**（读取 LogicRecord 的某个维度并转发结果），
# 本身不是独立数学能力，因此登记时必须标注 wraps，避免与方法层重复计数。
SCHEDULER_WRAPS = {
    "semantic_linker": [],          # 独立：CD 语义链接，方法层无对应
    "structural_classifier": ["poly_classify"],
    "evaluator": ["arith_eval"],
    "consistency_checker": [],      # 独立：四维一致性检查（编排层）
    "equation_solver": ["linear_solve", "quadratic_formula", "numeric_root"],
    "report_writer": [],            # 独立：结论汇总（编排层）
}


def build_coalition(methods_doc: dict) -> dict:
    members: list[dict] = []

    # (1) 调度器内置算法（真实存在于代码中，权限与安全标记均来自源码）
    try:
        from openmath_sys.scheduler import build_default_alliance  # noqa: E402
        alliance = build_default_alliance()
        for a in alliance.list_algorithms():
            wraps = SCHEDULER_WRAPS.get(a["name"], [])
            members.append({
                "id": a["name"],
                "name": a["name"],
                "origin": "scheduler",
                "layer": "orchestration",   # 编排层：调度/转发，非独立数学能力
                "where": "openmath_sys/scheduler.py",
                "domain": "联盟调度",
                "tier": a["level"],
                "safe": a["safe"],
                "implemented": True,
                "tags": ["orchestration"],
                "wraps_capabilities": wraps,
                "is_duplicate_capability": bool(wraps),
                "description": a["desc"],
            })
    except Exception as e:  # noqa: BLE001
        members.append({
            "id": "_scheduler_import_error", "name": "调度器导入失败",
            "origin": "scheduler", "layer": "orchestration",
            "where": "openmath_sys/scheduler.py",
            "domain": "联盟调度", "tier": "READ", "safe": True,
            "implemented": False, "tags": ["orchestration"],
            "wraps_capabilities": [], "is_duplicate_capability": False,
            "description": f"导入失败：{type(e).__name__}: {e}",
        })

    # (2) 方法体系（标准数学方法；implemented 严格表示本流水线当前是否真有代码）
    #     统计每条方法能解锁哪些猜想方向
    unlock: dict[str, list[str]] = {}
    for lk in methods_doc.get("linkage", []):
        for mid in lk.get("missing_methods", []):
            unlock.setdefault(mid, []).append(lk["conjecture_id"])
        for mid in lk.get("implemented_applicable", []):
            unlock.setdefault(mid, []).append(lk["conjecture_id"])

    for m in methods_doc.get("methods", []):
        members.append({
            "id": m["id"],
            "name": m["name"],
            "origin": "method_system",
            "layer": "capability",      # 能力层：真正的数学/计算方法
            "where": m.get("where"),
            "domain": m.get("domain"),
            "tier": _tier_for_method(m),
            # 所有登记方法均为内部纯计算算法；无外部写出/破坏性操作
            "safe": True,
            "implemented": bool(m.get("implemented")),
            "tags": _tags_for_method(m),
            "description": m.get("description"),
            "limitation": m.get("limitation"),
            "unlocks_conjectures": sorted(set(unlock.get(m["id"], []))),
        })

    by_tier, by_origin = {}, {}
    for x in members:
        by_tier[x["tier"]] = by_tier.get(x["tier"], 0) + 1
        by_origin[x["origin"]] = by_origin.get(x["origin"], 0) + 1

    # 去重：调度器中有 3 个是包装在方法层之上的适配器，不构成独立能力
    dup = [x for x in members if x.get("is_duplicate_capability")]
    unique_units = len(members) - len(dup)
    unique_impl = sum(1 for x in members if x["implemented"]
                      and not x.get("is_duplicate_capability"))

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_coalition.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "tier_note": ("权限层级 READ<COMPUTE<TRANSFORM<SUPREME 仅为**内部逻辑授权**分级，"
                          "SUPREME 不映射任何操作系统提权；safe=False 的算法在任何层级均被拒绝。"),
        },
        "summary": {
            "members_total": len(members),
            "implemented": sum(1 for x in members if x["implemented"]),
            "missing": sum(1 for x in members if not x["implemented"]),
            "by_tier": by_tier,
            "by_origin": by_origin,
            "by_layer": {
                "capability": sum(1 for x in members if x.get("layer") == "capability"),
                "orchestration": sum(1 for x in members if x.get("layer") == "orchestration"),
            },
            "unsafe_refused": sum(1 for x in members if not x["safe"]),
            # 去重后的真实规模：编排层适配器不计为独立能力
            "unique_capability_units": unique_units,
            "unique_implemented": unique_impl,
            "duplicate_wrappers": len(dup),
            "dedup_note": (
                "调度器内置算法中有 {n} 个（{ids}）是包装在方法层之上的编排适配器，"
                "本身不提供新的数学能力，故 `unique_capability_units` 已将其扣除，"
                "避免把'接口数'误报为'能力数'。"
            ).format(n=len(dup), ids=", ".join(x["id"] for x in dup) or "无"),
        },
        "members": members,
    }


# ===========================================================================
# H. 突破量化评分与路线图
# ===========================================================================

# 实现成本基线（1=易 .. 5=难）。诚实说明：这是**主观启发式估计**，
# 用于相对排序，非实测工时；不同实现者差异可能很大。
#
# 采用**显式表**而非关键词子串匹配：子串匹配会把 lattice_qcd_numeric（格点 QCD
# 数值模拟，极难）因含 "numeric" 而误判为低成本，导致路线图给出错误建议。
COST_TABLE = {
    # --- 能力层：句法/基础计算（1-2） ---
    "ast_parse": 1, "arith_eval": 1, "transc_eval": 2, "poly_classify": 1,
    "prime_sieve": 2, "exhaustive_search": 2, "map_iteration": 2,
    "linear_solve": 2, "quadratic_formula": 2, "modular_analysis": 2,
    "rad_computation": 2,
    # --- 中等：经典符号/数值方法（3） ---
    "factorization": 3, "gaussian_elimination": 3, "symbolic_diff": 3,
    "limit_computation": 3, "numeric_root": 3, "numeric_zero_search": 3,
    # --- 较难（4） ---
    "eigen_decomposition": 4, "asymptotic_estimation": 4, "sieve_theory": 4,
    "random_matrix_analogy": 4, "complexity_reduction": 4,
    # --- 很难：需专门理论/大规模实现（5） ---
    "symbolic_int": 5, "grobner_basis": 5, "circle_method": 5,
    "elliptic_curve_computation": 5, "l_function_evaluation": 5,
    "cohomology_computation": 5, "pde_numerical_simulation": 5,
    "energy_estimate": 5, "algebraic_complexity": 5, "lattice_qcd_numeric": 5,
    "renormalization": 5, "ricci_flow_analysis": 5,
}
DEFAULT_COST = 3
# 未知方法的保守兜底：按领域关键词给一个粗档，避免一律取中间值掩盖差异
FALLBACK_RULES = [
    (("pde", "cohomology", "groebner", "renormal", "ricci", "l_function",
      "elliptic", "qcd", "complexity"), 5),
    (("symbolic", "eigen", "sieve", "asymptotic"), 4),
    (("parse", "eval", "classif", "sieve_of"), 1),
]


def estimate_cost(m: dict) -> int:
    mid = m.get("id", "")
    if mid in COST_TABLE:
        return COST_TABLE[mid]
    blob = (mid + " " + (m.get("name") or "") + " " + (m.get("domain") or "")).lower()
    for kws, c in FALLBACK_RULES:
        if any(k in blob for k in kws):
            return c
    return DEFAULT_COST


def build_roadmap(methods_doc: dict, coalition: dict) -> dict:
    linkage = methods_doc.get("linkage", [])
    impl_ids = {m["id"] for m in coalition["members"] if m["implemented"]}
    miss_ids = {m["id"] for m in coalition["members"] if not m["implemented"]}

    # 需求度：某方法出现在多少条猜想的缺失方法清单里
    demand: dict[str, int] = {}
    for lk in linkage:
        for mid in lk.get("missing_methods", []):
            demand[mid] = demand.get(mid, 0) + 1

    rows = []
    for m in coalition["members"]:
        if m["id"] in impl_ids or m["id"] not in miss_ids:
            continue
        d = demand.get(m["id"], 0)
        cost = estimate_cost(m)
        # 优先级 = 需求度 / 成本（需求为 0 时给 0，避免"没人需要"的方法靠低成本刷榜）
        score = round(d / cost, 4) if d else 0.0
        rows.append({
            "id": m["id"], "name": m["name"], "domain": m["domain"],
            "tier": m["tier"], "demand": d,
            "unlocks_conjectures": m.get("unlocks_conjectures", []),
            "cost_estimate": cost,
            "priority_score": score,
        })
    rows.sort(key=lambda r: (-r["priority_score"], -r["demand"], r["cost_estimate"]))

    # ---- 累计方向覆盖增益曲线 -------------------------------------------
    # 假设按路线图顺序逐条"实现"，重算每条猜想的 method_coverage，
    # 得到「再实现 k 条方法 → 平均方向覆盖率」的曲线。
    # 诚实：这是覆盖率(有多少条适用方法可用)，**不是解决率**。
    curve = []
    have = set(m["id"] for m in coalition["members"] if m["implemented"])
    for k in range(0, len(rows) + 1):
        covs = []
        for lk in linkage:
            applicable = lk.get("applicable_methods", [])
            if not applicable:
                continue
            ok = sum(1 for a in applicable if a in have)
            covs.append(ok / len(applicable))
        avg = sum(covs) / len(covs) if covs else 0.0
        full = sum(1 for c in covs if c >= 0.999)
        curve.append({
            "implemented_extra": k,
            "avg_direction_coverage": round(avg, 4),
            "conjectures_with_all_methods": full,
        })
        if k < len(rows):
            have.add(rows[k]["id"])

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_coalition.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "scoring_note": (
                "priority_score = demand / cost_estimate。"
                "demand = 该方法出现在多少条未解猜想的'缺失方法'清单中（客观，来自 method_system.linkage）；"
                "cost_estimate = 1..5 的**主观启发式估计**，非实测工时，仅用于相对排序。"
                "两者相除得到的分数只表示'性价比排序'，不代表投入产出承诺。"
            ),
            "coverage_note": (
                "avg_direction_coverage 是**方向覆盖率**（有多少适用的方法真正可用），"
                "**不是猜想的解决率**。方法可用 ≠ 猜想被证明；can_resolve 在本体系中恒不因实现方法而自动置真。"
            ),
        },
        "summary": {
            "missing_methods_scored": len(rows),
            "with_demand": sum(1 for r in rows if r["demand"] > 0),
            "with_zero_demand": sum(1 for r in rows if r["demand"] == 0),
            "coverage_now": curve[0]["avg_direction_coverage"] if curve else 0.0,
            "coverage_if_top5": curve[min(5, len(curve) - 1)]["avg_direction_coverage"],
            "coverage_if_all": curve[-1]["avg_direction_coverage"],
        },
        "roadmap": rows,
        "coverage_curve": curve,
    }


# ===========================================================================
# I. 可能性空间的诚实用量化
# ===========================================================================
def _perm(n: int, k: int) -> int:
    return math.perm(n, k) if 0 <= k <= n else 0


def build_possibility(coalition: dict, roadmap: dict) -> dict:
    """量化「组合可能性空间」，并明确它与「实际能力」的区别。"""
    # 口径：只统计**能力层**已实现方法。编排层适配器是固定管道骨架（转发/汇总），
    # 把它们混进排列会把"接口数"当成"能力数"，虚增组合空间。
    impl = [m for m in coalition["members"]
            if m["implemented"] and m.get("layer") == "capability"]
    orchestration_n = sum(1 for m in coalition["members"]
                          if m.get("layer") == "orchestration")

    def pipe_space(n: int) -> int:
        """长度 1..n 的有序不重复管道总数 = sum_k P(n,k)"""
        return sum(_perm(n, k) for k in range(1, n + 1))

    n_now = len(impl)
    # 语义有效管道的**保守上界**：必须以句法/解析类起头，至少含一个计算/变换类，
    # 且链长限制在 2..4（更长的链条在本体系中无明确语义）。
    starters = [m for m in impl if "syntax" in m["tags"] or "orchestration" in m["tags"]]
    endings = [m for m in impl if any(t in m["tags"] for t in ("compute", "transform",
                                                               "verification"))]
    middles = [m for m in impl if m not in starters and m not in endings]
    valid_upper = 0
    for L in (2, 3, 4):
        # 起点 1 个 + 中间 (L-2) 个有序取自 middles + 终点 1 个
        valid_upper += len(starters) * _perm(len(middles), L - 2) * len(endings)

    # 若实现路线图前 k 条，空间如何增长
    growth = []
    for k in (0, 3, 5, 10, len(roadmap["roadmap"])):
        growth.append({
            "extra_implemented": k,
            "available_methods": n_now + k,
            "nominal_pipeline_space": pipe_space(n_now + k),
        })

    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_coalition.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "interpretation_warning": (
                "**组合空间 ≠ 能力**。下列计数是'从 n 个可实现方法中排成有序管道'的"
                "纯组合学事实（Σ_{k=1..n} P(n,k)），它随 n 阶乘式增长，但其中"
                "**绝大多数排列没有数学意义**（例如'求根→解析'是无语义的）。"
                "真正的解题能力取决于方法的**覆盖面与正确性**，不取决于排列数。"
                "因此这里同时给出语义约束后的保守上界，供对比。"
            ),
        },
        "current": {
            "implemented_methods": n_now,
            "orchestration_layer_members": orchestration_n,
            "nominal_pipeline_space": pipe_space(n_now),
            "semantically_valid_upper_bound": valid_upper,
            "starters": len(starters), "endings": len(endings), "middles": len(middles),
            "ratio_nominal_to_valid": (
                round(pipe_space(n_now) / valid_upper, 1) if valid_upper else None),
            "caliber_note": (
                "组合空间仅基于能力层已实现的 {n} 个数学方法计算；"
                "编排层 {o} 个成员是固定管道骨架（解析/转发/汇总），不参与排列。"
            ).format(n=n_now, o=orchestration_n),
        },
        "growth_if_implemented": growth,
    }


# ===========================================================================
# 报告
# ===========================================================================
def write_report(coal: dict, road: dict, poss: dict) -> None:
    L = []
    cs, rs, ps = coal["summary"], road["summary"], poss["current"]
    L.append("# 算法联盟 · 量化与突破路线图\n")
    L.append(f"> 生成时间：{GEN_AT}　|　"
             f"生成者：`06-AI自动化/01-工作流/openmath_coalition.py`　|　"
             f"证据等级：**L0/L2**　|　`provenance.ai_assisted = true`\n")
    L.append("> **本文件不构成任何数学证明。** 方向覆盖率 ≠ 解决率；"
             "成本为启发式估计；组合计数为组合学事实而非能力声明。\n")

    L.append("\n## 1. 算法联盟统一注册表\n")
    L.append(f"联盟成员共 **{cs['members_total']}** 个"
             f"（调度器内置 {cs['by_origin'].get('scheduler', 0)} 个 + "
             f"数学方法 {cs['by_origin'].get('method_system', 0)} 个），"
             f"其中**已实现 {cs['implemented']}**、未实现 {cs['missing']}。\n")
    L.append(f"其中 {cs['duplicate_wrappers']} 个调度器成员是包装在方法层之上的"
             f"**编排适配器**（非独立能力），扣除后真实能力单元为 "
             f"**{cs['unique_capability_units']}** 个（已实现 {cs['unique_implemented']}）。\n")
    L.append("| 权限层级 | 成员数 | 含义 |")
    L.append("|---|---|---|")
    tier_desc = {"READ": "只读/检索/解析", "COMPUTE": "数值计算/求值/判定",
                 "TRANSFORM": "结构变换/求解", "SUPREME": "全量逻辑授权上限"}
    for t in ("READ", "COMPUTE", "TRANSFORM", "SUPREME"):
        if t in cs["by_tier"]:
            L.append(f"| {t} | {cs['by_tier'][t]} | {tier_desc[t]} |")
    L.append("")
    L.append(f"被安全门拒绝的成员（`safe=False`）：**{cs['unsafe_refused']}** 个。\n")
    L.append("> 权限层级仅为内部逻辑授权分级，SUPREME **不映射任何操作系统提权**。\n")

    L.append("\n## 2. 突破路线图（按性价比排序）\n")
    L.append(f"未实现方法 **{rs['missing_methods_scored']}** 条，其中 "
             f"**{rs['with_demand']}** 条被至少一条未解猜想需要，"
             f"**{rs['with_zero_demand']}** 条当前无猜想需求。\n")
    top = [r for r in road["roadmap"] if r["demand"] > 0][:10]
    if top:
        L.append("| # | 方法 | 领域 | 需求度 | 成本 | 优先级 | 解锁猜想 |")
        L.append("|---|---|---|---|---|---|---|")
        for i, r in enumerate(top, 1):
            uc = ", ".join(r["unlocks_conjectures"][:4]) or "—"
            L.append(f"| {i} | `{r['id']}` | {r['domain']} | {r['demand']} | "
                     f"{r['cost_estimate']} | {r['priority_score']:.2f} | {uc} |")
        L.append("")
    L.append("> 需求度 = 该方法出现在多少条未解猜想的「缺失方法」清单中（客观）；"
             "成本 = 1–5 的**主观启发式估计**，仅用于相对排序，非工时承诺。\n")

    L.append("\n## 3. 累计方向覆盖增益曲线\n")
    L.append("按路线图顺序逐条补齐方法后，未解猜想的**平均方向覆盖率**变化：\n")
    L.append("| 额外实现方法数 | 平均方向覆盖率 | 方法齐备的猜想数 |")
    L.append("|---|---|---|")
    marks = {0, 1, 3, 5, 10, 20, len(road["coverage_curve"]) - 1}
    for i, c in enumerate(road["coverage_curve"]):
        if i in marks:
            L.append(f"| +{c['implemented_extra']} | {c['avg_direction_coverage']:.1%} | "
                     f"{c['conjectures_with_all_methods']} |")
    L.append("")
    L.append(f"当前 **{rs['coverage_now']:.1%}** → 补齐 Top5 **{rs['coverage_if_top5']:.1%}** "
             f"→ 全部补齐 **{rs['coverage_if_all']:.1%}**。\n")
    L.append("> **关键诚实说明**：方向覆盖率上升只表示「可下手的计算/验证路径变多」，"
             "**绝不表示猜想被推进到可解决**。本体系中 `can_resolve` 不因方法实现而自动置真——"
             "从「有方法」到「有证明」之间仍隔着人类数学家的工作与形式化验证。\n")

    L.append("\n## 4. 「无限可能」的诚实用量化\n")
    L.append(f"计算口径：仅能力层已实现的 **{ps['implemented_methods']}** 个数学方法参与排列；"
             f"编排层 {ps['orchestration_layer_members']} 个成员是固定管道骨架，不参与。"
             f"把它们任意排成有序不重复管道，名义组合空间为 "
             f"**{ps['nominal_pipeline_space']:,}** 种（Σ P(n,k)）。\n")
    L.append(f"但施加语义约束（须以解析类起头、至少含一个计算/变换类、链长 2–4）后，"
             f"保守有效上界仅 **{ps['semantically_valid_upper_bound']:,}** 种，"
             f"名义空间是有效空间的约 **{ps['ratio_nominal_to_valid']}×**。\n")
    L.append("| 额外实现 | 可用方法数 | 名义管道空间 |")
    L.append("|---|---|---|")
    for g in poss["growth_if_implemented"]:
        L.append(f"| +{g['extra_implemented']} | {g['available_methods']} | "
                 f"{g['nominal_pipeline_space']:,} |")
    L.append("")
    L.append("> 组合空间随方法数**阶乘式膨胀**，这是事实；但**膨胀的是排列数，不是能力**。"
             "绝大多数排列无数学语义。真正决定突破的是方法的覆盖面与正确性，"
             "因此本节的价值在于用对比说明「无限可能」的正确理解："
             "**可能的组合很多，有意义的组合很少。**\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ===========================================================================
# 主流程
# ===========================================================================
def main():
    methods_doc = _load("method_system.json")

    coalition = build_coalition(methods_doc)
    _dump(coalition, "algorithm_coalition.json")
    print(f"[G] 算法联盟注册表：{coalition['summary']['members_total']} 成员"
          f"（实现 {coalition['summary']['implemented']} / "
          f"未实现 {coalition['summary']['missing']}，"
          f"被安全门拒绝 {coalition['summary']['unsafe_refused']}）")

    roadmap = build_roadmap(methods_doc, coalition)
    _dump(roadmap, "breakthrough_roadmap.json")
    print(f"[H] 突破路线图：{roadmap['summary']['missing_methods_scored']} 条待实现方法，"
          f"方向覆盖率 现在 {roadmap['summary']['coverage_now']:.1%} → "
          f"Top5 {roadmap['summary']['coverage_if_top5']:.1%} → "
          f"全补齐 {roadmap['summary']['coverage_if_all']:.1%}")

    poss = build_possibility(coalition, roadmap)
    _dump(poss, "possibility_space.json")
    print(f"[I] 可能性空间：名义 {poss['current']['nominal_pipeline_space']:,} 种组合，"
          f"语义有效上界 {poss['current']['semantically_valid_upper_bound']:,} 种"
          f"（相差约 {poss['current']['ratio_nominal_to_valid']}×）")

    write_report(coalition, roadmap, poss)
    print(f"[R] 报告已写：{REPORT}")


if __name__ == "__main__":
    main()
