# -*- coding: utf-8 -*-
"""OM-T-SC-0001 Cramér–Rao 不等式的独立验证脚本（第 13 批）。

    定理：T 为 g(θ) 的无偏估计（E_θ[T]=g(θ)）时
          Var_θ(T) >= g'(θ)^2 / I_n(θ)，  I_n(θ)=E_θ[score^2]=-E_θ[d^2 log p/dθ^2]，
          等号成立 <=> score = a(θ)·(T - g(θ))。

本库不重做证明（红线八：定理出自已刊文献，见记录 fact_check）。这台仪器办四件事：

1) **两个可算族的 Fisher 信息各用两条结构不同的通道算**，两条同值才算数。
   二项族 Bin(m,q)：通道 A＝按定义直接求和 Σ p·(d log p/dq)²（纯精确有理，无浮点）；
                     通道 B＝自然参数的对数配分曲率 A''(η) 除回雅可比 (dq/dη)²（50 dps 数值）。
   正规位置族 N(θ,σ²)：通道 A＝score² 的期望；通道 B＝期望曲率 −E[∂² log p]。
2) **「无偏」也核对**，不当定义跳过：尺度族 N(0,σ²) 里 T=sqrt(π/2)|x| 对 σ 无偏——
   无偏性本身就是一条积分子，与 Fisher 通道互相独立。
3) **等号条件必须有判别力**：同一把尺在「达到界」与「达不到界」两个例子上必须给出不同裁定，
   且与「方差减界」那条独立通道同判。判据实现为**可解性检验**：
   若存在 a 使 score_j = a·(T_j - g) 对若干采样点同时成立，则等号可及；否则不可及。
   位置族（T=x）⇒ 可及且 Var-界=0；尺度族（T=sqrt(π/2)|x|）⇒ 不可及且 Var-界>0。
   这是**双向**对照：只有一边红一边绿才说明尺子会判，全绿不算证据。
4) **第二口径**：sympy 的积分通道可能返回闭式也可能静默返回未算式，
   故位置族三条积分读数再由 mpmath 50 dps 数值求积独立复算，印两套读数的差；
   求积把 (-oo,oo) 换成 (-L,L)，尾概率上界现算并印出——截断误差自带账单。

诚实红线（红线一）：全部 PASS 只说明「脚本写下的这几个族、这几个采样点上没有算错」，
不构成证明，也不得被引作任何新结果。

用法：cd openmath && PYTHONIOENCODING=utf-8 python 08-工具/examples/verify_OM-T-SC-0001.py
     自检（变异体必须响、正例必须不误伤）：加 --selftest
退出码：0＝全部判定通过；1＝有判定不过；2＝前置条件缺失（未装 sympy/mpmath）。
"""
import sys
import time

try:
    import sympy as sp
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 sympy/mpmath，本脚本无判据可跑。安装: pip install sympy mpmath")
    sys.exit(2)

DPS = 50
mp.mp.dps = DPS
PI = sp.pi
SQRT = sp.sqrt
X, Q, ETA = sp.symbols("x q eta", real=True)
SG = sp.Symbol("sigma", positive=True)
TH = sp.Symbol("theta", real=True)
K = sp.Symbol("k", integer=True)
TOL_EXACT = mp.mpf(0)          # 精确有理通道：残差必须是 0，不留余地
TOL_CHANNEL = mp.mpf("1e-40")  # 两条不同来源的读数之差（50 dps）
TOL_QUAD = mp.mpf("1e-30")     # mpmath 求积 vs sympy 解析：开工前钉死，见判定4


def num(expr, dps=DPS):
    """代成 50 dps 的 mpf；解析式若没归约为数就抛，不静默返回符号。"""
    val = sp.N(expr, dps)
    if not val.is_Number:
        raise ValueError("解析式未归约为数：%s" % (sp.sstr(val)[:90],))
    return mp.mpf(sp.sstr(val))


def logp_loc(x_, sg_, th_):
    return -((x_ - th_) ** 2) / (2 * sg_ ** 2) - sp.log(sg_ * SQRT(2 * PI))


def logp_scale(x_, sg_):
    return -(x_ ** 2) / (2 * sg_ ** 2) - sp.log(sg_ * SQRT(2 * PI))


