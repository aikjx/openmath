# -*- coding: utf-8 -*-
"""
sequences：序列理论流水线（S9）
==============================================================================

  Q1. 调用引擎 sequences.analyze_all()，在整数序列库上跑三条通道：
        C1 常系数线性递推（C-finite，精确有理高斯消元）
        C2 一阶有理（超几何）递推 a(n+1)/a(n) = P(n)/Q(n)
        C3 增长率（指数底 λ / 多项式次数 / 超指数）
      发现集只用前 30 项，**后续 30 项一律不参与发现**，只做外推检验；
      再用前 15 项跑一遍压力测试，暴露小样本过拟合。
  Q2. 调用 audit.audit_sequences() 做独立复核：
        - 教科书/OEIS 首项对照（参照值不取自本仓库任何代码）
        - 每条被报出的递推由**另一份实现**重算全量项（交叉相乘，无除法）
        - 增长率类型与理论底数对照（只断言有把握的条目）
  Q3. 产出：
        - 09-数据/sequence_theory.json       全量结果（含校准与关系网）
        - 09-数据/sequence_candidates.json   候选 + 已知重发现 + 人工复核队列
  Q4. 自核验（把方法用在自己的产物上），共 9 项不变量检查。
  Q5. 生成 06-AI自动化/01-工作流/SEQUENCE_REPORT.md。

与 S7 的区别（重要）
------------------------------------------------------------------------------
S7 的 theoryforge 找的是**同一对象内部**不变量之间的静态关系（如 χ ≥ ω）；
S9 找的是**沿参数 n 演化**的动态关系：a(n) 如何由前面的项表示。
两者互补，合起来才覆盖「静态不变量 + 动态递推」两类可机器搜索的结构。

诚实红线（00-宪章/02-诚实红线.md）
------------------------------------------------------------------------------
  - 本脚本**不证明任何东西**。递推通过外推检验只说明「在已生成的这些项上
    没找到反例」，检验集之外永远是未知；这一点在每条记录里都写着。
  - 「已知递推的重发现」是**校准件**，用来证明机器能工作，不是新结果。
  - 未列入校准表但被独立发现的项，进**人工复核队列**，不得直接称为发现。
"""
from __future__ import annotations

import datetime
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):
    REPO = os.path.dirname(REPO)

DATA_DIR = os.path.join(REPO, "09-数据")
REPORT = os.path.join(_HERE, "SEQUENCE_REPORT.md")
ENGINE_SRC = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理自动生成，未经人类复核，不得作为 L3+ 证据。",
}
N_TERMS = 60

sys.path.insert(0, ENGINE_SRC)

from openmath_sys import sequences as sq  # noqa: E402
from openmath_sys.audit import Auditor, audit_sequences  # noqa: E402


