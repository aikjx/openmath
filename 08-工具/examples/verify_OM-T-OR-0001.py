# -*- coding: utf-8 -*-
"""OM-T-OR-0001 判定册：M/M/1 的几何平稳量与 Little 律闭合形式（十枚通道）。

红线一：本脚本只做**残差核对**，不构成证明；PASS 只覆盖这里点名的通道、采样点与两条通路。
红线八：不复制晚于本面落盘的闸门读数；任何「条数／枚数」一律让读者现读版面。

五条判定（每条都有第二通道，不是把同一条式子算两遍）：
 判定 1  字符串路 vs 对象路：十枚通道从盘上 YAML 的 sympy 字段按括号深度拆回来，
         与脚本用 sympy 对象重拼的十枚逐枚比 `expand(差)==0`（结构级），再逐枚比 80 位代值（数值级）。
 判定 2  独立生产者：第一段只用四条细致平衡方程（不含任何归一化）现推 p_n = p_0 * r^n，不借闭式；
         第二段把无限归一化读成「部分和与 1 之差恰为闭式余项 r^(K+1)」，且项数 K+1 由 r 与衰减尺
         STABILITY_DECAY=1e-20 现场循环算出（第一版把 K 手感钉成 40，于是 r=1/2 的余项 2^-41≈4.5e-13
         永远够不到 1e-20，判红的是自己的旋钮，不是数学）；
         第三段把归一化换成 sum_{n<=4}p_n=1，现推出来的是**有限容量链**，它必须与卡面闭式不同值——
         两种归一化币种若读成同一个数，这一段就是抄表（电池 M4 用 denom_exp=4/5 两档测这把尺的牙）。
 判定 3  概率侧（这一侧真的需要稳定性）：截断和 sum_{n<=K} pi_n 与 1-r^{K+1} 之差须恰为 0（有限几何恒等式），
         截断期望与闭式 r/(1-r) 之差才是收敛性读数——r=1/2 那格须小于 1e-20，r=2 那格须大于 1，两格都印。
 判定 4  稳定性承重控制：r=1 那格「五枚非有限／五枚 0」的分裂形状、r=2 那格「十枚仍全零
         而 pi_0=-1、尾项 -1.0995e+12」——断言这个形状，因为它就是「机器字段对稳定条件零分辨力」的证人。
 判定 5  边界与视界：r->1^- 时 L_s 单调发散（0.9/0.99/0.999 三档）；同一被积式把视界推到 +oo
         时 sympy 返回 Piecewise（按 mu-lambda_a 的符号分支）——本卡因此只声明有限视界。

仪器自记（本轮栽过的坑，写在脸上防复发）：
  * 预演台 v1 自己崩在收口之前：摘除律夹具把「放宽一档」的期望写成 [p,T]，而 p 在夹具里有两枚主人，
    摘掉一枚还剩一枚，永远抓不到——真能测出放宽的只有 sole-owner 的 T。见证 scratch/T20_OR_probe.v1_NOVERDICT.txt。
  * 「十枚全绿」不是稳定性的证据：r=2 那格它照样全绿。所以判定 4 把这句话做成断言而不是散文。
  * r=1 那格五枚读数是 sympy 的 NaN 型：is_nan 属性在 sympy 1.13 已不存在（早先据此崩过一次），
    而 NaN.is_finite 读成 None（未定），不是 False——所以分桶只能用 `is_finite is not True`，
    并把类型名一起印出，免得散文把「读不成数」写成「读成无穷」。
  * 空脚本也返回 rc=0，所以判定面非空由驱动器另行断言，不由本文件的退出码担保。
"""
import io
import os
import platform
import sys
import time

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
CARD_REL = os.path.join("02-公式库", "运筹与系统科学",
                        "OM-T-OR-0001-mm1-geometric-stationary-law-and-little-identity.yaml")
CARD = os.path.join(ROOT, CARD_REL)
DPS = 80
PASS_TOL = sp.Rational(1, 10) ** 40
STABILITY_DECAY = sp.Rational(1, 10) ** 20
TAGS = ["G1_归一化有限和K=1", "G2_归一化有限和K=2", "B1_细致平衡0到1", "B2_细致平衡1到2",
        "L1_Little律", "L2_队长自洽", "L3_逗留时间分解", "U1_占用率", "Q1_排队长闭式",
        "E1_尾积分有限视界"]
FAILS = []
CHECKS = [0]


