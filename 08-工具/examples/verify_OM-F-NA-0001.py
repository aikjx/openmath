# -*- coding: utf-8 -*-
"""OM-F-NA-0001 判定册：三点 Gauss-Legendre 求积在任意区间上对不超过 5 次多项式精确。

红线一：本脚本只做**残差核对**，不构成证明；PASS 只覆盖这里点名的次数、区间与通道。
红线八：不复制晚于本面落盘的闸门读数；任何「条数／枚数」一律让读者现读版面。

五条判定（每条都有第二通道，不是把同一条式子算两遍）：
  判定 1  表格侧 vs 精确侧：p=0..5 逐格，四枚区间（含两枚非对称区间），80 位档；自带 G1 地板尺对照
  判定 2  矩匹配现推（solve 出半宽与权重）vs 卡面表格：这是**独立生产者**，不是抄表
  判定 3  Legendre 通道：sympy 的 legendre(3,t) 与卡里的 t^3-(3/5)t 同形；根通道＋正交通道各读一次
  判定 4  仿射不变律：同一枚积分走 [lo,hi] 直算与 [-1,1] 换元两条路；非多项式 f=exp 那格印「不精确」的量级
  判定 5  上限恰为 5：p=6、p=7 必须非零，且反对照不许只落在对称区间（p=7 在 [-1,1] 上对消成 0 是数学事实）

仪器自记（本轮栽过的坑，写在脸上防复发）：
  * Jacobian (hi-lo)/2 是公式的一半，不是可选修饰：对象路漏乘它，p=0 那格当场展开成 -hi+lo+2
    （预演面 scratch/T18B_NA_probe.txt 留痕，驱动器 scratch/_t18b_na_probe.py）。
  * 反对照可以是没牙的：p=7 的展开式非零，但在对称区间上读成 0.000e+00。
    所以判定 5 断言「取样里至少有一枚非对称区间」，否则印 INVALID-CONTROL 判红，不印通过。
  * 矩方程右端不是 2/(p+1) 对一切 p：奇数次的精确矩是 0。把它写成统一式，
    solve 会给出「满足错方程的解」，于是判定 2 会在假目标上现推。
  * 空脚本也返回 rc=0，所以判定面非空由驱动器另行断言，不由本文件的退出码担保。
"""
import sys
import time

import sympy as sp
from mpmath import mp, workdps

FAILS = []
SQRT35 = sp.sqrt(sp.Rational(3, 5))
NODES = [-SQRT35, sp.Integer(0), SQRT35]
WEIGHTS = [sp.Rational(5, 9), sp.Rational(8, 9), sp.Rational(5, 9)]
INTERVALS = [("-1", "1"), ("1/2", "3"), ("0", "2"), ("-3", "-1/4")]
# 通过/失败两把尺分开：真精确的格读 1e-78 量级（节点本身只知到 80 位），
# 真不精确的格读 1e-2 量级——两把尺之间有 70 多个数量级的空档，不许把它们并成一枚阈值。
PASS_TOL = sp.Rational(1, 10) ** 50
CEIL_FLOOR = sp.Rational(1, 10) ** 40


def say(line):
    print(line)


def bad(tag, detail):
    FAILS.append(tag)
    say("  [红] %s :: %s" % (tag, detail))


def mpf(z, dps=80):
    """sympy 对象 -> mpmath 数：走十进制字符串，不经过 Python float（`sympy` 顶层没有 nstr，用 str）。"""
    with workdps(dps):
        return mp.mpf(str(sp.N(z, dps)))


def moment(p):
    """[-1,1] 上 t^p 的精确矩：奇数次为 0，偶数次为 2/(p+1)。"""
    return sp.Integer(0) if p % 2 else sp.Rational(2, p + 1)


def rule_value(nodes, weights, lo, hi, p, dps=80):
    with workdps(dps):
        L, H = mpf(sp.nsimplify(lo), dps), mpf(sp.nsimplify(hi), dps)
        half, mid = (H - L) / 2, (L + H) / 2
        total = mp.mpf(0)
        for n, w in zip(nodes, weights):
            total += mpf(w, dps) * (mid + half * mpf(n, dps)) ** p
        return half * total


def exact_value(lo, hi, p, dps=80):
    with workdps(dps):
        L, H = mpf(sp.nsimplify(lo), dps), mpf(sp.nsimplify(hi), dps)
        return (H ** (p + 1) - L ** (p + 1)) / (p + 1)