# ---------------------------------------------------------------- 判定 1：二项族
def binomial_pair(m, qnum, qden):
    """Bin(m,q) 的两通道读数。通道 A 精确有理；通道 B 走对数配分曲率＋雅可比。"""
    qq = sp.Rational(qnum, qden)
    p = sp.binomial(m, K) * Q ** K * (1 - Q) ** (m - K)
    score = sp.diff(sp.log(p), Q)
    norm = sp.summation(p, (K, 0, m))
    e_score = sp.summation(p * score, (K, 0, m))
    i_direct = sp.summation(p * score ** 2, (K, 0, m))
    target = sp.Rational(m) / (Q * (1 - Q))
    out = {
        "norm": num((norm - 1).subs({Q: qq})),
        "e_score": num(e_score.subs({Q: qq})),
        "i_direct": num((i_direct - target).subs({Q: qq})),
        "i_direct_mp": num(i_direct.subs({Q: qq})),
        "i_target_mp": num(target.subs({Q: qq})),
    }
    # 通道 B：eta=log(q/(1-q))，A(eta)=m log(1+e^eta)；I(q)=A''(eta)/(dq/deta)^2
    eta0 = sp.log(qq / (1 - qq))
    i_eta = num(sp.diff(m * sp.log(1 + sp.exp(ETA)), ETA, 2).subs({ETA: eta0}))
    dq_deta = num(sp.simplify(1 / sp.diff(sp.log(Q / (1 - Q)), Q)).subs({Q: qq}))
    out["i_channelB"] = i_eta / dq_deta ** 2
    out["channel_gap"] = out["i_channelB"] - out["i_direct_mp"]
    return out


# ---------------------------------------------------------------- 判定 2：位置族
def gaussian_location(sigma, theta):
    """N(θ,σ²)（σ 已知）：I(θ)=1/σ² 两通道、无偏性、Var(T)-界（T=x）。"""
    pts = {SG: sp.Rational(sigma), TH: sp.Rational(theta)}
    p = sp.exp(logp_loc(X, SG, TH))
    score = sp.diff(logp_loc(X, SG, TH), TH)
    curv = -sp.diff(logp_loc(X, SG, TH), TH, 2)
    integ = lambda f: sp.Integral(f, (X, -sp.oo, sp.oo))
    i_a = integ(p * score ** 2)
    i_b = integ(p * curv)
    var = integ((X - TH) ** 2 * p)
    e_sc = integ(p * score)
    tgt = 1 / SG ** 2
    return {
        "i_score": num((i_a - tgt).subs(pts)),
        "i_curv": num((i_b - tgt).subs(pts)),
        "i_two_channel": num((i_a - i_b).subs(pts)),
        "e_score": num(e_sc.subs(pts)),
        "var": num(var.subs(pts)),
        "var_minus_bound": num((var - 1 / tgt).subs(pts)),
        "i_value": num(i_a.subs(pts)),
        "crit_a": num((score / (X - TH)).subs(pts).subs({X: sp.Rational(3, 7)})),
    }


# ---------------------------------------------------------------- 判定 3：尺度族
def gaussian_scale(sigma):
    """N(0,σ²)：I(σ)=2/σ² 两通道；T=sqrt(π/2)|x| 无偏但不达界。"""
    pts = {SG: sp.Rational(sigma)}
    p = sp.exp(logp_scale(X, SG))
    score = sp.diff(logp_scale(X, SG), SG)
    curv = -sp.diff(logp_scale(X, SG), SG, 2)
    tgt = 2 / SG ** 2
    c = SQRT(PI / 2)
    m1 = 2 * sp.Integral(X * p, (X, 0, sp.oo))      # E|x|，避开 Abs 的积分
    m2 = sp.Integral(X ** 2 * p, (X, -sp.oo, sp.oo))
    i_a = sp.Integral(p * score ** 2, (X, -sp.oo, sp.oo))
    i_b = sp.Integral(p * curv, (X, -sp.oo, sp.oo))
    var_t = c ** 2 * (m2 - m1 ** 2)                 # Var(c|x|)
    out = {
        "unbiased": num((c * m1 - SG).subs(pts)),
        "i_score": num((i_a - tgt).subs(pts)),
        "i_curv": num((i_b - tgt).subs(pts)),
        "i_two_channel": num((i_a - i_b).subs(pts)),
        "var_t": num(var_t.subs(pts)),
        "bound": num((1 / tgt).subs(pts)),
        "var_minus_bound": num((var_t - 1 / tgt).subs(pts)),
        "var_over_bound": num((var_t * tgt).subs(pts)),
    }
    # 等号条件可解性：由采样点 x1 解出 a，代回 x2，残差非零⇒不可及（取最大者）
    t = c * sp.Abs(X)
    worst = mp.mpf(0)
    pair = None
    out["crit_inconsistency"] = mp.mpf(0)
    for x1, x2 in ((1, 2), (1, -2), (2, 3)):
        a_est = score.subs(pts).subs({X: sp.Integer(x1)}) / (t.subs({X: sp.Integer(x1)}) - sp.Rational(sigma))
        resid = score.subs(pts).subs({X: sp.Integer(x2)}) - a_est * (t.subs({X: sp.Integer(x2)}) - sp.Rational(sigma))
        r = num(sp.simplify(resid))
        if abs(r) > worst:
            worst, pair = abs(r), (x1, x2)
            out["crit_inconsistency"] = r
    out["crit_pair"] = pair
    return out


