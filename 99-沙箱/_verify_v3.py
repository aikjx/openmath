# -*- coding: utf-8 -*-
"""核验第三轮产物：provenance / evidence_level / 覆盖率 / 缺失与回退清单。"""
import json
import os

BASE = r"D:\a10\aikjx\code\my_lib\openmath"


def load(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return json.load(f)


cat = load(os.path.join("09-数据", "openmath_cds", "catalog.json"))
ana = load(os.path.join("09-数据", "openmath_4d_analysis.json"))
idx = load(os.path.join("10-文献与索引", "arxiv_index.json"))

out = []
for name, d in (("catalog", cat), ("analysis", ana), ("arxiv", idx)):
    m = d["meta"]
    out.append(
        f"{name}: ai_assisted={m['provenance']['ai_assisted']} "
        f"evidence_proof={m.get('evidence_level', {}).get('proof')}"
    )

out.append("catalog.coverage = " + json.dumps(cat["meta"]["coverage"], ensure_ascii=False))
out.append("symbols_total = %d" % sum(c["symbol_count"] for c in cat["cds"]))
out.append("cds_total = %d" % len(cat["cds"]))
out.append("missing = %s" % [c["name"] for c in cat["cds"] if c["origin"] is None])
out.append("local_fallback = %s" % [
    c["name"] for c in cat["cds"] if c["origin"] == "local_snapshot"])
out.append("parse_error = %s" % [c["name"] for c in cat["cds"] if c["parse_error"]])
out.append("zero_symbol_cds = %s" % [
    c["name"] for c in cat["cds"] if c["symbol_count"] == 0])
out.append("analysis.coverage = " + json.dumps(
    {k: v for k, v in ana["coverage"].items() if k != "note"}, ensure_ascii=False))
out.append("unparsed_capped = %d" % ana["unparsed_samples"]["count_capped"])
out.append("equations_analyzed = %d" % ana["equations_analyzed"])
out.append("papers = %d" % idx["stats"]["total"])

with open(os.path.join(BASE, "99-沙箱", "_verify_v3.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("verify done")
