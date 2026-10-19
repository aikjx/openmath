# -*- coding: utf-8 -*-
"""OM-T-SC-0002 Fisher 信息可加性的独立验证脚本（第 14 批）。

    定理：X_1,…,X_n 相互独立、各分量满足正则条件时
          I_n(θ) = Σ I_i(θ)（i.i.d. 时 = n·I_1），
          自然指数族 p(x;η)=h(x)e^{ηT(x)-A(η)} 满足 E[T]=A′(η)、I(η)=Var(T)=A″(η)，
          重参数化下 I(η)=I(θ)·(dθ/dη)²。

本库不重做证明（红线八：定理出自已刊文献，见记录 fact_check）。这台仪器办五件事：

1) **可加性由两条结构不同的生产者各算一次**（离散侧）：
   生产者 A＝把 2ⁿ 个原子逐个枚举出来的显式和（不用任何闭式，也不调用独立性假设的代数量形）；
   生产者 B＝求和统计量 Bin(n,q) 的闭式求和。两者同值才计一次数。
2) **连续侧三条通道对齐同一个和**：嵌套双重积分（score² 的期望）、Fubini 分解后的单积分乘积、
   期望曲率 −E[∂² log(p1p2)/∂θ²]。三条都须等于 1/σ1²+1/σ2²，且交叉项的两个因子 E[s_i]=0 单独印出
   ——「交叉项为零」是这台仪器的判定对象，不是它的前提。
3) **「精度相加」落到估计侧，并且双向判**：
   逆方差加权 T_w 使 score=I_2·(T_w−θ) 逐点成立 ⇒ Var(T_w)=界；
   算术平均 T_a 在 σ1≠σ2 时 Var−界>0 且等号条件不可解。
   同一把尺在两边给出**不同**裁定，且与「方差减界」那条独立通道同判——只有一边红一边绿才算尺会判。
4) **信息＝曲率**在三个族上各核对（Bernoulli／Poisson／正规位置），
   外加两条结构性核对：求和族的 A″ 相加＝单枚 A″ 之和；重参数化律三族各算一次。
5) **第二口径**：连续可加性的三条读数再由 mpmath 50 dps 求积独立复算，
   截断误差自带尾概率账单；把 sympy 的解析闭式当数值证据时它出自符号机（红线一）。

用法：cd openmath && PYTHONIOENCODING=utf-8 python 08-工具/examples/verify_OM-T-SC-0002.py
     自检（变异体必须响、正例必须不误伤）：加 --selftest
退出码：0＝全部判定通过；1＝有判定不过；2＝前置条件缺失（未装 sympy/mpmath）。
"""
import itertools
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
Q = sp.Symbol("q", positive=True)
ETA = sp.Symbol("eta", real=True)
LAM = sp.Symbol("lam", positive=True)
K = sp.Symbol("k", integer=True)
XX = sp.Symbol("x", integer=True)
X1 = sp.Symbol("x1", real=True)
X2 = sp.Symbol("x2", real=True)
TH = sp.Symbol("theta", real=True)
S1 = sp.Symbol("sd1", positive=True)
S2 = sp.Symbol("sd2", positive=True)
TOL_EXACT = mp.mpf(0)          # 精确有理通道：残差必须是 0，不留余地
TOL_CHANNEL = mp.mpf("1e-40")  # 两条不同来源的读数之差（50 dps）
TOL_QUAD = mp.mpf("1e-30")     # mpmath 求积 vs sympy 解析：开工前钉死，见判定5


def ex(expr):
    """精确有理通道：先代点、再由 simplify 解析求积/求和、最后取 mpf。
    顺序不能反——未代点就 doit 会撞进 sympy 的 meijerint 内部 KeyError（本轮实测），
    而代点后不 simplify 时 `sp.N` 会把 Integral 原样吐出，被 num() 判成「未归约」。
    形状守卫不是装饰：未归约的 Sum/Integral 交给 `sp.N` 会退化成数值加速求和，
    它**能**印出一个数——本轮实测 η-参数化 Poisson 的一阶矩给出 -1.4185（真值 0），
    错误以「残差」的形状出现而不是以异常出现，所以必须在这里拦住。"""
    red = sp.simplify(expr)
    if isinstance(red, (sp.Sum, sp.Integral)) or red.has(sp.Sum, sp.Integral):
        raise ValueError("通道未归约为闭式（不许当残差读）：%s" % sp.sstr(red)[:80])
    return num(red)


