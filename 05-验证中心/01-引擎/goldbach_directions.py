"""Three finite Goldbach experiments, AI-assisted; not an infinite proof."""
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from pwcv_goldbach_l2 import primes_up_to


def binary_convolution(a, b):
    """Exact polynomial multiplication by carry-free integer packing."""
    assert len(a) and len(b)
    assert all(x in (0, 1) for x in a) and all(x in (0, 1) for x in b)
    width = (min(len(a), len(b)).bit_length() + 7) // 8
    packed_a = int.from_bytes(b''.join(int(x).to_bytes(width, 'little') for x in a), 'little')
    packed_b = int.from_bytes(b''.join(int(x).to_bytes(width, 'little') for x in b), 'little')
    length = len(a) + len(b) - 1
    raw = (packed_a * packed_b).to_bytes(length * width, 'little')
    return [int.from_bytes(raw[i*width:(i+1)*width], 'little') for i in range(length)]


def main():
    limit = 100000
    isp, primes = primes_up_to(limit + 2)
    a = [int(x) for x in isp[:limit+1]]
    pairs = binary_convolution(a, a)
    # T(N) counts ordered p+q=N with q+2 also prime.
    twins = [int(isp[q] and isp[q+2]) for q in range(limit+1)]
    transport = binary_convolution(a, twins)
    checked = list(range(4, 2001, 2)) + [8192, 10000, 32768, 65536, 100000]
    for n in checked:
        assert pairs[n] == sum(a[p]*a[n-p] for p in range(1, n))
        assert transport[n] == sum(a[p]*twins[n-p] for p in range(1, n))
    bands = []
    for lo, hi in [(4, 100), (102, 1000), (1002, 10000), (10002, limit)]:
        ns = range(lo, hi+1, 2)
        worst = min(ns, key=lambda n: Fraction(pairs[n]*n.bit_length()**2, n))
        bands.append({'from': lo, 'to': hi, 'minimum_ratio_N': worst,
                      'ordered_pairs': pairs[worst],
                      'min_P_bitlength_squared_over_N': str(Fraction(pairs[worst]*worst.bit_length()**2, worst))})
    zero_transfer = [n for n in range(6, limit-1, 2) if transport[n] == 0]
    residue_ns = [n for n in range(8, limit-1, 6)]
    assert all((transport[n] > 0) == bool(a[n-3]) for n in residue_ns)
    obstruction_family = list(range(38, limit-1, 30))
    assert all(transport[n] == 0 for n in obstruction_family)
    transfer_example = None
    if zero_transfer:
        n = zero_transfer[0]
        transfer_example = {'N': n,
                            'unordered_pairs': [[p, n-p] for p in range(2, n//2+1) if a[p] and a[n-p]],
                            'next_unordered_pairs': [[p, n+2-p] for p in range(2, (n+2)//2+1) if a[p] and a[n+2-p]]}
    monotone_fail = [n for n in range(4, limit-1, 2)
                     if (pairs[n+2]+a[(n+2)//2])//2 < (pairs[n]+a[n//2])//2]
    sieve_failures = 0
    first_sieve_failure = None
    union_positive = 0
    first_union_inconclusive = None
    for n in range(6, 5001, 2):
        y = math.isqrt(n)
        initial = list(range(y+1, n//2+1))
        alive = initial[:]
        total_individual_deletions = 0
        for p in map(int, primes):
            if p > y:
                break
            before = len(alive)
            killed = [m for m in alive if m % p == 0 or (n-m) % p == 0]
            rho = 1 if n % p == 0 else 2
            proposed_cap = (rho*before + p-1)//p
            if len(killed) > proposed_cap:
                sieve_failures += 1
                if first_sieve_failure is None:
                    first_sieve_failure = {'N': n, 'p': p, 'rho': rho,
                                           'survivors_before': alive[:], 'killed': killed,
                                           'proposed_cap': proposed_cap}
            alive = [m for m in alive if m % p and (n-m) % p]
            total_individual_deletions += sum(m % p == 0 or (n-m) % p == 0 for m in initial)
        h = sum(a[m]*a[n-m] for m in initial)
        assert len(alive) == h
        lower = len(initial) - total_individual_deletions
        assert lower <= h
        if lower > 0:
            union_positive += 1
        elif first_union_inconclusive is None:
            first_union_inconclusive = {'N': n, 'union_lower_bound': lower, 'actual_central_pairs': h}
    result = {
        'target': 'OM-P-NT-0003', 'conjecture_status': 'OPEN',
        'provenance': {'ai_assisted': True, 'independent_human_review': False},
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'arithmetic': 'exact integers and rational ratios',
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [Path(__file__), Path(__file__).with_name('test_goldbach_directions.py'),
                           Path(__file__).with_name('pwcv_goldbach_l2.py')]},
        'convolution': {'all_even_from': 4, 'all_even_to': limit, 'even_count': (limit-2)//2,
                        'goldbach_counterexamples': [n for n in range(4, limit+1, 2) if not pairs[n]],
                        'candidate': 'P(N) * bit_length(N)^2 >= N',
                        'candidate_counterexamples': [n for n in range(4, limit+1, 2) if pairs[n]*n.bit_length()**2 < n],
                        'bands': bands, 'direct_crosscheck_N_count': len(checked)},
        'transport': {'all_even_from': 6, 'all_even_to': limit-2,
                      'mod3_equivalence_checked_N_count': len(residue_ns),
                      'infinite_family_formula': 'N = 30*k + 8, k >= 1',
                      'family_members_in_search': len(obstruction_family),
                      'zero_transfer_count': len(zero_transfer), 'first_zero_transfer': transfer_example,
                      'last_zero_transfer_N': zero_transfer[-1] if zero_transfer else None,
                      'first_ten_zero_transfer_N': zero_transfer[:10],
                      'G_monotonicity_failure_count': len(monotone_fail),
                      'first_monotonicity_failure_N': monotone_fail[0] if monotone_fail else None},
        'sieve': {'all_even_from': 6, 'all_even_to': 5000,
                  'candidate': 'killed_p <= ceil(rho_p * survivors_before / p)',
                  'candidate_failing_layers': sieve_failures,
                  'first_failure': first_sieve_failure,
                  'union_bound_positive_N_count': union_positive,
                  'first_union_bound_inconclusive': first_union_inconclusive},
        'limits': ['Finite experiments only; successful candidates remain unproved.',
                   'Falsified auxiliary inequalities are not counterexamples to Goldbach.',
                   'No L4 formalization or independent expert review.']}
    out = Path(__file__).resolve().parents[1] / '03-结果/2026/09/OM-P-NT-0003-directions-20260920.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
