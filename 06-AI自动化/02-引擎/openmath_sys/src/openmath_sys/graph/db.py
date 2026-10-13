"""SQLite 持久化后端（企业级）。

把 GraphStore 的 nodes/edges 落盘到 SQLite，替代纯 JSON 文件。
- nodes 表：node_id PK, ntype, label, attrs_json
- edges 表：edge_id PK, src, dst, etype, evidence, attrs_json
- 索引：(src), (dst), (etype), (ntype)

用法：
    from openmath_sys.graph.db import save_sqlite, load_sqlite
    save_sqlite(g, "knowledge_graph.db")
    g2 = load_sqlite("knowledge_graph.db")
"""
from __future__ import annotations

import json
import os
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import GraphStore


SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id   TEXT PRIMARY KEY,
    ntype     TEXT NOT NULL,
    label     TEXT NOT NULL,
    attrs_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS edges (
    edge_id    TEXT PRIMARY KEY,
    src       TEXT NOT NULL,
    dst       TEXT NOT NULL,
    etype     TEXT NOT NULL,
    evidence  TEXT NOT NULL DEFAULT '',
    attrs_json TEXT NOT NULL DEFAULT '{}'
);
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    node_id UNINDEXED, label, ntype UNINDEXED, content='nodes', content_rowid='rowid'
);
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, node_id, label, ntype)
    VALUES (new.rowid, new.node_id, new.label, new.ntype);
END;
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(ntype);
CREATE INDEX IF NOT EXISTS idx_edges_src   ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst   ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_edges_type  ON edges(etype);
"""


def save_sqlite(g: "GraphStore", path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO nodes(node_id, ntype, label, attrs_json) VALUES(?,?,?,?)",
            [(n.node_id, n.ntype, n.label, json.dumps(n.attrs, ensure_ascii=False))
             for n in g.nodes.values()],
        )
        conn.executemany(
            "INSERT INTO edges(edge_id, src, dst, etype, evidence, attrs_json) VALUES(?,?,?,?,?,?)",
            [(e.edge_id, e.src, e.dst, e.etype, e.evidence, json.dumps(e.attrs, ensure_ascii=False))
             for e in g.edges],
        )
        conn.commit()
    finally:
        conn.close()


def load_sqlite(path: str) -> "GraphStore":
    from .store import GraphStore
    g = GraphStore()
    if not os.path.exists(path):
        return g
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        for row in conn.execute("SELECT * FROM nodes"):
            g.upsert_node(row["node_id"], row["ntype"], row["label"],
                          **json.loads(row["attrs_json"]))
        for row in conn.execute("SELECT * FROM edges"):
            g.add_edge(row["src"], row["dst"], row["etype"], row["evidence"],
                       **json.loads(row["attrs_json"]))
    finally:
        conn.close()
    return g


def stats_sqlite(path: str) -> dict:
    """只读统计（不落 GraphStore）。"""
    if not os.path.exists(path):
        return {}
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM nodes")
        nodes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM edges")
        edges = cur.fetchone()[0]
        cur.execute("SELECT ntype, COUNT(*) FROM nodes GROUP BY ntype ORDER BY 2 DESC")
        by_node_type = dict(cur.fetchall())
        cur.execute("SELECT etype, COUNT(*) FROM edges GROUP BY etype ORDER BY 2 DESC")
        by_edge_type = dict(cur.fetchall())
        return {"nodes": nodes, "edges": edges,
                "by_node_type": by_node_type, "by_edge_type": by_edge_type}
    finally:
        conn.close()


def search_sqlite(path: str, keyword: str, limit: int = 20) -> list[dict]:
    """FTS5 全文搜索节点 label。返回 [{node_id, label, ntype, rank}]。"""
    if not os.path.exists(path):
        return []
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        try:
            sql = """
                SELECT n.node_id, n.label, n.ntype
                FROM nodes_fts f
                JOIN nodes n ON n.rowid = f.rowid
                WHERE nodes_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            cur.execute(sql, (f'"{keyword}"*', limit))
        except sqlite3.OperationalError:
            cur.execute(
                "SELECT node_id, label, ntype FROM nodes WHERE label LIKE ? LIMIT ?",
                (f"%{keyword}%", limit),
            )
        return [{"node_id": r[0], "label": r[1], "ntype": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()
