"""Stress E_+ and test an independent CRT discrepancy budget. AI-assisted."""
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from goldbach_cancellation import ledger
from pwcv_goldbach_l2 import primes_up_to


def decimal(x):
    with localcontext() as ctx:
        ctx.prec = 18
        return str(Decimal(x.numerator)/Decimal(x.denominator))


def fast_ledger(n, primes):
    lo, hi = math.isqrt(n)+1, n//2
    mask = np.ones(hi-lo+1, dtype=bool)
    initial = before = len(mask)
    model = F(initial)
    positive = signed = F(0)
    refined_cap = F(0)
    crt_sum = 0
    period = allowed = 1
    max_local_slack_violation = F(0)
    for p in primes:
        p = int(p)
        if p*p > n:
            break
        rho = 1 if n % p == 0 else 2
        killed = int(np.count_nonzero(mask[(-lo) % p::p]))
        mask[(-lo) % p::p] = False
        if rho == 2:
            killed += int(np.count_nonzero(mask[(n-lo) % p::p]))
            mask[(n-lo) % p::p] = False
        alpha = F(p-rho, p)
        d = F(p*killed-rho*before, p)
        independent_cap = allowed*rho*alpha
        assert abs(d) <= independent_cap
        occupied_upper = min(initial, ((initial+period-1)//period)*allowed)
        refined_layer_cap = alpha*min(allowed*rho, occupied_upper)
        assert d <= refined_layer_cap
        refined_cap = alpha*refined_cap+refined_layer_cap
        max_local_slack_violation = max(max_local_slack_violation, abs(d)-independent_cap)
        positive = alpha*positive+max(d, 0)
        signed = alpha*signed+d
        model *= alpha
        before -= killed
        crt_sum += rho*period
        period *= p
        allowed *= p-rho
    assert before == int(np.count_nonzero(mask))
    assert model-signed == before
    independent_ratio = F(crt_sum, initial)
    assert positive <= model*independent_ratio
    assert positive <= refined_cap
    return {'N': n, 'H': before, 'M': model, 'E': signed, 'E_plus': positive,
            'positive_ratio': positive/model, 'crt_ratio': independent_ratio,
            'refined_ratio': refined_cap/model,
            'crt_sum': crt_sum, 'initial_candidates': initial,
            'independent_bound_positive': crt_sum < initial,
            'local_cap_violation': max_local_slack_violation}


def main():
    anchors = [10000, 100000, 1000000, 10000000]
    targets = sorted(set(anchors + [2**k+d for k in range(10, 21) for d in [-2, 0, 2]]
                         + [30030, 510510, 9699690]))
    prime, primes = primes_up_to(max(targets))
    small = []
    for n in range(6, 501, 2):
        row = fast_ledger(n, primes)
        old = ledger(n, primes)
        assert row['H'] == old['H'] and row['M'] == old['M']
        assert row['E_plus'] == (old['A']+old['E'])/2
        small.append(row)
    rows = [fast_ledger(n, primes) for n in targets]
    for row in rows:
        n = row['N']
        lo, hi = math.isqrt(n)+1, n//2
        direct = int(np.count_nonzero(prime[lo:hi+1] & prime[n-hi:n-lo+1][::-1]))
        assert row['H'] == direct
    half_failures = [r for r in rows if r['positive_ratio'] > F(1, 2)]
    full_failures = [r for r in rows if r['positive_ratio'] >= 1]
    worst = max(rows, key=lambda r: r['positive_ratio'])

    def compact(r):
        return {'N': r['N'], 'H': r['H'], 'M_decimal': decimal(r['M']),
                'E_plus_over_M_exact': str(r['positive_ratio']),
                'E_plus_over_M_decimal': decimal(r['positive_ratio']),
                'independent_CRT_ratio_decimal': decimal(r['crt_ratio']),
                'independent_CRT_ratio_exact': str(r['crt_ratio']),
                'refined_independent_ratio_decimal': decimal(r['refined_ratio']),
                'refined_independent_ratio_exact': str(r['refined_ratio']),
                'refined_bound_positive': r['refined_ratio'] < 1,
                'independent_bound_positive': r['independent_bound_positive']}

    result = {'target_id': 'OM-P-NT-0003', 'conjecture_status': 'OPEN',
              'provenance': {'ai_assisted': True, 'independent_review': False},
              'timestamp': datetime.now(timezone.utc).isoformat(),
              'environment': {'python': platform.python_version(), 'numpy': np.__version__},
              'arithmetic': 'Fraction/integer comparisons; decimal strings are display only',
              'small_independent_crosscheck': {'from': 6, 'to': 500, 'count': len(small)},
              'small_CRT_positive_N': [r['N'] for r in small if r['independent_bound_positive']],
              'small_refined_positive_N': [r['N'] for r in small if r['refined_ratio'] < 1],
              'large_refined_positive_N': [r['N'] for r in rows if r['refined_ratio'] < 1],
              'small_CRT_first_failure': compact(next(r for r in small if not r['independent_bound_positive'])),
              'large_target_N': targets, 'large_target_count': len(rows),
              'half_budget_failure_N': [r['N'] for r in half_failures],
              'full_budget_failure_N': [r['N'] for r in full_failures],
              'worst_observed': compact(worst), 'anchors': [compact(r) for r in rows if r['N'] in anchors],
              'all_rows': [compact(r) for r in rows],
              'bound_formula': 'E_plus/M <= sum_i rho_i*Q_(i-1)/S0, Q_(i-1)=product of earlier primes',
              'refined_formula': 'C_i=alpha_i*C_(i-1)+alpha_i*min(rho_i*A_(i-1),U_(i-1)); U=min(S0,ceil(S0/Q)*A)',
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                               [Path(__file__), Path(__file__).with_name('goldbach_cancellation.py'),
                                Path(__file__).with_name('pwcv_goldbach_l2.py')]},
              'limits': ['Larger targets are 40 selected samples, not an all-even sweep.',
                         'Observed ratios are not an independent proof of a global half-budget.',
                         'The derived CRT bound is independent but can be much too weak.']}
    out = Path(__file__).resolve().parents[1]/'03-结果/2026/09/OM-P-NT-0003-key-bound-20260920.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['all_rows','anchors','worst_observed','small_CRT_first_failure']}, ensure_ascii=False, indent=2))
    print('WORST:', worst['N'], decimal(worst['positive_ratio']))
    for r in rows:
        if r['N'] in anchors:
            print('ANCHOR:', r['N'], 'positive ratio', decimal(r['positive_ratio']), 'refined cap', decimal(r['refined_ratio']))


if __name__ == '__main__':
    main()
