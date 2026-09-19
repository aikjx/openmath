# -*- coding: utf-8 -*-
"""
综合：处理方法全谱 · 未破解验证 · 有限化定理 · 扩展维度框架
==============================================================

  J. 处理方法全谱 —— 把方法体系按**处理逻辑范式**（而非数学领域）重新归类，
     暴露"我们能做哪一类处理、哪一类完全空白"。

  K. 未破解验证 —— 对每条未解猜想，记录已做的验证，并**严格论证**
     为什么这些验证不构成证明（给出具体的逻辑缺口，而非笼统声明）。

  L. 有限化定理 —— 把无限域猜想**有限化**为可穷举的有限命题，
     对这些有限命题给出**逻辑上严格的穷举演绎证明**。
     并明确声明：有限定理**不蕴含**原猜想。

  M. 扩展维度框架 —— 在四维（句法/语义/结构/计算）之上增加
     D5 证据维度与 D6 元认知维度。

诚实红线（00-宪章/02-诚实红线.md）：
  - **本流水线不证明、也不能证明任何未解猜想。** 凡声称证明皆为欺诈。
  - L 阶段的定理是**有限域上的穷举证明**，逻辑严格，但其论域是有限集，
    与原猜想的无限论域之间存在**不可跨越的逻辑鸿沟**。
  - 数值验证（含抽样）在任何意义上都不是证明。
"""
from __future__ import annotations

import json
import os
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):
    REPO = os.path.dirname(REPO)

DATA_DIR = os.path.join(REPO, "09-数据")
REPORT = os.path.join(_HERE, "SYNTHESIS_REPORT.md")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理自动生成，未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = ("本文件为 L0/L2 级整理与计算产物。有限域穷举结论在其论域内严格，"
           "但**不蕴含**任何无限域猜想的证明。")


def _load(n):
    with open(os.path.join(DATA_DIR, n), encoding="utf-8") as f:
        return json.load(f)


