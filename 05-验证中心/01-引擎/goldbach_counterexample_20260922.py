# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 反证法路线：反例的等价形式 + 近反例扫描（2026-09-22）

两个此前未做的实验，全部精确整数 / 浮点仅用于诊断比值：

  A. 反例的容斥等价形式（数值验证恒等式）
     B_p = {m in X : p | m(N-m)}，X = 中央区间内奇数。
     "N 是反例" ⟺ 并集覆盖 X ⟺ 全阶容斥和恰等于 |X|：
         sum_{非空 T} (-1)^{|T|-1} A_T  ==  |X| - H_N
     本脚本对 N=172, 800, 1000 逐项枚举全部 2^k-1 个 T 验证该恒等式，
     并同时验证低阶截断（二阶/三阶）在反例判定上不可能取代全阶。

  B. 近反例扫描：谁最接近"零表示"？
     G(N)  = 无序素数对数（真值）
     R_pp(N) = sum_{p+q=N} log p log q （有序，含对角）
     S(N)  = 2C2 * prod_{p|N, p>2} (p-1)/(p-2)   （Goldbach 奇异级数）
     rho(N) = R_pp(N) / (S(N) * N)              （有限尺寸欠计比率，应趋 1）
     扫描 6<=N<=30000，记录 rho 的极小点与 G 的极小点及其算术结构
     （E/2 是否素数、不同奇素因子个数），刻画"反例若存在必须长什么样"。

