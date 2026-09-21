# -*- coding: utf-8 -*-
"""分析未解析 CMP 反例，精确定位失败模式，判断哪些可安全修复。"""
import json
import os
import re

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
ana = json.load(open(os.path.join(REPO, "09-数据", "openmath_4d_analysis.json"),
                    encoding="utf-8"))
samples = ana["unparsed_samples"]["samples"]

CATS = [
    ("尾随句点/逗号", lambda s: s.rstrip().endswith((".", ",", ";"))),
    ("量词变体(for all无| / for every / there exists)",
     lambda s: bool(re.match(r"^\s*(for\s+(all|every|any|each)\b|there\s+exists?\b)",
                             s, re.I))),
    ("标准量词前缀但仍有|残留",
     lambda s: bool(re.match(r"^\s*for\s+all\b", s, re.I)) and "|" in s),
    ("含 LaTeX 反斜杠", lambda s: "\\" in s),
    ("含绝对值竖线", lambda s: bool(re.search(r"\|[^|]+\|", s))),
    ("含 lambda", lambda s: "lambda" in s.lower()),
    ("含下标 a_1", lambda s: bool(re.search(r"[A-Za-z]_\d", s))),
    ("含区间 [1..n]", lambda s: bool(re.search(r"\[\s*\d+\s*\.\.", s))),
    ("含逻辑/条件连接词", lambda s: bool(re.search(
        r"\b(and|iff|if and only if|such that|implies|then|where)\b", s, re.I))),
    ("含系动词/散文", lambda s: bool(re.search(
        r"\b(is|are|be|denotes?|represents?|means?)\b", s, re.I))),
    ("含 HTML/OM 标签残留", lambda s: bool(re.search(r"</?[A-Za-z]+>", s))),
    ("多个句子(句号>=2)", lambda s: s.count(".") >= 2),
    ("前导散文后接方程(如 the X of ...)",
     lambda s: bool(re.match(r"^\s*(the|if|when|given|let|suppose)\b", s, re.I))),
]

counts = {}
examples = {}
for s in samples:
    raw = s["raw"]
    for name, pred in CATS:
        try:
            hit = pred(raw)
        except Exception:  # noqa: BLE001
            hit = False
        if hit:
            counts[name] = counts.get(name, 0) + 1
            examples.setdefault(name, []).append(raw)

uncovered = [s["raw"] for s in samples
             if not any(p(s["raw"]) for _n, p in CATS)]

lines = ["总计未解析样本 = %d" % len(samples), ""]
lines.append("=== 失败模式统计（可重叠）===")
for name, _ in CATS:
    lines.append("  %-44s %3d" % (name, counts.get(name, 0)))
lines.append("")
lines.append("未被任何模式覆盖 = %d" % len(uncovered))

lines.append("")
lines.append("=== 各类样例（每类最多 3 条）===")
for name, _ in CATS:
    ex = examples.get(name, [])
    if not ex:
        continue
    lines.append("")
    lines.append("[%s]  n=%d" % (name, len(ex)))
    for e in ex[:3]:
        lines.append("   %r" % e[:150])

lines.append("")
lines.append("=== 未覆盖样例（最多 12 条）===")
for e in uncovered[:12]:
    lines.append("   %r" % e[:150])

with open(os.path.join(REPO, "99-沙箱", "_analyze_fail.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("analyze done")