def _dump(obj, n):
    with open(os.path.join(DATA_DIR, n), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


# ===========================================================================
# J. 处理方法全谱：按"处理逻辑范式"而非数学领域分类
# ===========================================================================
PARADIGMS = {
    "representation": ("表示", "把对象编码为可机器处理的形式（解析/建模）"),
    "evaluation": ("求值", "代入具体数值/参数计算结果"),
    "decision": ("判定", "判断对象属于哪个类别或是否具有某性质"),
    "construction": ("构造", "生成满足条件的数学对象或集合"),
    "search": ("搜索", "在（可能无限的）空间中寻找目标点/根/解"),
    "solving": ("求解", "求出未知量的精确或数值解"),
    "transform": ("变换", "把对象等价改写为另一形式"),
    "approximation": ("逼近", "给出渐近式或上/下界估计"),
    "reduction": ("归约", "把问题化归到另一（已知）问题或缩小论域"),
    "structure_computation": ("结构计算", "计算代数/拓扑不变量（秩、上同调等）"),
    "simulation": ("模拟", "按规则演化系统并观察统计行为"),
    "analogy": ("类比", "把对象映射到另一领域，借用其已知结构"),
}

PARADIGM_MAP = {
    "ast_parse": "representation",
    "arith_eval": "evaluation",
    "transc_eval": "evaluation",
    "l_function_evaluation": "evaluation",
    "poly_classify": "decision",
    "prime_sieve": "construction",
    "sieve_theory": "construction",
    "rad_computation": "construction",
    "exhaustive_search": "search",
    "numeric_root": "search",
    "numeric_zero_search": "search",
    "linear_solve": "solving",
    "quadratic_formula": "solving",
    "gaussian_elimination": "solving",
    "factorization": "transform",
    "grobner_basis": "transform",
    "eigen_decomposition": "transform",
    "symbolic_diff": "transform",
    "symbolic_int": "transform",
    "renormalization": "transform",
    "limit_computation": "approximation",
    "asymptotic_estimation": "approximation",
    "circle_method": "approximation",
    "energy_estimate": "approximation",
    "modular_analysis": "reduction",
    "complexity_reduction": "reduction",
    "elliptic_curve_computation": "structure_computation",
    "cohomology_computation": "structure_computation",
    "algebraic_complexity": "structure_computation",
    "structure_computation": "structure_computation",
    "homology_computation": "structure_computation",
    "map_iteration": "simulation",
    "pde_numerical_simulation": "simulation",
    "lattice_qcd_numeric": "simulation",
    "ricci_flow_analysis": "simulation",
    "random_matrix_analogy": "analogy",
}


def build_paradigms(methods_doc: dict) -> dict:
    buckets: dict[str, list[dict]] = {}
    for m in methods_doc.get("methods", []):
        p = PARADIGM_MAP.get(m["id"], "evaluation")
        buckets.setdefault(p, []).append(m)

    rows = []
    for pid, (name, desc) in PARADIGMS.items():
        ms = buckets.get(pid, [])
        impl = [m for m in ms if m.get("implemented")]
        rows.append({
            "paradigm": pid, "name": name, "description": desc,
            "methods_total": len(ms),
            "methods_implemented": len(impl),
            "implemented_ids": [m["id"] for m in impl],
            "missing_ids": [m["id"] for m in ms if not m.get("implemented")],
            "coverage": round(len(impl) / len(ms), 4) if ms else None,
        })
    rows.sort(key=lambda r: (-r["methods_implemented"], r["paradigm"]))

    blank = [r for r in rows if r["methods_implemented"] == 0]
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_synthesis.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "note": ("按**处理逻辑范式**（我们能做哪一类操作）而非数学领域归类。"
                     "同一范式可跨多个数学领域复用；范式层面的空白比领域层面的空白更致命，"
                     "因为它意味着'这一类操作根本不会做'。"),
        },
        "summary": {
            "paradigms": len(rows),
            "methods_classified": sum(r["methods_total"] for r in rows),
            "fully_blank_paradigms": [r["paradigm"] for r in blank],
        },
        "paradigms": rows,
    }


# ===========================================================================
# K. 未破解验证：每条猜想做了什么验证、为什么不构成证明
# ===========================================================================
# 逻辑缺口类型学：这是"为什么没破解"的严格答案，而非笼统声明。
GAP_TYPES = {
    "finiteness": ("有限性鸿沟",
                   "穷举/验证只覆盖有限子集，而猜想是**无限域的全称命题**。"
                   "任何有限证据在逻辑上都无法排除'更大的反例'。"),
    "skewes_warning": ("Skewes 型警告",
                       "存在**已被严格证明**的先例：π(x)<li(x) 在天文数字范围内恒成立，"
                       "但 Littlewood 证明了差值会无穷次变号（首个变号点小于 Skewes 数 ~10^316）。"
                       "这**严格证明**了'长期数值吻合不能推出无限结论'。"),
    "precision": ("精度鸿沟",
                  "浮点/数值方法存在截断与分支切割误差；"
                  "本流水线已实测到复变分支切割导致的'假阴性'（atanh 恒等式在 |z|>1 时虚部反号）。"),
    "structure": ("结构鸿沟",
                  "数值证据只触及可计算的实例，未触及猜想所断言的**底层结构**"
                  "（如谱解释、上同调类、复杂性类分离），无法转化为结构性论证。"),
    "uncomputable_aspect": ("不可计算成分",
                            "猜想的实质内容包含当前无算法可判定的部分，"
                            "计算能力再强也不产生证明。"),
}

