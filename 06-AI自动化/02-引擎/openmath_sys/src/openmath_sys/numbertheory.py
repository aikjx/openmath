# -*- coding: utf-8 -*-
"""数论计算能力（对应方法体系中 rad_computation / modular_analysis /
sieve_theory / asymptotic_estimation 四条方法的具体实现）。

诚实范围声明（务必阅读）：
  本模块实现的是**可计算的简化版本**，不等于相应的完整数学理论：

  - rad_computation   : 精确实现 rad(n)（不同素因子之积），这是定义本身，无简化。
  - sieve_theory      : 仅实现**哥德巴赫分拆计数**与**孪生素数筛**两个具体筛法应用，
                        **不是** Selberg 筛/大筛法等一般解析筛法理论。
  - asymptotic_estimation : 仅实现素数计数函数 π(x) 与 x/ln x、li(x) 的数值比较，
                        **不是**一般意义下的渐近展开推导工具。
  - modular_analysis  : 按剩余类统计 Collatz 轨道的停止时间分布，是最朴素的模类统计。

所有输出均为 **L2 计算证据**：数值结果不构成任何证明，且受搜索范围上限限制。
"""
from __future__ import annotations

import math

# Soldner–Ramanujan 常数：li(x) 的主值积分常数项
_SOLDNER = 1.045163780117492784844588889194613136522615578151


