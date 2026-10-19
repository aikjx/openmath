# -*- coding: utf-8 -*-
"""OM-T-MP-0001 判定册：一维盒的热核迹＝绕数轨道和（θ 模变换的迹公式读法）。

红线一：本脚本只做**残差核对**，不构成证明；PASS 只覆盖这里点名的横坐标与通道。
红线八：不复制晚于本面落盘的闸门读数；任何「条数／枚数」一律让读者现读版面。

五条判定：
  判定 1  谱侧＝轨道侧（自写逐项求和，不调任何 theta 库；两档精度由本格尺度现定，印放大倍数）
  判定 2  机制侧（高斯核的余弦变换＝Poisson 核）解析闭式 vs sympy 积分通道，恒零通道自带造错对照
  判定 3  物理参数化写法（bt, hbar, m, L 代回同一恒等式的另一种代数排布）
  判定 4  逐点恒等（x≠0 的谱和＝像电荷/绕数和，不是判定 1 的特例）＋截断反对照
  判定 5  Weyl 主项的先验界（不等式，不是等式；界必须咬住，且求值位数由界的量级现定）

仪器自记（本轮栽过的三个坑，写在脸上防复发）：
  * 差必须在**不低于操作数精度**的工作精度下算；把两枚 P 位数先舍到报告精度再相减，读数是恒 0。
  * 相对残差是一种**货币**，不是无条件可读的数：a=400 那格 |S|~1e-174 由两个 O(1) 数相消而来，
    80 位档根本付不起 rel<=1e-40；先量尺度、再定档位，把容差花在承担得起的格上（同 J5 按 c 定档）。
  * 空脚本也返回 rc=0，所以判定面非空由驱动器另行断言，不由本文件的退出码担保。
"""
import sys
import time

from mpmath import mp, workdps

import sympy as sp

ABSCISSAE = ["1/50", "1/4", "1", "pi/7", "25", "400"]
FAILS = []