# 每条猜想的验证现状与缺口（诚实：只写我们**实际做过**的验证）
VERIFICATION = {
    "RH": {
        "done": "未做任何零点搜索（numeric_zero_search 未实现）。"
                "仅实现了 asymptotic_estimation，可对照 π(x) 与 li(x)。",
        "type": "无直接验证",
        "gaps": ["finiteness", "skewes_warning", "structure"],
    },
    "GC": {
        "done": "穷举验证：n ≤ 10000 的每个偶数都有哥德巴赫分拆。",
        "type": "有限域穷举（演绎严格，但论域有限）",
        "gaps": ["finiteness", "structure"],
    },
    "TPC": {
        "done": "筛法精确计数：≤ 200000 内孪生素数 2160 对。",
        "type": "有限域精确计数（只说明'存在多少'，不说明'无穷多'）",
        "gaps": ["finiteness"],
    },
    "COLLATZ": {
        "done": "穷举验证：n ≤ 20000 全部迭代到 1；并按 mod 6 统计停止时间。",
        "type": "有限域穷举（演绎严格，但论域有限）",
        "gaps": ["finiteness", "structure"],
    },
    "ABC": {
        "done": "穷举搜索：c ≤ 3000 内 quality>1 的三元组 57 个，最高 q=1.4557。",
        "type": "有限域穷举（且猜想本身状态为 DISPUTED）",
        "gaps": ["finiteness", "structure"],
    },
    "BSD": {"done": "无（椭圆曲线计算、L 函数求值均未实现）。", "type": "无",
            "gaps": ["structure", "uncomputable_aspect"]},
    "HODGE": {"done": "无（上同调计算未实现）。", "type": "无",
              "gaps": ["structure", "uncomputable_aspect"]},
    "NS": {"done": "无（PDE 数值模拟、能量估计均未实现）。", "type": "无",
           "gaps": ["structure", "precision"]},
    "PNP": {"done": "无（复杂性归约、代数复杂性均未实现）。", "type": "无",
            "gaps": ["structure", "uncomputable_aspect"]},
    "YM": {"done": "无（格点数值模拟、重整化均未实现）。", "type": "无",
           "gaps": ["structure", "precision"]},
    "POINCARE": {
        "done": "本流水线未做验证。该猜想已由**人类数学家**解决"
                "（Perelman, 2003，属 L4 级人类证明），此处列出仅为登记表完整性，"
                "**不是本体系的成果**。",
        "type": "非本体系成果",
        "gaps": [],
    },
}


def build_verification(conj_doc: dict) -> dict:
    rows = []
    for c in conj_doc.get("conjectures", []):
        cid = c["id"]
        v = VERIFICATION.get(cid, {"done": "无", "type": "无", "gaps": ["structure"]})
        rows.append({
            "id": cid, "name": c["name"], "status": c["status"],
            "proof_claimed": c.get("proof_claimed", False),
            "verification_done": v["done"],
            "verification_type": v["type"],
            # 由本流水线产出的一切验证，在任何情况下都不构成证明
            "constitutes_proof": False,
            "gap_types": v["gaps"],
            "gap_explanations": [GAP_TYPES[g][1] for g in v["gaps"]],
            "is_our_result": not (c["status"] == "SOLVED"),
        })
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_synthesis.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "disclaimer": ("**本流水线未破解任何未解猜想。** 下表如实记录每条猜想"
                           "实际做过的验证，并给出'为什么不构成证明'的具体逻辑缺口。"),
        },
        "gap_typology": {k: {"name": v[0], "explanation": v[1]}
                         for k, v in GAP_TYPES.items()},
        "verifications": rows,
    }


