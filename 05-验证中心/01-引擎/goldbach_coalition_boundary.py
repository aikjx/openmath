"""Finite boundary audit, not a proof of Goldbach. AI-assisted, 2026-09-20.

Run with Python; reuses the existing numpy PWCV engine without overwriting
its historical result. All new mathematical checks use exact integers.
"""
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import pwcv_goldbach_l2 as pwcv


def trial_prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def main():
    limit = 2000
    prime, primes = pwcv.primes_up_to(limit)
    assert all(bool(prime[n]) == trial_prime(n) for n in range(limit + 1))
    proper_powers = set()
    for p in map(int, primes):
        x = p * p
        while x <= limit:
            proper_powers.add(x)
            x *= p
    power_support = set(map(int, primes)) | proper_powers
    failures = []
    central_zero = []
    residual_max = 0
    contamination_max = {"N": None, "ordered_count": -1}
    for n in range(4, limit + 1, 2):
        g = sum(bool(prime[m] and prime[n-m]) for m in range(2, n//2 + 1))
        if not g:
            failures.append(n)
        ordered = sum(bool(prime[m] and prime[n-m]) for m in range(1, n))
        assert ordered == 2*g - int(prime[n//2])
        y = math.isqrt(n)
        h = sum(bool(prime[m] and prime[n-m]) for m in range(y + 1, n//2 + 1))
        screened = sum(all(m % int(p) and (n-m) % int(p)
                           for p in primes if p <= y)
                       for m in range(y + 1, n//2 + 1))
        residual_max = max(residual_max, abs(h - screened))
        if not h:
            central_zero.append(n)
        t = sum(m in power_support and n-m in power_support for m in range(1, n))
        contamination = t - ordered
        proper_count = sum(x < n for x in proper_powers)
        k = n.bit_length() - 1
        assert 0 <= contamination <= 2 * proper_count <= 2 * (k-1) * y
        if contamination > contamination_max["ordered_count"]:
            contamination_max = {"N": n, "ordered_count": contamination}
    assert residual_max == 0
    assert central_zero == [4]
    anchors = [pwcv.verify(n) for n in sorted(pwcv.ANCHOR)]
    anchor_ok = all(r["resid_G"] == 0 and r["resid_survive_minus_direct"] == 0
                    and r["all_survivors_prime_pairs"]
                    and r["k_nonprime_counterexamples"] == 0
                    and r["q1_le_zprev_counterexamples"] == 0 for r in anchors)
    result = {
        "target_id": "OM-P-NT-0003", "conjecture_status": "OPEN",
        "provenance": {"ai_assisted": True, "independent_human_review": False},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "numpy": pwcv.np.__version__},
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), Path(pwcv.__file__)]},
        "arithmetic": "exact integers for new checks; inherited anchor engine uses floating cube-root phase boundary and diagnostic ratios",
        "conditioning": "not applicable to new exact-integer checks",
        "scope": {"all_even_N_from": 4, "all_even_N_to": limit,
                  "even_N_count": (limit-4)//2+1,
                  "separate_anchor_N": sorted(pwcv.ANCHOR)},
        "goldbach_search": {"counterexamples": failures, "search_upper_bound": limit},
        "central_zero_N": central_zero,
        "central_identity_max_integer_residual": residual_max,
        "prime_power_contamination_max": contamination_max,
        "ordered_unordered_and_contamination_checks": "PASS",
        "anchor_structure_checks": "PASS" if anchor_ok else "FAIL",
        "anchors": anchors,
        "limitations": ["No all-even coverage between 2000 and the two anchors.",
                        "No weighted logarithmic correlation bound was checked or proved.",
                        "No L4 build; no proof of infinite positivity."]}
    out = Path(__file__).resolve().parents[1] / "03-结果/2026/09/OM-P-NT-0003-boundary-20260920.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not anchor_ok or failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
