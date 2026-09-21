import sys
SRC = r"D:/a10/aikjx/code/my_lib/openmath/06-AI自动化/02-引擎/openmath_sys/src"
sys.path.insert(0, SRC)
import openmath_sys.sequences as S

print("N_TERMS=%r DISCOVERY_LEN=%r P_ORDER_MAX=%r P_DEG_MAX=%r" % (
    S.N_TERMS, S.DISCOVERY_LEN, S.P_ORDER_MAX, S.P_DEG_MAX))

seqs = S.build_sequences(S.N_TERMS + 2)
s = next(x for x in seqs if x["id"] == "apery")
print("apery terms len:", len(s["terms"]))

base_prec = S._has(s["terms"], "prec")
tf, fn = S.TRANSFORMS["diff"]
tv = fn(s["terms"])
print("diff tv len:", len(tv))
after_prec = S._has(tv, "prec")
relaxed_prec = any(c.get("survived_extrapolation")
                   for c in S.discover_polynomial_recurrence(
                       tv, max_order=S.P_ORDER_MAX + 2))
degenerate = (all(x == 0 for x in tv[len(tv)//2:])
              or len(set(tv[len(tv)//2:])) <= 2)

lost = (base_prec and not after_prec and not degenerate and not relaxed_prec)
print("base_prec=%s after_prec=%s relaxed_prec=%s degenerate=%s"
      % (base_prec, after_prec, relaxed_prec, degenerate))
print("=> precursive_lost =", lost)
