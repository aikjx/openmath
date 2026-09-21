# -*- coding: utf-8 -*-
"""探查：16 阶候选构造里到底能分出几个互不同构的群（教科书计数 14）。

不变量指纹故意做得比较细——元素阶多重集 + 共轭类大小多重集 + 子群格剖面
（每个子群的 (阶, 是否交换, 指数)）+ 中心/正规子群数。指纹相同**不代表**同构，
所以若指纹数 < 候选构造的直觉分类数，必须如实写"可能漏"，不得硬凑到 14。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openmath_sys import structure as st  # noqa: E402


def inv_map(table, ident):
    n = len(table)
    inv = {}
    for a in range(n):
        for b in range(n):
            if table[a][b] == ident:
                inv[a] = b
                break
    return inv


def induced_table(table, members):
    ms = sorted(members)
    pos = {e: i for i, e in enumerate(ms)}
    return [[pos[table[a][b]] for b in ms] for a in ms]


def fingerprint(table):
    info = st.analyze_group(table)
    assert info["is_group"], "构造不是群"
    n = len(table)
    ident = info["identity"]

    subs = [tuple(s) for s in info["proper_subgroups"]] + [tuple(range(n))]
    inv = inv_map(table, ident)
    # 共轭类
    conj = {}
    for x in range(n):
        cls = frozenset(table[table[g][x]][inv[g]] for g in range(n))
        conj[x] = cls
    classes = {}
    for x in range(n):
        rep = min(conj[x])
        classes.setdefault(rep, set()).add(x)

    sub_profile = []
    for s in subs:
        t2 = induced_table(table, s)
        i2 = st.analyze_group(t2)
        sub_profile.append((len(s), int(i2["abelian"]), i2["exponent"]))
    sub_profile.sort()

    # 正规子群计数
    normal = 0
    for s in subs:
        ss = set(s)
        if all(table[table[g][x]][inv[g]] in ss
               for g in range(n) for x in s):
            normal += 1

    return (
        n,
        int(info["abelian"]),
        info["exponent"],
        info["center_size"],
        len(classes),
        info["proper_subgroups_count"],
        normal,
        tuple(sorted(info["element_orders"])),
        tuple(sorted(len(c) for c in classes.values())),
        tuple(sub_profile),
    )


def main() -> int:
    cands = st.order16_candidates()
    print(f"候选构造数: {len(cands)}")

    bad = []
    by_fp = {}
    for name, t in cands:
        info = st.analyze_group(t)
        if len(t) == 8 and name == "Q8":
            # Q8 只是 8 阶构造件，单独验一次群公理后跳过 16 阶计数
            assert info["is_group"], "Q8 构造不是群"
            assert sorted(info["element_orders"]) == [1, 2, 4, 4, 4, 4, 4, 4], \
                "Q8 构造的元素阶不对"
            continue
        if len(t) != 16 or not info["is_group"]:
            bad.append((name, len(t), info["is_group"],
                        info["associative"], info["inverses_exist"]))
            continue
        fp = fingerprint(t)
        by_fp.setdefault(fp, []).append(name)

    print(f"验不过群公理 / 阶不对: {len(bad)}")
    for b in bad:
        print("   ", b)
    print(f"\n互不相同的指纹数: {len(by_fp)}   （教科书计数 14）")
    for fp, names in sorted(by_fp.items(), key=lambda kv: kv[1][0]):
        print(f"  n={fp[0]} ab={fp[1]} exp={fp[2]} |Z|={fp[3]} cls={fp[4]} "
              f"sub={fp[5]} nrm={fp[6]}")
        print(f"       阶多重集={fp[7]}")
        print(f"       代表={names[0]}  同指纹={names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