输出：05-验证中心/03-结果/2026/09/OM-P-NT-0003-counterexample-20260922.json
"""
import json
import os
from itertools import combinations
from math import isqrt, log

SCAN_MAX = 30000
ANCHORS = [10 ** 5, 10 ** 6, 2 * 10 ** 6]
SIEVE_MAX = max(ANCHORS)
C2 = 0.6601618158468696


def sieve(limit):
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return s


def primes_from(s, limit):
    return [i for i in range(2, limit + 1) if s[i]]


def periodic_mask(length, period, residue):
    if residue >= length or length <= 0:
        return 0
    n = (length - 1 - residue) // period + 1
    block = ((1 << (period * n)) - 1) // ((1 << period) - 1)
    return (block << residue) & ((1 << length) - 1)


def build(N, odd_primes):
    y = isqrt(N)
    hi = N // 2
    first_odd = y + 1 if (y + 1) % 2 == 1 else y + 2
    cnt = (hi - first_odd) // 2 + 1 if first_odd <= hi else 0
    ps = [p for p in odd_primes if p <= isqrt(N)]
    masks = []
    for p in ps:
        m = 0
        for r in sorted({0, N % p}):
            res = ((r - first_odd) * pow(2, -1, p)) % p
            m |= periodic_mask(cnt, p, res)
        masks.append(m)
    return cnt, ps, masks


def inclusion_exclusion_check(N, odd_primes):
    """A: 全阶容斥 == |X| - H_N（精确整数）"""
    X, ps, masks = build(N, odd_primes)
    k = len(ps)
    # 全体存活点
    surv = (1 << X) - 1
    for m in masks:
        surv &= ~m
    H = surv.bit_count()

    total = 0
    for r in range(1, k + 1):
        for T in combinations(range(k), r):
            inter = -1
            for i in T:
                inter = masks[i] if inter < 0 else (inter & masks[i])
            total += (1 if r % 2 == 1 else -1) * inter.bit_count()

    # 低阶截断（对照）
    def partial(maxr):
        s = 0
        for r in range(1, maxr + 1):
            for T in combinations(range(k), r):
                inter = -1
                for i in T:
                    inter = masks[i] if inter < 0 else (inter & masks[i])
                s += (1 if r % 2 == 1 else -1) * inter.bit_count()
        return s

    return {
        "N": N, "|X|": X, "k_primes": k, "H_N": H,
        "full_inclusion_exclusion": total,
        "|X|_minus_H": X - H,
        "identity_holds": total == X - H,
        "partial_order2": partial(2),
        "partial_order3": partial(3),
        "note": "反例 ⟺ total == |X|（即 H=0）",
    }


def singular_series(N):
    """S(N) = 2C2 * prod_{p|N, p odd} (p-1)/(p-2)

    实现纪律（两次踩坑后定稿）：必须**先剥掉全部 2 的因子**，再用奇数 p 试除至
    p^2 > n（n 递减）。此时残留 n 必为 1 或一个奇素数，因子只在 n>1 时乘一次。
    历史缺陷：
      v1  `if n > 2:`                      —— N≡0 (mod 4) 时把残留 2^v 当素数，S 被放大；
      v2  `if n > 2 and n % 2 == 1:`       —— 残留形如 2^a·p (a>=1) 时整段漏掉，
                                              S 被低估（如 26288=2^4·31·53 漏 53，低估 2.7%）。
    见 probe_singular_series.py 对拍记录。
    """
    s = 2 * C2
    n = N
    while n % 2 == 0:
        n //= 2
    p = 3
    while p * p <= n:
        if n % p == 0:
            s *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 1:
        s *= (n - 1) / (n - 2)
    return s


def coverage_profile(N, odd_primes):
    """精确覆盖指标（不含任何奇异级数假设）：
    cover = OR 全部小素数掩码；H = |X| - |cover|；frac_covered = |cover|/|X|。
    max_covered_run = 被覆盖奇数的最长连续段；max_survivor_run = 存活奇数最长连续段。
    反例 ⟺ frac_covered == 1（等价地 max 段无存活点）。
    """
    X, ps, masks = build(N, odd_primes)
    if X <= 0:
        return None
    cover = 0
    for m in masks:
        cover |= m
    surv = ((1 << X) - 1) & ~cover
    cov_bits = cover.bit_count()
    H = surv.bit_count()
    max_cov_run = max((len(s) for s in bin(cover)[2:].split("0")), default=0)
    max_sur_run = max((len(s) for s in bin(surv)[2:].split("1")), default=0)
    return {
        "N": N, "X": X, "k_primes": len(ps), "H": H,
        "covered": cov_bits, "frac_covered": cov_bits / X,
        "max_covered_run": max_cov_run, "max_survivor_run": max_sur_run,
    }


def distinct_odd_factors(N):
    """不同奇素因子个数（同样必须先剥 2，否则残留复合数会被误计为一个因子）"""
    n = N
    while n % 2 == 0:
        n //= 2
    cnt = 0
    d = 3
    while d * d <= n:
        if n % d == 0:
            cnt += 1
            while n % d == 0:
                n //= d
        d += 2
    if n > 1:
        cnt += 1
    return cnt


def count_and_rpp(N, odd_primes, is_prime):
    """返回 (G, R_pp)。**唯一定义源，禁止在别处复写**。

    G   = 无序素数对数 #{p<=q : p+q=N, 两数皆素}
    R_pp = Σ_{有序 (p,q), p+q=N, 两数皆素} log p·log q

    权重纪律（2026-09-22 修复的缺陷）：
      p<q 的素对 → 有序对 2 个，计入 2·log p·log q；
      p=q 的素对 → 有序对 **1** 个，只计入 **1**·log²p。
    历史缺陷：旧写法在循环里对 p<=q 一律计 2·…（对角被计 2 次），
    又额外 `Rpp += log(N/2)**2`（第 3 次），故 N=2p 时对角共被计 **3** 次，
    R_pp 虚高 2·log²(N/2)。实测 [6,2000) 内 997 个偶数中 167 个偏大，
    且 167 恰为全部 N=2p；N=34 的 ρ 被抬高到 1.2009（真值 0.8656）。
    见 scratch/probe_rpp_diagonal.py。
    """
    G, Rpp = 0, 0.0
    half = N // 2
    for p in odd_primes:
        if p > half:
            break
        q = N - p
        if is_prime[q]:
            if p < q:
                G += 1
                Rpp += 2.0 * log(p) * log(q)
            else:                      # p == q == N/2（对角，有序对仅 1 个）
                G += 1
                Rpp += log(p) * log(p)
    return G, Rpp


def rpp_by_full_enumeration(N, is_prime):
    """独立路径：显式枚举**全部**有序对（p 从 2 到 N-2），用于自检"""
    tot = 0.0
    for p in range(2, N - 1):
        if is_prime[p] and is_prime[N - p]:
            tot += log(p) * log(N - p)
    return tot


def rpp_selfcheck(is_prime, sample_N):
    """对抽样 N 断言 count_and_rpp 与全枚举一致（不一致即逐条列出）"""
    odd_primes = [p for p in range(3, max(sample_N) + 1) if is_prime[p]]
    bad = []
    for N in sample_N:
        if N < 6:
            continue
        _, a = count_and_rpp(N, odd_primes, is_prime)
        b = rpp_by_full_enumeration(N, is_prime)
        # 用**相对**容差：两条路径的加法顺序不同，N=10^6 量级会有 ~1e-14 的相对舍入差，
        # 绝对容差 1e-9 会把这类噪声误报为"不一致"。
        if abs(a - b) > 1e-11 * max(1.0, abs(b)):
            bad.append((N, a, b))
    return bad


def scan(np_sieve, odd_primes):
    """B: 近反例扫描（含精确覆盖指标）"""
    prime_set = set(odd_primes) | {2}
    worst_rho = None            # 最小 rho
    worst_rho_large = None      # 1e4 以上最小 rho
    min_G_above_1e4 = None      # 1e4 以上 G 的极小
    max_cover = None            # 全区间最大 frac_covered（精确）
    max_cover_above_1e4 = None  # 1e4 以上最大 frac_covered
    max_cover_run_above_1e4 = None
    per_decade = {}
    zero_counterexamples = []

    N = 6
    while N <= SCAN_MAX:
        G, Rpp = count_and_rpp(N, odd_primes, np_sieve)
        if G == 0:
            zero_counterexamples.append(N)

        S = singular_series(N)
        rho = Rpp / (S * N) if N > 6 else None

        cp = coverage_profile(N, odd_primes)
        if cp is not None:
            rec = (N, cp["frac_covered"], cp["H"], cp["X"],
                   cp["max_covered_run"], distinct_odd_factors(N),
                   (N // 2) in prime_set, round(S, 4))
            if max_cover is None or cp["frac_covered"] > max_cover[1]:
                max_cover = rec
            if N >= 10 ** 4:
                if max_cover_above_1e4 is None or cp["frac_covered"] > max_cover_above_1e4[1]:
                    max_cover_above_1e4 = rec
                if max_cover_run_above_1e4 is None or cp["max_covered_run"] > max_cover_run_above_1e4[4]:
                    max_cover_run_above_1e4 = rec

        if N >= 10 ** 4:
            if min_G_above_1e4 is None or G < min_G_above_1e4[1]:
                min_G_above_1e4 = (N, G, distinct_odd_factors(N), (N // 2) in prime_set,
                                   round(S, 4), round(rho, 4) if rho else None)
        if rho is not None and (worst_rho is None or rho < worst_rho[1]):
            worst_rho = (N, rho, G, distinct_odd_factors(N), (N // 2) in prime_set,
                         round(S, 4))
        if rho is not None and N >= 10 ** 4:
            if worst_rho_large is None or rho < worst_rho_large[1]:
                worst_rho_large = (N, rho, G, distinct_odd_factors(N),
                                   (N // 2) in prime_set, round(S, 4))

        dec = 10 ** (len(str(N)) - 1)
        per_decade.setdefault(dec, []).append(
            (rho if rho else 0.0, N, distinct_odd_factors(N),
             (N // 2) in prime_set, round(S, 4),
             cp["frac_covered"] if cp else 0.0, G))
        N += 2

    anchors = []
    for A in ANCHORS:
        G, Rpp = count_and_rpp(A, odd_primes, np_sieve)
        S = singular_series(A)
        anchors.append({"N": A, "G": G, "S": round(S, 4),
                        "rho": round(Rpp / (S * A), 4),
                        "distinct_odd_factors": distinct_odd_factors(A)})

    dec_stats = []
    for dec in sorted(per_decade):
        rows = [r for r in per_decade[dec] if r[0] > 0]
        if rows:
            vals = sorted(r[0] for r in rows)
            argmin = min(rows, key=lambda r: r[0])
            argmaxcov = max(rows, key=lambda r: r[5])
            argminG = min(rows, key=lambda r: r[6])
            dec_stats.append({
                "decade": dec, "count": len(rows),
                "min_rho": round(vals[0], 4),
                "median_rho": round(vals[len(vals) // 2], 4),
                "max_rho": round(vals[-1], 4),
                "argmin_N": argmin[1],
                "argmin_rho": round(argmin[0], 4),
                "argmin_N_over_2_is_prime": argmin[3],
                "argmin_distinct_odd_factors": argmin[2],
                "argmin_S": argmin[4],
                "max_frac_covered": round(argmaxcov[5], 6),
                "max_frac_covered_at_N": argmaxcov[1],
                "min_G": argminG[6],
                "min_G_at_N": argminG[1],
            })

    def pack(rec):
        if rec is None:
            return None
        return {"N": rec[0], "frac_covered": round(rec[1], 6), "H": rec[2],
                "X": rec[3], "max_covered_run": rec[4],
                "distinct_odd_factors": rec[5], "N_over_2_is_prime": rec[6],
                "S": rec[7]}

    return {
        "scan_range": "6 <= N <= %d" % SCAN_MAX,
        "counterexamples_found": zero_counterexamples,
        "min_rho": {"N": worst_rho[0], "rho": round(worst_rho[1], 4),
                    "G": worst_rho[2], "distinct_odd_factors": worst_rho[3],
                    "N_over_2_is_prime": worst_rho[4], "S": worst_rho[5]},
        "min_rho_above_1e4": (
            {"N": worst_rho_large[0], "rho": round(worst_rho_large[1], 4),
             "G": worst_rho_large[2], "distinct_odd_factors": worst_rho_large[3],
             "N_over_2_is_prime": worst_rho_large[4],
             "S": worst_rho_large[5]} if worst_rho_large else None),
        "min_G_above_1e4": {"N": min_G_above_1e4[0], "G": min_G_above_1e4[1],
                            "distinct_odd_factors": min_G_above_1e4[2],
                            "N_over_2_is_prime": min_G_above_1e4[3],
                            "S": min_G_above_1e4[4], "rho": min_G_above_1e4[5]},
        "max_frac_covered": pack(max_cover),
        "max_frac_covered_above_1e4": pack(max_cover_above_1e4),
        "max_covered_run_above_1e4": pack(max_cover_run_above_1e4),
        "decades": dec_stats,
        "anchors": anchors,
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-counterexample-20260922.json")
    log_path = os.path.join(out_dir, "_counterexample_runlog.txt")

    np_sieve = sieve(SIEVE_MAX + 10)
    odd_primes = [p for p in primes_from(np_sieve, SIEVE_MAX) if p > 2]

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "ai_assisted": True, "independent_human_review": False,
           "arithmetic": "容斥部分精确整数；比值用浮点仅作诊断"}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(s):
            log.write(s + "\n")
            log.flush()

        emit("== A0: R_pp 实现自检（count_and_rpp vs 全枚举有序对） ==")
        sample_N = list(range(6, 400, 2)) + [10 ** 4, 2 * 10 ** 4, 10 ** 5, 10 ** 6]
        bad = rpp_selfcheck(np_sieve, sample_N)
        emit("抽样 %d 个 N；不一致 %d 个 %s" % (len(sample_N), len(bad), bad[:5]))
        out["rpp_selfcheck"] = {"sampled": len(sample_N), "mismatch_count": len(bad),
                                "mismatch_head": bad[:5],
                                "note": "对角权重=1（有序定义）；旧版在 N=2p 上多计 2·log²(N/2)"}

        emit("== A: 反例的容斥等价形式 ==")
        A = [inclusion_exclusion_check(N, odd_primes) for N in (172, 800, 1000)]
        for r in A:
            emit(json.dumps(r, ensure_ascii=False))
        out["inclusion_exclusion"] = A

        emit("== B: 近反例扫描 ==")
        B = scan(np_sieve, odd_primes)
        emit(json.dumps(B, ensure_ascii=False))
        out["near_counterexample_scan"] = B

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
