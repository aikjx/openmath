# -*- coding: utf-8 -*-
"""探测「未覆盖」失败样例的真实报错，区分【缺陷】与【能力上限】。"""
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎",
                                "openmath_sys", "src"))
from openmath_sys.parser import parse_text  # noqa: E402

CASES = [
    # 疑似应该可解析
    "sin(A + B) = sin A cos B + cos A sin B",
    "sin A = - sin(-A)",
    "cos A = cos(-A)",
    "tan A = sin A / cos A",
    "sec A = 1/cos A",
    "not true = false",
    "not false = true",
    # 已知语法限制
    "-pi < Im ln x <= pi",
    "a + 0 = a.",
    "x^2 = 4,",
    "outerproduct(a,b)_{i,j} = a_i * b_j",
    "factorial n = product [1..n]",
    # 对照：已知可解析
    "sin(x) + cos(x) = 1",
    "2*x + 3 = 7",
]

lines = ["%-52s %-6s %s" % ("CASE", "OK", "ERROR")]
for c in CASES:
    r = parse_text(c)
    lines.append("%-52r %-6s %s" % (c[:50], r.parse_ok, (r.error or "")[:80]))

with open(os.path.join(REPO, "99-沙箱", "_probe_fail.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("probe done")
