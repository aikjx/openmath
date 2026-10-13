"""graph_store 核心单元测试（企业级细粒度）。

覆盖：Node/Edge 构造、upsert 幂等、add_edge 去重、类型校验、
neighbors 双向、shortest_path BFS、export/load 往返。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.store import GraphStore, Node, Edge, NODE_TYPES, EDGE_TYPES  # noqa: E402


class TestNodeEdge(unittest.TestCase):
    def test_node_creation(self):
        n = Node(node_id="work:t1", ntype="WORK", label="测试卷", attrs={"domain": "tuft"})
        self.assertEqual(n.node_id, "work:t1")
        self.assertEqual(n.ntype, "WORK")
        self.assertEqual(n.attrs["domain"], "tuft")

    def test_edge_creation(self):
        e = Edge(edge_id="e1", src="a", dst="b", etype="CITES", evidence="t1.md")
        self.assertEqual(e.src, "a")
        self.assertEqual(e.etype, "CITES")
        self.assertEqual(e.evidence, "t1.md")


class TestUpsert(unittest.TestCase):
    def setUp(self):
        self.g = GraphStore()

    def test_upsert_new_node(self):
        self.g.upsert_node("a", "WORK", "A")
        self.assertIn("a", self.g.nodes)
        self.assertEqual(self.g.nodes["a"].label, "A")

    def test_upsert_overwrite(self):
        self.g.upsert_node("a", "WORK", "A")
        self.g.upsert_node("a", "WORK", "A-v2")
        self.assertEqual(self.g.nodes["a"].label, "A-v2")
        self.assertEqual(len(self.g.nodes), 1)

    def test_upsert_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            self.g.upsert_node("x", "INVALID", "x")


class TestAddEdge(unittest.TestCase):
    def setUp(self):
        self.g = GraphStore()
        self.g.upsert_node("a", "WORK", "A")
        self.g.upsert_node("b", "WORK", "B")

    def test_add_edge(self):
        e = self.g.add_edge("a", "b", "CITES", evidence="a.md")
        self.assertEqual(len(self.g.edges), 1)
        self.assertEqual(e.etype, "CITES")

    def test_add_edge_dedup(self):
        """同 (src,dst,etype) 签名不重复。"""
        self.g.add_edge("a", "b", "CITES", evidence="first.md")
        self.g.add_edge("a", "b", "CITES", evidence="second.md")
        self.assertEqual(len(self.g.edges), 1)
        # 已有 evidence 时不覆盖
        self.assertEqual(self.g.edges[0].evidence, "first.md")

    def test_add_edge_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            self.g.add_edge("a", "b", "INVALID")


class TestNeighbors(unittest.TestCase):
    def setUp(self):
        self.g = GraphStore()
        for nid in ("a", "b", "c"):
            self.g.upsert_node(nid, "WORK", nid)
        self.g.add_edge("a", "b", "CITES")
        self.g.add_edge("c", "a", "AUDITS")

    def test_neighbors_both(self):
        ns = self.g.neighbors("a")
        self.assertEqual(len(ns), 2)

    def test_neighbors_out(self):
        ns = self.g.neighbors("a", direction="out")
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0].dst, "b")

    def test_neighbors_in(self):
        ns = self.g.neighbors("a", direction="in")
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0].src, "c")

    def test_neighbors_by_type(self):
        ns = self.g.neighbors("a", etype="CITES")
        self.assertEqual(len(ns), 1)


class TestShortestPath(unittest.TestCase):
    def setUp(self):
        self.g = GraphStore()
        for nid in ("a", "b", "c", "d"):
            self.g.upsert_node(nid, "WORK", nid)
        self.g.add_edge("a", "b", "CITES")
        self.g.add_edge("b", "c", "CITES")
        self.g.add_edge("c", "d", "CITES")

    def test_direct_path(self):
        chain = self.g.shortest_path("a", "b")
        self.assertEqual(len(chain), 1)

    def test_two_hop_path(self):
        chain = self.g.shortest_path("a", "c")
        self.assertEqual(len(chain), 2)

    def test_same_node_empty(self):
        self.assertEqual(self.g.shortest_path("a", "a"), [])

    def test_no_path_returns_none(self):
        self.g.upsert_node("isolated", "WORK", "iso")
        self.assertIsNone(self.g.shortest_path("a", "isolated"))

    def test_max_hops(self):
        """超过 max_hops 返回 None。"""
        self.assertIsNone(self.g.shortest_path("a", "d", max_hops=2))


class TestExportLoad(unittest.TestCase):
    def test_roundtrip(self):
        g = GraphStore()
        g.upsert_node("a", "WORK", "A", domain="tuft")
        g.upsert_node("b", "AUDIT", "勘误#1")
        g.add_edge("b", "a", "AUDITS", evidence="b.md")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "graph.json")
            g.export(path)
            self.assertTrue(os.path.exists(path))

            g2 = GraphStore.load(path)
            self.assertEqual(len(g2.nodes), 2)
            self.assertEqual(len(g2.edges), 1)
            self.assertEqual(g2.nodes["a"].attrs["domain"], "tuft")
            self.assertEqual(g2.edges[0].etype, "AUDITS")

    def test_load_missing_file_returns_empty(self):
        g = GraphStore.load("nonexistent.json")
        self.assertEqual(len(g.nodes), 0)


class TestCounts(unittest.TestCase):
    def test_node_type_counts(self):
        g = GraphStore()
        g.upsert_node("a", "WORK", "A")
        g.upsert_node("b", "WORK", "B")
        g.upsert_node("c", "AUDIT", "C")
        counts = g.node_type_counts()
        self.assertEqual(counts["WORK"], 2)
        self.assertEqual(counts["AUDIT"], 1)

    def test_edge_type_counts(self):
        g = GraphStore()
        g.upsert_node("a", "WORK", "A")
        g.upsert_node("b", "WORK", "B")
        g.add_edge("a", "b", "CITES")
        g.add_edge("b", "a", "AUDITS")
        counts = g.edge_type_counts()
        self.assertEqual(counts["CITES"], 1)
        self.assertEqual(counts["AUDITS"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
