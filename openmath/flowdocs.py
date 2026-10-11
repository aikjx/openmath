"""由 graph 渲染关系流程图与交叉引用索引（产物全是生成物）。

设计约束（让"图画得对不对"可被机器判）：
1. 每张图的节点必须来自 graph 的节点集、边必须来自 graph 的边集；渲染器不许自己
   添边，跨层折叠必须把"折叠了几条"印在边上。
2. 空图不许当成功：图上没有节点行 ⇒ EMPTY-CHART 缺陷。
3. 输出必须可重跑复现（不许用 hash() 之类进程内随机量）。
4. 所有读数只落在 _版面/graph_face.txt，文档引用那张面。
"""

import json
import os

from . import graph as graph_mod
from . import ids

KIND_LAYER = {
    "definition": "逻辑层",
    "formula": "方程层",
    "theorem": "方程层",
    "algorithm": "方程层",
    "counterexample": "方程层",
    "conjecture": "难题层",
    "problem": "难题层",
    "programme": "难题层",
    "doc-ledger": "难题层",
}
LAYERS = ("体系层", "逻辑层", "方程层", "难题层")
LEVELS = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")
TAG_OF = {"体系层": "SYS", "逻辑层": "L1", "方程层": "L2", "难题层": "L3"}
ARROW = {
    "related": ("-->", None),
    "specializes": ("-->", "特例"),
    "generalizes": ("-->", "推广"),
    "implies": ("==>", "蕴含"),
    "uses": ("-->", "用到"),
    "bridges": ("==>", "桥接"),
    "cites": ("-->", "引用"),
    "evidenced_by": ("-->", "旁证"),
    "contradicts": ("-.->", "冲突"),
}


def _clean(text, limit=56):
    out = str(text).replace('"', "'").replace("|", "/")
    out = " ".join(out.split())
    if len(out) > limit:
        out = out[: limit - 1] + "…"
    return out or "?"


def _label(node):
    ident = node["id"] or os.path.basename(node["path"])
    bits = [ident, _clean(node["title_zh"] or node["kind"] or "", 34)]
    if node["node_type"] == "record":
        bits.append("%s/%s/%s" % (node["kind"], node["evidence_level"] or "?", node["status"] or "?"))
    else:
        bits.append("doc/%s" % (node["status"] or "?"))
    return " ".join(bits)


class _Alias(object):
    def __init__(self):
        self.map = {}

    def of(self, key):
        if key not in self.map:
            self.map[key] = "n%d" % (len(self.map) + 1)
        return self.map[key]


def _index(g):
    out = {}
    for node in g["nodes"]:
        out[graph_mod.node_key(node)] = node
    return out


def _edge_line(alias, by_key, edge, extra_label=None):
    src_key = edge["src"]
    dst_key = edge["dst"]
    arrow, label = ARROW.get(edge["type"], ("-->", None))
    label = extra_label or label or edge["type"]
    s = alias.of(src_key)
    d = alias.of(dst_key)
    return "  %s %s|%s| %s" % (s, arrow, _clean(label, 22), d)


def _emit_end(lines, alias, by_key, key, raw):
    """边的一个端点画成什么。落不进节点集也要画。

    把盲端从图上抹掉不等于盲区不存在，只是让它没法被看见——上一版就是这么把
    04 图抹成空图的，被 EMPTY-CHART 判据拦下。所以这里给盲端一个显式标签。
    """
    if key is None:
        akey = "offgraph:" + raw
        if akey in alias.map:
            return alias.map[akey]
        name = alias.of(akey)
        lines.append('  %s["（无节点载体）%s"]' % (name, _clean(os.path.basename(raw), 40)))
        return name
    if key in alias.map:
        return alias.map[key]
    node = by_key.get(key)
    label = _clean(_label(node)) if node else _clean(os.path.basename(key), 40)
    name = alias.of(key)
    lines.append('  %s["%s"]' % (name, label))
    return name


def _arrow_line(edge, a_name, b_name):
    arrow, label = ARROW.get(edge["type"], ("-->", None))
    return "  %s %s|%s| %s" % (a_name, arrow, _clean(label or edge["type"], 22), b_name)


