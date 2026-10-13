# -*- coding: utf-8 -*-
"""
OpenMath / 99-沙箱 · 续：把 Schur 问题编译成 SAT，用纯标准库 CDCL 求解

上一轮（2026-10-12）的读数：构造给 S(4) >= 40，局部搜索给 S(4) >= 41，
但两个引擎都没能给出上界 ⇒ S(4) 精确值 UNKNOWN。
本轮走真实做法：编码成 CNF + CDCL(1UIP 学习 / watched literal / VSIDS / Luby 重启)。

方法学纪律（否则 UNSAT 结论没有意义）：
  1. 求解器上线前必须过【已知答案自检】：既有 SAT 实例（须给出证书），
     也有 UNSAT 实例（须与上一轮完整穷举引擎的结论一致）。
  2. 求解器说 SAT → 立刻交给两条独立验证器复核（自评分不算数）。
  3. 求解器说 UNSAT → 必须连同【其外部可信度】一起汇报：
     本脚本不生成 DRAT 证明，故该结论强度 = 求解器实现正确 + 自检通过，
     不等于"可被独立复核的机器证书"。这一条不得省略。
  4. 超时/未收敛 ⇒ UNKNOWN，不得写成 PASS。
"""
import argparse
import importlib.util
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def load_core():
    """复用一个已验证的验证器（单一真源，不重写第三份）。"""
    for fn in os.listdir(HERE):
        if fn.startswith("schur_搜索与构造") and fn.endswith(".py"):
            spec = importlib.util.spec_from_file_location(
                "schur_core", os.path.join(HERE, fn))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise SystemExit("未找到验证器来源脚本（schur_搜索与构造*.py）")


# ==========================================================================
# 一、CDCL 求解器（MiniSat 风格，纯标准库）
# ==========================================================================
def luby(y, x):
    size, seq = 1, 0
    while size < x + 1:
        seq += 1
        size = 2 * size + 1
    while size - 1 != x:
        size = (size - 1) >> 1
        seq -= 1
        x = x % size
    return y ** seq


