"""变异体电池：证明 openmath graph 的每类缺口判据都能被指名打破（不动真语料）。

做法：在系统临时目录里铸一棵最小仓库（00-宪章 + 四条 YAML + 两份 md 账本 + 桥接 + 域依赖.yaml），
基线要求"每类都为 0 且图非空"，然后逐个投放变异，要求**指定的那一类相对基线增长**
（非空不算牙：基线本身就红的类，投不投变异都红）。每个变异只动一处；跑完还原并复算基线。
M9 不动盘——它把图删掉一个节点而表照旧，测渲染器与图之间的行数一致性（XREF-ROWS）。
运行日志写进仓内版面 `10-文献与索引/知识图谱/_版面/graph_mutants_face.txt`（LF，写后回读比对）。
"""

import json
import os
import shutil
import sys
import tempfile

BS = chr(92)
REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BS.join(["..", ".."])))
TMP = os.path.join(tempfile.gettempdir(), "OMG_FIXTURE")
sys.path.insert(0, REPO_ROOT)

from openmath import flowdocs, graph as G  # noqa: E402

YAML_T = """schema_version: "0.1"
id: OM-T-NT-0001
kind: theorem
title_zh: 样例定理
title_en: Sample theorem
domain: NT
status: VERIFIED(L2)
evidence_level: L2
revision: 1
created: 2026-10-11
updated: 2026-10-11
assumptions: []
tags:
  - 样例标签
symbols:
  - name: "q"
    meaning_zh: "样例符号"
    type: integer
related:
  - OM-F-NT-0001
generalizations:
  - OM-F-NT-0001
verification:
  levels:
    L2:
      passed: true
      script: 05-验证中心/01-引擎/exists.py
provenance:
  ai_assisted: true
  ai_role: verification
"""

YAML_F = """schema_version: "0.1"
id: OM-F-NT-0001
kind: formula
title_zh: 样例公式
title_en: Sample formula
domain: NT
status: VERIFIED(L2)
evidence_level: L2
revision: 1
created: 2026-10-11
updated: 2026-10-11
latex: "a + b = c"
assumptions: []
tags:
  - 样例标签
symbols:
  - name: "a"
    meaning_zh: "样例量"
related:
  - OM-T-NT-0001
verification:
  levels:
    L2:
      passed: true
      script: 05-验证中心/01-引擎/exists.py
provenance:
  ai_assisted: true
  ai_role: verification
"""

YAML_D = """schema_version: "0.1"
id: OM-D-NT-0001
kind: definition
title_zh: 样例量
title_en: Sample quantity
domain: NT
status: CANONICAL
evidence_level: L1
revision: 1
created: 2026-10-11
updated: 2026-10-11
assumptions: []
related:
  - OM-F-NT-0001
symbols:
  - name: "a"
    meaning_zh: "样例量"
provenance:
  ai_assisted: true
  ai_role: drafting
"""

MD_P = """---
id: OM-P-NT-0001
title_zh: 样例难题
status: OPEN
---

# OM-P-NT-0001 · 样例难题

参见 [另一份轮次](OM-P-NT-0001-round1.md) 与 OM-T-NT-0001。
"""

MD_ROUND = """# OM-P-NT-0001 · 样例难题第一轮

回到 [主条目](OM-P-NT-0001.md)。
"""

BRIDGE = """# OM-BR-0001 样例桥接

把 OM-F-NT-0001（NT）与 OM-F-AN-0001（AN）接起来。
"""

YAML_ANALYSIS = """schema_version: "0.1"
id: OM-F-AN-0001
kind: formula
title_zh: 样例分析公式
title_en: Sample analysis formula
domain: AN
status: VERIFIED(L2)
evidence_level: L2
revision: 1
created: 2026-10-11
updated: 2026-10-11
latex: "e^(i pi) + 1 = 0"
assumptions: []
symbols: []
related:
  - OM-F-NT-0001
verification:
  levels:
    L2:
      passed: true
      script: 05-验证中心/01-引擎/exists.py
provenance:
  ai_assisted: true
  ai_role: verification
"""

TIERS = """schema_version: "0.1"
source: "fixture"
unplaced_domains:
  - code: NT
  - code: AN
tiers:
  - rank: 1
    domains: [FD]
    label: "基础"
intra_tier_edges:
  - ["FD", "FD", "自环占位"]
"""


def W(rel, text):
    path = os.path.join(TMP, rel)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))


