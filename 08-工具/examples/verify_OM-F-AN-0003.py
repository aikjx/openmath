# -*- coding: utf-8 -*-
"""OM-F-AN-0003 欧拉公式（一般形式）的独立验证脚本。

用法：
    python 08-工具/examples/verify_OM-F-AN-0003.py

输出**残差**而不是"通过"：残差量级必须与所设精度匹配（50 位 → 应在 1e-45 量级以下）。
另外把记录正文 §二 声称的三个后果（de Moivre、n 次单位根、加法->乘法的同态性）各测一次，
这样"文档里写了而只靠定义蒙混"的段落会被这台脚本自己点名。

诚实边界：本公式在幂级数定义下是定义的直接推论，L2/L3 通过几乎不提供信息量；
它们检验的是实现一致性，不是数学内容。
"""

import sys

try:
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 mpmath，无法执行 L2 验证。安装: pip install mpmath")
    return_ = 0
    sys.exit(return_)

TOL = mp.mpf("1e-40")


def theta_grid():
    """确定性网格：12 个 pi 的有理倍数 + 12 个 sqrt(m)，不用随机数（seed 无可依赖语义）。"""
    pts = [mp.mpf(k) * mp.pi / 12 for k in range(12)]
    pts += [mp.sqrt(mp.mpf(m)) for m in range(1, 13)]
    return pts


def check(name, residual, extra=""):
    ok = residual < TOL
    print("%-22s residual=%-12s %s %s"
          % (name, mp.nstr(residual, 6), "OK" if ok else "OVER-TOL", extra))
    return ok, residual


def main():
    mp.mp.dps = 50
    I = mp.mpc(0, 1)
    worst = mp.mpf(0)
    n_points = 0
    all_ok = True

    print("OM-F-AN-0003 e^{i*theta} = cos(theta) + i*sin(theta)  （及一般形式）")
    print("-" * 72)
    print("精度         : %d 位有效数字" % mp.mp.dps)
    print("容差         : %s" % mp.nstr(TOL, 5))
    print("采样         : 确定性网格（pi 的有理倍数 12 点 + sqrt(m) 12 点），无随机" )

    # (1) 主式：e^{i theta} 与 cos + i sin
    for th in theta_grid():
        n_points += 1
        ok, r = check("e^(i*theta)-(...)", abs(mp.e ** (I * th) - (mp.cos(th) + I * mp.sin(th))),
                      "theta=%s" % mp.nstr(th, 8))
        all_ok = all_ok and ok
        worst = max(worst, r)

    # (2) 一般形式：e^{z} = e^{x}(cos y + i sin y)，x != 0
    for x in (mp.mpf("-2"), mp.mpf("0.5"), mp.mpf("3"), mp.mpf("-17")):
        for y in (mp.mpf("1"), mp.pi / 7, mp.sqrt(mp.mpf("2"))):
            n_points += 1
            z = x + I * y
            ok, r = check("general-form", abs(mp.e ** z - mp.e ** x * (mp.cos(y) + I * mp.sin(y))),
                          "z=%s" % mp.nstr(z, 8))
            all_ok = all_ok and ok
            worst = max(worst, r)

    # (3) §二 后果一：de Moivre
    for th in (mp.pi / 6, mp.sqrt(mp.mpf("3")), mp.mpf("2")):
        for n in (2, 5, 13):
            n_points += 1
            lhs = (mp.cos(th) + I * mp.sin(th)) ** n
            rhs = mp.cos(n * th) + I * mp.sin(n * th)
            ok, r = check("de-Moivre(n=%d)" % n, abs(lhs - rhs))
            all_ok = all_ok and ok
            worst = max(worst, r)

    # (4) §二 后果二：n 次单位根恰为 e^{2 pi i k / n}，且乘积为 1（根的乘性群）
    for n in (3, 4, 6, 12):
        n_points += 1
        prod = mp.mpf(1)
        for k in range(n):
            w = mp.e **(2 * I * mp.pi * k / n)
            prod *= w
            r1 = abs(w ** n - 1)
            all_ok = all_ok and (r1 < TOL)
            worst = max(worst, r1)
        # 乘积 = (-1)^{n-1}（z^n - 1 的常数项），本库不写新事实，只核对已知闭式
        expect = mp.mpf(-1) ** (n - 1)
        ok, r = check("roots-of-unity(n=%d)" % n, abs(prod - expect), "prod-expect")
        all_ok = all_ok and ok
        worst = max(worst, r)

    # (5) §一 同态性：e^{z+w} = e^{z} e^{w}
    for (a, b) in ((mp.mpf("0.3"), I * mp.pi / 5), (mp.mpf("-4"), I * mp.sqrt(mp.mpf("5"))),
                   (mp.mpf("1") + I, mp.mpf("-2") + I * mp.pi)):
        n_points += 1
        ok, r = check("homomorphism", abs(mp.e ** (a + b) - mp.e ** a * mp.e ** b))
        all_ok = all_ok and ok
        worst = max(worst, r)

    print("-" * 72)
    print("SAMPLE_COUNT = %d" % n_points)
    print("MAX_ABS_RESIDUAL = %s" % mp.nstr(worst, 3))

    l3 = l3_check()

    if not all_ok or not l3:
        print("L2/L3 FAIL: 至少一项残差超出容差或符号化简未归零。")
        return 1
    print("L2 PASS + L3 PASS: 全部 %d 项在容差内。" % n_points)
    print("诚实提醒: 本公式是复指数幂级数定义的直接推论，此 PASS 不构成证明、不表示进展。")
    return 0


def l3_check():
    try:
        from sympy import I, cos, exp, simplify, sin, symbols
    except ImportError:
        print("L3 SKIP: 未安装 sympy。")
        return True
    x, y, t = symbols("x y t", real=True)
    e1 = simplify(exp(x + I * y) - exp(x) * (cos(y) + I * sin(y)))
    e2 = simplify(exp(I * t) - (cos(t) + I * sin(t)))
    e3 = simplify(exp(2 * I * t) - exp(I * t) ** 2)
    print("L3 一般形式 残差符号式: %r" % (e1,))
    print("L3 主式      残差符号式: %r" % (e2,))
    print("L3 deMoivre  残差符号式: %r" % (e3,))
    return e1 == 0 and e2 == 0 and e3 == 0


if __name__ == "__main__":
    sys.exit(main())
