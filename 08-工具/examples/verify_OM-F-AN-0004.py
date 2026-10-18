# -*- coding: utf-8 -*-
"""OM-F-AN-0004 狄利克雷 L-函数函数方程的独立验证脚本（第 10 批）。

    Λ(s,χ) := (q/π)^{(s+a)/2} · Γ((s+a)/2) · L(s,χ),   a = (1 − χ(−1))/2
    函数方程：Λ(s,χ) = ε(χ) · Λ(1−s,χ̄),  |ε(χ)| = 1

这台仪器**不许把根数的写法当先验**：文献里 ε(χ) 有 τ(χ)/(i^a√q)、i^a τ(χ)/√q、
τ(χ̄)/(i^a√q) 等并存的约定，抄哪一种都可能把整条方程写成反号或共轭错。
所以第 1 步是**测量**——在若干采样点上算 ε_meas = Λ(s,χ)/Λ(1−s,χ̄)，
先证它随 s 恒定（这才是「存在一条函数方程」这件事的证据），再拿测得的常数
与候选约定逐一比对，由比对结果决定 YAML 里写哪一句。

L(s,χ) 的解析延拓走 Hurwitz 路线：L(s,χ) = q^{-s} Σ_{r=1..q} χ(r) ζ_H(s, r/q)。
这条路线自己就是本轮的陷阱：χ 为主特征时 ζ_H 在 s=1 的极点不会被抵消，
所以采样只取**非主特征**（本轮三个特征全非主），主特征的情形登记进 caveat 不测。

用法：cd openmath && PYTHONIOENCODING=utf-8 python 08-工具/examples/verify_OM-F-AN-0004.py
退出码：0＝全部判定通过；1＝有判定不过；2＝前置条件缺失（未装 mpmath）。
"""
import sys

try:
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 mpmath，无法执行 L2 验证。安装: pip install mpmath")
    sys.exit(2)

DPS = 50
SPREAD_TOL = mp.mpf("1e-30")   # ε 随采样点的漂移上限：证明「是个常数」
MODULUS_TOL = mp.mpf("1e-30")  # ||ε| − 1| 的上限
RESID_TOL = mp.mpf("1e-30")    # 定下约定后，方程两边的残差

# 采样点：刻意避开 s=1 极点、平凡零点（Λ 在那里两端同时为零 ⇒ 无效检验点）
SAMPLE_POINTS = [
    "0.5+14.134725*I",
    "0.3+7.2*I",
    "0.7+25.0*I",
    "-1.5+3.0*I",
    "0.25+100.0*I",
    "0.9+2.5*I",
]

# 特征：values[r-1] = χ(r)，r = 1..q。全部非主特征。
# 这张表**必须在 dps 设好之后现建**：模块导入时 mpmath 还是默认 15 位，
# 用 15 位建出的 e^(2πi·k/6) 会让 χ(-1) 变成 -1+2.9e-16j，判 χ 奇偶的那一步当场崩
# （本轮第一跑就是把它打在导入期，崩在 parity()——是仪器的错，不是语料的错）。
def characters():
    z = mp.e**(2j * mp.pi / 6)
    w = [mp.mpf(1)] + [z ** k for k in range(1, 6)]
    return [
        ("chi_4", "模 4 奇特征（L = Dirichlet beta 函数）", [mp.mpf(1), mp.mpf(0), mp.mpf(-1), mp.mpf(0)]),
        ("chi_3", "模 3 奇特征（二次，实值）", [mp.mpf(1), mp.mpf(-1), mp.mpf(0)]),
        ("chi_5", "模 5 偶二次特征", [mp.mpf(1), mp.mpf(-1), mp.mpf(-1), mp.mpf(1), mp.mpf(0)]),
        # (Z/7)* 以 3 为生成元：3^0=1,3^1=3,3^2=2,3^3=6,3^4=4,3^5=5；χ(3^k)=ζ_6^k ⇒ 阶 6、复值、原始
        ("chi_7", "模 7 阶 6 复特征（τ(χ) ≠ τ(χ̄)，用来分辨共轭约定）",
         [w[0], w[2], w[1], w[4], w[5], w[3], mp.mpf(0)]),
    ]


def parse(text):
    text = text.strip()
    if "*I" in text:
        head = text.replace("*I", "")
        # 允许 '0.5+14.1*I' 与 '-1.5+3.0*I'：虚部符号取最后一个 +/- 分隔
        for split_at in range(len(head) - 1, 0, -1):
            if head[split_at] in "+-" and head[split_at - 1] not in "eE":
                return mp.mpc(mp.mpf(head[:split_at]), mp.mpf(head[split_at:]))
        return mp.mpc(0, mp.mpf(head))
    return mp.mpc(mp.mpf(text))


