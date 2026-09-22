# -*- coding: utf-8 -*-
"""对拍 S(N) 实现：现用版 vs 独立全因子版（穷举所有 d 试除）

⚠️ 历史与现状（2026-09-22 修订）：
  原版把 `cur` 写成 `if n > 2 and n % 2 == 1:` —— 那是**已被否证的 v2 缺陷实现**
  （残留形如 2^a·p 时整段漏掉，S 被低估），却被命名为"现用实现"，会误导后来者。
  现已把 `cur` 改为**与引擎一致的最终实现**（先剥 2 → 奇数试除 → n>1 才乘），
  并把 v1/v2 两个缺陷实现保留为 `defect_v1 / defect_v2` 供回归对照。
  同时改为**写文件**输出（本环境 PowerShell 不回显 stdout，print 型探针等于没有输出）。

用法：python probe_singular_series.py [输出路径]
"""
import os
import sys
from math import isqrt

C2 = 0.6601618158468696


def cur(N):
    """现用实现（与 goldbach_counterexample_20260922.py::singular_series 逐字一致）"""
    s = 2 * C2
    n = N
    while n % 2 == 0:            # 必须先剥掉全部 2 的因子
        n //= 2
    p = 3
    while p * p <= n:
        if n % p == 0:
            s *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 1:                    # 残留为 1 或一个奇素数，只在 >1 时乘一次
        s *= (n - 1) / (n - 2)
    return s


def defect_v1(N):
    """历史缺陷 v1：不剥 2，N≡0 (mod 4) 时把残留 2^v 当成素数因子 → S 放大"""
    s = 2 * C2
    n = N
    p = 3
    while p * p <= n:
        if n % p == 0:
            s *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 2:
        s *= (n - 1) / (n - 2)
    return s


def defect_v2(N):
    """历史缺陷 v2：残留形如 2^a·p (a>=1) 时整段漏掉 → S 低估"""
    s = 2 * C2
    n = N
    p = 3
    while p * p <= n:
        if n % p == 0:
            s *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 2 and n % 2 == 1:
        s *= (n - 1) / (n - 2)
    return s


def ref(N):
    """独立版：先剥 2，再全试除（含偶数 d，保证残留为 1 或素数）"""
    s = 2 * C2
    n = N
    while n % 2 == 0:
        n //= 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            s *= (d - 1) / (d - 2)
            while n % d == 0:
                n //= d
        d += 2
    if n > 1:
        s *= (n - 1) / (n - 2)
    return s


def factors(N):
    n = N
    out = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        out.append(n)
    return out


TESTS = [12, 68, 128, 152, 632, 1112, 1412, 9602, 10006, 13892, 26288, 27908,
         100000, 1000000, 2000000]


def main():
    out_path = (sys.argv[1] if len(sys.argv) > 1
                else r"D:\a10\aikjx\code\my_lib\scratch\_probe_singular_series.txt")
    lines = ["%-9s %-20s %-12s %-12s %-10s %-12s %-12s" %
             ("N", "全素因子", "cur==ref", "diff", "v1偏差", "v2偏差", "备注")]
    n_cur_bad = n_v1 = n_v2 = 0
    for N in TESTS:
        c, r = cur(N), ref(N)
        d1, d2 = defect_v1(N) - r, defect_v2(N) - r
        ok = abs(c - r) < 1e-12
        if not ok:
            n_cur_bad += 1
        if abs(d1) > 1e-12:
            n_v1 += 1
        if abs(d2) > 1e-12:
            n_v2 += 1
        lines.append("%-9s %-20s %-12s %-12.2e %-10.2e %-12.2e %s" %
                     (N, str(factors(N)), ok, c - r, d1, d2,
                      "" if ok else "cur 与 ref 不一致!"))
    lines.append("")
    lines.append("结论：cur==ref 失败 %d 个（应为 0）；"
                 "v1 有偏差 %d 个；v2 有偏差 %d 个（两者均为历史缺陷实现，保留作反面记录）"
                 % (n_cur_bad, n_v1, n_v2))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
