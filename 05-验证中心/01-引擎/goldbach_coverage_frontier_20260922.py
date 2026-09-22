# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 前缀覆盖前沿（coverage frontier）精确核算（2026-09-22）

用户提出的机制：把"用不超过 q 的素数能生成的最大和值 2q"与
"用不超过 q 的素数能**连续覆盖**到的最大偶数 C(q)"严格区分。

本脚本给出三条互相独立的计算：
  P0  验证用户的 31 前缀反例：primes<=31 时覆盖集恰为 {4..54}∪{58,60,62}，缺 56。
  P1  lambda(N) = min{ max(p,q) : p+q=N, p<=q 素数 }
      = N - max{ p <= N/2 : p, N-p 均为素数 }   （"该偶数最早需要用到多大的素数"）
      对全部偶数 4<=N<=2e6 精确计算；由此导出
        连续覆盖前沿 C(q) = max{ N 偶数 : max_{m<=N} lambda(m) <= q }
      （算法 B：lambda 路径）
  P2  独立核对（算法 A：前缀和集位运算）
      C_A(q) = 用 primes<=q 两两求和，取从 4 起连续覆盖的最大偶数
      与算法 B 在 q ∈ {31,37,101,1009,10007,100003} 上逐点对拍。

全部精确整数；无浮点统计。报告与用户给定数字（1,000,537 / 339 / 78,498 / 999,999）的核对结果。
输出：05-验证中心/03-结果/2026/09/OM-P-NT-0003-coverage-frontier-20260922.json
"""
import json
import os
from bisect import bisect_right

X = 2_000_000
CHECK_Q = [31, 37, 101, 1009, 10007, 100003]
STAT_Q = [31, 37, 101, 1009, 10007, 100003, 500009, 999983, 1_000_000,
          1_000_537, 1_500_000, 1_999_999, 2_000_000]


def sieve(limit):
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, int(limit ** 0.5) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return s


def C_by_prefix_sumset(q, primes):
    """算法 A：用 primes<=q 两两求和的位掩码，取从 4 连续覆盖的最大偶数"""
    ps = [p for p in primes if p <= q]
    if not ps:
        return 0
    top = 2 * q
    ba = bytearray((top >> 3) + 2)
    for p in ps:
        ba[p >> 3] |= 1 << (p & 7)
    pm = int.from_bytes(ba, "little")
    cov = 0
    for p in ps:
        cov |= pm << p
    cov &= (1 << (top + 1)) - 1
    em = ((1 << (top + 2)) - 16) // 3          # 位置 4,6,...,top
    unc = (~cov) & em
    if unc == 0:
        return top
    cb = unc.to_bytes((top >> 3) + 2, "little")
    for n in range(4, top + 1, 2):
        if (cb[n >> 3] >> (n & 7)) & 1:
            return n - 2
    return top


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-coverage-frontier-20260922.json")
    log_path = os.path.join(out_dir, "_coverage_frontier_runlog.txt")

    s = sieve(X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "ai_assisted": True, "independent_human_review": False,
           "X": X, "method": "前缀覆盖前沿 lambda(N) + 独立位运算对拍",
           "arithmetic": "全部精确整数"}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        # ---------- P0：验证用户 31 前缀反例 ----------
        small = [p for p in primes if p <= 31]
        sums31 = set()
        for i, a in enumerate(small):
            for b in small[i:]:
                sums31.add(a + b)
        evens31 = sorted(v for v in sums31 if v % 2 == 0)
        top31 = 2 * 31
        gaps31 = [n for n in range(4, top31 + 1, 2) if n not in sums31]
        p0 = {
            "primes_used": small, "p_max": 31, "max_reachable_sum": top31,
            "covered_evens": evens31,
            "gaps_within_4_to_2p": gaps31,
            "claim_56_unsatisfiable_check": {
                "why": "56 的表示 a+b 需 a>=56-31=25；[25,31] 内素数只有 29,31；"
                       "且 a,b 同为奇数时 a+b>=58>56（若含 2 则 a+b<=33）",
                "min_largest_prime_for_56": 37,
                "witness": "56 = 19 + 37（37>31，故 31 前缀内不可能覆盖）",
            },
        }
        emit("== P0: primes<=31 的覆盖集与缺口 ==")
        emit(json.dumps(p0, ensure_ascii=False))
        out["p0_prefix31"] = p0

        # ---------- P1：lambda(N) 全表 ----------
        lam = [0] * (X // 2 + 1)               # 索引 N//2
        missing = []
        for N in range(4, X + 1, 2):
            j = bisect_right(primes, N // 2) - 1
            got = 0
            while j >= 0:
                p = primes[j]
                if s[N - p]:
                    got = N - p
                    break
                j -= 1
            lam[N // 2] = got
            if got == 0:
                missing.append(N)

        events = []
        run = 0
        for N in range(4, X + 1, 2):
            v = lam[N // 2]
            if v > run:
                run = v
                events.append([N, v, N - v])   # (N, lambda, 较小素因子)
        T = run
        cnt_eq_T = sum(1 for i in range(2, X // 2 + 1) if lam[i] == T)
        cnt_gt_1e6 = sum(1 for i in range(2, X // 2 + 1) if lam[i] > 10 ** 6)
        cnt_ge_1e6 = sum(1 for i in range(2, X // 2 + 1) if lam[i] >= 10 ** 6)
        argmax = [2 * i for i in range(2, X // 2 + 1) if lam[i] == T]

        # events 的 v 严格递增 ⇒ 可二分（老版是 O(len(events)) 线性扫描）
        ev_v = [e[1] for e in events]
        ev_N = [e[0] for e in events]

        def C_of_q(q):
            j = bisect_right(ev_v, q) - 1
            if j < 0:
                return 2
            return ev_N[j + 1] - 2 if j + 1 < len(ev_N) else X

        stat = []
        for q in STAT_Q:
            C = C_of_q(q)
            stat.append({"q": q, "C_q": C, "2q": 2 * q,
                         "deficit_2q_minus_C": 2 * q - C,
                         "ratio_C_over_2q": round(C / (2 * q), 6)})

        p1 = {
            "evens_checked": (X - 4) // 2 + 1,
            "unrepresentable_evens": missing[:20],
            "unrepresentable_count": len(missing),
            "max_lambda_T": T,
            "argmax_N_list_len": len(argmax),
            "argmax_N_smallest": argmax[0] if argmax else None,
            "argmax_N_largest": argmax[-1] if argmax else None,
            "count_lambda_eq_T": cnt_eq_T,
            "count_lambda_gt_1e6": cnt_gt_1e6,
            "count_lambda_ge_1e6": cnt_ge_1e6,
            "advancement_event_count": len(events),
            "first_events": events[:12],
            "last_events": events[-12:],
            "frontier_table": stat,
            "pi_1e6": sum(1 for p in primes if p <= 10 ** 6),
        }
        emit("== P1: lambda(N) 全表与前沿 ==")
        emit(json.dumps(p1, ensure_ascii=False))
        out["p1_lambda"] = p1

        # ---------- P2：算法 A 对拍 ----------
        cross = []
        for q in CHECK_Q:
            cA = C_by_prefix_sumset(q, primes)
            cB = C_of_q(q)
            cross.append({"q": q, "C_algorithmA_prefix_sumset": cA,
                          "C_algorithmB_lambda_path": cB, "agree": cA == cB})
        emit("== P2: 两算法对拍 ==")
        emit(json.dumps(cross, ensure_ascii=False))
        out["p2_cross_check"] = cross

        # ---------- P3：与用户给定数字核对 ----------
        claim = {
            "pi_1e6_claim_78498":
                {"claimed": 78498, "computed": p1["pi_1e6"],
                 "match": p1["pi_1e6"] == 78498},
            "evens_4_to_2e6_claim_999999":
                {"claimed": 999999, "computed": p1["evens_checked"],
                 "match": p1["evens_checked"] == 999999},
            "threshold_claim_1000537":
                {"claimed": 1000537, "computed": T, "match": T == 1000537},
            "certificates_claim_339":
                {"claimed": 339,
                 "candidates": {"count_lambda_eq_T": cnt_eq_T,
                                "count_lambda_gt_1e6": cnt_gt_1e6,
                                "count_lambda_ge_1e6": cnt_ge_1e6},
                 "match_any_aggregate": 339 in (cnt_eq_T, cnt_gt_1e6, cnt_ge_1e6),
                 "which": [k for k, v in (("eq_T", cnt_eq_T),
                                          ("gt_1e6", cnt_gt_1e6),
                                          ("ge_1e6", cnt_ge_1e6)) if v == 339],
                 # ↓ 2026-09-22 破译（见 OM-P-NT-0003-certificate-339-decode-20260922.json）：
                 #   339 不是任何"沿 N 的聚合计数"，而是**单点证书窗口内的奇数个数**
                 #       = δ(N_T)/2，其中 δ(N)=λ(N)−N/2，N_T = argmax λ。
                 #   旧版只查聚合口径，故此处恒为 False，已造成误导；现补上正确口径。
                 "decoded_single_point": {
                     "N_T": argmax[0] if argmax else None,
                     "T": T,
                     "delta_T_minus_half": (T - argmax[0] // 2) if argmax else None,
                     "window_odd_count": ((T - argmax[0] // 2) // 2) if argmax else None,
                     "match": bool(argmax) and (T - argmax[0] // 2) // 2 == 339,
                     "note": "证书窗口 (N_T−T, N_T/2] 的奇数个数；偶数位自动被 2 整除故折半",
                 },
                 "match": bool(argmax) and (T - argmax[0] // 2) // 2 == 339},
        }
        emit("== P3: 与用户数字核对 ==")
        emit(json.dumps(claim, ensure_ascii=False))
        out["p3_claim_check"] = claim

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
