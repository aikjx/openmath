# -*- coding: utf-8 -*-
"""调试：连写 `sin A cos B` 的记号流与报错。"""
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎",
                                "openmath_sys", "src"))
from openmath_sys.parser import (  # noqa: E402
    parse_text, scan_tokens, split_letter_runs, insert_implicit_mul)

lines = []
for s in ["sin A cos B", "sin A", "a b c", "sin A * cos B"]:
    toks, ws = scan_tokens(s)
    toks2, ws2 = split_letter_runs(toks, ws, None)
    toks3 = insert_implicit_mul(toks2, ws2)
    r = parse_text(s)
    lines.append("raw   = %r" % s)
    lines.append("tokens= %s" % (toks3,))
    lines.append("ok=%s err=%s" % (r.parse_ok, (r.error or "")[:90]))
    lines.append("")

with open(os.path.join(REPO, "99-沙箱", "_dbg.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("dbg done")
