"""统一知识图谱查询入口：邻居/统计/反驳链/最短路径。

用法：
    python query_graph.py stats                     # 总览统计
    python query_graph.py neighbors <node_id>        # 查某实体所有边
    python query_graph.py audits                    # 列出全部审计/勘误
    python query_graph.py supersede                  # 版本替代链
    python query_graph.py path <src_id> <dst_id>     # 最短路径
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph_store import GraphStore  # noqa: E402


def load() -> GraphStore:
    path = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.json")
    return GraphStore.load(path)


def cmd_stats(g: GraphStore, _: list[str]) -> None:
    print("=== 图谱总览 ===")
    print(f"节点: {len(g.nodes)}  边: {len(g.edges)}")
    print("按类型节点:", g.node_type_counts())
    print("按类型边:", g.edge_type_counts())


def cmd_neighbors(g: GraphStore, args: list[str]) -> None:
    if not args:
        print("用法: neighbors <node_id>")
        return
    nid = args[0]
    if nid not in g.nodes:
        print(f"未找到节点: {nid}")
        return
    n = g.nodes[nid]
    print(f"=== {n.label} ({nid}) ===")
    for e in g.neighbors(nid):
        other = e.dst if e.src == nid else e.src
        other_label = g.nodes[other].label if other in g.nodes else other
        direction = "→" if e.src == nid else "←"
        print(f"  {direction} [{e.etype}] {other_label}  ({e.evidence})")


def cmd_audits(g: GraphStore, _: list[str]) -> None:
    print("=== 勘误/审计 ===")
    for nid, n in g.nodes.items():
        if n.ntype == "AUDIT":
            targets = [e for e in g.edges if e.src == nid and e.etype == "AUDITS"]
            for e in targets:
                tgt = g.nodes.get(e.dst)
                print(f"  {n.label} 审计 → {tgt.label if tgt else e.dst}  ({e.evidence})")


def cmd_supersede(g: GraphStore, _: list[str]) -> None:
    print("=== 版本替代链（最新→最旧前 15） ===")
    edges = [e for e in g.edges if e.etype == "SUPERSEDES"]
    for e in edges[:15]:
        src = g.nodes.get(e.src)
        dst = g.nodes.get(e.dst)
        print(f"  {src.label if src else e.src}  ⟵ 替代 {dst.label if dst else e.dst}")


def cmd_path(g: GraphStore, args: list[str]) -> None:
    if len(args) < 2:
        print("用法: path <src_id> <dst_id>")
        return
    chain = g.shortest_path(args[0], args[1])
    if chain is None:
        print("无路径")
        return
    print(f"路径长度: {len(chain)} 跳")
    node = args[0]
    print(f"  {g.nodes[node].label if node in g.nodes else node}")
    for e in chain:
        nxt = e.dst if e.src == node else e.src
        lbl = g.nodes[nxt].label if nxt in g.nodes else nxt
        print(f"  --[{e.etype}]--> {lbl}")
        node = nxt


COMMANDS = {
    "stats": cmd_stats,
    "neighbors": cmd_neighbors,
    "audits": cmd_audits,
    "supersede": cmd_supersede,
    "path": cmd_path,
}


def main() -> None:
    g = load()
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"未知命令: {cmd}；可用: {list(COMMANDS)}")
        return
    handler(g, sys.argv[2:])


if __name__ == "__main__":
    main()
