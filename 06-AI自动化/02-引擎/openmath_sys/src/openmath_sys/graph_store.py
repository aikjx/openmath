"""统一研究知识图谱：实体-关系多对多存储与查询。

设计要点（对应"全维无限扩展、多对对"诉求）：
- 实体（Node）多对多挂边（Edge），无向/有向统一表达；
- 每个实体带 type（WORK/THEOREM/CLAIM/AUDIT/FINDING/PERSONA/TOOL）与属性；
- 每种关系带 type（CITES/REFUTES/CONFIRMS/EXTENDS/SUPERSEDES/AUDITS/USES/BELONGS_TO）与证据指针；
- JSON 持久化，可增量合并；
- 查询：邻居、按类型统计、反驳链、引用链。
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable


# ---- 常量枚举（字符串，JSON 友好） ----
NODE_TYPES = ("WORK", "THEOREM", "CLAIM", "AUDIT", "FINDING", "PERSONA", "TOOL", "DATASET")
EDGE_TYPES = (
    "CITES",        # A 引用 B
    "REFUTES",      # A 反驳/排除 B 的结论
    "CONFIRMS",     # A 验证/确认 B
    "EXTENDS",      # A 扩展 B
    "SUPERSEDES",   # A 替代 B（版本升级）
    "AUDITS",       # A 审计 B
    "USES",         # A 使用 B（方法/工具/数据）
    "BELONGS_TO",   # A 归属 B（域/卷）
    "DERIVES_FROM", # A 推导自 B
)


@dataclass
class Node:
    node_id: str
    ntype: str
    label: str
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Edge:
    edge_id: str
    src: str
    dst: str
    etype: str
    evidence: str = ""          # 证据指针（文件路径/页码/行号）
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class GraphStore:
    """多对多知识图谱存储。"""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._adj: dict[str, list[Edge]] = defaultdict(list)
        self._edge_seq = 0

    # ---- 写入（幂等：同 node_id 覆盖，同边签名去重） ----
    def upsert_node(self, node_id: str, ntype: str, label: str, **attrs: Any) -> Node:
        if ntype not in NODE_TYPES:
            raise ValueError(f"unknown node type: {ntype}")
        n = Node(node_id=node_id, ntype=ntype, label=label, attrs=attrs)
        self.nodes[node_id] = n
        return n

    def add_edge(self, src: str, dst: str, etype: str, evidence: str = "", **attrs: Any) -> Edge:
        if etype not in EDGE_TYPES:
            raise ValueError(f"unknown edge type: {etype}")
        sig = (src, dst, etype)
        for e in self.edges:
            if (e.src, e.dst, e.etype) == sig:
                if evidence and not e.evidence:
                    e.evidence = evidence
                return e
        self._edge_seq += 1
        e = Edge(
            edge_id=f"e{self._edge_seq}",
            src=src, dst=dst, etype=etype, evidence=evidence, attrs=attrs,
        )
        self.edges.append(e)
        self._adj[src].append(e)
        self._adj[dst].append(e)
        return e

    # ---- 查询 ----
    def neighbors(self, node_id: str, etype: str | None = None, direction: str = "both") -> list[Edge]:
        out = []
        for e in self._adj.get(node_id, []):
            if etype and e.etype != etype:
                continue
            if direction == "out" and e.src != node_id:
                continue
            if direction == "in" and e.dst != node_id:
                continue
            out.append(e)
        return out

    def node_type_counts(self) -> dict[str, int]:
        return dict(Counter(n.ntype for n in self.nodes.values()))

    def edge_type_counts(self) -> dict[str, int]:
        return dict(Counter(e.etype for e in self.edges))

    def find_refutation_chain(self, root_id: str) -> list[Edge]:
        """从某实体出发的直接 REFUTES/CONFIRMS 判决边。"""
        return [e for e in self._adj.get(root_id, []) if e.etype in ("REFUTES", "CONFIRMS")]

    def shortest_path(self, src: str, dst: str, max_hops: int = 6) -> list[Edge] | None:
        """BFS 最短边链（按边的方向忽略，多对多无向图）。"""
        if src == dst:
            return []
        prev: dict[str, tuple[str, Edge]] = {}
        frontier = [src]
        seen = {src}
        for _ in range(max_hops):
            nxt = []
            for cur in frontier:
                for e in self._adj.get(cur, []):
                    nxt_node = e.dst if e.src == cur else e.src
                    if nxt_node in seen:
                        continue
                    seen.add(nxt_node)
                    prev[nxt_node] = (cur, e)
                    if nxt_node == dst:
                        chain = []
                        node = dst
                        while node != src:
                            p, edge = prev[node]
                            chain.append(edge)
                            node = p
                        chain.reverse()
                        return chain
                    nxt.append(nxt_node)
            frontier = nxt
        return None

    # ---- 持久化 ----
    def export(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "stats": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "by_node_type": self.node_type_counts(),
                "by_edge_type": self.edge_type_counts(),
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "GraphStore":
        g = cls()
        if not os.path.exists(path):
            return g
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        for n in payload.get("nodes", []):
            g.upsert_node(n["node_id"], n["ntype"], n["label"], **n.get("attrs", {}))
        for e in payload.get("edges", []):
            g.add_edge(e["src"], e["dst"], e["etype"], e.get("evidence", ""), **e.get("attrs", {}))
        return g