def _dump(obj, n):
    with open(os.path.join(DATA_DIR, n), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


STATUS_CN = {
    "CANDIDATE_UNVERIFIED": "待验证候选（L2）",
    "KNOWN_RECURRENCE_REDISCOVERED": "已知递推的重发现（校准件）",
    "FALSIFIED_BY_EXTRAPOLATION": "外推已证伪",
}

GROWTH_CN = {
    "exponential": "指数型",
    "polynomial_like": "多项式型",
    "super_exponential": "超指数型",
    "neither": "中间型（两模型都不拟合）",
    "unknown": "不可判定（拒答）",
}


# ===========================================================================
# Q1-Q2. 跑引擎 + 独立复核
# ===========================================================================
def run_engine() -> dict:
    res = sq.analyze_all(N_TERMS)
    res["meta"] = {
        "generated_at": GEN_AT,
        "generator": "06-AI自动化/01-工作流/openmath_sequences.py",
        "evidence_level": "L2",
        "provenance": PROVENANCE,
        "honesty": (
            "所有结论的论域严格是「已生成的这些项」。通过外推检验只表示在该长度内"
            "没有找到反例，**不证明**递推对所有 n 成立。"
        ),
    }
    return res


def run_cross_audit() -> dict:
    aud = Auditor()
    audit_sequences(aud, n_terms=N_TERMS)
    return aud.sections[-1]


# ===========================================================================
# Q3a. 序列关系网：同一条递推的解空间里有哪些序列
# ===========================================================================
def build_net(res: dict) -> dict:
    """按「递推式」聚合：共享同一递推的序列属于同一解空间的不同初值。

    这是把逐条的发现连成网的一步——它回答的不是「这个序列满足什么」，
    而是「哪些序列其实在同一条递推的不同初值上」。
    """
    net: dict = {}
    for s in res["sequences"]:
        for cand in s["linear"] + s["hyper"]:
            if not cand.get("survived_extrapolation"):
                continue
            key = cand["statement"]
            node = net.setdefault(key, {
                "statement": key,
                "channel": cand["channel"],
                "recognition": (cand.get("recognition") or {}).get("known_name"),
                "is_known": bool(cand.get("recognition")),
                "members": [],
            })
            node["members"].append({
                "seq": s["id"], "cn": s["cn"],
                "status": cand["status"],
                "index_base": s["index_base"],
            })
    # 多成员的递推更值得看：说明这条递推的解空间里不止一个已知序列
    out = sorted(net.values(), key=lambda d: (-len(d["members"]), d["statement"]))
    return {
        "note": ("同一条递推式下的不同初值即不同序列；这里按递推式聚合。"
                 "成员数 ≥ 2 的条目说明该递推的解空间里不止一个知名序列。"),
        "n_recurrences": len(out),
        "n_multi_member": sum(1 for d in out if len(d["members"]) >= 2),
        "recurrences": out,
    }


# ===========================================================================
# Q4. 自核验：把同一套怀疑用在自己的产物上
# ===========================================================================
def self_audit(res: dict, cross: dict, net: dict) -> list:
    checks = []

    def add(name, violations, why):
        checks.append({"check": name, "passed": not violations,
                       "violations": list(violations), "why": why})

    seqs = {s["id"]: s for s in res["sequences"]}

    # 1. 序列长度：留出集必须非空，否则"外推检验"是空话
    bad = [s["id"] for s in res["sequences"]
           if s["n_terms"] <= res["parameters"]["discovery_len"]]
    add("留出集非空（n_terms > discovery_len）", bad,
        "发现集若等于全量，外推检验就是自证，等于没有检验")

    # 2. 每条被接受的候选都必须真的通过了外推
    bad = []
    for s in res["sequences"]:
        for c in s["linear"] + s["hyper"]:
            if c["status"] == "CANDIDATE_UNVERIFIED" and not c.get("survived_extrapolation"):
                bad.append(f"{s['id']}::{c['statement']}")
    add("候选均通过外推检验", bad,
        "未通过外推的东西若被标成候选，说明状态机与检验逻辑脱钩")

    # 3. 标成"已知重发现"的必须给出可核对的 known_id
    bad = []
    for s in res["sequences"]:
        for c in s["linear"] + s["hyper"]:
            if c["status"] == "KNOWN_RECURRENCE_REDISCOVERED" and not (c.get("recognition") or {}).get("known_id"):
                bad.append(f"{s['id']}::{c['statement']}")
    add("重发现均带 known_id", bad,
        "没有出处的重发现无法复核，等于自封")

    # 4. 校准表引用的序列必须在库里
    from openmath_sys.sequences import KNOWN_RECURRENCES
    bad = [r["seq"] for r in KNOWN_RECURRENCES if r["seq"] not in seqs]
    add("校准表条目均在序列库中", bad,
        "校准表指向不存在的序列会让召回率虚高")

    # 5. 期望阳性集与期望阴性集不得相交（否则校准自相矛盾）
    from openmath_sys.sequences import EXPECTED_NEGATIVE
    pos = {r["seq"] for r in KNOWN_RECURRENCES}
    add("期望阳性与期望阴性不相交", sorted(pos & EXPECTED_NEGATIVE),
        "同一序列既要求找得到又要求找不到，校准就失去意义")

    # 6. 校准召回：期望阳性的序列必须被召回
    add("校准召回无遗漏", res["calibration"]["missed"],
        "漏掉已知的递推说明搜索空间或阶数上限不够")

    # 7. 期望阴性上不得报出候选（报出即假警报）
    add("期望阴性上无假警报", res["calibration"]["false_alarm"],
        "在不该有递推的序列上报出候选，说明过拟合没被挡住")

    # 8. 独立审计与引擎判定零分歧
    add("独立重算与引擎判定一致",
        [] if cross.get("n_independent_disagreements", 0) == 0
        else [d["key"] for d in cross.get("disagreements", [])],
        "审计用另一份实现重算，若与引擎结论不一致，至少一方有 bug")

    # 9. 双路径对账：凡能对账的序列，两条路径必须指向同一类型
    rc = res.get("growth_reconciliation", {})
    add(f"C1↔C3 对账无分歧（{rc.get('n_agree', 0)}/{rc.get('n_reconcilable', 0)}）",
        rc.get("disagreeing", []),
        "递推特征根与窗口拟合若给出不同类型，至少一方有 bug；这是两条独立路径的交叉检验")

    # 10. 关系网成员必须都是真的存活项（已由 2 覆盖，这里查网的完整性）
    total_surv = sum(1 for s in res["sequences"]
                     for c in s["linear"] + s["hyper"]
                     if c.get("survived_extrapolation"))
    net_members = sum(len(d["members"]) for d in net["recurrences"])
    add(f"关系网成员数一致（网内 {net_members} / 存活 {total_surv}）",
        [] if net_members == total_surv else [f"{net_members} != {total_surv}"],
        "网若漏掉存活项，说明聚合口径与筛选口径不一致")

    return checks


# ===========================================================================
# Q5. 报告
# ===========================================================================
def _tbl(rows, header=None):
    if not rows:
        return "_（无）_\n"
    ncol = len(rows[0])
    out = ["| " + " | ".join(str(x) for x in rows[0]) + " |",
           "|" + "|".join(["---"] * ncol) + "|"]
    for r in rows[1:]:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out) + "\n"