def sieve_primes(n: int) -> list[int]:
    """埃拉托斯特尼筛，返回 <= n 的全部素数。"""
    if n < 2:
        return []
    flags = bytearray([1]) * (n + 1)
    flags[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            flags[i * i::i] = bytearray(len(flags[i * i::i]))
    return [i for i in range(2, n + 1) if flags[i]]


def sieve_is_prime(n: int) -> bytearray:
    """返回 0..n 的素性标记字节数组。"""
    flags = bytearray([1]) * (n + 1)
    if n >= 0:
        flags[0] = 0
    if n >= 1:
        flags[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            flags[i * i::i] = bytearray(len(flags[i * i::i]))
    return flags


def radical_table(n: int) -> list[int]:
    """用筛法一次性计算 rad(0..n)：rad(k) = k 的不同素因子之积。"""
    rad = [1] * (n + 1)
    for p in sieve_primes(n):
        for k in range(p, n + 1, p):
            rad[k] *= p
    return rad


def rad(n: int) -> int:
    """rad(n)：n 的不同素因子之积（rad(1)=1）。用于 ABC 猜想。"""
    if n <= 1:
        return 1
    m, result = n, 1
    if m % 2 == 0:
        result *= 2
        while m % 2 == 0:
            m //= 2
    d = 3
    while d * d <= m:
        if m % d == 0:
            result *= d
            while m % d == 0:
                m //= d
        d += 2
    if m > 1:
        result *= m
    return result


def abc_quality(a: int, b: int, c: int) -> dict:
    """ABC 三元组 (a,b,c)（a+b=c，两两互素）的质量 q = ln c / ln rad(abc)。

    ABC 猜想断言：对任意 eps>0，仅有有限多个三元组满足 q > 1+eps。
    q > 1 的三元组存在（如 3+125=128, q≈1.4265）。
    """
    r = rad(a) * rad(b) * rad(c)      # 两两互素时 rad(abc)=rad(a)rad(b)rad(c)
    if r <= 1:
        return {"a": a, "b": b, "c": c, "rad": r, "quality": None}
    return {"a": a, "b": b, "c": c, "rad": r,
            "quality": math.log(c) / math.log(r)}


def search_abc_triples(c_max: int = 3000, top_k: int = 8) -> dict:
    """在 c <= c_max 内搜索 quality 最高的 ABC 三元组。

    复杂度 O(c_max^2)：c_max=3000 约需数秒。结果受范围限制，
    **未找到更高 quality 不代表不存在**，仅是本搜索范围内的证据。
    """
    rad_tbl = radical_table(c_max)
    best: list[dict] = []
    above_one = 0
    for c in range(3, c_max + 1):
        rc = rad_tbl[c]
        for a in range(1, c // 2 + 1):
            b = c - a
            if math.gcd(a, b) != 1:
                continue
            r = rad_tbl[a] * rad_tbl[b] * rc
            if r <= 1:
                continue
            q = math.log(c) / math.log(r)
            if q > 1.0:
                above_one += 1
                if len(best) < top_k:
                    best.append({"a": a, "b": b, "c": c, "rad": r, "quality": q})
                    best.sort(key=lambda x: -x["quality"])
                elif q > best[-1]["quality"]:
                    best[-1] = {"a": a, "b": b, "c": c, "rad": r, "quality": q}
                    best.sort(key=lambda x: -x["quality"])
    return {
        "c_max": c_max,
        "triples_with_quality_above_1": above_one,
        "top_by_quality": [
            {**x, "quality": round(x["quality"], 6)} for x in best
        ],
        "known_reference": {
            "note": "已知最高 quality 的例子远超本搜索范围"
                    "（如 2 + 3^10*109 = 23^5，q≈1.6299），"
                    "本结果仅反映搜索上限内的情况。",
        },
    }


def goldbach_partitions(n: int, is_prime: bytearray) -> int:
    """偶数 n 的哥德巴赫分拆数 G(n)：n=p+q (p<=q, 均为素数) 的方案数。"""
    if n % 2 or n < 4:
        return 0
    cnt = 0
    for p in range(2, n // 2 + 1):
        if is_prime[p] and is_prime[n - p]:
            cnt += 1
    return cnt


def goldbach_profile(limit: int = 20000, sample_step: int | None = None) -> dict:
    """统计 limit 内所有偶数的哥德巴赫分拆数，检查是否存在 0（即反例）。

    哥德巴赫猜想：每个 >=4 的偶数都是两素数之和。此处为**穷举验证**（L2），
    在 limit 内成立不代表猜想成立。
    """
    is_prime = sieve_is_prime(limit)
    min_g, min_at, zeros = None, None, []
    samples = []
    for n in range(4, limit + 1, 2):
        g = goldbach_partitions(n, is_prime)
        if g == 0:
            zeros.append(n)
        if min_g is None or g < min_g:
            min_g, min_at = g, n
        if sample_step and n % sample_step == 0:
            samples.append({"n": n, "partitions": g})
    return {
        "limit": limit,
        "all_even_have_partition": not zeros,
        "counterexamples_in_range": zeros[:20],
        "min_partitions": {"n": min_at, "count": min_g},
        "samples": samples,
        "trend_note": "G(n) 整体随 n 增长（Hardy–Littlewood 渐近 ~ n/(ln n)^2 * C2），"
                      "但局部波动剧烈；此处为穷举计数，非渐近公式。",
    }


def twin_prime_profile(limit: int = 200000) -> dict:
    """筛出 limit 内孪生素数对。孪生素数猜想断言有无穷多对（未解）。"""
    is_prime = sieve_is_prime(limit)
    twins = [(p, p + 2) for p in range(3, limit - 1)
             if is_prime[p] and is_prime[p + 2]]
    return {
        "limit": limit,
        "twin_pairs": len(twins),
        "largest_pair": twins[-1] if twins else None,
        "first_pairs": [list(t) for t in twins[:5]],
    }


def logarithmic_integral(x: float) -> float:
    """li(x) = PV∫_0^x dt/ln t，用 Soldner 常数 + Simpson 数值积分（从 2 到 x）。

    分段原因：被积函数 1/ln t 在 t→2 附近变化剧烈而随后极其平缓，
    若对 [2, x] 用**均匀** Simpson，步长 h 由大区间决定，起点附近分辨率严重不足
    （实测 li(1e5) 会偏高约 15）。故拆为 [2,10] 与 [10,x] 两段分别加密。
    """
    if x <= 2:
        return _SOLDNER

    def f(t: float) -> float:
        return 1.0 / math.log(t)

    def simpson(a: float, b: float, n: int) -> float:
        h = (b - a) / n
        s = f(a) + f(b)
        for i in range(1, n):
            s += (4 if i % 2 else 2) * f(a + i * h)
        return s * h / 3.0

    total = simpson(2.0, 10.0, 4000)
    if x > 10:
        total += simpson(10.0, float(x), 4000)
    elif x > 2:
        total = simpson(2.0, float(x), 4000)
    return _SOLDNER + total


def prime_count_asymptotics(limit: int = 100000) -> dict:
    """比较 π(x) 与两个经典近似：x/ln x 与 li(x)。

    素数定理断言 π(x) ~ li(x) ~ x/ln x。这是**数值对照**（L2），
    在有限范围内吻合不构成证明。
    """
    is_prime = sieve_is_prime(limit)
    pi = 0
    rows = []
    checkpoints = [10 ** k for k in range(2, len(str(limit)) + 1) if 10 ** k <= limit]
    cp = set(checkpoints)
    max_li_err = 0.0
    max_xln_err = 0.0
    for i in range(2, limit + 1):
        if is_prime[i]:
            pi += 1
        if i in cp:
            approx1 = i / math.log(i)
            approx2 = logarithmic_integral(i)
            e1 = abs(pi - approx1) / pi
            e2 = abs(pi - approx2) / pi
            max_li_err = max(max_li_err, e2)
            max_xln_err = max(max_xln_err, e1)
            rows.append({
                "x": i, "pi_x": pi,
                "x_over_ln_x": round(approx1, 2),
                "li_x": round(approx2, 2),
                "rel_err_x_over_ln": round(e1, 6),
                "rel_err_li": round(e2, 6),
            })
    last = rows[-1] if rows else None
    return {
        "limit": limit,
        "rows": rows,
        "max_rel_err_li": round(max_li_err, 6),
        "max_rel_err_x_over_ln": round(max_xln_err, 6),
        # 最大误差发生在最小检查点（小 x 处两个近似都很差），代表性有限；
        # 故额外给出**最大 x 处**的对比，那里才反映渐近行为。
        "at_largest_x": last,
        "note": (
            "必须区分小 x 与大 x：li(x) 的**最大**相对误差出现在最小检查点，"
            "因为 li(x)=x/lnx + x/ln²x + ... 多出的高阶项在小 x 处占比很大，"
            "会明显高估（例如 x=100 时 li 的误差反而大于 x/ln x）。"
            "但在 x>=1000 之后 li 的优势稳定显现并随 x 增大而放大，"
            "到最大检查点处 li 的误差远小于 x/ln x（见 at_largest_x）。"
            "本结果仅为有限范围内的数值对照，不构成证明。"
        ),
    }


def collatz_stopping_time(n: int, cache: dict[int, int] | None = None) -> int:
    """Collatz（3n+1）总停止时间：首次到达 1 所需步数。"""
    if cache is None:
        cache = {1: 0}
    if n in cache:
        return cache[n]
    path = []
    m = n
    while m not in cache:
        path.append(m)
        m = m // 2 if m % 2 == 0 else 3 * m + 1
    base = cache[m]
    for i, v in enumerate(reversed(path)):
        base += 1
        if v > 1:
            cache[v] = base
    return cache[n]


def collatz_modular_profile(n_max: int = 20000, modulus: int = 6) -> dict:
    """按 n mod m 分组统计 Collatz 停止时间分布（最朴素的模类分析）。

    用途：观察是否存在某一剩余类系统性地具有更长/更短的轨道。
    这是描述性统计，**不提供任何证明方向**。
    """
    cache: dict[int, int] = {1: 0}
    buckets: dict[int, list[int]] = {}
    for n in range(1, n_max + 1):
        t = collatz_stopping_time(n, cache)
        buckets.setdefault(n % modulus, []).append(t)
    stats = []
    for r in sorted(buckets):
        vals = buckets[r]
        stats.append({
            "residue": r,
            "count": len(vals),
            "mean_steps": round(sum(vals) / len(vals), 4),
            "max_steps": max(vals),
        })
    overall = sum(sum(v) for v in buckets.values()) / n_max
    return {
        "n_max": n_max, "modulus": modulus,
        "overall_mean_steps": round(overall, 4),
        "by_residue": stats,
        "note": "模类均值差异反映停止时间的算术结构，但**不构成** Collatz 猜想的证明方向；"
                "该猜想仍完全未解。",
    }
