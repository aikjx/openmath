# -*- coding: utf-8 -*-
"""
audit：独立审计流水线（S8）
==============================================================================

  A1. 调用引擎 audit.run_audit()，用**与被测代码不同的算法**重算 S1-S7 已经
      产出的每一个可复核数字（算术函数、素数计数、li、划分数、图不变量、
      有限群、链复形同调、恒等式验证器的判准率与拒答率）。
  A2. 产出：
        - 09-数据/audit_report.json   全量审计结果（含每条失败的具体数值）
  A3. 生成 06-AI自动化/01-工作流/AUDIT_REPORT.md。
  A4. 自核验：把审计方法用在审计自身上（6 项）。

与其它阶段的区别：
  S1-S7 是**生产**（产出结论），S8 是**体检**（检查前面产出的数字能不能站住）。
  审计不修改被审对象，只报差异；修不修由人决定。

诚实红线（00-宪章/02-诚实红线.md）：
  - 审计通过**不等于**结论正确：它只说明「在给定对象集与给定独立算法下没有发现差异」。
  - 参考值本身也可能是错的（本轮就发生过一次），所以在报告里单列一节记录。
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
REPORT = os.path.join(_HERE, "AUDIT_REPORT.md")
ENGINE_SRC = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理自动生成，未经人类复核，不得作为 L3+ 证据。",
}

sys.path.insert(0, ENGINE_SRC)

from openmath_sys.audit import (  # noqa: E402
    run_audit, SCOPE_NOTE, VERIFIER_TESTSET, VERIFIER_REFUSALS,
)


def _dump(obj, n):
    with open(os.path.join(DATA_DIR, n), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


SECTION_CN = {
    "arithmetic": "算术函数（φ / τ / σ / rad）",
    "primes": "素数计数 π(x)",
    "logarithmic_integral": "对数积分 li(x)",
    "partitions": "整数划分 p(n) 与共轭",
    "graphs": "有限简单图不变量",
    "groups": "有限群结构",
    "homology": "有限链复形同调",
    "identity_verifier": "恒等式验证器",
}

# 本轮（2026-09-19）审计发现并已修复的缺陷。留在这里是为了让每日报告都能看到
# 「这套流水线曾经错在哪」，而不是让它们悄悄消失在 git 历史里。
RECORDED_FIXES = [
    {
        "id": "F1",
        "severity": "高",
        "where": "numeric.verify_identity（S2 数值验证）",
        "symptom": "33 条 CD 公式里有 14 条被判「恒等式不成立」，结论写进了 "
                   "conjecture_verification / numeric_solutions 两个产物。",
        "root_cause": "把超出能力范围的式子也判了真伪：英文散文词 the 被当成变量、"
                      "函数名 sin 被当成变量、iz 与 2z 这类隐式乘法被静默处理成"
                      "单个标识符或常量、待解方程 a*x^2+b*x+c=0 被当成恒等式抽样。",
        "fix": "新增 numeric.screen_identity 准入筛查，先用范围判定（级数/积分/微分/"
               "集合/量词）、变量合理性、隐式乘法检测、待解方程识别把不能验的式子挡掉，"
               "抽样阶段再统计求值错误率，只要有一个点求不出值就判 inconclusive。",
        "effect": "14 条假阴性降到 1 条（且该条已标注为分支约定问题，不是反例）；"
                  "同时用 18 条带标准答案的测试集确认在能力范围内判准率 100%。",
    },
    {
        "id": "F2",
        "severity": "中",
        "where": "theoryforge.graph_invariants（S7 理论锻造）",
        "symptom": "单点图 P1 / K1 / S1 的生成树数为 0。",
        "root_cause": "基尔霍夫矩阵树定理的实现里写了 nv>=2 才取余子式，"
                      "nv=1 掉进 else 分支返回 0；而平凡图有恰好 1 棵生成树（空树）。",
        "fix": "改为先判连通性，连通且 nv==1 时显式返回 1。",
        "effect": "图族 549 项独立复核全部通过（此前 3 项失败）。",
    },
    {
        "id": "F3",
        "severity": "中",
        "where": "numbertheory.logarithmic_integral（S3 数论实验）",
        "symptom": "x=1e5 处 li(x) 相对误差 2.4e-5（用 Ei 幂级数独立复核发现）。",
        "root_cause": "对 [10, x] 只做一次均匀 Simpson，x 大时步长约 25，分辨率不足。",
        "fix": "改为按 10 倍几何分段加密。",
        "effect": "相对误差降到 1e-13 量级；π(x) 与 li(x) 的对比结论不再受积分误差污染。",
    },
    {
        "id": "F4",
        "severity": "提示",
        "where": "审计自身（非生产代码）",
        "symptom": "审计第一轮报 li(x) 系统性偏大 1.045，一度被当作 bug。",
        "root_cause": "参考值记错了：5.120 是 ∫₂¹⁰ dt/ln t，而 li(10)=6.1656。",
        "fix": "改用 Ei 幂级数作为独立参考，不再依赖记忆中的数值。",
        "effect": "提醒：审计的参考值必须来自独立算法或教科书，不能来自印象。",
    },
]


def _tbl(rows, header):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out) + "\n"


def self_audit(res: dict) -> list:
    """把审计方法用在审计自身上。"""
    checks = []

    def add(name, bad, why):
        checks.append({"check": name, "passed": not bad,
                       "violations": bad[:6], "why": why})

    secs = res["sections"]

    # 1) 每个维度都必须真的跑了检查（防止某个维度静默空转）
    empty = [s["name"] for s in secs if s["checks"] == 0]
    add("每个审计维度的检查数必须大于 0", empty,
        "空转的维度会给人「已审计」的错觉，比不审计更危险")

    # 2) 失败项必须带可复核的具体数值
    bad = []
    for s in secs:
        for f in s["failures"]:
            if not f.get("item") or not f.get("got") or not f.get("want"):
                bad.append(s["name"])
    add("每条失败都必须给出 项/实测值/参考值 三项", bad,
        "否则无法复核，等于只是喊了一声不一致")

    # 3) 审计必须覆盖全部已实现的能力维度
    required = set(SECTION_CN)
    missing = sorted(required - {s["name"] for s in secs})
    add("审计必须覆盖全部已实现的能力维度", missing,
        "漏掉的维度在报告里不会显示为空，只会不存在")

    # 4) 恒等式验证器必须同时被测「判准」和「拒答」两面
    vs = next((s for s in secs if s["name"] == "identity_verifier"), None)
    bad = []
    if vs is None:
        bad.append("缺少 identity_verifier 维度")
    else:
        if not VERIFIER_TESTSET:
            bad.append("标准答案测试集为空")
        if not VERIFIER_REFUSALS:
            bad.append("拒答测试集为空：只测判准不测拒答，会奖励一个什么都敢判的验证器")
    add("验证器必须同时通过判准测试与拒答测试", bad,
        "只会判准、不会拒答的验证器在真实语料上必然制造假阴性")

    # 5) 报告中必须保留历史缺陷记录，不得因重跑而消失
    add("报告必须保留已修复缺陷的记录", [] if RECORDED_FIXES else ["RECORDED_FIXES 为空"],
        "让每日报告都能看到这套流水线曾经错在哪")

    # 6) 审计结论不得被表述为「结论正确」
    banned = ("全部正确", "完全正确", "证明无误", "零误差", "绝对可靠")
    text = json.dumps(res, ensure_ascii=False, default=str)
    hit = [w for w in banned if w in text]
    add("审计产物中不得出现绝对化措辞", hit,
        "诚实红线：审计通过只说明在给定对象集下没发现差异")
    return checks


def write_report(res: dict, checks: list) -> None:
    s = res["summary"]
    L = []
    A = L.append
    A("# S8 独立审计报告\n")
    A(f"- 生成时间：{GEN_AT}")
    A(f"- 生成脚本：`06-AI自动化/01-工作流/openmath_audit.py`")
    A(f"- 计算核心：`06-AI自动化/02-引擎/openmath_sys/src/openmath_sys/audit.py`")
    A(f"- 证据等级：**L2（计算证据）**；`provenance.ai_assisted=true`\n")

    A("## 1. 这次审计在做什么\n")
    A("S1 到 S7 是生产阶段，负责产出结论；S8 是体检阶段，负责回答一个问题：")
    A("**前面那些数字，用另一套算法重算一遍，还是不是同一个数？**\n")
    A(SCOPE_NOTE + "\n")
    A("三条硬约束：\n")
    A("1. 参考值要么来自教科书已知值，要么来自**与被测代码完全不同的算法**")
    A("   （li 用 Ei 幂级数对照 Simpson 积分；p(n) 用五边形数递推对照直接生成；")
    A("   生成树数用 Bareiss 精确消元对照库内基尔霍夫实现）。")
    A("2. 审计**不修改**被审对象，只报差异；修不修由人决定。")
    A("3. 每条失败都必须带可复核的具体数值，不允许只写「不一致」。\n")

    A("## 2. 总览\n")
    A(_tbl([[SECTION_CN.get(sec["name"], sec["name"]), sec["checks"],
             sec["passed"], len(sec["failures"])] for sec in res["sections"]] +
           [["**合计**", f"**{s['total_checks']}**", f"**{s['passed_checks']}**",
             f"**{s['failed_checks']}**"]],
           ["维度", "检查项", "通过", "失败"]))
    A("> 全部通过只说明**在给定对象集与给定独立算法下没有发现差异**，")
    A("> 不说明被审对象的结论正确，也不说明审计本身没有系统性盲区。\n")

    A("## 3. 各维度明细\n")
    for sec in res["sections"]:
        A(f"### {SECTION_CN.get(sec['name'], sec['name'])}\n")
        A(f"- 检查 {sec['checks']} 项，通过 {sec['passed']} 项，失败 {len(sec['failures'])} 项")
        A(f"- 方法：{sec['note']}\n")
        if sec["name"] == "identity_verifier":
            A(f"- 真恒等式判准：{sec.get('true_identities_correct')}")
            A(f"- 假恒等式判准：{sec.get('false_identities_correct')}")
            A(f"- {sec.get('note', '')}\n")
        if sec["name"] == "primes":
            A("- 对照值：" + "，".join(f"π({k})={v}" for k, v in sec["known_values"].items()) + "\n")
        if sec["failures"]:
            A("失败明细：\n")
            A(_tbl([["项", "实测值", "参考值"]] +
                   [[f["item"], f["got"], f["want"]] for f in sec["failures"][:30]],
                   ["项", "实测值", "参考值"]))
        else:
            A("（无失败项）\n")

    A("## 4. 本轮发现并已修复的缺陷\n")
    A("这些是**已经修好**的，列在这里是因为它们说明了这套流水线会在哪里犯错。\n")
    A(_tbl([[f["id"], f["severity"], f["where"], f["symptom"], f["root_cause"], f["fix"]]
            for f in RECORDED_FIXES],
           ["编号", "严重度", "位置", "症状", "根因", "修复"]))

    A("## 5. 审计自身的局限（必须读）\n")
    A("1. **参考值可能是错的**。本轮 F4 就是例子：我一度认为 `li(10)=5.120`，")
    A("   那是 ∫₂¹⁰ dt/ln t 的值，真值 6.1656——**被测代码是对的，参考错了**。")
    A("   所以参考值一律取自独立算法或教科书，不取印象。\n")
    A("2. **两个实现可能错到一起去**。本审计检查的是「两套算法是否一致」，")
    A("   若两者共用同一个错误前提（例如同一个分支约定），一致也不代表对。\n")
    A("3. **对象集很小**。整数只到 120，划分只到 40，图 61 个，群阶数 ≤12。")
    A("   大对象上的行为没有被审计到。\n")
    A("4. **审计不覆盖语义层**。它查的是数算得对不对，不查「这条结论该不该这么下」。")
    A("   例如 S7 里把同调挂到 Hodge 猜想上是**判断**问题，审计管不了。\n")
    A("5. **通过率会随时间失真**。被测代码改了而审计没改，就会出现「全部通过」")
    A("   但其实该测的没测。所以第 3 条自核验专门查维度是否齐全。\n")

    A("## 6. 自核验（审计用在审计自身上）\n")
    A(_tbl([["检查项", "结果", "为什么查这一条"]] +
           [["✅ " + c["check"] if c["passed"] else "❌ " + c["check"],
             "通过" if c["passed"] else "违规：" + "，".join(map(str, c["violations"])),
             c["why"]] for c in checks],
           ["检查项", "结果", "为什么查这一条"]))
    viol = sum(1 for c in checks if not c["passed"])
    A(f"\n合计 {len(checks)} 项，违规 {viol} 项。\n")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main() -> None:
    res = run_audit()
    res["meta"] = {
        "generated_at": GEN_AT,
        "generator": "06-AI自动化/01-工作流/openmath_audit.py",
        "evidence_level": "L2",
        "provenance": PROVENANCE,
    }
    res["recorded_fixes"] = RECORDED_FIXES
    checks = self_audit(res)
    res["self_audit"] = {
        "checks": checks,
        "total_checks": len(checks),
        "violations": sum(1 for c in checks if not c["passed"]),
        "generated_at": GEN_AT,
    }
    _dump(res, "audit_report.json")
    write_report(res, checks)
    s = res["summary"]
    print(f"[S8] 审计 {s['total_checks']} 项，失败 {s['failed_checks']} 项")
    print(f"[S8] 自核验 {len(checks)} 项，违规 {res['self_audit']['violations']} 项")
    print(f"[S8] 报告已写：{REPORT}")


if __name__ == "__main__":
    main()
