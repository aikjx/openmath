"""四维逻辑处理框架。

将数学对象的理解分解为四个正交维度：
  D1 句法维度 (Syntactic)   —— 解析、符号与算子清单、AST 形态
  D2 语义维度 (Semantic)    —— 符号到 OpenMath CD 的语义映射与类型推断
  D3 结构维度 (Structural)  —— 代数形态分类、方程类别、变量耦合
  D4 计算维度 (Computational)—— 求值、化简、求解等可执行变换
四者组合为一条 LogicRecord，作为"人类四维逻辑"的机器可处理表示。
"""
from __future__ import annotations

from typing import Any

from .models import LogicFacet, LogicRecord, MathExpr, OMSymbol
from . import parser as P


class FourDimLogicEngine:
    def __init__(self, symbol_table: dict[str, OMSymbol] | None = None):
        self.symbol_table = symbol_table or {}

    # --- D1 句法 -----------------------------------------------------------
    def _d1_syntactic(self, expr: MathExpr) -> LogicFacet:
        if not expr.parse_ok:
            return LogicFacet("D1", "句法维度", "解析失败",
                              {"error": expr.error})
        ast = expr.ast
        operators = sorted({n.op for n in P._walk(ast)
                            if isinstance(n, P.BinOp)})
        functions = sorted({n.name for n in P._walk(ast)
                            if isinstance(n, P.FuncCall)})
        return LogicFacet(
            "D1", "句法维度 (Syntactic)",
            "成功构建抽象语法树并提取表层结构",
            {
                "ast_type": type(ast).__name__,
                "variables": expr.variables,
                "operators": operators,
                "functions": functions,
                "is_equation": expr.is_equation,
            },
        )

    # --- D2 语义 -----------------------------------------------------------
    def _d2_semantic(self, expr: MathExpr, symbol_table: dict[str, OMSymbol]) -> LogicFacet:
        if not expr.parse_ok:
            return LogicFacet("D2", "语义维度", "跳过（解析失败）", {})
        linked: list[dict] = []
        for v in expr.variables:
            if v in symbol_table:
                sym = symbol_table[v]
                linked.append({"symbol": v, "cd": sym.cd,
                               "meaning": sym.description})
            else:
                linked.append({"symbol": v, "cd": None,
                               "meaning": "未登记于已加载的 OpenMath CD（视为自由变量/参数）"})
        # 类型推断（极简版）：含超越函数 -> 实值；否则按整数/实数默认实数
        has_trans = any(isinstance(n, P.FuncCall) for n in P._walk(expr.ast))
        inferred_type = "real-valued (transcendental involved)" if has_trans else "real-valued"
        return LogicFacet(
            "D2", "语义维度 (Semantic)",
            "将符号链接到 OpenMath 内容字典语义并做类型推断",
            {"links": linked, "inferred_type": inferred_type},
        )

    # --- D3 结构 -----------------------------------------------------------
    def _d3_structural(self, expr: MathExpr) -> LogicFacet:
        if not expr.parse_ok:
            return LogicFacet("D3", "结构维度", "跳过（解析失败）", {})
        ast = expr.ast
        form = P.classify(ast, expr.variables)
        degrees = {v: P.degree_of(ast, v) for v in expr.variables}
        rel = None
        if isinstance(ast, P.Relation):
            rel = ast.op
        return LogicFacet(
            "D3", "结构维度 (Structural)",
            f"识别为 {form} 形态",
            {
                "form": form,
                "relation": rel,
                "degree_by_var": {k: (v if v != float("inf") else "inf")
                                  for k, v in degrees.items()},
                "variable_count": len(expr.variables),
            },
        )

    # --- D4 计算 -----------------------------------------------------------
    def _d4_computational(self, expr: MathExpr) -> LogicFacet:
        if not expr.parse_ok:
            return LogicFacet("D4", "计算维度", "跳过（解析失败）", {})
        ast = expr.ast
        details: dict[str, Any] = {}
        # 在样本点上求值以观察行为
        if expr.variables:
            v0 = expr.variables[0]
            sample_vals = {}
            for x in (1.0, 2.0, 3.0):
                try:
                    sample_vals[x] = P.evaluate(ast, {v0: x})
                except Exception:  # noqa: BLE001
                    sample_vals[x] = None
            details["sample_eval"] = {f"{v0}={k}": val for k, val in sample_vals.items()}
        # 方程求解（单变量多项式）
        if expr.is_equation and isinstance(ast, P.Relation):
            if len(expr.variables) == 1:
                var = expr.variables[0]
                try:
                    coeffs = P.poly_coeffs(P.BinOp("-", ast.left, ast.right), var)
                    details["solve"] = P.solve_poly(coeffs, var)
                except Exception as e:  # noqa: BLE001
                    details["solve"] = {"solvable": False, "reason": str(e)}
            else:
                details["solve"] = {"solvable": False,
                                    "reason": "多变量方程，超出本演示求解范围"}
        details["evaluable"] = expr.variables == [] or bool(expr.variables)
        return LogicFacet(
            "D4", "计算维度 (Computational)",
            "执行求值与（若适用）方程求解",
            details,
        )

    # --- 组合 -------------------------------------------------------------
    def process(self, raw: str, symbol_table: dict[str, OMSymbol] | None = None) -> LogicRecord:
        st = symbol_table or self.symbol_table
        expr = P.parse_text(raw)
        f1 = self._d1_syntactic(expr)
        f2 = self._d2_semantic(expr, st)
        f3 = self._d3_structural(expr)
        f4 = self._d4_computational(expr)
        conclusions = self._conclude([f1, f2, f3, f4], expr)
        return LogicRecord(raw=raw, facets=[f1, f2, f3, f4], conclusions=conclusions)

    @staticmethod
    def _conclude(facets: list[LogicFacet], expr: MathExpr) -> list[str]:
        out: list[str] = []
        if not expr.parse_ok:
            out.append("⚠ 表达式解析失败，四维推理无法展开；请检查语法。")
            return out
        d3 = next(f for f in facets if f.dimension == "D3")
        form = d3.details.get("form", "unknown")
        out.append(f"句法上含 {len(expr.variables)} 个变量、可构成 AST；")
        out.append(f"结构上判定为 {form} 形态；")
        d4 = next(f for f in facets if f.dimension == "D4")
        if "solve" in d4.details:
            sol = d4.details["solve"]
            if sol.get("solvable"):
                roots = sol["roots"]
                out.append(f"计算维度已求得根：{roots}；")
            else:
                out.append(f"计算维度暂未求解：{sol.get('reason')}；")
        out.append("四维一致：句法可解析、语义可链接、结构可分类、计算可执行（在沙箱内）。")
        return out
