"""算法联盟调度器（含最高权限处理模式）。

核心安全约束：
- 每个算法登记时声明 required_level（所需权限等级）与 safe 标志。
- dispatch 仅执行 required_level <= 当前模式 且 safe=True 的算法。
- 任何会执行破坏性文件操作或外部网络写出的算法必须 safe=False，
  在任意模式下都被拒绝，从设计上杜绝"越权"。
- SUPREME（最高权限）只是逻辑授权上限，绝不映射为操作系统 root/admin。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .models import Authority, ExecutionReport, LogicRecord


@dataclass
class Algorithm:
    name: str
    fn: Callable[[LogicRecord], object]
    required_level: Authority
    description: str
    safe: bool = True  # 默认安全；破坏性/外部写出必须为 False


class AlgorithmAlliance:
    def __init__(self) -> None:
        self._registry: dict[str, Algorithm] = {}

    def register(self, algo: Algorithm) -> None:
        self._registry[algo.name] = algo

    def list_algorithms(self) -> list[dict]:
        return [{"name": a.name, "level": a.required_level.name,
                 "safe": a.safe, "desc": a.description}
                for a in self._registry.values()]

    def dispatch(self, record: LogicRecord, mode: Authority = Authority.SUPREME) -> list[ExecutionReport]:
        reports: list[ExecutionReport] = []
        for algo in self._registry.values():
            # 权限门：模式等级必须 >= 算法所需等级
            if algo.required_level.value > mode.value:
                reports.append(ExecutionReport(
                    algo.name, mode.name, "skipped",
                    note=f"所需权限 {algo.required_level.name} 高于当前模式 {mode.name}"))
                continue
            # 安全门：任何 safe=False 的算法一律拒绝
            if not algo.safe:
                reports.append(ExecutionReport(
                    algo.name, mode.name, "refused",
                    note="算法被标记为不安全（破坏性/外部写出），按设计拒绝执行"))
                continue
            try:
                out = algo.fn(record)
                reports.append(ExecutionReport(
                    algo.name, mode.name, "ok", output=out))
            except Exception as e:  # noqa: BLE001
                reports.append(ExecutionReport(
                    algo.name, mode.name, "error", note=str(e)))
        return reports


# ---------------------------------------------------------------------------
# 预置算法（均为 safe=True 的内部算法）
# ---------------------------------------------------------------------------
def build_default_alliance() -> AlgorithmAlliance:
    a = AlgorithmAlliance()

    def structural_classifier(rec: LogicRecord):
        d3 = next((f for f in rec.facets if f.dimension == "D3"), None)
        return d3.details if d3 else None

    def equation_solver(rec: LogicRecord):
        d4 = next((f for f in rec.facets if f.dimension == "D4"), None)
        return d4.details.get("solve") if d4 else None

    def evaluator(rec: LogicRecord):
        d4 = next((f for f in rec.facets if f.dimension == "D4"), None)
        return d4.details.get("sample_eval") if d4 else None

    def semantic_linker(rec: LogicRecord):
        d2 = next((f for f in rec.facets if f.dimension == "D2"), None)
        return d2.details.get("links") if d2 else None

    def consistency_checker(rec: LogicRecord):
        ok = all(f.details for f in rec.facets)
        return {"consistent": ok, "conclusions": rec.conclusions}

    def report_writer(rec: LogicRecord):
        return {"raw": rec.raw, "conclusions": rec.conclusions}

    a.register(Algorithm("semantic_linker", semantic_linker, Authority.READ,
                          "将符号链接到 OpenMath CD 语义", safe=True))
    a.register(Algorithm("structural_classifier", structural_classifier, Authority.COMPUTE,
                          "结构形态分类", safe=True))
    a.register(Algorithm("evaluator", evaluator, Authority.COMPUTE,
                          "样本点求值", safe=True))
    a.register(Algorithm("consistency_checker", consistency_checker, Authority.COMPUTE,
                          "四维一致性检查", safe=True))
    a.register(Algorithm("equation_solver", equation_solver, Authority.TRANSFORM,
                          "方程求解（单变量多项式）", safe=True))
    a.register(Algorithm("report_writer", report_writer, Authority.READ,
                          "汇总推理结论", safe=True))
    return a