def make_tree():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    for d in ("00-宪章", "02-公式库", "03-难题与猜想", "01-数学体系",
              "04-数学统一场论/04-桥接定理", "05-验证中心/01-引擎"):
        os.makedirs(os.path.join(TMP, d))
    W("02-公式库/OM-T-NT-0001-sample.yaml", YAML_T)
    W("02-公式库/OM-F-NT-0001-sample.yaml", YAML_F)
    W("02-公式库/OM-D-NT-0001-sample.yaml", YAML_D)
    W("02-公式库/OM-F-AN-0001-sample.yaml", YAML_ANALYSIS)
    W("03-难题与猜想/OM-P-NT-0001.md", MD_P)
    W("03-难题与猜想/OM-P-NT-0001-round1.md", MD_ROUND)
    W("04-数学统一场论/04-桥接定理/OM-BR-0001.md", BRIDGE)
    W("01-数学体系/域依赖.yaml", TIERS)
    W("05-验证中心/01-引擎/exists.py", "# fixture engine\n")


def measure():
    g = G.build(TMP)
    charts, meta = flowdocs.render_charts(g)
    rows = flowdocs.xref_md(g)
    faults = flowdocs.check_invariants(g, charts, meta, [], writes_expected=False, rows=rows)
    counts = {}
    for name, value in g["gaps"].items():
        counts[name] = len(value) if hasattr(value, "__len__") else 0
    return counts, faults, g, meta


def measure_dropped_node():
    """M9：图比表多一个节点（语料在渲染后又长了一条 / 渲染器漏掉一类节点）。

    判据 XREF-ROWS 的期望行数由 graph 现推，所以「表少一行」必须红；这一格不需要动盘，
    它测的是渲染器与图之间的一致性，而不是盘上的数据。
    """
    g = G.build(TMP)
    charts, meta = flowdocs.render_charts(g)
    rows = flowdocs.xref_md(g)
    clean = flowdocs.check_invariants(g, charts, meta, [], writes_expected=False, rows=rows)
    if clean:
        return None, "基线已有不变量故障，M9 无从对照"
    doctored = json.loads(json.dumps(g))
    doctored["nodes"] = doctored["nodes"][:-1]
    faults = flowdocs.check_invariants(doctored, charts, meta, [], writes_expected=False, rows=rows)
    hit = [f for f in faults if f.startswith("XREF-ROWS")]
    return hit, faults


def mutate(rel, old, new):
    path = os.path.join(TMP, rel)
    with open(path, "rb") as fh:
        data = fh.read().decode("utf-8")
    n = data.count(old)
    if n != 1:
        raise AssertionError("变异锚点在 %s 里出现 %d 次（必须 1 次）" % (rel, n))
    with open(path, "wb") as fh:
        fh.write(data.replace(old, new).encode("utf-8"))


MUTANTS = [
    ("M1-DANGLING", "02-公式库/OM-T-NT-0001-sample.yaml",
     "  - OM-F-NT-0001\ngeneralizations", "  - OM-X-NT-9999\ngeneralizations", "DANGLING"),
    ("M2-INVERSION", "02-公式库/OM-T-NT-0001-sample.yaml",
     "evidence_level: L2", "evidence_level: L4", "EVIDENCE_INVERSION"),
    ("M3-UNPLACED", "01-数学体系/域依赖.yaml", "    domains: [FD]", "    domains: [ZZ]",
     "DOMAIN_UNPLACED"),
    ("M4-BROKENLINK", "03-难题与猜想/OM-P-NT-0001.md",
     "](OM-P-NT-0001-round1.md)", "](OM-P-NT-0001-nope.md)", "BROKEN_DOC_LINK"),
    ("M5-TERM", "02-公式库/OM-F-NT-0001-sample.yaml",
     "  - 样例标签", "  - 样例 标 签", "TERM_INCONSISTENCY"),
    ("M6-ORPHAN", "02-公式库/OM-D-NT-0001-sample.yaml",
     "related:\n  - OM-F-NT-0001\n", "", "ORPHAN"),
    ("M7-COLLISION", "03-难题与猜想/OM-P-NT-0001-round1.md",
     "回到 [主条目](OM-P-NT-0001.md)。",
     "| **ID** | OM-T-NT-0001 |\n\n回到 [主条目](OM-P-NT-0001.md)。",
     "ID_COLLISION_YAML_VS_MD"),
    ("M8-UNDEF-SYMBOL", "02-公式库/OM-F-NT-0001-sample.yaml",
     '  - name: "a"', '  - name: "zzz"', "UNDEFINED_SYMBOL"),
]

LOG = []


def emit(line):
    LOG.append(line)
    print(line)