def say(line=""):
    print(line)


def bad(tag, detail):
    FAILS.append(tag)
    say("  [红] %s :: %s" % (tag, detail))


def ok(tag, detail=""):
    CHECKS[0] += 1
    say("  [绿] %s%s" % (tag, (" :: " + detail) if detail else ""))


def split_sos(src):
    """按括号深度把平方和拆回逐通道：深度 0 的 '+' 才是通道分隔，括号里的 '+' 是通道内部。"""
    parts, depth, cur = [], 0, []
    for ch in src:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("括号在拆到第 %d 枚时提前闭合" % len(parts))
        if ch == "+" and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


def primitives(mode="clean"):
    """对象路的原始构件：pi_n 闭式、L_s、W_s、L_q、W_q。变异体只改这里，不改比较逻辑。"""
    la = sp.Symbol("lambda_a")
    mu = sp.Symbol("mu")
    r = la / mu
    one_minus_r = (1 + r) if mode == "M1_pi_sign" else (1 - r)
    pi = lambda n: one_minus_r * r ** n
    L_s = r / (1 - r)
    W_s = 1 / (la - mu) if mode == "M2_little_flipped" else 1 / (mu - la)
    L_q = r ** 2 / (1 - r)
    W_q = la / (mu * (mu - la))
    return la, mu, r, pi, L_s, W_s, L_q, W_q


def object_channels(mode="clean"):
    la, mu, r, pi, L_s, W_s, L_q, W_q = primitives(mode)
    T = sp.Rational(5, 2)
    t = sp.Symbol("t")
    return [
        (TAGS[0], (pi(0) + pi(1) - (1 - r ** 2)) ** 2),
        (TAGS[1], (pi(0) + pi(1) + pi(2) - (1 - r ** 3)) ** 2),
        (TAGS[2], (pi(0) * la - pi(1) * mu) ** 2),
        (TAGS[3], (pi(1) * la - pi(2) * mu) ** 2),
        (TAGS[4], (L_s - la * W_s) ** 2),
        (TAGS[5], (L_s - (r + r * L_s)) ** 2),
        (TAGS[6], (W_s - (W_q + 1 / mu)) ** 2),
        (TAGS[7], (1 - pi(0) - r) ** 2),
        (TAGS[8], (L_q - la ** 2 / (mu * (mu - la))) ** 2),
        (TAGS[9], (sp.integrate(r * sp.exp(-(mu - la) * t), (t, 0, T))
                   - r * (1 - sp.exp(-(mu - la) * T)) / (mu - la)) ** 2),
    ]


def card_field():
    from openmath import record as rec_mod
    data, err = rec_mod.load_yaml(CARD)
    if err:
        raise RuntimeError("卡读不回来：%s" % err)
    return data, split_sos(data["sympy"])


def j1(mode="clean"):
    say("--- 判定 1 字符串路 vs 对象路（十枚通道，结构级 + 数值级两把尺）---")
    data, parts = card_field()
    if len(parts) != 10:
        bad("J1-split", "按深度 0 的 '+' 拆出 %d 枚（应为 10）——字段的形状变了，判集不许塌缩" % len(parts))
        return
    ok("J1-split", "盘上字段 %d 字符拆回 %d 枚，与 TAGS 等长" % (len(data["sympy"]), len(parts)))
    obj = object_channels(mode)
    assert len(obj) == len(parts)
    samples = [("1/2", "1"), ("7/4", "2")]
    struct_red, num_red = 0, 0
    for (tag, oe), src in zip(obj, parts):
        se = sp.sympify(src)
        same = sp.expand(se - oe) == 0
        resid = []
        for lv, mv in samples:
            subs = {sp.Symbol("lambda_a"): sp.Rational(lv), sp.Symbol("mu"): sp.Rational(mv)}
            resid.append((sp.N(se.subs(subs), 30), sp.N(oe.subs(subs), 30)))
        zeros = all(sv == 0 and ov == 0 for sv, ov in resid)
        if not same:
            struct_red += 1
            say("    %-22s 结构级=差非零（对象路与字符串路不是同一枚式子） 数值级(串/对)=%s" % (tag, resid))
        elif not zeros:
            num_red += 1
            say("    %-22s 结构级=同 数值级=非零 %s" % (tag, resid))
        else:
            say("    %-22s 结构级=同 数值级=两路在两格上均恰 0" % tag)
    if struct_red:
        bad("J1-structure", "%d 枚通道的字符串路与对象路展开后不同文（模式 %s）" % (struct_red, mode))
    elif num_red:
        bad("J1-numeric", "%d 枚通道同文却在格点上不归零（两路各自都要读 0）" % num_red)
    else:
        ok("J1-clean", "十枚通道两路同文且逐格、逐路归零（模式 %s）；红线一：这只说明代数量级，不说明 lambda_a<mu" % mode)


