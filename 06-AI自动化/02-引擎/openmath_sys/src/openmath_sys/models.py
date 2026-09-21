"""数据模型与权限等级定义。

说明：Authority 枚举描述的是"算法联盟"内部的算法授权分级，
与操作系统权限无关。SUPREME 仅表示允许运行所有 safe=True 的内部算法。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Authority(Enum):
    """算法联盟内部权限等级（逻辑授权，非 OS 提权）。"""
    READ = 1        # 只读：检索、解析、语义链接
    COMPUTE = 2     # 计算：求值、结构分析、一致性检查
    TRANSFORM = 3   # 变换：化简、求解、重写
    SUPREME = 4     # 最高权限：放行所有 safe=True 的内部算法


@dataclass
class Paper:
    paper_id: str
    title: str
    authors: list[str]
    summary: str
    url: str
    pdf_url: str | None = None
    published: str | None = None
    categories: list[str] = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OMSymbol:
    name: str
    cd: str
    description: str = ""
    properties: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MathExpr:
    raw: str
    ast: Any = None
    variables: list[str] = field(default_factory=list)
    # 式中实际出现的函数调用名（小写）。用来把「函数名被当成变量」和
    # 「真正的自由变量」区分开——筛查层据此判断式子结构是否可信。
    functions: list[str] = field(default_factory=list)
    is_equation: bool = False
    parse_ok: bool = False
    error: str | None = None
    # OpenMath CMP 常见全称量词前缀（"for all a,b | a+b=b+a"）。
    # 解析器不理解量词语法，会把 for/all 当变量做隐式乘法而失败，
    # 故 parse_text 会先剥离前缀再解析；被剥离的约束变量记录在此，
    # 以免全称语义被静默丢弃。仅作标注用途，不构成形式化证明。
    quantified: list[str] = field(default_factory=list)


@dataclass
class LogicFacet:
    dimension: str
    title: str
    summary: str
    details: dict = field(default_factory=dict)


@dataclass
class LogicRecord:
    raw: str
    facets: list[LogicFacet] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "facets": [asdict(f) for f in self.facets],
            "conclusions": self.conclusions,
        }


@dataclass
class ExecutionReport:
    algorithm: str
    authority: str
    status: str
    output: Any = None
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
