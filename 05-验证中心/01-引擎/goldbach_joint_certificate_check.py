# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 联合筛证书：独立复算（2026-09-22）

复算三件事，全部使用精确整数 / Fraction，无浮点：

  A. N=172 与 N=800 的 Bonferroni 型证书分量
       X      = 中央区间 (sqrt(N), N/2] 内的奇数候选
       B_p    = { m in X : p | m 或 p | (N-m) }，p 取 <= sqrt(N) 的奇素数
       S1 = sum |B_p|
       S2 = sum_{p<q} |B_p & B_q|            （全部二元组）
       S3 = sum_{p<q<r} |B_p & B_q & B_r|    （全部三元组）
       H  = 真实中央素数对数（仅用于对照，不代入下界）

  B. 检验 |X| - S1 + S2 - S3 是否为 H 的合法下界

  C. 独立重算 6 <= N <= 20000 全部偶数的 E_+/M 比值并取最大值
       定义沿用 OM-P-NT-0003-关键点_独立单侧误差界_20260920.md 第 1 节：
       I = [isqrt(N)+1, N/2]，S0 = N/2 - isqrt(N)
       p_1<...<p_k <= sqrt(N)，rho_i = 1 (p_i|N) 否则 2，alpha_i = 1 - rho_i/p_i
       D_i = K_i - (rho_i/p_i) S_{i-1}
       M   = S0 * prod alpha_i
       E_+ = sum_i max(D_i,0) * prod_{j>i} alpha_j
       这里 K_i、S_{i-1} 由真实位图筛逐点计数得到，不调用任何已有 H。