def j2_trunc(la_v, mu_v, card_side, denom_exp=5, report=True):
    """截断链 vs 无限链的归一化币种：返回红名册（空＝绿）。denom_exp 是币种旋钮，电池用 4 造错。"""
    r = la_v / mu_v
    q = sp.symbols("q0:5")
    eqs2 = [q[i] * la_v - q[i + 1] * mu_v for i in range(4)] + [sum(q) - 1]
    sol2 = sp.solve(eqs2, list(q), dict=True)
    red = []
    if len(sol2) != 1:
        red.append("J2-trunc-solve(枚数=%d)" % len(sol2))
        return red
    got = [sp.nsimplify(sol2[0][x]) for x in q]
    finite_form = [(1 - r) * r ** n / (1 - r ** denom_exp) for n in range(5)]
    if report:
        say("    截断链现推 q_0..q_4 = %s" % ",".join(str(x) for x in got))
        say("    有限容量闭式 (1-r)r^n/(1-r^%d) = %s｜卡面无限闭式 = %s" % (
            denom_exp, ",".join(str(x) for x in finite_form), ",".join(str(x) for x in card_side)))
    if [sp.simplify(a - b) for a, b in zip(got, finite_form)] != [sp.Integer(0)] * 5:
        red.append("J2-trunc-match")
    if sp.simplify(got[0] - card_side[0]) == 0:
        red.append("J2-teeth(截断与无限读成同一个数)")
    if report and not red:
        ok("J2-trunc", "同一组平衡方程、两种归一化币种：q_0=%s 对 pi_0=%s，差=%s ⇒ 判定 2 分得出「截断（有限容量 5）」与「无限链」" % (
            got[0], card_side[0], sp.simplify(got[0] - card_side[0])))
    return red


def j2():
    say("--- 判定 2 独立生产者：只用细致平衡方程现推几何比，不借闭式 ---")
    la_v, mu_v = sp.Rational(1, 2), sp.Integer(1)
    r = la_v / mu_v
    p = sp.symbols("p0:5")
    eqs = [p[i] * la_v - p[i + 1] * mu_v for i in range(4)]
    sol = sp.solve(eqs, list(p[1:]), dict=True)
    if len(sol) != 1:
        bad("J2-solve", "平衡方程侧解的枚数=%d（应为 1 枚参数族），本卡不判定那种退化" % len(sol))
        return
    ratios = [sp.simplify(sol[0][p[n]] - p[0] * r ** n) for n in range(1, 5)]
    say("    平衡方程（不含任何归一化）现推：p_n = p_0 * r^n 的差 = %s" % ",".join(str(x) for x in ratios))
    if any(x != 0 for x in ratios):
        bad("J2-ratio", "几何比没被独立推出（差非零 %s）——判定 2 的第一段不许登记" % ratios)
        return
    ok("J2-ratio", "四枚差全零：平衡方程自己就给出 p_n = p_0 r^n，这一段没有用卡面闭式，是第二台生产者")
    card_side = [(1 - r) * r ** n for n in range(5)]
    K2 = 0
    while not (r ** (K2 + 1) < STABILITY_DECAY):
        K2 += 1
    partial = sum((1 - r) * r ** n for n in range(K2 + 1))
    gap = sp.simplify(1 - partial)
    say("    无限归一化的可读形：尺=%s、r=%s ⇒ 现推需要前 %d 项（项数由 r 与尺算出，不手感钉）；部分和与 1 之差 = %s" % (
        STABILITY_DECAY, r, K2 + 1, gap))
    if gap != r ** (K2 + 1):
        bad("J2-normalize", "部分和与 1 之差读成 %s，不等于闭式余项 r^(K+1)=%s——归一化这一段没闭合" % (
            gap, r ** (K2 + 1)))
    elif not (gap < STABILITY_DECAY):
        bad("J2-normalize", "r=%s 那格的余项 %s 没衰减到 %s 之下——「稳定区」这个词在这里没有内容" % (
            r, gap, STABILITY_DECAY))
    else:
        ok("J2-normalize", "补齐 p_0=1-r 之后，前 %d 项部分和与 1 之差恰为 r^%d=%s（<%s）：无限归一化在 r<1 才读得通，"
                            "而这一步（r<1）不是机器判据，本卡只在有限和通道上读归一化" % (
           K2 + 1, K2 + 1, gap, STABILITY_DECAY))
    say("    截断对照（本判定第一版栽在这一格，读数原样留着）：把归一化改成 sum_{n<=4}p_n=1 解出来的是**有限容量链**")
    for item in j2_trunc(la_v, mu_v, card_side, denom_exp=5):
        bad(item.split("(")[0], "截断币种那格没收口（红项=%s）——判定 2 的第二段不许登记" % item)


