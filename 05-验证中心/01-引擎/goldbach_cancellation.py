"""Exact sieve error ledger and bounded two-sided transport experiments.

AI-assisted research only. No claim of proving Goldbach.
"""
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

from pwcv_goldbach_l2 import primes_up_to


def ledger(n, primes):
    initial = list(range(math.isqrt(n)+1, n//2+1))
    alive = initial[:]
    main = F(len(initial))
    signed = absolute = F(0)
    layers = []
    for p in primes:
        p = int(p)
        if p*p > n:
            break
        before = len(alive)
        alive = [m for m in alive if m % p and (n-m) % p]
        killed = before-len(alive)
        alpha = 1-F(1 if n % p == 0 else 2, p)
        d = killed-(1-alpha)*before
        main *= alpha
        signed = alpha*signed+d
        absolute = alpha*absolute+abs(d)
        layers.append((alpha, d))
    # Independently expand the weighted sum backwards.
    tail = F(1)
    expanded = expanded_abs = F(0)
    for alpha, d in reversed(layers):
        expanded += d*tail
        expanded_abs += abs(d)*tail
        tail *= alpha
    assert main == len(initial)*tail
    assert signed == expanded and absolute == expanded_abs
    assert main-signed == len(alive)
    return {'N': n, 'H': len(alive), 'M': main, 'E': signed, 'A': absolute}


def closest_shift(left, right):
    if not left or not right:
        return None
    i = j = 0
    best = None
    while i < len(left) and j < len(right):
        distance = abs(right[j]-left[i])
        if best is None or distance < best[0]:
            best = (distance, left[i], right[j])
        if distance == 0:
            break
        if left[i] < right[j]:
            i += 1
        else:
            j += 1
    return best


def main():
    limit = 20000
    prime, primes = primes_up_to(limit+2)
    assert closest_shift([3, 7], [5, 11]) == (2, 3, 5)
    assert closest_shift([], [3]) is None
    assert closest_shift([3], [3]) == (0, 3, 3)
    records = [ledger(n, primes) for n in range(6, 5001, 2)]
    for r in records:
        n = r['N']
        assert r['H'] == sum(bool(prime[m] and prime[n-m])
                             for m in range(math.isqrt(n)+1, n//2+1))
    tests = {}
    for label, predicate in [
        ('absolute_error_less_than_main', lambda r: r['A'] < r['M']),
        ('positive_error_less_than_main', lambda r: (r['A']+r['E'])/2 < r['M']),
        ('positive_error_at_most_half_main', lambda r: (r['A']+r['E'])/2 <= r['M']/2),
        ('signed_error_at_most_half_main', lambda r: r['E'] <= r['M']/2),
        ('signed_error_at_most_three_quarters_main', lambda r: r['E'] <= 3*r['M']/4),
    ]:
        bad = [r for r in records if not predicate(r)]
        tests[label] = {'failed_N_count': len(bad), 'first_failure': bad[0] if bad else None,
                        'last_failure': bad[-1] if bad else None,
                        'first_ten_failure_N': [r['N'] for r in bad[:10]]}
    worst = max(records, key=lambda r: r['E']/r['M'])
    worst_abs = max(records, key=lambda r: r['A']/r['M'])
    worst_positive = max(records, key=lambda r: (r['A']+r['E'])/(2*r['M']))
    ranges = [0, 2, 4, 8, 16, 32]
    migration = {str(r): {'failure_count': 0, 'first_failure': None} for r in ranges}
    prev = None
    max_shift = None
    empty = []
    checked_direct = 0
    for n in range(6, limit+3, 2):
        ps = primes[primes < n]
        current = list(map(int, ps[prime[n-ps]]))
        if not current:
            empty.append(n)
        if prev is not None:
            best = closest_shift(prev, current)
            if n <= 202:
                reference = min((abs(q-p) for p in prev for q in current), default=None)
                assert (best[0] if best else None) == reference
                checked_direct += 1
            witness = {'N': n-2, 'minimum_absolute_shift': best[0] if best else None,
                       'old_pair': [best[1], n-2-best[1]] if best else None,
                       'new_pair': [best[2], n-best[2]] if best else None}
            if best is not None and (max_shift is None or best[0] > max_shift['minimum_absolute_shift']):
                max_shift = witness
            for radius in ranges:
                if best is None or best[0] > radius:
                    migration[str(radius)]['failure_count'] += 1
                    if migration[str(radius)]['first_failure'] is None:
                        migration[str(radius)]['first_failure'] = witness
        prev = current
    result = {
        'target_id': 'OM-P-NT-0003', 'conjecture_status': 'OPEN',
        'provenance': {'ai_assisted': True, 'independent_review': False},
        'timestamp': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
        'arithmetic': 'exact integers and Fraction; no floating-point tests',
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [Path(__file__), Path(__file__).with_name('pwcv_goldbach_l2.py')]},
        'ledger': {'all_even_from': 6, 'all_even_to': 5000, 'count': len(records),
                   'forward_backward_identity_max_residual': 0, 'candidates': tests,
                   'max_signed_error_ratio_record': dict(worst, ratio=worst['E']/worst['M']),
                   'max_absolute_error_ratio_record': dict(worst_abs, ratio=worst_abs['A']/worst_abs['M']),
                   'max_positive_error_ratio_record': dict(worst_positive, ratio=(worst_positive['A']+worst_positive['E'])/(2*worst_positive['M'])),
                   'caveat': 'E=M-H is exact: E<M is equivalent to central positivity, not independent evidence.'},
        'two_sided_transport': {'all_even_N_from': 6, 'all_even_N_to': limit,
                                'N_plus_2_included_through': limit+2,
                                'rule': '(p,q) -> (p+d,q+2-d), abs(d)<=radius',
                                'candidate_radii': migration, 'max_minimum_shift': max_shift,
                                'empty_pair_sets': empty, 'brute_force_comparison_count': checked_direct},
        'limitations': ['No infinite error bound.', 'Successful radius is an observation, not an induction theorem.',
                        'Auxiliary counterexamples do not refute Goldbach.']}
    out = Path(__file__).resolve().parents[1]/'03-结果/2026/09/OM-P-NT-0003-cancellation-20260920.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
