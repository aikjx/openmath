# -*- coding: utf-8 -*-
"""验证并列函数应用（sin A -> sin(A)）：正确性、语义结构、散文保护未放开、回归。"""
import json
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
ENG = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
sys.path.insert(0, ENG)

from openmath_sys.parser import parse_text  # noqa: E402
from openmath_sys.fetcher import parse_ocd  # noqa: E402
import openmath_sys.parser as P  # noqa: E402

out = []
failures = 0


def report(desc, ok, detail=""):
    global failures
    if not ok:
        failures += 1
    out.append("%-4s %-44s %s" % ("PASS" if ok else "FAIL", desc[:42], detail))


def parse_ok(raw):
    return parse_text(raw).parse_ok


out.append("=== 1. 并列函数应用（修复目标）===")
for s in ["sin A", "cos A", "tan A", "sec A", "abs x", "ln x", "sqrt 2",
          "sin A cos B", "tan A = sin A / cos A", "sec A = 1/cos A",
          "sin A = - sin(-A)", "cos A = cos(-A)",
          "sin(A + B) = sin A cos B + cos A sin B"]:
    report(s, parse_ok(s))

out.append("")
out.append("=== 2. 语义结构：必须是函数应用而非乘积 ===")
r = parse_text("sin A")
ok = isinstance(r.ast, P.FuncCall) and getattr(r.ast, "name", "") == "sin" \
    and len(r.ast.args) == 1 and isinstance(r.ast.args[0], P.Var)
report("sin A -> FuncCall(sin,[A])", ok, type(r.ast).__name__)

r = parse_text("a b")
ok = isinstance(r.ast, P.BinOp) and getattr(r.ast, "op", "") == "*"
report("a b -> BinOp(*,a,b) 乘积仍成立", ok, type(r.ast).__name__)

r = parse_text("tan A = sin A / cos A")
ok = isinstance(r.ast, P.Relation) and getattr(r.ast, "op", "") == "="
report("tan A = ... -> Relation(=)", ok, type(r.ast).__name__)

r = parse_text("sin A cos B")
ok = isinstance(r.ast, P.BinOp) and r.ast.op == "*" \
    and isinstance(r.ast.left, P.FuncCall) and isinstance(r.ast.right, P.FuncCall)
report("sin A cos B -> sin(A)*cos(B)", ok, type(r.ast).__name__)

out.append("")
out.append("=== 3. 散文保护不得放开（必须仍失败）===")
for s in ["factorial n", "not true", "not false = true",
          "There does not exist a c"]:
    report("仍应失败: " + s, not parse_ok(s))

out.append("")
out.append("=== 4. 回归 ===")
for s in ["2*x + 3 = 7", "x^2 - 5*x + 6 = 0", "a*x^2 + b*x + c = 0",
          "power(2, 3) + sqrt(16)", "gcd(12, 18)", "sin(x) + cos(x)",
          "lcm(4, 6) = 12", "2 ln(x + 1)", "x >= 3", "a != b",
          "x^2 + y^2 = z^2", "(a+b)*(a-b) = a^2 - b^2",
          "for all a | a + 0 = a", "a + 0 = a.", "0.5 + 1 = 1.5"]:
    report(s, parse_ok(s))

out.append("")
out.append("=== 5. 不得影响：内置名作独立变量/作函数用法 ===")
r = parse_text("sin")
report("sin 单独仍是 Var", isinstance(r.ast, P.Var))
r = parse_text("sin(x)")
report("sin(x) 仍是 FuncCall", isinstance(r.ast, P.FuncCall))

# ---- CMP 覆盖率实测 ----
CDS = os.path.join(REPO, "09-数据", "openmath_cds")
cat = json.load(open(os.path.join(CDS, "catalog.json"), encoding="utf-8"))
OPS = ["=", "<=", ">=", "!=", "<", ">"]
tot = eqlike = parsed = 0
seen = set()
for c in cat["cds"]:
    p = os.path.join(CDS, c["name"] + ".ocd")
    if not os.path.exists(p):
        continue
    try:
        syms = parse_ocd(open(p, encoding="utf-8").read())
    except Exception:  # noqa: BLE001
        continue
    for s in syms:
        for prop in s.properties:
            tot += 1
            if prop in seen:
                continue
            if not any(op in prop for op in OPS):
                continue
            if not any(ch.isalpha() for ch in prop):
                continue
            eqlike += 1
            if parse_text(prop).parse_ok:
                parsed += 1
                seen.add(prop)

out.append("")
out.append("=== 6. CMP 可解析率（本地快照实测）===")
out.append("cmp_total=%d  equation_like=%d  parsed=%d  rate=%.4f" % (
    tot, eqlike, parsed, parsed / eqlike if eqlike else 0))
out.append("")
out.append("FAILURES=%d" % failures)

with open(os.path.join(REPO, "99-沙箱", "_test_v7.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("v7 test done, failures=%d" % failures)