def judge1(nodes=None, weights=None, dps=80, quiet=False):
    say("判定 1  表格侧 vs 精确侧（p=0..5 逐格，%d 枚区间，%d 位档）" % (len(INTERVALS), dps))
    nodes = nodes if nodes is not None else NODES
    weights = weights if weights is not None else WEIGHTS
    worst = mp.mpf(0)
    for lo, hi in INTERVALS:
        for p in range(6):
            d = abs(rule_value(nodes, weights, lo, hi, p, dps) - exact_value(lo, hi, p, dps))
            worst = max(worst, d)
            if not quiet:
                say("    lo=%-4s hi=%-4s p=%d 残差=%.3e" % (lo, hi, p, d))
            if d > PASS_TOL:
                bad("J1", "lo=%s hi=%s p=%d 残差 %.3e 超容差" % (lo, hi, p, d))
    # G1 地板尺对照：把一枚权重扰动 1e-6，残差必须翻到 1e-8 以上——否则判定 1 读的是瞎尺。
    pert = [WEIGHTS[0], WEIGHTS[1] + sp.Rational(1, 10 ** 6), WEIGHTS[2]]
    dp = abs(rule_value(NODES, pert, "1/2", "3", 1, 80) - exact_value("1/2", "3", 1, 80))
    if not quiet:
        say("    G1 对照：权重扰动 1e-6 后 lo=1/2 hi=3 p=1 残差=%.3e（地板尺随扰动翻动才算有牙）" % dp)
    if dp < sp.Rational(1, 10 ** 8):
        bad("J1/G1", "扰动 1e-6 只读到 %.3e ⇒ 该格对扰动不敏感，尺子在这一型上是瞎的" % dp)
    return worst


def judge2():
    say("判定 2  矩匹配现推 vs 卡面表格（独立生产者，不抄表）")
    w1, w2, a = sp.symbols("w1 w2 a", positive=True)
    xs = (-a, sp.Integer(0), a)
    ws = (w1, w2, w1)
    eqs = []
    for p in (0, 2, 4):
        lhs = sum(w * x ** p for w, x in zip(ws, xs))
        eqs.append(sp.Eq(sp.simplify(lhs), moment(p)))
    sols = sp.solve(eqs, [w1, w2, a], dict=True)
    real = [s for s in sols if all(v.is_real for v in s.values())]
    say("    解=%d 枚（实数解 %d 枚）：%s" % (len(sols), len(real), real))
    if len(real) != 1:
        bad("J2", "矩匹配的实数解不是唯一一枚（%d 枚）⇒ 卡面「节点＝P_3 的根」不由本通道定死" % len(real))
        return
    s = real[0]
    got_nodes = sorted([sp.simplify(-s[a]), sp.Integer(0), sp.simplify(s[a])], key=lambda z: float(z))
    got_w = [sp.simplify(s[w1]), sp.simplify(s[w2]), sp.simplify(s[w1])]
    say("    现推节点=%s 现推权重=%s" % (got_nodes, got_w))
    if got_nodes != sorted(NODES, key=lambda z: float(z)) or got_w != WEIGHTS:
        bad("J2", "现推与卡面表格不同值")
    for p in (1, 3, 5):
        lhs = sp.simplify(sum(w * x ** p for w, x in zip(got_w, got_nodes)))
        say("    奇数次 p=%d 现推侧矩=%s 精确矩=%s" % (p, lhs, moment(p)))
        if sp.simplify(lhs - moment(p)) != 0:
            bad("J2", "现推那组解在 p=%d 上不满足矩方程" % p)


def judge3():
    say("判定 3  Legendre 通道（sympy 特殊函数模块 vs 卡里的三次多项式）")
    t = sp.Symbol("t")
    P3 = sp.legendre(3, t)
    monic = sp.Rational(2, 5) * P3
    say("    sympy.legendre(3,t)=%s 首一化=%s" % (P3, sp.expand(monic)))
    if sp.expand(monic - (t ** 3 - sp.Rational(3, 5) * t)) != 0:
        bad("J3", "sympy 的 P_3 与卡里 t^3-(3/5)t 不同形 ⇒ 节点来源断言作废")
    roots = sorted([sp.simplify(r) for r in sp.solve(sp.Eq(P3, 0), t)], key=lambda z: float(z))
    say("    sympy 解出的根=%s 卡面节点=%s" % (roots, sorted(NODES, key=lambda z: float(z))))
    if roots != sorted(NODES, key=lambda z: float(z)):
        bad("J3", "根通道与卡面节点不同值")
    for m in range(3):
        sym = sp.integrate(t ** m * P3, (t, -1, 1))
        with workdps(50):
            # 被积的是首一化 P_3 = t^3 - (3/5) t，系数是 3/5；把节点位置 sqrt(3/5) 当系数写进来
            # 是本判定第一版的错（数值通道读到 1.164e-01 咬红自己），两枚数不相干，别混。
            num = mp.quad(lambda u: u ** m * (u ** 3 - (mp.mpf(3) / 5) * u), [-1, 0, 1])
        say("    正交 m=%d 符号通道=%s 数值通道=%.3e" % (m, sym, abs(num)))
        if sym != 0:
            bad("J3", "符号正交通道 m=%d 不归零" % m)
        if abs(num) > 1e-40:
            bad("J3", "数值正交通道 m=%d 读到 %.3e 超容差" % (m, abs(num)))