# ===========================================================================
# L. 有限化定理：把无限猜想化为有限命题，给出严格的穷举演绎证明
# ===========================================================================
def build_finite_theorems(nt_doc: dict) -> dict:
    """把猜想**有限化**，对有限命题给出穷举证明。

    关键区分（数学上是本质的）：
      - exhaustive_deductive：穷举了论域中**每一个**元素，结论在该有限论域上
        逻辑严格（演绎有效）。这是**真正的证明**——只是论域有限。
      - sampled_numerical：只抽取部分样本，**不是证明**，仅为证据。
    """
    e1 = nt_doc["experiments"]["E1_abc_quality"]
    e2 = nt_doc["experiments"]["E2_goldbach"]
    e3 = nt_doc["experiments"]["E3_twin_primes"]
    e4 = nt_doc["experiments"]["E4_prime_asymptotics"]
    e5 = nt_doc["experiments"]["E5_collatz_modular"]
    top = e1["top_by_quality"][0] if e1["top_by_quality"] else None
    lx = e4.get("at_largest_x") or {}

    theorems = []

    if e2["all_even_have_partition"]:
        theorems.append({
            "id": "FT-GC-10000",
            "name": "哥德巴赫猜想的有限化（n ≤ 10000）",
            "statement": f"对所有偶数 n，4 ≤ n ≤ {e2['limit']}，存在素数 p, q 使得 n = p + q。",
            "proof_type": "exhaustive_deductive",
            "is_proof": True,
            "method": "对区间内每一个偶数逐一检验（素数表由埃拉托斯特尼筛精确构造）",
            "domain": f"有限集 {{n 偶数 : 4 ≤ n ≤ {e2['limit']}}}",
            "result": True,
            "evidence": {"limit": e2["limit"],
                         "min_partitions": e2["min_partitions"]},
            "does_not_imply": "哥德巴赫猜想（对所有偶数）。有限论域之外无任何断言。",
        })

    theorems.append({
        "id": "FT-ABC-3000",
        "name": "ABC 三元组质量的有限化上界（c ≤ 3000）",
        "statement": (f"在所有满足 a+b=c、gcd(a,b)=1、c ≤ {e1['c_max']} 的三元组中，"
                      f"quality q = ln c / ln rad(abc) 的最大值为 "
                      f"{top['quality'] if top else 'N/A'}"
                      + (f"，在 (a,b,c)=({top['a']},{top['b']},{top['c']}) 处取得。"
                         if top else "。")),
        "proof_type": "exhaustive_deductive",
        "is_proof": True,
        "method": "枚举全部 (a,c) 组合并用筛法预计算 rad 表，完整穷举论域",
        "domain": f"有限集 {{三元组 : c ≤ {e1['c_max']}}}",
        "result": top["quality"] if top else None,
        "evidence": {"triples_with_q_above_1": e1["triples_with_quality_above_1"],
                     "top": top},
        "does_not_imply": "ABC 猜想。已知更高 quality 的例子存在于更大 c（如 q≈1.6299），"
                          "故本上界**不是**全局上界，仅是论域内的精确值。",
    })

    theorems.append({
        "id": "FT-COLLATZ-20000",
        "name": "Collatz 迭代的有限化（n ≤ 20000）",
        "statement": f"对所有 n，1 ≤ n ≤ {e5['n_max']}，Collatz 迭代序列在有限步内到达 1。",
        "proof_type": "exhaustive_deductive",
        "is_proof": True,
        "method": "逐个计算总停止时间（带记忆化），全部有限终止",
        "domain": f"有限集 {{n : 1 ≤ n ≤ {e5['n_max']}}}",
        "result": True,
        "evidence": {"n_max": e5["n_max"],
                     "overall_mean_steps": e5["overall_mean_steps"]},
        "does_not_imply": "Collatz 猜想。已知的验证上限远高于此（~10^20 量级），"
                          "但**任何**有限上限都不构成证明。",
    })

    theorems.append({
        "id": "FT-TWIN-200000",
        "name": "孪生素数的有限化精确计数（≤ 200000）",
        "statement": f"在区间 [1, {e3['limit']}] 内，孪生素数对恰有 {e3['twin_pairs']} 对。",
        "proof_type": "exhaustive_deductive",
        "is_proof": True,
        "method": "埃拉托斯特尼筛精确构造素数表后逐点计数",
        "domain": f"有限集 {{p ≤ {e3['limit']} : p 与 p+2 均为素数}}",
        "result": e3["twin_pairs"],
        "evidence": {"largest_pair": e3["largest_pair"]},
        "does_not_imply": "孪生素数猜想（有无穷多对）。计数结果只描述有限区间。",
    })

    if lx:
        theorems.append({
            "id": "FT-PI-100000",
            "name": "素数计数的精确值（x = 10^5）",
            "statement": f"π({lx['x']}) = {lx['pi_x']}。",
            "proof_type": "exhaustive_deductive",
            "is_proof": True,
            "method": "筛法精确计数（非估计）",
            "domain": f"有限集 {{素数 p ≤ {lx['x']}}}",
            "result": lx["pi_x"],
            "evidence": {"li_x": lx["li_x"], "x_over_ln_x": lx["x_over_ln_x"],
                         "rel_err_li": lx["rel_err_li"],
                         "rel_err_x_over_ln": lx["rel_err_x_over_ln"]},
            "does_not_imply": "素数定理（无限极限命题）。此处仅给出单点精确值。"
                              "注意：li 与 π 的差值在有限处很小，**不排除**其在更大 x 处变号"
                              "（Littlewood 定理，见 Skewes 型警告）。",
        })

    # 对照组：抽样验证**不是**证明（教学性对比，必须保留）
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_synthesis.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "critical_distinction": (
                "**穷举演绎证明**（exhaustive_deductive）：论域有限且被**逐一**检验，"
                "结论在该论域内逻辑严格，是真正的证明。\n"
                "**抽样数值验证**（sampled_numerical）：只检验部分样本，"
                "无论样本多少都**不是证明**，仅为支持性证据。\n"
                "本体系产生的所有'定理'均属前者（有限论域），"
                "且**无一蕴含**对应的无限域猜想。"
            ),
            "why_finite_is_not_enough": (
                "从有限到无限是**量词层面的跳跃**：有限定理是"
                "∀n∈S（S 有限），猜想是 ∀n∈ℕ（无限）。"
                "在经典逻辑中，对有限多个实例的验证永远无法演绎出全称命题——"
                "这不是'证据不够多'的问题，而是**推理形式本身不允许**。"
            ),
        },
        "summary": {
            "theorems": len(theorems),
            "all_exhaustive": all(t["proof_type"] == "exhaustive_deductive"
                                  for t in theorems),
            "none_implies_conjecture": True,
        },
        "theorems": theorems,
    }


