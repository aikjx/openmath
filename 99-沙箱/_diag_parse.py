# -*- coding: utf-8 -*-
"""诊断：新引擎 parse_text 为何对全部 CD 的 CMP 解析失败（对内置种子却成功）。"""
import json
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src"))

from openmath_sys.parser import parse_text  # noqa: E402

ana = json.load(
    open(os.path.join(REPO, "09-数据", "openmath_4d_analysis.json"), encoding="utf-8"))
samples = ana["unparsed_samples"]["samples"]

out = ["unparsed_samples = %d" % len(samples), ""]
out.append("=== 失败的 CMP 样本（取前 8 条）===")
for s in samples[:8]:
    rec = parse_text(s["raw"])
    out.append("source: %s" % s["source"])
    out.append("raw: %r" % s["raw"][:160])
    out.append("  parse_ok=%s error=%s" % (rec.parse_ok, getattr(rec, "error", None)))
    out.append("")

out.append("=== 内置种子（对照组）===")
for seed in ["2*x + 3 = 7", "gcd(12, 18)", "lcm(4, 6) = 12", "x^2 - 5*x + 6 = 0"]:
    rec = parse_text(seed)
    out.append("seed=%r parse_ok=%s error=%s"
               % (seed, rec.parse_ok, getattr(rec, "error", None)))

with open(os.path.join(REPO, "99-沙箱", "_diag_parse.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("diag done")
