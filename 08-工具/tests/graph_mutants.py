"""变异体电池：证明 openmath graph 的每类缺口判据都能被指名打破（不动真语料）。

做法：在系统临时目录里铸一棵最小仓库（00-宪章 + 四条 YAML + 两份 md 账本 + 桥接 + 域依赖.yaml），
基线要求"每类都为 0 且图非空"，然后逐个投放变异，要求**指定的那一类相对基线增长**
（非空不算牙：基线本身就红的类，投不投变异都红）。每个变异只动一处；跑完还原并复算基线。
M9 不动盘——它把图删掉一个节点而表照旧，测渲染器与图之间的行数一致性（XREF-ROWS）。
M10 测 no-carrier 型悬边：正文引了一个盘上没有载体的号（OM-P-NT-0003 那批攻坚档案
改号之前就是这个形状）。第 8 批以前这里测的是「终点是配对面孔」，那张面孔如今按
FACE_SUFFIXES 归给记录本身，不再是悬边——所以那一型改由 M14/M15 守着。
M11 测渲染表：把 ARROW 里的 `contradicts` 撤掉（只改内存不动盘），02 图会静默少画边——
M11 测渲染表：把 ARROW 里的 `contradicts` 撤掉（只改内存不动盘），02 图会静默少画边——
只有 TYPE-UNRENDERED 点名它，同时印出少画的边数（撤表真有影响才算数）。
M12 测单边账：冲突只记在一边（反例记了、公式没记）时 CONTRADICTION_ASYMMETRIC 必须增长。
M13 测通道名单：把 EDGE_CHANNELS 里的 `uses` 撤掉（只改内存不动盘），语料声明的 `uses:` 边会
静默丢掉——RELATION_KEY_UNREAD 必须点名这个键，且少建的边数要现印（>=1 才证明撤通道真动了输出）。
这一格是被 42 条 uses 边的现场失血逼出来的：发射器只认它列过的键，schema 里没写、版面里没画的键
不会让任何一台仪器变红。
M14/M15 测第 8 批新加的面孔通道：撤掉 graph.FACE_SUFFIXES（只改内存）悬边必须增多，增多数由两次
build 现减；另一枚什么都不撤，从节点与边的形状独立点数同一批边——两把尺子同读数才算接上了电。
M16/M17 测「撞号只认声明」这一收紧是校准还是遮眼：夹具摆两份纯文件名兜底挂号的档案，收紧面须
ID_COLLISION=0 而 ID_MULTI_FILE 点名它们，放宽面须在同一棵树上多红。
M18 测撞号边：引用指向一个两份 md 共有、却没有记录主人的号，老尺子 resolvable 说它存在（不红），
AMBIGUOUS_REFERENCE 必须点名——这一格是给「判据改挂在 resolve() 的撞号名单上」配的牙。
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
uses:
  - OM-X-NT-0001
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

再看 [配对面孔](OM-P-NT-0002.md)——基线它不落进悬边表，靠的就是面孔通道。
"""

MD_ROUND = """# OM-P-NT-0001 · 样例难题第一轮

回到 [主条目](OM-P-NT-0001.md)。
"""

# 卷宗命名档案：号只能从**文件名**兜底得来（正文不声明 ID），与样例定理 OM-T-NT-0001 同号。
# 它是第 8 批 `ID_CLAIM_SOURCES` 收紧的夹具：基线它进 ID_MULTI_FILE 而不进 ID_COLLISION，
# M16 把兜底加进声明名单它就多红一枚，M17 收紧面则要求它仍为 0 且**被点名**（不是没落地）。
FALLBACK_ID = "OM-T-NT-0001"
FALLBACK_RELS = ["03-难题与猜想/OM-T-NT-0001-round1-note.md",
                 "03-难题与猜想/OM-T-NT-0001-round2-note.md"]
MD_NOTE1 = """# 样例轮次档案（第一轮）

卷宗命名：本档案不声明号段，只引 OM-F-NT-0001。
"""

