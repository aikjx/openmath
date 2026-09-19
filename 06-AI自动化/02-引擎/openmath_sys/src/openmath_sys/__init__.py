"""OpenMath 综合处理系统 —— 包入口。

模块组成：
  fetcher       论文与 OpenMath 内容字典检索
  parser        方程词法/语法分析与求值
  logic_framework 四维逻辑处理框架
  scheduler     算法联盟调度器（含最高权限处理模式）
  structure     有限群与有限链复形的结构计算
  theoryforge   有限对象库上的关系发现与两级反例搜索
  system        总编排器
"""
from .models import (
    Authority, Paper, OMSymbol, MathExpr, LogicFacet, LogicRecord, ExecutionReport,
)
from .parser import parse_text
from .logic_framework import FourDimLogicEngine
from .fetcher import fetch_arxiv, fetch_openmath_cd, rank_papers
from .scheduler import AlgorithmAlliance, Algorithm, build_default_alliance
from .knowledge import KnowledgeBase
from .numbertheory import rad, abc_quality, goldbach_partitions, sieve_is_prime
from .structure import (
    ChainComplex, homology_summary, analyze_group, cyclic_additive_group,
    dihedral_group, symmetric_group, STANDARD_COMPLEXES, STANDARD_GROUPS,
)
from .theoryforge import (
    build_sites, discover_linear, discover_monomial, discover_inequality,
    pareto_filter_inequalities, recognize_known, stress_test, theory_net,
    forge_all, KNOWN_RELATIONS, DEFINITIONAL_LINEAR,
)
from .system import OpenMathProcessor

__all__ = [
    "Authority", "Paper", "OMSymbol", "MathExpr", "LogicFacet", "LogicRecord",
    "ExecutionReport", "parse_text", "FourDimLogicEngine", "fetch_arxiv",
    "fetch_openmath_cd", "rank_papers", "AlgorithmAlliance", "Algorithm",
    "build_default_alliance", "KnowledgeBase", "OpenMathProcessor",
    "rad", "abc_quality", "goldbach_partitions", "sieve_is_prime",
    "ChainComplex", "homology_summary", "analyze_group", "cyclic_additive_group",
    "dihedral_group", "symmetric_group", "STANDARD_COMPLEXES", "STANDARD_GROUPS",
    "build_sites", "discover_linear", "discover_monomial", "discover_inequality",
    "pareto_filter_inequalities", "recognize_known", "stress_test", "theory_net",
    "forge_all", "KNOWN_RELATIONS", "DEFINITIONAL_LINEAR",
]