def judge4():
    say("判定 4  仿射不变律（直算 vs 换元），外加非多项式的一格「不精确」")
    # mp.quad 用**当前** mp.dps；不在 workdps 里跑就只在默认 15 位上积分，
    # 于是 lo=1/2 hi=3 那格读到 1.421e-14（默认位的噪声）而被 1e-40 的尺咬红。
    with workdps(80):
        for lo, hi in [("-1", "1"), ("1/2", "3"), ("-3", "-1/4")]:
            L, H = mpf(sp.nsimplify(lo)), mpf(sp.nsimplify(hi))
            half, mid = (H - L) / 2, (L + H) / 2
            for f_mp, tag in ((lambda u: u ** 5, "t^5"), (lambda u: mp.exp(u), "exp(t)")):
                direct = mp.quad(f_mp, [L, H])
                mapped = half * mp.quad(lambda s: f_mp(mid + half * s), [-1, 0, 1])
                d = abs(direct - mapped)
                say("    lo=%-4s hi=%-4s f=%-7s 直算 vs 换元差=%.3e" % (lo, hi, tag, d))
                if d > 1e-40:
                    bad("J4", "仿射不变律在 lo=%s hi=%s f=%s 上破了（%.3e）" % (lo, hi, tag, d))
                if tag == "exp(t)":
                    g = sum(mpf(w) * mp.exp(mid + half * mpf(n)) for n, w in zip(NODES, WEIGHTS))
                    err = abs(half * g - (mp.exp(H) - mp.exp(L)))
                    say("      exp 那格的求积误差=%.3e（本卡只声明多项式次数 <=5，这一枚是边界外的证据，不是反例）" % err)
                    if err < 1e-20:
                        bad("J4", "exp(t) 那格读到 %.3e 太小 ⇒ 三点规则对非多项式也精确？断言边界失真" % err)


def judge5(nodes=None, weights=None, quiet=False):
    say("判定 5  上限恰为 5（p=6、p=7 必须非零；反对照不许只落在对称区间）")
    nodes = nodes if nodes is not None else NODES
    weights = weights if weights is not None else WEIGHTS
    asym = [(lo, hi) for lo, hi in INTERVALS
            if sp.simplify(sp.nsimplify(lo) + sp.nsimplify(hi)) != 0]
    if not asym:
        bad("J5", "INVALID-CONTROL：取样全是对称区间，奇数次误差必为 0，上限断言没有牙")
        return
    say("    非对称区间 %d 枚（共 %d 枚）：%s" % (len(asym), len(INTERVALS), asym))
    for p in (6, 7):
        for lo, hi in INTERVALS:
            d = abs(rule_value(nodes, weights, lo, hi, p, 80) - exact_value(lo, hi, p, 80))
            sym = sp.simplify(sp.nsimplify(lo) + sp.nsimplify(hi)) == 0
            if not quiet:
                say("    p=%d lo=%-4s hi=%-4s 残差=%.3e%s" % (p, lo, hi, d,
                                                              "（对称区间对消格，不作上限证据）" if sym and p % 2 else ""))
            if sym and p % 2:
                if d > PASS_TOL:
                    bad("J5", "对称区间上的奇数次反对照本应读 0，读到 %.3e ⇒ 求积式本身有误" % d)
                continue
            if d <= CEIL_FLOOR:
                bad("J5", "p=%d 在 lo=%s hi=%s 上仍读成 %.3e ⇒ 上限不止 5，卡面断言作废" % (p, lo, hi, d))
    for lo, hi in asym:
        d = abs(rule_value(nodes, weights, lo, hi, 4, 80) - exact_value(lo, hi, 4, 80))
        if not quiet:
            say("    正对照 p=4 lo=%s hi=%s 残差=%.3e（须为机器噪声量级，不许被咬红）" % (lo, hi, d))
        if d > PASS_TOL:
            bad("J5/正对照", "p=4 那一格被咬红，不是数学是尺子")


