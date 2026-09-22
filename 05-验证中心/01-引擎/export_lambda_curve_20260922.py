# -*- coding: utf-8 -*-
"""导出 lambda(N) 曲线（抽样）用于可视化 + 前沿表"""
import json
import os
from bisect import bisect_right

X = 2_000_000
STEP = 4000


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
    s = sieve(X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]

    pts = []
    argmax = (0, 0)
    missing = 0
    for N in range(4, X + 1, 2):
        lam = 0                      # 每轮必须重置：否则找不到素对时会沿用上一个 N 的值，
                                     # 静默掩盖反例（2026-09-22 修复的缺陷）
        j = bisect_right(primes, N // 2) - 1
        while j >= 0:
            p = primes[j]
            if s[N - p]:
                lam = N - p
                break
            j -= 1
        if lam == 0:
            missing += 1
            continue
        if lam > argmax[1]:
            argmax = (N, lam)
        if N % STEP == 0:
            pts.append([N, lam])
    pts.append([argmax[0], argmax[1]])

    with open(os.path.join(out_dir, "_lambda_curve.json"), "w", encoding="utf-8") as f:
        json.dump({"step": STEP, "points": pts, "argmax": list(argmax),
                   "unrepresentable_count": missing}, f)


if __name__ == "__main__":
    main()
