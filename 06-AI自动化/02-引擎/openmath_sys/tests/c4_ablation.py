# -*- coding: utf-8 -*-
"""Task 22：C4 的 (P_ORDER_MAX, P_DEG_MAX) 对照实验。

问题不是"放宽好不好"，而是"放宽**换来了什么、代价是什么**"。所以每行都报：
  · 召回（通过外推检验的候选数）
  · 假警报（找到了候选但外推被证伪 —— 这就是过拟合的直接读数）
  · **阴性对照命中**：bell / partition 的生成函数非 D-finite，C4 在任何参数下
    都应报不出来；一旦放宽后出现输出，说明放宽引入的是噪声不是召回。
  · 耗时
结论只按这张表说话，不预设"放宽更好"。
"""
import os
import sys
import time
from math import comb
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openmath_sys import sequences as sq  # noqa: E402

# 阴性对照：生成函数非 D-finite，C4 在任何参数下都必须报不出来
NEGATIVE_CONTROLS = {"bell", "partition"}


def run_grid(seqs, orders, degs):
    rows = []
    for k in orders:
        for d in degs:
            t0 = time.perf_counter()
            n_pass = n_fail = 0
            neg_hit = []
            per_seq = {}
            for s in seqs:
                cands = sq.discover_polynomial_recurrence(
                    s["terms"], max_order=k, max_deg=d)
                good = [c for c in cands if c.get("survived_extrapolation")]
                bad = [c for c in cands if not c.get("survived_extrapolation")
                       and not c.get("skipped")]
                n_pass += len(good)
                n_fail += len(bad)
                per_seq[s["id"]] = len(good)
                if s["id"] in NEGATIVE_CONTROLS and (good or bad):
                    neg_hit.append(s["id"])
            rows.append({
                "order": k, "deg": d, "recall": n_pass, "false_alarms": n_fail,
                "negative_control_hits": neg_hit,
                "seconds": round(time.perf_counter() - t0, 2),
                "per_seq": per_seq,
            })
    return rows


def transformed_library(seqs):
    """变换后的序列库。

    为什么单独扫一遍：差分会把 P-recursive 的**次数**抬高
    （实测 apery 的差分需要 deg 4，而 apery 本身只要 deg 3），
    只看基础库会得出「deg 4 无收益」的结论，而那个结论只在基础库上成立。
    差分/部分和/二项/逆二项都保持 D-finite 性，所以 bell / partition
    的变换版本仍是有效的阴性对照。
    """
    out = []
    for s in seqs:
        t = s["terms"]
        d = [t[i + 1] - t[i] for i in range(len(t) - 1)]
        ps, acc = [], 0
        for v in t:
            acc += v
            ps.append(acc)
        binom = [sum(comb(n, k) * t[k] for k in range(n + 1)) for n in range(len(t))]
        inv = [sum((-1) ** (n - k) * comb(n, k) * t[k] for k in range(n + 1))
               for n in range(len(t))]
        for tag, arr in (("diff", d), ("prefix_sum", ps),
                         ("binomial", binom), ("inv_binomial", inv)):
            out.append({"id": f"{s['id']}@{tag}", "terms": arr,
                        "base": s["id"], "transform": tag})
    return out