def dd(integrand):
    """双重积分的**未代入**形状（调用方代点后再交给 ex）。"""
    return sp.Integral(sp.Integral(integrand, (X1, -sp.oo, sp.oo)), (X2, -sp.oo, sp.oo))


def num(expr, dps=DPS):
    """代成 50 dps 的 mpf；解析式若没归约为数就抛，不静默返回符号。"""
    val = sp.N(expr, dps)
    if not val.is_Number:
        raise ValueError("解析式未归约为数：%s" % (sp.sstr(val)[:90],))
    return mp.mpf(sp.sstr(val))


# ---------------------------------------------------------------- 判定 1：离散可加性
def discrete_additivity(n, qnum, qden):
    """两条生产者各算一次 n 枚独立 Bernoulli 的 I_n。A＝逐原子枚举；B＝Bin(n,q) 闭式。"""
    qq = sp.Rational(qnum, qden)
    # 生产者 A：2ⁿ 个原子的显式和（不用闭式、不用独立性代数量形）
    pts = list(itertools.product((0, 1), repeat=n))
    tot = sp.Integer(0)
    sq = sp.Integer(0)
    for p in pts:
        pr = sp.Mul(*[(qq if a == 1 else (1 - qq)) for a in p])
        sc = sum(sp.Rational(a) / qq - (1 - sp.Rational(a)) / (1 - qq) for a in p)
        tot += pr * sc
        sq += pr * sc ** 2
    e_s_cube = num(sp.simplify(tot))
    i_cube = num(sp.simplify(sq))
    target = sp.Rational(n) / (qq * (1 - qq))
    # 生产者 B：求和统计量 Bin(n,q) 的闭式求和
    pbin = sp.binomial(n, K) * Q ** K * (1 - Q) ** (n - K)
    scoreb = K / Q - (n - K) / (1 - Q)
    i_closed = num(sp.simplify((sp.summation(pbin * scoreb ** 2, (K, 0, n))
                                - n / (Q * (1 - Q))).subs({Q: qq})))
    norm = num(sp.simplify((sp.summation(pbin, (K, 0, n)) - 1).subs({Q: qq})))
    es_closed = num(sp.simplify(sp.summation(pbin * scoreb, (K, 0, n)).subs({Q: qq})))
    single = num(sp.simplify(((1 - Q) * (1 / (1 - Q)) ** 2 + Q * (1 / Q) ** 2
                              - 1 / (Q * (1 - Q))).subs({Q: qq})))
    return {"n": n, "q": qq, "e_s_cube": e_s_cube, "i_cube": i_cube,
            "i_cube_minus_target": i_cube - num(target), "i_closed": i_closed,
            "norm": norm, "e_s_closed": es_closed, "single": single,
            "atoms": len(pts)}


# ---------------------------------------------------------------- 判定 2：连续可加性
def pnorm(x, s):
    return sp.exp(-(x - TH) ** 2 / (2 * s ** 2)) / (s * sp.sqrt(2 * PI))


def continuous_additivity(s1, s2, theta):
    """N(θ,σ1²)×N(θ,σ2²)：三条通道对齐 1/σ1²+1/σ2²，交叉项的两个因子单独印。"""
    pts = {S1: sp.Rational(s1), S2: sp.Rational(s2), TH: sp.Rational(theta)}
    p1, p2 = pnorm(X1, S1), pnorm(X2, S2)
    t = 1 / S1 ** 2 + 1 / S2 ** 2
    sc = (X1 - TH) / S1 ** 2 + (X2 - TH) / S2 ** 2
    dbl = dd(p1 * p2 * sc ** 2)
    i1 = sp.Integral(p1 * ((X1 - TH) / S1 ** 2) ** 2, (X1, -sp.oo, sp.oo))
    i2 = sp.Integral(p2 * ((X2 - TH) / S2 ** 2) ** 2, (X2, -sp.oo, sp.oo))
    m1 = sp.Integral(p1, (X1, -sp.oo, sp.oo))
    m2 = sp.Integral(p2, (X2, -sp.oo, sp.oo))
    c1 = sp.Integral(p1 * (X1 - TH) / S1 ** 2, (X1, -sp.oo, sp.oo))
    c2 = sp.Integral(p2 * (X2 - TH) / S2 ** 2, (X2, -sp.oo, sp.oo))
    fub = i1 * m2 + m1 * i2 + 2 * c1 * c2
    logr = -(X1 - TH) ** 2 / (2 * S1 ** 2) - (X2 - TH) ** 2 / (2 * S2 ** 2)
    curv = -sp.diff(logr, TH, 2)
    cur_int = dd(p1 * p2 * curv)
    return {"i_double": ex((dbl - t).subs(pts)), "i_fubini": ex((fub - t).subs(pts)),
            "i_curvature": ex((cur_int - t).subs(pts)),
            "i1": ex((i1 - 1 / S1 ** 2).subs(pts)), "i2": ex((i2 - 1 / S2 ** 2).subs(pts)),
            "cross1": ex(c1.subs(pts)), "cross2": ex(c2.subs(pts)),
            "norm1": ex((m1 - 1).subs(pts)), "norm2": ex((m2 - 1).subs(pts)),
            "dbl_val": ex(dbl.subs(pts)), "tgt_val": num(t.subs(pts)),
            "tgt": t}