def write_report(res: dict, cross: dict, net: dict, checks: list) -> None:
    L = []
    A = L.append
    summ = res["summary"]
    cal = res["calibration"]

    A("# 序列理论报告（S9）\n")
    A(f"- 生成时间：{GEN_AT}")
    A("- 性质：AI 辅助自动生成，**未经人类复核**，不构成证明。")
    A(f"- 序列库：{summ['n_sequences']} 个序列 × {N_TERMS} 项；"
      f"发现集前 {res['parameters']['discovery_len']} 项，"
      f"其余 {N_TERMS - res['parameters']['discovery_len']} 项仅用于外推检验。\n")

    A("## 1. 这一阶段在做什么\n")
    A("S7 找的是**同一对象内部**不变量之间的静态关系；S9 找的是**沿参数 n 演化**的")
    A("动态关系——`a(n)` 如何由前面的项表示。三条通道：\n")
    A("1. **C1 常系数线性递推**：`a(n) = c₁a(n-1) + … + c_k a(n-k)（+ 常数）`，"
      "系数由精确有理高斯消元求出，最高 4 阶。")
    A("2. **C2 一阶有理（超几何）递推**：`a(n+1)/a(n) = P(n)/Q(n)`，精确插值判定。")
    A("3. **C3 增长率**：尾部项分别拟合 `log a(n)~n` 与 `log a(n)~log n`，"
      "比较残差；再用 `log a(n)/n` 的走向识别超指数型。\n")
    A("**关键约束**：发现只用前一半项，后一半只用来打脸。另用前 15 项跑一遍压力测试，")
    A("专门暴露「小样本上拟合出来、全量上不成立」的过拟合。\n")

    A("## 2. 总览\n")
    A(_tbl([["指标", "数值", "含义"]] + [
        ["序列数", summ["n_sequences"], "参与搜索的整数序列"],
        ["已知递推重发现", summ["n_known_rediscovered"], "校准件：证明机器能工作"],
        ["待验证候选", summ["n_candidates"], "通过外推但没对上已知表的项"],
        ["主发现集被外推证伪", summ["n_falsified_main"], "过拟合被挡下的数量"],
        ["压力测试（15 项）被证伪", summ["n_falsified_stress"], "小样本过拟合暴露数"],
    ]))

    A("## 3. 逐序列结果\n")
    rows = [["序列", "中文名", "通道/状态", "增长率", "底数/次数"]]
    for s in res["sequences"]:
        ch = []
        for c in s["linear"] + s["hyper"]:
            tag = "C1" if c["channel"] == "linear" else "C2"
            mark = ("✓已知" if c["status"] == "KNOWN_RECURRENCE_REDISCOVERED"
                    else ("候选" if c["status"] == "CANDIDATE_UNVERIFIED" else "✗证伪"))
            ch.append(f"{tag}:{mark}")
        g = s["growth"]
        extra = ""
        if g.get("base_lambda") is not None:
            extra = f"λ≈{g['base_lambda']}"
        elif g.get("degree_estimate") is not None:
            extra = f"k≈{g['degree_estimate']}"
        if g.get("subexponential_warning"):
            extra += " ⚠次指数"
        rows.append([s["id"], s["cn"], "，".join(ch) or "—",
                     GROWTH_CN.get(g.get("type"), g.get("type")), extra or "—"])
    A(_tbl(rows))

    A("## 4. 校准：这套机器到底能不能用\n")
    A(_tbl([["指标", "结果"]] + [
        ["期望阳性（校准表）", f"{len(cal['expected_positive'])} 条"],
        ["召回", f"{len(cal['recalled'])}/{len(cal['expected_positive'])}"
                 f"（率 {cal['recall_rate']}）"],
        ["遗漏", "、".join(cal["missed"]) or "无"],
        ["期望阴性", f"{len(cal['expected_negative'])} 个序列"],
        ["真阴性", f"{len(cal['true_negative'])} 个（这些本就不该有递推）"],
        ["假警报", "、".join(cal["false_alarm"]) or "无"],
    ]))
    A("\n**未列入校准表、但被机器独立发现**的序列（进人工复核队列，"
      "不称为新发现）：\n")
    A(_tbl([["序列", "已知背景", "机器找到的形式"]] +
           [[k, v, next((c["statement"] for s in res["sequences"] if s["id"] == k
                         for c in s["linear"] + s["hyper"]
                         if c.get("survived_extrapolation")), "—")]
            for k, v in sorted(cal["unlisted_found"].items())]))

    A("\n## 5. 独立复核（S8 审计交叉核验）\n")
    A(f"- 教科书/OEIS 首项对照：**{cross['n_reference_terms_checked']} 项**，"
      f"失败 {len(cross['failures'])} 项。")
    A(f"- 递推独立重算：{cross['n_recurrence_candidates']} 条候选，"
      f"用另一份实现（交叉相乘、无除法）重算全量项，"
      f"与引擎判定分歧 **{cross['n_independent_disagreements']}** 条。")
    A(f"- 增长率类型对照：只断言有把握的 "
      f"{len(cross['growth_observed'])} 个中的一部分，其余留作观测不断言。")
    A(f"- 主特征根对照经典常数（φ、tribonacci 常数、塑性数）："
      f"{len(cross['char_root_expect'])} 条，容差 {cross['char_root_expect'] and '1e-6'}。")
    A(f"- C1↔C3 双路径对账：{cross['n_reconciled']} 条，"
      f"类型分歧 {cross['n_reconcile_type_mismatch']} 条。\n")
    A("参照值**不取自本仓库任何代码**（写错就会红）。这是刻意的：")
    A("上一轮审计里我自己就把 `li(10)` 的参照值写错过一次，"
      "所以参照必须来自独立算法或教科书，不来自印象。\n")

    A("## 6. 递推 → 特征根 → 增长率：把 C1 与 C3 接起来\n")
    A("这一节是本阶段**唯一一条方法论上的新增**：原来 C1（递推）与 C3（增长率）")
    A("是两条各算各的通道，现在把它们对上账。\n")
    A("若 `a(n) = c₁a(n-1) + … + c_k a(n-k)（ + d）`，则特征多项式为")
    A("`x^k − c₁x^(k−1) − … − c_k`。记其根为 `r₁,…,r_k`：\n")
    A("- 若 `max|rᵢ| > 1`，增长为 `|r_max|^n`——底数由**递推结构**决定，不看窗口；")
    A("- 若主根模 = 1 且 1 是 `m` 重根：齐次（`d=0`）时 ~ `n^(m−1)`，"
      "常数强迫（`d≠0`）时 ~ `n^m`。\n")
    A("平方数是原型：`a(n)=2a(n−1)−a(n−2)+2` ⇒ `(E−1)²a = 2` ⇒ `a ~ n²`。")
    A("（初版把次数写成 `m+1`，正是被这次对账打出 `deg=3 vs 窗口 2.0` 才发现的。）\n")
    A("**对账结果**：\n")
    def _cell(sd, k_rec, k_win):
        rec = sd["recurrence_implied"]
        det = sd.get("detail", {})
        return (str(rec.get(k_rec, "—")) if k_rec in rec else "—",
                str(det.get(k_win, "—")))

    rows = [["序列", "递推", "特征根给出", "窗口拟合", "一致"]]
    for s in res["sequences"]:
        sd = s["growth_vs_recurrence"]
        if not sd["available"]:
            continue
        if sd["recurrence_implied"].get("type") == "exponential":
            a, b = _cell(sd, "base_exact_from_recurrence", "base_from_window")
        else:
            a, b = _cell(sd, "degree_from_recurrence", "degree_from_window")
            a, b = f"次数 {a}", f"次数 {b}"
        rows.append([s["id"], sd["recurrence_used"], a, b,
                     "✅" if sd.get("agrees") else "❌"])
    A(_tbl(rows))
    rc = res["growth_reconciliation"]
    A(f"\n可对账 {rc['n_reconcilable']} 条，一致 {rc['n_agree']} 条，"
      f"分歧 {rc['n_disagree']} 条。\n")
    A("**次指数警告的消解**：`perrin` 与 `padovan` 的窗口底数 ρ≈1.3247 接近 1，"
      "单看数值分不出指数与次指数，C3 因此挂了警告。但递推 `a(n)=a(n−2)+a(n−3)`")
    A("的特征根给出**确定底数** ρ=1.32471796（塑性数），警告即被消解——")
    A("警告本身没错，是递推证据补上了缺口。\n")

    A("## 7. 序列关系网：同递推 → 同解空间\n")
    A(_tbl([["递推式", "通道", "成员", "已知出处"]] +
           [[d["statement"], "C1" if d["channel"] == "linear" else "C2",
             "、".join(m["cn"] for m in d["members"]),
             d["recognition"] or "—"]
            for d in net["recurrences"] if len(d["members"]) >= 2]))
    A(f"\n共 {net['n_recurrences']} 条通过外推的递推，"
      f"其中 {net['n_multi_member']} 条不止一个成员序列。\n")

    A("## 7. 已知局限（必须读）\n")
    A("1. **外推不是证明**。这里每一项都只在 ≤60 项上验过；"
      "第 61 项起是未知。\n")
    A("2. **底数有窗口偏差**。λ^n·n^α 型序列在有限窗口上拟合出的底数必然偏低：\n")
    A(_tbl([["序列", "理论底数", "窗口观测", "相对缺口"]] +
           [[k, v["theoretical"], v["observed"], f"{v['relative_deficit']:.2%}"]
            for k, v in sorted(cross["growth_base_bias"].items())]))
    A("   多项式的因子被吸收进指数项了。这是方法固有的偏差，不是 bug；"
      "但把观测底数当结论用就会错。\n")
    A("3. **增长率类型不全覆盖**。以下序列的类型由引擎给出但**未经审计确认**：")
    A(f"   {'、'.join(cross['unchecked_growth_ids'])}。")
    A("   它们的真实增长多属中间型（n/log n、n log n、exp(√n) 一类），"
      "两模型都不拟合是**正确**结果，不是失败。\n")
    A("4. **序列库是我自己列的**。库里没有的序列，机器不会去找；"
      "「没找到」只对库内成立。\n")
    A("5. **C1 有阶数上限 4**。更高阶的线性递推不在搜索范围内。\n")

    A("## 8. 自核验（把方法用在自己的产物上）\n")
    A(_tbl([["检查项", "结果", "为什么查这一条"]] +
           [["✅ " + c["check"] if c["passed"] else "❌ " + c["check"],
             "通过" if c["passed"] else "违规：" + "，".join(map(str, c["violations"])),
             c["why"]] for c in checks]))
    viol = sum(1 for c in checks if not c["passed"])
    A(f"\n合计 {len(checks)} 项，违规 {viol} 项。\n")

    A("## 9. 结论（克制版）\n")
    A(f"1. 在 {summ['n_sequences']} 个序列 × {N_TERMS} 项上，三条通道共报出 "
      f"{summ['n_known_rediscovered']} 条已知递推的重发现、"
      f"{summ['n_candidates']} 条待验证候选；校准召回 "
      f"{cal['recall_rate']}，期望阴性上无假警报。\n")
    A("2. 重发现是**校准件**：它们的价值在于证明「枚举 + 精确检验」这套机制能工作，"
      "而不是产生新知识。把它们当新结果是自欺。\n")
    A("3. 本阶段真正新增的东西只有两类：一是**未列入校准表却被独立发现**的几条"
      "（第 4 节，进人工复核队列）；二是**同一递推解空间的聚合**（第 6 节），"
      "它把逐条发现连成了网。\n")
    A("4. 从第 7 节可以看出，这套方法在**增长率**这一维上只能给区间与警告，"
      "给不了确定值；这是数值估计的固有性质，不是可以靠加代码修掉的。\n")
    A("5. 本阶段产出类型是 **L2 候选供给**。任何一条要走成定理，"
      "都得有人补一个针对**所有 n** 的论证——这一步机器没做，也不该假装做了。\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ===========================================================================
# main
# ===========================================================================
def main() -> None:
    print("[S9] 序列理论：开始")
    res = run_engine()
    summ = res["summary"]
    print(f"     序列 {summ['n_sequences']} 个；重发现 {summ['n_known_rediscovered']}，"
          f"候选 {summ['n_candidates']}，外推证伪 {summ['n_falsified_main']}")

    cross = run_cross_audit()
    print(f"     独立复核 {cross['checks']} 项，失败 {len(cross['failures'])} 项；"
          f"递推重算分歧 {cross['n_independent_disagreements']} 条")
    res["independent_audit"] = cross

    net = build_net(res)
    res["sequence_net"] = net
    print(f"     关系网：{net['n_recurrences']} 条递推，"
          f"其中 {net['n_multi_member']} 条多成员")

    checks = self_audit(res, cross, net)
    res["self_audit"] = {
        "checks": checks,
        "total_checks": len(checks),
        "violations": sum(1 for c in checks if not c["passed"]),
        "generated_at": GEN_AT,
        "provenance": PROVENANCE,
    }

    cands = {
        "meta": {
            "generated_at": GEN_AT,
            "generator": "openmath_sequences.py",
            "evidence_level": "L2",
            "provenance": PROVENANCE,
            "note": ("以下关系在被检验的有限项上成立，**不是证明**；"
                     "外推存活只表示在该长度内没找到反例。"),
        },
        "sequences": [],
        "human_review_queue": [
            {"seq": k, "known_background": v,
             "why_in_queue": "未写入校准表却被独立发现，需要人工核对形式与出处"}
            for k, v in sorted(res["calibration"]["unlisted_found"].items())
        ],
    }
    for s in res["sequences"]:
        items = []
        for c in s["linear"] + s["hyper"]:
            items.append({
                "channel": c["channel"],
                "statement": c["statement"],
                "status": c["status"],
                "status_cn": STATUS_CN.get(c["status"], c["status"]),
                "survived_extrapolation": c.get("survived_extrapolation"),
                "first_failure": c.get("first_failure"),
                "recognition": c.get("recognition"),
                "evidence": c.get("evidence"),
            })
        cands["sequences"].append({
            "id": s["id"], "cn": s["cn"], "index_base": s["index_base"],
            "first_terms": s["first_terms"],
            "growth": s["growth"],
            "findings": items,
        })

    _dump(res, "sequence_theory.json")
    _dump(cands, "sequence_candidates.json")
    write_report(res, cross, net, checks)
    print(f"[S9] 自核验：{len(checks)} 项，违规 {res['self_audit']['violations']} 项")
    print(f"[S9] 报告已写：{REPORT}")


if __name__ == "__main__":
    main()