def chart_overview(g):
    by_key = _index(g)
    alias = _Alias()
    lines = ["flowchart TB"]
    domain_nodes = {}
    for node in g["nodes"]:
        if node["domain"]:
            domain_nodes.setdefault(node["domain"], []).append(node)
    lines.append("  subgraph SYS[体系层：%d 个域有登记条目（共 %d 域）]" % (
        len(domain_nodes), len(ids.DOMAINS)))
    for code in sorted(domain_nodes):
        lines.append('    D_%s["%s %s：%d 条"]' % (
            code, code, _clean(ids.DOMAINS.get(code, code)), len(domain_nodes[code])))
    lines.append("  end")
    counts = {layer: [] for layer in LAYERS[1:]}
    for node in g["nodes"]:
        counts.setdefault(KIND_LAYER.get(node["kind"], "难题层"), []).append(node)
    for layer in LAYERS[1:]:
        tag = TAG_OF[layer]
        nodes = counts[layer]
        lines.append("  subgraph %s[%s：%d 个节点]" % (tag, layer, len(nodes)))
        for node in sorted(nodes, key=lambda n: graph_mod.node_key(n)):
            key = graph_mod.node_key(node)
            lines.append('    %s["%s"]' % (alias.of(key), _clean(_label(node))))
        lines.append("  end")
    folded = {}
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    dropped = 0
    for edge, (a, b) in zip(g["edges"], refs):
        src = by_key.get(a)
        dst = by_key.get(b)
        if not src or not dst:
            dropped += 1
            continue
        a = KIND_LAYER.get(src["kind"], "难题层")
        b = KIND_LAYER.get(dst["kind"], "难题层")
        if a == b:
            continue
        folded.setdefault((a, b), set()).add((edge["src"], edge["dst"], edge["type"]))
    for (a, b), triples in sorted(folded.items()):
        lines.append('  %s -.->|"折叠 %d 条真实边"| %s' % (TAG_OF[a], len(triples), TAG_OF[b]))
    meta = {"layer_nodes": {k: len(v) for k, v in counts.items()},
            "domains_with_nodes": len(domain_nodes),
            "layer_edges": len(folded),
            "real_edges_between_layers": sum(len(v) for v in folded.values()),
            "edges_off_graph": dropped}
    return "\n".join(lines) + "\n", meta


def chart_domain_tiers(g):
    tiers = g["tiers"]["ranks"]
    by_domain = {}
    for node in g["nodes"]:
        if node["domain"]:
            by_domain[node["domain"]] = by_domain.get(node["domain"], 0) + 1
    lines = ["flowchart TB"]
    prev = None
    for tier in sorted(tiers, key=lambda t: t["rank"]):
        tag = "R%d" % tier["rank"]
        lines.append("  subgraph %s[第 %d 层：%s]" % (tag, tier["rank"], _clean(tier.get("label") or "未命名")))
        for code in tier["domains"]:
            lines.append('    T%d_%s["%s %s：%d 条"]' % (
                tier["rank"], code, code, _clean(ids.DOMAINS.get(code, code)), by_domain.get(code, 0)))
        lines.append("  end")
        if prev:
            lines.append('  %s -->|"借用工具（非逻辑基础）"| %s' % (prev, tag))
        prev = tag
    for a, b in sorted(g["tiers"]["intra"]):
        rank_a = next((t["rank"] for t in tiers if a in t["domains"]), None)
        rank_b = next((t["rank"] for t in tiers if b in t["domains"]), None)
        if rank_a and rank_b:
            lines.append('  R%d_%s -.->|同层互译| R%d_%s' % (rank_a, a, rank_b, b))
    for code in sorted(g["tiers"]["unplaced"]):
        lines.append('  U_%s["%s %s：声明为未归层"]' % (code, code, _clean(ids.DOMAINS.get(code, code))))
    for code in sorted(g["tiers"]["missing_placement"]):
        lines.append('  M_%s["%s %s：既未归层也未声明未归层（DEFECT）"]' % (
            code, code, _clean(ids.DOMAINS.get(code, code))))
    meta = {"tiers": len(tiers),
            "tier_edges": max(0, len(tiers) - 1),
            "intra_edges": len(g["tiers"]["intra"]),
            "unplaced": len(g["tiers"]["unplaced"]),
            "missing_placement": len(g["tiers"]["missing_placement"])}
    return "\n".join(lines) + "\n", meta