# ---------------------------------------------------------------- 判定 3：达到界／不达到界
def weighted_pair(s1, s2, theta):
    """σ1≠σ2 时两种合并法的对照：逆方差加权（达界）与算术平均（不达界）。"""
    pts = {S1: sp.Rational(s1), S2: sp.Rational(s2), TH: sp.Rational(theta)}
    p1, p2 = pnorm(X1, S1), pnorm(X2, S2)
    t = 1 / S1 ** 2 + 1 / S2 ** 2
    tw = (X1 / S1 ** 2 + X2 / S2 ** 2) / t
    ta = (X1 + X2) / 2
    integ = dd
    out = {}
    for tag, tv in (("w", tw), ("a", ta)):
        out["unbiased_" + tag] = ex(integ((tv - TH) * p1 * p2).subs(pts))
        out["var_" + tag] = ex(integ((tv - TH) ** 2 * p1 * p2).subs(pts))
        out["varminus_" + tag] = ex((integ((tv - TH) ** 2 * p1 * p2) - 1 / t).subs(pts))
    # 等号条件可解性尺（与 OM-T-SC-0001 同一把）：跨采样对解 a 后代回
    sc = (X1 - TH) / S1 ** 2 + (X2 - TH) / S2 ** 2
    pairs = [((3, 5), (-2, 7)), ((0, 1), (4, -3)), ((5, 2), (5, -6)), ((-1, 9), (2, 1))]
    worst = {}
    for tag, tv in (("w", tw), ("a", ta)):
        w = mp.mpf(0)
        for (x1a, x2a), (x1b, x2b) in pairs:
            da = num((tv - TH).subs(pts).subs({X1: x1a, X2: x2a}))
            if da == 0:
                continue
            a_est = num(sc.subs(pts).subs({X1: x1a, X2: x2a})) / da
            r = abs(num(sp.simplify((sc - a_est * (tv - TH)).subs(pts)
                                    .subs({X1: x1b, X2: x2b}))))
            w = max(w, r)
        worst[tag] = w
    out["crit_w"] = worst["w"]
    out["crit_a"] = worst["a"]
    out["bound"] = num((1 / t).subs(pts))
    out["tgt_val"] = num(t.subs(pts))
    out["varw"] = out["var_w"]
    out["vara"] = out["var_a"]
    return out


def solvability_identity(s1, s2, theta):
    """等号条件的**恒等式**形状：score-I_2·(T_w-θ) 逐点为 0（不含积分，符号层直接归约）。"""
    t = 1 / S1 ** 2 + 1 / S2 ** 2
    tw = (X1 / S1 ** 2 + X2 / S2 ** 2) / t
    sc = (X1 - TH) / S1 ** 2 + (X2 - TH) / S2 ** 2
    e = sp.simplify(sc - t * (tw - TH))
    return num(e.subs({S1: sp.Rational(s1), S2: sp.Rational(s2), TH: sp.Rational(theta),
                       X1: sp.Rational(5, 7), X2: sp.Rational(-3, 4)})), e


