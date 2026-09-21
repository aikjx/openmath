# -*- coding: utf-8 -*-
"""量化剩余未解析 CMP 中各「可扩展模式」的分布，决定是否值得实现。"""
import json
import os
import re

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
ana = json.load(open(os.path.join(REPO, "09-数据", "openmath_4d_analysis.json"),
                    encoding="utf-8"))
samples = ana["unparsed_samples"]["samples"]

REL = r"[<>=!]=?"
# 非关系的散文词（出现即大概率不是可解析方程）
PROSE = re.compile(r"\b(is|are|be|denotes?|represents?|means?|there|such|that|"
                   r"if|then|when|where|however|note|this|usually|implies)\b",
                   re.I)

cats = {
    "链式关系(>=2个关系运算符)": lambda s: len(re.findall(REL, s)) >= 2,
    "  └ 其中不含散文词": lambda s: len(re.findall(REL, s)) >= 2
                                 and not PROSE.search(s),
    "and 连接": lambda s: bool(re.search(r"\band\b", s, re.I)),
    "  └ 其中不含散文词": lambda s: bool(re.search(r"\band\b", s, re.I))
                                 and not PROSE.search(s),
    "绝对值竖线 |..|": lambda s: bool(re.search(r"\|[^|]{1,40}\|", s)),
    "下标 _ 记号": lambda s: bool(re.search(r"[A-Za-z0-9_]\)?_\{?[A-Za-z0-9,]", s))
                             and "_" in s,
    "LaTeX 反斜杠": lambda s: "\\" in s,
    "lambda": lambda s: "lambda" in s.lower(),
    "区间 [1..n]": lambda s: bool(re.search(r"\[\s*\d+\s*\.\.", s)),
    "含散文词(疑非方程)": lambda s: bool(PROSE.search(s)),
    "不含散文词(潜在可解析)": lambda s: not PROSE.search(s),
}

lines = ["未解析样本总数 = %d" % len(samples), "",
         "=== 模式分布（可重叠）==="]
for name, pred in cats.items():
    n = sum(1 for s in samples if pred(s["raw"]))
    lines.append("  %-30s %3d" % (name, n))

pot = [s["raw"] for s in samples if not PROSE.search(s["raw"])]
lines.append("")
lines.append("=== 潜在可解析（不含散文词）样本，共 %d 条 ===" % len(pot))
for s in pot[:25]:
    lines.append("   %r" % s[:150])

with open(os.path.join(REPO, "99-沙箱", "_probe_cap.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("probe cap done")
