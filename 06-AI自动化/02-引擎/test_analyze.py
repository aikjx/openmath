"""analyze.py 智能分析函数测试（risk/hubs/verdicts/refutations）。"""
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.store import GraphStore
from openmath_sys.graph.analyze import risk, hubs, verdicts, refutations


def _make_graph() -> GraphStore:
    """构造测试图谱：3 个 WORK，1 个被 REFUTES，1 个被 AUDITS。"""
    g = GraphStore()
    g.upsert_node("work:a", "WORK", "工作A", verdict="confirmed")
    g.upsert_node("work:b", "WORK", "工作B", verdict="refuted")
    g.upsert_node("work:c", "WORK", "工作C", verdict="mixed")
    g.upsert_node("tool:script", "TOOL", "脚本")
    g.upsert_node("audit:e1", "AUDIT", "勘误#1")
    g.add_edge("work:b", "work:a", "REFUTES", evidence="B 反驳 A")
    g.add_edge("audit:e1", "work:c", "AUDITS", evidence="勘误#1 审计 C")
    g.add_edge("work:a", "tool:script", "USES")
    g.add_edge("work:b", "tool:script", "USES")
    g.add_edge("work:c", "tool:script", "USES")
    return g


class TestRisk(unittest.TestCase):
    """高风险：被 AUDITS 指向的 WORK。"""

    def test_audited_work_is_risk(self):
        g = _make_graph()
        risks = risk(g)
        # 每条 (label, cnt, node_id)
        risk_ids = {r[2] for r in risks}
        self.assertIn("work:c", risk_ids)  # 被 AUDITS

    def test_no_audits_empty(self):
        g = GraphStore()
        g.upsert_node("work:x", "WORK", "X")
        self.assertEqual(risk(g), [])


class TestHubs(unittest.TestCase):
    """hubs：度排行。"""

    def test_tool_is_hub(self):
        g = _make_graph()
        h = hubs(g, top=3)
        # 每条 (label, degree, node_id, ntype)
        top_id = h[0][2]
        self.assertEqual(top_id, "tool:script")  # 3 条 USES，度最高

    def test_hub_limit(self):
        g = _make_graph()
        h = hubs(g, top=2)
        self.assertEqual(len(h), 2)


class TestVerdicts(unittest.TestCase):
    """判决分布。"""

    def test_counts(self):
        g = _make_graph()
        dist = verdicts(g)
        self.assertEqual(dist.get("confirmed", 0), 1)
        self.assertEqual(dist.get("refuted", 0), 1)
        self.assertEqual(dist.get("mixed", 0), 1)


class TestRefutations(unittest.TestCase):
    """被反驳的工作清单。"""

    def test_refuted_list(self):
        g = _make_graph()
        refs = refutations(g)
        # 每条 (label, cnt, node_id)——返回发起 REFUTES 的节点
        ids = {r[2] for r in refs}
        self.assertIn("work:b", ids)  # work:b 发起 REFUTES


if __name__ == "__main__":
    unittest.main()