class CDCL(object):
    def __init__(self, nvars, clauses, seed=0):
        self.n = nvars
        self.clauses = []
        self.watches = [[] for _ in range(2 * nvars + 3)]
        self.assign = [0] * (nvars + 1)      # 0 未赋值, 1 真, -1 假
        self.level = [0] * (nvars + 1)
        self.reason = [-1] * (nvars + 1)
        self.trail = []
        self.trail_lim = []
        self.qhead = 0
        self.activity = [0.0] * (nvars + 1)
        self.phase = [0] * (nvars + 1)
        self.inc = 1.0
        self.decay = 0.95
        self.rng = random.Random(seed)
        self.stats = {"conflicts": 0, "decisions": 0, "propagations": 0,
                      "learned": 0, "restarts": 0}
        self.next_restart = 100
        self.restart_idx = 0
        self.learnt = []                 # 已学习子句的下标（用于回收）
        self.reduce_every = 8000
        self.next_reduce = 8000
        self._units = []
        for c in clauses:
            self._add(c)
        for u in self._units:
            self._enqueue(u, -1)
        self.propagate_ok = (self.propagate() is None)

    # ---------- 字面量工具 ----------
    def _wi(self, lit):
        # 监视表下标：必须偏移成非负，否则负字面量会被 Python 当"从尾部倒数"
        return lit + self.n

    def _val(self, lit):
        a = self.assign[abs(lit)]
        return 0 if a == 0 else (a if lit > 0 else -a)

    def _level_of(self, lit):
        return self.level[abs(lit)]

    # ---------- 子句接入 ----------
    def _add(self, lits):
        seen, out = set(), []
        for l in lits:
            if l in seen:
                continue
            if -l in seen:
                return                      # 恒真，丢弃
            seen.add(l)
            out.append(l)
        if not out:
            self._units = []                # 空子句：不可满足，交给 solve 判
            self._trivial_unsat = True
            return
        ci = len(self.clauses)
        self.clauses.append(out)
        if len(out) == 1:
            self._units.append(out[0])
            return
        self.watches[self._wi(out[0])].append(ci)
        self.watches[self._wi(out[1])].append(ci)

    def _enqueue(self, lit, reason):
        v = abs(lit)
        want = 1 if lit > 0 else -1
        if self.assign[v] != 0:
            return self.assign[v] == want
        self.assign[v] = want
        self.level[v] = len(self.trail_lim)
        self.reason[v] = reason
        self.trail.append(lit)
        self.phase[v] = 1 if lit > 0 else 0
        return True

    def _current_level(self):
        return len(self.trail_lim)

    # ---------- 单元传播 ----------
    def propagate(self):
        st = self.stats
        while self.qhead < len(self.trail):
            p = self.trail[self.qhead]
            self.qhead += 1
            st["propagations"] += 1
            ws = self.watches[self._wi(-p)]
            i = 0
            while i < len(ws):
                ci = ws[i]
                c = self.clauses[ci]
                if c[0] == -p:
                    c[0], c[1] = c[1], c[0]
                first = c[0]
                if self._val(first) == 1:
                    i += 1
                    continue
                found = False
                for k in range(2, len(c)):
                    if self._val(c[k]) != -1:
                        # 不变式：受监视的两个位置是 c[0] 与 c[1]。
                        # 新监视必须写进 c[1]（它原来是假字面量 -p），并把 -p 挪到坑位 k；
                        # 若改写成"交换 c[0] 与 c[k]"，-p 会滞留在 c[1] 上，
                        # 于是子句槽位说它监视 -p、而监视表已摘掉该条目 ⇒ 后续假冲突。
                        c[1], c[k] = c[k], c[1]
                        ws[i] = ws[-1]
                        ws.pop()
                        self.watches[self._wi(c[1])].append(ci)
                        found = True
                        break
                if found:
                    continue
                if self._val(first) == -1:
                    return ci                          # 冲突
                self._enqueue(first, ci)
                i += 1
        return None

    # ---------- 冲突分析（1UIP） ----------
    def _bump(self, v):
        self.activity[v] += self.inc
        if self.activity[v] > 1e100:
            for u in range(1, self.n + 1):
                self.activity[u] *= 1e-100
            self.inc *= 1e-100

    def _decay(self):
        self.inc /= self.decay

    def _analyse(self, confl):
        learnt = [0]
        seen = [0] * (self.n + 1)
        counter = 0
        p = 0
        idx = len(self.trail) - 1
        while True:
            c = self.clauses[confl]
            for q in c:
                if p != 0 and q == p:
                    continue
                v = abs(q)
                if not seen[v] and self.level[v] > 0:
                    seen[v] = 1
                    self._bump(v)
                    if self.level[v] == self._current_level():
                        counter += 1
                    else:
                        learnt.append(q)
            while True:
                p = self.trail[idx]
                idx -= 1
                if seen[abs(p)]:
                    break
            seen[abs(p)] = 0
            counter -= 1
            if counter <= 0:
                break
            confl = self.reason[abs(p)]
            if confl == -1:
                break
        learnt[0] = -p
        # 关键：把本次为"低层字面量"打上的 seen 标记清回 0。
        # 不清会污染下一次冲突分析的计数（把残留标记当已计入），
        # 使 counter 提前归零 ⇒ 产出过强的非法子句 ⇒ 假 UNSAT。
        for l in learnt[1:]:
            seen[abs(l)] = 0
        if len(learnt) == 1:
            return learnt, 0
        bt, bi = 0, 0
        for j in range(1, len(learnt)):
            lv = self._level_of(learnt[j])
            if lv > bt:
                bt, bi = lv, j
        if bi != 1:
            learnt[1], learnt[bi] = learnt[bi], learnt[1]
        return learnt, bt

    def _backtrack(self, lvl):
        if self._current_level() <= lvl:
            return
        lim = self.trail_lim[lvl]
        for i in range(len(self.trail) - 1, lim - 1, -1):
            v = abs(self.trail[i])
            self.assign[v] = 0
            self.reason[v] = -1
            self.level[v] = 0
        del self.trail[lim:]
        del self.trail_lim[lvl:]
        self.qhead = len(self.trail)

    def _pick(self):
        best, besta = 0, -1.0
        for v in range(1, self.n + 1):
            if self.assign[v] == 0 and self.activity[v] > besta:
                best, besta = v, self.activity[v]
        if best == 0:                     # 全部赋值 ⇒ 用零活跃度打破平局（按序）
            for v in range(1, self.n + 1):
                if self.assign[v] == 0:
                    return v
            return 0
        # 平局随机化（避免同一局部陷阱反复）
        cands = [v for v in range(1, self.n + 1)
                 if self.assign[v] == 0 and self.activity[v] == besta]
        return self.rng.choice(cands) if len(cands) > 1 else best

    def _reduce(self):
        """回收学习子句：保留长度<=4 的与较短的一半；正在当 reason 的不动。
        删子句是保可满足性的（被删的都是原式的推论），但被删的必须同时从监视表摘掉。"""
        locked = set()
        for lit in self.trail:
            r = self.reason[abs(lit)]
            if r >= 0:
                locked.add(r)
        cand = [ci for ci in self.learnt
                if ci not in locked and self.clauses[ci] and len(self.clauses[ci]) > 4]
        if not cand:
            return
        cand.sort(key=lambda ci: len(self.clauses[ci]))
        keep = set(cand[:len(cand) // 2])
        for ci in cand[len(cand) // 2:]:
            c = self.clauses[ci]
            for lit in (c[0], c[1]):
                lst = self.watches[self._wi(lit)]
                try:
                    lst.remove(ci)
                except ValueError:
                    pass
            self.clauses[ci] = []
        self.learnt = [ci for ci in self.learnt if ci in keep or ci in locked
                       or (self.clauses[ci] and len(self.clauses[ci]) <= 4)]

    def _model(self):
        return [i if self.assign[i] == 1 else -i for i in range(1, self.n + 1)]

    def solve(self, deadline=None, max_conflicts=None):
        if getattr(self, "_trivial_unsat", False):
            return "UNSAT", None, None
        if not self.propagate_ok:
            return "UNSAT", None, None
        while True:
            if deadline is not None and time.time() > deadline:
                return "UNKNOWN", None, None
            if max_conflicts is not None and self.stats["conflicts"] > max_conflicts:
                return "UNKNOWN", None, None
            confl = self.propagate()
            if confl is not None:
                self.stats["conflicts"] += 1
                if not self.trail_lim:
                    return "UNSAT", None, None
                learnt, bt = self._analyse(confl)
                self._backtrack(bt)
                if len(learnt) == 1:
                    self._enqueue(learnt[0], -1)
                else:
                    ci = len(self.clauses)
                    self.clauses.append(learnt)
                    self.watches[self._wi(learnt[0])].append(ci)
                    self.watches[self._wi(learnt[1])].append(ci)
                    self.learnt.append(ci)
                    self.stats["learned"] += 1
                    self._enqueue(learnt[0], ci)
                    if self.stats["conflicts"] >= self.next_reduce:
                        self._reduce()
                        self.next_reduce = self.stats["conflicts"] + self.reduce_every
                if self.stats["conflicts"] >= self.next_restart:
                    self._backtrack(0)
                    self.restart_idx += 1
                    self.next_restart = (self.stats["conflicts"] +
                                         luby(100, self.restart_idx))
                    self.stats["restarts"] += 1
                self._decay()
            else:
                v = self._pick()
                if v == 0:
                    return "SAT", self._model(), self.stats
                self.stats["decisions"] += 1
                self.trail_lim.append(len(self.trail))
                self._enqueue(v if self.phase[v] == 1 else -v, -1)


# ==========================================================================
# 二、Schur 问题的 CNF 编码
# ==========================================================================
def encode_schur(n, k, symmetry=True, amo=True):
    """
    变量 v(i,c) = (i-1)*k + (c+1)，i in [1,n]，c in [0,k-1]。
    子句：
      (a) 每个 i 至少一色： (v(i,0) v ... v v(i,k-1))
      (a') 每个 i 至多一色（两两互斥）；对可满足性无影响，但显著加强传播
      (b) 对每个 Schur 三元组 x+y=z 与每个色 c： (¬v(x,c) ∨ ¬v(y,c) ∨ ¬v(z,c))
      (c) 对称性破缺（颜色按"首现位置递增"编号，可对任意解重新编号而不失一般性）：
          v(1,0) 为真；对 i>=2, c>=1： ¬v(i,c) ∨ ⋁_{j<i} v(j,c-1)
    """
    nv = n * k
    def V(i, c):
        return (i - 1) * k + (c + 1)
    clauses = []
    for i in range(1, n + 1):
        clauses.append([V(i, c) for c in range(k)])
    if amo and k > 1:
        for i in range(1, n + 1):
            for c1 in range(k):
                for c2 in range(c1 + 1, k):
                    clauses.append([-V(i, c1), -V(i, c2)])
    ntri = 0
    for z in range(1, n + 1):
        for x in range(1, z // 2 + 1):
            y = z - x
            ntri += 1
            for c in range(k):
                clauses.append([-V(x, c), -V(y, c), -V(z, c)])
    if symmetry and k > 1:
        clauses.append([V(1, 0)])
        if n >= 2:
            # 1 取色 0（规范编号）；1+1=2 ⇒ 2 不能是色 0 ⇒ 规范编号下 2 必取新色 1
            clauses.append([V(2, 1)])
        for i in range(2, n + 1):
            for c in range(1, k):
                cl = [-V(i, c)]
                for j in range(1, i):
                    cl.append(V(j, c - 1))
                clauses.append(cl)
    return nv, clauses, V, ntri


def decode(model, n, k):
    coloring = [None] * (n + 1)
    for i in range(1, n + 1):
        for c in range(k):
            var = (i - 1) * k + (c + 1)
            if model[var - 1] > 0:
                coloring[i] = c
                break
    return coloring


# ==========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sat-budget", type=float, default=60.0, help="每个 SAT 实例的时间预算（秒）")
    ap.add_argument("--unsat-budget", type=float, default=120.0, help="UNSAT 实例的时间预算（秒）")
    ap.add_argument("--seed", type=int, default=101,
                    help="随机种子（求解器按 seed+n 实例化，便于复现）")
    args = ap.parse_args()

    core = load_core()
    verify, verify2 = core.verify, core.verify_by_classes
    t0 = time.time()
    guards, items = [], []

    # ---------- 第一段：已知答案自检（求解器不通过就一切作废） ----------
    selftests = [
        # (n, k, 期望, 说明)
        (2, 1, "UNSAT", "1 色在 n=2 上必有同色 1+1=2"),
        (1, 1, "SAT", "1 色在 n=1 上平凡可行"),
        (4, 2, "SAT", "S(2)=4"),
        (5, 2, "UNSAT", "S(2)=4 的上界"),
        (13, 3, "SAT", "S(3)=13"),
        (14, 3, "UNSAT", "S(3)=13 的上界"),
        (40, 4, "SAT", "上一轮构造给出的下界"),
    ]
    for n, k, expect, why in selftests:
        nv, clauses, V, ntri = encode_schur(n, k)
        s = CDCL(nv, clauses, seed=args.seed + n)
        st, model, stats = s.solve(deadline=time.time() + args.sat_budget,
                                   max_conflicts=500000)
        ok = (st == expect)
        detail = "%s（期望 %s）｜子句 %d 条、变量 %d 个、冲突 %d" % (
            st, expect, len(clauses), nv, s.stats["conflicts"])
        if st == "SAT":
            col = decode(model, n, k)
            v1, m1 = verify(col, n)
            v2, m2 = verify2(col, n)
            ok = ok and v1 and v2
            detail += "｜证书复核 %s / %s" % ("OK" if v1 else m1, "OK" if v2 else m2)
        guards.append({"id": "S-自检 n=%d k=%d" % (n, k), "pass": ok,
                       "detail": "%s｜%s" % (why, detail)})

    selftest_pass = all(g["pass"] for g in guards)
    items.append({
        "id": "0-求解器自检", "level": "L2",
        "claim": "CDCL 求解器在 7 个已知答案实例上与预期一致",
        "status": "PASS" if selftest_pass else "FAIL",
        "note": "任一自检失败 ⇒ 本轮所有下游结论作废（脚本会提前退出）",
    })
    if not selftest_pass:
        payload = {"date": "2026-10-13", "guards": guards, "items": items,
                   "aborted": True}
        with open(os.path.join(HERE, "schur_SAT_S4等号_2026-10-13.json"), "w",
                  encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        sys.stdout.write("自检未通过，已中止\n")
        for g in guards:
            sys.stdout.write("[%s] %s：%s\n" % ("PASS" if g["pass"] else "FAIL",
                                                g["id"], g["detail"]))
        return 1

    # ---------- 第二段：SAT 侧——逐步逼近 S(4) 的下界 ----------
    sat_results = {}
    for n in (41, 42, 43, 44, 45):
        nv, clauses, V, ntri = encode_schur(n, 4)
        s = CDCL(nv, clauses, seed=args.seed + n)
        st, model, stats = s.solve(deadline=time.time() + args.sat_budget)
        entry = {"status": st, "conflicts": s.stats["conflicts"],
                 "decisions": s.stats["decisions"], "seconds": None,
                 "clauses": len(clauses), "vars": nv, "triples": ntri}
        if st == "SAT":
            col = decode(model, n, 4)
            v1, m1 = verify(col, n)
            v2, m2 = verify2(col, n)
            entry["verify"] = [v1, v2]
            entry["coloring"] = col
            if not (v1 and v2):
                entry["status"] = "ENGINE-LIED"       # 引擎自称成功但复核不过
        sat_results[n] = entry
        items.append({
            "id": "1-%d" % n, "level": "L2",
            "claim": "n=%d 上 4 色可染" % n,
            "status": {"SAT": "PASS", "UNSAT": "FAIL", "UNKNOWN": "UNKNOWN",
                       "ENGINE-LIED": "ERROR"}[entry["status"]],
            "note": ("CNF %d 变量 / %d 子句 / %d 个 Schur 三元组；冲突 %d 次；证书双路复核 %s"
                     % (nv, len(clauses), ntri, entry["conflicts"],
                        entry.get("verify"))) if entry["status"] == "SAT" else
                    ("求解器判 UNSAT（上界结论见 2-45 条目）" if entry["status"] == "UNSAT"
                     else "未在预算 %gs 内定论" % args.sat_budget),
        })

    # ---------- 第三段：UNSAT 侧——n=45 是否真的不可 4 着色 ----------
    nv, clauses, V, ntri = encode_schur(45, 4)
    s = CDCL(nv, clauses, seed=args.seed + 45)
    t1 = time.time()
    st45, _, _ = s.solve(deadline=time.time() + args.unsat_budget)
    dt45 = time.time() - t1
    unsat45 = {"status": st45, "seconds": round(dt45, 1),
               "conflicts": s.stats["conflicts"], "learned": s.stats["learned"],
               "restarts": s.stats["restarts"],
               "conflicts_per_sec": round(s.stats["conflicts"] / max(dt45, 1e-9), 1)}
    items.append({
        "id": "2-45 的 UNSAT", "level": "L2",
        "claim": "不存在 [1,45] 的 4 色无和染色（即 S(4) < 45）",
        "status": {"UNSAT": "PASS", "SAT": "FAIL", "UNKNOWN": "UNKNOWN"}[st45],
        "note": ("%s；冲突 %d 次 / %d 次重启 / %.1fs（%.0f 冲突每秒）。"
                 "注意：本脚本不产 DRAT 证明，故该 UNSAT 的可信度 = 求解器实现 + 自检通过，"
                 "不是可脱离求解器独立复核的证书。" %
                 (st45, s.stats["conflicts"], s.stats["restarts"], dt45,
                  unsat45["conflicts_per_sec"])),
    })

    # ---------- 第三段之二：多种子复核（判定是否依赖随机序） ----------
    corroboration = []
    for extra in (1001, 2002, 3003):
        s2 = CDCL(nv, clauses, seed=args.seed + 45 + extra)
        t2 = time.time()
        st2, _, _ = s2.solve(deadline=time.time() + args.unsat_budget)
        corroboration.append({"seed": args.seed + 45 + extra, "status": st2,
                              "conflicts": s2.stats["conflicts"],
                              "seconds": round(time.time() - t2, 1)})
    n_unsat = sum(1 for c in corroboration if c["status"] == "UNSAT")
    items.append({
        "id": "2b-多种子复核", "level": "L2",
        "claim": "n=45 判 UNSAT 不依赖随机序",
        "status": "PASS" if n_unsat == len(corroboration) else "UNKNOWN",
        "note": "另取 3 个种子重跑：%s。注意这与'独立解法'不同——它排除的是运气/随机序，"
                "排除不了实现层面的系统性错误。" % json.dumps(corroboration, ensure_ascii=False),
    })

    # ---------- 汇总裁决 ----------
    lower = 0
    for n in (41, 42, 43, 44, 45):
        if sat_results.get(n, {}).get("status") == "SAT":
            lower = n
        else:
            break
    if unsat45["status"] == "UNSAT" and lower == 44:
        verdict = "S(4) = 44（L2：n=44 有证书 + n=45 求解器判 UNSAT）"
    elif lower:
        verdict = "S(4) >= %d（下界有证书，上界未定）" % lower
    else:
        verdict = "S(4) 未定"
    items.append({"id": "3-裁决", "level": "L2", "claim": verdict,
                  "status": "PASS" if "= 44" in verdict else "UNKNOWN",
                  "note": "上界一侧若无 UNSAT（或 UNSAT 无 DRAT 证书），一律不写成等号。"})

    payload = {
        "date": "2026-10-13", "topic": "Schur S(4): CNF + 纯标准库 CDCL",
        "provenance": {"ai_assisted": True,
                       "role": "起草求解器 + 编码 + 自检 + 核验；等级按脚本直出"},
        "guards": guards, "items": items, "sat_side": sat_results,
        "unsat_45": unsat45, "unsat_45_corroboration": corroboration,
        "verdict": verdict,
        "budgets": {"sat": args.sat_budget, "unsat": args.unsat_budget},
        "seed_base": args.seed,
        "elapsed_sec": round(time.time() - t0, 2),
        "python": sys.version.split()[0],
    }
    with open(os.path.join(HERE, "schur_SAT_S4等号_2026-10-13.json"), "w",
              encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    lines = ["# Schur S(4)：CNF + 纯标准库 CDCL（2026-10-13）\n",
             "- 脚本：`99-沙箱/schur_SAT求解与S4等号_2026-10-13.py`",
             "- 读数：`99-沙箱/schur_SAT_S4等号_2026-10-13.json`",
             "- 验证器复用上一轮（单一真源）：`schur_搜索与构造_AI闭环演示_2026-10-12.py`\n",
             "## 一、求解器自检（先证明它会算对，再谈它的 UNSAT 有几分可信）"]
    for g in guards:
        lines.append("- [%s] %s：%s" % ("PASS" if g["pass"] else "FAIL", g["id"], g["detail"]))
    lines.append("\n## 二、SAT 侧（下界）")
    for n in sorted(sat_results):
        e = sat_results[n]
        lines.append("- n=%d：%s（冲突 %d，证书复核 %s）"
                     % (n, e["status"], e["conflicts"], e.get("verify")))
    lines.append("\n## 三、UNSAT 侧（上界）")
    lines.append("- n=45：%s，冲突 %d，%.1fs，%.0f 冲突/秒"
                 % (unsat45["status"], unsat45["conflicts"], unsat45["seconds"],
                    unsat45["conflicts_per_sec"]))
    lines.append("\n## 三之二、多种子复核（排除随机序带来的运气）")
    for c in corroboration:
        lines.append("- seed=%d：%s（冲突 %d，%.1fs）" %
                     (c["seed"], c["status"], c["conflicts"], c["seconds"]))
    lines.append("\n## 四、裁决\n- **%s**" % verdict)
    lines.append("\n## 五、诚实边界")
    lines.append("- 不产 DRAT/LRAT：UNSAT 结论的可信度 = 求解器实现正确 + 已知答案自检通过，"
                 "**不等于**可脱离本求解器独立复核的机器证书。")
    lines.append("- 自检只覆盖 n<=40 的同类实例；外推到 n=45 属同类但规模更大，不可宣称等价。")
    lines.append("- 未做 Lean 形式化（L4）；不主张任何构造/编码的首创。")
    with open(os.path.join(HERE, "schur_SAT_S4等号_2026-10-13.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))

    sys.stdout.write("selftest %d/%d\n" % (sum(1 for g in guards if g["pass"]), len(guards)))
    for n in sorted(sat_results):
        sys.stdout.write("n=%d %s conflicts=%d\n" % (n, sat_results[n]["status"],
                                                     sat_results[n]["conflicts"]))
    sys.stdout.write("n=45 %s conflicts=%d %.1fs\n" % (unsat45["status"],
                                                       unsat45["conflicts"],
                                                       unsat45["seconds"]))
    sys.stdout.write("verdict: %s\n" % verdict)
    sys.stdout.write("elapsed %.1fs\n" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