# ===========================================================================
# M. 扩展维度框架
# ===========================================================================
def build_extended_dimensions() -> dict:
    dims = [
        {"id": "D1", "name": "句法", "question": "它是什么形式？",
         "operation": "解析为结构（AST）", "origin": "既有四维框架"},
        {"id": "D2", "name": "语义", "question": "它指称什么？",
         "operation": "链接到 OpenMath CD 符号定义", "origin": "既有四维框架"},
        {"id": "D3", "name": "结构", "question": "它属于哪类对象？",
         "operation": "形态分类（线性/二次/超越/…）", "origin": "既有四维框架"},
        {"id": "D4", "name": "计算", "question": "它的值/解是什么？",
         "operation": "求值、求解、恒等式验证", "origin": "既有四维框架"},
        {"id": "D5", "name": "证据", "question": "这个结论凭什么成立？",
         "operation": "标注证据等级 L0–L6、来源、可否证性、论域边界",
         "origin": "本轮新增"},
        {"id": "D6", "name": "元认知", "question": "我该用什么方法、以及我是否根本做不到？",
         "operation": "方法选择与缺口识别、**不可能性意识**"
                      "（明确判定'本体系无能力处理'而非给出虚假进展）",
         "origin": "本轮新增"},
    ]
    return {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_synthesis.py",
            "generated_at": GEN_AT, "provenance": PROVENANCE, "honesty": HONESTY,
            "scope_note": ("这是**认识论/工程性的处理思维框架**（用于组织计算与标注证据），"
                           "**不是新的数学理论**，不对任何数学对象作出新断言。"),
        },
        "dimensions": dims,
        "meta_paradigm": {
            "name": "有限化 → 验证 → 缺口识别 → 有限证明",
            "steps": [
                "1) 把无限命题**有限化**为可穷举的有限命题（明确论域边界）",
                "2) 对有限命题执行**穷举演绎**（得到严格结论）",
                "3) 用**逻辑缺口类型学**判定为何该结论不能外推到无限",
                "4) 输出**有限定理 + 明确的不可外推声明**",
            ],
            "value": "把'我以为我证明了'替换为'我证明了什么、以及我没证明什么'，"
                     "二者都给出可核验的依据。",
        },
    }


