"""端到端集成测试：build → stats → search → neighbors → export 全链路。"""
import unittest
import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.store import GraphStore
from openmath_sys.graph.db import save_sqlite, load_sqlite, search_sqlite, stats_sqlite
from openmath_sys.graph.analyze import hubs, verdicts


class TestE2EWorkflow(unittest.TestCase):
    """模拟真实使用链路：建图 → 存 SQLite → 搜索 → 分析 → 加载。"""

    def setUp(self):
        self.tmp_db = tempfile.mktemp(suffix=".db")
        self.tmp_json = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        for p in (self.tmp_db, self.tmp_json):
            if os.path.exists(p):
                os.remove(p)

    def test_full_workflow(self):
        # 1. 建图
        g = GraphStore()
        g.upsert_node("work:test", "WORK", "测试文档", domain="tuft", verdict="confirmed")
        g.upsert_node("theorem:T01", "THEOREM", "T01 任务", number=1)
        g.upsert_node("tool:script.py", "TOOL", "脚本")
        g.add_edge("work:test", "theorem:T01", "CITES", evidence="引用 T01")
        g.add_edge("work:test", "tool:script.py", "USES", evidence="使用脚本")

        # 2. 导出 JSON + SQLite
        g.export(self.tmp_json)
        save_sqlite(g, self.tmp_db)
        self.assertTrue(os.path.exists(self.tmp_json))
        self.assertTrue(os.path.exists(self.tmp_db))

        # 3. 读 stats
        s = stats_sqlite(self.tmp_db)
        self.assertEqual(s["nodes"], 3)
        self.assertEqual(s["edges"], 2)

        # 4. FTS 搜索
        results = search_sqlite(self.tmp_db, "测试", limit=5)
        self.assertTrue(any(r["node_id"] == "work:test" for r in results))

        # 5. 分析
        h = hubs(g, top=1)
        self.assertEqual(h[0][2], "work:test")  # (label, degree, node_id, ntype)
        dist = verdicts(g)
        self.assertEqual(dist.get("confirmed", 0), 1)

        # 6. 从 SQLite 加载
        g2 = load_sqlite(self.tmp_db)
        self.assertEqual(len(g2.nodes), 3)
        self.assertEqual(len(g2.edges), 2)

    def test_neighbors_after_load(self):
        """加载后邻居查询正确。"""
        g = GraphStore()
        g.upsert_node("work:x", "WORK", "X")
        g.upsert_node("work:y", "WORK", "Y")
        g.upsert_node("work:z", "WORK", "Z")
        g.add_edge("work:x", "work:y", "CITES")
        g.add_edge("work:z", "work:x", "EXTENDS")
        save_sqlite(g, self.tmp_db)

        g2 = load_sqlite(self.tmp_db)
        nbrs = g2.neighbors("work:x")
        # work:x 有 2 条边（→y, z→x）
        self.assertEqual(len(nbrs), 2)


if __name__ == "__main__":
    unittest.main()
