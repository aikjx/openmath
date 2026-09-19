# -*- coding: utf-8 -*-
"""探测全部 38 个官方 CD 的抓取与 XML 解析安全性（沙箱探针，非流水线产物）。

目的：在把 CD_NAMES 从 20 扩到 38 之前，确认每个 CD 能否被 parse_ocd 安全解析，
避免非标准 XML 导致整条流水线崩溃。
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_REPO), "openmath_sys", "src"))

from openmath_sys.fetcher import fetch_openmath_cd_raw, parse_ocd  # noqa: E402

NAMES = [
    "alg1", "altenc", "arith1", "bigfloat1", "calculus1", "complex1", "error",
    "fns1", "fns2", "integer1", "interval1", "limit1", "linalg1", "linalg2",
    "list1", "logic1", "mathmlattr", "mathmltypes", "meta", "metagrp",
    "metasig", "minmax1", "multiset1", "nums1", "piece1", "quant1",
    "relation1", "relation3", "rounding1", "s_data1", "s_dist1", "scscp1",
    "scscp2", "set1", "setname1", "sts", "transc1", "veccalc1",
]

rows = []
for n in NAMES:
    raw = fetch_openmath_cd_raw(n, timeout=10)
    row = {
        "name": n,
        "fetched": raw is not None,
        "bytes": len(raw) if raw else 0,
        "symbols": None,
        "props": None,
        "error": None,
    }
    if raw:
        try:
            syms = parse_ocd(raw)
            row["symbols"] = len(syms)
            row["props"] = sum(len(s.properties) for s in syms)
        except Exception as e:  # noqa: BLE001
            row["error"] = f"{type(e).__name__}: {e}"
    rows.append(row)

with open(os.path.join(_HERE, "_probe_all_cds.txt"), "w", encoding="utf-8") as f:
    f.write(json.dumps(rows, ensure_ascii=False, indent=2))
print("probe done")