def j3():
    say("--- 判定 3 概率侧：截断和与截断期望（这一侧真的要稳定性）---")
    K = 200
    for lam_v, mu_v, tag in [("1/2", "1", "r=1/2 稳态"), ("2", "1", "r=2 过载")]:
        la_v, mu_v = sp.Rational(lam_v), sp.Rational(mu_v)
        r = la_v / mu_v
        pi = lambda n: (1 - r) * r ** n
        s_norm = sum(pi(n) for n in range(K + 1))
        s_mean = sum(n * pi(n) for n in range(K + 1))
        d_norm = sp.simplify(s_norm - (1 - r ** (K + 1)))
        d_mean = sp.simplify(s_mean - r / (1 - r))
        say("    %-10s 截断归一化差=%s｜截断期望=%s，闭式 L_s=%s，截断余项=%s" % (
            tag, sp.N(d_norm, 8), sp.N(s_mean, 8), sp.N(r / (1 - r), 8), sp.N(d_mean, 8)))
        if d_norm != 0:
            bad("J3-finite", "%s 那格有限几何和差读成 %s（应为恰好 0）——G 族通道的机器形与手算不同文" % (
                tag, sp.N(d_norm, 8)))
        rem = sp.N(sp.Abs(r ** (K + 1)), 8)
        tail = sp.N(sp.Abs((1 - r) * r ** K), 8)
        say("    （余项 r^(K+1)=%s；尾项 (1-r)r^K=%s）" % (rem, tail))
        if r < 1:
            if not (tail < STABILITY_DECAY):
                bad("J3-tail", "稳态那格的尾项 (1-r)r^K=%s 没衰减到 %s 之下" % (tail, STABILITY_DECAY))
            elif sp.Abs(d_mean) > STABILITY_DECAY:
                bad("J3-mean", "稳态那格的截断期望与闭式差=%s，大于 %s——截断余项不该在这个尺度上还手" % (
                    sp.N(d_mean, 8), STABILITY_DECAY))
            else:
                ok("J3-tail", "r=1/2：尾项=%s、截断期望与闭式之差=%s，两者都在 %s 之下（这才是「收敛」的可读形）" % (
                    tail, sp.N(d_mean, 8), STABILITY_DECAY))
        else:
            if rem < 1:
                bad("J3-diverge", "r=2 那格 r^(K+1) 读成 %s，没有发散——判定 3 的对照没牙" % rem)
            elif sp.Abs(d_mean) < 1:
                bad("J3-diverge", "r=2 那格截断期望与闭式只差 %s，没有分开——过载对照没牙" % sp.N(d_mean, 8))
            else:
                ok("J3-diverge", "r=2：余项 r^(K+1)=%s、截断期望与闭式之差=%s（无穷和不存在），闭式在那里不再是期望值 ⇒ 概率侧确实要 lambda_a<mu" % (
                    rem, sp.N(d_mean, 8)))
        if tag.startswith("r=1/2"):
            say("    （对照记：判定 1 的十枚通道在 r=2 那格仍全零，见判定 4；两件事别混着引）")