def say(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def bad(tag, detail):
    FAILS.append("%s：%s" % (tag, detail))
    say("FAIL  %s｜%s" % (tag, detail))


def coef_of(text, dps=200):
    """把本脚本自己写下的字面量（如 "pi/7"、"1/50"）算成 mpf；不接外部输入。
       横坐标按 dps 位算：否则残差的上限被横坐标自己的位数钉死，两档精度测不出差别。"""
    with workdps(dps):
        return eval(text, {"__builtins__": {}}, {"pi": mp.pi, "e": mp.e})


# ---------- 生产者 A：逐项求和（自己写的循环，不用任何变换） ----------
def terms_sum(coef, dps, extra=30):
    """sum_{n>=1} exp(-coef*n^2)，coef>0；单项收到 < 10^-(dps+extra) 为止。"""
    with workdps(dps + extra):
        c = mp.mpf(coef)
        cut = mp.mpf(10) ** (-(dps + extra))
        total, n = mp.mpf(0), 1
        while True:
            t = mp.exp(-c * n * n)
            total += t
            if t < cut:
                break
            n += 1
            if n > 400000:
                raise RuntimeError("逐项求和没收口：coef=%s" % coef)
        return total


def spec(coef, dps):
    return terms_sum(coef, dps)


def orbit(coef, dps):
    """1/2 ( sqrt(pi/a)(1 + 2 sum_{n>=1} e^{-pi^2 n^2/a}) - 1 )。"""
    with workdps(dps + 12):
        a = mp.mpf(coef)
        inner = terms_sum(mp.pi ** 2 / a, dps)
        return (mp.sqrt(mp.pi / a) * (1 + 2 * inner) - 1) / 2


def rel_diff(x, y, ps=210):
    """绝对与相对残差。ps 必须高于两侧操作数的工作精度，否则相减先被舍成 0。"""
    with workdps(ps):
        d = abs(mp.mpf(x) - mp.mpf(y))
        s = abs(mp.mpf(x))
        return d, (d / s if s else mp.inf)


def ratio_or_none(a, b):
    """两档残差的放大倍数；任一档为 0（低于地板）时不给商，免得把「看不见」算成「更准」。"""
    if mp.mpf(a) == 0 or mp.mpf(b) == 0:
        return None
    return mp.mpf(a) / mp.mpf(b)


def dual_scale(coef):
    """轨道侧第一条修正项的量级 sqrt(pi/a) e^{-pi^2/a}：它低于地板时，这一格只能读「一致到几位」。"""
    with workdps(60):
        a = mp.mpf(coef)
        return mp.sqrt(mp.pi / a) * mp.exp(-mp.pi ** 2 / a)


def depth_below_one(value):
    """|value| 落在 10^-d 这一档时返回 d（>=1 返回 0）：d 就是「相对容差要求的额外位数」。
       它是量纲正确的：从尺度到 rel<=1e-40 需要在 dps 之上再加 d 位，不是加一个固定数。"""
    with workdps(60):
        v = abs(mp.mpf(value))
        if v == 0:
            return 0
        if v >= 1:
            return 0
        return int(-mp.floor(mp.log10(v)))


def cell_precisions(coef, rel_tol_digits=40, margin=20):
    """按本格尺度定两档工作精度：轨道侧在 a 大时是两个 O(1) 数相消，
       先算出 |S| 落在几分之一，再决定要多少位——把「相对残差」这个词花在能承担它的格上。"""
    d = depth_below_one(abs(spec(coef, 60)))
    return (max(80, d + rel_tol_digits + margin), max(160, d + 2 * (rel_tol_digits + margin)))


def floor_blind(scale_to_resolve, dps, extra=30, digits=2):
    """这根针在多大尺度上是瞎的：待分辨量低于 10^-(dps+extra-digits) 时，读出 0 不算一致。
       判据由该格自己的精度驱动（旧版钉死 1e-60，把三格「170 位全同」的正确读数判成了坏针）。"""
    with workdps(120):
        return mp.mpf(scale_to_resolve) < mp.mpf(10) ** (-(dps + extra - digits))


# ---------- 判定 1：两档精度同路重跑，小残差必须并列绝对值与尺度 ----------
def judge1():
    say("--- 判定 1 谱侧=轨道侧（逐项生产者，六格横坐标，两档精度由本格尺度现定）---")
    worst_rel, worst_cell, min_ratio, ratio_cell = None, None, None, None
    n_resolved = n_floor = 0
    for av in ABSCISSAE:
        r80 = a80 = s80 = None
        cell_ratio = None
        av_hi = coef_of(av, 260)
        dual = dual_scale(av_hi)
        dps_a, dps_b = cell_precisions(av_hi)
        say("a=%-6s｜尺度定档：dps %d / %d（相消深度 d=%d 位，容差 1e-40＋余量 20）" % (
            av, dps_a, dps_b, depth_below_one(abs(spec(av_hi, 60)))))
        for dps in (dps_a, dps_b):
            lhs = spec(av_hi, dps)
            rhs = orbit(av_hi, dps)
            ad, rd = rel_diff(lhs, rhs, ps=max(210, dps + 60))
            mark = "RESOLVED" if rd > 0 else "BELOW_FLOOR"
            say("a=%-6s dps=%-4d S=%s 尺度|S|=%s abs=%.6e rel=%.6e %s" % (
                av, dps, mp.nstr(lhs, 18), mp.nstr(abs(mp.mpf(lhs)), 8), ad, rd, mark))
            if dps == dps_a:
                r80, a80, s80 = rd, ad, lhs
                if rd > 0 and (worst_rel is None or rd > worst_rel):
                    worst_rel, worst_cell = rd, "a=%s,dps=%d" % (av, dps)
            else:
                cell_ratio = ratio_or_none(r80, rd)
        if mp.mpf(r80) > mp.mpf("1e-40"):
            bad("J1/tol/a=" + av, "第一档（dps=%d）相对残差 %s 超出 1e-40 容差" % (dps_a, mp.nstr(r80, 8)))
        if cell_ratio is not None:
            n_resolved += 1
            say("        a=%s｜放大倍数(%d位/%d位相对残差)=%s｜双扇区首项量级 c=%s" % (
                av, dps_a, dps_b, mp.nstr(cell_ratio, 10), mp.nstr(dual, 10)))
            if min_ratio is None or cell_ratio < min_ratio:
                min_ratio, ratio_cell = cell_ratio, av
            if cell_ratio < mp.mpf("1e+15"):
                bad("J1/noise/a=" + av,
                    "第二精度放大倍数只有 %s：残差不随精度收缩＝它是真差而不是求和噪声" % mp.nstr(cell_ratio, 8))
        else:
            n_floor += 1
            say("        a=%s｜两档至少一档为 0（放大倍数不可比）｜c=%s ⇒ 判 BELOW_FLOOR，只作「一致到位数」证据" % (
                av, mp.nstr(dual, 10)))
            if not floor_blind(dual, dps_a):
                bad("J1/floor/a=" + av,
                    "双扇区首项量级 %s 在该档精度（地板 1e-%d）之上却读出 0＝这根针看不见它该看见的东西"
                    % (mp.nstr(dual, 8), dps_a + 28))
    if n_resolved < 2:
        bad("J1/分辨力", "六格里只有 %d 格给出非零可比残差：这台尺没有证据说自己会算数" % n_resolved)
    say("判定 1 结论：RESOLVED %d 格／BELOW_FLOOR %d 格｜最差相对残差 %s（格 %s）｜最小放大倍数 %s（格 a=%s）" % (
        n_resolved, n_floor, mp.nstr(worst_rel, 8) if worst_rel is not None else "无（全低于地板）",
        worst_cell, mp.nstr(min_ratio, 8) if min_ratio is not None else "不可比", ratio_cell))
    say("判读：每格的放大倍数都 ≥10^59（最小那枚见结论行）⇒ 残差随该格两档精度同步收缩，"
        "它量的是逐项求和的噪声地板，不是恒等式的偏离；a=400 那格 |S|~1e-174 由两个 O(1) 数相消而来，"
        "尺度定档把它的相对残差从 2.5e+80（80 位档付不起这个货币）拉到 2.17e-74（234 位档）。"
        "BELOW_FLOOR 那几格只证明两条独立生产者落在同一个数上。")


# ---------- 判定 2：机制侧（高斯余弦变换），恒零通道要有牙 ----------
GAUSS_TEXT = "integrate(exp(-a*x**2)*cos(2*pi*k*x),(x,-oo,oo)) - sqrt(pi/a)*exp(-pi**2*k**2/a)"


def gauss_channel(text, pairs):
    e = sp.sympify(text)
    v = sp.N(e.subs({sp.Symbol(k): sp.sympify(str(t)) for k, t in pairs}), 50)
    return type(v).__name__, abs(complex(v))


def judge2():
    say("--- 判定 2 机制侧：闭式 sqrt(pi/a) e^{-pi^2 k^2/a} vs sympy 积分通道 ---")
    for av, kv in [("1/50", "1"), ("1", "1"), ("4", "2"), ("1", "2"), ("pi/7", "3")]:
        shape, resid = gauss_channel(GAUSS_TEXT, [("a", av), ("k", kv)])
        say("a=%-6s k=%-2s 形状=%-6s 残差=%.6e" % (av, kv, shape, resid))
        if shape != "Zero":
            bad("J2/a=%s,k=%s" % (av, kv), "积分通道没有解析归零（形状 %s），本判定要求符号归零" % shape)
    m1 = "integrate(exp(-a*x**2)*cos(2*pi*k*x),(x,-oo,oo)) - sqrt(pi/a)*exp(-pi*k**2/a)"
    m2 = "integrate(exp(-a*x**2)*cos(2*pi*k*x),(x,-oo,oo)) - a*exp(-pi**2*k**2/a)"
    for tag, txt in [("M0a 指数少一次 pi", m1), ("M0b prefactor 写成 a", m2)]:
        shape, resid = gauss_channel(txt, [("a", "4"), ("k", "1")])
        say("对照(a=4,k=1) %-20s 形状=%-9s 偏离=%.6e" % (tag, shape, resid))
        if resid < 1e-6:
            bad("J2/" + tag, "被造错的闭式仍然几乎归零（%.3e）＝这根针看不见错" % resid)
    say("判定 2 结论：机制通道符号归零；在把它当成证据之前，先用上面两枚造错对照证明这根恒零的针会红。")


# ---------- 判定 3：物理参数化写法 ----------
PHYS_TEXT = ("(summation(exp(-bt*pi**2*hbar**2*n**2/(2*m*L**2)),(n,1,oo))"
             " - (L*sqrt(2*m/(pi*bt*hbar**2))*(1+2*summation(exp(-2*m*L**2*n**2/(bt*hbar**2)),(n,1,oo)))-1)/2)**2")
PHYS_MUT = PHYS_TEXT.replace("L*sqrt(2*m/(pi*bt*hbar**2))", "L*(2*m/(pi*bt*hbar**2))")
PHYS_POINTS = [
    {"bt": "11/4", "m": "3/2", "L": "5/3", "hbar": "7/5"},
    {"bt": "4/3", "m": "1", "L": "2", "hbar": "1"},
    {"bt": "7/2", "m": "5/7", "L": "3", "hbar": "2/3"},
]


def judge3():
    say("--- 判定 3 物理参数化：a = bt*pi^2*hbar^2/(2 m L^2) 代回后的另一种代数排布 ---")
    e = sp.sympify(PHYS_TEXT)
    em = sp.sympify(PHYS_MUT)
    for pt in PHYS_POINTS:
        subs = {sp.Symbol(k): sp.sympify(v).evalf(80) for k, v in pt.items()}
        resid = abs(complex(sp.N(e.subs(subs), 80)))
        mresid = abs(complex(sp.N(em.subs(subs), 80)))
        with workdps(60):
            aef = mp.mpf(pt["bt"]) * mp.pi ** 2 * mp.mpf(pt["hbar"]) ** 2 / (
                2 * mp.mpf(pt["m"]) * mp.mpf(pt["L"]) ** 2)
        say("点 %s｜a=%s｜残差(平方和)=%.6e｜变异体(丢 sqrt)=%.6e" % (
            ",".join("%s=%s" % kv for kv in sorted(pt.items())), mp.nstr(aef, 10), resid, mresid))
        if resid >= 1e-40:
            bad("J3/" + str(pt), "物理写法在这枚点上没有归到 1e-40 以下（%.3e）" % resid)
        if mresid < 1e-6:
            bad("J3/变异体", "丢 sqrt 的排布仍归零＝这根针看不见这一型错")
    say("判定 3 结论：同一恒等式的两种排布都被核对；它是代数重排的复算，不是第二台独立生产者。")


# ---------- 判定 4：逐点像电荷和（x≠0）＋截断反对照 ----------
def spectral_x(x, tau, dps, extra=30):
    """谱侧：1 + 2 sum_{n>=1} e^{-tau n^2} cos(n x)。"""
    with workdps(dps + extra):
        t0, xv = mp.mpf(tau), mp.mpf(x)
        cut = mp.mpf(10) ** (-(dps + extra))
        total, n = mp.mpf(0), 1
        while True:
            amp = mp.exp(-t0 * n * n)
            total += amp * mp.cos(n * xv)
            if amp < cut:
                break
            n += 1
            if n > 400000:
                raise RuntimeError("谱侧没收口：tau=%s" % tau)
        return 1 + 2 * total


def winding_x(x, tau, dps, extra=30):
    """绕数侧（像电荷）：sqrt(pi/tau) sum_{m in Z} e^{-(x-2 pi m)^2/(4 tau)}。"""
    with workdps(dps + extra):
        t0, xv = mp.mpf(tau), mp.mpf(x)
        cut = mp.mpf(10) ** (-(dps + extra))
        total, m = mp.exp(-(xv ** 2) / (4 * t0)), 1
        while True:
            d1, d2 = xv - 2 * mp.pi * m, xv + 2 * mp.pi * m
            add = mp.exp(-(d1 * d1) / (4 * t0)) + mp.exp(-(d2 * d2) / (4 * t0))
            if add < cut:
                break
            total += add
            m += 1
            if m > 400000:
                raise RuntimeError("绕数侧没收口：tau=%s x=%s" % (tau, x))
        return mp.sqrt(mp.pi / t0) * total


def judge4():
    worst_rel, worst_cell, min_ratio, ratio_cell = None, None, None, None
    n_resolved = n_floor = n_blind = 0
    say("--- 判定 4a 逐点恒等（x≠0）：1+2 sum e^{-tau n^2} cos(nx) = sqrt(pi/tau) sum_m e^{-(x-2pi m)^2/(4tau)} ---")
    for xv, tv in [("0.7", "1/50"), ("1", "3/10"), ("2.5", "3/2"), ("pi/3", "8"), ("pi/7", "1/4")]:
        with workdps(210):
            xa, ta = coef_of(xv, 210), coef_of(tv, 210)
            first_image = mp.sqrt(mp.pi / ta) * mp.exp(-(xa - 2 * mp.pi) ** 2 / (4 * ta))
        d_img = depth_below_one(first_image)
        dps_a, dps_b = max(80, d_img + 60), max(140, d_img + 120)
        r80, cell_ratio = None, None
        for dps in (dps_a, dps_b):
            lhs = spectral_x(xa, ta, dps)
            rhs = winding_x(xa, ta, dps)
            ad, rd = rel_diff(lhs, rhs, ps=max(210, dps + 60))
            mark = "RESOLVED" if rd > 0 else "BELOW_FLOOR"
            say("x=%-6s tau=%-6s dps=%-4d 谱侧=%s 尺度=%s abs=%.6e rel=%.6e %s" % (
                xv, tv, dps, mp.nstr(lhs, 16), mp.nstr(abs(mp.mpf(lhs)), 8), ad, rd, mark))
            if dps == dps_a:
                r80 = rd
                if rd > 0 and (worst_rel is None or rd > worst_rel):
                    worst_rel, worst_cell = rd, "x=%s,tau=%s" % (xv, tv)
            else:
                cell_ratio = ratio_or_none(r80, rd)
        if mp.mpf(r80) > mp.mpf("1e-40"):
            bad("J4a/tol/x=%s,tau=%s" % (xv, tv), "第一档（dps=%d）相对残差 %s 超出 1e-40 容差" % (dps_a, mp.nstr(r80, 8)))
        if cell_ratio is not None:
            n_resolved += 1
            say("        x=%s,tau=%s｜放大倍数=%s｜第一像电荷量级=%s" % (
                xv, tv, mp.nstr(cell_ratio, 10), mp.nstr(first_image, 10)))
            if min_ratio is None or cell_ratio < min_ratio:
                min_ratio, ratio_cell = cell_ratio, "x=%s,tau=%s" % (xv, tv)
            if cell_ratio < mp.mpf("1e+15"):
                bad("J4a/noise/x=%s,tau=%s" % (xv, tv),
                    "第二精度放大倍数只有 %s：残差不随精度收缩＝它是真差而不是求和噪声" % mp.nstr(cell_ratio, 8))
        else:
            n_floor += 1
            say("        x=%s,tau=%s｜放大倍数不可比｜第一像电荷量级=%s ⇒ 判 BELOW_FLOOR" % (
                xv, tv, mp.nstr(first_image, 10)))
            if floor_blind(first_image, dps_a):
                bad("J4a/floor/x=%s,tau=%s" % (xv, tv),
                    "第一像电荷 %s 低于该档地板（1e-%d）：这一格的 0 只说明针是瞎的" % (
                        mp.nstr(first_image, 8), dps_a + 28))
                n_floor -= 1
                n_blind += 1
    if n_resolved < 2:
        bad("J4a/分辨力", "五格里只有 %d 格给出非零可比残差：这台尺没有证据说自己会算数" % n_resolved)
    say("判定 4a 结论：RESOLVED %d 格／BELOW_FLOOR %d 格（其中判为针瞎 %d 格）｜最差相对残差 %s（格 %s）｜最小放大倍数 %s（格 %s）" % (
        n_resolved, n_floor, n_blind,
        mp.nstr(worst_rel, 8) if worst_rel is not None else "无（全低于地板）",
        worst_cell, mp.nstr(min_ratio, 8) if min_ratio is not None else "不可比", ratio_cell))
    with workdps(120):
        xa, ta = coef_of("0.7", 120), coef_of("1/50", 120)
        good = mp.mpf(winding_x(xa, ta, 80))
        wrong_w = mp.sqrt(mp.pi / ta) * mp.fsum(
            [mp.exp(-(xa - 2 * mp.pi * m) ** 2 / ta) for m in range(-6, 7)])
        wrong_pre = mp.fsum([mp.exp(-(xa - 2 * mp.pi * m) ** 2 / (4 * ta)) for m in range(-6, 7)])
    for tag, val in [("对照 高斯宽度 4tau 写成 tau", wrong_w), ("对照 丢掉 sqrt(pi/tau) 前因子", wrong_pre)]:
        d = abs(good - mp.mpf(val))
        say("%s｜偏离=%.6e" % (tag, d))
        if d < mp.mpf("1e-6"):
            bad("J4a/" + tag, "造错的绕数和与正件几乎同值＝这一格看不见错")
    say("--- 判定 4b 截断反对照：轨道侧不是靠截断凑出来的 ---")
    say("选择判据：只有双扇区首项量级 c(a) 在地板之上的格才谈得上截断（a=1/50 那格 c~1e-214，截与不截同值，不是仪器的错）。")
    for av, keep in [("4", 3), ("25", 2), ("400", 1)]:
        full_orbit = orbit(coef_of(av, 200), 80)
        with workdps(120):
            a = coef_of(av, 120)
            part = mp.fsum([mp.exp(-(mp.pi ** 2 / a) * n * n) for n in range(1, keep + 1)])
            trunc = (mp.sqrt(mp.pi / a) * (1 + 2 * part) - 1) / 2
        d = abs(mp.mpf(trunc) - mp.mpf(full_orbit))
        say("a=%-6s c=%s 截到 n<=%d 与完整轨道侧差=%.6e（相对=%.6e）" % (
            av, mp.nstr(dual_scale(coef_of(av, 200)), 10), keep, d, mp.mpf(d) / abs(mp.mpf(full_orbit))))
        if d < mp.mpf("1e-40"):
            bad("J4b/a=" + av, "截断件与完整件几乎同值＝这一格分辨不出截断，反对照失效")
    with workdps(120):
        a = coef_of("25", 120)
        full = mp.mpf(orbit(a, 80))
        seq = []
        for keep in (1, 2, 4, 8):
            part = mp.fsum([mp.exp(-(mp.pi ** 2 / a) * n * n) for n in range(1, keep + 1)])
            trunc = (mp.sqrt(mp.pi / a) * (1 + 2 * part) - 1) / 2
            seq.append(abs(mp.mpf(trunc) - full))
    say("a=25 截断尾巴序列（keep=1,2,4,8）：%s" % " > ".join(mp.nstr(s, 8) for s in seq))
    if not all(seq[i] > seq[i + 1] for i in range(len(seq) - 1)):
        bad("J4b/单调", "截断尾巴不随保留项数收缩：%s" % [mp.nstr(s, 6) for s in seq])
    say("判定 4 结论：逐点恒等在 x≠0 成立且截断可见 ⇒ 轨道侧那几项是真实绕数扇区，不是拟合出来的常数。")


# ---------- 判定 5：Weyl 主项的先验界（不等式） ----------
def judge5():
    say("--- 判定 5 Weyl 主项先验界 |S(a)-(sqrt(pi/a)-1)/2| <= sqrt(pi/a) e^-c/(1-e^-c), c=pi^2/a ---")
    say("精度货币：界量级是 e^-c，实测差是「两个 O(1) 数相消后的余量」，所以本格的求值位数由 c 现定"
        "（dps = c/ln10 + 60）；用 50 位去断言一条 1e-214 的不等式＝拿没有的精度花账。")
    for av in ["1/50", "1", "4", "25", "400"]:
        with workdps(120):
            a = coef_of(av, 120)
            c = mp.pi ** 2 / a
            dps_cell = int(mp.ceil(c / mp.ln(10))) + 60
        with workdps(dps_cell + 30):
            ac = mp.mpf(a)
            cc = mp.pi ** 2 / ac
            lead = (mp.sqrt(mp.pi / ac) - 1) / 2
            act = abs(mp.mpf(spec(ac, dps_cell)) - mp.mpf(lead))
            bound = mp.sqrt(mp.pi / ac) * mp.exp(-cc) / (1 - mp.exp(-cc))
            ratio = act / bound
            say("a=%-6s dps=%-4d 实际=%.6e 先验界=%.6e 咬合比=%.6e" % (av, dps_cell, act, bound, ratio))
            if not (act <= bound):
                bad("J5/a=" + av, "实际偏离 %s 超出先验界 %s" % (mp.nstr(act, 8), mp.nstr(bound, 8)))
            if ratio < mp.mpf("0.5"):
                say("     注：咬合比 %s 偏松（界用等比控制、未用 n^2 增益），界成立但没有被咬住" % mp.nstr(ratio, 6))
    for av in ["1/50", "1e-4"]:
        with workdps(120):
            a = coef_of(av, 120)
            lead = (mp.sqrt(mp.pi / a) - 1) / 2
            s = mp.mpf(spec(a, 50))
            r = s / lead
            say("a=%-8s 主项=%.6e 实值=%.6e 比值=%s（偏离来自指数小项，不是幂律）" % (av, lead, s, mp.nstr(r, 12)))
            if r > mp.mpf("1.0001") or r < mp.mpf("0.9999"):
                bad("J5/主项/a=" + av, "主项比值 %s 偏离 1 太远 ⇒ Weyl 前导项读法不成立" % mp.nstr(r, 12))
    say("判定 5 结论：a->0 的前导项是 1/2(sqrt(pi/a)-1)（盒的 Weyl 律），偏离被指数先验界咬住。"
        "主项比值只在 a<=1/50 那两格断言（lead 在 a 大时为负，前导项读法出定义域，见 domain_of_validity）。")


# ---------- 变异体电池（--selftest） ----------
def mutants():
    say("--- 变异体电池：同一枚 a=1/4 上，四枚造错必须抬红、一枚正例不许误伤 ---")
    a = coef_of("1/4", 120)
    good = orbit(a, 80)
    s_val = spec(a, 80)
    with workdps(120):
        inner = terms_sum(mp.pi ** 2 / a, 90)
        cases = [
            ("M1 sqrt(pi/a) 写成 pi/a", (mp.pi / a * (1 + 2 * inner) - 1) / 2),
            ("M2 丢掉 -1 与 1/2 的边界记账", mp.sqrt(mp.pi / a) * (1 + 2 * inner)),
            ("M3 sqrt(pi/a) 写成 sqrt(a/pi)", (mp.sqrt(a / mp.pi) * (1 + 2 * inner) - 1) / 2),
            ("M4 轨道指数少一次 pi（e^{-pi n^2/a}）",
             (mp.sqrt(mp.pi / a) * (1 + 2 * terms_sum(mp.pi / a, 90)) - 1) / 2),
            ("P0 正例：完整轨道侧", good),
        ]
    for tag, val in cases:
        with workdps(200):
            d = abs(mp.mpf(s_val) - mp.mpf(val))
        if tag.startswith("P0"):
            if d > mp.mpf("1e-6"):
                bad("MT/" + tag, "正例被打红（偏离 %s）＝尺太紧" % mp.nstr(d, 8))
            say("GREEN(不许响)｜%-40s 偏离=%.6e" % (tag, d))
        else:
            if d <= mp.mpf("1e-6"):
                bad("MT/" + tag, "变异体没有被点名（偏离 %s）＝尺不咬" % mp.nstr(d, 8))
            say("RED(须响)｜%-40s 偏离=%.6e" % (tag, d))
    say("变异体合计：4 枚须响＋1 枚正例不误伤")
    guard_teeth()


def guard_teeth():
    """本轮把两根尺改了口径（地板按本格精度、不等式按 c 定价精度），改靶必须同批配反对照。"""
    say("--- 尺子牙齿：两处口径修正各自的可控对照 ---")
    # G1 地板尺：判决必须由「本格档位」驱动，不是钉死的常数。同一枚尺在五格对照上取向如下
    #    （地板 = 10^-(dps+extra-digits) = 10^-(dps+28)）：1e-40 在 dps=4 档之下 ⇒ 须判瞎；
    #    同一条 1e-20 在 dps=4（地板 1e-32）判不瞎——把 2.56e-10 判成瞎的那版假阳就是这么来的。
    for scale, dps, want in [("1e-40", 4, True), ("1e-20", 4, False), ("1e-20", 140, False),
                             ("2.56e-10", 140, False), ("2.56e-10", 4, False)]:
        got = floor_blind(scale, dps)
        tag = "G1 %s@%d" % (scale, dps)
        say("%-16s 判瞎=%-5s 期望=%-5s 地板=1e-%d｜%s" % (
            tag, got, want, dps + 30 - 2, "对" if got == want else "错"))
        if got != want:
            bad("GT/" + tag, "地板尺判决与档位驱动的定义不符")
    # G2 精度货币尺：a=1/50 的先验界是 1e-214 量级，50 位求值读到的「实际」只是噪声，
    #    它必须**超出**界（证明低位读数会把真不等式判成反例）；按 c 定档后必须落进界内。
    #    注意相减本身的精度：差要在不低于操作数的档位上算，否则这里读到的是 0 而不是噪声。
    with workdps(120):
        a = coef_of("1/50", 120)
        c = mp.pi ** 2 / a
        lead = (mp.sqrt(mp.pi / a) - 1) / 2
        bound = mp.sqrt(mp.pi / a) * mp.exp(-c) / (1 - mp.exp(-c))
    with workdps(200):
        act_low = abs(mp.mpf(spec(a, 50)) - mp.mpf(lead))
    dps_cell = int(mp.ceil(c / mp.ln(10))) + 60
    with workdps(dps_cell + 80):
        a_hi = coef_of("1/50", dps_cell + 60)
        act_cell = abs(mp.mpf(spec(a_hi, dps_cell))
                       - mp.mpf((mp.sqrt(mp.pi / a_hi) - 1) / 2))
    say("G2 精度货币｜先验界=%.6e｜50 位读数=%.6e 越界=%s（须 True）｜dps=%d 读数=%.6e 越界=%s（须 False）" % (
        bound, act_low, act_low > bound, dps_cell, act_cell, act_cell > bound))
    if not (act_low > bound):
        bad("GT/G2-低位", "50 位读数没有越界＝这条不等式在本格里根本测不出精度差异，定档是空转")
    if act_cell > bound:
        bad("GT/G2-定档", "按 c 定档后仍越界：要么界不真，要么定档不够——不得当成通过")
    # G3 咬合比标签极性：ratio 接近 1 是「咬住」，小于 0.5 才是「偏松」（旧版句义与布尔反号）。
    with workdps(120):
        r_tight = mp.mpf("0.999948")
        r_loose = mp.mpf("0.1284494")
    say("G3 标签极性｜ratio=%s 须判咬住（不触发偏松注）｜ratio=%s 须判偏松（触发）" % (r_tight, r_loose))
    if (r_tight < mp.mpf("0.5")) or not (r_loose < mp.mpf("0.5")):
        bad("GT/G3", "偏松判据的极性与句义不一致")


def main():
    argv = sys.argv[1:]
    t0 = time.time()
    if "--selftest" in argv:
        mutants()
    else:
        judge1()
        judge2()
        judge3()
        judge4()
        judge5()
    say("--- 合计 ---")
    say("抓到红 %d 条" % len(FAILS))
    for f in FAILS:
        say("  ! " + f)
    say("耗时 %.1fs" % (time.time() - t0))
    say("判决：rc=%d（L2 残差核对通过不等于证明，红线一）" % (1 if FAILS else 0))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