def main() -> int:
    seqs = sq.build_sequences(sq.N_TERMS)
    ids = [s["id"] for s in seqs]
    print(f"序列数 {len(seqs)}（含新增 apery）")
    print(f"阴性对照: {sorted(NEGATIVE_CONTROLS & set(ids))}")

    rows = run_grid(seqs, range(1, 6), range(0, 5))
    print("\n order deg | 召回 假警报 | 阴性对照命中 | 耗时s")
    print(" " + "-" * 58)
    for r in rows:
        flag = "  <-- 假警报!" if r["negative_control_hits"] else ""
        print(f"   {r['order']}    {r['deg']}  |  {r['recall']:3d}   {r['false_alarms']:3d}  "
              f"| {','.join(r['negative_control_hits']) or '-':12s} | {r['seconds']:6.2f}{flag}")

    # 边际收益：从 (3,2)【当前设置】往上，每步新增了哪些序列
    base = {(r["order"], r["deg"]): r for r in rows
            if (r["order"], r["deg"]) == (sq.P_ORDER_MAX, sq.P_DEG_MAX)}
    cur = base[(sq.P_ORDER_MAX, sq.P_DEG_MAX)]["per_seq"]
    print(f"\n当前设置 (order={sq.P_ORDER_MAX}, deg={sq.P_DEG_MAX}) "
          f"召回 {base[(sq.P_ORDER_MAX, sq.P_DEG_MAX)]['recall']} 条："
          f"{sorted(k for k, v in cur.items() if v)}")

    prev = cur
    for k, d in [(3, 3), (3, 4), (4, 2), (4, 3), (5, 2), (5, 3), (5, 4)]:
        r = next((x for x in rows if (x["order"], x["deg"]) == (k, d)), None)
        if r is None:
            continue
        new = [s for s in ids if r["per_seq"].get(s, 0) > prev.get(s, 0)]
        lost = [s for s in ids if r["per_seq"].get(s, 0) < prev.get(s, 0)]
        print(f"  → (order={k}, deg={d}): 召回 {r['recall']} "
              f"(+{r['recall'] - sum(prev.values())}) 新增={new or '无'} "
              f"丢失={lost or '无'} 假警报={r['false_alarms']} "
              f"阴性命中={r['negative_control_hits'] or '无'} 耗时={r['seconds']}s")
        prev = r["per_seq"]

    # apery 这一条单独说清楚：它是 deg 3 才够的硬校准件
    print("\napery（order 2 / deg 3 硬校准件）在各参数下是否被召回：")
    for r in rows:
        if r["per_seq"].get("apery"):
            print(f"   order={r['order']} deg={r['deg']} → {r['per_seq']['apery']} 条候选"
                  f"（外推通过者计入召回）")
    print("   以上未列出的参数组合 = 报不出来")

    # ---- 变换库：差分会把次数抬高，只看基础库会漏判 deg 的收益 ----
    print("\n[变换库] 差分 / 部分和 / 二项 / 逆二项 后的序列，各参数下的召回")
    tlib = transformed_library(seqs)
    tids = [s["id"] for s in tlib]
    neg_t = [i for i in tids if i.split("@")[0] in NEGATIVE_CONTROLS]
    print(f"  变换序列 {len(tlib)} 条；阴性对照 {len(neg_t)} 条")
    print("  order deg | 召回 假警报 | 阴性对照命中 | 耗时s")
    print("  " + "-" * 56)
    trows = []
    for k, d in [(3, 2), (3, 3), (3, 4), (4, 3), (4, 4)]:
        t0 = time.perf_counter()
        n_pass = n_fail = 0
        neg_hit = []
        per_seq = {}
        for s in tlib:
            cands = sq.discover_polynomial_recurrence(s["terms"], max_order=k, max_deg=d)
            good = [c for c in cands if c.get("survived_extrapolation")]
            bad = [c for c in cands if not c.get("survived_extrapolation")
                   and not c.get("skipped")]
            n_pass += len(good)
            n_fail += len(bad)
            per_seq[s["id"]] = len(good)
            if s["base"] in NEGATIVE_CONTROLS and (good or bad):
                neg_hit.append(s["id"])
        r = {"order": k, "deg": d, "recall": n_pass, "false_alarms": n_fail,
             "negative_control_hits": neg_hit,
             "seconds": round(time.perf_counter() - t0, 2), "per_seq": per_seq}
        trows.append(r)
        flag = "  <-- 假警报!" if neg_hit else ""
        print(f"    {k}    {d}  |  {n_pass:3d}   {n_fail:3d}  "
              f"| {','.join(neg_hit) or '-':12s} | {r['seconds']:6.2f}{flag}")

    base_t = next(r for r in trows if (r["order"], r["deg"]) == (sq.P_ORDER_MAX, sq.P_DEG_MAX))
    prev_t = base_t["per_seq"]
    print(f"\n  当前设置 (order={sq.P_ORDER_MAX}, deg={sq.P_DEG_MAX}) 召回 {base_t['recall']} 条")
    for k, d in [(3, 4), (4, 3), (4, 4)]:
        r = next(x for x in trows if (x["order"], x["deg"]) == (k, d))
        new = [s for s in tids if r["per_seq"].get(s, 0) > prev_t.get(s, 0)]
        lost = [s for s in tids if r["per_seq"].get(s, 0) < prev_t.get(s, 0)]
        print(f"    → (order={k}, deg={d}): 召回 {r['recall']} "
              f"(+{r['recall'] - sum(prev_t.values())}) 新增={new or '无'} "
              f"丢失={lost or '无'} 假警报={r['false_alarms']} "
              f"阴性命中={r['negative_control_hits'] or '无'} 耗时={r['seconds']}s")
        prev_t = r["per_seq"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
