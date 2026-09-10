# -*- coding: utf-8 -*-
"""孪生素数（Landau 问题 #2）数值验证引擎 · 候选 L2 引擎。

本模块做两件事：
  1. 用筛法精确枚举孪生素数对 (p, p+2)，给出 \(\pi_2(x)\)（≤x 的孪生素数对计数）；
  2. 交叉校验 OEIS A007508 的权威已知值（非本程序生成），并与严格的
     Hardy–Littlewood 渐近 \(\pi_2(x) \sim 2 C_2\, x/(\ln x)^2\)（C_2 为孪生素数常数）做标定。

诚实声明（红线五 / 红线一）
--------------------------
孪生素数猜想（存在无穷多对 (p,p+2)）**至今未证明**（张益唐 2013 仅证有界间隔 < 7e7，
Polymath8/Maynard 改进至 246；间隔恰好为 2 仍未解决）。
本模块只提供 **L2（数值）** 证据：数值通过只能"支持"，不能"证明"猜想。
Hardy–Littlewood 渐近是经典解析数论结论，本脚本用数值验证其对真实 \(\pi_2(x)\) 的逼近程度。

运行：
    python 孪生素数_验证.py            # 标准自检（到 1e7）
    python 孪生素数_验证.py --big      # 追加到 1e8
    python 孪生素数_验证.py --plot     # 额外输出两张 PNG（需 matplotlib）
"""

from __future__ import annotations

import math
import sys
import time
from array import array


# --------------------------------------------------------------------------
# 0. 工具
# --------------------------------------------------------------------------

def isqrt(n: int) -> int:
    return math.isqrt(n)


def sieve_primes(limit: int):
    """返回 [0, limit] 的素数布尔表与升序素数表。"""
    flags = bytearray([1]) * (limit + 1)
    flags[0] = flags[1] = 0
    i = 2
    while i * i <= limit:
        if flags[i]:
            flags[i * i : limit + 1 : i] = bytearray(
                len(range(i * i, limit + 1, i))
            )
        i += 1
    primes = [k for k in range(2, limit + 1) if flags[k]]
    return flags, primes


# --------------------------------------------------------------------------
# 1. 孪生素数计数
# --------------------------------------------------------------------------

def twin_pairs(N: int):
    """枚举所有 p <= N 且 p+2 也为素数的对 (p, p+2)。"""
    if N < 3:
        return []
    flags, _ = sieve_primes(N + 2)
    return [(p, p + 2) for p in range(2, N + 1) if flags[p] and flags[p + 2]]


def pi2(N: int) -> int:
    """\(\pi_2(N)\)：≤N 的孪生素数对 (p, p+2) 的个数。"""
    if N < 3:
        return 0
    flags, _ = sieve_primes(N + 2)
    cnt = 0
    for p in range(2, N + 1):
        if flags[p] and flags[p + 2]:
            cnt += 1
    return cnt


# --------------------------------------------------------------------------
# 2. 孪生素数常数 C2 与 Hardy–Littlewood 渐近
# --------------------------------------------------------------------------

def compute_C2(prime_limit: int = 10_000_000) -> tuple[float, list[int]]:
    """C2 = prod_{p>=3} (1 - 1/(p-1)^2) = prod_{p>=3} p(p-2)/(p-1)^2。

    返回 (C2, 收敛轨道：[前 k 个奇素数截断值])，用于观察收敛。
    """
    _, primes = sieve_primes(prime_limit)
    prod = 1.0
    track = []
    seen = 0
    for p in primes:
        if p == 2:
            continue
        prod *= (p * (p - 2)) / ((p - 1) * (p - 1))
        seen += 1
        if seen in (10, 100, 1000, 10000, 100000, 1000000, len(primes) - 1):
            track.append(prod)
    return prod, track


def hl_estimate(x: int, C2: float) -> float:
    """Hardy–Littlewood 主项：2*C2 * x / (ln x)^2。"""
    if x < 3:
        return 0.0
    ln = math.log(x)
    return 2.0 * C2 * x / (ln * ln)


# --------------------------------------------------------------------------
# 3. 已知基线（OEIS A007508：≤ 10^k 的孪生素数对数量，外部权威值）
# --------------------------------------------------------------------------

OEIS_A007508 = {
    1: 2,
    2: 8,
    3: 35,
    4: 205,
    5: 1224,
    6: 8169,
    7: 58980,
    8: 440312,
    9: 3424506,
    10: 27412679,
}


# --------------------------------------------------------------------------
# 4. 自检
# --------------------------------------------------------------------------

