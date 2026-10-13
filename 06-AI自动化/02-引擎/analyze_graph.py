"""企业级智能分析层：高风险卷册 / 中心度枢纽 / 反驳簇 / 判决一致性。

用法：
    python analyze_graph.py risk        # 被多勘误审计的高风险卷册
    python analyze_graph.py hubs        # 度排行 top 20 枢纽实体
    python analyze_graph.py verdicts    # 判决一致性（CONFIRMS vs REFUTES）
    python analyze_graph.py refutations # 反驳簇（含 REFUTES 边最多的卷册）
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph_store import GraphStore  # noqa: E402


def load() -> GraphStore:
    path = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.json")
    return GraphStore.load(path)


def cmd_risk(g: GraphStore, _: list[str]) -> None:
    """被多个勘误审计同时命中的卷册 = 高风险。"""
    audit_count = Counter()
    for e in g.edges:
        if e.etype == "AUDITS":
            audit_count[e.dst] += 1
    print("=== 高风险卷册（被多勘误审计）===")
    for nid, cnt in audit_count.most_common(15):
        n = g.nodes.get(nid)
        print(f"  [{cnt} 条勘误] {n.label if n else nid}")


def cmd_hubs(g: GraphStore, _: list[str]) -> None:
    """度排行：枢纽实体（连接最多）。"""
    degree = Counter()
    for e in g.edges:
        degree[e.src] += 1
        degree[e.dst] += 1
    print("=== 枢纽实体 top 20（度排行）===")
    for nid, deg in degree.most_common(20):
        n = g.nodes.get(nid)
        label = n.label if n else nid
        ntype = n.ntype if n else "?"
        print(f"  [{deg:3d} 边] ({ntype}) {label}")


def cmd_verdicts(g: GraphStore, _: list[str]) -> None:
    """判决一致性：CONFIRMS vs REFUTES 分布。"""
    confirm = [e for e in g.edges if e.etype == "CONFIRMS"]
    refute = [e for e in g.edges if e.etype == "REFUTES"]
    neutral = [e for e in g.edges if e.etype == "WORK" and False]
    print(f"=== 判决分布 ===")
    print(f"  CONFIRMS（已验证/闭合）: {len(confirm)}")
    print(f"  REFUTES（已拒/错位/OOM）: {len(refute)}")
    total = len(confirm) + len(refute)
    if total:
        print(f"  验证率: {len(confirm)/total*100:.1f}%   拒绝率: {len(refute)/total*100:.1f}%")


def cmd_refutations(g: GraphStore, _: list[str]) -> None:
    """反驳簇：含 REFUTES 边的卷册（研究试错热点）。"""
    refute_count = Counter()
    for e in g.edges:
        if e.etype == "REFUTES":
            refute_count[e.src] += 1
    print("=== 反驳热点卷册（REFUTES 边最多）===")
    for nid, cnt in refute_count.most_common(15):
        n = g.nodes.get(nid)
        print(f"  [{cnt} 次反驳] {n.label if n else nid}")


COMMANDS = {"risk": cmd_risk, "hubs": cmd_hubs, "verdicts": cmd_verdicts, "refutations": cmd_refutations}


def main() -> None:
    g = load()
    if len(sys.argv) < 2:
        print(__doc__)
        return
    handler = COMMANDS.get(sys.argv[1])
    if not handler:
        print(f"未知命令: {sys.argv[1]}；可用: {list(COMMANDS)}")
        return
    handler(g, sys.argv[2:])


if __name__ == "__main__":
    main()
