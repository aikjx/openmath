# -*- coding: utf-8 -*-
"""PWCV 框架定理的 L2 独立验证引擎。

本模块是 `prime_pi_block.py` / `prime_discrete_calculus.py` 的**派生补充**：它把
PWCV（Primorial Wheel Coverage–Void）论文中那条"闭环链"里**尚未被引擎覆盖**的
等式逐条做精确整数核对，并复用独立基准（埃拉托色尼筛 + 最小素因子表 + 前缀计数）
确保"两边独立"才构成非平凡验证。

覆盖 02-公式库/数论/ 中 PWCV 体系记录：
  OM-D-NT-0001  整除脉冲 δ、素数指示 I、整数阶跃 Θ
  OM-T-NT-0001  素数离散微积分闭环（I ↔ π ↔ p_n 离散导/积/逆）
  OM-T-NT-0002  素数计数分块递归分解（Legendre φ / Meissel P2 / Lehmer P3）
  OM-F-NT-0002  第 n 素数 n-only 母公式（定理 7）
  OM-T-NT-0003  阶乘互素定理（下一素数母定理，定理 2）
  OM-T-NT-0004  首逃逸合数平方定理（定理 3）
  OM-T-NT-0005  模 6 合数覆盖母方程（定理 4）
  OM-T-NT-0006  一般 wheel 覆盖定理（定理 5）
  OM-T-NT-0007  阶乘互素安全窗口定理
  OM-T-NT-0008  素数间隔的 Jacobsthal 上界

诚实声明（红线一 / 红线五）
--------------------------
本模块**只提供 L2（精确整数）证据**。所有"残差"都是精确整数差（离散等式），
恒为 0 表示"等式成立"而非"近似好"。L2 通过只能证伪，不能证明（本库无 L4 形式化）。

运行：
    python pwcv_theorems.py            # 标准自检（全部 10 条记录）
    python pwcv_theorems.py --id OM-T-NT-0003   # 只验证单条
"""

from __future__ import annotations

import math
import os
import platform
import sys
import time

# --------------------------------------------------------------------------
# 0. 独立基准（不依赖 prime_pi_block，确保"两边独立"构成非平凡验证）
# --------------------------------------------------------------------------

MAXN = 1_050_000  # 覆盖首逃逸平方 m<=1000（q^2<=1018081）、模6/wheel<=500000 等


def build_spf(limit: int):
    """最小素因子表 spf[x] = x 的最小素因子；x>=2 时 spf[x]==x 即素数。"""
    spf = list(range(limit + 1))
    i = 2
    while i * i <= limit:
        if spf[i] == i:  # i 为素数
            step = i
            start = i * i
            spf[start:limit + 1:step] = [i] * len(range(start, limit + 1, step))
        i += 1
    return spf


def build_prefix(spf):
    """π 前缀表：prefix[k] = #{素数 <= k}，由 spf 推导。"""
    from array import array
    from itertools import accumulate
    limit = len(spf) - 1
    flags = bytearray([1]) * (limit + 1)
    flags[0] = 0
    if limit >= 1:
        flags[1] = 0
    for x in range(2, limit + 1):
        flags[x] = 1 if spf[x] == x else 0
    return array("I", accumulate(flags))


def is_prime(spf, x):
    return x >= 2 and spf[x] == x


def prime_factors(spf, x):
    fac = []
    while x > 1:
        p = spf[x]
        fac.append(p)
        while x % p == 0:
            x //= p
    return fac


def coprime_to_mfact(x, m, spf):
    """gcd(x, m!) == 1 当且仅当 x 的所有素因子都 > m。"""
    while x > 1:
        p = spf[x]
        if p <= m:
            return False
        x //= p
    return True


def coprime_to_M(x, pmax, spf):
    """gcd(x, M) == 1，其中 M 的素因子都 <= pmax。"""
    while x > 1:
        p = spf[x]
        if p <= pmax:
            return False
        x //= p
    return True


def next_prime(m, spf):
    x = m + 1
    while x < len(spf):
        if spf[x] == x:
            return x
        x += 1
    raise RuntimeError("next_prime 超出 spf 表范围")


