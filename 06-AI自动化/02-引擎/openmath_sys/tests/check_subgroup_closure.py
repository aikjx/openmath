# -*- coding: utf-8 -*-
"""Task 21 护栏：新子群枚举（join 闭包）vs 旧枚举（指数级子集枚举）逐群对账。

对账用的是**另一个算法**（穷举含单位元的子集 + 闭包），不是同一套代码的两条路径，
所以一致才是真证据。另外再验一组教科书子群计数。
"""
import itertools
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openmath_sys import structure as st  # noqa: E402
from openmath_sys import theoryforge as tf  # noqa: E402


def old_enumeration(table, identity):
    """旧算法：枚举全部含单位元的子集，取闭包，只留真子群。"""
    n = len(table)
    op = lambda i, j: table[i][j]

    def closure(seed):
        s = set(seed)
        s.add(identity)
        changed = True
        while changed:
            changed = False
            for a in list(s):
                for b in list(s):
                    c = op(a, b)
                    if c not in s:
                        s.add(c)
                        changed = True
        return tuple(sorted(s))

    found = set()
    others = [x for x in range(n) if x != identity]
    for r in range(0, len(others) + 1):
        for combo in itertools.combinations(others, r):
            cl = closure(combo)
            if len(cl) < n:
                found.add(cl)
    return sorted(found, key=lambda t: (len(t), t))


# 教科书子群计数（含平凡子群与群自身的**真子群**个数）
KNOWN_PROPER_SUBGROUP_COUNTS = {
    "Z1": 0, "Z2": 1, "Z3": 1, "Z4": 2, "Z5": 1, "Z6": 3,
    "Z7": 1, "Z8": 3, "Z9": 2, "Z10": 3, "Z11": 1, "Z12": 5,
    "S3": 5, "D2": 4, "D3": 5, "D4": 9, "D5": 7, "D6": 15,
    "Q8": 5, "Z2xZ2": 4, "Z2xZ3": 3, "Z2xZ4": 7, "Z3xZ3": 5,
}


def main() -> int:
    groups = tf.build_group_library(extended=False)
    disagree = []
    unknown_fact = []
    t_new = t_old = 0.0

    for g in groups:
        table = g["raw"]
        n = len(table)
        info = st.analyze_group(table)
        if not info["is_group"] or info["identity"] is None:
            continue
        ident = info["identity"]

        t0 = time.perf_counter()
        new_subs = [s for s in st._subgroup_join_closure(
            lambda i, j: table[i][j], n, ident) if len(s) < n]
        t1 = time.perf_counter()
        old_subs = old_enumeration(table, ident)
        t2 = time.perf_counter()
        t_new += t1 - t0
        t_old += t2 - t1

        if new_subs != old_subs:
            disagree.append((g["label"], len(new_subs), len(old_subs)))

        want = KNOWN_PROPER_SUBGROUP_COUNTS.get(g["label"])
        if want is not None and len(new_subs) != want:
            unknown_fact.append((g["label"], len(new_subs), want))

    print(f"对账群数            : {len(groups)}")
    print(f"新算法 vs 旧枚举分歧 : {len(disagree)}")
    for d in disagree:
        print("   分歧:", d)
    print(f"教科书计数不符       : {len(unknown_fact)}")
    for d in unknown_fact:
        print("   不符:", d)
    print(f"耗时  新={t_new:.3f}s  旧={t_old:.3f}s  加速={t_old / max(t_new, 1e-9):.1f}x")

    # 16 阶：旧算法要多久 vs 新算法
    t16 = tf.build_group_library(extended=True)
    n16 = [g for g in t16 if len(g["raw"]) == 16]
    print(f"\n库中 16 阶群数       : {len(n16)}")

    return 1 if (disagree or unknown_fact) else 0


if __name__ == "__main__":
    sys.exit(main())
