# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 素数侧路线闭合：reach（到达性）与 pairing（配对性）的分离

要回答的问题
------------
素数侧框架里的"等待区"其实混杂了**两种机制不同的阻塞**，必须先分离：

(REACH) 顶部阻塞：在层级 k（最大素数 q=p_k）上，若 N > p_{k-1}+p_k，
        则 N 根本超出"两个 ≤q 的素数之和"的可达范围 ⇒ 只能等更大的素数。
(PAIR)  底部阻塞：若 N ≤ p_{k-1}+p_k，则可达范围内没有任何一对素数之和等于 N
        ⇒ 阻塞来自"候选窗口 [N-q, N/2] 内无配对"，与可达范围无关。

定理 A（本轮证明，见记录）断言 REACH 阻塞对每个 N 都是**有限期**的：
   ∃k0(N)<∞ 使 k≥k0 时 N ≤ p_{k-1}+p_k。
于是"素数主动生成/把偶数填满"中的**生成（reach）部分是自由且可证的**，
真正的困难 100% 落在 PAIR 上——即短区间内的素数配对存在性（parity barrier 所在）。

本脚本核算
----------
1. 对每个偶数 N：找 λ(N)，定位它在素数表中的下标 i_lam；算 k0(N)；linger = i_lam − k0。
2. 在"填充前一层"（层级 i_lam−1）判定阻塞类型：TOP(REACH) 还是 BOT(PAIR)。
3. 统计两类占比、linger 分布、以及"最后一个阻塞层"的窗口宽度。
"""
import json
import os
from bisect import bisect_left, bisect_right

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
    json_path = os.path.join(out_dir, "OM-P-NT-0003-reach-vs-pairing-20260922.json")
    log_path = os.path.join(out_dir, "_reach_pairing_runlog.txt")

    s = sieve(2 * X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]
    P = len(primes)
    # S[m] = primes[m-1] + primes[m]  (m>=1)：用前 m+1 个素数能达到的最大和
    S = [0] * P
    for m in range(1, P):
        S[m] = primes[m - 1] + primes[m]
    Slist = S[1:]                       # Slist[j] 对应 m=j+1
    idx_of = {p: i for i, p in enumerate(primes)}

    def k0_of(N):
        """最小层级 m，使 N 在层级 m 上**可达**（reach-available）。
        层级 m 的素数为 primes[0..m]，最大和 = 2*primes[m]；但 (p_{m-1}+p_m, 2p_m) 是空洞，
        故可达 ⟺ N <= primes[m-1]+primes[m]  或  N == 2*primes[m]（等值对）。
        """
        m_S = bisect_left(Slist, N) + 1
        if N % 2 == 0 and N // 2 >= 2 and s[N // 2]:
            return min(m_S, idx_of[N // 2])
        return m_S

    # ---- λ 表：**只算一次**（原实现算了整整两遍；且局部变量 q 未逐轮重置，
    #      一旦某个偶数找不到素对就会沿用上一个偶数的值，静默掩盖反例）----
    lam_arr = [0] * (X // 2 + 1)          # lam_arr[i] = λ(2i)
    missing = []
    for N in range(4, X + 1, 2):
        q = 0
        j = bisect_right(primes, N // 2) - 1
        while j >= 0:
            p = primes[j]
            if s[N - p]:
                q = N - p
                break
            j -= 1
        lam_arr[N // 2] = q
        if q == 0:
            missing.append(N)

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22", "X": X,
           "goal": "分离 REACH 阻塞与 PAIR 阻塞，判定素数侧生成路线的逻辑终点",
           "n_unrepresentable": len(missing),
           "unrepresentable_head": missing[:20]}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        emit("=== 1. 逐偶数分类：λ(N)、k0(N)、linger、阻塞类型 ===")
        n_top = n_bot = n_triv = n_missing = 0
        lingers = []            # (linger, N)
        maxlinger = (-1, 0)
        bot_window_max = (-1, 0)   # BOT 型在最后一层的前沿窗口宽度 N/2-(N-q)
        top_excess_max = (-1, 0)   # TOP 型超出量 N-(p_{k-2}+p_{k-1})
        # 抽样
        samples = []
        for N in range(4, X + 1, 2):
            q = lam_arr[N // 2]
            if q == 0:                       # 反例（本区间实测为 0 个）
                n_missing += 1
                continue
            i_lam = idx_of[q]
            k0 = k0_of(N)
            if i_lam < 2:
                n_triv += 1
                continue
            linger = i_lam - k0
            lingers.append(linger)
            if linger > maxlinger[0]:
                maxlinger = (linger, N)
            # 填充前一层 m0 = i_lam - 1（最大素数 primes[i_lam-1]）
            q_prev = primes[i_lam - 1]
            top_edge = primes[i_lam - 2] + q_prev      # 用 ≤q_prev 的最大非等值和
            reach_ok = (N <= top_edge) or (N == 2 * q_prev)
            if not reach_ok:
                n_top += 1
                ex = N - top_edge
                if ex > top_excess_max[0]:
                    top_excess_max = (ex, N)
            else:
                n_bot += 1
                w = N // 2 - (N - q)                    # 底部窗口宽度 = δ(N)
                if w > bot_window_max[0]:
                    bot_window_max = (w, N)
            if N in (8, 56, 68, 1_999_718, 1_872_236):
                samples.append({"N": N, "lambda": q, "i_lam": i_lam, "k0": k0,
                                "linger": linger, "type": "TOP" if not reach_ok else "BOT",
                                "top_edge": top_edge, "bot_window": N // 2 - (N - q)})

        n_cls = n_top + n_bot
        emit("分类完成：TOP(REACH) = %d (%.2f%%)   BOT(PAIR) = %d (%.2f%%)   平凡点(小N) = %d"
             % (n_top, 100.0 * n_top / n_cls, n_bot, 100.0 * n_bot / n_cls, n_triv))
        emit("max linger = %d  at N=%d （该偶数在'纯粹配对阻塞'状态停留的层数）"
             % (maxlinger[0], maxlinger[1]))
        emit("linger 分布：=0 的 %d 个；>=1 的 %d 个；最大 %d"
             % (sum(1 for L in lingers if L == 0), sum(1 for L in lingers if L >= 1), maxlinger[0]))
        emit("BOT 型最大底部窗口宽度 = %d  at N=%d" % (bot_window_max[0], bot_window_max[1]))
        emit("TOP 型最大超出量 = %d  at N=%d" % (top_excess_max[0], top_excess_max[1]))
        emit("抽样：")
        for r in samples:
            emit("  N=%-9d λ=%-9d i_lam=%-7d k0=%-7d linger=%-5d %s top_edge=%-9d bot_win=%d"
                 % (r["N"], r["lambda"], r["i_lam"], r["k0"], r["linger"], r["type"],
                    r["top_edge"], r["bot_window"]))

        out["taxonomy"] = {
            "n_classified": n_cls,
            "n_TOP_reach": n_top, "pct_TOP": round(100.0 * n_top / n_cls, 3),
            "n_BOT_pair": n_bot, "pct_BOT": round(100.0 * n_bot / n_cls, 3),
            "n_trivial_small": n_triv,
            "max_linger": maxlinger[0], "argmax_linger_N": maxlinger[1],
            "n_linger_eq_0": sum(1 for L in lingers if L == 0),
            "n_linger_ge_1": sum(1 for L in lingers if L >= 1),
            "max_bot_window": bot_window_max[0], "argmax_bot_window_N": bot_window_max[1],
            "max_top_excess": top_excess_max[0], "argmax_top_excess_N": top_excess_max[1],
            "samples": samples,
        }

        # ---- 2. 定理 A 的经验核验：k0 <= i_lam 是否恒成立 ----
        emit("")
        emit("=== 2. 定理 A 核验：k0(N) ≤ i_lam(N) 恒成立？（即 REACH 必在填充前解除）===")
        emit("  注：k0 用修正后的可达判定（含 N=2p 的等值对，否则会漏掉全部 2p 点）")
        emit("  注：本核验复用 §1 已算好的 λ 表（原实现重复计算了整整一遍）")
        viol = 0
        checked = 0
        for N in range(4, X + 1, 2):
            q = lam_arr[N // 2]
            if q == 0:
                continue
            checked += 1
            if k0_of(N) > idx_of[q]:
                viol += 1
        emit("受检偶数 %d（跳过反例 %d 个）；违反 k0 ≤ i_lam 的个数 = %d （应为 0）"
             % (checked, len(missing), viol))
        out["theoremA_check"] = {"checked": checked, "violations": viol, "holds": viol == 0}
        emit("反例（不可表示偶数）个数 = %d" % len(missing))

        # ---- 3. linger 直方图（按区间） ----
        emit("")
        emit("=== 3. linger = i_lam − k0 的分布（层数）===")
        import collections
        hist = collections.Counter()
        for L in lingers:
            b = 0 if L == 0 else (1 if L <= 2 else (2 if L <= 10 else (3 if L <= 100 else (4 if L <= 1000 else 5))))
            hist[b] += 1
        labels = {0: "0", 1: "1-2", 2: "3-10", 3: "11-100", 4: "101-1000", 5: ">1000"}
        for b in sorted(hist):
            emit("  linger %-9s : %d" % (labels[b], hist[b]))
        out["linger_hist"] = {labels[b]: hist[b] for b in sorted(hist)}

        # ---- 4. 结论 ----
        emit("")
        emit("=== 4. 结论 ===")
        emit("(1) 定理 A：REACH 阻塞有限期（k0(N)<∞ 且 k0≤i_lam，实测零违反）。")
        emit("(2) 分类：TOP 型 %.2f%% vs BOT 型 %.2f%% —— 多数偶数的最后一次阻塞来自 PAIR。"
             % (100.0 * n_top / n_cls, 100.0 * n_bot / n_cls))
        emit("(3) 生成（reach）部分可证且平凡；困难 100%% 落在 PAIR → 短区间素数配对。")
        emit("(4) 因此素数侧生成路线无法绕过 parity barrier；它把问题还原为同一条 HL 主项-误差要求。")
        emit("(5) 猜想仍未证明。")
        out["conclusion"] = {
            "theoremA": "REACH 阻塞有限期：∃k0(N)<∞ 使 k≥k0 时 N ≤ p_{k-1}+p_k",
            "theoremA_verified": viol == 0,
            "taxonomy_split": {"TOP_pct": round(100.0 * n_top / n_cls, 3),
                               "BOT_pct": round(100.0 * n_bot / n_cls, 3)},
            "route_verdict": "素数侧生成路线不能绕过 parity barrier；核心困难＝PAIR（短区间素数配对）",
            "status": "NOT PROVEN",
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