def L_of(s, chi, q):
    """L(s,chi) 经 Hurwitz ζ 的解析延拓。非主特征下 s=1 极点相消。"""
    total = mp.mpc(0)
    for r in range(1, q + 1):
        if chi[r - 1] == 0:
            continue
        total += chi[r - 1] * mp.hurwitz(s, mp.mpf(r) / q)
    return mp.power(mp.mpf(q), -s) * total


def completed(s, chi, q, a):
    gamma_arg = (s + a) / 2
    factor = mp.power(mp.mpf(q) / mp.pi, gamma_arg) * mp.gamma(gamma_arg)
    return factor * L_of(s, chi, q)


def gauss_sum(chi, q):
    return sum(chi[r - 1] * mp.e**(2j * mp.pi * r / q) for r in range(1, q + 1))


def conj_of(chi, q):
    return [mp.conj(v) for v in chi]


def parity(chi, q):
    """a = (1 - chi(-1))/2；chi(-1) = chi[q-2]（r = q-1）。χ(-1) 只能是 ±1。"""
    val = chi[q - 2]
    if abs(val - 1) < mp.mpf("1e-30"):
        return 0
    assert abs(val + 1) < mp.mpf("1e-30"), "chi(-1) 不是 ±1：%s" % mp.nstr(val, 20)
    return 1