结果写入 05-验证中心/03-结果/2026/09/OM-P-NT-0003-joint-cert-20260922.json
"""
import json
import os
from fractions import Fraction
from itertools import combinations
from math import isqrt


def primes_upto(limit):
    """埃氏筛，返回 <= limit 的全部素数"""
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p::p] = bytearray(len(sieve[p * p::p]))
    return [i for i in range(2, limit + 1) if sieve[i]]


def is_prime(n, cache=None):
    if cache is not None and n in cache:
        return cache[n]
    if n < 2:
        r = False
    elif n < 4:
        r = True
    elif n % 2 == 0:
        r = False
    else:
        d = 3
        r = True
        while d * d <= n:
            if n % d == 0:
                r = False
                break
            d += 2
    if cache is not None:
        cache[n] = r
    return r


def periodic_mask(length, period, residue):
    """二进制位掩码：下标集合 { residue + k*period } ∩ [0, length)

    用 2^period 进制的循环单位数 (2^{period*n} - 1)/(2^period - 1) 直接构造，
    避免逐位循环。返回 Python int。
    """
    if residue >= length:
        return 0
    n = (length - 1 - residue) // period + 1
    base = (1 << period) - 1
    block = ((1 << (period * n)) - 1) // base
    return (block << residue) & ((1 << length) - 1)


# ---------------------------------------------------------------- A / B ------

def certificate(N, prime_cache):
    """精确计算 N 的中央候选集合上的 Bonferroni 分量"""
    y = isqrt(N)
    X = [m for m in range(y + 1, N // 2 + 1) if m % 2 == 1]
    Xset = set(X)
    ps = [p for p in primes_upto(isqrt(N)) if p % 2 == 1 and p * p <= N]

    B = {}
    for p in ps:
        victim = set()
        # m ≡ 0 (mod p) 或 m ≡ N (mod p)
        for r in {0, N % p}:
            m = r if r != 0 else p
            # 遍历该剩余类在 X 范围内的代表
            start = ((y + 1 - r + p - 1) // p) * p + r
            m = start
            while m <= N // 2:
                if m % 2 == 1:
                    victim.add(m)
                m += p
        B[p] = victim & Xset

    S1 = sum(len(B[p]) for p in ps)
    S2 = sum(len(B[p] & B[q]) for p, q in combinations(ps, 2))
    S3 = sum(len(B[p] & B[q] & B[r]) for p, q, r in combinations(ps, 3))

    H_true = sum(1 for m in X if is_prime(m, prime_cache) and is_prime(N - m, prime_cache))

    return {
        "N": N,
        "y_isqrt": y,
        "candidate_definition": "奇数 m, sqrt(N) < m <= N/2",
        "primes_used": ps,
        "|X|": len(X),
        "S1_sum_|Bp|": S1,
        "S2_all_pairs": S2,
        "S3_all_triples": S3,
        # 注意：偶数阶截断给幸存数的是【上界】，不是下界；此处仅作对照记录。
        "order2_allpairs_is_UPPER_bound": len(X) - S1 + S2,
        # 奇数阶截断（三阶全含）才是无条件下界，不依赖任何图选取。
        "order3_alltriples_LOWER_bound": len(X) - S1 + S2 - S3,
        "H_true_central": H_true,
        "arithmetic_string": "%d - %d + %d - %d = %d" % (
            len(X), S1, S2, S3, len(X) - S1 + S2 - S3),
    }


# ------------------------------------------------------------------- C ------

def scan_single(N):
    """单个偶数的 E_+/M（精确 Fraction）"""
    y = isqrt(N)
    S0 = N // 2 - y
    if S0 <= 0:
        return None
    start = y + 1
    ps = primes_upto(isqrt(N))

    full = (1 << S0) - 1
    cur = full
    alphas = []
    Ds = []
    for p in ps:
        rho = 1 if N % p == 0 else 2
        m0 = periodic_mask(S0, p, (-start) % p)
        m1 = periodic_mask(S0, p, (N - start) % p)
        mask = m0 | m1
        S_prev = cur.bit_count()
        K = (cur & mask).bit_count()
        alpha = Fraction(1) - Fraction(rho, p)
        Ds.append(Fraction(K) - Fraction(rho, p) * S_prev)
        alphas.append(alpha)
        cur = (cur & ~mask) & full

    M = Fraction(S0)
    for a in alphas:
        M *= a

    Eplus = Fraction(0)
    for i, D in enumerate(Ds):
        if D > 0:
            tail = Fraction(1)
            for a in alphas[i + 1:]:
                tail *= a
            Eplus += D * tail

    return {
        "N": N,
        "H_central": cur.bit_count(),
        "E+_over_M_str": str(Eplus / M),
        "E+_over_M_frac": [Eplus.numerator * M.denominator, Eplus.denominator * M.numerator],
        "E+_lt_M": bool(Eplus < M),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "OM-P-NT-0003-joint-cert-20260922.json")

    log_path = os.path.join(out_dir, "_joint_cert_runlog.txt")
    log = open(log_path, "w", encoding="utf-8")

    def emit(s):
        log.write(s + "\n")
        log.flush()

    result = {
        "target_id": "OM-P-NT-0003",
        "check_date": "2026-09-22",
        "arithmetic": "Fraction / 精确整数；位图筛逐点计数，不调用已有 H",
        "ai_assisted": True,
        "independent_human_review": False,
    }

    # ---- A / B: 证书分量
    prime_cache = {}
    certs = []
    for N in (172, 800):
        c = certificate(N, prime_cache)
        certs.append(c)
        emit("N=%d |X|=%d S1=%d S2=%d S3=%d" % (N, c["|X|"], c["S1_sum_|Bp|"],
                                                c["S2_all_pairs"], c["S3_all_triples"]))
        emit("   order3 lower bound = %s ; H_true = %d ; order3 <= H_true : %s"
             % (c["arithmetic_string"], c["H_true_central"],
                c["order3_alltriples_LOWER_bound"] <= c["H_true_central"]))
        emit("   order2 all-pairs value = %d is an UPPER bound ; H_true <= it : %s"
             % (c["order2_allpairs_is_UPPER_bound"],
                c["H_true_central"] <= c["order2_allpairs_is_UPPER_bound"]))
    result["certificates"] = certs

    # ---- C: 6 <= N <= 20000 全扫描
    best = None
    failures = []
    count = 0
    N = 6
    while N <= 20000:
        r = scan_single(N)
        count += 1
        if r is None:
            N += 2
            continue
        if not r["E+_lt_M"]:
            failures.append(N)
        ratio = Fraction(r["E+_over_M_frac"][0], r["E+_over_M_frac"][1])
        if best is None or ratio > best[1]:
            best = (N, ratio)
            emit("  new max: N=%d ratio=%s" % (N, r["E+_over_M_str"]))
        if N % 4000 == 0:
            emit("scanned up to %d (%d evens)" % (N, count))
        N += 2

    emit("scanned_evens=%d" % count)
    emit("max ratio N=%d value=%s" % (best[0], best[1]))
    emit("E+>=M failures: %s" % (failures[:20],))
    result["scan"] = {
        "range": "6 <= N <= 20000, 步长 2",
        "scanned_evens": count,
        "all_E+_lt_M": len(failures) == 0,
        "failure_count": len(failures),
        "max_ratio": {"N": best[0],
                      "value": str(best[1]),
                      "float_approx": float(best[1])},
    }

    log.close()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("done", flush=True)


if __name__ == "__main__":
    main()