def main():
    emit("graph mutant battery over fixture tree %s" % TMP)
    make_tree()
    base_counts, base_faults, base_g, base_meta = measure()
    emit("== baseline ==")
    for name in sorted(base_counts):
        emit("  %-30s : %d" % (name, base_counts[name]))
    emit("  faults : %s" % (", ".join(base_faults) or "NONE"))
    emit("  bridge_edges : %d  cites : %d" % (
        base_meta["04-桥接与旁证"]["bridge_edges"],
        sum(1 for e in base_g["edges"] if e["type"] == "cites")))
    base_ok = (not base_faults and base_counts.get("DANGLING", 0) == 0
               and base_counts.get("EVIDENCE_INVERSION", 0) == 0
               and base_counts.get("BROKEN_DOC_LINK", 0) == 0
               and base_meta["04-桥接与旁证"]["bridge_edges"] >= 1)
    emit("  ==> baseline clean with teeth: %s" % base_ok)
    if not base_ok:
        emit("==> ABORT：基线不干净，变异判据无效")
        return 3

    results = []
    for name, rel, old, new, target in MUTANTS:
        path = os.path.join(TMP, rel)
        with open(path, "rb") as fh:
            before = fh.read()
        anchor_miss = None
        try:
            mutate(rel, old, new)
            counts, faults, _g, _meta = measure()
            hit = counts.get(target, 0)
            base = base_counts.get(target, 0)
            # 判据是「增量」而不是「非空」：基线本身就非空的类（域未归层／孤立点／
            # 符号未定义／md 账本）投不投变异都红，非空当牙等于恒绿。
            verdict = "CAUGHT" if hit > base else "ESCAPED"
            results.append((name, target, hit - base, verdict, len(faults)))
        except AssertionError as exc:
            anchor_miss = str(exc)
            results.append((name, target, -1, "ANCHOR-MISS", -1))
        finally:
            with open(path, "wb") as fh:
                fh.write(before)
        if anchor_miss is not None:
            emit("  %s : ANCHOR-MISS（%s）判据从未被投进去，这一格不算数" % (name, anchor_miss))
            continue
        after_counts, after_faults, _g, _meta = measure()
        restored = after_counts == base_counts and after_faults == base_faults
        emit("  %-16s -> %-26s base=%-3d after=%-3d delta=%-3d %-9s 还原=%s faults=%d" % (
            name, target, base, hit, hit - base, results[-1][3], restored, len(after_faults)))
        if not restored:
            emit("  ==> 还原后与基线不同判：%s" % (
                json.dumps({k: v for k, v in after_counts.items() if base_counts.get(k) != v},
                           ensure_ascii=False)))
            return 4

    hit, all_faults = measure_dropped_node()
    if hit is None:
        results.append(("M9-XREF-ROWS", "XREF-ROWS", -1, "ANCHOR-MISS", -1))
        emit("  M9-XREF-ROWS : ANCHOR-MISS（基线不干净：%s）" % all_faults)
    else:
        verdict = "CAUGHT" if hit else "ESCAPED"
        results.append(("M9-XREF-ROWS", "XREF-ROWS", len(hit), verdict, len(all_faults)))
        emit("  %-16s -> %-26s 图里删 1 个节点而表照旧 ⇒ %s" % (
            "M9-XREF-ROWS", "XREF-ROWS", " | ".join(hit) if hit else "无故障（判据无牙）"))

    escaped = [r for r in results if r[3] != "CAUGHT"]
    emit("== verdict ==")
    emit("  mutants=%d caught=%d not_caught=%d" % (
        len(results), len(results) - len(escaped), len(escaped)))
    for name, target, delta, verdict, _f in escaped:
        emit("  %s %s（%s：基线 %s 类，投变异后增量=%d）" % (
            verdict, name, target, base_counts.get(target, 0), delta))
    return 0 if not escaped else 1


if __name__ == "__main__":
    rc = main()
    face_rel = "10-文献与索引/知识图谱/_版面/graph_mutants_face.txt"
    payload = ("\n".join(LOG) + "\n").encode("utf-8")
    with open(os.path.join(REPO_ROOT, face_rel), "wb") as fh:
        fh.write(payload)
    back = open(os.path.join(REPO_ROOT, face_rel), "rb").read()
    assert back == payload, "版面回读不符"
    assert back.count(b"\r") == 0 and back.count(bytes([0])) == 0, "版面含 CR/NUL"
    print("版面行数=%d 载体=%s（%d B, CR=0, NUL=0）rc=%d" % (
        len(LOG), face_rel, len(back), rc))
    sys.exit(rc)
