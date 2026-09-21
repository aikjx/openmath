# -*- coding: utf-8 -*-
"""核验第四轮产物，并归类仍然解析失败的 CMP 反例（供引擎侧修复定位）。"""
import json
import os
import re

BASE = r"D:\a10\aikjx\code\my_lib\openmath"
QUANT_RE = re.compile(r"^\s*for\s+all\s+[^|]*\|\s*", re.I)

with open(os.path.join(BASE, "09-数据", "openmath_4d_analysis.json"), encoding="utf-8") as f:
    ana = json.load(f)
with open(os.path.join(BASE, "09-数据", "openmath_cds", "catalog.json"), encoding="utf-8") as f:
    cat = json.load(f)

cov = ana["coverage"]
out = [
    "catalog.coverage = " + json.dumps(cat["meta"]["coverage"], ensure_ascii=False),
    "symbols_total = %d" % sum(c["symbol_count"] for c in cat["cds"]),
    "analysis.coverage = " + json.dumps(
        {k: v for k, v in cov.items() if k != "note"}, ensure_ascii=False),
    "equations_analyzed = %d" % ana["equations_analyzed"],
]

samples = ana["unparsed_samples"]["samples"]
out.append("unparsed_recorded = %d (cap %d)"
           % (ana["unparsed_samples"]["count_capped"], ana["unparsed_samples"]["cap"]))

# 归类残余失败
buckets = {
    "量词前缀未匹配(其他量词/写法)": lambda s: bool(re.match(r"^\s*(for|exists|there)\b", s, re.I)),
    "存在量词/there does not exist": lambda s: "does not exist" in s.lower(),
    "such that 从句": lambda s: "such that" in s.lower(),
    "自然语言尾注(Note that/implies)": lambda s: bool(
        re.search(r"\b(note that|implies|is an integer|is a )", s, re.I)),
    "仍带 for all 前缀": lambda s: bool(QUANT_RE.match(s)),
    "其他": lambda s: True,
}
counts = {k: 0 for k in buckets}
for s in samples:
    raw = s["raw"]
    for k, pred in buckets.items():
        if k == "其他":
            continue
        if pred(raw):
            counts[k] += 1
            break
    else:
        counts["其他"] += 1
# 「其他」= 未被任何前置桶命中
counts["其他"] = sum(
    1 for s in samples
    if not any(pred(s["raw"]) for k, pred in buckets.items() if k != "其他")
)

out.append("")
out.append("=== 残余失败归类（可重叠，按首个命中计）===")
for k, v in counts.items():
    out.append("  %s: %d" % (k, v))

out.append("")
out.append("=== 其他类样本（前 10 条，最可能是引擎真实缺陷）===")
others = [s for s in samples
          if not any(pred(s["raw"]) for k, pred in buckets.items() if k != "其他")]
for s in others[:10]:
    out.append("  [%s] %r" % (s["source"], s["raw"][:110]))

with open(os.path.join(BASE, "99-沙箱", "_verify_v4.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("verify v4 done")
