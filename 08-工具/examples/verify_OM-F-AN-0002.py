# -*- coding: utf-8 -*-
"""OM-F-AN-0002 Riemann ζ 函数函数方程的独立验证脚本。

    ζ(s) = 2^s · pi^(s-1) · sin(pi·s/2) · Γ(1-s) · ζ(1-s)

用法：
    python 08-工具/examples/verify_OM-F-AN-0002.py

关键陷阱（见条目的 caveat 字段）：
  1. 不能用级数 Σ n^{-s} 计算 —— 在 Re(s) < 1 时级数发散；
     必须使用实现了解析延拓的函数（mpmath.zeta）。
  2. 平凡零点 s = -2, -4, ... 处两边同时为零，是**无效**检验点。
  3. s 接近正整数时 Γ(1-s) 发散、sin(pi·s/2) 趋零，出现 0 × ∞，
     低精度下会灾难性抵消，必须用 ≥ 50 位精度。
"""

import sys

try:
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 mpmath，无法执行 L2 验证。安装: pip install mpmath")
    sys.exit(0)

# 采样点：刻意避开平凡零点与 s=1 极点
SAMPLE_POINTS = [
    ("0.5+14.134725*I", "第一个非平凡零点附近"),
    ("0.3+7.2*I", "临界带内随机点"),
    ("0.7+25.0*I", "临界带内、虚部适中"),
    ("0.5+40.918719*I", "高阶零点附近"),
    ("-1.5+3.0*I", "临界带左侧（需解析延拓）"),
    ("0.25+100.0*I", "大虚部"),
    ("0.9+2.5*I", "接近临界带右边界"),
    ("0.1+55.3*I", "接近临界带左边界"),
]

TOLERANCE = mp.mpf("1e-35")


def residual_at(s_str):
    s = mp.mpmathify(s_str.replace("*I", "j")) if "j" in s_str else _parse(s_str)
    left = mp.zeta(s)
    right = (
        mp.power(2, s)
        * mp.power(mp.pi, s - 1)
        * mp.sin(mp.pi * s / 2)
        * mp.gamma(1 - s)
        * mp.zeta(1 - s)
    )
    return s, left - right


def _parse(text):
    """把 'a+b*I' 形式解析为 mpmath 复数。"""
    text = text.strip()
    if "*I" in text:
        real_part, _, imag_part = text.partition("+")
        imag_part = imag_part.replace("*I", "").strip()
        return mp.mpc(mp.mpf(real_part.strip()), mp.mpf(imag_part))
    return mp.mpf(text)


def main():
    mp.mp.dps = 50
    print("OM-F-AN-0002 Riemann ζ 函数函数方程")
    print("-" * 72)
    print("精度 : %d 位有效数字    容差 : %s" % (mp.mp.dps, mp.nstr(TOLERANCE, 5)))
    print("-" * 72)
    print("%-22s %-14s %s" % ("s", "|残差|", "备注"))
    print("-" * 72)

    worst = mp.mpf(0)
    failures = 0
    for s_str, note in SAMPLE_POINTS:
        try:
            s, residual = residual_at(s_str)
            magnitude = abs(residual)
        except Exception as exc:
            print("%-22s %-14s 求值失败: %s" % (s_str, "-", exc))
            failures += 1
            continue
        worst = max(worst, magnitude)
        flag = "" if magnitude < TOLERANCE else "  ⚠️ 超容差"
        print("%-22s %-14s %s%s" % (s_str, mp.nstr(magnitude, 6), note, flag))
        if magnitude >= TOLERANCE:
            failures += 1

    print("-" * 72)
    print("最大残差 : %s" % mp.nstr(worst, 10))
    if failures:
        print("L2 FAIL : %d 个采样点超出容差。" % failures)
        print("          请人工判断：是条目有误，还是采样点落在奇点附近。")
        print("          禁止通过放宽容差或修改断言来让测试变绿。")
        return 1
    print("L2 PASS : %d 个采样点均在容差内。" % len(SAMPLE_POINTS))
    print("诚实提醒: 函数方程是**已证明的定理**；本脚本的数值通过不是它的证明。")
    print("          同时，本脚本与黎曼假设无关——二者不可混淆。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