# ===========================================================================
# 报告
# ===========================================================================
def write_report(par, ver, ft, ext) -> None:
    L = []
    L.append("# 综合：处理方法全谱 · 未破解验证 · 有限化定理 · 扩展维度\n")
    L.append(f"> 生成时间：{GEN_AT}　|　`06-AI自动化/01-工作流/openmath_synthesis.py`　|　"
             f"证据等级：**L0/L2**　|　`provenance.ai_assisted = true`\n")
    L.append("> **本流水线未破解任何未解猜想。** 下文如实区分「我严格证明了什么（有限论域）」"
             "与「我没有证明什么（无限论域）」。\n")

    L.append("\n## 1. 处理方法全谱（按处理逻辑范式）\n")
    L.append("把方法按**处理逻辑范式**而非数学领域归类——同一范式可跨领域复用，"
             "因此范式层面的空白比领域空白更致命。\n")
    L.append("| 范式 | 含义 | 方法数 | 已实现 | 覆盖率 |")
    L.append("|---|---|---|---|---|")
    for r in par["paradigms"]:
        cov = "—" if r["coverage"] is None else f"{r['coverage']:.0%}"
        L.append(f"| {r['name']} `{r['paradigm']}` | {r['description']} | "
                 f"{r['methods_total']} | {r['methods_implemented']} | {cov} |")
    L.append("")
    blank = par["summary"]["fully_blank_paradigms"]
    if blank:
        # 动态生成：不要写死范式名，否则会与实际统计不符
        blank_names = "、".join(PARADIGMS[b][0] for b in blank)
        L.append(f"**完全空白的范式**（无任何已实现方法）：{blank_names}"
                 f"（{', '.join(blank)}）。\n")
        notes = []
        if "structure_computation" in blank:
            notes.append("**结构计算**空白 → BSD（需椭圆曲线秩）与 Hodge（需上同调）"
                         "的方法覆盖率为 0")
        if "analogy" in blank:
            notes.append("**类比**空白 → RH 的随机矩阵/谱解释路线无从下手")
        if "transform" in blank:
            notes.append("**变换**空白 → 无法做因式分解、符号微积分、Gröbner 基等"
                         "等价改写，符号层面的推理全部缺位")
        if notes:
            L.append("> 关键发现：" + "；".join(notes) + "。"
                     "**这不是数据不够，而是我们根本不会做那一类操作**——"
                     "再多的 CD 与论文也无法弥补范式层面的空白。\n")

    L.append("\n## 2. 未破解验证：做了什么，为什么不构成证明\n")
    L.append("| 猜想 | 状态 | 已做验证 | 是否构成证明 | 逻辑缺口 |")
    L.append("|---|---|---|---|---|")
    for v in ver["verifications"]:
        gaps = ", ".join(GAP_TYPES[g][0] for g in v["gap_types"]) or "—"
        st = v["status"] + ("" if v.get("is_our_result", True) else "（非本体系成果）")
        L.append(f"| {v['name']} | {st} | {v['verification_done'][:46]}… | "
                 f"**否** | {gaps} |")
    L.append("")
    L.append("### 逻辑缺口类型学（为什么数值验证永远不够）\n")
    for k, v in ver["gap_typology"].items():
        L.append(f"- **{v['name']}**：{v['explanation']}")
    L.append("")
    L.append("> 其中 **Skewes 型警告**是有严格证明支撑的先例，值得单独强调："
             "π(x) < li(x) 在极大的范围内恒成立，但 Littlewood（1914）**已证明**"
             "π(x) − li(x) 会无穷次变号，首个变号点小于 Skewes 数（约 10³¹⁶）。"
             "这意味着**再多的数值吻合也可能被更大的反例推翻**——"
             "这不是保守，而是已被证明的事实。\n")

    L.append("\n## 3. 有限化定理（严格证明的部分）\n")
    L.append(f"共 **{ft['summary']['theorems']}** 条。以下每条都在**明确有限的论域**上"
             f"通过**穷举演绎**得到，逻辑严格。\n")
    L.append("| 定理 | 命题 | 论域 | 结果 | 证明方式 |")
    L.append("|---|---|---|---|---|")
    for t in ft["theorems"]:
        L.append(f"| {t['id']} | {t['statement']} | {t['domain']} | "
                 f"`{t['result']}` | 穷举演绎 ✓ |")
    L.append("")
    L.append("> **重要**：这些是**真正的证明**，但论域有限。每一条的 "
             "`does_not_imply` 字段都明确声明了它**不蕴含**原猜想。\n")
    L.append("> 从有限到无限是**量词层面的跳跃**（∀n∈有限集 → ∀n∈ℕ），"
             "在经典逻辑中，对有限多个实例的验证**在推理形式本身上**就无法演绎出全称命题。"
             "这不是'证据不够多'，而是推理不允许。\n")

    L.append("\n## 4. 扩展维度框架（D5/D6）\n")
    L.append("| 维度 | 名称 | 追问 | 操作 | 来源 |")
    L.append("|---|---|---|---|---|")
    for d in ext["dimensions"]:
        L.append(f"| {d['id']} | {d['name']} | {d['question']} | {d['operation']} | {d['origin']} |")
    L.append("")
    mp = ext["meta_paradigm"]
    L.append(f"### 元范式：{mp['name']}\n")
    for s in mp["steps"]:
        L.append(f"- {s}")
    L.append("")
    L.append(f"> {mp['value']}\n")
    L.append("> 诚实标注：这是**认识论/工程性的思维框架**，用于组织计算与标注证据边界，"
             "**不是新的数学理论**。\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    methods_doc = _load("method_system.json")
    conj_doc = _load("conjectures.json")
    nt_doc = _load("nt_experiments.json")

    par = build_paradigms(methods_doc)
    _dump(par, "method_paradigms.json")
    blank = par["summary"]["fully_blank_paradigms"]
    print(f"[J] 处理方法全谱：{par['summary']['paradigms']} 个范式，"
          f"完全空白 {len(blank)} 个 -> {blank}")

    ver = build_verification(conj_doc)
    _dump(ver, "conjecture_verification.json")
    print(f"[K] 未破解验证：{len(ver['verifications'])} 条猜想，"
          f"constitutes_proof 全部为 False；缺口类型 {len(ver['gap_typology'])} 类")

    ft = build_finite_theorems(nt_doc)
    _dump(ft, "finite_theorems.json")
    print(f"[L] 有限化定理：{ft['summary']['theorems']} 条（均为穷举演绎，"
          f"且均不蕴含原猜想）")

    ext = build_extended_dimensions()
    _dump(ext, "extended_dimensions.json")
    print(f"[M] 扩展维度：D1-D6 共 {len(ext['dimensions'])} 维")

    write_report(par, ver, ft, ext)
    print(f"[R] 报告已写：{REPORT}")


if __name__ == "__main__":
    main()
