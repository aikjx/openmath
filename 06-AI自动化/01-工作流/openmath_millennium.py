# -*- coding: utf-8 -*-
"""
millennium：千禧难题档案流水线（S10）
==============================================================================

  M1. 七道千禧难题的**命题形式化**：写成机器可读的逻辑方程（量词结构 / 谓词 /
      反命题 / **有限影子**），并显式标注"影子是否蕴含原命题"。
  M2. **套娃分解**：把每题递归拆成子命题树，直到叶节点是已知定理、可算检验或开放叶。
      开放叶**如实保留**，不假装闭合。
  M3. **有限影子实验**：跑真计算（RH 零点计数、BSD 点计数、NS Burgers 激波、
      HODGE 组合 Hodge、PNP SAT 相变、POINCARE 同调必要条件）。
  M4. 产出：
        - 09-数据/millennium_dossier.json
        - 06-AI自动化/01-工作流/MILLENNIUM_REPORT.md
  M5. 自核验（8 项）。

与其它阶段的根本区别：
  S1-S9 是**生产**（我们声称发现了什么），S10 是**档案与边界**（我们到底能碰什么）。
  本阶段**不产出任何新的数学主张**，也不声称推进了任何一道难题的解决。

诚实红线（00-宪章/02-诚实红线.md）：
  - 七道题的 `shadow_implies_full` 全部为 False。这是结构性的，不是保守：
    有限截断不可能蕴含无限命题。
  - 开放叶数不为 0 是**正常结果**。把它写成 0 才是伪造。
  - 每个实验的 caveat 必须写清"能说明什么、不能说明什么"，不得只写"仅作参考"。
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
REPORT = os.path.join(_HERE, "MILLENNIUM_REPORT.md")
ENGINE_SRC = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理自动生成，未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = (
    "本阶段为 L0/L2 级档案与计算校验产物，**非证明**。七道千禧难题中六道未解，"
    "本流水线不声称解决任何一道，也不声称对任何一道提供了证明性证据。"
    "所有计算均为有限范围内的 L2 数值证据。"
)

sys.path.insert(0, ENGINE_SRC)

from openmath_sys import millennium as MM  # noqa: E402
from openmath_sys import millennium_lab as ML  # noqa: E402


def _dump(name: str, obj) -> None:
    with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


# ---------------------------------------------------------------------------
# 自核验
# ---------------------------------------------------------------------------
def self_audit(doc: dict) -> list:
    checks = []

    def add(name, bad, why):
        checks.append({"check": name, "passed": not bad,
                       "violations": bad[:6], "why": why})

    probs = doc["problems"]

    # 1) 七道题必须齐
    ids = {p["id"] for p in probs}
    want = {"RH", "PNP", "NS", "BSD", "HODGE", "YM", "POINCARE"}
    add("七道千禧难题齐备", sorted(want - ids),
        "少一道就会让档案看起来是完整的，而它并不完整")

    # 2) 每题都必须有逻辑方程的四件套
    missing = [p["id"] for p in probs
               if not (p.get("formula") and p.get("quantifiers")
                       and p.get("predicate") and p.get("negation"))]
    add("每题都有量词/谓词/反命题", missing,
        "缺反命题就没法走证伪通道——只能证实不能证伪的档案是残缺的")

    # 3) **关键**：影子不得被声称蕴含原命题
    lying = [p["id"] for p in probs if p.get("shadow_implies_full")]
    add("没有任何题声称'有限影子蕴含原命题'", lying,
        "这是本档案最重要的一条红线：有限截断不可能蕴含无限命题")

    # 4) 每题都必须写清影子不蕴含的理由
    no_note = [p["id"] for p in probs
               if p.get("finite_shadow") and not p.get("shadow_note")]
    add("有影子的题都写了'影子不蕴含原命题'的理由", no_note,
        "只写 False 不写理由，读者会以为那只是没做")

    # 5) 未解题的分解树必须有开放叶（开放叶为 0 = 假装全闭合）
    closed_fake = [p["id"] for p in probs
                   if p["status"] == "UNSOLVED"
                   and p["leaf_counts"].get("open", 0) == 0]
    add("未解题的分解树保留开放叶", closed_fake,
        "未解难题却没有开放叶，等于声称我们知道怎么往下走")

    # 6) 每个实验都必须带 caveat，且 caveat 不能太短
    thin = [e["id"] for e in doc["experiments"]
            if len(e.get("caveat", "")) < 40]
    add("每个实验都有实质性的口径说明", thin,
        "caveat 过短等于没写，读者会误以为实验支持了命题")

    # 7) 实验不得声称证明了什么
    claiming = [e["id"] for e in doc["experiments"]
                if "证明" in (e.get("caveat", "") + json.dumps(e, ensure_ascii=False))
                and "不" not in e.get("caveat", "")[:200]]
    add("实验结论中不含证明性声称", claiming,
        "L2 证据被写成证明是本项目最严重的越线")

    # 8) 已解决的题必须标注证明者，不得被计为我们的成果
    no_attr = [p["id"] for p in probs
               if p["status"] == "SOLVED" and not p.get("proof_by")]
    add("已解题标注了证明者", no_attr,
        "不标注出处会让人误以为是我们证的")

    return checks


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------
def _tbl(rows, header):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out) + "\n"


def write_report(doc: dict) -> None:
    L = []
    s = doc["summary"]
    L.append("# 千禧难题档案 · 逻辑方程 / 套娃分解 / 有限影子\n")
    L.append(f"- 生成时间：{GEN_AT}")
    L.append(f"- 证据等级：L0/L2（**非证明**）")
    L.append(f"- provenance：AI 辅助生成，未经人类复核\n")
    L.append("## 0. 一句话口径\n")
    L.append("本档案**不声称解决任何一道千禧难题**，也不声称提供了任何证明性证据。"
             "它做的是三件事：把命题写成逻辑方程、把命题递归拆成子命题树、"
             "在**有限影子**上跑真计算。七道题的 `shadow_implies_full` **全部为 False**——"
             "这是结构性的，不是保守：有限截断不可能蕴含无限命题。\n")

    L.append("## 1. 总览\n")
    L.append(_tbl(
        [[p["id"], p["name"], p["status"],
          "有" if p.get("finite_shadow") else "无",
          "否" if not p.get("shadow_implies_full") else "**是**",
          p["leaf_counts"].get("theorem", 0),
          p["leaf_counts"].get("computable", 0),
          p["leaf_counts"].get("open", 0),
          p["decomposition_depth"]]
         for p in doc["problems"]],
        ["ID", "问题", "状态", "有限影子", "影子蕴含原命题", "定理叶", "可算叶", "开放叶", "分解深度"]))
    L.append(f"\n未解 {s['n_unsolved']} 道 / 已解 {s['n_solved']} 道；"
             f"有有限影子的 {s['n_with_finite_shadow']} 道；"
             f"声称影子蕴含原命题的 **{s['n_shadow_implies_full']}** 道；"
             f"开放叶合计 **{s['total_open_leaves']}** 个。\n")
    L.append("> 开放叶不为 0 是**正常结果**，不是缺陷。把它写成 0 才是伪造。\n")

    L.append("## 2. 逐题：逻辑方程与有限影子\n")
    for p in doc["problems"]:
        L.append(f"### {p['id']} · {p['name']}　（`{p['status']}`）\n")
        L.append(f"- **命题**：{p.get('statement','')}")
        L.append(f"- **逻辑方程**：`{p['formula']}`")
        qs = "；".join(f"{q['kind']} {q['var']} ∈ {q['domain']}"
                       for q in p.get("quantifiers", []))
        L.append(f"- **量词结构**：{qs}")
        L.append(f"- **待证谓词**：{p.get('predicate','')}")
        L.append(f"- **反命题（证伪通道）**：`{p.get('negation','')}`")
        if p.get("finite_shadow"):
            L.append(f"- **有限影子**（范围 {p.get('shadow_bound')}）：{p['finite_shadow']}")
            L.append(f"- **影子是否蕴含原命题**：{'是' if p.get('shadow_implies_full') else '**否**'}")
            L.append(f"- **为什么否**：{p.get('shadow_note','')}")
        else:
            L.append("- **有限影子**：无。原因：" + str(p.get("shadow_note", "")))
        if p.get("proof_by"):
            L.append(f"- **已证者**：{p['proof_by']}")
        if p.get("theoretical_gap"):
            L.append(f"- **理论缺口**：{p['theoretical_gap']}")
        L.append("")

    L.append("## 3. 套娃分解树\n")
    L.append("递归在开放叶处停止。**开放叶就是“我们不知道怎么往下走”的位置**，"
             "它们被如实保留。其中若干开放叶下面挂的是**已证的不可能性定理**——"
             "例如 P vs NP 下的三个障碍（Baker–Gill–Solovay / Razborov–Rudich / "
             "Aaronson–Wigderson），那才是这套分解真正的深度所在。\n")

    def walk(node, depth):
        mark = {"theorem": "[定理]", "computable": "[可算]", "open": "[**开放**]"}.get(
            node["kind"], "[ ]")
        L.append("  " * depth + f"- {mark} {node['text']}")
        if node.get("note"):
            L.append("  " * depth + f"  - 注：{node['note']}")
        for c in node.get("children", []):
            walk(c, depth + 1)

    for p in doc["problems"]:
        L.append(f"### {p['id']}\n")
        walk(p["decomposition"], 0)
        L.append("")

    L.append("## 4. 有限影子实验（真计算）\n")
    for e in doc["experiments"]:
        L.append(f"### {e['id']}　（{e['problem']}）\n")
        if e["id"] == "zeta_zero_count":
            L.append(f"- 高度 T = {e['T']}；Hardy Z 符号变号数 **{e['zeros_found']}**；"
                     f"Riemann–von Mangoldt 主项 **{e['von_mangoldt_main_term']}**；"
                     f"S(T) 估计 **{e['S_T_estimate']:+g}**")
            L.append(f"- 前 10 个零点对照教科书：{e['calibration']['matched_within_0.02']}"
                     f"/{e['calibration']['checked']} 命中，最大误差 "
                     f"{e['calibration']['max_error']}")
        elif e["id"] == "xi_functional_equation":
            L.append(f"- ξ(s)=ξ(1−s) 全部通过：{e['all_ok']}（最大相对差 "
                     f"{max(r['rel_diff'] for r in e['rows']):.2e}）")
        elif e["id"] == "ec_point_count":
            L.append(f"- 素数 p < {e['pmax']}；Hasse 界检验 {e['hasse_ok']}/{e['hasse_checked']}"
                     f" 全部通过：{e['hasse_all_ok']}")
            for c in e["curves"]:
                L.append(f"  - {c['name']}：{c['n_primes']} 个素数，"
                         f"mean(a_p/√p) = {c['mean_ap_over_sqrt_p']}")
        elif e["id"] == "ns_burgers_shock":
            L.append(f"- ν = {e['nu']}；理论激波时刻 t* = {e['theoretical_shock_time']}")
            L.append(f"- 特征线估计量：{e['characteristic_estimates']}，"
                     f"最细网格误差 {e['characteristic_finest_error']}，"
                     f"细分下收敛：{e['characteristic_converging']}")
            L.append(f"- 梯度越阈估计量：{e['threshold_estimates']}，"
                     f"细分下收敛：**{e['threshold_converging']}**")
        elif e["id"] == "combinatorial_hodge":
            for r in e["results"]:
                L.append(f"- {r['complex']}：b = {r['betti']}（教科书 {r['expected_betti']}）"
                         f"，调和维数 = {r['harmonic_dim']}，"
                         f"Hodge 恒等式成立：{r['hodge_identity_holds']}")
        elif e["id"] == "sat_phase_transition":
            L.append("| α | m | 可满足率 | 决策节点中位数 |")
            L.append("|---|---|---|---|")
            for r in e["rows"]:
                L.append(f"| {r['alpha']} | {r['m']} | {r['sat_fraction']} | "
                         f"{r['median_decisions']} |")
            L.append("")
        elif e["id"] == "homology_sphere_check":
            L.append(f"- {e['complex']}：b = {e['betti']}（期望 {e['expected_betti']}）"
                     f"，匹配：{e['matches']}")
        L.append(f"- **口径**：{e['caveat']}\n")

    L.append("## 5. 自核验\n")
    for c in doc["self_audit"]:
        L.append(f"- {'通过' if c['passed'] else '**违规**'}：{c['check']}"
                 + ("" if c["passed"] else f"　→ {c['violations']}"))
    n_bad = sum(1 for c in doc["self_audit"] if not c["passed"])
    L.append(f"\n自核验 {len(doc['self_audit'])} 项，违规 **{n_bad}** 项。\n")

    L.append("## 6. 本阶段没有做的事\n")
    L.append("- **没有**证明或推进任何一道千禧难题。")
    L.append("- **没有**把任何开放叶写成闭合。")
    L.append("- **没有**为 YM 编造实验：该题的前提（四维量子测度的严格构造）尚未完成，"
             "在测度都不存在的情况下不存在可计算的谱。")
    L.append("- **没有**把校准件（Hasse 界、函数方程、b_k = dim ker Δ_k、"
             "S³ 的同调）当成对猜想的证据——它们检验的是**我们的代码**，不是数学。\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------------------
def main() -> int:
    print("[S10] 千禧难题档案：开始")
    doc = MM.build_dossier_structure()
    lab = ML.run_all()
    doc["experiments"] = lab["experiments"]
    doc["experiments_summary"] = lab["summary"]
    doc["meta"] = {
        "generated_by": "06-AI自动化/01-工作流/openmath_millennium.py",
        "generated_at": GEN_AT,
        "provenance": PROVENANCE,
        "honesty": HONESTY,
        "evidence_grade": "L0/L2",
        "claim": "none",
        "claim_note": "本阶段不提出任何新的数学主张，也不声称推进任何一道千禧难题。",
    }
    doc["self_audit"] = self_audit(doc)

    n_open = doc["summary"]["total_open_leaves"]
    n_bad = sum(1 for c in doc["self_audit"] if not c["passed"])
    print(f"     命题 {doc['summary']['n_problems']} 道（未解 "
          f"{doc['summary']['n_unsolved']}）；开放叶 {n_open} 个；"
          f"实验 {len(doc['experiments'])} 个")
    print(f"[S10] 自核验：{len(doc['self_audit'])} 项，违规 {n_bad} 项")

    _dump("millennium_dossier.json", doc)
    write_report(doc)
    print(f"[S10] 报告已写：{REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