MD_NOTE2 = """# 样例轮次档案（第二轮）

卷宗命名：本档案不声明号段，只引 OM-F-NT-0001。
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
    W(FALLBACK_RELS[0], MD_NOTE1)
    W(FALLBACK_RELS[1], MD_NOTE2)
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


def measure_unread_channel():
    """M13：只改内存里的通道名单，把 `uses` 那一型从 EDGE_CHANNELS 撤掉。

    撤掉之后语料声明的 `uses:` 边**静默丢掉**（盘、版面、老四把尺子一切照旧）——
    这正是 42 条 uses 边在被丢时的形状，也是上一轮 `generalizations` 缺陷的形状。
    两件事都要当场成立：RELATION_KEY_UNREAD 点名这个键，且边数真的下降（下降数现印，
    >=1 才证明撤通道确实动了输出，而不是我的撤动作碰不到任何东西）。
    """
    g = G.build(TMP)
    if not any(e["type"] == "uses" and e["via"] == "uses" for e in g["edges"]):
        return None, 0, 0, ["夹具里没有 uses 通道建出的边，M13 测不到东西"]
    base_unread = len(g["gaps"].get("RELATION_KEY_UNREAD") or [])
    base_edges = len(g["edges"])
    saved = G.EDGE_CHANNELS
    try:
        G.EDGE_CHANNELS = tuple(x for x in saved if x[0] != "uses")
        g2 = G.build(TMP)
    finally:
        G.EDGE_CHANNELS = saved
    hit = g2["gaps"].get("RELATION_KEY_UNREAD") or []
    return hit, len(hit) - base_unread, base_edges - len(g2["edges"]), hit


def measure_face_channel():
    """M14 与 M15 共用一次测量：撤通道做差 ＋ 独立点数。

    两把尺子读同一批边，但取数路径完全不同：M14 靠「撤掉通道再 build 一次」的差，
    M15 谁都不撤、也不调 resolve()，只按节点与边的形状把「等于某条记录的同干 md 面孔」
    的端点数出来。若只有 M14 会动，M15 就是恒绿摆设；若两数不符，说明有一型被静默吞掉。
    """
    g = G.build(TMP)
    base_refs, _ = G.resolve(g["nodes"], g["edges"])
    base_rows = G.off_graph_edges(g["nodes"], g["edges"])

    def tag(r):
        return (r["src"], r["dst"], r["type"], r["via"])

    base_tags = set([tag(r) for r in base_rows])
    saved = G.FACE_SUFFIXES
    try:
        G.FACE_SUFFIXES = ()
        g2 = G.build(TMP)
        off2 = G.off_graph_edges(g2["nodes"], g2["edges"])
    finally:
        G.FACE_SUFFIXES = saved
    off2_tags = set([tag(r) for r in off2])
    new_rows = [r for r in off2 if tag(r) not in base_tags]
    lost_rows = [r for r in base_rows if tag(r) not in off2_tags]
    new_sides = [c for r in new_rows for c in r["cls"]]

    keys = set([G.node_key(n) for n in g["nodes"]])
    node_ids = set([n["id"] for n in g["nodes"] if isinstance(n["id"], str)])
    faces = set()
    for n in g["nodes"]:
        if n["node_type"] != "record" or not isinstance(n.get("path"), str):
            continue
        stem, ext = os.path.splitext(n["path"].replace("\\", "/"))
        if ext != ".md":
            faces.add(stem + ".md")
    landed = []
    for edge, (a, b) in zip(g["edges"], base_refs):
        for side, ref in ((edge["src"], a), (edge["dst"], b)):
            norm = side.replace("\\", "/")
            if norm in faces and norm not in keys and norm not in node_ids:
                landed.append({"end": norm, "row": tag(edge), "live": ref is not None})
    return {
        "rows_added": len(new_rows),
        "sides_added": len(new_sides),
        "classes": sorted(set(new_sides)),
        "lost": [tag(r) for r in lost_rows],
        "independent": len(landed),
        "dead_at_baseline": sorted(set([x["end"] for x in landed if not x["live"]])),
        "which": sorted(set([x["end"] for x in landed])),
    }


def measure_claim_sources():
    """M16 与 M17 共用一次测量：撞号判据的收紧面与放宽面。

    收紧面（M17）要的是「同一份盘上兜底档案真的存在、却不进 DEFECT 名单」——只印 0 枚
    不点名＝夹具可能压根没落地，那是恒绿不是校准。放宽面（M16）把兜底加进声明名单，
    多红出来的每一行都必须点着兜底档案的 rel，否则收紧遮住了别的东西。
    """
    g = G.build(TMP)
    base_col = list(g["gaps"].get("ID_COLLISION_YAML_VS_MD") or [])
    multi = [x for x in (g["gaps"].get("ID_MULTI_FILE") or []) if x["id"] == FALLBACK_ID]
    named = sorted(set([f for x in multi for f in x["files"] if f in FALLBACK_RELS]))
    saved = G.ID_CLAIM_SOURCES
    try:
        G.ID_CLAIM_SOURCES = tuple(saved) + (G.ID_FALLBACK_SOURCE,)
        g2 = G.build(TMP)
    finally:
        G.ID_CLAIM_SOURCES = saved
    wide_col = list(g2["gaps"].get("ID_COLLISION_YAML_VS_MD") or [])
    key = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
    added = [x for x in wide_col if key(x) not in set([key(y) for y in base_col])]
    return {
        "base": len(base_col),
        "wide": len(wide_col),
        "added": [{"id": x["id"], "md": x["md"], "yaml": x["yaml"],
                   "source_would_be": G.ID_FALLBACK_SOURCE} for x in added],
        "multi_rows": len(multi),
        "named": named,
    }


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
    # M10：正文引一个盘上没有载体的号（no-carrier 型）。配对面孔那一型在第 8 批之后
    # 已经会落进图（那是 FACE_SUFFIXES 的本职，由 M14/M15 守），这里换测剩下的那一型：
    # 分账必须由 off_graph_edges 的 cls 现推成 no-carrier，而不是我替它挑一个名字。
    ("M10-NO-CARRIER", "03-难题与猜想/OM-P-NT-0001-round1.md",
     "回到 [主条目](OM-P-NT-0001.md)。",
     "回到 [主条目](OM-P-NT-0001.md)，另引 OM-P-NT-7777。",
     "EDGE_ENDPOINT_OFF_GRAPH"),
    # M12：冲突是对称事实，只记在一边＝另一边的读者永远不知道自己被指过矛盾。
    ("M12-ASYM", "02-公式库/OM-F-NT-0001-sample.yaml",
     "contradicts:\n  - OM-X-NT-0001\n", "", "CONTRADICTION_ASYMMETRIC"),
    # M18：OM-P-NT-0001 在基线就有两份 md 共有、却没有记录主人（撞号名单里有它，
    # 但没有任何一条边指着它，所以 AMBIGUOUS_REFERENCE 基线为 0）。桥接文档引它一次，
    # 这条边就无处落脚：resolvable 仍为真（node_by_id 里有这个号），DANGLING 不红，
    # BROKEN_DOC_LINK 不红——只有按 resolve() 的撞号名单记账的新判据看得见。
    ("M18-AMBIGUOUS", "04-数学统一场论/04-桥接定理/OM-BR-0001.md",
     "把 OM-F-NT-0001（NT）与 OM-F-AN-0001（AN）接起来。",
     "把 OM-F-NT-0001（NT）与 OM-F-AN-0001（AN）接起来，另引 OM-P-NT-0001。",
     "AMBIGUOUS_REFERENCE"),
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

    hit13, delta13, dropped13, faults13 = measure_unread_channel()
    if not hit13 and delta13 == 0 and dropped13 == 0:
        results.append(("M13-UNREAD-CH", "RELATION_KEY_UNREAD", -1, "ANCHOR-MISS", -1))
        emit("  M13-UNREAD-CH : ANCHOR-MISS（%s）" % (
            " | ".join(faults13) if isinstance(faults13, list) and faults13 and
            not str(faults13[0]).startswith("uses") else "撤通道既没点名也没少边＝判据无牙"))
    else:
        verdict = "CAUGHT" if (delta13 >= 1 and dropped13 >= 1) else "ESCAPED"
        results.append(("M13-UNREAD-CH", "RELATION_KEY_UNREAD", delta13, verdict, dropped13))
        emit("  %-16s -> %-26s 撤掉 EDGE_CHANNELS 的 uses ⇒ 少建 %d 条边｜点名 %d 条：%s" % (
            "M13-UNREAD-CH", "RELATION_KEY_UNREAD", dropped13, delta13,
            " | ".join(hit13) if hit13 else "无（判据没牙）"))

    fc = measure_face_channel()
    v14 = "CAUGHT" if (fc["rows_added"] >= 1 and not fc["lost"]
                       and fc["classes"] == ["unexplained"]) else "ESCAPED"
    results.append(("M14-PAIRED-FACE", "EDGE_ENDPOINT_OFF_GRAPH", fc["rows_added"], v14, 0))
    emit("  %-16s -> %-26s 撤掉 FACE_SUFFIXES ⇒ 悬边 +%d 行／+%d 端（两次 build 现减）｜"
         "新增端型=%s｜撤后反而消失的行=%s" % (
             "M14-PAIRED-FACE", "EDGE_ENDPOINT_OFF_GRAPH", fc["rows_added"], fc["sides_added"],
             ",".join(fc["classes"]) or "NONE", fc["lost"] or "NONE"))
    v15 = "CAUGHT" if (fc["independent"] >= 1 and fc["independent"] == fc["sides_added"]
                       and not fc["dead_at_baseline"]) else "ESCAPED"
    results.append(("M15-FACE-LANDS", "EDGE_ENDPOINT_OFF_GRAPH", fc["independent"], v15, 0))
    emit("  %-16s -> %-26s 不撤不改、按形状独立点数＝%d 端，与 M14 现减的 %d %s｜"
         "基线本就悬着的面孔端点=%s｜点名的端=%s" % (
             "M15-FACE-LANDS", "EDGE_ENDPOINT_OFF_GRAPH", fc["independent"], fc["sides_added"],
             "同值" if fc["independent"] == fc["sides_added"] else "不符（有一型被吞）",
             fc["dead_at_baseline"] or "NONE", fc["which"] or "NONE"))

    cs = measure_claim_sources()
    v16 = "CAUGHT" if (cs["wide"] > cs["base"] and cs["added"]
                       and all(x["md"] in FALLBACK_RELS and x["id"] == FALLBACK_ID
                               for x in cs["added"])) else "ESCAPED"
    results.append(("M16-CLAIM-WIDEN", "ID_COLLISION_YAML_VS_MD", cs["wide"] - cs["base"], v16, 0))
    emit("  %-16s -> %-26s 把兜底算进声明名单 ⇒ %d → %d 枚｜新增行=%s" % (
        "M16-CLAIM-WIDEN", "ID_COLLISION_YAML_VS_MD", cs["base"], cs["wide"],
        " | ".join("%s←%s" % (x["id"], x["md"]) for x in cs["added"]) or "无（判据没牙）"))
    v17 = "CAUGHT" if (cs["base"] == 0 and cs["multi_rows"] >= 1
                       and sorted(cs["named"]) == sorted(FALLBACK_RELS)) else "ESCAPED"
    results.append(("M17-CLAIM-NARROW", "ID_COLLISION_YAML_VS_MD", cs["multi_rows"], v17, 0))
    emit("  %-16s -> %-26s 收紧面：基线撞号 %d 枚，而 %d 行 ID_MULTI_FILE 点名 %s（兜底档案=%d/%d 份）" % (
        "M17-CLAIM-NARROW", "ID_COLLISION_YAML_VS_MD", cs["base"], cs["multi_rows"],
        "点到了" if sorted(cs["named"]) == sorted(FALLBACK_RELS) else "没点到",
        len(cs["named"]), len(FALLBACK_RELS)))

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
