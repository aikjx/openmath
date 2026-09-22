# -*- coding: utf-8 -*-
"""
OM-P-NT-0003 联合筛：二阶森林证书族的【精确最优】（2026-09-22 第三轮）

问题. 在"只用空交集许可的森林选边"这一二阶族中，求
        max  sum_{(p,q) in E(G)} A_{pq}
     s.t. 对每个真实出现的模式 S = V(n)，E(G) 在 S 上的诱导子图是森林。

对偶（本项目使用的解法）. 记候选边（A_{pq}>0）为 e，权重 w_e=A_{pq}。
则上式 = W_total - min{ sum_{e in X} w_e : X 与每个"禁环"相交非空 }，
其中禁环 = 全部顶点落在某个真实模式内的简单环（只用候选边）。
于是化为**最小权命中集**问题，用"挑一个未命中的环、逐个排除其边"的分支限界
精确求解，配贪心初始解与"边不相交环"的下界剪枝。命中集小 → 搜索快，
因此可以把此前"预算耗尽"的情形提升为**已证明最优**。

自检：N=172 应复现终稿的 6 条边与精确最优值 26（下界 2）。

输出：05-验证中心/03-结果/2026/09/OM-P-NT-0003-joint-optimal-20260922.json
"""
import json
import os
import time
from itertools import combinations
from math import isqrt

LADDER = [172, 800, 1000, 1500, 2000, 3000]
MAX_CYCLE_LEN = 9
NODE_BUDGET = 3000000
TIME_LIMIT_S = 240.0


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
    if residue >= length or length <= 0:
        return 0
    n = (length - 1 - residue) // period + 1
    block = ((1 << (period * n)) - 1) // ((1 << period) - 1)
    return (block << residue) & ((1 << length) - 1)


def build(N):
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
    pats = {}
    for j in range(X):
        s = frozenset(i for i in range(len(ps)) if (masks[i] >> j) & 1)
        pats[s] = pats.get(s, 0) + 1
    return pats


def maximal_patterns(pats):
    """去掉被别的模式包含的模式：判断 vset 是否落在某个模式内只需查极大模式"""
    keys = [S for S in pats if len(S) >= 3]
    maxs = [S for S in keys if not any(S < T for T in keys)]
    return maxs


