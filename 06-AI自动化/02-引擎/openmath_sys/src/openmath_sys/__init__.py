"""OpenMath 综合处理系统 —— 包入口。

模块组成：
  fetcher       论文与 OpenMath 内容字典检索
  parser        方程词法/语法分析与求值
  logic_framework 四维逻辑处理框架
  scheduler     算法联盟调度器（含最高权限处理模式）
  structure     有限群与有限链复形的结构计算
  theoryforge   有限对象库上的关系发现与两级反例搜索
  sequences     整数序列上的递推/超几何闭式/增长率发现（含特征根对账）
  audit         独立审计：用不同算法重算本仓库自己算出的每个数字
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
from .audit import run_audit, SCOPE_NOTE as AUDIT_SCOPE_NOTE
# 注意命名冲突：sequences 与 theoryforge **都有** discover_linear。
# 若把 sequences 的 discover_linear 扁平导入进来，会静默遮蔽 theoryforge 的那个
# （两者语义完全不同：一个是有限对象不变量的线性关系，一个是整数序列的递推）。
# 所以这里**不**扁平导入任何与 theoryforge 重名的函数，改用模块引用。
from . import sequences as seq
from .sequences import (
    build_sequences, analyze_sequence, analyze_all,
    characteristic_polynomial, polynomial_roots,
    growth_from_recurrence, reconcile_growth,
    discover_polynomial_recurrence, meta_test_falsification, transform_closure,
    mod_primes, rational_reconstruct,
    KNOWN_RECURRENCES, EXPECTED_NEGATIVE, KNOWN_PRECURENCES,
    P_RECURSIVE_NEGATIVE,
    SCOPE_NOTE as SEQ_SCOPE_NOTE, EVIDENCE_NOTE as SEQ_EVIDENCE_NOTE,
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
    "run_audit", "AUDIT_SCOPE_NOTE",
    # 序列侧：重名函数一律走 seq.<name>，不扁平导出，避免遮蔽 theoryforge
    "seq", "build_sequences", "analyze_sequence", "analyze_all",
    "characteristic_polynomial", "polynomial_roots", "growth_from_recurrence",
    "reconcile_growth", "discover_polynomial_recurrence",
    "meta_test_falsification", "transform_closure",
    "mod_primes", "rational_reconstruct",
    "KNOWN_RECURRENCES", "EXPECTED_NEGATIVE", "KNOWN_PRECURENCES",
    "P_RECURSIVE_NEGATIVE",
    "SEQ_SCOPE_NOTE", "SEQ_EVIDENCE_NOTE",
]
