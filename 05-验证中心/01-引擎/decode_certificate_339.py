# -*- coding: utf-8 -*-
"""
破译用户给出的"339 条整除证书"（X=2e6，阈值 T=1,000,537）

思路：要证明阈值 T 不能降低，必须在一个"最坏偶数" N 上证明
      "任一表示 N=p+q (p<=q) 都满足 q >= T"。
      q = N - p，故等价于：区间 p in (N-T, N/2] 内没有任何素数 p 使 N-p 为素数。
      该区间内的偶数 p 自动非素数；每个【奇数】p 都需一条整除证书
      （p 合数 -> 给出 p 的因子；p 素数 -> 给出 N-p 的因子）。
      => 证书条数 = 该窗口内奇数个数。检验是否恰为 339。

同时用试除法独立验证两个见证素数，并对 N=2e6 及 λ 前几名做同样统计。
"""
import json
import os
from bisect import bisect_right
from math import isqrt

X = 2_000_000


def sieve(limit):
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return s


def is_prime_trial(n):
    """独立试除法（不引用筛表），用于验证见证素数"""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def smallest_factor(n):
    if n % 2 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d += 2
    return n


def lam_of(N, s, primes):
    j = bisect_right(primes, N // 2) - 1
    while j >= 0:
        p = primes[j]
        if s[N - p]:
            return N - p, p
        j -= 1
    return None, None


def certificate_window(N, T, s, emit):
    """窗口 (N-T, N/2] 内的整除证书清单"""
    lo, hi = N - T + 1, N // 2
    odd = [p for p in range(lo if lo % 2 else lo + 1, hi + 1, 2)]
    certs, prime_ps = [], []
    for p in odd:
        if s[p]:
            prime_ps.append(p)
            d = smallest_factor(N - p)
            certs.append({"p": p, "p_is_prime": True, "witness_for": "N-p",
                          "N_minus_p": N - p, "divisor": d,
                          "quotient": (N - p) // d})
        else:
            d = smallest_factor(p)
            certs.append({"p": p, "p_is_prime": False, "witness_for": "p",
                          "value": p, "divisor": d, "quotient": p // d})
    emit("N=%d  T=%d  window=(%d, %d]  宽度=%d  奇数个数=%d"
         % (N, T, N - T, N // 2, hi - lo + 1, len(odd)))
    emit("  其中 p 本身为素数者 %d 个（需给出 N-p 的因子），p 本身合数者 %d 个（给出 p 的因子）"
         % (len(prime_ps), len(odd) - len(prime_ps)))
    return certs, len(odd)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    json_path = os.path.join(out_dir, "OM-P-NT-0003-certificate-339-decode-20260922.json")
    log_path = os.path.join(out_dir, "_decode339_runlog.txt")

    s = sieve(X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "X": X, "question": "为何 339 条整除证书在复算中未命中"}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        emit("=== 0. 先找 argmax lambda（最坏偶数）===")
        best = (0, 0, 0)
        for N in range(4, X + 1, 2):
            lam, p = lam_of(N, s, primes)
            if lam > best[0]:
                best = (lam, N, p)
        T, Nstar, pstar = best
        emit("argmax: lambda=%d  at N=%d  见证对 (%d, %d)"
             % (T, Nstar, pstar, Nstar - pstar))
        out["argmax"] = {"lambda": T, "N": Nstar, "p": pstar, "q": Nstar - pstar}

        emit("")
        emit("=== 1. 用试除法独立验证两个见证素数 ===")
        v1 = is_prime_trial(pstar)
        v2 = is_prime_trial(Nstar - pstar)
        emit("p* = %d  trial-division prime? %s" % (pstar, v1))
        emit("q* = %d  trial-division prime? %s" % (Nstar - pstar, v2))
        emit("N* = p*+q* ? %s" % (pstar + (Nstar - pstar) == Nstar))
        out["witness_verification"] = {"N": Nstar, "p": pstar, "q": Nstar - pstar,
                                       "p_prime_trial": v1, "q_prime_trial": v2,
                                       "sum_ok": True}

        emit("")
        emit("=== 2. 关键：证书窗口 (N-T, N/2] 的奇数个数 ===")
        certs, cnt = certificate_window(Nstar, T, s, emit)
        emit("  => 证书条数 = %d（与用户所称 339 相符？%s）" % (cnt, cnt == 339))
        out["certificate_window"] = {
            "N": Nstar, "T": T, "window_open": Nstar - T, "window_closed": Nstar // 2,
            "width": Nstar // 2 - (Nstar - T), "odd_count": cnt,
            "matches_339": cnt == 339,
            "certificates_head": certs[:8], "certificates_tail": certs[-5:],
        }

        emit("")
        emit("=== 3. 对照：其他候选 N 的窗口大小（看 339 是否特异）===")
        rows = []
        # 去重：老版把 Nstar 与硬编码的 1_999_718 重复列了两次，且 Nstar+2 越界时又回退成 Nstar
        cand = sorted({X, X - 2, Nstar, Nstar - 2, Nstar + 2, Nstar + 218})
        for N in cand:
            if N % 2 or N < 4 or N > X:
                continue
            lam, p = lam_of(N, s, primes)
            if lam is None:
                continue
            lo, hi = N - lam + 1, N // 2
            od = len(range(lo if lo % 2 else lo + 1, hi + 1, 2))
            rows.append({"N": N, "lambda": lam, "p_star": p,
                         "window": [N - lam, N // 2], "odd_count": od})
            emit("  N=%-8d lambda=%-8d p*=%-8d window=(%d,%d] 奇数=%d"
                 % (N, lam, p, N - lam, N // 2, od))
        out["other_candidates"] = rows

        emit("")
        emit("=== 4. 结论 ===")
        emit("若要证明阈值 T 不可降低，须在最坏偶数 N*=%d 的窗口 (%d,%d] 内"
             % (Nstar, Nstar - T, Nstar // 2))
        emit("对每个奇数 p 各给一条整除证书；该窗口恰含 %d 个奇数。" % cnt)
        emit("此前复算之所以'未命中'，是因为只统计了 lambda 层面的计数"
             "（=T 的偶数个数 1、lambda>1e6 的偶数 98 等），"
             "而 339 是【单点证书窗口的宽度除法计数】，两者不是同一个量。")
        out["explanation"] = ("339 = 最坏偶数 N*=1999718 的证书窗口 (999181, 999859] "
                              "内的奇数个数；与此前统计的 lambda 口径不同")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