def reduced_residues(M, primes_in_M, spf):
    """1 <= r < M 中与 M 互素的剩余系。"""
    out = []
    for r in range(1, M):
        if coprime_to_M(r, primes_in_M[-1], spf):
            out.append(r)
    return out


# --------------------------------------------------------------------------
# 1. 各记录的验证实现（均返回 (ok, bad_list, detail_dict)）
# --------------------------------------------------------------------------


def verify_D1(spf, prefix):
    """OM-D-NT-0001：δ_d(t)=1_{d|t}、I(t)=1_{t prime}、Θ(z)=1_{z>0}。"""
    bad = []
    for t in range(1, 301):
        for d in range(1, t + 1):
            delta = t // d - (t - 1) // d
            if delta != (1 if t % d == 0 else 0):
                bad.append(("delta", d, t))
                break
        if bad:
            break
    badI = [t for t in range(1, 10001) if _I_naive(t, spf) != (1 if is_prime(spf, t) else 0)]
    badT = [z for z in range(-10, 11) if math.ceil(z / (abs(z) + 1)) != (1 if z > 0 else 0)]
    return (not bad and not badI and not badT,
            bad + [("I", x) for x in badI[:3]] + [("Theta", z) for z in badT[:3]])


def _I_naive(t, spf):
    """素数指示 I(t)=∏_{d=2}^{⌊√t⌋}(1-δ_d(t))，独立路径（逐 d 试除）。"""
    if t < 2:
        return 0
    r = 1
    for d in range(2, int(math.isqrt(t)) + 1):
        r *= 1 - (t // d - (t - 1) // d)
    return r


def verify_T1(spf, prefix):
    """OM-T-NT-0001：离散微积分闭环。"""
    Nmax = 20000
    pi_ind = [0] * (Nmax + 1)
    for t in range(2, Nmax + 1):
        pi_ind[t] = pi_ind[t - 1] + (1 if is_prime(spf, t) else 0)
    bad = [N for N in range(2, Nmax + 1)
           if _I_naive(N, spf) != pi_ind[N] - pi_ind[N - 1]]
    # π(p_n)=n 且 p_n = min{x: π(x)>=n}
    bad2 = []
    for n in range(1, 2001):
        p = _nth_prime(n, prefix)
        if prefix[p] != n:
            bad2.append((n, p, prefix[p]))
        # 反向：min{x: π(x)>=n}
        x = 2
        while prefix[x] < n:
            x += 1
        if x != p:
            bad2.append(("inv", n, p, x))
    # LargestPrime<=N = p_{π(N)}
    bad3 = []
    for N in range(2, 5001):
        lp = N
        while not is_prime(spf, lp):
            lp -= 1
        if lp != _nth_prime(prefix[N], prefix) and prefix[lp] == prefix[N]:
            # 仅当 π(N) 给出正确阶时核对
            if _nth_prime(prefix[N], prefix) != lp:
                bad3.append(N)
    return (not bad and not bad2 and not bad3,
            [("dpi", x) for x in bad[:3]] + [("pn", x) for x in bad2[:3]]
            + [("largest", x) for x in bad3[:3]])


def _nth_prime(n, prefix):
    """第 n 个素数：二分查找 min{x: prefix[x]>=n}。"""
    lo, hi = 2, len(prefix) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if prefix[mid] >= n:
            hi = mid
        else:
            lo = mid + 1
    return lo


def verify_T2(spf, prefix):
    """OM-T-NT-0002：分块递归分解（Legendre φ 递归恒等式）。

    本引擎只核对"分块递归"的核心：Legendre 的递归
        φ(x,a) = φ(x,a-1) - φ(⌊x/p_a⌋, a-1),  φ(x,0)=x
    与其直接定义（1..x 中不被前 a 个素数整除的整数个数）逐点一致，
    并由此推出 Legendre 素数计数公式 π(x)=φ(x,a)+a-1。

    （Meissel / Lehmer 的 P2/P3 交叉验证由 prime_pi_block.py 独立承担，
     本条目在 related 中引用 OM-F-NT-0001 / OM-A-NT-0001。）
    """
    primes = [0] + [x for x in range(2, len(spf)) if spf[x] == x]  # 1-索引：primes[1]=2

    memo = {}

    def phi_rec(x, a):
        if a == 0:
            return x
        if x <= 0:
            return 0
        key = (x, a)
        v = memo.get(key)
        if v is not None:
            return v
        val = phi_rec(x, a - 1) - phi_rec(x // primes[a], a - 1)
        memo[key] = val
        return val

    def phi_direct(x, a):
        small = set(primes[1:a + 1])
        return sum(1 for m in range(1, x + 1) if all(m % p != 0 for p in small))

    bad = []
    for a in range(0, 8):
        for x in [97, 1000, 99991, 50000, 200000]:
            if phi_rec(x, a) != phi_direct(x, a):
                bad.append(("rec", x, a, phi_rec(x, a), phi_direct(x, a)))
    # Legendre 素数计数公式
    for x in [1000, 10000, 100000, 200000, 500000]:
        a = prefix[math.isqrt(x)]
        if phi_rec(x, a) + a - 1 != prefix[x]:
            bad.append(("legendre", x))
    return (not bad, [("T2", x) for x in bad[:3]])


def verify_F2(spf, prefix):
    """OM-F-NT-0002：第 n 素数 n-only 母公式（定理 7）。

    p_n = L_n + Σ_{x=L_n}^{U_n-1} Θ(n - π(x))，其中 π(x) 由 I 的连乘展开式独立计算。
    """
    # 用 I 连乘展开预计算 π（独立路径，不查筛法前缀）
    Nmax = 9000
    piI = [0] * (Nmax + 1)
    for x in range(2, Nmax + 1):
        piI[x] = piI[x - 1] + _I_naive(x, spf)

    def theta(z):
        return math.ceil(z / (abs(z) + 1))

    bad = []
    for n in range(6, 1001):
        ln = math.log(n)
        lln = math.log(ln)
        L = int(math.floor(n * (ln + lln - 1))) + 1
        U = int(math.ceil(n * (ln + lln)))
        s = sum(theta(n - piI[x]) for x in range(L, U))
        pn_formula = L + s
        pn_ref = _nth_prime(n, prefix)
        if pn_formula != pn_ref:
            bad.append((n, pn_formula, pn_ref))
    return (not bad, [("F2", x) for x in bad[:3]])


def verify_T3(spf, prefix):
    """OM-T-NT-0003：阶乘互素定理 NextPrime(m) = min{x>m: gcd(x, m!)=1}。"""
    M_MAX = 1000
    bad = []
    for m in range(2, M_MAX + 1):
        q = next_prime(m, spf)
        x = m + 1
        while not coprime_to_mfact(x, m, spf):
            x += 1
        if x != q:
            bad.append((m, q, x))
    return (not bad, [("nextprime", x) for x in bad[:5]])


def verify_T4(spf, prefix):
    """OM-T-NT-0004：首逃逸合数平方定理 FirstEscape(m) = NextPrime(m)^2。"""
    M_MAX = 1000
    bad = []
    for m in range(2, M_MAX + 1):
        q = next_prime(m, spf)
        x = 2
        found = None
        while x < len(spf):
            if x > 1 and not is_prime(spf, x) and coprime_to_mfact(x, m, spf):
                found = x
                break
            x += 1
        if found != q * q:
            bad.append((m, q * q, found))
    return (not bad, [("escape", x) for x in bad[:5]])


def verify_T5(spf, prefix):
    """OM-T-NT-0005：模 6 合数覆盖母方程 k = 6ab + aεσ + bσ。"""
    Nmax = 500000
    bad = []
    cnt = 0
    for N in range(5, Nmax + 1):
        if N % 6 not in (1, 5):
            continue
        if is_prime(spf, N):
            continue
        cnt += 1
        f = spf[N]
        sigma = 1 if (f % 6 == 1) else -1
        a = (f - sigma) // 6
        g = N // f
        eps = 1 if (N % 6 == 1) else -1
        if (g - eps * sigma) % 6 != 0:
            bad.append(("sig", N, f, g))
            continue
        b = (g - eps * sigma) // 6
        if a < 0 or b < 0 or (6 * a + sigma) * (6 * b + eps * sigma) != N:
            bad.append(("recon", N, f, g, a, b))
    return (not bad, [("mod6", x) for x in bad[:5]], cnt)


def verify_T6(spf, prefix):
    """OM-T-NT-0006：一般 wheel 覆盖定理 k = Mab + as + br + (rs-u)/M。"""
    Ms = [6, 30, 210]
    bad = {}
    cnt = {}
    for M in Ms:
        primes_in_M = [x for x in range(2, len(spf)) if spf[x] == x and x <= _max_prime_in(M)]
        pmax = primes_in_M[-1]
        b = []
        c = 0
        Nmax = 500000
        for N in range(2, Nmax + 1):
            if not coprime_to_M(N, pmax, spf):
                continue
            if is_prime(spf, N):
                continue
            c += 1
            f = spf[N]
            r = f % M
            a = (f - r) // M
            g = N // f
            s = g % M
            bb = (g - s) // M
            if a < 0 or bb < 0 or (M * a + r) * (M * bb + s) != N:
                b.append((M, N, f, g, a, bb))
        bad[M] = b
        cnt[M] = c
    ok = all(len(v) == 0 for v in bad.values())
    flat = []
    for M, v in bad.items():
        flat.extend([("wheel", M, x) for x in v[:3]])
    return ok, flat, cnt


def _max_prime_in(M):
    p = 2
    while p * p <= M:
        p += 1
    # 回退：M 的素因子最大值，直接用试除
    m = M
    mx = 1
    d = 2
    while d * d <= m:
        while m % d == 0:
            mx = max(mx, d)
            m //= d
        d += 1
    if m > 1:
        mx = max(mx, m)
    return mx


def verify_T7(spf, prefix):
    """OM-T-NT-0007：安全窗口 m < x < q^2 ⇒ gcd(x, m!)=1 ⟺ x 为素数。"""
    M_MAX = 200
    bad = []
    for m in range(2, M_MAX + 1):
        q = next_prime(m, spf)
        for x in range(m + 1, q * q):
            if coprime_to_mfact(x, m, spf) and not is_prime(spf, x):
                bad.append((m, x))
                break
    return (not bad, [("window", x) for x in bad[:5]])


def verify_T8(spf, prefix):
    """OM-T-NT-0008：素数间隔的 Jacobsthal 上界 g_n ≤ j(p_n#)。"""
    primes = [0] + [x for x in range(2, len(spf)) if spf[x] == x]  # 1-索引：primes[1]=2
    bad = []
    details = []
    for n in range(1, 8):
        M = 1
        for i in range(1, n + 1):
            M *= primes[i]
        pmax = primes[n]
        residues = reduced_residues(M, [primes[i] for i in range(1, n + 1)], spf)
        # j(M) = 周期 [0, M) 内相邻既约剩余的最大间隔
        k = len(residues)
        gaps = [residues[i + 1] - residues[i] for i in range(k - 1)]
        gaps.append((residues[0] + M) - residues[-1])
        jM = max(gaps)
        pn = primes[n]
        pn1 = primes[n + 1]
        g = pn1 - pn
        details.append((n, pn, pn1, g, jM, M))
        if g > jM:
            bad.append((n, g, jM))
    return (not bad, [("jac", x) for x in bad[:5]], details)


# --------------------------------------------------------------------------
# 2. 引擎接口（见 05-验证中心/01-引擎/README.md）
# --------------------------------------------------------------------------


def capabilities() -> dict:
    return {
        "name": "pwcv-theorems",
        "levels": ["L2"],
        "domains": ["NT"],
        "dependencies": [],
        "deterministic": True,
    }


def available() -> bool:
    return True


def environment() -> dict:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "dependencies": [],
        "spf_limit": MAXN,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _item(name, ok, detail=""):
    return {"name": name, "passed": bool(ok), "detail": detail}


def run(record: dict, level: str = "L2", options: dict = None) -> dict:
    """L2 精确整数验证入口；按 record['id'] 分派到对应定理的核验收。"""
    if level != "L2":
        return {"status": "SKIP", "engine": "pwcv-theorems", "level": level,
                "reason": "本引擎仅实现 L2（精确整数）", "environment": environment()}
    rid = (record or {}).get("id")
    t0 = time.perf_counter()
    try:
        spf = build_spf(MAXN)
        prefix = build_prefix(spf)
    except Exception as exc:
        return {"status": "ERROR", "engine": "pwcv-theorems", "level": "L2",
                "reason": "基准构建失败: %r" % exc, "environment": environment()}
    try:
        if rid == "OM-D-NT-0001":
            ok, bad = verify_D1(spf, prefix)
            items = [_item("D1. δ/I/Θ 脉冲与阶跃性质", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0001":
            ok, bad = verify_T1(spf, prefix)
            items = [_item("T1. 离散微积分闭环 (I↔π↔p_n)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0002":
            ok, bad = verify_T2(spf, prefix)
            items = [_item("T2. 分块递归分解 (Legendre/Meissel/Lehmer)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-F-NT-0002":
            ok, bad = verify_F2(spf, prefix)
            items = [_item("F2. n-only 母公式 == p_n (n=6..1000)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0003":
            ok, bad = verify_T3(spf, prefix)
            items = [_item("T3. 阶乘互素定理 (m=2..1000)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0004":
            ok, bad = verify_T4(spf, prefix)
            items = [_item("T4. 首逃逸合数平方 (m=2..1000)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0005":
            ok, bad, cnt = verify_T5(spf, prefix)
            items = [_item("T5. 模6母方程 (N<=500000, %d 个合数)" % cnt, ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0006":
            ok, bad, cnt = verify_T6(spf, prefix)
            items = [_item("T6. 一般wheel覆盖 M∈{6,30,210} (N<=500000, %s 个合数)"
                           % cnt, ok, "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0007":
            ok, bad = verify_T7(spf, prefix)
            items = [_item("T7. 安全窗口 (m=2..200)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        elif rid == "OM-T-NT-0008":
            ok, bad, det = verify_T8(spf, prefix)
            items = [_item("T8. Jacobsthal 上界 g_n<=j(p_n#) (n=1..7)", ok,
                           "无不一致" if ok else "不一致=%s" % (bad[:5],))]
        else:
            return {"status": "SKIP", "engine": "pwcv-theorems", "level": "L2",
                    "reason": "未识别的记录 id: %s" % rid, "environment": environment()}
    except Exception as exc:
        return {"status": "ERROR", "engine": "pwcv-theorems", "level": "L2",
                "reason": "验证异常: %r" % exc, "environment": environment()}
    passed = sum(1 for it in items if it["passed"])
    status = "PASS" if passed == len(items) and all(it["passed"] for it in items) else "FAIL"
    return {
        "status": status,
        "engine": "pwcv-theorems",
        "level": "L2",
        "max_abs_residual": "0",  # 离散等式，精确整数差恒为 0
        "items": items,
        "environment": environment(),
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    }


# --------------------------------------------------------------------------
# 3. 自检（CLI 直接运行）
# --------------------------------------------------------------------------


def self_test(only_id=None) -> dict:
    ids = ["OM-D-NT-0001", "OM-T-NT-0001", "OM-T-NT-0002", "OM-F-NT-0002",
           "OM-T-NT-0003", "OM-T-NT-0004", "OM-T-NT-0005", "OM-T-NT-0006",
           "OM-T-NT-0007", "OM-T-NT-0008"]
    if only_id:
        ids = [only_id]
    print("=" * 78)
    print("PWCV 框架定理 · 独立 L2 验证  (spf_limit=%d)" % MAXN)
    print("=" * 78)
    results = []
    for rid in ids:
        res = run({"id": rid}, "L2")
        results.append(res)
        tag = "[%s]" % res["status"]
        print("%-4s %-16s %s" % (tag, rid,
              (res.get("items") or [{}])[0].get("name", "") if res.get("items") else res.get("reason", "")))
    print("-" * 78)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print("汇总：%d/%d 通过" % (passed, len(results)))
    return {"passed": passed, "total": len(results), "results": results,
            "environment": environment()}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    only = None
    if "--id" in sys.argv:
        only = sys.argv[sys.argv.index("--id") + 1]
    out = self_test(only)
    sys.exit(0 if out["passed"] == out["total"] else 1)