def location_criterion(sigma, theta):
    """位置族的同一把可解性尺：残差必须为 0（等号可及）。"""
    pts = {SG: sp.Rational(sigma), TH: sp.Rational(theta)}
    score = sp.diff(logp_loc(X, SG, TH), TH)
    t = X
    worst = mp.mpf(0)
    for x1, x2 in ((1, 2), (-3, 5), (0, 4)):
        d1 = t.subs({X: sp.Integer(x1)}) - sp.Rational(theta)
        if d1 == 0:
            continue
        a_est = score.subs(pts).subs({X: sp.Integer(x1)}) / d1
        resid = num(sp.simplify(score.subs(pts).subs({X: sp.Integer(x2)}) - a_est
                                * (t.subs({X: sp.Integer(x2)}) - sp.Rational(theta))))
        worst = max(worst, abs(resid))
    return worst


# ---------------------------------------------------------------- 判定 4：mpmath 复核
def numeric_location(sigma, theta):
    """独立仪器：50 dps 数值求积重算位置族三条积分，并附尾概率账单。"""
    s, t0 = mp.mpf(sigma), mp.mpf(theta)
    dens = lambda u: mp.exp(-(u - t0) ** 2 / (2 * s * s)) / (s * mp.sqrt(2 * mp.pi))
    L = s * 40
    tail = 2 * mp.erfc(mp.mpf(L) / (s * mp.sqrt(2)))
    i_a = mp.quad(lambda u: dens(u) * ((u - t0) / (s * s)) ** 2, [-L, L])
    var = mp.quad(lambda u: (u - t0) ** 2 * dens(u), [-L, L])
    e_sc = mp.quad(lambda u: dens(u) * (u - t0) / (s * s), [-L, L])
    return dict(i=i_a, var=var, e_score=e_sc, tail=tail, L=L, target=1 / (s * s))


