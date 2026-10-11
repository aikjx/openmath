"""知识图谱、关系流程图与缺口检测。

产物全部是**生成物**（请勿手改）：
    10-文献与索引/知识图谱/graph.json
    10-文献与索引/知识图谱/流程图/NN-*.mmd
    10-文献与索引/知识图谱/_版面/graph_face.txt      ← 本模块所有读数的载体
    10-文献与索引/交叉引用索引/{按ID,术语索引,引用图,缺口检测}.md

为什么要单独建这一层：`openmath index` 只走 `OM-*.yaml`，而语料里大量账本住在
`OM-*.md`（含 03-难题与猜想 的整条攻坚线）。图这一层必须同时看得见两种载体，
否则「引用图」只覆盖机器可读的那一半，读者却会把它当成全部。
"""

import json
import os
import re
import time

from . import ids
from . import record as record_mod

GRAPH_DIR = "10-文献与索引/知识图谱"
FLOW_DIR = GRAPH_DIR + "/流程图"
FACE_PATH = GRAPH_DIR + "/_版面/graph_face.txt"
XREF_DIR = "10-文献与索引/交叉引用索引"
TIERS_PATH = "01-数学体系/域依赖.yaml"

SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", "外部仓库", "99-沙箱", "启动脚本"}

ID_RE = re.compile(r"OM-(?:[A-Z]{1,3}-(?:[A-Z]{2}-)?\d{4}|BR-\d{4}|SYS-\d{4})")
# 关系键的唯一来源：发射器按它建边，缺口判据按它点名「语料声明了、发射器不读」的键。
# 两处必须共用这张表，否则又是一次「generalizations 不在名单里 ⇒ 边静默丢掉」的缺陷。
EDGE_CHANNELS = (
    ("related", "related"),
    ("specializations", "specializes"),
    ("generalizations", "generalizes"),
    ("equivalent_forms", "implies"),
    ("implications", "implies"),
    ("contradicts", "contradicts"),
    ("uses", "uses"),
)
TEXT_REF_KEYS = ("proof", "hypotheses", "assumptions", "conclusion_latex", "domain_of_validity")
_FRONT_ID = re.compile(r"^id:\s*(OM-[A-Z0-9-]+)\s*$", re.M)
_TABLE_ID = re.compile(r"\|\s*\*\*ID\*\*\s*\|\s*(OM-[A-Z0-9-]+)\s*\|")
_FRONT_STATUS = re.compile(r"^status:\s*([A-Z_]+)\s*$", re.M)
_TABLE_STATUS = re.compile(r"\|\s*\*\*状态\*\*\s*\|\s*`?([A-Z_]+)`?")
_TIER_RANK = re.compile(r"^\s*-\s*rank:\s*(\d+)\s*$")
_TIER_DOMAINS = re.compile(r"^\s*domains:\s*\[([A-Z,\s]*)\]\s*$")
_TIER_LABEL = re.compile(r'^\s*label:\s*"(.*)"\s*$')
_UNPLACED = re.compile(r"^\s*-\s*code:\s*([A-Z]{2})\s*$")
_EDGE_STYLE = {
    "related": "---",
    "specializes": "-.->",
    "generalizes": "-.->",
    "implies": "==>|蕴含|",
    "uses": "-->",
    "bridges": "==>",
    "cites": "-->",
    "contradicts": "--x",
}


def _walk(root, suffix):
    out = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, "")):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for name in sorted(filenames):
            if name.endswith(suffix):
                rel = os.path.relpath(os.path.join(dirpath, name), root).replace("\\", "/")
                out.append(rel)
    return sorted(out)


def _flatten(value, acc):
    """把 YAML 里可能是 str / list / dict 的字段拉平成字符串序列。"""
    if isinstance(value, str):
        acc.append(value)
    elif isinstance(value, list):
        for item in value:
            _flatten(item, acc)
    elif isinstance(value, dict):
        for key, item in value.items():
            acc.append(str(key))
            _flatten(item, acc)
    elif value is not None:
        acc.append(str(value))
    return acc


def _fields(data, names):
    acc = []
    for name in names:
        if name in data:
            _flatten(data.get(name), acc)
    return acc


def _norm_tag(tag):
    return re.sub(r"[\s_\-]+", "", str(tag)).lower()


