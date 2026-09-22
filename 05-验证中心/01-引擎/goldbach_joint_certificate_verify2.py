# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 联合筛：终稿核对 + 低阶可扩展性的定量检验（2026-09-22）

全部精确整数运算（无浮点、无外部依赖）。

  A1  N=172：单项/两两计数、6 条边图证书、下界 2；§4.1 的 13 行整数反模型；
      以及森林条件的"实际模式"判据（只对真实出现的 V(n) 检查，而非全部 32 个子集）。
  A2  N=800：60 个非零系数在全部 256 个布尔向量上验证 P(x) <= 1_{x=0}；
      用独立（非 CRT）计数重算 186 / -334 / +208 / -43 = 17。
  B   定义无关的三阶 Bonferroni 下界
        L3(N) = |X| - S1 + S2(全二元组) - S3(全三元组)
      在 6<=N<=20000 内的正性范围与失效点。
  C   二阶图证书（仅用空交集许可的森林选边）的【精确最优】：分支限界求
      最大 Σ A_pair，并检验终稿 N=172 的 6 条边是否为该类的真实最优。
      同时给出朴素贪心（按交集大小降序）作对照。

输出：05-验证中心/03-结果/2026/09/OM-P-NT-0003-joint-verify2-20260922.json
"""
import json
import os
import time
from itertools import combinations
from math import isqrt

NMAX_SCAN = 20000
LADDER = [172, 800, 1000, 1500, 2000]
NODE_BUDGET = 2000000
TIME_LIMIT_S = 180.0


def primes_upto(limit):
    if limit < 2:
        return []
    s = bytearray([1]) * (limit + 1)
    s[0] = s[1] = 0
    for p in range(2, isqrt(limit) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(s[p * p::p]))
    return [i for i in range(2, limit + 1) if s[i]]


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def periodic_mask(length, period, residue):
    """下标 {residue + k*period} ∩ [0,length) 的位掩码"""
    if residue >= length or length <= 0:
        return 0
    n = (length - 1 - residue) // period + 1
    block = ((1 << (period * n)) - 1) // ((1 << period) - 1)
    return (block << residue) & ((1 << length) - 1)


def build(N):
    """候选 = 中央区间内的奇数 n。索引 j 对应 m = first_odd + 2j。"""
    y = isqrt(N)
    hi = N // 2
    first_odd = y + 1 if (y + 1) % 2 == 1 else y + 2
    cnt = (hi - first_odd) // 2 + 1 if first_odd <= hi else 0
    ps = [p for p in primes_upto(isqrt(N)) if p % 2 == 1]
    masks = []
    for p in ps:
        m = 0
        for r in sorted({0, N % p}):
            res = ((r - first_odd) * pow(2, -1, p)) % p
            m |= periodic_mask(cnt, p, res)
        masks.append(m)
    return cnt, ps, masks


def true_H(N):
    y = isqrt(N)
    return sum(1 for m in range(y + 1, N // 2 + 1)
               if m % 2 == 1 and is_prime(m) and is_prime(N - m))


def realized_patterns(X, ps, masks):
    """真实出现的命中集 V(n)（去重），以及每个模式的点数权重"""
    pats = {}
    for j in range(X):
        s = frozenset(i for i in range(len(ps)) if (masks[i] >> j) & 1)
        pats[s] = pats.get(s, 0) + 1
    return pats


# --------------------------------------------------------------- A1: N=172 --

MODEL_172 = [
    ("3", 9), ("5", 5), ("3,5", 5), ("7", 3), ("3,7", 3), ("3,5,7", 2),
    ("11", 2), ("3,11", 1), ("3,5,11", 1), ("13", 2), ("3,5,7,13", 1),
    ("3,11,13", 1), ("3,5,7,11,13", 1),
]
EDGES_172 = [(3, 5), (3, 7), (3, 11), (5, 13), (7, 11), (7, 13)]


def induced_is_forest(S, edges):
    S = set(S)
    if len(S) <= 1:
        return True
    es = [(a, b) for a, b in edges if a in S and b in S]
    if len(es) > len(S) - 1:
        return False
    parent = {v: v for v in S}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in es:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True


def check_172():
    out = {"N": 172}
    X, ps, masks = build(172)
    idx = {p: i for i, p in enumerate(ps)}
    out["primes"] = ps
    out["|X|"] = X

    single = {p: masks[idx[p]].bit_count() for p in ps}
    out["singletons_recomputed"] = single
    out["singletons_matches_paper"] = [single[p] for p in ps] == [24, 15, 10, 6, 5]

    pairs = {(a, b): (masks[idx[a]] & masks[idx[b]]).bit_count()
             for a, b in combinations(ps, 2)}
    out["pairs_recomputed"] = {f"{a},{b}": v for (a, b), v in pairs.items()}

    s2 = sum(pairs[e] for e in EDGES_172)
    out["graph_edges"] = [list(e) for e in EDGES_172]
    out["bound_order2_graph"] = X - sum(single.values()) + s2

    # (i) 全部 32 个子集：作为诊断
    bad_all = []
    for r in range(len(ps) + 1):
        for S in combinations(ps, r):
            if not induced_is_forest(S, EDGES_172):
                bad_all.append(list(S))
    out["non_forest_subsets_over_all32"] = bad_all

    # (ii) 只对【真实出现】的模式检查（这才是引理的条件）
    pats = realized_patterns(X, ps, masks)
    bad_real = [sorted(ps[i] for i in S) for S in pats
                if not induced_is_forest(S, EDGES_172)]
    out["realized_pattern_count"] = len(pats)
    out["non_forest_realized_patterns"] = bad_real
    out["forest_condition_holds_on_realized"] = (len(bad_real) == 0)

    # (iii) 每个被排除子集是否都含 (4) 中的禁交子集
    f1, f2 = {3, 7, 11}, {5, 7, 13}
    out["all_excluded_subsets_contain_forbidden"] = all(
        (f1 <= set(S)) or (f2 <= set(S)) for S in bad_all)
    out["forbidden_intersections"] = [sorted(f1), sorted(f2)]

    # 空交集直接核验
    m3, m7, m11 = (masks[idx[3]], masks[idx[7]], masks[idx[11]])
    m5, m13 = masks[idx[5]], masks[idx[13]]
    out["A_{3,7,11}"] = (m3 & m7 & m11).bit_count()
    out["A_{5,7,13}"] = (m5 & m7 & m13).bit_count()

    # §4.1 整数反模型
    w = {tuple(sorted(int(t) for t in k.split(","))): v for k, v in MODEL_172}
    out["model_total"] = sum(w.values())
    out["model_s_total_ok"] = sum(w.values()) == X
    out["model_singletons_ok"] = all(
        sum(v for S, v in w.items() if p in S) == single[p] for p in ps)
    out["model_pairs_ok"] = all(
        sum(v for S, v in w.items() if a in S and b in S) == pairs[(a, b)]
        for a, b in pairs)
    out["model_empty_weight"] = w.get(tuple(), 0)
    out["model_is_valid_antimodel"] = (
        out["model_s_total_ok"] and out["model_singletons_ok"]
        and out["model_pairs_ok"] and out["model_empty_weight"] == 0)
    out["H_true_172"] = true_H(172)
    out["true_pairs_172"] = [
        (m, 172 - m) for m in range(15, 87, 2)
        if is_prime(m) and is_prime(172 - m)]
    return out


# --------------------------------------------------------------- A2: N=800 --

TERMS = ([(1, 0)]                                   # 常数项 a_∅ = +1
         + [(-1, m) for m in (1, 2, 4, 8, 16, 32, 64, 128)]
         + [(1, m) for m in (3, 5, 9, 17, 33, 65, 129, 10, 34, 66, 130,
                             12, 20, 36, 132, 24, 40, 136, 80, 160)]
         + [(-1, m) for m in (11, 35, 67, 131, 13, 21, 37, 133, 25, 41, 137,
                              81, 161, 193, 42, 74, 138, 162, 194, 28, 44,
                              76, 140, 100, 164, 104, 168, 208)]
         + [(1, m) for m in (196, 200, 224)])


def mask_to_set(m):
    return frozenset(i for i in range(8) if (m >> i) & 1)


def check_800():
    out = {"N": 800}
    X, ps, masks = build(800)
    out["primes"] = ps
    out["|X|"] = X
    out["n_nonzero_coefficients"] = 1 + len(TERMS)
    out["singleton_counts"] = [m.bit_count() for m in masks]

    terms = [(mask_to_set(m), a) for a, m in TERMS]
    worst = (-10 ** 9, -1)
    viol = 0
    for vec in range(256):
        vs = frozenset(i for i in range(8) if (vec >> i) & 1)
        P = sum(a for S, a in terms if S <= vs)
        d = P - (1 if len(vs) == 0 else 0)
        if d > 0:
            viol += 1
        if d > worst[0]:
            worst = (d, vec)
    out["max_violation"] = worst[0]
    out["violation_count_over_256"] = viol
    out["pointwise_ok"] = (viol == 0 and worst[0] <= 0)

    def A(S):
        if not S:
            return X
        m = -1
        for i in S:
            m = masks[i] if m < 0 else (m & masks[i])
        return m.bit_count()

    def group(order):
        return sum(a * A(mask_to_set(m)) for a, m in order)

    c1 = group([(a, m) for a, m in TERMS if bin(m).count("1") == 1])
    c2 = group([(a, m) for a, m in TERMS if bin(m).count("1") == 2])
    t3 = [(a, m) for a, m in TERMS if bin(m).count("1") == 3]
    c3n = group([(a, m) for a, m in t3 if a == -1])
    c3p = group([(a, m) for a, m in t3 if a == 1])
    out["c_order0"] = X
    out["c_order1"] = c1
    out["c_order2_selected"] = c2
    out["c_order3_neg"] = c3n
    out["c_order3_pos"] = c3p
    out["c_order3_total"] = c3n + c3p
    out["total"] = X + c1 + c2 + c3n + c3p
    out["total_equals_17"] = out["total"] == 17
    out["H_true_800"] = true_H(800)
    out["bound_le_true"] = out["total"] <= out["H_true_800"]

    S1 = sum(m.bit_count() for m in masks)
    S2 = sum((masks[i] & masks[j]).bit_count()
             for i, j in combinations(range(len(ps)), 2))
    S3 = sum((masks[i] & masks[j] & masks[l]).bit_count()
             for i, j, l in combinations(range(len(ps)), 3))
    out["allpairs_S1_S2_S3"] = [S1, S2, S3]
    out["naive_order3_bound"] = X - S1 + S2 - S3
    out["pure_order2_with_their_20pairs"] = X - S1 + c2
    return out


# --------------------------------------------- B: 三阶 Bonferroni 的失效点 --

def scan_L3(nmax=NMAX_SCAN):
    pos = 0
    last_pos = None
    first_bad_after = None
    sample = []
    N = 6
    while N <= nmax:
        X, ps, masks = build(N)
        S1 = sum(m.bit_count() for m in masks)
        S2 = sum((masks[i] & masks[j]).bit_count()
                 for i, j in combinations(range(len(masks)), 2))
        S3 = sum((masks[i] & masks[j] & masks[l]).bit_count()
                 for i, j, l in combinations(range(len(masks)), 3))
        L3 = X - S1 + S2 - S3
        if L3 > 0:
            pos += 1
            last_pos = N
        elif last_pos is not None and first_bad_after is None:
            first_bad_after = N
        if N in (172, 800, 1000, 2000, 5000, 10000, 20000):
            sample.append({"N": N, "|X|": X, "k_primes": len(ps),
                           "S1": S1, "S2": S2, "S3": S3, "L3": L3})
        if N % 4000 == 0:
            print("  L3 scan up to %d" % N, flush=True)
        N += 2
    rec = None
    if last_pos is not None:
        X, ps, masks = build(last_pos)
        S1 = sum(m.bit_count() for m in masks)
        S2 = sum((masks[i] & masks[j]).bit_count()
                 for i, j in combinations(range(len(masks)), 2))
        S3 = sum((masks[i] & masks[j] & masks[l]).bit_count()
                 for i, j, l in combinations(range(len(masks)), 3))
        rec = {"N": last_pos, "|X|": X, "k_primes": len(ps),
               "S1": S1, "S2": S2, "S3": S3, "L3": X - S1 + S2 - S3}
    return {"range": "6 <= N <= %d" % nmax, "count_L3_positive": pos,
            "last_N_with_L3_positive": last_pos,
            "first_N_negative_after_positive": first_bad_after,
            "last_positive_record": rec, "samples": sample}


# --------------------------------- C: 二阶森林证书的精确最优（分支限界） ----

def best_order2(N, time_limit=TIME_LIMIT_S, node_budget=NODE_BUDGET):
    X, ps, masks = build(N)
    k = len(ps)
    S1 = sum(m.bit_count() for m in masks)
    pats = list(realized_patterns(X, ps, masks).keys())
    pairs = sorted(((masks[i] & masks[j]).bit_count(), i, j)
                   for i, j in combinations(range(k), 2))
    pairs = [(c, i, j) for c, i, j in pairs if c > 0]

    stat = {"nodes": 0, "timeout": False, "budget_exhausted": False}
    t0 = time.time()
    best = {"w": None, "edges": None}

    suffix = [0] * (len(pairs) + 1)
    for t in range(len(pairs) - 1, -1, -1):
        suffix[t] = suffix[t + 1] + pairs[t][0]

    adj = {i: set() for i in range(k)}

    def feasible(i, j):
        for S in pats:
            if i not in S or j not in S:
                continue
            seen = {i}
            stack = [i]
            while stack:
                v = stack.pop()
                if v == j:
                    return False
                for u in adj[v]:
                    if u in S and u not in seen:
                        seen.add(u)
                        stack.append(u)
        return True

    def dfs(t, w, chosen):
        stat["nodes"] += 1
        if stat["nodes"] > node_budget:
            stat["budget_exhausted"] = True
            return
        if time.time() - t0 > time_limit:
            stat["timeout"] = True
            return
        if best["w"] is not None and w + suffix[t] <= best["w"]:
            return
        if t == len(pairs):
            if best["w"] is None or w > best["w"]:
                best["w"] = w
                best["edges"] = list(chosen)
            return
        c, i, j = pairs[t]
        if feasible(i, j):
            adj[i].add(j)
            adj[j].add(i)
            chosen.append((i, j, c))
            dfs(t + 1, w + c, chosen)
            chosen.pop()
            adj[i].discard(j)
            adj[j].discard(i)
        if stat["budget_exhausted"] or stat["timeout"]:
            return
        dfs(t + 1, w, chosen)

    dfs(0, 0, [])

    w = best["w"] if best["w"] is not None else 0
    edges = best["edges"] or []
    return {
        "N": N, "|X|": X, "k_primes": k, "S1": S1,
        "candidate_pairs": len(pairs),
        "S2_all_pairs": sum(c for c, _, _ in pairs),
        "optimal_S2": w,
        "optimal_edges": [[ps[i], ps[j], c] for i, j, c in edges],
        "optimal_order2_bound": X - S1 + w,
        "bound_positive": (X - S1 + w) > 0,
        "proven_optimal": not (stat["timeout"] or stat["budget_exhausted"]),
        "search": {"nodes": stat["nodes"], "timeout": stat["timeout"],
                   "budget_exhausted": stat["budget_exhausted"],
                   "seconds": round(time.time() - t0, 2)},
        "H_true": true_H(N),
    }


def greedy_order2(N):
    X, ps, masks = build(N)
    k = len(ps)
    S1 = sum(m.bit_count() for m in masks)
    pats = list(realized_patterns(X, ps, masks).keys())
    pairs = sorted(((masks[i] & masks[j]).bit_count(), i, j)
                   for i, j in combinations(range(k), 2))
    pairs = [(c, i, j) for c, i, j in pairs if c > 0]
    adj = {i: set() for i in range(k)}
    chosen = []
    for c, i, j in pairs:
        ok = True
        for S in pats:
            if i not in S or j not in S:
                continue
            seen = {i}
            stack = [i]
            while stack:
                v = stack.pop()
                if v == j:
                    ok = False
                    break
                for u in adj[v]:
                    if u in S and u not in seen:
                        seen.add(u)
                        stack.append(u)
            if not ok:
                break
        if ok:
            chosen.append((i, j, c))
            adj[i].add(j)
            adj[j].add(i)
    w = sum(c for _, _, c in chosen)
    return {"N": N, "edges_added": len(chosen), "S2_selected": w,
            "greedy_order2_bound": X - S1 + w,
            "bound_positive": (X - S1 + w) > 0}


# ------------------------------------------------------------------- main ----

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-joint-verify2-20260922.json")
    log_path = os.path.join(out_dir, "_joint_verify2_runlog.txt")

    result = {
        "target_id": "OM-P-NT-0003",
        "check_date": "2026-09-22",
        "arithmetic": "精确整数位图计数；Python 3.13 标准库，无浮点无外部依赖",
        "ai_assisted": True,
        "independent_human_review": False,
    }

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(s):
            log.write(s + "\n")
            log.flush()
            print(s, flush=True)

        emit("== A1: N=172 ==")
        r172 = check_172()
        emit(json.dumps(r172, ensure_ascii=False))
        result["N172"] = r172

        emit("== A2: N=800 ==")
        r800 = check_800()
        emit(json.dumps(r800, ensure_ascii=False))
        result["N800"] = r800

        emit("== B: 三阶 Bonferroni L3 ==")
        sc = scan_L3()
        emit(json.dumps(sc, ensure_ascii=False))
        result["L3_scan"] = sc

        emit("== C1: 二阶森林证书 · 精确最优 ==")
        opt = []
        for N in LADDER:
            r = best_order2(N)
            emit(json.dumps(r, ensure_ascii=False))
            opt.append(r)
        result["order2_optimal"] = opt

        emit("== C2: 二阶森林证书 · 朴素贪心对照 ==")
        grd = []
        for N in LADDER:
            r = greedy_order2(N)
            emit(json.dumps(r, ensure_ascii=False))
            grd.append(r)
        result["order2_greedy"] = grd

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