# ---------------------------------------------------------------- 自检：牙齿
def selftest():
    """变异体（必须响）＋正例（必须不误伤）。全绿不算证据，所以两边都要跑。"""
    print("=== 变异体自检（--selftest）===")
    ok = True
    m = 5
    qq = sp.Rational(2, 5)
    p = sp.binomial(m, K) * Q ** K * (1 - Q) ** (m - K)
    score = sp.diff(sp.log(p), Q)
    i_direct = sp.summation(p * score ** 2, (K, 0, m))

    for name, expr, want_nonzero in [
        ("M1 把二项 Fisher 错标成 m·q(1-q)（拿 A''(eta) 当 I(q)）",
         sp.simplify((i_direct - m * Q * (1 - Q)).subs({Q: qq})), True),
        ("M2 把位置族 Fisher 错标成 1/σ（少一次方）",
         num((sp.Integral(sp.exp(logp_loc(X, SG, TH)) * sp.diff(logp_loc(X, SG, TH), TH) ** 2,
                          (X, -sp.oo, sp.oo)) - 1 / SG).subs({SG: 2, TH: 1})), True),
        ("M4 二项漏掉二项系数（p=q^k(1-q)^(m-k)）的归一化",
         num((sp.summation(Q ** K * (1 - Q) ** (m - K), (K, 0, m)) - 1).subs({Q: qq})), True),
    ]:
        rv = expr if isinstance(expr, mp.mpf) else num(sp.simplify(expr))
        hit = (abs(rv) > 0) if want_nonzero else (abs(rv) == 0)
        print("%s：残差 %s ⇒ %s" % (name, mp.nstr(rv, 10),
                                    "响（被抓住）" if hit else "漏网（尺坏）"))
        ok = ok and hit

    sc = gaussian_scale("3")
    hit = abs(sc["var_over_bound"] - 1) > mp.mpf("1e-12") and sc["crit_inconsistency"] != 0
    print("M3 宣称尺度族达到界：Var/界=%s（≠1）且等号条件残差 %s（≠0）⇒ %s"
          % (mp.nstr(sc["var_over_bound"], 12), mp.nstr(sc["crit_inconsistency"], 10),
             "响（两通道都判不可及）" if hit else "漏网（尺坏）"))
    ok = ok and hit

    loc = gaussian_location("5/2", "-4/9")
    good = (abs(loc["var_minus_bound"]) == 0 and abs(loc["i_score"]) == 0
            and location_criterion("5/2", "-4/9") == 0)
    print("P1 正例 位置族 Var-界=%s、I 通道残差=%s、等号条件最大残差=%s ⇒ %s"
          % (mp.nstr(loc["var_minus_bound"], 6), mp.nstr(loc["i_score"], 6),
             mp.nstr(location_criterion("5/2", "-4/9"), 6),
             "不误伤" if good else "误伤（尺过紧）"))
    ok = ok and good

    b = binomial_pair(5, 2, 5)
    good = (b["norm"] == 0 and b["e_score"] == 0 and b["i_direct"] == 0
            and abs(b["channel_gap"]) < TOL_CHANNEL)
    print("P2 正例 二项三子残差 %s/%s/%s、两通道差 %s ⇒ %s"
          % (mp.nstr(b["norm"], 4), mp.nstr(b["e_score"], 4), mp.nstr(b["i_direct"], 4),
             mp.nstr(b["channel_gap"], 6), "不误伤" if good else "误伤（尺过紧）"))
    ok = ok and good

    print("=== 自检汇总：%s（变异体 4 枚须全响、正例 2 枚须不误伤）==="
          % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    t0 = time.time()
    print("=== OM-T-SC-0001 Cramér–Rao 不等式 L2 检验（第 13 批）===")
    print("dps=%d；精确通道要求残差恒 0（TOL_EXACT=%s），通道间比较容差 %s，求积比较容差 %s"
          % (DPS, TOL_EXACT, TOL_CHANNEL, TOL_QUAD))

    # ---- 判定 1：二项族两条通道 --------------------------------------------
    rows = []
    for m in (1, 2, 5, 7, 20):
        for (qn, qd) in ((2, 5), (1, 3), (7, 8)):
            rows.append((m, qn, qd, binomial_pair(m, qn, qd)))
    worst_exact = max(max(abs(b["norm"]), abs(b["e_score"]), abs(b["i_direct"])) for *_x, b in rows)
    worst_gap = max(abs(b["channel_gap"]) for *_x, b in rows)
    j1 = (worst_exact == TOL_EXACT) and (worst_gap < TOL_CHANNEL)
    sample = [r for r in rows if r[0] == 5 and (r[1], r[2]) == (2, 5)][0][3]
    print("[判定1a] 二项族 %d 组 (m,q)：精确有路子残差（归一化／E[score]／I 直接求和）最大 %s"
          % (len(rows), mp.nstr(worst_exact, 4)))
    print("[判定1b] 通道 B（A''(η)/(dq/dη)²）与通道 A 现值之差，最大 %s" % mp.nstr(worst_gap, 8))
    print("         样例 m=5,q=2/5：I_通道A=%s I_通道B=%s 目标 m/(q(1-q))=%s"
          % (mp.nstr(sample["i_direct_mp"], 12), mp.nstr(sample["i_channelB"], 12),
             mp.nstr(sample["i_target_mp"], 12)))
    print("[判定1] %s" % ("PASS（两通道在全部 %d 组上同值）" % len(rows) if j1 else "FAIL"))

    # ---- 判定 2：正规位置族 -------------------------------------------------
    locs = [gaussian_location(s, t) for s, t in (("5/2", "-4/9"), ("3", "1"))]
    worst2 = max(max(abs(g["i_score"]), abs(g["i_curv"]), abs(g["i_two_channel"]),
                     abs(g["e_score"]), abs(g["var_minus_bound"])) for g in locs)
    crit2 = max(location_criterion(s, t) for s, t in (("5/2", "-4/9"), ("3", "1")))
    j2 = (worst2 == TOL_EXACT) and (crit2 == 0)
    g0 = locs[0]
    print("[判定2a] N(θ,σ²)：I−1/σ² 两通道残差 %s／%s，两通道互差 %s，E[score]=%s"
          % (mp.nstr(g0["i_score"], 6), mp.nstr(g0["i_curv"], 6),
             mp.nstr(g0["i_two_channel"], 6), mp.nstr(g0["e_score"], 6)))
    print("[判定2b] Var(T)-界（T=x）=%s；I 现值 %s；等号条件系数 a=score/(x-θ)=%s（应与 I 同值）"
          % (mp.nstr(g0["var_minus_bound"], 6), mp.nstr(g0["i_value"], 10), mp.nstr(g0["crit_a"], 10)))
    print("[判定2c] 两组 (σ,θ) 五路残差最大 %s；等号条件可解性最大残差 %s ⇒ 判「可及」"
          % (mp.nstr(worst2, 4), mp.nstr(crit2, 4)))
    print("[判定2] %s" % ("PASS（界被达到，且两条独立通道都这么说）" if j2 else "FAIL"))

    # ---- 判定 3：正规尺度族（界不被达到）----------------------------------
    sc = gaussian_scale("3")
    j3a = (abs(sc["i_score"]) == 0 and abs(sc["i_curv"]) == 0
           and abs(sc["i_two_channel"]) == 0 and abs(sc["unbiased"]) == 0)
    j3b = (abs(sc["crit_inconsistency"]) > 0) and (sc["var_minus_bound"] > 0)
    j3 = j3a and j3b
    print("[判定3a] 尺度族 I(σ)=2/σ²：两通道残差 %s／%s，互差 %s；T=sqrt(π/2)|x| 的无偏残差 %s"
          % (mp.nstr(sc["i_score"], 6), mp.nstr(sc["i_curv"], 6),
             mp.nstr(sc["i_two_channel"], 6), mp.nstr(sc["unbiased"], 6)))
    print("[判定3b] Var(T)=%s 界=%s ⇒ Var/界=%s，超出 %s%%；等号条件残差 %s（采样对 x=%d,x=%d）≠0"
          % (mp.nstr(sc["var_t"], 10), mp.nstr(sc["bound"], 10), mp.nstr(sc["var_over_bound"], 12),
             mp.nstr((sc["var_over_bound"] - 1) * 100, 8), mp.nstr(sc["crit_inconsistency"], 10),
             sc["crit_pair"][0], sc["crit_pair"][1]))
    print("[判定3] %s" % ("PASS（「界不被达到」被两条独立通道同时说中）" if j3 else "FAIL"))

    # ---- 判定 4：mpmath 独立求积 ------------------------------------------
    nm = numeric_location("5/2", "-4/9")
    d_i = abs(nm["i"] - nm["target"])
    d_v = abs(nm["var"] - mp.mpf("5") / 2 * (mp.mpf("5") / 2))
    d_e = abs(nm["e_score"])
    j4 = (max(d_i, d_v, d_e) < TOL_QUAD) and (nm["tail"] < mp.mpf("1e-100"))
    print("[判定4] mpmath 50 dps 求积（截断 L=40σ=%.1fσ，尾概率上界 %s）：|I-1/σ²|=%s |Var-σ²|=%s |E[score]|=%s ⇒ %s"
          % (40, mp.nstr(nm["tail"], 6), mp.nstr(d_i, 8), mp.nstr(d_v, 8), mp.nstr(d_e, 8),
             "PASS" if j4 else "FAIL"))
    print("        分辨率账单：差值以 %d dps 打印，小于 %s 的差印成 0.0，所以判定4 的 0.0 读作「低于本精度下限」而非「严格为 0」；"
          "同一条目里 |E[score]|=%s 非零，说明求积通道确在算数、不是恒零的坏针。"
          % (DPS, mp.nstr(mp.mpf(10) ** (-(DPS - 5)), 6), mp.nstr(d_e, 8)))
    print("        通道性质：判定2/判定3 的积分残差来自 sympy 的**解析闭式**（可恰为 0），判定4 才是同批积分的**数值**复算；"
          "把前者当数值证据时须记住它出自符号机（红线一），两面同意才计一次数。")

    n_pass = sum([j1, j2, j3, j4])
    ok = (n_pass == 4)
    print("=== 判定汇总：判定 1-4 中 PASS %d／FAIL %d（判定1=%s 判定2=%s 判定3=%s 判定4=%s）｜ 耗时 %.1fs ==="
          % (n_pass, 4 - n_pass, j1, j2, j3, j4, time.time() - t0))
    print("注（红线一、红线八）：本面只核对脚本内写下的族与采样点，不证明定理，"
          "也不构成对任何开放问题的进展；定理地位来自文献，不由本面授予。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