def enumerate_forbidden_cycles(k, edges, patterns, max_len):
    """枚举顶点集落在某个真实模式内的简单环（长 3..max_len），返回边的 frozenset 列表"""
    adj = {i: set() for i in range(k)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    def in_pattern(vset):
        return any(vset <= S for S in patterns)

    found = set()

    def dfs(start, path, pathset):
        v = path[-1]
        for u in adj[v]:
            if u == start and len(path) >= 3:
                vs = frozenset(path)
                if in_pattern(vs):
                    es = frozenset(
                        (min(path[i], path[i + 1]), max(path[i], path[i + 1]))
                        for i in range(len(path) - 1))
                    es = es | {tuple(sorted((path[-1], start)))}
                    found.add(es)
                continue
            if u <= start or u in pathset:
                continue
            if len(path) >= max_len:
                continue
            path.append(u)
            pathset.add(u)
            dfs(start, path, pathset)
            pathset.discard(u)
            path.pop()

    for s in sorted({a for a, _ in edges}):
        dfs(s, [s], {s})
    return list(found)


def min_weight_hitting_set(edges, weights, cycles, time_limit, node_budget):
    """最小权命中集：X 与每个环相交非空，最小化 sum_{e in X} w_e"""
    if not cycles:
        return 0, [], {"nodes": 0, "proven": True}

    cycle_edges = [tuple(sorted(c)) for c in cycles]
    eidx = {e: i for i, e in enumerate(edges)}
    cyc = [tuple(eidx[e] for e in c) for c in cycle_edges]

    t0 = time.time()
    stat = {"nodes": 0, "timeout": False, "budget": False}

    # 贪心初始解：反复挑"命中环最多/权重最小"的边
    def greedy():
        remaining = set(range(len(cyc)))
        chosen = []
        while remaining:
            cnt = {}
            for ci in remaining:
                for e in cyc[ci]:
                    cnt[e] = cnt.get(e, 0) + 1
            best_e = max(cnt, key=lambda e: (cnt[e] / weights[e], cnt[e]))
            chosen.append(best_e)
            remaining = {ci for ci in remaining if best_e not in cyc[ci]}
        return sum(weights[e] for e in chosen), chosen

    best_cost, best_set = greedy()

    # 下界剪枝：找一组边不相交的未命中环，每个至少贡献其最小权
    def lower_bound(remaining):
        used = set()
        lb = 0
        for ci in remaining:
            if any(e in used for e in cyc[ci]):
                continue
            m = min(weights[e] for e in cyc[ci])
            lb += m
            used.update(cyc[ci])
        return lb

    def dfs(cost, chosen, remaining):
        nonlocal best_cost, best_set
        stat["nodes"] += 1
        if stat["nodes"] > node_budget:
            stat["budget"] = True
            return
        if time.time() - t0 > time_limit:
            stat["timeout"] = True
            return
        if cost >= best_cost:
            return
        if cost + lower_bound(remaining) >= best_cost:
            return
        if not remaining:
            best_cost = cost
            best_set = list(chosen)
            return
        # 选第一个未命中环
        ci = min(remaining)
        for e in cyc[ci]:
            nrem = {c for c in remaining if e not in cyc[c]}
            chosen.append(e)
            dfs(cost + weights[e], chosen, nrem)
            chosen.pop()
            if stat["budget"] or stat["timeout"]:
                return

    dfs(0, [], set(range(len(cyc))))
    stat["seconds"] = round(time.time() - t0, 2)
    stat["proven"] = not (stat["timeout"] or stat["budget"])
    return best_cost, best_set, stat


def solve(N, time_limit=TIME_LIMIT_S, node_budget=NODE_BUDGET):
    X, ps, masks = build(N)
    k = len(ps)
    S1 = sum(m.bit_count() for m in masks)
    pats = realized_patterns(X, ps, masks)
    maxp = maximal_patterns(pats)

    cand = []
    for i, j in combinations(range(k), 2):
        w = (masks[i] & masks[j]).bit_count()
        if w > 0:
            cand.append(((i, j), w))
    edges = [e for e, _ in cand]
    weights = [w for _, w in cand]
    W_total = sum(weights)

    maxlen = min(MAX_CYCLE_LEN, max((len(S) for S in pats), default=3))
    cyc = enumerate_forbidden_cycles(k, edges, maxp, maxlen)

    del_cost, del_set, stat = min_weight_hitting_set(
        edges, weights, cyc, time_limit, node_budget)

    best_kept = W_total - del_cost
    return {
        "N": N, "|X|": X, "k_primes": k, "S1": S1,
        "realized_patterns": len(pats),
        "maximal_patterns": len(maxp),
        "max_pattern_size": max((len(S) for S in pats), default=0),
        "candidate_edges": len(edges),
        "W_total_all_pairs": W_total,
        "forbidden_cycles": len(cyc),
        "min_deleted_weight": del_cost,
        "deleted_edges": [[ps[edges[e][0]], ps[edges[e][1]], weights[e]]
                          for e in del_set],
        "optimal_S2_forest_family": best_kept,
        "optimal_order2_bound": X - S1 + best_kept,
        "bound_positive": (X - S1 + best_kept) > 0,
        "proven_optimal": stat["proven"],
        "search": stat,
        "H_true": true_H(N),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    out_dir = os.path.join(root, "05-验证中心", "03-结果", "2026", "09")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "OM-P-NT-0003-joint-optimal-20260922.json")
    log_path = os.path.join(out_dir, "_joint_optimal_runlog.txt")

    out = {"target_id": "OM-P-NT-0003", "check_date": "2026-09-22",
           "method": "候选图上的最小权命中集（对偶形式），分支限界精确求解",
           "arithmetic": "精确整数", "ai_assisted": True,
           "independent_human_review": False, "results": []}

    with open(log_path, "w", encoding="utf-8") as log:
        def emit(s):
            log.write(s + "\n")
            log.flush()

        for N in LADDER:
            r = solve(N)
            emit(json.dumps(r, ensure_ascii=False))
            out["results"].append(r)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        emit("written: " + json_path)


if __name__ == "__main__":
    main()
