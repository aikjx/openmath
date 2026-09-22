# -*- coding: utf-8 -*-
"""核对用户给出的 "339 条整除证书" —— 穷举各种自然口径，看哪个等于 339

⚠️ 已被取代（2026-09-22 同日）：本探针只穷举**沿 N 的聚合口径**
（#{N : λ(N) ≥ v} 之类），按构造不可能命中 339，故其 "NONE" 结论**不是**"339 不存在"，
而是**口径选错**。正确口径见 `decode_certificate_339.py`：
    339 = δ(N_T)/2，δ(N)=λ(N)−N/2，N_T = argmax λ（单点证书窗口内的奇数个数）。
保留本文件仅作"错误口径"的反面记录。**不要再据此下任何结论。**
"""
import json
import os
from bisect import bisect_right

X = 2_000_000


def sieve(limit):
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, int(limit ** 0.5) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return s


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    log_path = os.path.join(out_dir, "_probe339.txt")

    s = sieve(X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]
    lam = [0] * (X // 2 + 1)
    for N in range(4, X + 1, 2):
        j = bisect_right(primes, N // 2) - 1
        while j >= 0:
            p = primes[j]
            if s[N - p]:
                lam[N // 2] = N - p
                break
            j -= 1

    vals = [lam[i] for i in range(2, X // 2 + 1)]
    T = max(vals)
    n = len(vals)

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        emit("X=%d  evens=%d  T=%d" % (X, n, T))
        emit("")
        emit("A. 阈值口径 #{N : lambda(N) >= v}  （v 取 999000 以上的所有出现值）")
        distinct = sorted({v for v in vals if v >= 999000}, reverse=True)
        for v in distinct:
            c = sum(1 for x in vals if x >= v)
            emit("  v=%-9d  count=lambda>=v: %-6d   (lambda==v: %d)"
                 % (v, c, sum(1 for x in vals if x == v)))
        emit("")
        emit("B. 其他自然口径")
        cand = {
            "count_lambda_eq_T": sum(1 for x in vals if x == T),
            "count_lambda_ge_T": sum(1 for x in vals if x >= T),
            "count_lambda_gt_1e6": sum(1 for x in vals if x > 10 ** 6),
            "count_lambda_ge_1e6": sum(1 for x in vals if x >= 10 ** 6),
            "count_lambda_gt_999983": sum(1 for x in vals if x > 999983),
            "count_lambda_ge_999983": sum(1 for x in vals if x >= 999983),
            "count_lambda_gt_999979": sum(1 for x in vals if x > 999979),
            "distinct_lambda_values_gt_1e6": len({x for x in vals if x > 10 ** 6}),
            "distinct_lambda_values_ge_999000": len(distinct),
            "primes_in_1e6_to_T": sum(1 for p in primes if 10 ** 6 < p <= T),
            "primes_in_999983_to_T": sum(1 for p in primes if 999983 <= p <= T),
            "count_lambda_eq_1000003": sum(1 for x in vals if x == 1000003),
            "count_lambda_eq_1000033": sum(1 for x in vals if x == 1000033),
            "count_lambda_eq_1000037": sum(1 for x in vals if x == 1000037),
            "count_lambda_eq_1000159": sum(1 for x in vals if x == 1000159),
            "count_lambda_eq_1000409": sum(1 for x in vals if x == 1000409),
            "count_lambda_eq_1000537": sum(1 for x in vals if x == 1000537),
        }
        emit(json.dumps(cand, ensure_ascii=False, indent=2))
        emit("")
        emit("C. 命中 339 的口径：")
        hits = [k for k, v in cand.items() if v == 339]
        hits += ["lambda>=%d" % v for v in distinct
                 if sum(1 for x in vals if x >= v) == 339]
        emit(json.dumps(hits if hits else "NONE", ensure_ascii=False))


if __name__ == "__main__":
    main()