def _parse_tiers(path):
    """读 域依赖.yaml 的 rank/domains/unplaced（自带小解析器，两种 YAML 后端都能跑）。"""
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    tiers = []
    section = None
    pending = None
    unplaced = []
    for line in text.splitlines():
        if line.startswith("tiers:"):
            section = "tiers"
            continue
        if line.startswith("unplaced_domains:"):
            section = "unplaced"
            continue
        if line.startswith("intra_tier_edges:"):
            section = "other"
        if section == "unplaced":
            hit = _UNPLACED.match(line)
            if hit:
                unplaced.append(hit.group(1))
            continue
        if section != "tiers":
            continue
        hit = _TIER_RANK.match(line)
        if hit:
            pending = {"rank": int(hit.group(1)), "domains": [], "label": ""}
            tiers.append(pending)
            continue
        hit = _TIER_DOMAINS.match(line)
        if hit and pending is not None:
            pending["domains"] = [d for d in hit.group(1).replace(" ", "").split(",") if d]
            continue
        hit = _TIER_LABEL.match(line)
        if hit and pending is not None:
            pending["label"] = hit.group(1)
    intra = []
    for line in text.splitlines():
        hit = re.match(r"^\s*-\s*\[\"\s*([A-Z]{2})\s*\",\s*\"\s*([A-Z]{2})\s*\",", line)
        if hit:
            intra.append((hit.group(1), hit.group(2)))
    return tiers, unplaced, intra


def _md_ledger(root):
    """扫全部 OM-*.md 账本。

    三种身份要分开（否则会把"记录的人类面孔"当成缺陷）：
      docs     —— 没有 .yaml 伴生的 md（机器索引看不见它，是 LEDGER-GAP）
      evidence —— 05-验证中心 的结果档（只作旁证，不作知识节点）
      paired   —— 与 .yaml 同名的 md 面孔（记录本体已在节点集里，不再建节点）
    all_md 用来解析文件名链接：链接目标可以是三种中的任何一种。
    """
    docs = []
    evidence = []
    paired = []
    all_md = set()
    id_hits = {}
    for rel in _walk(root, ".md"):
        base = os.path.basename(rel)
        if not base.startswith("OM-"):
            continue
        all_md.add(rel)
        has_yaml = os.path.exists(os.path.join(root, rel[: -len(".md")] + ".yaml"))
        with open(os.path.join(root, rel), "r", encoding="utf-8") as handle:
            text = handle.read()
        head = text[:4000]
        identifier = None
        hit = _FRONT_ID.search(text[:2000])
        if hit:
            identifier = hit.group(1)
        else:
            hit = _TABLE_ID.search(head)
            if hit:
                identifier = hit.group(1)
        if identifier is None:
            hit = ID_RE.search(base)
            identifier = hit.group(0) if hit else None
        status = None
        hit = _FRONT_STATUS.search(text[:2000])
        if hit:
            status = hit.group(1)
        else:
            hit = _TABLE_STATUS.search(head)
            if status is None and hit:
                status = hit.group(1)
        title = None
        for line in text.splitlines()[:40]:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        # 攻坚线（24 轮 OM-P-NT-0003-goldbach-*.md）之间的关系住在**文件名链接**里，
        # 不在 ID 里；只按 ID 建边的图会把这条线整段看不见，所以文件名链接也算引用。
        link_targets = set()
        for hit in re.finditer(r"\]\((OM-[^\s)]+?\.md)\)", text):
            link_targets.add(os.path.dirname(rel) + "/" + hit.group(1))
        record = {
            "rel": rel,
            "id": identifier,
            "status": status,
            "title": title,
            "ids_cited": sorted(set(ID_RE.findall(text)) - ({identifier} if identifier else set())),
            "links": sorted(link_targets),
            "roles": sorted(set(ID_RE.findall(base))),
        }
        if has_yaml:
            paired.append(record)
            continue
        if rel.startswith("05-验证中心/"):
            evidence.append(record)
        else:
            docs.append(record)
        if identifier:
            id_hits.setdefault(identifier, []).append(rel)
    return docs, evidence, paired, all_md, id_hits


