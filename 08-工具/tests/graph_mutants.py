"""变异体电池：证明 openmath graph 的每类缺口判据都能被指名打破（不动真语料）。

做法：在系统临时目录里铸一棵最小仓库（00-宪章 + 四条 YAML + 两份 md 账本 + 桥接 + 域依赖.yaml），
基线要求"每类都为 0 且图非空"，然后逐个投放变异，要求**指定的那一类相对基线增长**
（非空不算牙：基线本身就红的类，投不投变异都红）。每个变异只动一处；跑完还原并复算基线。
M9 不动盘——它把图删掉一个节点而表照旧，测渲染器与图之间的行数一致性（XREF-ROWS）。
M10 测端点解析：一条边的终点是一个**存在的文件但不是节点**（配对 md 面孔），
老的四把尺子（BROKEN_DOC_LINK／DANGLING／resolvable／EMPTY-CHART）全都判它正常。
M11 测渲染表：把 ARROW 里的 `contradicts` 撤掉（只改内存不动盘），02 图会静默少画边——
只有 TYPE-UNRENDERED 点名它，同时印出少画的边数（撤表真有影响才算数）。
M12 测单边账：冲突只记在一边（反例记了、公式没记）时 CONTRADICTION_ASYMMETRIC 必须增长。
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
contradicts:
  - OM-X-NT-0001
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

YAML_PAIRED = """schema_version: "0.1"
id: OM-P-NT-0002
kind: problem
title_zh: 样例配对难题
title_en: Sample paired problem
domain: NT
status: OPEN
evidence_level: L1
revision: 1
created: 2026-10-11
updated: 2026-10-11
assumptions: []
related:
  - OM-T-NT-0001
provenance:
  ai_assisted: true
  ai_role: drafting
"""

# 配对面孔：与 .yaml 同名的 md。`_md_ledger` 里它在建节点之前就 continue 了，
# 所以它**在盘上、在 all_md 里，却不是节点**——指向它的链接一切检查都过，
# 只有端点解析这台仪器看得见「这条边在图上无处落脚」。
MD_PAIRED = """---
id: OM-P-NT-0002
title_zh: 样例配对难题
status: OPEN
---

# OM-P-NT-0002 · 样例配对难题（人类面孔）

正文见同名 YAML。
"""

# 反例条目：`contradicts` 通道的载体。它与 OM-F-NT-0001 **互相**记着冲突，
# 所以基线这一类为 0；M12 只拆掉一边，剩下的单边账必须被 CONTRADICTION_ASYMMETRIC 点名。
YAML_X = """schema_version: "0.1"
id: OM-X-NT-0001
kind: counterexample
title_zh: 样例反例
title_en: Sample counterexample
domain: NT
status: PROPOSED
evidence_level: L1
revision: 1
created: 2026-10-11
updated: 2026-10-11
assumptions: []
symbols: []
contradicts:
  - OM-F-NT-0001
provenance:
  ai_assisted: true
  ai_role: drafting
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
    W("02-公式库/OM-X-NT-0001-sample.yaml", YAML_X)
    W("03-难题与猜想/OM-P-NT-0001.md", MD_P)
    W("03-难题与猜想/OM-P-NT-0001-round1.md", MD_ROUND)
    W("03-难题与猜想/OM-P-NT-0002.yaml", YAML_PAIRED)
    W("03-难题与猜想/OM-P-NT-0002.md", MD_PAIRED)
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


def measure_unrendered():
    """M11：只改内存里的渲染表，把 `contradicts` 那一型从 ARROW 撤掉。

    撤掉之后 02 图会**静默少画**若干条边（`chart_record_deps` 用 `type not in ARROW`
    过滤），而盘、图、老四把尺子一切照旧——这正是上一轮把 57 条边抹掉那个缺陷的形状。
    新判据 TYPE-UNRENDERED 必须当场点名，且少画的边数要现印（>=1 才证明这一型真在被丢，
    而不是我的撤表动作根本没影响任何输出）。
    """
    g = G.build(TMP)
    charts, meta = flowdocs.render_charts(g)
    rows = flowdocs.xref_md(g)
    clean = flowdocs.check_invariants(g, charts, meta, [], writes_expected=False, rows=rows)
    if clean:
        return None, 0, ["基线已有不变量故障，M11 无从对照"]
    if "contradicts" not in flowdocs.ARROW:
        return None, 0, ["ARROW 表里没有 contradicts 这一型，M11 测不到东西"]
    key = "02-公式与定理依赖"
    before = meta[key]["edges"]
    saved = flowdocs.ARROW.pop("contradicts")
    try:
        charts2, meta2 = flowdocs.render_charts(g)
        faults = flowdocs.check_invariants(g, charts2, meta2, [], writes_expected=False, rows=rows)
    finally:
        flowdocs.ARROW["contradicts"] = saved
    hit = [f for f in faults if f.startswith("TYPE-UNRENDERED")]
    return hit, before - meta2[key]["edges"], faults


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
    # M10：把轮次文件的链接指向**配对面孔**。文件在盘上（BROKEN_DOC_LINK 不红）、
    # 目标 ID 有载体（DANGLING 不红）、resolvable 也照旧是真——因为这一支的
    # resolvable 量的是「盘上有没有这个文件」。只有端点解析看得见：这条边的终点
    # 不是节点，画进图里就无处落脚。这一格测的是新仪器有没有牙，不是老仪器坏没坏。
    ("M10-OFFGRAPH", "03-难题与猜想/OM-P-NT-0001-round1.md",
     "回到 [主条目](OM-P-NT-0001.md)。",
     "回到 [主条目](OM-P-NT-0001.md)，另见 [面孔](OM-P-NT-0002.md)。",
     "EDGE_ENDPOINT_OFF_GRAPH"),
    # M12：冲突是对称事实，只记在一边＝另一边的读者永远不知道自己被指过矛盾。
    ("M12-ASYM", "02-公式库/OM-F-NT-0001-sample.yaml",
     "contradicts:\n  - OM-X-NT-0001\n", "", "CONTRADICTION_ASYMMETRIC"),
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

    hit11, dropped11, faults11 = measure_unrendered()
    if hit11 is None:
        results.append(("M11-UNRENDERED", "TYPE-UNRENDERED", -1, "ANCHOR-MISS", -1))
        emit("  M11-UNRENDERED : ANCHOR-MISS（%s）" % faults11)
    else:
        verdict = "CAUGHT" if (hit11 and dropped11 >= 1) else "ESCAPED"
        results.append(("M11-UNRENDERED", "TYPE-UNRENDERED", len(hit11), verdict, len(faults11)))
        emit("  %-16s -> %-26s 撤掉 ARROW 的 contradicts ⇒ 02 图少画 %d 条边｜%s" % (
            "M11-UNRENDERED", "TYPE-UNRENDERED", dropped11,
            " | ".join(hit11) if hit11 else "无故障（判据无牙）"))

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
