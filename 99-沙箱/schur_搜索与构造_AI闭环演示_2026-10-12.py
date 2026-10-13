# -*- coding: utf-8 -*-
"""
OpenMath / 99-沙箱 · 「AI 破解数学难题」机制演示：Schur 数

演示的不是一个"答案"，而是那条真正起作用的闭环：
    猜想生成 -> 机器证伪/修正 -> 构造 or 搜索 -> 独立验证器 -> 诚实标注等级

研究对象：Schur 数 S(k)。
定义：S(k) = 最大的 n，使得 {1..n} 可以被 k 染色且不存在同色三元组满足 x + y = z
      （x = y 允许）。等价说法：S(k) = 最大的 n 使 [1,n] 可划分为 k 个无和集。

证据等级（对齐 05-验证中心/00-验证协议）：
    L2  数值/穷举验证（有限范围内的完整搜索）
    L3  符号/构造性证明（本脚本用显式构造并在机器上核验）
    L4  形式化证明（Lean）——本脚本【未做】，因此不声称"已证明"
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


# --------------------------------------------------------------------------
# 一、验证器（判定 fa 的唯一真源，任何结论都必须过这一关）
# --------------------------------------------------------------------------
def find_bad_triples(coloring, n, limit=5):
    """返回违反 'x+y=z 同色' 的三元组列表（最多 limit 个）。空列表 = 通过。"""
    bad = []
    for z in range(1, n + 1):
        cz = coloring[z]
        for x in range(1, z // 2 + 1):          # x <= y，覆盖 x == y 情形
            y = z - x
            if coloring[x] == cz and coloring[y] == cz:
                bad.append((x, y, z))
                if len(bad) >= limit:
                    return bad
    return bad


def verify(coloring, n):
    """完整核验：长度、色数、越界值都要检查（防'看着像'的假证书）。"""
    if not isinstance(coloring, (list, tuple)):
        return False, "类型错误"
    if len(coloring) != n + 1:
        return False, "长度错：期望 %d，实得 %d" % (n + 1, len(coloring))
    used = set()
    for i in range(1, n + 1):
        c = coloring[i]
        if not isinstance(c, int) or c < 0:
            return False, "第 %d 位非法取值 %r" % (i, c)
        used.add(c)
    bad = find_bad_triples(coloring, n)
    if bad:
        return False, "存在同色 Schur 三元组 %r" % (bad,)
    return True, "OK: n=%d，用到 %d 种颜色，无同色 x+y=z" % (n, len(used))


def verify_by_classes(coloring, n):
    """
    第二条代码路径（交叉校验用）：按颜色分组，检查组内任意两元素之和是否仍在组内。
    与 find_bad_triples 的'枚举三元组'是完全不同的实现，避免同源 bug 同时污染两条路径。
    """
    classes = {}
    for i in range(1, n + 1):
        classes.setdefault(coloring[i], set()).add(i)
    for c, members in sorted(classes.items()):
        for x in members:
            for y in members:
                if (x + y) in members:
                    return False, "色类 %d 违反：%d + %d = %d 同色" % (c, x, y, x + y)
    return True, "第二路径 OK：%d 个色类，组内两两之和均不在组内" % len(classes)


# --------------------------------------------------------------------------
# 二、搜索器：DFS + 前向检查(forb 位掩码) + MRV 动态选元 + 对称性破缺
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# 二之二、引擎 B：WalkSAT 式局部搜索（不完备，不能证明上界，但可能更快找到证书）
# --------------------------------------------------------------------------
def triples_of(n):
    ts = []
    for z in range(1, n + 1):
        for x in range(1, z // 2 + 1):
            ts.append((x, z - x, z))
    return ts


def local_search(n, k, deadline, seed=12345, walk_p=0.25, init=None):
    """
    min-conflicts + 随机游走。注意：本引擎【不完备】，
    它说"没找到"不代表不存在；它说"找到了"也必须交给 verify() 复核。
    内部冲突数每步全量重算（不用增量记账——本脚本开发过程中，
    增量记账版本曾自称 total=0 而独立验证器查出 6 个违反三元组）。
    """
    import random as _rd
    ts = triples_of(n)
    part = {}
    for i in range(1, n + 1):
        part[i] = []
    for idx, t in enumerate(ts):
        for a in set(t):
            part[a].append(idx)
    _rd.seed(seed)
    col = [_rd.randrange(k) for _ in range(n + 1)]
    if init is not None:                       # 热启动：沿用已知的较短证书
        m = min(len(init) - 1, n)
        for i in range(1, m + 1):
            if isinstance(init[i], int):
                col[i] = init[i]
    steps, best, restarts = 0, None, 1
    t_start = time.time()
    while time.time() < deadline:
        total = sum(1 for t in ts if col[t[0]] == col[t[1]] == col[t[2]])
        if total == 0:
            best = list(col)
            break
        bad = [t for t in ts if col[t[0]] == col[t[1]] == col[t[2]]]
        v = _rd.choice(_rd.choice(bad))
        if _rd.random() < walk_p:
            col[v] = _rd.randrange(k)
        else:
            old, bestd, bestc = col[v], None, col[v]
            for c in range(k):
                if c == old:
                    continue
                col[v] = c
                d = sum(1 for i in part[v] if col[ts[i][0]] == col[ts[i][1]] == col[ts[i][2]])
                if bestd is None or d < bestd or (d == bestd and _rd.random() < 0.3):
                    bestd, bestc = d, c
            col[v] = bestc
        steps += 1
    return {"found": best is not None, "coloring": best, "steps": steps,
            "restarts": restarts, "ms": round((time.time() - t_start) * 1000, 1)}


class Timeout(Exception):
    pass


def _popcount(x):
    return bin(x).count("1")


def search_schur(n, k, deadline, tie="large"):
    """
    在 [1..n] 上找 k 染色使其无同色 x+y=z。
    返回 dict: {"found": bool, "coloring": list|None, "nodes": int,
                "ms": float, "timeout": bool}
    对称性破缺：颜色按"首次出现的先后"引入（第 m 色不得早于第 m-1 色出现），
                并固定 color[1] = 0。这不损失一般性，因为颜色标签可任意置换。
    """
    color = [None] * (n + 1)
    forb = [0] * (n + 1)          # 每个未赋值元素的禁色集合（位掩码）
    assigned = []
    used_mask = [0]
    nodes = [0]
    solution = [None]
    started = time.time()

    def allowed_mask(u):
        m = used_mask[0]
        c = 0
        while c < k and (m >> c) & 1:          # 找第一个未使用过的颜色下标
            c += 1
        if c < k:
            m |= (1 << c)                      # 只允许"已用色 + 下一个新色"
        return m & ~forb[u]

    def pick(layer):
        # MRV：可用色数最少者优先；平局按 tie 偏好（large = 大下标优先）
        best_u, best_cnt, best_last = -1, 99, None
        for u in range(1, n + 1):
            if color[u] is not None:
                continue
            m = allowed_mask(u)
            cnt = _popcount(m)
            if cnt == 0:
                return u, 0                     # 死路
            if cnt < best_cnt or (cnt == best_cnt and tie == "large" and u > best_u):
                best_u, best_cnt = u, cnt
            best_last = u
        return best_u, best_cnt

    def dfs(layer):
        if time.time() > deadline:
            raise Timeout()
        nodes[0] += 1
        if layer == n:
            solution[0] = list(color)
            return True
        u, cnt = pick(layer)
        if cnt == 0 or u == -1:
            return False
        mask = allowed_mask(u)
        for c in range(k):
            if not (mask >> c) & 1:
                continue
            bit = 1 << c
            color[u] = c
            assigned.append(u)
            new_used = not (used_mask[0] & bit)
            if new_used:
                used_mask[0] |= bit
            added = []
            conflict = False
            # 前向检查 / 冲突检查：必须双向看，否则会漏掉
            #   (1) u + v  ->  未来的和值不得取该色（或已是该色则冲突）
            #   (2) u - v  ->  已赋值的两元素之和等于 u（此时 u-v 已被赋同色则冲突）
            for v in assigned:                 # 含 v == u，覆盖 2u 情形
                if color[v] != c:
                    continue
                s = u + v
                if s <= n:
                    if color[s] == c:
                        conflict = True
                        break
                    if color[s] is None and not (forb[s] & bit):
                        forb[s] |= bit
                        added.append(s)
                d = u - v
                if d >= 1 and color[d] == c:
                    conflict = True
                    break
            if not conflict and dfs(layer + 1):
                return True
            for s in added:                    # 撤销前向检查
                forb[s] &= ~bit
            assigned.pop()
            color[u] = None
            if new_used:
                used_mask[0] &= ~bit
        return False

    color[1] = 0
    assigned.append(1)
    used_mask[0] |= 1
    timeout = False
    found = False
    try:
        found = dfs(1)
    except Timeout:
        timeout = True
    return {
        "found": found,
        "coloring": solution[0],
        "nodes": nodes[0],
        "ms": round((time.time() - started) * 1000, 1),
        "timeout": timeout,
    }


def largest_colorable(k, nmax, budget_sec, tie="large"):
    """从小到大找最大的可染色 n（用于下界）。返回 (best_n, coloring, 记录)。"""
    best_n, best_col, log = 0, None, []
    t_end = time.time() + budget_sec
    for n in range(1, nmax + 1):
        r = search_schur(n, k, t_end, tie=tie)
        log.append({"n": n, "found": r["found"], "timeout": r["timeout"],
                    "nodes": r["nodes"], "ms": r["ms"]})
        if not r["found"]:
            break
        best_n, best_col = n, r["coloring"]
        if time.time() > t_end:
            break
    return best_n, best_col, log


# --------------------------------------------------------------------------
# 三、构造性定理：S(k+1) >= 3*S(k) + 1
#     给定 [1..n] 的无 Schur k-染色 c，构造 [1..3n+1] 的 (k+1)-染色 d：
#         d(m) = c(m)                 m in [1, n]
#         d(m) = k  (新色)            m in [n+1, 2n+1]
#         d(m) = c(m - (2n+1))        m in [2n+2, 3n+1]
#     证明要点（逐情形）：
#       (a) 新色块 [n+1,2n+1]：两元素之和 >= 2n+2 > 2n+1，故块内无 x+y=z
#       (b) 老色类扩张 Ci = Ai U (2n+1 + Ai)：
#           - Ai 内两两之和不在 Ai，且 <= 2n < 2n+2 故也不落进位移块
#           - 位移块内两两之和 > 3n+1，越界
#           - Ai 元素 x 与位移块元素 (2n+1+b) 之和 = 2n+1 + (x+b)，
#             它属于位移块当且仅当 x+b in Ai，而这被 Ai 的无和性排除
#     因此 Ci 无和，覆盖 [1,3n+1]，用了 k+1 色。
# --------------------------------------------------------------------------
def extend_coloring(coloring, n, new_color):
    N = 3 * n + 1
    out = [None] * (N + 1)
    for m in range(1, n + 1):
        out[m] = coloring[m]
    for m in range(n + 1, 2 * n + 2):
        out[m] = new_color
    for m in range(2 * n + 2, N + 1):
        out[m] = coloring[m - (2 * n + 1)]
    return out, N


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=60.0,
                    help="k>=4 的整体时间预算（秒）")
    ap.add_argument("--climb", type=float, default=60.0,
                    help="证书热启动爬升的时间预算（秒）")
    ap.add_argument("--nmax", type=int, default=64, help="搜索的最大 n")
    ap.add_argument("--tie", default="large", choices=["large", "small"])
    args = ap.parse_args()

    t0 = time.time()
    items, guards = [], []

    # ---- 阳性对照：验证器本身必须先被证明"会报错" ----
    mono = [0] * 9
    for m in range(1, 9):
        mono[m] = 0
    ok_bad, msg_bad = verify(mono, 8)                     # 全同色，必有 x+y=z
    guards.append({"id": "G1-阳性对照-全同色必被拒", "pass": (not ok_bad),
                   "detail": msg_bad})
    ok_good, msg_good = verify([0, 0, 1, 1, 0, 2], 5)     # 1->0, 2->1, 3->1, 4->0, 5->2
    guards.append({"id": "G2-已知解-3色5", "pass": (ok_good is True), "detail": msg_good})
    # 已知 S(2)=4 的一个解：[1,4] 用 2 色：{1,4},{2,3}
    sample2 = [None, 0, 1, 1, 0]
    ok_s2, msg_s2 = verify(sample2, 4)
    guards.append({"id": "G3-已知解-2色4", "pass": ok_s2, "detail": msg_s2})

    # ---- 第一步：精确值（下界=找到解，上界=S(k)+1 无解） ----
    exact = {}
    for k in (1, 2, 3):
        best, col, log = largest_colorable(k, args.nmax, budget_sec=30.0, tie=args.tie)
        upper = None
        if best > 0:
            r = search_schur(best + 1, k, time.time() + 60, tie=args.tie)
            upper = (not r["found"] and not r["timeout"])
            if upper:
                ok, msg = verify(col, best)
                exact[k] = {"S": best, "certified": ok, "check": msg,
                            "search_nodes": r["nodes"]}
            items.append({
                "id": "A-%d" % k, "level": "L2",
                "claim": "S(%d) = %d" % (k, best),
                "status": "PASS" if upper else "UNKNOWN",
                "note": ("下界由显式证书给出；上界由对 n=%d 的完整穷举（无解）给出，穷举节点数 %d"
                         % (best + 1, r["nodes"])) if upper else
                        "上界未在预算内完成穷举（超时），不得声称等于",
            })
        else:
            items.append({"id": "A-%d" % k, "level": "L2",
                          "claim": "S(%d)" % k, "status": "UNKNOWN",
                          "note": "搜索未返回结果"})

    # ---- 第二步：构造性定理的机器核验链 ----
    chain = []
    if 1 in exact and exact[1]["certified"]:
        cur_n, cur_col = 1, [None, 0]
        chain.append({"k": 1, "n": 1, "ok": True, "detail": "起点 [1] 单色，平凡无和"})
    else:
        cur_n, cur_col = 0, None
    for k in range(2, 8):
        if cur_col is None:
            break
        new_col, N = extend_coloring(cur_col, cur_n, k - 1)
        ok, msg = verify(new_col, N)
        chain.append({"k": k, "n": N, "ok": ok, "detail": msg,
                      "bound": "S(%d) >= %d" % (k, N)})
        if not ok:
            break
        cur_n, cur_col = N, new_col
    items.append({
        "id": "B-构造定理", "level": "L3",
        "claim": "S(k+1) >= 3*S(k) + 1",
        "status": "PASS" if all(c["ok"] for c in chain) else "FAIL",
        "note": "构造在机器被逐项核验至 n=%d；超出此处之外的核验本轮未执行" %
                (chain[-1]["n"] if chain else 0),
    })

    # ---- 第三步：朴素猜想的证伪（AI 流水线里最容易被跳掉的一步） ----
    naive = {"statement": "S(k+1) = 3*S(k) + 1", "status": "UNKNOWN", "witness": None}
    s3 = exact.get(3, {}).get("S")
    if s3:
        target = 3 * s3 + 1                    # 构造给出的 k=4 下界 = 40
        # 两个引擎并行尝试能否染到 target+1（一旦成功即证伪"等号总成立"）
        half = args.budget / 2.0
        ra = search_schur(target + 1, 4, time.time() + half, tie=args.tie)
        rb = local_search(target + 1, 4, time.time() + half) if (not ra["found"]) else {
            "found": False, "steps": 0, "ms": 0.0}
        engines = {
            "A_DFS完备穷举": {"found": ra["found"], "nodes": ra["nodes"],
                              "timeout": ra["timeout"], "ms": ra["ms"]},
            "B_局部搜索不完备": {"found": rb["found"], "steps": rb["steps"], "ms": rb["ms"]},
        }
        witness = None
        for tag in ("A_DFS完备穷举", "B_局部搜索不完备"):
            if tag == "A_DFS完备穷举" and ra["found"]:
                witness = ra["coloring"]
            elif tag == "B_局部搜索不完备" and rb["found"]:
                witness = rb["coloring"]
        if witness is not None:
            ok, msg = verify(witness, target + 1)          # 路径一：枚举三元组
            ok2, msg2 = verify_by_classes(witness, target + 1)   # 路径二：色类成员判别
            if ok != ok2:
                ok = False
                msg = "两条验证路径结论不一致：%s / %s" % (msg, msg2)
            guards.append({"id": "G5-双路径交叉验证-证书", "pass": (ok and ok2),
                           "detail": "路径一：%s｜路径二：%s" % (msg, msg2)})
            naive["status"] = "FALSIFIED" if ok else "UNKNOWN"
            naive["witness"] = {"n": target + 1, "check": msg, "coloring": witness}
            naive["note"] = ("构造只给到 %d，但 %gs 内搜索给出了 %d 的证书"
                             % (target, args.budget, target + 1)) if ok else \
                            "引擎自称成功但独立验证器不认可——证书作废"
        else:
            naive["status"] = "UNKNOWN"
            naive["note"] = ("两引擎在 %gs 预算内均未给出 n=%d 的证书，且穷举未收敛；"
                             "既不得声称被证伪，也不得声称成立" % (args.budget, target + 1))
        naive["engines"] = engines
    items.append({"id": "C-朴素猜想", "level": "L2", "claim": naive["statement"],
                  "status": naive["status"], "note": naive["note"]})
    items.append({
        "id": "E-双引擎对比", "level": "L2",
        "claim": "完备穷举 vs 局部搜索在同一任务上的表现",
        "status": "PASS",
        "note": json.dumps(naive.get("engines", {}), ensure_ascii=False),
    })

    # ---- 第三步之二：把证书往上爬（热启动迭代） ----
    climbs = []
    if naive.get("witness"):
        cur = naive["witness"]["coloring"]
        cur_n = naive["witness"]["n"]
        t_climb_end = time.time() + args.climb
        while cur_n < args.nmax and time.time() < t_climb_end:
            r = local_search(cur_n + 1, 4, t_climb_end, seed=1000 + cur_n, init=cur)
            if not r["found"]:
                break
            ok, msg = verify(r["coloring"], cur_n + 1)
            ok2, msg2 = verify_by_classes(r["coloring"], cur_n + 1)
            if not (ok and ok2):
                break                          # 引擎自称成功但验证器不认可：立即停，不记账
            cur, cur_n = r["coloring"], cur_n + 1
            climbs.append({"n": cur_n, "ms": r["ms"], "steps": r["steps"], "check": msg})
        if climbs:
            note = ("由 n=%d 的证书起热启动迭代，机器把证书推到 n=%d（共 %d 级）；"
                    "每一级都经独立验证器复核。这是下界，不是等号。" %
                    (naive["witness"]["n"], cur_n, len(climbs)))
        else:
            note = ("以 n=%d 的证书热启动迭代 %.0fs，未能取到 n=%d 的证书；"
                    "当前下界仍为 n=%d。没有结果就是没有结果，不得改写成进展。" %
                    (naive["witness"]["n"], args.climb, cur_n + 1, cur_n))
        items.append({
            "id": "F-下界爬升", "level": "L2",
            "claim": "S(4) >= %d" % cur_n,
            "status": "PASS",
            "note": note,
        })
    naive["climb"] = climbs
    payload_climb = climbs

    # ---- 第四步：诚实边界 ----
    items.append({
        "id": "D-边界", "level": "L2",
        "claim": "S(5) 的精确值",
        "status": "UNKNOWN",
        "note": "本轮只得到构造给出的下界（见 chain），未做任何形式化证明(L4)；"
                "搜索规模随 n 指数增长，穷举到 S(5) 的实际量级远超本次算力预算。",
    })

    guards_pass = sum(1 for g in guards if g["pass"])

    # ---- 交叉核对：搜索器算出的精确值必须与教科书上的已知值一致 ----
    # 这是一条"阳性对照"：若搜索器有 bug（例如漏了某个方向的约束检查），
    # 这里会立刻报警，而不是让错误的 S(k) 流入后面的结论。
    KNOWN = {1: 1, 2: 4, 3: 13}
    for k, expect in KNOWN.items():
        got = exact.get(k, {}).get("S")
        guards.append({
            "id": "G4-搜索器交叉核对-S(%d)=%d" % (k, expect),
            "pass": (got == expect),
            "detail": "本机算出 %r，教科书值 %r" % (got, expect),
        })
        if got != expect:
            for it in items:
                if it["id"] == "A-%d" % k:
                    it["status"] = "ERROR"
                    it["note"] = ("搜索器结果与教科书值不一致（算得 %r）"
                                  "——下游结论一律作废，不得使用。" % (got,))
    guards_pass = sum(1 for g in guards if g["pass"])
    payload = {
        "topic": "Schur number demo for AI-solves-math pipeline",
        "date": "2026-10-12",
        "provenance": {"ai_assisted": True,
                       "role": "起草 + 搜索 + 核验；结论等级由脚本直出，未人工上调"},
        "guards": guards,
        "items": items,
        "exact": {str(k): v for k, v in exact.items()},
        "construction_chain": chain,
        "naive_conjecture": naive,
        "climb_ladder": payload_climb if 'payload_climb' in dir() else [],
        "budget_sec": args.budget,
        "elapsed_sec": round(time.time() - t0, 2),
        "python": sys.version.split()[0],
    }

    base = os.path.join(HERE, "schur_AI闭环演示_2026-10-12")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    lines = []
    lines.append("# Schur 数：AI 解数学难题的闭环演示（2026-10-12）\n")
    lines.append("- 脚本：`99-沙箱/schur_搜索与构造_AI闭环演示_2026-10-12.py`（纯标准库）")
    lines.append("- 原始读数：`99-沙箱/schur_AI闭环演示_2026-10-12.json`\n")
    lines.append("## 自检（验证器必须先被证明会报错）")
    for g in guards:
        lines.append("- [%s] %s：%s" % ("PASS" if g["pass"] else "FAIL", g["id"], g["detail"]))
    lines.append("\n自检 %d/%d" % (guards_pass, len(guards)))
    lines.append("\n## 结论（等级/状态均按本机脚本直出）")
    for it in items:
        lines.append("- **%s**（%s，%s）：%s" % (it["claim"], it["status"], it["level"], it["note"]))
    lines.append("\n## 构造链 S(k+1) >= 3*S(k)+1 的逐项核验")
    for c in chain:
        lines.append("- k=%d，构造出 n=%d：%s｜%s" % (c["k"], c["n"], c.get("bound", ""), c["detail"]))
    lines.append("\n## 诚实边界")
    lines.append("- 本脚本最高证据等级为 L2/L3：**未做 Lean 形式化（L4）**，故不声称\"已证明\"。")
    lines.append("- 构造 S(k+1) >= 3S(k)+1 是经典路径上的标准构造，本演示**不主张首创**。")
    lines.append("- 凡超时/未完成的判定一律为 UNKNOWN，不得改写成 PASS。")
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    sys.stdout.write("guards %d/%d\n" % (guards_pass, len(guards)))
    for it in items:
        sys.stdout.write("[%-18s][%s] %s\n" % (it["status"], it["level"], it["claim"]))
    for c in chain:
        sys.stdout.write("chain k=%d n=%d ok=%s\n" % (c["k"], c["n"], c["ok"]))
    sys.stdout.write("elapsed %.1fs\n" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
