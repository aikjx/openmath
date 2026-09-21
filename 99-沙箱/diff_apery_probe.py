import sys, math
SRC = r"D:/a10/aikjx/code/my_lib/openmath/06-AI自动化/02-引擎/openmath_sys/src"
sys.path.insert(0, SRC)
import openmath_sys.sequences as S

n_terms = 62
apery = [sum(math.comb(n, k) ** 2 * math.comb(n + k, k) ** 2
             for k in range(n + 1)) for n in range(n_terms)]
tv = [apery[i + 1] - apery[i] for i in range(len(apery) - 1)]

print("apery max abs term:", max(abs(x) for x in apery), "len", len(apery))
print("diff   max abs term:", max(abs(x) for x in tv), "len", len(tv))
print("P_TERM_ABS_BOUND =", S.P_TERM_ABS_BOUND)

def probe(terms, label, MO, MD, DL=30):
    cands = S.discover_polynomial_recurrence(terms, discovery_len=DL,
                                             max_order=MO, max_deg=MD)
    print(f"\n[{label}] max_order={MO} max_deg={MD} discovery_len={DL} -> {len(cands)} candidate(s)")
    for c in cands:
        print("   order=%d deg=%d survived=%s stmt=%s" % (
            c["order"], c["deg"], c.get("survived_extrapolation"),
            c.get("statement")))
    return cands

# 1) base apery (should be order 2 / deg 3)
probe(apery, "base apery", S.P_ORDER_MAX, S.P_DEG_MAX)
# 2) diff apery, default bounds (what _has uses) -> reported LOST
probe(tv, "diff apery DEFAULT", S.P_ORDER_MAX, S.P_DEG_MAX)
# 3) diff apery, relaxed ORDER only (what transform_closure relaxed_prec does)
probe(tv, "diff apery relaxed ORDER only", S.P_ORDER_MAX + 2, S.P_DEG_MAX)
# 4) diff apery, raise DEG too
probe(tv, "diff apery relaxed ORDER+DEG", S.P_ORDER_MAX + 2, S.P_DEG_MAX + 2)
# 5) even higher to see if recoverable at all
probe(tv, "diff apery ORD6 DEG8", 6, 8)
# 6) maybe needs more discovery terms; also try longer discovery_len
probe(tv, "diff apery ORD6 DEG8 DL40", 6, 8, DL=40)
