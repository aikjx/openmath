"""OpenMath 综合处理系统 —— 包入口。

模块组成：
  fetcher       论文与 OpenMath 内容字典检索
  parser        方程词法/语法分析与求值
  logic_framework 四维逻辑处理框架
  scheduler     算法联盟调度器（含最高权限处理模式）
  knowledge     符号语义与推理记录知识库
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
from .system import OpenMathProcessor

__all__ = [
    "Authority", "Paper", "OMSymbol", "MathExpr", "LogicFacet", "LogicRecord",
    "ExecutionReport", "parse_text", "FourDimLogicEngine", "fetch_arxiv",
    "fetch_openmath_cd", "rank_papers", "AlgorithmAlliance", "Algorithm",
    "build_default_alliance", "KnowledgeBase", "OpenMathProcessor",
]