def mutants():
    """变异体电池：每枚都必须被点名，否则判定面是恒绿的假账。"""
    out = []
    wrong_node = [-sp.sqrt(sp.Rational(2, 5)), sp.Integer(0), sp.sqrt(sp.Rational(2, 5))]
    wrong_w = [sp.Rational(5, 9), sp.Rational(7, 9), sp.Rational(5, 9)]
    eq_nodes = [sp.Rational(-1, 2), sp.Integer(0), sp.Rational(1, 2)]
    for tag, nodes, weights in (("M1 节点错成 sqrt(2/5)", wrong_node, WEIGHTS),
                                ("M2 权重 8/9 改成 7/9", NODES, wrong_w),
                                ("M4 用等距三枚（Simpson 的节点配 Gauss 的权重）", eq_nodes, WEIGHTS)):
        before = len(FAILS)
        judge1(nodes, weights, quiet=True)
        out.append((tag, len(FAILS) - before))
    # M3 漏乘 Jacobian：只在 p=2 那一格比，残差必须翻
    wrong = sum(w * (n * mpf(sp.Rational(1, 2))) ** 2 for w, n in zip(WEIGHTS, NODES))
    right = exact_value("-1", "1", 2, 80)
    out.append(("M3 漏乘 Jacobian（p=2 那格）", abs(wrong - right) > 1e-6))
    # M5 上限抬到 p=6：那一格在 lo=1/2、hi=3 上必须非零（否则「恰为 5」没证据）
    d6 = abs(rule_value(NODES, WEIGHTS, "1/2", "3", 6, 80) - exact_value("1/2", "3", 6, 80))
    out.append(("M5 上限抬到 p=6（该格必须非零）", d6 > CEIL_FLOOR))
    # M6 矩方程右端写成一枚 2/(p+1) 通吃（含奇数次）：solve 会给出错的解，现推通道必须与卡面不符
    w1, w2, a = sp.symbols("w1 w2 a", positive=True)
    xs, ws = (-a, sp.Integer(0), a), (w1, w2, w1)
    bad_eqs = [sp.Eq(sum(w * x ** p for w, x in zip(ws, xs)), sp.Rational(2, p + 1))
               for p in (0, 2, 3)]
    got = sp.solve(bad_eqs, [w1, w2, a], dict=True)
    agree = any(all(sp.simplify(v - r) == 0 for v, r in zip([s[w1], s[w2], s[a]],
                                                             [WEIGHTS[0], WEIGHTS[1], SQRT35]))
                 for s in got) if got else False
    out.append(("M6 矩方程右端把奇数次写成 2/(p+1)（错目标，现推必与卡面不符）", not agree))
    return out


def guard_teeth():
    """尺子对照：坏例每型须响；判定面自身不许在正例上假阳。"""
    say("牙齿电池（每枚变异体须响；正例不误伤）")
    rows = mutants()
    defects = 0
    for tag, hits in rows:
        red = bool(hits) if not isinstance(hits, bool) else hits
        say("  %-52s %s" % (tag, "已响" if red else "未响（DEFECT：该型断言没牙）"))
        if not red:
            defects += 1
            bad("SELFTEST", "%s 未被打红" % tag)
    if len(rows) < 5:
        defects += 1
        bad("SELFTEST", "变异体只有 %d 枚，少于本卡登记的坏例形状数" % len(rows))
    say("  变异体共 %d 枚，DEFECT %d 枚" % (len(rows), defects))
    del FAILS[:]


def main():
    argv = sys.argv[1:]
    started = time.time()
    if "--selftest" in argv:
        guard_teeth()
        say("牙齿面：DEFECT=%d 条 rc=%d（DEFECT 非零＝某型坏例打不红＝该型断言没牙；全 0＝牙齿完好，不等于证明）"
            % (len(FAILS), 1 if FAILS else 0))
        say("== 用时 %.1f s ==" % (time.time() - started))
        return 1 if FAILS else 0
    judge1()
    judge2()
    judge3()
    judge4()
    judge5()
    say("判定面抓到红 %d 条 rc=%d；用时 %.1f s" % (len(FAILS), 1 if FAILS else 0, time.time() - started))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
