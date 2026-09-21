# -*- coding: utf-8 -*-
"""探测隐式乘法：两个记号之间有空格时是否插入乘号。"""
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎",
                                "openmath_sys", "src"))
from openmath_sys.parser import (  # noqa: E402
    parse_text, scan_tokens, split_letter_runs, insert_implicit_mul)

CASES = [
    "a b", "a b = c", "2 x", "x y", "sin A", "a*b", "a b c",
    "2*x", "a  b", "factorial n", "not true",
]

lines = ["=== 解析结果 ==="]
for c in CASES:
    r = parse_text(c)
    lines.append("%-16r ok=%-5s err=%s" % (c, r.parse_ok, (r.error or "")[:70]))

lines.append("")
lines.append("=== 记号流（含隐式乘插入后）===")
for c in ["a b", "sin A", "2 x", "a*b"]:
    toks, ws = scan_tokens(c)
    toks2, ws2 = split_letter_runs(toks, ws, context_letters=None)
    toks3 = insert_implicit_mul(toks2, ws2)
    lines.append("%-10r -> %s" % (c, toks3))

with open(os.path.join(REPO, "99-沙箱", "_probe_mul.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("probe done")
