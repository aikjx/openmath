# -*- coding: utf-8 -*-
"""验证引擎量词前缀修复：正确性 + 回归安全性 + CMP 覆盖率实测。"""
import json
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
ENG = os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src")
sys.path.insert(0, ENG)

from openmath_sys.parser import parse_text  # noqa: E402
from openmath_sys.fetcher import parse_ocd  # noqa: E402

out = []
failures = 0


def check(raw, want_ok=True, want_q=None):
    global failures
    r = parse_text(raw)
    ok = (r.parse_ok == want_ok)
    if want_q is not None and r.quantified != want_q:
        ok = False
    if not ok:
        failures += 1
    out.append("%-4s %-48r ok=%-5s q=%-12s err=%s" % (
        "PASS" if ok else "FAIL", raw[:46], r.parse_ok, r.quantified,
        (r.error or "")[:58]))


out.append("=== 1. 量词前缀（本次修复目标）===")
check("for all a | a + 0 = a", True, ["a"])
check("for all a,b | a + b = b + a", True, ["a", "b"])
check("for all integers a,b | lcm(a,b) = a*b/gcd(a,b)", True, ["a", "b"])
check("for all real x | sin(x)^2 + cos(x)^2 = 1", True, ["x"])
check("For All a | a * 1 = a", True, ["a"])
check("for all a | 0 * a = 0", True, ["a"])

out.append("")
out.append("=== 2. 回归：既有表达式必须仍可解析 ===")
for s in ["2*x + 3 = 7", "x^2 - 5*x + 6 = 0", "a*x^2 + b*x + c = 0",
          "power(2, 3) + sqrt(16)", "gcd(12, 18)", "sin(x) + cos(x)",
          "lcm(4, 6) = 12", "2 ln(x + 1)", "x >= 3", "a != b",
          "x^2 + y^2 = z^2", "(a+b)*(a-b) = a^2 - b^2"]:
    check(s, True)

out.append("")
out.append("=== 3. 非量词不得被误剥离 ===")
check("a + 0 = a", True, [])
check("forall(x)", True, [])
check("a + b = b + a", True, [])

# ---- CMP 覆盖率实测（只读本地快照）----
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
out.append("=== 4. CMP 可解析率（本地快照实测）===")
out.append("cmp_total=%d  equation_like=%d  parsed=%d  rate=%.4f" % (
    tot, eqlike, parsed, parsed / eqlike if eqlike else 0))
out.append("")
out.append("FAILURES=%d" % failures)

with open(os.path.join(REPO, "99-沙箱", "_test_quant.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("test done, failures=%d" % failures)
