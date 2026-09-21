"""Derivative, Bonferroni, Fourier and moment audits. AI-assisted, not a proof."""
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

import mpmath as mp
import numpy as np
import sympy as sp
from pwcv_goldbach_l2 import primes_up_to


def choose(n, k):
    return math.comb(n, k) if 0 <= k <= n else 0


def bonferroni(limit):
    prime, primes = primes_up_to(limit)
    orders = [1, 3, 5, 7]
    stats = {str(r): {'positive_lower_bound_count': 0, 'exact_count': 0,
                     'first_nonpositive': None} for r in orders}
    max_t = {'multiplicity': 0}
    for n in range(6, limit+1, 2):
        lo, hi = math.isqrt(n)+1, n//2
        hits = np.zeros(hi-lo+1, dtype=np.int16)
        small = [int(p) for p in primes if p*p <= n]
        for p in small:
            hits[(-lo) % p::p] += 1
            if n % p:
                hits[(n-lo) % p::p] += 1
        hist = np.bincount(hits)
        h = int(hist[0])
        assert h == sum(bool(prime[m] and prime[n-m]) for m in range(lo, hi+1))
        if n <= 100:
            direct = [sum(m % p == 0 or (n-m) % p == 0 for p in small)
                      for m in range(lo, hi+1)]
            assert direct == list(hits)
        t = int(hits.max())
        if t > max_t['multiplicity']:
            m = lo+int(np.argmax(hits))
            max_t = {'N': n, 'm': m, 'other': n-m, 'multiplicity': t,
                     'distinct_small_prime_divisors': [p for p in small if m % p == 0 or (n-m) % p == 0]}
        for r in orders:
            lower = sum(int(count)*sum((-1)**j*choose(t, j) for j in range(r+1))
                        for t, count in enumerate(hist))
            tail = sum(int(hist[t])*choose(t-1, r) for t in range(1, len(hist)))
            assert lower == h-tail and lower <= h
            if lower > 0:
                stats[str(r)]['positive_lower_bound_count'] += 1
            if lower == h:
                stats[str(r)]['exact_count'] += 1
            if lower <= 0 and stats[str(r)]['first_nonpositive'] is None:
                stats[str(r)]['first_nonpositive'] = {'N': n, 'lower': lower, 'H': h, 'tail': tail}
    return {'all_even_from': 6, 'all_even_to': limit, 'count': (limit-4)//2,
            'orders': stats, 'maximum_hit_multiplicity': max_t,
            'identity_residual': 0, 'arithmetic': 'exact integers'}


def calculus_and_fourier():
    x = sp.Symbol('x')
    _, pa = primes_up_to(127)
    primes = list(map(int, pa))
    polynomial = sum(x**p for p in primes)
    square = sp.expand(polynomial**2)
    coeff = [0]*256
    for p in primes:
        for q in primes:
            coeff[p+q] += 1
    poly = sp.Poly(square, x)
    assert all(int(poly.nth(n)) == coeff[n] for n in range(256))
    derivative = {}
    for n in [4, 6, 10, 38, 100]:
        value = sp.diff(square, x, n).subs(x, 0)/sp.factorial(n)
        assert value == coeff[n]
        derivative[str(n)] = int(value)
    toy = sp.expand((x**3+x**7)**2)
    assert sp.diff(toy, x, 8).subs(x, 0) == 0
    assert all(sp.diff(toy, x, k).subs(x, sp.Rational(1, 2)) > 0 for k in range(15))
    length = 256
    k = len(primes)
    main_dc = F(k*k, length)
    main_parity = F(k*k+(2-k)**2, length)
    numeric = []
    for precision in [80, 120]:
        mp.mp.dps = precision
        roots = [mp.exp(-2j*mp.pi*j/length) for j in range(length)]
        spectrum = [sum(roots[(j*p) % length] for p in primes) for j in range(length)]
        energy = sum(abs(z)**2 for z in spectrum)/length
        residual = mp.mpf(0)
        for n in range(4, 127, 2):
            reconstructed = sum(spectrum[j]**2*mp.conj(roots[(j*n) % length])
                                for j in range(length))/length
            residual = max(residual, abs(reconstructed-coeff[n]))
        tolerance = mp.mpf(10)**(-precision+15)
        assert residual < tolerance and abs(energy-k) < tolerance
        numeric.append({'decimal_digits': precision, 'max_complex_residual': mp.nstr(residual, 12),
                        'parseval_residual': mp.nstr(abs(energy-k), 12),
                        'absolute_tolerance': mp.nstr(tolerance, 6)})
    vals = [coeff[n] for n in range(4, 127, 2)]
    first, second = sum(vals), sum(v*v for v in vals)
    bound = F(first*first, second)
    return {
        'generating_function': {'primes_through': 127, 'prime_count': k,
                               'coefficient_comparisons': 256, 'derivative_over_factorial': derivative,
                               'toy_polynomial': str(toy), 'toy_missing_coefficient': 8,
                               'toy_positive_derivatives_at_half': list(range(15))},
        'fourier': {'transform_length': length, 'target_even_from': 4, 'target_even_to': 126,
                    'no_aliasing': 'degree 254 < transform length 256',
                    'dc_main': str(main_dc), 'dc_triangle_lower_bound': str(2*main_dc-k),
                    'dc_plus_parity_main': str(main_parity),
                    'dc_plus_parity_triangle_lower_bound': str(2*main_parity-k),
                    'checks': numeric, 'max_componentwise_relative_condition_number': str(F(k, min(vals))),
                    'conditioning_definition': 'sum(abs(F_k^2/L))/abs(P(N)) = prime_count/P(N)',
                    'caveat': 'High-precision diagnostics are not interval-certified real analysis or a minor-arc estimate.'},
        'moments': {'all_even_from': 4, 'all_even_to': 126, 'slots': len(vals),
                    'first_moment': first, 'second_moment': second,
                    'cauchy_support_lower_bound': str(bound),
                    'integer_support_lower_bound': (bound.numerator+bound.denominator-1)//bound.denominator,
                    'actual_positive_slots': sum(v > 0 for v in vals)}}


def main():
    results = calculus_and_fourier()
    results['bonferroni'] = bonferroni(10000)
    results.update({
        'target_id': 'OM-P-NT-0003', 'conjecture_status': 'OPEN',
        'provenance': {'ai_assisted': True, 'independent_review': False},
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': {'python': platform.python_version(), 'numpy': np.__version__,
                        'sympy': sp.__version__, 'mpmath': mp.__version__},
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [Path(__file__), Path(__file__).with_name('pwcv_goldbach_l2.py')]},
        'limits': ['Finite evidence only, not a proof of Goldbach.',
                   'No assertion that all mathematical methods have been exhausted.',
                   'Exact higher-order inclusion-exclusion does not give a uniform analytic lower bound.']})
    out = Path(__file__).resolve().parents[1]/'03-结果/2026/09/OM-P-NT-0003-new-methods-20260920.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
