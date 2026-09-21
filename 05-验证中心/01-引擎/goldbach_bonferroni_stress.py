"""Exact fixed-order Bonferroni stress tests at explicitly listed anchors."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from pwcv_goldbach_l2 import primes_up_to
from goldbach_new_methods import choose


def main():
    anchors = [10000, 100000, 1000000, 10000000]
    prime, primes = primes_up_to(max(anchors))
    rows = []
    for n in anchors:
        lo, hi = math.isqrt(n)+1, n//2
        hits = np.zeros(hi-lo+1, dtype=np.int16)
        for p in primes:
            p = int(p)
            if p*p > n:
                break
            hits[(-lo) % p::p] += 1
            if n % p:
                hits[(n-lo) % p::p] += 1
        hist = list(map(int, np.bincount(hits)))
        direct = int(np.count_nonzero(prime[lo:hi+1] & prime[n-hi:n-lo+1][::-1]))
        assert hist[0] == direct
        lowers = {}
        for r in [1, 3, 5, 7, 9, 11]:
            tail = sum(hist[t]*choose(t-1, r) for t in range(1, len(hist)))
            lower = sum(count*sum((-1)**j*choose(t, j) for j in range(r+1))
                        for t, count in enumerate(hist))
            assert lower == direct-tail
            lowers[str(r)] = {'lower': lower, 'tail': tail}
        rows.append({'N': n, 'central_pairs': direct, 'multiplicity_histogram': hist,
                     'bonferroni': lowers})
    coverage = []
    for n in [10, 100, 1000, 10000]:
        count = int(prime[3:n-2:2].sum())
        coverage.append({'N': n, 'odd_prime_count': count, 'odd_slots': n//2-2,
                         'pigeonhole_lower': 2*count-(n//2-2)})
    result = {'target_id': 'OM-P-NT-0003', 'conjecture_status': 'OPEN',
              'provenance': {'ai_assisted': True, 'independent_review': False},
              'timestamp': datetime.now(timezone.utc).isoformat(),
              'arithmetic': 'exact integers', 'scope': 'four anchors, not all even N up to 10^7',
              'rows': rows, 'pigeonhole': coverage,
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                               [Path(__file__), Path(__file__).with_name('goldbach_new_methods.py'),
                                Path(__file__).with_name('pwcv_goldbach_l2.py')]}}
    out = Path(__file__).resolve().parents[1]/'03-结果/2026/09/OM-P-NT-0003-bonferroni-stress-20260920.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
