# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 生成式（和集覆盖）填满实验（2026-09-22）

裁定两条读法：
  读法1：令 S_X = { p+q : p<=q 素数, p+q <= X }，问 S_X ⊇ 2Z∩[4,X]（是否所有偶数被"填满"）。
  读法2："两个最大素数之和" 与 "需填充范围上端" 比较，能否保证填满。

核心事实（逐项量化）：
  * 生成视角与逐点视角是同一命题的两种写法（S_X ⊇ 2Z∩[4,X] ⟺ 无反例 ≤ X），
    不是两条独立证明路线；但生成视角在计算上更优（4e18 验证用的就是它）。
  * "两个最大素数之和 ≈ 1~2 × X" 对每个 X 都成立，属恒真条件，无判别力。
  * 取最大的 k 个素数，其和集被限制在顶端一个窄窗口内，窗口下方一个偶数都覆盖不到。
  * 加法组合学障碍：素数集密度为 0，Schnirelmann 型"A+A 覆盖"定理不适用；
    真正可闭合的是阶 4（Helfgott 三元 + 3），而阶 2 就是猜想本身。

全部精确整数（位运算），无浮点假设。
输出：05-验证中心/03-结果/2026/09/OM-P-NT-0003-generation-fill-20260922.json
"""
import json
import os
from bisect import bisect_left, bisect_right
from math import isqrt

X_LIST = [10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6]
SIEVE_MAX = max(X_LIST) + 10
TOP_K_LIST = (2, 5, 10, 50, 100, 500, 2000)


def sieve(limit):
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return s


def primes_from(s, limit):
    return [i for i in range(2, limit + 1) if s[i]]


def bitmask_of(vals, top):
    """把 vals 中的位置置 1，返回长度 top+1 位的大整数（低位=0 号位置）"""
    ba = bytearray((top >> 3) + 2)
    for v in vals:
        if v <= top:
            ba[v >> 3] |= 1 << (v & 7)
    return int.from_bytes(ba, "little")


def even_mask(X):
    """位置 4,6,8,...,X 全置 1（X 偶数）。Σ_{j=2}^{X/2} 4^j = (2^(X+2)-16)/3"""
    assert X % 2 == 0 and X >= 4
    return ((1 << (X + 2)) - 16) // 3


def build_covered(X, primes_le_X):
    """covered = OR_{p<=X/2} (pm << p)，截断到 <= X；返回 (covered, bytes)"""
    pm = bitmask_of(primes_le_X, X)
    limit = (1 << (X + 1)) - 1
    covered = 0
    half = X // 2
    for p in primes_le_X:
        if p > half:
            break
        covered |= pm << p
    covered &= limit
    cb = covered.to_bytes((X >> 3) + 2, "little")
    return covered, cb


def bitat(cb, n):
    return (cb[n >> 3] >> (n & 7)) & 1


def fill_check(X, primes_le_X):
    covered, cb = build_covered(X, primes_le_X)
    em = even_mask(X)
    cov_even = (covered & em).bit_count()
    total_even = X // 2 - 1                  # 4,6,...,X 共 X/2-1 个
    unc = (~covered) & em
    head = []
    if unc:
        for n in range(4, X + 1, 2):
            if not bitat(cb, n):
                head.append(n)
                if len(head) >= 10:
                    break
    pl_half_idx = bisect_right(primes_le_X, X // 2)
    return {
        "X": X, "total_even_in_range": total_even, "covered_even": cov_even,
        "coverage_ratio": cov_even / total_even,
        "uncovered_count": unc.bit_count(),
        "uncovered_head": head,
        "all_filled": unc == 0,
        "p_max_le_X_over_2": primes_le_X[pl_half_idx - 1],
        "top2_sum_within_X_over_2": primes_le_X[pl_half_idx - 1] + primes_le_X[pl_half_idx - 2],
        "top2_sum_minus_X": (primes_le_X[pl_half_idx - 1] + primes_le_X[pl_half_idx - 2]) - X,
        "two_largest_primes_le_X": [primes_le_X[-1], primes_le_X[-2]],
        "their_sum": primes_le_X[-1] + primes_le_X[-2],
        "their_sum_minus_X": primes_le_X[-1] + primes_le_X[-2] - X,
    }


def top_sum_analysis(X, primes_le_X):
    half = X // 2
    idx = bisect_right(primes_le_X, half)
    ps = primes_le_X[:idx]
    pairs = 0
    for p in ps:
        lo = bisect_left(primes_le_X, p)
        hi = bisect_right(primes_le_X, X - p)
        if hi > lo:
            pairs += hi - lo
    p1 = ps[-1]
    rows = []
    for k in TOP_K_LIST:
        if k > len(ps):
            continue
        sel = ps[-k:]
        sums = set()
        for i, a in enumerate(sel):
            for b in sel[i:]:
                v = a + b
                if v <= 2 * p1:
                    sums.add(v)
        lo_, hi_ = min(sums), max(sums)
        rows.append({
            "k_largest_primes": k,
            "window_min": lo_, "window_max": hi_,
            "window_width": hi_ - lo_,
            "distinct_evens_covered": len(sums),
            "fraction_of_4_to_2p_max": round(len(sums) / ((2 * p1) // 2 - 1), 8),
        })
    sset_even = set()
    restricted_head = []
    if len(ps) <= 6000:                      # O(k^2) 保护：X=1e6 时 k=41538 不可枚举
        for i, a in enumerate(ps):
            for b in ps[i:]:
                v = a + b
                if v % 2 == 0 and v <= 2 * p1:
                    sset_even.add(v)
        for v in range(4, 2 * p1 + 1, 2):
            if v not in sset_even:
                restricted_head.append(v)
                if len(restricted_head) >= 12:
                    break
    evens_in_range = p1 - 1                  # [4, 2p1] 内偶数个数 = (2p1-4)/2+1 = p1-1
    return {
        "X": X, "pairs_p_le_q_p_plus_q_le_X": pairs,
        "primes_le_X_over_2": len(ps),
        "p_max_le_X_over_2": p1, "p_prev": ps[-2],
        "top_k_window_analysis": rows,
        "restricted_generation_note": (
            "以下指标刻意限制生成集为 p<=X/2 的素数两两求和；因上端偶数可能需要一个 >X/2 "
            "的素因子，故 [4,2p_max] 顶端会留空隙——这是'限制生成集必留空隙'的直接见证，"
            "与下方 fill_check（用 p<=X 的全部素数）给出的 100% 覆盖是两回事。"),
        "restricted_distinct_even_sums_up_to_2p_max": (
            len(sset_even) if sset_even else "skipped_too_large"),
        "evens_in_range_4_to_2p_max": evens_in_range,
        "restricted_even_coverage_ratio": (
            round(len(sset_even) / evens_in_range, 8) if sset_even else None),
        "restricted_uncovered_evens_head": restricted_head,
    }


def order_distribution(X, cb, is_prime):
    """加法基阶数 ord(n)（允许重复），偶数 n<=X：
       ord<=2 iff n 为两素数和（covered）；
       ord<=3 iff n-2 为两素数和（形态 2+p+q），或 n-4 为素数（形态 2+2+p）；
       其余 ord<=4（Helfgott：n=3+(n-3)，n-3 为 >=7 奇数 = 3 素数）。"""
    dist = {2: 0, 3: 0, 4: 0}
    ex3, ex4 = [], []
    for n in range(4, X + 1, 2):
        if bitat(cb, n):
            dist[2] += 1
        elif bitat(cb, n - 2) or (n - 4 >= 3 and is_prime[n - 4]):
            dist[3] += 1
            if len(ex3) < 5:
                ex3.append(n)
        else:
            dist[4] += 1
            if len(ex4) < 5:
                ex4.append(n)
    return {"range": "4..%d (偶数)" % X, "ord2": dist[2], "ord3": dist[3],
            "ord4": dist[4], "examples_ord3": ex3, "examples_ord4": ex4}


def independent_dp_check(N, primes_upto_N, cb):
    """独立路径：DP 求最小素数个数（允许重复），与位图路径交叉验证"""
    INF = 99
    best = [INF] * (N + 1)
    best[0] = 0
    for n in range(2, N + 1):
        b = INF
        for p in primes_upto_N:
            if p > n:
                break
            if best[n - p] + 1 < b:
                b = best[n - p] + 1
        best[n] = b
    mism = [n for n in range(4, N + 1, 2) if (best[n] == 2) != bool(bitat(cb, n))]
    return {"N": N, "checked_even": len(range(4, N + 1, 2)),
            "dp_ord2_count": sum(1 for n in range(4, N + 1, 2) if best[n] == 2),
            "dp_ord3_count": sum(1 for n in range(4, N + 1, 2) if best[n] == 3),
            "mismatch_count": len(mism), "mismatch_head": mism[:10]}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-generation-fill-20260922.json")
    log_path = os.path.join(out_dir, "_generation_fill_runlog.txt")

    s = sieve(SIEVE_MAX)
    all_primes = primes_from(s, SIEVE_MAX)

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "ai_assisted": True, "independent_human_review": False,
           "method": "生成式和集覆盖（精确整数位运算）",
           "arithmetic": "全部精确整数，无浮点假设"}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        emit("== 读法1：生成式填满检查 S_X ⊇ 2Z∩[4,X] ==")
        fills = []
        for X in X_LIST:
            pl = [p for p in all_primes if p <= X]
            r = fill_check(X, pl)
            fills.append(r)
            emit(json.dumps(r, ensure_ascii=False))
        out["fill_check"] = fills

        emit("== 读法2：最大素数和 vs 填充范围 + 顶端 k 个素数的窗口 ==")
        tsa = []
        for X in X_LIST:
            pl = [p for p in all_primes if p <= X]
            r = top_sum_analysis(X, pl)
            tsa.append(r)
            emit(json.dumps(r, ensure_ascii=False))
        out["top_sum_analysis"] = tsa

        emit("== 加法基阶数分布（偶数 4..1e6） ==")
        X = 10 ** 6
        pl = [p for p in all_primes if p <= X]
        _, cb = build_covered(X, pl)
        o = order_distribution(X, cb, s)
        emit(json.dumps(o, ensure_ascii=False))
        out["order_distribution"] = o

        emit("== 独立路径交叉验证（DP 最小素数个数，N<=2000） ==")
        N = 2000
        plN = [p for p in all_primes if p <= N]
        d = independent_dp_check(N, plN, cb)
        emit(json.dumps(d, ensure_ascii=False))
        out["dp_crosscheck"] = d

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