def chart_record_deps(g):
    by_key = _index(g)
    alias = _Alias()
    lines = ["flowchart LR"]
    rec_keys = set([graph_mod.node_key(n) for n in g["nodes"] if n["node_type"] == "record"])
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    emitted = 0
    for edge, (a, b) in zip(g["edges"], refs):
        if a not in rec_keys or b not in rec_keys:
            continue
        if edge["type"] not in ARROW:
            continue
        for key in (edge["src"], edge["dst"]):
            node = by_key[key]
            if key not in alias.map:
                lines.append('  %s["%s"]' % (alias.of(key), _clean(_label(node))))
        lines.append(_edge_line(alias, by_key, edge))
        emitted += 1
    meta = {"record_nodes_in_chart": len(alias.map), "edges": emitted}
    return "\n".join(lines) + "\n", meta


def chart_problem_bottleneck(g):
    by_key = _index(g)
    alias = _Alias()
    lines = ["flowchart TB"]
    problem_kinds = ("problem", "conjecture", "programme", "doc-ledger")
    prob_keys = set()
    for node in g["nodes"]:
        if node["kind"] in problem_kinds:
            key = graph_mod.node_key(node)
            prob_keys.add(key)
            lines.append('  %s["%s"]' % (alias.of(key), _clean(_label(node))))
    prose = {}
    for row in g["gaps"]["PROSE_RELATION_UNTRAVERSABLE"]:
        prose.setdefault(row["src"], set()).add(row["field"])
    for src in sorted(prose):
        if src in prob_keys:
            owner = alias.of(src)
            gap = alias.of("prose:" + src)
            lines.append('  %s["卡点：%s 的关系只写在 %s 里，无法遍历"]' % (
                gap, src, "+".join(sorted(prose[src]))))
            lines.append('  %s -.->|不可遍历| %s' % (owner, gap))
    dangling = sorted(set(g["gaps"]["DANGLING"]))
    for target in dangling:
        gap = alias.of("dangling:" + target)
        lines.append('  %s["悬空引用：%s（被引用但无载体）"]' % (gap, target))
        if target in by_key:
            lines.append('  %s -.->|撞名| %s' % (alias.of(target), gap))
    emitted = 0
    off_graph = 0
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    for edge, (a, b) in zip(g["edges"], refs):
        if edge["type"] not in ("cites", "implies", "uses", "bridges", "evidenced_by"):
            continue
        if a not in prob_keys and b not in prob_keys:
            continue
        if a is None or b is None:
            off_graph += 1
        a_name = _emit_end(lines, alias, by_key, a, edge["src"])
        b_name = _emit_end(lines, alias, by_key, b, edge["dst"])
        lines.append(_arrow_line(edge, a_name, b_name))
        emitted += 1
    meta = {"problem_nodes": len(prob_keys), "chart_nodes": len(alias.map),
            "edges": emitted, "prose_bottlenecks": len(prose), "dangling": len(dangling),
            "edges_with_off_graph_end": off_graph}
    return "\n".join(lines) + "\n", meta


