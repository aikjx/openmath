# -*- coding: utf-8 -*-
"""排查快照新鲜度：本地 .ocd 与上游最新内容是否一致（只读比对，不改文件）。"""
import hashlib
import json
import os
import sys

REPO = r"D:\a10\aikjx\code\my_lib\openmath"
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎",
                                "openmath_sys", "src"))
from openmath_sys.fetcher import fetch_openmath_cd_raw, parse_ocd  # noqa: E402

CDS = os.path.join(REPO, "09-数据", "openmath_cds")
cat = json.load(open(os.path.join(CDS, "catalog.json"), encoding="utf-8"))
names = [c["name"] for c in cat["cds"]]


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def sym_props(text):
    if not text:
        return None
    try:
        syms = parse_ocd(text)
        return (len(syms), sum(len(x.properties) for x in syms))
    except Exception:  # noqa: BLE001
        return None


rows = []
for n in names:
    p = os.path.join(CDS, n + ".ocd")
    local = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    raw = fetch_openmath_cd_raw(n, timeout=10)
    rows.append({
        "name": n,
        "local_size": len(local) if local else 0,
        "fresh_size": len(raw) if raw else 0,
        "identical": (local is not None and raw is not None
                      and sha(local) == sha(raw)),
        "local_sp": sym_props(local),
        "fresh_sp": sym_props(raw),
        "fetch_ok": raw is not None,
    })

diff = [r for r in rows if r["fetch_ok"] and not r["identical"]]
fail = [r for r in rows if not r["fetch_ok"]]
miss_local = [r for r in rows if r["local_size"] == 0]

lines = [
    "total=%d  identical=%d  DIFFERENT=%d  fetch_failed=%d  no_local=%d"
    % (len(rows), sum(1 for r in rows if r["identical"]),
       len(diff), len(fail), len(miss_local)),
    "",
    "=== 与上游不一致的本地快照（陈旧）===",
]
for r in diff:
    lines.append("  %-14s local=%dB fresh=%dB  local(sym,props)=%s  fresh(sym,props)=%s"
                 % (r["name"], r["local_size"], r["fresh_size"],
                    r["local_sp"], r["fresh_sp"]))
if not diff:
    lines.append("  （无）")

lines.append("")
lines.append("=== 本次抓取失败（将回退本地陈旧快照）===")
for r in fail:
    lines.append("  %s" % r["name"])
if not fail:
    lines.append("  （无）")

lines.append("")
lines.append("=== 各 CD 性质总数（上游口径）===")
tot = 0
for r in rows:
    sp = r["fresh_sp"] or r["local_sp"]
    if sp:
        tot += sp[1]
lines.append("  fresh 口径 CMP 总数 = %d" % tot)

with open(os.path.join(REPO, "99-沙箱", "_probe_fresh.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("probe done")