def j4(enforce=True):
    """返回本判定登记的断言枚数——牙齿台用「撤掉控制 ⇒ 断言枚数变 0」来演示没牙的尺长什么样。"""
    say("--- 判定 4 稳定性承重控制（机器字段对 lambda_a<mu 零分辨力）---")
    made = 0
    for lam_v, mu_v, tag in [("1", "1", "r=1 临界"), ("2", "1", "r=2 过载")]:
        subs = {sp.Symbol("lambda_a"): sp.Rational(lam_v), sp.Symbol("mu"): sp.Rational(mu_v)}
        vals = [sp.N(oe.subs(subs), 20) for _t, oe in object_channels("clean")]
        zero_idx = [i for i, v in enumerate(vals) if v == 0]
        odd_idx = [i for i, v in enumerate(vals) if v != 0]
        unreadable_idx = [i for i in odd_idx if getattr(vals[i], "is_finite", None) is not True]
        finite_odd = [vals[i] for i in odd_idx if i not in unreadable_idx]
        kinds = ",".join(sorted(set(type(vals[i]).__name__ for i in odd_idx)))
        rho = sp.Rational(lam_v) / sp.Rational(mu_v)
        pi0 = 1 - rho
        tail = sp.N(pi0 * rho ** 40, 8)
        say("    %-8s 十枚读数 零=%d 读不成数(is_finite 不为 True)=%d 有限非零=%d（非零读数的类型=%s）｜pi_0=%s｜尾项 (1-rho)rho^40=%s" % (
            tag, len(zero_idx), len(unreadable_idx), len(finite_odd), kinds, pi0, tail))
        if not enforce:
            continue
        made += 4
        if finite_odd:
            bad("J4-shape", "%s 那格有 %d 枚读数既不是 0 也读不成数（%s）——残差形状超出本判定能命名的种类" % (
                tag, len(finite_odd), ",".join(str(v) for v in finite_odd)[:60]))
        if tag.startswith("r=1"):
            if len(zero_idx) != 5:
                bad("J4-critical", "r=1 那格零读数 %d 枚（期望 5 枚多项式通道）——含商通道与多项式通道的分界动了，读不成数=%d 枚" % (
                    len(zero_idx), len(unreadable_idx)))
            elif len(unreadable_idx) != 5:
                bad("J4-critical", "r=1 那格读不成数的读数 %d 枚（期望 5 枚含商通道），类型=%s" % (
                    len(unreadable_idx), kinds))
            else:
                ok("J4-critical", "r=1：恰五枚归零（G1/G2/B1/B2/U1 那五枚多项式），另五枚读成类型 %s（is_finite 不为 True）——所以采样点不含它，引擎会跳点" % kinds)
        else:
            if len(zero_idx) != 10:
                bad("J4-blind", "r=2 那格零读数 %d 枚（期望 10）——字段已不是对 rho 的恒等式，判定 4 的前提塌了" % len(zero_idx))
            else:
                ok("J4-blind", "r=2：十枚通道仍全部归零，而 pi_0=-1、尾项=%s ⇒ 「L2 PASS」不是稳定性的证据（本卡把它写进 caveat）" % tail)
            if pi0 >= 0 or tail > -1:
                bad("J4-prob", "过载那格 pi_0 或尾项没有破（pi_0=%s 尾项=%s）——概率侧的控制没牙" % (pi0, tail))
    return made


def j5():
    say("--- 判定 5 边界与视界：r->1^- 发散 + 无穷视界的分支形状 ---")
    prev = None
    for rv in [sp.Rational(9, 10), sp.Rational(99, 100), sp.Rational(999, 1000)]:
        L = rv / (1 - rv)
        say("    r=%-6s L_s=r/(1-r)=%s" % (rv, sp.N(L, 8)))
        if prev is not None and not (L > prev):
            bad("J5-mono", "L_s 没有随 r->1^- 单调上升（%s -> %s）" % (prev, L))
        prev = L
    ok("J5-mono", "三档单调上升：9 → 99 → 999，稳定区边界上队长发散（这不是反例，是断言的边界形状）")
    la, mu, t = sp.Symbol("lambda_a"), sp.Symbol("mu"), sp.Symbol("t")
    inf = sp.integrate(la / mu * sp.exp(-(mu - la) * t), (t, 0, sp.oo))
    say("    同一被积式推到 +oo：%s" % str(inf)[:120])
    if "Piecewise" not in str(inf):
        bad("J5-piece", "无穷视界没返回 Piecewise——本卡 hypotheses 里「按 mu-lambda_a 分支」那句现读失效，须就地订正")
    else:
        ok("J5-piece", "符号层返回 Piecewise（按 mu-lambda_a 的符号分支）⇒ 本卡只声明有限视界 T=5/2，分支不当结论用")