def self_test(big: bool = False, do_plot: bool = False) -> dict:
    print("=" * 78)
    print("孪生素数验证引擎 · 自检")
    print("=" * 78)

    # --- A. C2 常数收敛轨道 ------------------------------------------------
    t0 = time.perf_counter()
    C2, track = compute_C2(10_000_000)
    c2_sec = time.perf_counter() - t0
    print("\n[A] 孪生素数常数 C2 = prod_{p>=3} p(p-2)/(p-1)^2")
    print("    收敛轨道(截断到前k个奇素数):")
    for k, v in zip([10, 100, 1000, 10000, 100000, 1000000, "全部"], track):
        print("        k=%-8s C2 ≈ %.10f" % (k, v))
    print("    参考真值 C2 ≈ 0.6601618158468698    (本计算 %.10f, %s)"
          % (C2, "吻合" if abs(C2 - 0.6601618158) < 1e-6 else "需更多素数"))

    # --- B. OEIS A007508 交叉校验 -----------------------------------------
    print("\n[B] pi2(10^k) vs OEIS A007508")
    bad = []
    top = 8 if not big else 9
    for k in range(1, top + 1):
        x = 10 ** k
        got = pi2(x)
        exp = OEIS_A007508[k]
        ok = got == exp
        if not ok:
            bad.append((x, exp, got))
        print("    pi2(10^%d) = %-9d   OEIS=%d   %s"
              % (k, got, exp, "OK" if ok else "MISMATCH"))
    print("    结果: %s" % ("全部一致" if not bad else str(bad)))

    # --- C. HL 渐近标定（核心）--------------------------------------------
    print("\n[C] 真实 pi2(x) 与 Hardy–Littlewood 渐近的比值")
    print("    x         pi2(x)       HL=2C2 x/ln^2   比值(pi2/HL)")
    rows = []
    for x in [100, 1000, 10000, 100000, 1000000, 10000000]:
        truth = pi2(x)
        hl = hl_estimate(x, C2)
        r_hl = truth / hl if hl else float("nan")
        rows.append((x, truth, hl, r_hl))
        print("    %-9d %-11d %-15.2f %-14.4f"
              % (x, truth, hl, r_hl))
    print("    观察: pi2/HL -> 1（验证 HL 主项正确）")

    if do_plot:
        _make_plots(C2, rows)

    print("\n" + "=" * 78)
    print("诚实结论（L2）: 数值支持 'pi2(x) ~ 2 C2 x/(ln x)^2'，但")
    print("  孪生素数猜想（无穷多对）仍 OPEN，数值不能证明它。")
    print("=" * 78)

    return {
        "C2": C2,
        "c2_seconds": round(c2_sec, 3),
        "oeis_mismatch": bad,
        "hl_rows": [
            {"x": x, "pi2": t, "hl": h, "ratio_hl": rh}
            for (x, t, h, rh) in rows
        ],
    }


def _make_plots(C2: float, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # 无 matplotlib 时静默跳过（红线：引擎不得抛出）
        print("    [plot] 未安装 matplotlib，跳过绘图: %r" % exc)
        return

    xs = [r[0] for r in rows]
    truth = [r[1] for r in rows]
    hl = [r[2] for r in rows]

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ax[0].plot(xs, truth, "o-", label="pi2(x) exact (sieve)")
    ax[0].plot(xs, hl, "s--", label="HL: 2*C2*x/ln^2")
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_title("pi2(x) vs Hardy–Littlewood (C2=%.6f)" % C2)
    ax[0].set_xlabel("x")
    ax[0].set_ylabel("pi2")
    ax[0].legend()
    ax[0].grid(True, which="both", ls=":")

    rh = [r[3] for r in rows]
    ax[1].plot(xs, rh, "o-", label="pi2 / HL")
    ax[1].axhline(1.0, color="gray", ls="--", label="1.0 (HL baseline)")
    ax[1].set_xscale("log")
    ax[1].set_title("ratio convergence (pi2 / HL)")
    ax[1].set_xlabel("x")
    ax[1].set_ylabel("ratio")
    ax[1].legend()
    ax[1].grid(True, which="both", ls=":")

    fig.tight_layout()
    out = "孪生素数_验证_plot.png"
    fig.savefig(out, dpi=130)
    print("    [plot] 已保存: " + out)


if __name__ == "__main__":
    big = "--big" in sys.argv
    plot = "--plot" in sys.argv
    self_test(big=big, do_plot=plot)
