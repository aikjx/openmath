"""企业级智能分析：risk / hubs / verdicts / refutations / versions。"""
from __future__ import annotations

from collections import Counter

from .store import GraphStore


def risk(g: GraphStore, top: int = 15) -> list[tuple[str, int, str]]:
    """被多勘误审计命中的高风险卷册。"""
    c = Counter()
    for e in g.edges:
        if e.etype == "AUDITS":
            c[e.dst] += 1
    out = []
    for nid, cnt in c.most_common(top):
        n = g.nodes.get(nid)
        out.append((n.label if n else nid, cnt, nid))
    return out


def hubs(g: GraphStore, top: int = 20) -> list[tuple[str, int, str, str]]:
    """度排行枢纽。"""
    degree = Counter()
    for e in g.edges:
        degree[e.src] += 1
        degree[e.dst] += 1
    out = []
    for nid, deg in degree.most_common(top):
        n = g.nodes.get(nid)
        out.append((n.label if n else nid, deg, n.ntype if n else "?", nid))
    return out


def verdicts(g: GraphStore) -> dict:
    """判决分布（从 WORK.attrs['verdict'] 统计）。"""
    c = Counter()
    for n in g.nodes.values():
        if n.ntype == "WORK":
            c[n.attrs.get("verdict", "unknown")] += 1
    total = sum(c.values())
    return {
        "confirmed": c.get("confirmed", 0),
        "refuted": c.get("refuted", 0),
        "mixed": c.get("mixed", 0),
        "unknown": c.get("unknown", 0),
        "total": total,
        "confirm_rate": round(c.get("confirmed", 0) / total * 100, 1) if total else 0,
        "refute_rate": round(c.get("refuted", 0) / total * 100, 1) if total else 0,
    }


def refutations(g: GraphStore, top: int = 15) -> list[tuple[str, int, str]]:
    """REFUTES 边热点（自环边已去除，此为跨卷反驳）。"""
    c = Counter()
    for e in g.edges:
        if e.etype == "REFUTES":
            c[e.src] += 1
    out = []
    for nid, cnt in c.most_common(top):
        n = g.nodes.get(nid)
        out.append((n.label if n else nid, cnt, nid))
    return out


def version_chain(g: GraphStore) -> dict:
    """版本替代链按桶统计。"""
    c = Counter()
    for e in g.edges:
        if e.etype == "SUPERSEDES":
            bucket = e.attrs.get("bucket", "default")
            c[bucket] += 1
    return dict(c)