def battery():
    say("--- 变异体电池（--selftest）：四枚造错须被点名，干净版不许误伤 ---")
    caught, defect = 0, []
    say("  [M1] 对象路的 pi 闭式把 (1-r) 写成 (1+r)：判定 1 须红")
    before = len(FAILS)
    j1("M1_pi_sign")
    if len(FAILS) > before:
        caught += 1
        say("       => 抓住（判定 1 转红）")
        del FAILS[before:]
    else:
        defect.append("M1 没被抓住")
    say("  [M2] Little 右端 W_s 符号翻转成 1/(lambda_a-mu)：判定 1 须红")
    before = len(FAILS)
    j1("M2_little_flipped")
    if len(FAILS) > before:
        caught += 1
        say("       => 抓住（判定 1 转红）")
        del FAILS[before:]
    else:
        defect.append("M2 没被抓住")
    say("  [M3] 撤掉判定 4 的断言（enforce=False）：牙齿台须报「这一判定不再产生任何断言」")
    made_off = j4(enforce=False)
    made_on = j4(enforce=True)
    if made_off == 0 and made_on > 0:
        caught += 1
        say("       => 抓住：撤控制⇒登记断言 0 枚，装控制=>%d 枚（没牙的尺就是这种形状，本电池要求它必须可见）" % made_on)
    else:
        defect.append("M3 形状不符（撤掉后登记 %d 枚，装上后 %d 枚）" % (made_off, made_on))
    say("  [M4] 判定 2 的币种旋钮从「有限容量 5」拧到「有限容量 4」：现推链须与闭式偏离（J2-trunc-match 须响）")
    la_v, mu_v = sp.Rational(1, 2), sp.Integer(1)
    rr = la_v / mu_v
    card_side = [(1 - rr) * rr ** n for n in range(5)]
    red_off = j2_trunc(la_v, mu_v, card_side, denom_exp=4)
    red_on = j2_trunc(la_v, mu_v, card_side, denom_exp=5, report=False)
    if red_off and not red_on:
        caught += 1
        say("       => 抓住：错币种红项=%s，正确币种红项=%s（同一台生产者，只差归一化那一枚分母）" % (
            ",".join(red_off), ",".join(red_on) or "NONE"))
    else:
        defect.append("M4 形状不符（denom_exp=4 红项=%s｜denom_exp=5 红项=%s）" % (
            ",".join(red_off) or "NONE", ",".join(red_on) or "NONE"))
    say("  [正对照] 干净版判定 1 不许误伤：")
    before = len(FAILS)
    j1("clean")
    if len(FAILS) == before:
        say("       => 未误伤（正对照通过）")
    else:
        defect.append("正对照被误伤（干净版判定 1 转红）")
    say("变异体合计：应响 4 枚，实响 %d 枚｜DEFECT %d 枚：%s" % (
        caught, len(defect), "; ".join(defect) or "NONE"))
    if len(defect):
        bad("BATTERY", "; ".join(defect))
    if caught != 4:
        bad("BATTERY-COUNT", "抓住枚数 %d != 4——电池自己没接上" % caught)


def main():
    mode = "selftest" if "--selftest" in sys.argv else "clean"
    say("OM-T-OR-0001 判定册｜模式=%s｜时刻 %s" % (mode, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    import hashlib
    raw = io.open(CARD, "rb").read()
    say("卡=%s %d B md5=%s｜python=%s sympy=%s" % (
        os.path.relpath(CARD, ROOT).replace("\\", "/"), len(raw),
        hashlib.md5(raw).hexdigest()[:12], platform.python_version(), sp.__version__))
    if mode == "selftest":
        battery()
    else:
        j1("clean")
        j2()
        j3()
        j4(enforce=True)
        j5()
    say("")
    say("登记断言 %d 枚｜抓到红 %d 条" % (CHECKS[0], len(FAILS)))
    if FAILS:
        say("==> verdict: RED %d 条（%s）" % (len(FAILS), ",".join(FAILS)))
        say("==> rc=1 的含义只有「上面这些条自己判红」；它不是对 M/M/1 任何定理的判决（红线一）")
    else:
        say("==> verdict: CLEAN（本模式 %s 下点名判定全部收口）" % mode)
        say("==> rc=0 的含义只有「判集非空且逐条收口」；红线一：十枚通道是 rho 的恒等式，L2 PASS 不携带 lambda_a<mu（判定 4 现印）")
    return 1 if FAILS else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        say("==> verdict: NO VERDICT（崩在收口之前，本图不可引用）：%s: %s" % (
            type(exc).__name__, str(exc)[:120]))
        raise