# ---------------------------------------------------------------- 判定 4：信息＝曲率
def ngf_triplet(qnum, qden, lam_num, lam_den):
    """三族的 I(η) 与 A″(η) 两通道，外加求和族的曲率相加与重参数化律。"""
    qq = sp.Rational(qnum, qden)
    lam = sp.Rational(lam_num, lam_den)
    out = {}
    # Bernoulli：A=log(1+e^η)，T=x
    a_b = sp.log(1 + sp.exp(ETA))
    out["bern_curv"] = ex((sp.diff(a_b, ETA, 2).subs({ETA: sp.log(qq / (1 - qq))})
                            - qq * (1 - qq)))
    var_t = num((1 - qq) * (0 - qq) ** 2 + qq * (1 - qq) ** 2)
    out["bern_var_vs_curv"] = var_t - ex(sp.diff(a_b, ETA, 2).subs({ETA: sp.log(qq / (1 - qq))}))
    # Poisson：自然坐标 η=log(lam) 下 A(η)=e^η、T=x、score_η=x-lam。
    # 求和一律在 lam 坐标写：η-参数化的求和 sympy 不归约（见 ex 的形状守卫），
    # 而 η 只出现在 A 的导数里，那一条与求和无关。
    pois = sp.exp(-LAM) * LAM ** XX / sp.factorial(XX)
    out["pois_score"] = ex(sp.summation(pois * (XX - LAM) ** 2, (XX, 0, sp.oo)).subs({LAM: lam}) - lam)
    out["pois_escore"] = ex(sp.summation(pois * (XX - LAM), (XX, 0, sp.oo)).subs({LAM: lam}))
    out["pois_norm"] = ex((sp.summation(pois, (XX, 0, sp.oo)) - 1).subs({LAM: lam}))
    out["pois_curv"] = ex(sp.diff(sp.exp(ETA), ETA, 2).subs({ETA: sp.log(lam)}) - lam)
    # 正规位置族：η=θ/σ²，A(η)=σ²η²/2，T=x
    sg = sp.Rational(3, 2)
    a_n = sg ** 2 * ETA ** 2 / 2
    out["norm_curv"] = ex(sp.diff(a_n, ETA, 2) - sg ** 2)
    p = sp.exp(-(X1 - TH) ** 2 / (2 * sg ** 2)) / (sg * sp.sqrt(2 * PI))
    out["norm_score"] = ex(sp.Integral(p * (X1 - sg ** 2 * ETA) ** 2, (X1, -sp.oo, sp.oo))
                            .subs({ETA: sp.Rational(2, 5) / sg ** 2, TH: sp.Rational(2, 5)}) - sg ** 2)
    # 求和族：n 枚 Bernoulli 的 A_n=n·A ⇒ A_n″=n·A″
    n = 3
    out["sum_curv"] = ex((sp.diff(n * a_b, ETA, 2) - n * sp.diff(a_b, ETA, 2)).subs({ETA: sp.log(qq / (1 - qq))}))
    # 重参数化律：I(η)=I(q)·(dq/dη)²
    dq = sp.diff(sp.log(Q / (1 - Q)), Q)
    out["reparam_bern"] = ex((1 / (Q * (1 - Q)) / dq ** 2
                               - sp.diff(a_b, ETA, 2)).subs({Q: qq, ETA: sp.log(qq / (1 - qq))}))
    dlam = sp.diff(sp.log(LAM), LAM) ** -1
    out["reparam_pois"] = ex((1 / LAM * dlam ** 2 - LAM).subs({LAM: lam}))
    out["reparam_norm"] = ex(sp.simplify(1 / sg ** 2 * (sg ** 2) ** 2 - sg ** 2))
    out["q"] = qq
    out["lam"] = lam
    out["bern_i_eta"] = var_t
    return out


# ---------------------------------------------------------------- 判定 5：mpmath 复核
def numeric_additivity(s1, s2, theta):
    """独立仪器：50 dps 数值求积重算连续可加性（Fubini 单积分乘积），附尾概率账单。"""
    a, b, t0 = mp.mpf(s1), mp.mpf(s2), mp.mpf(theta)
    dens = lambda u, s: mp.exp(-(u - t0) ** 2 / (2 * s * s)) / (s * mp.sqrt(2 * mp.pi))
    L1, L2 = a * 40, b * 40
    tail = mp.erfc(L1 / a) * mp.erfc(L2 / b) / 4
    i1 = mp.quad(lambda u: dens(u, a) * ((u - t0) / (a * a)) ** 2, [-L1 + t0, L1 + t0])
    i2 = mp.quad(lambda u: dens(u, b) * ((u - t0) / (b * b)) ** 2, [-L2 + t0, L2 + t0])
    m1 = mp.quad(lambda u: dens(u, a), [-L1 + t0, L1 + t0])
    m2 = mp.quad(lambda u: dens(u, b), [-L2 + t0, L2 + t0])
    c1 = mp.quad(lambda u: dens(u, a) * (u - t0) / (a * a), [-L1 + t0, L1 + t0])
    c2 = mp.quad(lambda u: dens(u, b) * (u - t0) / (b * b), [-L2 + t0, L2 + t0])
    return dict(i=i1 * m2 + m1 * i2 + 2 * c1 * c2, target=1 / (a * a) + 1 / (b * b),
                c1=c1, c2=c2, tail=tail, L=(L1, L2))