def _node_from_record(rec):
    data = rec["data"]
    level = data.get("evidence_level")
    script = None
    levels = ((data.get("verification") or {}).get("levels")) or {}
    block = levels.get(str(level)) if isinstance(level, str) else None
    if isinstance(block, dict):
        script = block.get("script")
    symbols = []
    for item in data.get("symbols") or []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            symbols.append(item["name"])
    return {
        "node_type": "record",
        "id": rec.get("id"),
        "kind": data.get("kind"),
        "domain": data.get("domain"),
        "status": data.get("status"),
        "evidence_level": level,
        "title_zh": data.get("title_zh"),
        "path": rec["rel"],
        "tags": [str(t) for t in (data.get("tags") or [])],
        "symbols": symbols,
        "script": script,
        "latex": (data.get("latex") or data.get("statement_latex") or "").strip() or None,
        "machine_readable": True,
    }


def _edges_from_record(rec, node_by_id):
    data = rec["data"]
    origin = rec.get("id")
    edges = []
    seen = set()

    def add(target, etype, via):
        if not isinstance(target, str) or target == origin:
            return
        key = (origin, target, etype, via)
        if key in seen:
            return
        seen.add(key)
        edges.append({
            "src": origin,
            "dst": target,
            "type": etype,
            "via": via,
            "resolvable": target in node_by_id,
        })

    def add_list(name, etype):
        value = data.get(name)
        if not isinstance(value, list):
            return
        prose = []
        for item in value:
            if isinstance(item, str):
                found = ID_RE.findall(item)
                if found:
                    for target in found:
                        add(target, etype, name)
                else:
                    prose.append(item)
        return prose

    prose = []
    for name, etype in EDGE_CHANNELS:
        got = add_list(name, etype)
        if got:
            prose.extend((name, line) for line in got)

    for target in sorted(set(ID_RE.findall(" \n".join(_fields(data, TEXT_REF_KEYS))))):
        add(target, "uses", "正文引用")

    return edges, prose


def node_key(node):
    """节点唯一键：record 用 ID，doc 用相对路径。

    依据是实测而非惯例：19 个 record 的 ID 互不相同，24 个 doc 的路径互不相同，
    而 doc 的 ID 有 13 份共用 `OM-P-NT-0003`。按 ID 给 doc 建键会把 13 张面孔折成
    1 个节点，且 `build()` 里 `src = doc["rel"]` 的两个通道永远查不到键——
    流程图于是静默少画一批边，而少画的那批恰好是攻坚轮次那条线。
    """
    return node["id"] if node["node_type"] == "record" else node["path"]


def resolve(nodes, edges):
    """把边端点还原到节点键。端点按语料原样存（ID 或路径），两个命名空间都要认。

    返回 (refs, ambiguous)：refs[i] = (src 键或 None, dst 键或 None)。
    None ＝ 这一端在节点集里没有载体（证据档、配对 md 面孔、无载体的号）。
    撞号 ID 若无 record 主则一律判 None——宁可少连一条边，不许静默挑一份面孔连上。
    """
    keys = set()
    by_id = {}
    doc_id = {}
    for node in nodes:
        key = node_key(node)
        keys.add(key)
        ident = node["id"]
        if not isinstance(ident, str):
            continue
        if node["node_type"] == "record":
            by_id[ident] = key
        else:
            doc_id.setdefault(ident, []).append(key)
    ambiguous = sorted([i for i, ks in doc_id.items() if len(ks) > 1 and i not in by_id])
    for ident in sorted(doc_id):
        ks = doc_id[ident]
        if len(ks) == 1 and ident not in by_id:
            by_id[ident] = ks[0]
    for ident in ambiguous:
        by_id.pop(ident, None)

    def one(endpoint):
        if endpoint in keys:
            return endpoint
        return by_id.get(endpoint)

    return [(one(e["src"]), one(e["dst"])) for e in edges], ambiguous


def off_graph_edges(nodes, edges):
    """端点落不进节点集的边，逐条点名并标出它住在哪个通道（via）。"""
    refs, _ = resolve(nodes, edges)
    out = []
    for edge, (a, b) in zip(edges, refs):
        missing = [w for w, r in ((edge["src"], a), (edge["dst"], b)) if r is None]
        if missing:
            out.append({"src": edge["src"], "dst": edge["dst"], "type": edge["type"],
                        "via": edge["via"], "off": sorted(missing)})
    return sorted(out, key=lambda r: (r["type"], r["src"], r["dst"], r["via"]))