def main():
    mp.mp.dps = DPS
    print("OM-F-AN-0004 狄利克雷 L-函数函数方程｜L2 验证（精度 %d 位）" % DPS)
    print("-" * 78)
    failures = []
    lines = []
    powered, no_power, falsified = [], [], []
    for name, desc, chi in characters():
        q = len(chi)
        a = parity(chi, q)
        chi_bar = conj_of(chi, q)
        eps_meas, used, skipped = [], 0, 0
        for pt in SAMPLE_POINTS:
            s = parse(pt)
            try:
                left = completed(s, chi, q, a)
                right = completed(1 - s, chi_bar, q, a)
                if abs(right) < mp.mpf("1e-20"):
                    skipped += 1
                    print("  [跳过] %s @ %s：|Λ(1-s,chi_bar)| = %s < 1e-20（近零点，比值不是 ε 的可靠测量）"
                          % (name, pt, mp.nstr(abs(right), 8)))
                    continue
                eps_meas.append(left / right)
                used += 1
            except Exception as exc:  # Hurwitz 延拓在个别点可能失败：点名而不静默
                skipped += 1
                print("  [跳过] %s @ %s：%s" % (name, pt, exc))
        if used < 3:
            failures.append("%s：可用采样点 %d < 3，无法判 ε 恒定" % (name, used))
            continue
        spread = max(abs(e - eps_meas[0]) for e in eps_meas)
        modulus = abs(abs(eps_meas[0]) - 1)
        eps = eps_meas[0]
        tau = gauss_sum(chi, q)
        tau_bar = gauss_sum(chi_bar, q)
        root_q = mp.sqrt(mp.mpf(q))
        i_a = mp.j ** a
        cand = {
            "tau(chi)/(i^a*sqrt(q))": tau / (i_a * root_q),
            "i^a*tau(chi)/sqrt(q)": i_a * tau / root_q,
            "tau(chi_bar)/(i^a*sqrt(q))": tau_bar / (i_a * root_q),
            "i^a*tau(chi_bar)/sqrt(q)": i_a * tau_bar / root_q,
            "tau(chi)/sqrt(q)": tau / root_q,
        }
        # 「测得的模」必须独立成立，否则上面四个候选只是同一个数的四种写法
        mod_ok = modulus < MODULUS_TOL
        tol_match = abs(spread) < SPREAD_TOL
        matches = [k for k, v in cand.items() if abs(v - eps) < mp.mpf("1e-25")]
        # 定下约定后再算残差：用与约定无关的测得 ε 会把「方程成立」变成同义反复，
        # 所以这里用**候选公式**代回方程两端做残差。
        # 残差的**货币**：Λ 的两端在大虚部处指数级小（Γ((1-s+a)/2) 衰减到 ~1e-34），
        # 只报绝对残差会把「两边都是 1e-34 量级」的格子冒充高精度证据。
        # 所以每条候选同时报绝对与相对（相对按两端模的大者归一），并印出最小模＝这一格的尺度。
        resid, rel_resid = {}, {}
        scales = []
        for k, v in cand.items():
            rs, rr = [], []
            for pt in SAMPLE_POINTS:
                s = parse(pt)
                try:
                    lft = completed(s, chi, q, a)
                    rgt = completed(1 - s, chi_bar, q, a)
                    den = max(abs(lft), abs(v * rgt))
                    rs.append(abs(lft - v * rgt))
                    if den > mp.mpf("1e-20"):
                        rr.append(abs(lft - v * rgt) / den)
                    scales.append(den)
                except Exception:
                    pass
            resid[k] = max(rs) if rs else None
            rel_resid[k] = max(rr) if rr else None
        min_scale = min(scales) if scales else None
        best = min((k for k in cand if rel_resid[k] is not None), key=lambda k: rel_resid[k])
        REL_TOL = mp.mpf("1e-25")
        if rel_resid[best] is None or rel_resid[best] >= REL_TOL:
            failures.append("%s：命中约定的相对残差 %s 未过 %s（绝对残差不算数）"
                            % (name, mp.nstr(rel_resid[best], 8) if rel_resid[best] is not None else "n/a", REL_TOL))
        print("  该格尺度 min|两端| = %s（绝对残差必须配上这个数才可读）" % mp.nstr(min_scale, 8))
        print("[%s] %s" % (name, desc))
        print("  q=%d  a=%d  采样：用 %d 点／跳 %d 点" % (q, a, used, skipped))
        print("  eps_meas(首点) = %s" % mp.nstr(eps, 25))
        print("  |eps|-1        = %s  （判据 <%s）%s" % (mp.nstr(modulus, 8), MODULUS_TOL, "PASS" if mod_ok else "FAIL"))
        print("  eps 随点漂移   = %s  （判据 <%s）%s" % (mp.nstr(spread, 8), SPREAD_TOL, "PASS" if tol_match else "FAIL"))
        print("  tau(chi)       = %s ｜ |tau| = %s ｜ sqrt(q) = %s"
              % (mp.nstr(tau, 20), mp.nstr(abs(tau), 20), mp.nstr(root_q, 20)))
        for k, v in cand.items():
            print("  候选 %-30s = %s ｜ 与测得差 %s ｜ 绝对残差 %s ｜ 相对残差 %s%s"
                  % (k, mp.nstr(v, 20), mp.nstr(abs(v - eps), 8),
                     mp.nstr(resid[k], 8) if resid[k] is not None else "n/a",
                     mp.nstr(rel_resid[k], 8) if rel_resid[k] is not None else "n/a",
                     "  <== 命中" if k in matches else ""))
        print("  残差最小的约定：%s｜该约定的命中候选：%s" % (best, "是" if best in matches else "否"))
        # 分辨力披露：实值偶特征下五个候选可能全等，那一枚就对「写哪种约定」零证据。
        # 不把这种格子算作判定，否则结论会被一个本来分不出来的样本冒充。
        distinct = len({mp.nstr(cand[k], 12) for k in cand})
        print("  候选互异性：%d/5 个不同值｜本特征对约定的分辨力＝%s"
              % (distinct, "有" if distinct > 1 else "无（实值且 a=0 时五种写法全等）"))
        if distinct == 1:
            no_power.append(name)
        else:
            powered.append((name, matches))
        for k, v in cand.items():
            if k not in matches and rel_resid[k] is not None and rel_resid[k] > mp.mpf("1e-10"):
                falsified.append("%s/%s" % (name, k))
        if not (mod_ok and tol_match):
            failures.append("%s：ε 不恒定或 |ε|≠1" % name)
        # 「命中不止一个」有两种：实值特征下 χ=χ̄，两个标签本来就是同一个数（并格即可，
        # 不是歧义）；只有命中值互不相同才是真歧义。按**数值**去重，不按标签数。
        hit_values = {}
        for k in matches:
            hit_values.setdefault(mp.nstr(cand[k], 14), []).append(k)
        if not matches:
            failures.append("%s：测得 ε 不匹配任何候选约定（约定表要补）" % name)
        elif len(hit_values) > 1:
            failures.append("%s：命中的候选值互不相同（测量没定出唯一约定）" % name)
        elif best not in matches:
            failures.append("%s：残差最小者不在命中名单里" % name)
        if len(matches) > 1 and hit_values:
            print("  命中 %d 个标签但只有 %d 个值：%s（同值并格）"
                  % (len(matches), len(hit_values),
                     "／".join("≡".join(v) for v in hit_values.values())))
        lines.append((name, q, a, mp.nstr(eps, 25), mp.nstr(modulus, 8), mp.nstr(spread, 8),
                      best, mp.nstr(resid[best], 8), mp.nstr(rel_resid[best], 8), mp.nstr(min_scale, 8)))
    print("-" * 78)
    print("有分辨力的特征（候选不止一个值）：%s" % ("／".join(n for n, _ in powered) or "无"))
    print("无分辨力的特征（五种写法全等，不计入判定）：%s" % ("／".join(no_power) or "无"))
    print("被证伪的约定（残差 >1e-10）：%s" % ("／".join(sorted(set(falsified))) or "无"))
    if len(powered) < 2:
        failures.append("有分辨力的特征 <2：约定不是被测量选出来的")
    if not falsified:
        failures.append("没有任何候选被证伪：这台仪器对『写哪种约定』是空转的")
    if failures:
        print("判定：FAIL（%d 条）" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("判定：PASS｜4/4 特征的根数由测量确定、模为 1、随采样点恒定")
    for row in lines:
        print("  %s: q=%d a=%d eps=%s ||eps|-1=%s spread=%s 命中约定=%s 绝对残差=%s 相对残差=%s 最小尺度=%s" % row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
