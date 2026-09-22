# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 素数侧（生成式/反推）核算：素数把偶数填满

视角翻转
--------
偶数侧：给定 N，找一对素数 p+q=N。
素数侧：给定素数集合，看它们"生成"出的和是否把偶数填满。
        每个偶数的"到达时刻" = 填它所需的最小素数上界 λ(N)=min{max(p,q): p+q=N}。

本轮要核算的素数侧量
--------------------
1. 到达时刻下界（引理 H）：λ(N) ≥ N/2，等号 ⟺ N=2p（p 素数）。
   故"填满到 X"至少需要素数到 X/2 —— 到达时刻随 N 线性增长。
2. 超出半程量 δ(N) = λ(N) − N/2 ≥ 0：填 N 时素数"越过 N/2 多远"。
   上一轮破译的"339 条整除证书"正是 δ(N*)/2（证书窗口宽度 = δ）。
3. 等待区（引理 G）：设 q=p_k 为最大素数，则 (p_{k-1}+p_k, 2p_k) 内所有偶数
   都不能用 ≤q 的素数表示（除 2p_k 外最大和是 p_{k-1}+p_k），必须等待更大的素数。
   等待区半宽 ≈ 素数间隙。
4. 收获台账（partition）：h(q)=#{N: λ(N)=q} 把 [4,X] 内全部偶数**划分**到各素数头上，
   Σ h(q) = 偶数个数。据此统计：哪些素数是"前沿推进者"，哪些"颗粒无收"。