def resolution_census(nodes, edges):
    """解析普查：面只印这里的数，文档只许引这张面。"""
    refs, ambiguous = resolve(nodes, edges)
    return {
        "nodes": len(nodes),
        "node_keys": len(set([node_key(n) for n in nodes])),
        "edges": len(edges),
        "both_in_graph": sum(1 for a, b in refs if a and b),
        "one_endpoint_off_graph": sum(1 for a, b in refs if bool(a) != bool(b)),
        "both_endpoints_off_graph": sum(1 for a, b in refs if not a and not b),
        "collapsed_to_self_loop": sum(1 for a, b in refs if a and b and a == b),
        "ambiguous_doc_ids": ambiguous,
    }


def build(root):
    records, load_errors = record_mod.load_all(root)
    docs, evidence, paired, all_md, md_id_hits = _md_ledger(root)

    nodes = []
    node_by_id = {}
    dup_ids = []
    for rec in records:
        node = _node_from_record(rec)
        nodes.append(node)
        if isinstance(node["id"], str):
            node_by_id.setdefault(node["id"], node)
    yaml_ids = {n["id"] for n in nodes if isinstance(n["id"], str)}

    for doc in docs:
        domain = None
        if doc["id"]:
            try:
                domain = ids.parse(doc["id"]).get("domain")
            except ids.IdError:
                domain = None
        node = {
            "node_type": "doc",
            "id": doc["id"],
            "kind": "doc-ledger",
            "domain": domain,
            "status": doc["status"],
            "evidence_level": None,
            "title_zh": doc["title"],
            "path": doc["rel"],
            "tags": [],
            "symbols": [],
            "script": None,
            "latex": None,
            "machine_readable": False,
        }
        nodes.append(node)
        if doc["id"] and doc["id"] in yaml_ids:
            dup_ids.append({
                "id": doc["id"],
                "yaml": node_by_id[doc["id"]]["path"],
                "md": doc["rel"],
                "same_title": (node_by_id[doc["id"]]["title_zh"] == doc["title"]),
            })
        elif doc["id"] and doc["id"] not in node_by_id:
            node_by_id[doc["id"]] = node

    edges = []
    prose_relations = []
    broken_links = []
    for rec in records:
        part, prose = _edges_from_record(rec, node_by_id)
        edges.extend(part)
        prose_relations.extend([{"src": rec.get("id"), "field": f, "text": t} for f, t in prose])

    for doc in docs:
        for target in doc["ids_cited"]:
            edges.append({
                "src": doc["rel"],
                "dst": target,
                "type": "cites",
                "via": "md 账本正文（ID 引用）",
                "resolvable": target in node_by_id,
            })
        for target_rel in doc["links"]:
            exists = target_rel in all_md
            edges.append({
                "src": doc["rel"],
                "dst": target_rel,
                "type": "cites",
                "via": "md 文件名链接（攻坚轮次）",
                "resolvable": exists,
            })
            if not exists:
                broken_links.append({"from": doc["rel"], "link": target_rel})
    for md in paired:
        owner = md["id"]
        if owner not in node_by_id:
            continue
        for target in md["ids_cited"]:
            edges.append({
                "src": owner,
                "dst": target,
                "type": "cites",
                "via": "配对 md 正文（ID 引用）",
                "resolvable": target in node_by_id,
            })
        for target_rel in md["links"]:
            edges.append({
                "src": owner,
                "dst": target_rel,
                "type": "cites",
                "via": "配对 md 正文（文件名链接）",
                "resolvable": target_rel in all_md,
            })
            if target_rel not in all_md:
                broken_links.append({"from": md["rel"], "link": target_rel})

    bridge_docs = [d for d in docs if "/04-桥接定理/" in d["rel"] or "/03-跨纲领翻译表/" in d["rel"]]
    for doc in bridge_docs:
        cited = [node_by_id.get(t) for t in doc["ids_cited"]]
        cited = [n for n in cited if n and n.get("domain")]
        for i in range(len(cited)):
            for j in range(i + 1, len(cited)):
                if cited[i]["domain"] != cited[j]["domain"]:
                    edges.append({
                        "src": node_key(cited[i]),
                        "dst": node_key(cited[j]),
                        "type": "bridges",
                        "via": doc["rel"],
                        "resolvable": True,
                    })

    for ev in evidence:
        for target in ev["ids_cited"]:
            edges.append({
                "src": target,
                "dst": ev["rel"],
                "type": "evidenced_by",
                "via": "05-验证中心 结果档",
                "resolvable": True,
            })

    gaps = detect_gaps(root, records, nodes, edges, docs, evidence, md_id_hits, dup_ids,
                       prose_relations, load_errors)
    tiers, unplaced, intra = _parse_tiers(os.path.join(root, TIERS_PATH))
    placed = sorted({d for tier in tiers for d in tier["domains"]})
    missing_placement = sorted(set(ids.DOMAINS) - set(placed) - set(unplaced))
    gaps["DOMAIN_UNPLACED"] = missing_placement
    gaps["BROKEN_DOC_LINK"] = broken_links
    # 撞号的下游代价：任何指向 OM-P-NT-0003 的边都不知该落到哪条记录上。
    # 不裁决谁该改号（那是编号主人的决定，且涉及 88 份文件的引用），只把不能
    # 归属的边逐条点名，防止图把两条主张静默合并成一条。
    colliding_ids = {item["id"] for item in dup_ids}
    gaps["AMBIGUOUS_REFERENCE"] = sorted(
        [{"src": e["src"], "dst": e["dst"], "via": e["via"]} for e in edges if e["dst"] in colliding_ids],
        key=lambda r: (r["dst"], r["src"], r["via"]))
    # 边写好了、端点却不在节点集里：这条关系在图上无处落脚。证据通道（05-验证中心
    # 结果档本来就不作知识节点）与配对面孔都算，但逐条点名 via，不靠手工豁免。
    gaps["EDGE_ENDPOINT_OFF_GRAPH"] = off_graph_edges(nodes, edges)
    # 「A 与 B 冲突」是对称事实：只记在 A 那一侧，等于 B 的读者永远不知道自己的
    # 条目被人指过矛盾。这一类不裁决谁对谁错（那是证据等级的事），只点名单边账。
    conflicts = set()
    for e in edges:
        if e["type"] == "contradicts":
            conflicts.add((e["src"], e["dst"]))
    gaps["CONTRADICTION_ASYMMETRIC"] = sorted(
        [{"src": e["src"], "dst": e["dst"], "via": e["via"]} for e in edges
         if e["type"] == "contradicts" and (e["dst"], e["src"]) not in conflicts],
        key=lambda r: (r["src"], r["dst"], r["via"]))

    g = {
        "schema_version": "0.1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": os.path.basename(root),
        "nodes": sorted(nodes, key=lambda n: (str(n["id"] or "~"), n["path"])),
        "edges": sorted(edges, key=lambda e: (e["src"], e["type"], e["dst"])),
        "tiers": {"ranks": tiers, "unplaced": unplaced, "intra": intra,
                  "missing_placement": missing_placement},
        "gaps": gaps,
        "resolution": resolution_census(nodes, edges),
        "counts": {
            "record_nodes": sum(1 for n in nodes if n["node_type"] == "record"),
            "doc_nodes": sum(1 for n in nodes if n["node_type"] == "doc"),
            "evidence_docs": len(evidence),
            "edges": len(edges),
            "load_errors": len(load_errors),
        },
    }
    return g