def chart_bridges(g):
    by_key = _index(g)
    alias = _Alias()
    lines = ["flowchart LR"]
    bridges = sorted([e for e in g["edges"] if e["type"] == "bridges"], key=lambda e: (e["via"], e["src"], e["dst"]))
    docs = sorted({e["via"] for e in bridges})
    for doc in docs:
        lines.append('  %s["桥接文档：%s"]' % (alias.of("doc:" + doc), _clean(os.path.basename(doc), 40)))
    evid = sorted([e for e in g["edges"] if e["type"] == "evidenced_by"],
                 key=lambda e: (e["src"], e["dst"]))
    pairs = bridges + evid
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    index_of = dict((id(e), i) for i, e in enumerate(g["edges"]))
    off_graph = 0
    for edge in pairs:
        a, b = refs[index_of[id(edge)]]
        if a is None or b is None:
            off_graph += 1
        a_name = _emit_end(lines, alias, by_key, a, edge["src"])
        b_name = _emit_end(lines, alias, by_key, b, edge["dst"])
        lines.append(_arrow_line(edge, a_name, b_name))
        if edge in bridges:
            lines.append('  %s -.->|出处| %s' % (alias.of("doc:" + edge["via"]), a_name))
    meta = {"bridge_docs": len(docs), "bridge_edges": len(bridges),
            "evidence_edges": len(evid), "nodes": len(alias.map),
            "edges_with_off_graph_end": off_graph}
    return "\n".join(lines) + "\n", meta


def render_charts(g):
    charts = {}
    meta = {}
    charts["00-四层总览.mmd"], meta["00-四层总览"] = chart_overview(g)
    charts["01-域依赖.mmd"], meta["01-域依赖"] = chart_domain_tiers(g)
    charts["02-公式与定理依赖.mmd"], meta["02-公式与定理依赖"] = chart_record_deps(g)
    charts["03-难题卡点.mmd"], meta["03-难题卡点"] = chart_problem_bottleneck(g)
    charts["04-桥接与旁证.mmd"], meta["04-桥接与旁证"] = chart_bridges(g)
    return charts, meta


def _degrees(g):
    outdeg = {}
    indeg = {}
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    for edge, (a, b) in zip(g["edges"], refs):
        if a:
            outdeg[a] = outdeg.get(a, 0) + 1
        if b:
            indeg[b] = indeg.get(b, 0) + 1
    return outdeg, indeg


