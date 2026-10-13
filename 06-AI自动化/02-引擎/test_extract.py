"""extract.py 抽取规则测试（正则 + 域分类 + 双向链接）。"""
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph.extract import (
    WIKI_RE, TASK_RE, CLAIM_RE, ERRATA_RE, VERSION_RE,
    classify_domain, version_bucket,
)


class TestRegexPatterns(unittest.TestCase):
    """正则规则硬不变量。"""

    def test_task_number_extraction(self):
        """T01~T99 任务编号抽取。"""
        self.assertEqual(set(TASK_RE.findall("T01 任务描述 T09 第二轮")), {"01", "09"})
        self.assertEqual(set(TASK_RE.findall("没有任务编号")), set())

    def test_claim_number_extraction(self):
        """J01~J99 论断编号抽取。"""
        self.assertEqual(set(CLAIM_RE.findall("J12 论断 J42 反例")), {"12", "42"})

    def test_errata_extraction(self):
        """勘误 #28~#34 编号抽取。"""
        self.assertEqual(set(ERRATA_RE.findall("勘误#28 勘误 #29 勘误#34")), {"28", "29", "34"})

    def test_version_extraction(self):
        """v1.0 / v2.3 版本号抽取。"""
        m = VERSION_RE.search("v1.0 集成说明")
        self.assertEqual((m.group(1), m.group(2)), ("1", "0"))
        m2 = VERSION_RE.search("v2.3 优化报告")
        self.assertEqual((m2.group(1), m2.group(2)), ("2", "3"))

    def test_wiki_link_extraction(self):
        """[[目标]] 和 [[目标|别名]] 双向链接。"""
        # 基础形式
        matches = WIKI_RE.findall("见 [[goldbach_master]] 上文")
        self.assertEqual(matches, [("goldbach_master", "")])
        # 带别名
        matches = WIKI_RE.findall("见 [[goldbach_master|主文件]] 上文")
        self.assertEqual(matches, [("goldbach_master", "主文件")])
        # 多个
        matches = WIKI_RE.findall("关联 [[file_a]] 和 [[file_b|别名]]")
        self.assertEqual(matches, [("file_a", ""), ("file_b", "别名")])


class TestDomainClassification(unittest.TestCase):
    """域分类硬不变量。"""

    def test_tuft_domain(self):
        self.assertEqual(classify_domain("全域统一场论_v1.md"), "tuft")
        self.assertEqual(classify_domain("分支B_引力.md"), "tuft")

    def test_coalition_domain(self):
        self.assertEqual(classify_domain("算法联盟审计_v1.md"), "coalition")

    def test_goldbach_domain(self):
        self.assertEqual(classify_domain("pwcv_goldbach_master.md"), "goldbach")

    def test_misc_domain(self):
        self.assertEqual(classify_domain("random_notes.md"), "misc")


class TestVersionBucket(unittest.TestCase):
    """版本文档分桶。"""

    def test_changelog_bucket(self):
        self.assertEqual(version_bucket("新功能台账_v1.md"), "changelog")

    def test_integration_bucket(self):
        self.assertEqual(version_bucket("集成说明_v2.md"), "integration")

    def test_optimization_bucket(self):
        self.assertEqual(version_bucket("优化报告_v1.md"), "optimization")

    def test_diagnosis_bucket(self):
        self.assertEqual(version_bucket("诊断裁决_v1.md"), "diagnosis")

    def test_unknown_bucket(self):
        self.assertIsNone(version_bucket("普通文档_v1.md"))


if __name__ == "__main__":
    unittest.main()