def detect_gaps(root, records, nodes, edges, docs, evidence, md_id_hits, dup_ids,
                prose_relations, load_errors):
    node_ids = {n["id"] for n in nodes if isinstance(n["id"], str)}
    dangling = sorted({e["dst"] for e in edges if not e["resolvable"]})
    refs, _ = resolve(nodes, edges)
    degree = {}
    for n in nodes:
        degree[node_key(n)] = 0
    for e, (a, b) in zip(edges, refs):
        for key in (a, b):
            if key in degree:
                degree[key] += 1
    orphans = sorted([k for k, v in degree.items() if v == 0])

    defined_symbols = set()
    for n in nodes:
        if n["kind"] == "definition":
            defined_symbols.update(n["symbols"])
            if isinstance(n["title_zh"], str):
                defined_symbols.add(n["title_zh"])
    used_symbols = {}
    for n in nodes:
        for name in n["symbols"]:
            used_symbols.setdefault(name, []).append(node_key(n))
    undefined_symbols = sorted([s for s in used_symbols if s not in defined_symbols])

    inversions = []
    for n in nodes:
        if n["node_type"] != "record":
            continue
        level = n.get("evidence_level")
        status = str(n.get("status") or "")
        hit = re.search(r"VERIFIED\((L\d)\)", status)
        claimed = None
        if isinstance(level, str) and level in ("L4", "L5", "L6"):
            claimed = level
        elif hit:
            claimed = hit.group(1)
        if claimed is None:
            continue
        data = None
        for rec in records:
            if rec.get("id") == n["id"]:
                data = rec["data"]
                break
        block = (((data or {}).get("verification") or {}).get("levels") or {}).get(claimed) or {}
        script = block.get("script") if isinstance(block, dict) else None
        passed = isinstance(block, dict) and block.get("passed") is True
        on_disk = bool(script) and os.path.exists(os.path.join(root, str(script)))
        if not (passed and on_disk):
            inversions.append({"id": n["id"], "claimed": claimed, "passed": passed,
                               "script": script, "script_on_disk": on_disk})

    tagmap = {}
    for n in nodes:
        for tag in n["tags"]:
            tagmap.setdefault(_norm_tag(tag), set()).add(tag)
    inconsistent = {k: sorted(v) for k, v in sorted(tagmap.items()) if len(v) > 1}

    dup_files = []
    for identifier, rels in sorted(md_id_hits.items()):
        if len(rels) > 1:
            dup_files.append({"id": identifier, "files": rels})

    md_without_yaml = sorted([d["rel"] for d in docs] + [e["rel"] for e in evidence])
    # 语料自己声明「这一键是一组关系」（值＝纯 ID 字符串列表），而发射器的通道名单不读它
    # ⇒ 那些边在图上无处可画，且没有任何一台仪器会红。名单由语料现推，不打字。
    consumed_keys = set([k for k, _ in EDGE_CHANNELS]) | set(TEXT_REF_KEYS)
    unread_keys = {}
    for rec in records:
        for key, value in (rec["data"] or {}).items():
            if key in consumed_keys or not isinstance(value, list):
                continue
            bare = [x for x in value if isinstance(x, str) and ID_RE.fullmatch(x.strip())]
            if bare:
                k = "%s（%s）" % (key, rec.get("id"))
                unread_keys[k] = unread_keys.get(k, 0) + len(bare)
    relation_unread = sorted(["%s：%d 条边在图上无处可画" % (k, n)
                              for k, n in unread_keys.items()])

    seen_pairs = set()
    id_collisions = []
    for item in dup_ids:
        key = (item["id"], item["yaml"])
        if key not in seen_pairs:
            seen_pairs.add(key)
            id_collisions.append(item)

    return {
        "DANGLING": dangling,
        "ORPHAN": orphans,
        "MD_ONLY_LEDGER": md_without_yaml,
        "ID_MULTI_FILE": dup_files,
        "ID_COLLISION_YAML_VS_MD": id_collisions,
        "UNDEFINED_SYMBOL": undefined_symbols,
        "RELATION_KEY_UNREAD": relation_unread,
        "EVIDENCE_INVERSION": inversions,
        "PROSE_RELATION_UNTRAVERSABLE": prose_relations,
        "TERM_INCONSISTENCY": inconsistent,
        "LOAD_ERROR": [e["rel"] + ": " + str(e["error"]) for e in load_errors],
    }