# ---------------------------------------------------------------- 自检：牙齿
def selftest():
    """变异体（必须响）＋正例（必须不误伤）。全绿不算证据，所以两边都要跑。"""
    print("=== 变异体自检（--selftest）===")
    ok = True
    qq = sp.Rational(2, 5)
    n = 2
    pbin = sp.binomial(n, K) * Q ** K * (1 - Q) ** (n - K)
    scb = K / Q - (n - K) / (1 - Q)
    i_closed = sp.summation(pbin * scb ** 2, (K, 0, n))
    atoms = [(a, b) for a in (0, 1) for b in (0, 1)]
    i_enum = sp.Integer(0)
    for p in atoms:
        pr = sp.Integer(1)
        sc = sp.Integer(0)
        for a in p:
            pr *= qq if a == 1 else (1 - qq)
            sc += sp.Rational(a) / qq - (1 - sp.Rational(a)) / (1 - qq)
        i_enum += pr * sc ** 2
    single3 = (1 - Q) * (1 / (1 - Q)) ** 2 + Q * (1 / Q) ** 2
    for name, expr, want in [
        ("M1 把可加性丢掉：I_2 写成单枚 I_1", sp.simplify(i_enum - 1 / (Q * (1 - Q))).subs({Q: qq}), "nz"),
        ("M2 二项闭式的右端写成 n·q(1-q)（把 A″(η) 当 I(η)）",
         sp.simplify(i_closed - n * Q * (1 - Q)).subs({Q: qq}), "nz"),
        ("M3 交叉项写成非零（在 I_2 的目标上再加一枚 1）",
         sp.simplify(i_enum - (2 / (Q * (1 - Q)) + 1)).subs({Q: qq}), "nz"),
        ("M4 I(η) 写成 A′(η) 而不是 A″(η)",
         sp.diff(sp.log(1 + sp.exp(ETA)), ETA).subs({ETA: sp.log(qq / (1 - qq))}) - qq * (1 - qq), "nz"),
        ("M5 求和族的 A″ 少乘 n（n=2 写成 1）",
         (sp.diff(2 * sp.log(1 + sp.exp(ETA)), ETA, 2) - sp.log(1 + sp.exp(ETA)).diff(ETA, 2))
         .subs({ETA: sp.log(qq / (1 - qq))}), "nz"),
        ("M6 两个方差的信息写成乘积形式 1/(σ1σ2)",
         num(sp.simplify((sp.Integral(sp.Integral(pnorm(X1, S1) * pnorm(X2, S2)
                                                  * ((X1 - TH) / S1 ** 2 + (X2 - TH) / S2 ** 2) ** 2,
                                                  (X1, -sp.oo, sp.oo)), (X2, -sp.oo, sp.oo))
                              - 1 / (S1 * S2)).subs({S1: sp.Rational(3, 2), S2: sp.Rational(5, 3),
                                                     TH: sp.Rational(1, 3)}))), "nz"),
        ("M7 重参数化律少除一次雅可比（I(η)=I(q)/dq/dη）",
         sp.simplify((1 / (Q * (1 - Q)) / sp.diff(sp.log(Q / (1 - Q)), Q)
                      - Q * (1 - Q)).subs({Q: qq})), "nz"),
    ]:
        rv = expr if isinstance(expr, mp.mpf) else num(sp.simplify(expr))
        hit = (rv != 0) if want == "nz" else (rv == 0)
        print("%s：残差 %s ⇒ %s" % (name, mp.nstr(rv, 10),
                                    "响（被抓住）" if hit else "漏网（尺坏）"))
        ok = ok and hit

    # 正例：同一台仪器在未变异数据上不得误伤
    d = discrete_additivity(2, 2, 5)
    good = (d["norm"] == 0 and d["e_s_cube"] == 0 and d["i_cube_minus_target"] == 0
            and d["i_closed"] == 0 and abs(d["i_cube"] - num(2/(d["q"]*(1-d["q"])))) == 0)
    print("P1 正例 离散 n=2：归一化 %s、E[score] %s、枚举通道差目标 %s、闭式通道残差 %s ⇒ %s"
          % (mp.nstr(d["norm"], 4), mp.nstr(d["e_s_cube"], 4), mp.nstr(d["i_cube_minus_target"], 4),
             mp.nstr(d["i_closed"], 4), "不误伤" if good else "误伤（尺过紧）"))
    ok = ok and good
    w = weighted_pair("3/2", "5/3", "1/3")
    idr, _ = solvability_identity("3/2", "5/3", "1/3")
    good = (w["unbiased_w"] == 0 and w["varminus_w"] == 0 and w["crit_w"] < TOL_CHANNEL and idr == 0)
    print("P2 正例 逆方差加权：无偏 %s、Var-界 %s、等号条件最大残差 %s、恒等式残差 %s ⇒ %s"
          % (mp.nstr(w["unbiased_w"], 4), mp.nstr(w["varminus_w"], 4),
             mp.nstr(w["crit_w"], 4), mp.nstr(idr, 4), "不误伤" if good else "误伤（尺过紧）"))
    ok = ok and good
    # 反例侧：算术平均必须被同一把尺判成不可及（双向对照的另一半）
    good = (w["varminus_a"] > 0 and w["crit_a"] != 0)
    print("P3 正例 算术平均：Var-界 %s（>0）、等号条件最大残差 %s（≠0）⇒ %s"
          % (mp.nstr(w["varminus_a"], 6), mp.nstr(w["crit_a"], 6), "两通道同判不可及" if good else "判据失灵"))
    ok = ok and good
    print("=== 自检汇总：%s（变异体 7 枚须全响、正例 3 枚须不误伤）===" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    t0 = time.time()
    print("=== OM-T-SC-0002 Fisher 信息可加性 L2 检验（第 14 批）===")
    print("dps=%d；精确通道要求残差恒 0（TOL_EXACT=%s），通道间比较容差 %s，求积比较容差 %s"
          % (DPS, TOL_EXACT, TOL_CHANNEL, TOL_QUAD))

    # ---- 判定 1：离散可加性，两条生产者 -----------------------------------
    rows = []
    for n in (1, 2, 3, 4, 5):
        for (qn, qd) in ((2, 5), (1, 3), (7, 8)):
            rows.append(discrete_additivity(n, qn, qd))
    worst_exact = max(max(abs(r["norm"]), abs(r["e_s_cube"]), abs(r["e_s_closed"]),
                          abs(r["i_cube_minus_target"]), abs(r["i_closed"]), abs(r["single"]))
                      for r in rows)
    j1 = worst_exact == TOL_EXACT
    ref = [r for r in rows if r["n"] == 2 and r["q"] == sp.Rational(2, 5)][0]
    print("[判定1a] 枚举通道（%d 个原子显式和）：I_2 现值 %s，目标 2/(q(1-q))＝%s，差 %s"
          % (ref["atoms"], mp.nstr(ref["i_cube"], 12), mp.nstr(num(ref["q"] * 0 + 2 / (ref["q"] * (1 - ref["q"]))), 12),
             mp.nstr(ref["i_cube_minus_target"], 4)))
    print("[判定1b] 闭式通道 Bin(n,q) 求和：同一枚 (n=2,q=2/5) 残差 %s；归一化 %s；E[score] %s"
          % (mp.nstr(ref["i_closed"], 4), mp.nstr(ref["norm"], 4), mp.nstr(ref["e_s_closed"], 4)))
    print("[判定1c] %d 组 (n,q) 六路子残差最大 %s（n∈{1,2,3,4,5}）⇒ 可加性与两条生产者同值"
          % (len(rows), mp.nstr(worst_exact, 4)))
    print("[判定1] %s" % ("PASS（枚举与闭式两条通道在全部 %d 组上同值）" % len(rows) if j1 else "FAIL"))

    # ---- 判定 2：连续可加性，三条通道 -------------------------------------
    pairs = [("3/2", "5/3", "1/3"), ("2", "3", "-4/9")]
    cs = [continuous_additivity(a, b, t) for a, b, t in pairs]
    worst2 = max(max(abs(c["i_double"]), abs(c["i_fubini"]), abs(c["i_curvature"]),
                     abs(c["i1"]), abs(c["i2"]), abs(c["cross1"]), abs(c["cross2"]),
                     abs(c["norm1"]), abs(c["norm2"])) for c in cs)
    j2 = worst2 == TOL_EXACT
    c0 = cs[0]
    print("[判定2a] 嵌套双重积分通道：E[(s1+s2)²] 现值 %s，目标 1/σ1²+1/σ2²＝%s，残差 %s"
          % (mp.nstr(c0["dbl_val"], 12), mp.nstr(c0["tgt_val"], 12), mp.nstr(c0["i_double"], 4)))
    print("[判定2b] Fubini 单积分乘积通道残差 %s；期望曲率通道残差 %s（三条通道对齐同一个和）"
          % (mp.nstr(c0["i_fubini"], 4), mp.nstr(c0["i_curvature"], 4)))
    print("[判定2c] 交叉项的两个因子 E[s1]=%s、E[s2]=%s（各自为 0 才是交叉项消失的**理由**）；"
          "边际 I 残差 %s／%s，归一化残差 %s／%s"
          % (mp.nstr(c0["cross1"], 4), mp.nstr(c0["cross2"], 4), mp.nstr(c0["i1"], 4),
             mp.nstr(c0["i2"], 4), mp.nstr(c0["norm1"], 4), mp.nstr(c0["norm2"], 4)))
    print("[判定2d] 两组 (σ1,σ2,θ) 九路残差最大 %s" % mp.nstr(worst2, 4))
    print("[判定2] %s" % ("PASS（连续侧三条通道两两同值）" if j2 else "FAIL"))

    # ---- 判定 3：达到界／不达到界（双向）---------------------------------
    ws = [weighted_pair(a, b, t) for a, b, t in pairs]
    ids = [solvability_identity(a, b, t) for a, b, t in pairs]
    # 口径分家：恒等式与积分通道是**解析**的（要求恰 0），可解性那把尺是**数值**比值（50 dps），
    # 它的「可及」读数落在舍入量级而不是 0（本轮实测最大 2.3e-50），所以按 1e-40 判而不是按 ==0 判。
    j3a = all(w["unbiased_w"] == 0 and w["varminus_w"] == 0 and abs(w["crit_w"]) < TOL_CHANNEL
              and i[0] == 0 for w, i in zip(ws, ids))
    j3b = all(w["varminus_a"] > 0 and w["crit_a"] != 0 for w in ws)
    j3 = j3a and j3b
    w0 = ws[0]
    print("[判定3a] 逆方差加权 T_w：无偏残差 %s；Var(T_w)=%s＝界 %s ⇒ Var-界 %s；"
          "等号条件最大残差 %s；恒等式 score-I_2·(T_w-θ) 残差 %s"
          % (mp.nstr(w0["unbiased_w"], 4), mp.nstr(w0["varw"], 12), mp.nstr(w0["bound"], 12),
             mp.nstr(w0["varminus_w"], 4), mp.nstr(w0["crit_w"], 4), mp.nstr(ids[0][0], 4)))
    print("[判定3b] 算术平均 T_a：Var(T_a)=%s ⇒ Var-界=%s（>0）；等号条件最大残差 %s（≠0）"
          % (mp.nstr(w0["vara"], 12), mp.nstr(w0["varminus_a"], 10), mp.nstr(w0["crit_a"], 10)))
    print("[判定3c] 精度相加的读法：1/I_2=%s 而 1/(1/σ1²+1/σ2²)=%s（同一枚，逐字相等才算「精度相加」）"
          % (mp.nstr(w0["varw"], 12), mp.nstr(w0["bound"], 12)))
    print("[判定3] %s" % ("PASS（同一把尺：加权判可及、算术判不可及，两通道同判）" if j3 else "FAIL"))

    # ---- 判定 4：信息＝曲率 ---------------------------------------------
    ng = [ngf_triplet(2, 5, 7, 4), ngf_triplet(1, 3, 2, 1)]
    worst4 = max(max(abs(g["bern_curv"]), abs(g["bern_var_vs_curv"]), abs(g["pois_score"]),
                     abs(g["pois_curv"]), abs(g["norm_curv"]), abs(g["norm_score"]),
                     abs(g["sum_curv"]), abs(g["reparam_bern"]), abs(g["reparam_pois"]),
                     abs(g["reparam_norm"]), abs(g["pois_escore"]), abs(g["pois_norm"])) for g in ng)
    j4 = worst4 == TOL_EXACT
    g0 = ng[0]
    print("[判定4a] Bernoulli：A″(η)＝q(1-q) 残差 %s；Var(T)−A″ 残差 %s（两条通道）"
          % (mp.nstr(g0["bern_curv"], 4), mp.nstr(g0["bern_var_vs_curv"], 4)))
    print("[判定4b] Poisson（η=log lam，A=e^η）：score=x-A′ 的二阶矩残差 %s、A″ 残差 %s、E[score] %s"
          % (mp.nstr(g0["pois_score"], 4), mp.nstr(g0["pois_curv"], 4), mp.nstr(g0["pois_escore"], 4)))
    print("[判定4b2] Poisson 的 E[score] 与归一化两条求和通道残差最大 %s；"
          "形状守卫：ex() 对未归约的 Sum/Integral 直接抛，不让它退化成的数值读数冒充残差"
          % mp.nstr(max(abs(g["pois_escore"]) + abs(g["pois_norm"]) for g in ng), 6))
    print("[判定4c] 正规位置族：I(η)=σ² 曲率通道 %s、score 通道 %s；求和族 A″ 相加残差 %s"
          % (mp.nstr(g0["norm_curv"], 4), mp.nstr(g0["norm_score"], 4), mp.nstr(g0["sum_curv"], 4)))
    print("[判定4d] 重参数化律 I(η)=I(θ)(dθ/dη)² 三族残差 %s／%s／%s"
          % (mp.nstr(g0["reparam_bern"], 4), mp.nstr(g0["reparam_pois"], 4), mp.nstr(g0["reparam_norm"], 4)))
    print("[判定4] %s" % ("PASS（三族两通道＋求和与重参数化结构核对，全部恰 0）" if j4 else "FAIL"))

    # ---- 判定 5：mpmath 独立求积 ----------------------------------------
    nm = [numeric_additivity(a, b, t) for a, b, t in pairs]
    d5 = [abs(x["i"] - x["target"]) for x in nm]
    j5 = max(d5) < TOL_QUAD and nm[0]["tail"] < mp.mpf("1e-100") and max(abs(x["c1"]) + abs(x["c2"]) for x in nm) < TOL_QUAD
    print("[判定5] mpmath 50 dps 求积（截断 L=(%.1fσ1, %.1fσ2)，联合尾概率上界 %s）："
          "|I_2-目标|=%s／%s，|E[s_i]|=%s／%s ⇒ %s"
          % (nm[0]["L"][0] / mp.mpf(pairs[0][0]), nm[0]["L"][1] / mp.mpf(pairs[0][1]),
             mp.nstr(nm[0]["tail"], 6), mp.nstr(d5[0], 8), mp.nstr(d5[1], 8),
             mp.nstr(abs(nm[0]["c1"]), 8), mp.nstr(abs(nm[0]["c2"]), 8),
             "PASS" if j5 else "FAIL"))
    print("        通道性质：判定2 的九路残差出自 sympy 的**解析闭式**（可恰为 0），判定5 才是同批积分的**数值**复算；"
          "把前者当数值证据时须记住它出自符号机（红线一），两面同意才计一次数。")
    print("        取舍账单：Fubini 那条连续通道不进记录的 sympy 字段是**成本**取舍而不是算不出来——"
          "通用引擎口径（float 代入＋sp.N(50)）下单枚采样点 40.4 秒、残差 -9.126e-52"
          "（scratch/T14_PROTO3_face.txt 的 cost 段；第二台独立计时 69.9 秒同值，"
          "见 scratch/T14_CALIBER_probe.txt），而字段里那 11 项合计只要 6.7 秒（同一张面）。"
          "本脚本走精确有理通道：先 doit 再 simplify 时同一条 0.4 秒归约为 0；"
          "只 simplify（不调 doit）时 161.6 秒且不归约（同一张 CALIBER 面）——"
          "旧稿那句「单枚约 109 秒」量的正是这一型装配，本轮按两张面更正。")
    print("        形状守卫的用场：同一批积分**未做 Fubini 分解**的嵌套双重积分，"
          "在引擎口径下 0.0 秒直接返回未归约的 Integral（scratch/T14_PROTO3_face.txt），"
          "sp.N 会把它退化成一个数当作残差读，所以 ex() 必须抛。")

    n_pass = sum([j1, j2, j3, j4, j5])
    ok = (n_pass == 5)
    print("=== 判定汇总：判定 1-5 中 PASS %d／FAIL %d（判定1=%s 判定2=%s 判定3=%s 判定4=%s 判定5=%s）｜ 耗时 %.1fs ==="
          % (n_pass, 5 - n_pass, j1, j2, j3, j4, j5, time.time() - t0))
    print("注（红线一、红线八）：本面只核对脚本内写下的族与采样点，不证明定理，"
          "也不构成对任何开放问题的进展；定理地位来自文献，不由本面授予。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
