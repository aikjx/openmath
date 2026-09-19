# -*- coding: utf-8 -*-
"""探测 OpenMath 官方 CD 完整清单（一次性探测脚本，非流水线产物）。"""
import json
import urllib.request

url = "https://api.github.com/repos/OpenMath/CDs/contents/cd/Official"
out = []
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    names = sorted(x["name"][:-4] for x in data if x["name"].endswith(".ocd"))
    out.append("TOTAL_OFFICIAL_CDS: %d" % len(names))
    out.append(",".join(names))
except Exception as e:  # noqa: BLE001
    out.append("FETCH_FAILED: %s: %s" % (type(e).__name__, e))

with open(r"D:\a10\aikjx\code\my_lib\openmath\99-沙箱\_probe_cd_list.txt",
          "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n".join(out))