5. 未排空积压：Δ(q)=2q−C(q)（C=连续覆盖前沿）。
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
    json_path = os.path.join(out_dir, "OM-P-NT-0003-prime-side-20260922.json")
    log_path = os.path.join(out_dir, "_prime_side_runlog.txt")

    s = sieve(2 * X + 10)
    primes = [i for i in range(2, X + 1) if s[i]]
    P = len(primes)

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "X": X, "view": "素数侧（生成式/反推）"}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(t):
            log.write(t + "\n")
            log.flush()

        # ---------- 1. 到达时刻 λ(N) 与 δ(N) ----------
        emit("=== 1. 到达时刻 λ(N) 与超出半程量 δ(N)=λ(N)-N/2 ===")
        h = [0] * (X + 1)          # h[q] = #{N: λ(N)=q}
        maxdelta, argdelta = -1, 0
        maxlam, argmaxlam = -1, 0
        eqhalf = []
        dec_best = {}
        lam_head = []
        missing = []
        for N in range(4, X + 1, 2):
            q = 0                  # 每轮重置：陈旧值会静默掩盖反例（2026-09-22 修复）
            j = bisect_right(primes, N // 2) - 1
            while j >= 0:
                p = primes[j]
                if s[N - p]:
                    q = N - p
                    break
                j -= 1
            if q == 0:
                missing.append(N)
                continue
            h[q] += 1
            lam_head.append(q)
            if q > maxlam:
                maxlam, argmaxlam = q, N
            d = q - N // 2
            if d > maxdelta:
                maxdelta, argdelta = d, N
            if 2 * q == N:
                eqhalf.append(N)
            dec = len(str(N - 1)) - 1
            if dec not in dec_best or d > dec_best[dec][0]:
                dec_best[dec] = (d, N, q)

        n_evens = len(lam_head)
        delta_at_argmax = maxlam - argmaxlam // 2
        emit("偶数个数 (4..%d) = %d  不可表示(反例) = %d" % (X, n_evens, len(missing)))
        if missing:
            emit("  !! 反例清单（前 20）: %s" % missing[:20])
        emit("max λ = %d at N=%d （最坏偶数，需最大的素数）" % (maxlam, argmaxlam))
        emit("  ⇒ 该点 δ = λ − N/2 = %d ⇒ 证书窗口宽度 %d ⇒ 奇数(证书)条数 %d"
             % (delta_at_argmax, delta_at_argmax, delta_at_argmax // 2))
        emit("max δ = %d  at N=%d  (λ=%d, N/2=%d)  ← 与 maxλ 点不同，是两个量"
             % (maxdelta, argdelta, argdelta // 2 + maxdelta, argdelta // 2))
        emit("引理H: 2λ(N)=N 的 N 共 %d 个（形如 2p），前几个: %s"
             % (len(eqhalf), eqhalf[:10]))
        emit("引理H: 是否所有 N 都满足 2λ(N) ≥ N ? %s"
             % all(2 * v >= 4 + 2 * i for i, v in enumerate(lam_head)))
        out["arrival"] = {
            "n_evens": n_evens,
            "n_unrepresentable": len(missing),
            "unrepresentable_head": missing[:20],
            "max_lambda": maxlam, "argmax_lambda_N": argmaxlam,
            "delta_at_argmax_lambda": delta_at_argmax,
            "max_delta": maxdelta, "argmax_delta_N": argdelta,
            "count_N_with_2lambda_eq_N": len(eqhalf),
            "examples_2p": eqhalf[:10],
            "lemmaH_all_hold": all(2 * v >= 4 + 2 * i for i, v in enumerate(lam_head)),
        }
        emit("")
        emit("分年代 max δ(N):")
        rows = []
        for dec in sorted(dec_best):
            d, N, q = dec_best[dec]
            emit("  10^%d..: maxδ=%-6d at N=%-9d λ=%-9d" % (dec, d, N, q))
            rows.append({"decade": dec, "max_delta": d, "N": N, "lambda": q})
        out["delta_by_decade"] = rows

        # 339 复核：δ(N*) 与证书条数
        emit("")
        emit("339 复核：δ(N_T) = %d ⇒ 证书窗口宽度 = %d ⇒ 奇数(证书)条数 = %d"
             % (delta_at_argmax, delta_at_argmax, delta_at_argmax // 2))
        out["certificate_339_recheck"] = {
            "N_T": argmaxlam, "lambda": maxlam,
            "delta_at_argmax": delta_at_argmax,
            "window_width": delta_at_argmax,
            "certificate_count_odd": delta_at_argmax // 2,
            "note": ("与上一轮破译的 339 一致"
                     if delta_at_argmax // 2 == 339 else "不一致"),
        }

        # ---------- 2. 收获台账（划分恒等式） ----------
        emit("")
        emit("=== 2. 收获台账 h(q)=#{N:λ(N)=q}  （应构成划分）===")
        tot = sum(h)
        emit("Σ_q h(q) = %d   偶数个数 = %d   划分恒等式: %s"
             % (tot, n_evens, tot == n_evens))
        n_q_nonzero = sum(1 for q in primes if h[q] > 0)
        n_q_zero = sum(1 for q in primes if h[q] == 0)
        emit("素数总数 ≤ X: %d   收获非空(至少填一个偶数): %d   收获为空: %d  (%.1f%%)"
             % (P, n_q_nonzero, n_q_zero, 100.0 * n_q_zero / P))
        harvest_sorted = sorted(((h[q], q) for q in primes if h[q] > 0), reverse=True)
        emit("收获最大的前 10 个素数 (h, q): %s"
             % [(c, q) for c, q in harvest_sorted[:10]])
        emit("收获恰为 1 的素数个数: %d（这些偶数只有唯一最小表示）"
             % sum(1 for q in primes if h[q] == 1))
        out["harvest"] = {
            "partition_identity_holds": tot == n_evens,
            "sum_h": tot, "n_evens": n_evens,
            "n_primes": P, "n_primes_with_harvest": n_q_nonzero,
            "n_primes_zero_harvest": n_q_zero,
            "pct_zero_harvest": round(100.0 * n_q_zero / P, 2),
            "top10_harvest": [{"q": q, "h": c} for c, q in harvest_sorted[:10]],
            "count_h_eq_1": sum(1 for q in primes if h[q] == 1),
        }

        # ---------- 3. 连续覆盖前沿 C(q) 与积压 Δ(q) ----------
        emit("")
        emit("=== 3. 连续覆盖前沿 C(q) 与未排空积压 Δ(q)=2q-C(q) ===")
        # 前缀最大 M(N)=max_{m<=N} λ(m)；C(q)=max{N: M(N)<=q}
        pref = []          # (N, M(N))
        cur = 0
        for i, q in enumerate(lam_head):
            N = 4 + 2 * i
            if q > cur:
                cur = q
            pref.append((N, cur))
        prefN = [t[0] for t in pref]
        prefM = [t[1] for t in pref]

        def C_of(q):
            k = bisect_right(prefM, q) - 1
            return prefN[k] if k >= 0 else 0

        advance = 0
        prevC = 0
        table = []
        for idx, q in enumerate(primes):
            c = C_of(q)
            if c > prevC:
                advance += 1
            prevC = c
            if q in (31, 101, 1009, 10007, 100003, 500009, 999983, 1000039, 1000537):
                table.append({"q": q, "C": c, "2q": 2 * q, "Delta": 2 * q - c})
        emit("前沿推进素数个数: %d / %d = %.1f%%（其余素数不改变连续前沿）"
             % (advance, P, 100.0 * advance / P))
        emit("抽查 (q, C(q), 2q, Δ):")
        for r in table:
            emit("  q=%-9d C=%-9d 2q=%-9d Δ=%d" % (r["q"], r["C"], r["2q"], r["Delta"]))
        out["frontier"] = {
            "n_advancing_primes": advance, "n_primes": P,
            "pct_advancing": round(100.0 * advance / P, 2),
            "spot": table,
        }

        # ---------- 4. 等待区引理 G 的定点核验 ----------
        emit("")
        emit("=== 4. 两个窗口（都源于'候选耗尽'，但位置不同）===")
        qstar = maxlam
        N_T = argmaxlam
        kstar = bisect_right(primes, qstar) - 1
        q_prev = primes[kstar - 1] if kstar >= 1 else 3
        gap = qstar - q_prev

        # 4a 顶部等待区（引理 G）：最大素数 q=p_k 时 (p_{k-1}+p_k, 2p_k) 全不可达
        lo_w, hi_w = q_prev + qstar, 2 * qstar
        ws = [N for N in range(lo_w + 2, hi_w, 2)]
        bad = []
        for N in ws:
            j = bisect_right(primes, N // 2) - 1
            ok = False
            while j >= 0 and primes[j] <= qstar:
                p = primes[j]
                if s[N - p] and (N - p) <= qstar:
                    ok = True
                    break
                j -= 1
            if ok:
                bad.append(N)
        emit("[4a] 顶部等待区（引理G）  最大值素数 q*=p_%d=%d, 前一素数=%d, 素数间隙=%d"
             % (kstar + 1, qstar, q_prev, gap))
        emit("     等待区 = (%d, %d)  区间长度=%d=间隙  含偶数 %d 个" % (lo_w, hi_w, hi_w - lo_w, len(ws)))
        emit("     逐点核验：能用 ≤q* 素数表示者 %d 个（应为 0）" % len(bad))

        # 4a' 最大素数间隙 ⇒ 最大顶部等待区
        mg, mg_at = 0, 0
        for i in range(1, P):
            g = primes[i] - primes[i - 1]
            if g > mg:
                mg, mg_at = g, primes[i - 1]
        emit("     素数 ≤%d 的最大间隙 = %d（在 %d 与 %d 之间）⇒ 该处顶部等待区含 ≥%d 个偶数必须等待"
             % (X, mg, mg_at, mg_at + mg, (mg - 1) // 2))
        out.setdefault("max_gap", {})["max_gap_le_X"] = {
            "gap": mg, "after": mg_at, "next": mg_at + mg,
            "min_evens_waiting": (mg - 1) // 2,
        }

        # 4b 底部证书窗口（引理 A）：N_T 的窗口 (N_T-λ, N_T/2]
        lo_c, hi_c = N_T - qstar + 1, N_T // 2
        odds = list(range(lo_c if lo_c % 2 else lo_c + 1, hi_c + 1, 2))
        certs_prime_p, certs_comp_p, viol = 0, 0, []
        for p in odds:
            if s[p]:
                certs_prime_p += 1
                if s[N_T - p]:
                    viol.append(p)          # p 素数且 N_T-p 素数 ⇒ 会否证 λ=T
            else:
                certs_comp_p += 1
        emit("[4b] 底部证书窗口（引理A）  N_T=%d, λ=%d" % (N_T, qstar))
        emit("     窗口 = (%d, %d]  宽度=%d=δ  奇数(证书)条数=%d"
             % (lo_c - 1, hi_c, hi_c - (lo_c - 1), len(odds)))
        emit("     p 本身素数 %d 个（给 N_T-p 的因子）+ p 合数 %d 个（给 p 的因子）= %d"
             % (certs_prime_p, certs_comp_p, len(odds)))
        emit("     核验：存在 p 素数且 N_T-p 素数者 %d 个（应为 0，否则 λ 会更小）" % len(viol))
        out["waiting_zone"] = {
            "top_zone_lemmaG": {"q_star": qstar, "k_star": kstar + 1, "p_prev": q_prev,
                                 "zone": [lo_w, hi_w], "width": hi_w - lo_w, "gap": gap,
                                 "n_evens": len(ws), "unreachable_verified": len(bad) == 0},
            "bottom_cert_lemmaA": {"N_T": N_T, "lambda": qstar,
                                    "window": [lo_c - 1, hi_c], "width": hi_c - (lo_c - 1),
                                    "certificates": len(odds),
                                    "prime_p": certs_prime_p, "composite_p": certs_comp_p,
                                    "no_violation": len(viol) == 0},
        }

        # ---------- 5. 结论 ----------
        emit("")
        emit("=== 5. 素数侧结论 ===")
        emit("(a) 引理H: λ(N) ≥ N/2 ⇒ 填满到 X 必须动用 ≥X/2 的素数；到达时刻线性增长 ⇒ 有限素数不够。")
        emit("(b) 引理G: 每个素数间隙都在顶部制造一个宽度=间隙的等待区；间隙无界 ⇒ 等待区无界。")
        emit("(c) 划分恒等式: Σ_q h(q) = 偶数个数，成立 ⇒ '素数填偶数'的台账自洽。")
        emit("(d) 前沿推进素数仅占 %.1f%%：绝大多数素数不在前沿，只在已覆盖区提供替代表示；"
             % (100.0 * advance / P))
        emit("    但 %.1f%% 的素数确有非空收获（至少是某个偶数的最小表示的最大素数）。"
             % (100.0 * n_q_nonzero / P))
        emit("(e) 两个窗口：顶部等待区宽=素数间隙（无界）；底部证书窗口宽=δ（本轮 maxδ=%d）。" % maxdelta)
        emit("(f) 猜想 ⟺ 每个偶数的到达时刻 λ(N) 有限 ⟺ 所有等待区最终都被后续素数抽空。这一步未证。")
        out["conclusion"] = {
            "lemmaH": "λ(N)>=N/2, 等号 iff N=2p（本轮 78498 个等号点，恰为 ≤1e6 的素数个数）",
            "lemmaG": "素数间隙=顶部等待区宽度; 间隙无界⇒等待区无界",
            "partition": "Σ h(q) = #evens (verified)",
            "pct_frontier_primes": round(100.0 * advance / P, 2),
            "pct_primes_nonempty_harvest": round(100.0 * n_q_nonzero / P, 2),
            "missing_step": "所有等待区最终被抽空 ⇔ Goldbach（未证）",
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