SEVERITY = {
    "DANGLING": "DEFECT",
    "ID_COLLISION_YAML_VS_MD": "DEFECT",
    "DOMAIN_UNPLACED": "DEFECT",
    "AMBIGUOUS_REFERENCE": "DEFECT",
    "BROKEN_DOC_LINK": "DEFECT",
    "EVIDENCE_INVERSION": "DEFECT",
    "LOAD_ERROR": "DEFECT",
    "MD_ONLY_LEDGER": "LEDGER-GAP",
    "EDGE_ENDPOINT_OFF_GRAPH": "LEDGER-GAP",
    "RELATION_KEY_UNREAD": "LEDGER-GAP",
    "ID_MULTI_FILE": "LEDGER-GAP",
    "ORPHAN": "ADVISORY",
    "UNDEFINED_SYMBOL": "ADVISORY",
    "PROSE_RELATION_UNTRAVERSABLE": "ADVISORY",
    "CONTRADICTION_ASYMMETRIC": "ADVISORY",
    "TERM_INCONSISTENCY": "ADVISORY",
}


def defect_counts(g):
    out = {}
    for name, value in g["gaps"].items():
        out[name] = (SEVERITY.get(name, "ADVISORY"),
                     len(value) if hasattr(value, "__len__") else 0)
    return out
