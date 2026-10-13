"""csv_importer.py 企业业务数据导入测试。"""
import unittest
import sys, os, tempfile, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.store import GraphStore
from openmath_sys.graph.csv_importer import import_nodes_csv, import_edges_csv, auto_import


def _write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


class TestImportNodes(unittest.TestCase):
    """节点表导入。"""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".csv")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_import_business_nodes(self):
        """CRM 场景：客户/联系人/产品。"""
        _write_csv(self.tmp, [
            {"node_id": "cust:001", "ntype": "CUSTOMER", "label": "客户A", "industry": "金融"},
            {"node_id": "cust:002", "ntype": "CUSTOMER", "label": "客户B", "industry": "制造"},
            {"node_id": "prod:101", "ntype": "PRODUCT", "label": "产品X", "price": "999"},
        ], ["node_id", "ntype", "label", "industry", "price"])
        g = GraphStore()
        n = import_nodes_csv(g, self.tmp)
        self.assertEqual(n, 3)
        self.assertEqual(len(g.nodes), 3)
        self.assertEqual(g.nodes["cust:001"].attrs["industry"], "金融")
        self.assertEqual(len(g.list_nodes_by_type("CUSTOMER")), 2)

    def test_auto_import_nodes(self):
        _write_csv(self.tmp, [
            {"node_id": "p:1", "ntype": "PERSON", "label": "张三"},
        ], ["node_id", "ntype", "label"])
        g = GraphStore()
        n = auto_import(g, self.tmp)
        self.assertEqual(n, 1)
        self.assertIn("p:1", g.nodes)


class TestImportEdges(unittest.TestCase):
    """边表导入（自动建端点节点）。"""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".csv")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_import_relationships(self):
        """销售场景：客户-购买-产品。"""
        _write_csv(self.tmp, [
            {"edge_src": "cust:001", "edge_dst": "prod:101", "etype": "PURCHASES", "evidence": "2024 订单"},
            {"edge_src": "cust:002", "edge_dst": "prod:101", "etype": "PURCHASES", "evidence": "2024 订单"},
        ], ["edge_src", "edge_dst", "etype", "evidence"])
        g = GraphStore()
        n = import_edges_csv(g, self.tmp)
        self.assertEqual(n, 2)
        self.assertEqual(len(g.edges), 2)
        # 端点自动建
        self.assertIn("cust:001", g.nodes)
        self.assertIn("prod:101", g.nodes)

    def test_auto_import_edges(self):
        _write_csv(self.tmp, [
            {"edge_src": "a", "edge_dst": "b", "etype": "RELATES_TO"},
        ], ["edge_src", "edge_dst", "etype"])
        g = GraphStore()
        n = auto_import(g, self.tmp)
        self.assertEqual(n, 1)


class TestUniversalQuery(unittest.TestCase):
    """通用业务查询（list_nodes_by_type / find_nodes_by_attr）。"""

    def test_filter_by_attr(self):
        g = GraphStore()
        g.upsert_node("cust:001", "CUSTOMER", "客户A", industry="金融")
        g.upsert_node("cust:002", "CUSTOMER", "客户B", industry="制造")
        g.upsert_node("cust:003", "CUSTOMER", "客户C", industry="金融")
        fin = g.find_nodes_by_attr("industry", "金融")
        self.assertEqual(len(fin), 2)


if __name__ == "__main__":
    unittest.main()