def xref_md(g):
    rows = {}
    outdeg, indeg = _degrees(g)

    lines = ["# 交叉引用索引：按 ID", "", "> 生成物（`python -m openmath graph`），勿手改。", "",
             "| ID | 载体 | 类型 | 状态 | 等级 | 出边 | 入边 | 机器可读 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for node in g["nodes"]:
        key = graph_mod.node_key(node)
        lines.append("| %s | `%s` | %s | %s | %s | %d | %d | %s |" % (
            node["id"] or "—", node["path"], node["kind"] or "?", node["status"] or "?",
            node["evidence_level"] or "?", outdeg.get(key, 0), indeg.get(key, 0),
            "是" if node["machine_readable"] else "否（md 账本）"))
    rows["按ID.md"] = "\n".join(lines) + "\n"

    # 按域：空域必须占一行。「这个域没有任何条目」是结论，不是排版留白；只印有节点的
    # 域会把 18/20 的空白藏成一张看着挺满的地图。
    tier_of = {}
    for rank_item in g["tiers"]["ranks"]:
        for code in rank_item["domains"]:
            tier_of[code] = rank_item["rank"]
    by_domain = {}
    for node in g["nodes"]:
        if node["domain"]:
            by_domain.setdefault(node["domain"], []).append(node)
    domain_counts = dict((code, len(bucket)) for code, bucket in by_domain.items())
    lines = ["# 交叉引用索引：按域", "",
             "> 生成物，勿手改。域清单 = `openmath/ids.py` 的 `DOMAINS`；分层来自 `01-数学体系/域依赖.yaml`；"
             "未归层与缺层由缺口类 `DOMAIN_UNPLACED` 裁决。", "",
             "| 域 | 名称 | 层 | 枚数 | 记录 | 账本 | 条目（截断到 8） |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    printed = 0
    for code, name in sorted(ids.DOMAINS.items()):
        bucket = sorted(by_domain.get(code, []), key=lambda n: (str(n["id"] or "~"), n["path"]))
        printed += len(bucket)
        lines.append("| %s | %s | %s | %d | %d | %d | %s |" % (
            code, name, tier_of.get(code, "未归层"), len(bucket),
            sum(1 for n in bucket if n["node_type"] == "record"),
            sum(1 for n in bucket if n["node_type"] != "record"),
            ", ".join("`%s`" % _clean(str(n["id"] or n["path"]), 40) for n in bucket[:8])
            + ("…" if len(bucket) > 8 else "")))
    for code in sorted(set(by_domain) - set(ids.DOMAINS)):
        bucket = by_domain[code]
        printed += len(bucket)
        lines.append("| %s | 不在 `ids.DOMAINS` 里 | — | %d | %d | %d | 见 `按ID.md` |" % (
            code, len(bucket), sum(1 for n in bucket if n["node_type"] == "record"),
            sum(1 for n in bucket if n["node_type"] != "record")))
    # 自证闭合：枚数合计必须等于「有域标签的节点数」，且差额（域解析不出的节点）当场印出来
    # ——只列有节点的域会把丢掉的那些藏成一张看着挺全的地图。
    lines.append("")
    lines.append("合计 %d 枚；节点总数 %d，其中无域标签 %d（这些节点在别的表里，不在本表）；"
                 "空域 %d / %d；有内容域 %d 个。行数与图是否相符由 `check_invariants` 的 "
                 "XREF-ROWS 现推现比，本行只是这张表的算术。" % (
                     printed, len(g["nodes"]), len(g["nodes"]) - printed,
                     sum(1 for code in ids.DOMAINS if not domain_counts.get(code)),
                     len(ids.DOMAINS), sum(1 for c in domain_counts.values() if c)))
    rows["按域.md"] = "\n".join(lines) + "\n"

    # 按标签：与术语索引分开——术语索引按「术语」查，这张按「标签」查同一批节点的
    # 归属，两者口径不同（标签可重复、术语要归一）。
    by_tag = {}
    for node in g["nodes"]:
        for tag in node["tags"]:
            by_tag.setdefault(str(tag), set()).add(node["id"] or node["path"])
    lines = ["# 交叉引用索引：按标签", "", "> 生成物，勿手改。标签直取自记录的 `tags` 字段。", "",
             "| 标签 | 枚数 | 条目 |", "| --- | --- | --- |"]
    for tag in sorted(by_tag):
        keys = sorted(by_tag[tag])
        lines.append("| %s | %d | %s |" % (_clean(tag, 40), len(keys),
                                           ", ".join("`%s`" % k for k in keys[:12])
                                           + ("…" if len(keys) > 12 else "")))
    if not by_tag:
        lines.append("| （无任何标签） | 0 | — |")
    rows["按标签.md"] = "\n".join(lines) + "\n"

    # 按证据等级：L0–L6 全档都要占行，空档就是「这一级没有条目」的实测结论。
    by_level = {}
    for node in g["nodes"]:
        by_level.setdefault(node["evidence_level"] or "未标", []).append(node)
    lines = ["# 交叉引用索引：按证据等级", "",
             "> 生成物，勿手改。等级取自 `evidence_level`；md 账本没有该字段，落「未标」。"
             "「未标」非空 = 缺口类 `MD_ONLY_LEDGER` 的来源之一。", "",
             "| 等级 | 枚数 | 记录 | 账本 | 声称已验证而上证不足 |",
             "| --- | --- | --- | --- | --- |"]
    inverted_ids = {item["id"] for item in g["gaps"]["EVIDENCE_INVERSION"]}
    for level in list(LEVELS) + ["未标"]:
        bucket = sorted(by_level.pop(level, []), key=lambda n: (str(n["id"] or "~"), n["path"]))
        lines.append("| %s | %d | %d | %d | %s |" % (
            level, len(bucket), sum(1 for n in bucket if n["node_type"] == "record"),
            sum(1 for n in bucket if n["node_type"] != "record"),
            ", ".join("`%s`" % n["id"] for n in bucket if n["id"] in inverted_ids) or "—"))
    for level, bucket in sorted(by_level.items()):
        lines.append("| %s（不在 L0–L6） | %d | %d | %d | — |" % (
            level, len(bucket), sum(1 for n in bucket if n["node_type"] == "record"),
            sum(1 for n in bucket if n["node_type"] != "record")))
    rows["按证据等级.md"] = "\n".join(lines) + "\n"

    lines = ["# 交叉引用索引：术语", "", "> 生成物，勿手改。术语 = 标签（tags）＋符号表（symbols）。", "",
             "| 术语 | 种类 | 出现条目 |", "| --- | --- | --- |"]
    terms = {}
    for node in g["nodes"]:
        key = graph_mod.node_key(node)
        for tag in node["tags"]:
            terms.setdefault((str(tag), "标签"), set()).add(key)
        for sym in node["symbols"]:
            terms.setdefault((sym, "符号"), set()).add(key)
    for (term, kind), keys in sorted(terms.items()):
        lines.append("| %s | %s | %s |" % (term, kind, ", ".join("`%s`" % k for k in sorted(keys))))
    rows["术语索引.md"] = "\n".join(lines) + "\n"

    lines = ["# 交叉引用索引：引用图", "", "> 生成物，勿手改。「可遍历＝否」即缺口类 PROSE/悬空的来源。", "",
             "| 源 | 类型 | 目标 | 依据字段 | 可遍历 | 落到节点 |",
             "| --- | --- | --- | --- | --- | --- |"]
    refs, _ = graph_mod.resolve(g["nodes"], g["edges"])
    for edge, (a, b) in zip(g["edges"], refs):
        lands = ", ".join([("`%s`" % k) if k else "（无节点载体）" for k in (a, b)])
        lines.append("| `%s` | %s | `%s` | %s | %s | %s |" % (
            edge["src"], edge["type"], edge["dst"], edge["via"],
            "是" if edge["resolvable"] else "否", _clean(lands, 90)))
    rows["引用图.md"] = "\n".join(lines) + "\n"

    counts = graph_mod.defect_counts(g)
    lines = ["# 缺口检测", "", "> 生成物，勿手改。判据清单见 `10-文献与索引/README.md` §七。", "",
             "| 缺口类 | 严重度 | 枚数 |", "| --- | --- | --- |"]
    for name, (severity, count) in sorted(counts.items(), key=lambda kv: (-kv[1][1], kv[0])):
        lines.append("| `%s` | %s | %d |" % (name, severity, count))
    lines.append("")
    for name, value in sorted(g["gaps"].items()):
        n = len(value) if hasattr(value, "__len__") else 0
        lines.append("## `%s`（%d 枚，%s）" % (name, n, graph_mod.SEVERITY.get(name, "ADVISORY")))
        if isinstance(value, dict):
            for key, raw in sorted(value.items()):
                lines.append("- `%s` ← %s" % (key, ", ".join("`%s`" % r for r in raw)))
        elif isinstance(value, list):
            for item in value:
                lines.append("- " + (json.dumps(item, ensure_ascii=False, sort_keys=True)
                                     if isinstance(item, dict) else str(item)))
        if not value:
            lines.append("- （无）")
        lines.append("")
    rows["缺口检测.md"] = "\n".join(lines) + "\n"
    return rows


def face(g, meta, rows=None):
    lines = []
    emit = lines.append
    emit("openmath graph face — 本面是唯一载体，文档只许引用这里印出的数")
    emit("generated: %s" % g["generated"])
    emit("---- ledger scope ----")
    emit("record nodes (OM-*.yaml)            : %d" % g["counts"]["record_nodes"])
    emit("doc nodes (OM-*.md 无 .yaml 伴生)    : %d" % g["counts"]["doc_nodes"])
    emit("evidence docs (05-验证中心)          : %d" % g["counts"]["evidence_docs"])
    emit("typed edges                        : %d" % g["counts"]["edges"])
    emit("YAML load errors                   : %d" % g["counts"]["load_errors"])
    emit("---- edge type census ----")
    census = {}
    for edge in g["edges"]:
        census[edge["type"]] = census.get(edge["type"], 0) + 1
    for name, value in sorted(census.items(), key=lambda kv: (-kv[1], kv[0])):
        emit("  %-14s : %d" % (name, value))
    emit("---- gap classes ----")
    for name, (severity, count) in sorted(graph_mod.defect_counts(g).items(),
                                          key=lambda kv: (-kv[1][1], kv[0])):
        emit("  %-30s : %4d : %s" % (name, count, severity))
    emit("---- charts ----")
    for name in sorted(meta):
        emit("  %s : %s" % (name, json.dumps(meta[name], ensure_ascii=False, sort_keys=True)))
    emit("---- domain placement ----")
    placed = sorted({d for t in g["tiers"]["ranks"] for d in t["domains"]})
    emit("  tiers declared          : %d" % len(g["tiers"]["ranks"]))
    emit("  domains placed          : %d / %d（ids.DOMAINS）" % (len(placed), len(ids.DOMAINS)))
    emit("  declared unplaced       : %s" % (", ".join(sorted(g["tiers"]["unplaced"])) or "NONE"))
    emit("  missing_placement       : %s" % (", ".join(sorted(g["tiers"]["missing_placement"])) or "NONE"))
    emit("  domains with >=1 node   : %d / %d" % (
        len({n["domain"] for n in g["nodes"] if n["domain"]}), len(ids.DOMAINS)))
    if rows is not None:
        emit("---- artifacts ----")
        emit("  graph.json            : nodes %d / edges %d" % (len(g["nodes"]), len(g["edges"])))
        emit("  流程图               : %d 张（%s）" % (len(meta), ", ".join(sorted(meta))))
        emit("  交叉引用索引         : %d 张（%s）" % (len(rows), ", ".join(sorted(rows))))
    res = g.get("resolution") or {}
    if res:
        emit("---- endpoint resolution ----")
        emit("  nodes / unique keys : %d / %d%s" % (
            res["nodes"], res["node_keys"],
            "" if res["nodes"] == res["node_keys"] else "  <-- 键不够用，有节点在图上无处落脚"))
        emit("  edges both ends in graph : %d / %d" % (res["both_in_graph"], res["edges"]))
        emit("  one end off graph        : %d" % res["one_endpoint_off_graph"])
        emit("  both ends off graph      : %d" % res["both_endpoints_off_graph"])
        emit("  collapsed to self-loop   : %d" % res["collapsed_to_self_loop"])
        emit("  ambiguous doc ids        : %s" % (", ".join(res["ambiguous_doc_ids"]) or "NONE"))
    bad = sorted([name for name, (sev, count) in graph_mod.defect_counts(g).items()
                  if sev in ("DEFECT", "LEDGER-GAP") and count > 0])
    emit("==> verdict: %d 类 DEFECT/LEDGER-GAP 非空 -> %s" % (len(bad), ", ".join(bad) or "CLEAN"))
    return "\n".join(lines) + "\n"


def write_all(root, g, charts, meta, rows, face_text):
    written = []

    def w(relpath, text):
        data = text.encode("utf-8")
        path = os.path.join(root, relpath)
        if os.path.isdir(path):
            raise RuntimeError("生成物路径是目录，拒绝覆盖: %s" % relpath)
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, "wb") as handle:
            handle.write(data)
        written.append((relpath, len(data)))

    w(graph_mod.GRAPH_DIR + "/graph.json", json.dumps(g, ensure_ascii=False, indent=2) + "\n")
    for name in sorted(charts):
        w(graph_mod.FLOW_DIR + "/" + name, charts[name])
    for name in sorted(rows):
        w(graph_mod.XREF_DIR + "/" + name, rows[name])
    w(graph_mod.FACE_PATH, face_text)
    return written


def _md_rows(text):
    """数出一张 md 表的数据行（去掉分隔行与表头）。"""
    rows_seen = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        body = line.replace("|", "").strip()
        if body and set(body) <= set("-: "):
            continue
        rows_seen.append(line)
    return max(len(rows_seen) - 1, 0)


def xref_expectations(g):
    """由 graph 现推每张交叉引用表该有的数据行数（渲染器的行数不许自己证自己）。"""
    tags = set()
    terms = set()
    domains = set()
    levels = set()
    for node in g["nodes"]:
        for tag in node["tags"]:
            tags.add(str(tag))
            terms.add((str(tag), "标签"))
        for sym in node["symbols"]:
            terms.add((sym, "符号"))
        if node["domain"]:
            domains.add(node["domain"])
        levels.add(node["evidence_level"] or "未标")
    gap_classes = len(g["gaps"])
    return {
        "按ID.md": len(g["nodes"]),
        "按域.md": len(ids.DOMAINS) + len(domains - set(ids.DOMAINS)),
        "按标签.md": max(len(tags), 1),
        "按证据等级.md": len(LEVELS) + 1 + len(levels - set(LEVELS) - {"未标"}),
        "术语索引.md": len(terms),
        "引用图.md": len(g["edges"]),
        "缺口检测.md": gap_classes,
    }


def check_invariants(g, charts, meta, written, writes_expected=True, rows=None):
    faults = []
    for name, text in sorted(charts.items()):
        node_rows = [ln for ln in text.splitlines() if '["' in ln]
        if not node_rows:
            faults.append("EMPTY-CHART %s：图上零节点，不许算成功" % name)
        if "\r" in text or "\x00" in text:
            faults.append("BYTES %s：出现 CR 或 NUL" % name)
        if "\\" in text:
            faults.append("BACKSLASH %s：版面里不该有反斜杠（转义事故）" % name)
    for relpath, size in written:
        if size == 0:
            faults.append("EMPTY-FILE %s" % relpath)
    if writes_expected and not written:
        faults.append("NO-OUTPUT：一个生成物都没落")
    if not g["nodes"]:
        faults.append("NO-NODES：节点集为空，任何判决都无效")
    res = g.get("resolution") or {}
    if res.get("nodes") and res["node_keys"] != res["nodes"]:
        faults.append("KEY-COLLAPSE：%d 个节点只有 %d 个唯一键，至少 %d 个节点在图上无处落脚"                        % (res["nodes"], res["node_keys"], res["nodes"] - res["node_keys"]))
    if res.get("collapsed_to_self_loop"):
        faults.append("SELF-MERGE：%d 条边的两端解析成同一个键＝两个身份被静默合并"                        % res["collapsed_to_self_loop"])
    # 新增边型而 ARROW 表没跟上时，chart_record_deps 会把整型边静默跳过——上一轮
    # 就是这个形状把 57 条边抹成看不见的。判据不许靠"我记得加了"，要现扫图里的类型。
    rec_keys = set([graph_mod.node_key(n) for n in g["nodes"] if n["node_type"] == "record"])
    refs_t, _ = graph_mod.resolve(g["nodes"], g["edges"])
    unrendered = {}
    for edge, (a, b) in zip(g["edges"], refs_t):
        if a in rec_keys and b in rec_keys and edge["type"] not in ARROW:
            unrendered[edge["type"]] = unrendered.get(edge["type"], 0) + 1
    for etype in sorted(unrendered):
        faults.append("TYPE-UNRENDERED %s：%d 条记录间边在 02 图上无处可画＝ARROW 缺这一型，渲染器正静默丢掉它"
                      % (etype, unrendered[etype]))
    if rows is not None:
        # 渲染器不许自己证自己：期望行数由 graph 现推，再数表里实际落了几行。
        # 语料在写盘前又长了一条、或渲染器漏掉一类节点，都会在这里现形，
        # 而不是留下一张「看着挺全」的地图。
        expect = xref_expectations(g)
        for name in sorted(expect):
            text = rows.get(name)
            if text is None:
                faults.append("XREF-FILE %s：§五 承诺的表没渲染出来" % name)
                continue
            got = _md_rows(text)
            if got != expect[name]:
                faults.append("XREF-ROWS %s：图里应有 %d 行，实际渲染 %d 行" % (name, expect[name], got))
        for name in sorted(rows):
            if name not in expect:
                faults.append("XREF-UNKNOWN %s：不在 §五 承诺清单里，判据覆盖不到它" % name)
    return faults
