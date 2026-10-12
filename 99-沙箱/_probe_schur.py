# -*- coding: utf-8 -*-
"""临时探针：评估 4 色搜索在 n=41/42/44 的可完成性。用完即删。"""
import os, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
name = None
for fn in os.listdir(HERE):
    if fn.startswith("schur_") and fn.endswith(".py") and "AI" in fn:
        name = fn
        break

spec = importlib.util.spec_from_file_location("mod_schur", os.path.join(HERE, name))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for tie in ("large", "small"):
    for n in (41, 42, 44):
        t = time.time()
        r = mod.search_schur(n, 4, time.time() + 25, tie=tie)
        print("tie=%s n=%d found=%s timeout=%s nodes=%d ms=%.1f"
              % (tie, n, r["found"], r["timeout"], r["nodes"], (time.time() - t) * 1000))
