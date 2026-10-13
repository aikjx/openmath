"""db.py SQLite 持久化 + FTS5 测试。"""
import unittest
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.store import GraphStore
from openmath_sys.graph.db import save_sqlite, load_sqlite, stats_sqlite, search_sqlite


class TestSQLiteRoundtrip(unittest.TestCase):
    """save → load 往返一致性。"""

    def setUp(self):
        self.g = GraphStore()
        self.g.upsert_node("work:demo", "WORK", "演示文档", domain="tuft")
        self.g.upsert_node("theorem:T01", "THEOREM", "T01 任务", number=1)
        self.g.upsert_node("audit:errata#1", "AUDIT", "勘误#1")
        self.g.add_edge("work:demo", "theorem:T01", "CITES", evidence="demo 引用 T01")
        self.g.add_edge("work:demo", "audit:errata#1", "AUDITS", evidence="demo 被勘误#1")
        self.tmp = tempfile.mktemp(suffix=".db")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_save_load_roundtrip(self):
        save_sqlite(self.g, self.tmp)
        g2 = load_sqlite(self.tmp)
        self.assertEqual(len(g2.nodes), len(self.g.nodes))
        self.assertEqual(len(g2.edges), len(self.g.edges))
        self.assertIn("work:demo", g2.nodes)
        self.assertEqual(g2.nodes["work:demo"].label, "演示文档")
        self.assertEqual(g2.nodes["work:demo"].attrs.get("domain"), "tuft")

    def test_stats_sqlite(self):
        save_sqlite(self.g, self.tmp)
        s = stats_sqlite(self.tmp)
        self.assertEqual(s["nodes"], 3)
        self.assertEqual(s["edges"], 2)
        self.assertEqual(s["by_node_type"]["WORK"], 1)
        self.assertEqual(s["by_edge_type"]["CITES"], 1)

    def test_fts5_search(self):
        """FTS5 全文搜索（回退 LIKE）。"""
        save_sqlite(self.g, self.tmp)
        # 搜索中文标签
        results = search_sqlite(self.tmp, "演示", limit=5)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["ntype"], "WORK")
        # 搜索英文标签
        results2 = search_sqlite(self.tmp, "T01", limit=5)
        self.assertTrue(any(r["ntype"] == "THEOREM" for r in results2))

    def test_search_no_db(self):
        """DB 不存在时返回空列表，不报错。"""
        self.assertEqual(search_sqlite("nonexistent.db", "kw"), [])


if __name__ == "__main__":
    unittest.main()
