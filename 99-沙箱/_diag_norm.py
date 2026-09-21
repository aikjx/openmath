# -*- coding: utf-8 -*-
"""量化：剥离 OpenMath CMP 量词前缀（for all ... |）对 CMP 可解析率的影响。

只读本地 .ocd 快照，不联网。
"""
import json
import os
import re
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src"))

from openmath_sys.parser import parse_text  # noqa: E402
from openmath_sys.fetcher import parse_ocd  # noqa: E402

CDS = os.path.join(REPO, "09-数据", "openmath_cds")
OPS = ["=", "<=", ">=", "!=", "<", ">"]

cat = json.load(open(os.path.join(CDS, "catalog.json"), encoding="utf-8"))
names = [c["name"] for c in cat["cds"]]

QUANT_RE = re.compile(r"^\s*for\s+all\s+[^|]*\|\s*", re.I)


def norm(raw: str) -> str:
    m = QUANT_RE.match(raw)
    return raw[m.end():] if m else raw


def load_props():
    for n in names:
        p = os.path.join(CDS, n + ".ocd")
        if not os.path.exists(p):
            continue
        try:
            syms = parse_ocd(open(p, encoding="utf-8").read())
        except Exception:  # noqa: BLE001
            continue
        for s in syms:
            for prop in s.properties:
                yield n, s.name, prop


tot = 0
quant_hits = 0
for _n, _s, prop in load_props():
    tot += 1
    if QUANT_RE.match(prop):
        quant_hits += 1


def run(use_norm: bool):
    eqlike = 0
    parsed = 0
    seen = set()
    for _n, _s, prop in load_props():
        if prop in seen:
            continue
        if not any(op in prop for op in OPS):
            continue
        if not any(c.isalpha() for c in prop):
            continue
        eqlike += 1
        txt = norm(prop) if use_norm else prop
        if parse_text(txt).parse_ok:
            parsed += 1
            seen.add(prop)
    return eqlike, parsed


b_eq, b_ok = run(False)
a_eq, a_ok = run(True)

lines = [
    "cmp_total            = %d" % tot,
    "quantifier_prefix    = %d" % quant_hits,
    "before: eqlike=%d parsed=%d rate=%.4f"
    % (b_eq, b_ok, b_ok / b_eq if b_eq else 0),
    "after : eqlike=%d parsed=%d rate=%.4f"
    % (a_eq, a_ok, a_ok / a_eq if a_eq else 0),
]
with open(os.path.join(REPO, "99-沙箱", "_diag_norm.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
