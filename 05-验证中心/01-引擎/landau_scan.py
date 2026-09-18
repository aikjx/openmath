# -*- coding: utf-8 -*-
"""Landau 开放问题扫描引擎（L2：精确整数 + 高精度数值）。

本引擎覆盖 02-公式库/数论/ 中**此前没有任何引擎支撑**的四个条目：

  OM-F-NT-0003  区间素数计数的 Legendre 窗口恒等式
  OM-F-NT-0004  n^2+1 序列的 Legendre-Mobius 筛恒等式
  OM-P-NT-0003  Landau 第三问题（Legendre 猜想）—— 状态 OPEN
  OM-P-NT-0004  Landau 第四问题（n^2+1 素数）—— 状态 OPEN

设计原则（红线一 / 红线五）
--------------------------
1. **只提供 L2**。数值/枚举一致只能**证伪**，不能证明（本库无 L4 形式化）。
2. **开放问题条目（OM-P-*）永不返回 PASS=已解决**。其检查结果一律表述为
   "在范围内未发现反例"，并在 notes 中显式写出"范围外未知"。
3. **两条独立路径**：Legendre 窗口用「筛法前缀差分」与「phi 分块递归」两条
   不同算法交叉；n^2+1 的 Mobius 筛恒等式用「逐 n 试除」与「Mobius 求和」
   两条不同算法交叉。同源重复不算验证。
4. **残差而非布尔**：所有检查项都给出可比对的数字。

运行：
    python landau_scan.py                 # 全部自检
    python landau_scan.py --id OM-F-NT-0004
    python landau_scan.py --json
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from array import array
from itertools import accumulate

# --------------------------------------------------------------------------
# 0. 常量与外部锚点
# --------------------------------------------------------------------------

# OEIS A006880：pi(10^k)，用作筛法的外部锚（非本程序生成）
PI_10K = {
    1: 4, 2: 25, 3: 168, 4: 1229, 5: 9592,
    6: 78498, 7: 664579,
}

# 孪生素数常数 C_2（Hardy-Littlewood）
C2 = 0.66016181584686957392781211001455577843262336028473341331945

# Legendre 窗口扫描上界：(n+1)^2 <= WIN_LIMIT
WIN_N = 2000
WIN_LIMIT = (WIN_N + 1) ** 2          # 4_004_001

# phi 递归交叉验证的窗口上界（递归节点随 a 增长，取小规模）
PHI_N = 300

# n^2+1 扫描上界
N2_N = 20000                          # n^2+1 <= 4.0e8，确定性 MR 判定
N2_MOBIUS_N = 500                     # Mobius 恒等式精确核对范围
N2_MOBIUS_Y = (10, 20, 30, 42)        # 筛截断 Y（素数集合规模可控）

_SIEVE_CACHE = {}


# --------------------------------------------------------------------------
# 1. 基准：bytearray 筛 + 前缀计数
# --------------------------------------------------------------------------

def sieve_prefix(limit):
    """返回 (flags, prefix)：flags[x]==1 表示 x 为素数；prefix[k]=pi(k)。"""
    cached = _SIEVE_CACHE.get(limit)
    if cached is not None:
        return cached
    flags = bytearray([1]) * (limit + 1)
    if limit >= 0:
        flags[0] = 0
    if limit >= 1:
        flags[1] = 0
    i = 2
    while i * i <= limit:
        if flags[i]:
            start = i * i
            flags[start:limit + 1:i] = bytearray(len(range(start, limit + 1, i)))
        i += 1
    prefix = array("I", accumulate(flags))
    _SIEVE_CACHE[limit] = (flags, prefix)
    return flags, prefix


def primes_upto(limit):
    flags, _ = sieve_prefix(limit)
    return [i for i in range(2, limit + 1) if flags[i]]


# --------------------------------------------------------------------------
# 2. Legendre phi（递归 + 记忆化），用于与筛法交叉
# --------------------------------------------------------------------------

_PHI_MEMO = {}


def phi_legendre(x, a, primes):
    """phi(x,a) = #{1<=n<=x : n 不被前 a 个素数整除}（含 1）。"""
    if a == 0:
        return x
    key = (x, a)
    hit = _PHI_MEMO.get(key)
    if hit is not None:
        return hit
    val = phi_legendre(x, a - 1, primes) - phi_legendre(x // primes[a - 1], a - 1, primes)
    _PHI_MEMO[key] = val
    return val


# --------------------------------------------------------------------------
# 3. n^2+1 相关
# --------------------------------------------------------------------------

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime_mr(n):
    """确定性 Miller-Rabin：对 n < 3.317e24 正确（基底集为标准确定集）。"""
    if n < 2:
        return False
    for p in _MR_BASES:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def omega_p(p):
    """#{n mod p : p | n^2+1}。p=2 -> 1；p≡1(4) -> 2；p≡3(4) -> 0。"""
    if p == 2:
        return 1
    return 2 if p % 4 == 1 else 0


def omega_d(d, primes):
    """由 CRT：#{n mod d : d | n^2+1} = prod omega(p)（d 无平方因子）。"""
    w = 1
    for p in primes:
        if d % p == 0:
            w *= omega_p(p)
            if w == 0:
                return 0
    return w


def squarefree_divisors(primes):
    """P(Y)=prod primes 的全部无平方因子除数，按位枚举。"""
    out = []
    for mask in range(1 << len(primes)):
        d = 1
        mu = 1
        for i, p in enumerate(primes):
            if mask >> i & 1:
                d *= p
                mu = -mu
        out.append((d, mu))
    out.sort()
    return out


def li_func(x, power=1):
    """∫_2^x dt/(log t)^power，复合 Simpson（纯标准库，双精度）。"""
    if x <= 2:
        return 0.0

    def f(t):
        return 1.0 / (math.log(t) ** power)

    n = 20000
    if n % 2:
        n += 1
    h = (x - 2.0) / n
    total = f(2.0) + f(float(x))
    for i in range(1, n):
        total += (4.0 if i % 2 else 2.0) * f(2.0 + i * h)
    return total * h / 3.0


# --------------------------------------------------------------------------
# 4. 检查项：OM-F-NT-0003 区间素数计数（Legendre 窗口）
# --------------------------------------------------------------------------

def check_F3():
    items = []
    flags, prefix = sieve_prefix(WIN_LIMIT)

    # 4.1 筛法外部锚：pi(10^k) 对齐 OEIS A006880
    bad = []
    anchored = []
    for k, expect in sorted(PI_10K.items()):
        if 10 ** k > WIN_LIMIT:
            continue
        got = prefix[10 ** k]
        anchored.append(k)
        if got != expect:
            bad.append((k, got, expect))
    items.append({
        "name": "F3.1 筛法外部锚 pi(10^k) == OEIS A006880（k=%s）" % anchored,
        "passed": not bad,
        "detail": ("全部相等（k=%s）" % anchored if not bad else "不一致=%s" % bad[:5]),
    })

    # 4.2 恒等式 c(n) = pi((n+1)^2) - pi(n^2)：前缀差分 vs 逐点直接计数
    bad = []
    minc = None
    argmin = None
    for n in range(1, WIN_N + 1):
        lo = n * n
        hi = (n + 1) ** 2
        diff = prefix[hi] - prefix[lo]
        direct = sum(flags[lo + 1:hi + 1])
        if diff != direct:
            bad.append((n, diff, direct))
        if minc is None or diff < minc:
            minc = diff
            argmin = n
    items.append({
        "name": "F3.2 窗口恒等式 c(n)=pi((n+1)^2)-pi(n^2) （n<=%d，两法交叉）" % WIN_N,
        "passed": not bad,
        "detail": ("全部相等；min c(n)=%d @ n=%d" % (minc, argmin) if not bad
                   else "不一致=%s" % bad[:5]),
    })

    # 4.3 分块形式：c(n) = phi((n+1)^2, a) - phi(n^2, a)，a = pi(n+1)，n >= 2
    #     （n=1 时窗口含素数 2 = n+1，会被筛掉，故本式从 n=2 起成立）
    primes = primes_upto(PHI_N + 2)
    bad = []
    for n in range(2, PHI_N + 1):
        a = prefix[n + 1]
        val = phi_legendre((n + 1) ** 2, a, primes) - phi_legendre(n * n, a, primes)
        true = prefix[(n + 1) ** 2] - prefix[n * n]
        if val != true:
            bad.append((n, val, true))
    items.append({
        "name": "F3.3 分块恒等式 c(n)=phi((n+1)^2,a)-phi(n^2,a), a=pi(n+1) （2<=n<=%d）" % PHI_N,
        "passed": not bad,
        "detail": ("全部相等（离散残差 0）" if not bad else "不一致=%s" % bad[:5]),
    })
    return items, minc, argmin


# --------------------------------------------------------------------------
# 5. 检查项：OM-F-NT-0004 n^2+1 的 Legendre-Mobius 筛恒等式
# --------------------------------------------------------------------------

def check_F4():
    items = []
    N = N2_MOBIUS_N

    def has_small_factor(n, plist):
        v = n * n + 1
        for p in plist:
            if v % p == 0:
                return True
        return False

    for Y in N2_MOBIUS_Y:
        plist = primes_upto(Y)
        divs = squarefree_divisors(plist)

        # 路径 A：逐 n 试除，判 gcd(n^2+1, P(Y)) == 1
        direct = 0
        for n in range(1, N + 1):
            if not has_small_factor(n, plist):
                direct += 1

        # 路径 B：Mobius 求和 sum_{d | P(Y)} mu(d) * C_d(N)
        total = 0
        crt_bad = []
        for d, mu in divs:
            cnt = 0
            for n in range(1, N + 1):
                if (n * n + 1) % d == 0:
                    cnt += 1
            total += mu * cnt
            # CRT 结构：C_d(N) = omega(d)*floor(N/d) + r_d, 0 <= r_d <= omega(d)
            w = omega_d(d, plist)
            if w > 0:
                r = cnt - w * (N // d)
                if r < 0 or r > w:
                    crt_bad.append((d, cnt, w, r))
        ok = (total == direct) and not crt_bad
        items.append({
            "name": "F4.Y=%d Mobius 筛恒等式 A_Y(%d)（试除法 vs Mobius 求和）" % (Y, N),
            "passed": ok,
            "detail": ("两法均得 %d，且 C_d(N)=omega(d)floor(N/d)+r_d 余数界成立"
                       % direct if ok else "Mobius=%d 直接=%d CRT越界=%s"
                       % (total, direct, crt_bad[:3])),
        })

    # 完备化恒等式：Y >= N+1 时
    #   A(N) = A_Y(N) + E(N,Y),
    #   E(N,Y) = #{n<=N : n^2+1 为素数且 n^2+1 <= Y}
    # 其中 A_Y(N)=#{n<=N : gcd(n^2+1,P(Y))=1}。
    # 注意：Y 会把"n^2+1 自身就是 <=Y 的素数"这类 n 一并筛掉，故必须补 E。
    Yfull = N + 1
    plist = primes_upto(Yfull)
    cnt_sieved = 0
    cnt_prime = 0
    cnt_small_prime = 0
    for n in range(1, N + 1):
        v = n * n + 1
        if not has_small_factor(n, plist):
            cnt_sieved += 1
        if is_prime_mr(v):
            cnt_prime += 1
            if v <= Yfull:
                cnt_small_prime += 1
    ok = (cnt_sieved + cnt_small_prime == cnt_prime)
    items.append({
        "name": "F4.完备化恒等式 A(N)=A_Y(N)+E(N,Y)（Y=N+1=%d）" % Yfull,
        "passed": ok,
        "detail": ("A_Y=%d, E=%d, A_Y+E=%d, 素性判定 A=%d（残差 %d）"
                   % (cnt_sieved, cnt_small_prime, cnt_sieved + cnt_small_prime,
                      cnt_prime, cnt_sieved + cnt_small_prime - cnt_prime)),
    })

    # 主项 / 余项规模对比（筛法失效的可量化证据）
    #   主项  M(Y) = N * prod_{p<=Y}(1 - omega(p)/p)
    #   余项上界 R(Y) = sum_{d|P(Y)} omega(d) = prod_{p<=Y}(1 + omega(p))
    rows = []
    for Y in (42, 100, N):
        plist = primes_upto(Y)
        log10_err = 0.0
        main_prod = 1.0
        for p in plist:
            log10_err += math.log10(1.0 + omega_p(p))
            main_prod *= (1.0 - omega_p(p) / float(p))
        main_term = N * main_prod
        rows.append("Y=%d: 余项10^%.1f, 主项%.2f, 比值10^%.1f"
                    % (Y, log10_err, main_term,
                       log10_err - math.log10(max(main_term, 1e-12))))
    items.append({
        "name": "F4.余项爆炸：prod(1+omega(p)) 相对主项 N*prod(1-omega(p)/p) 的量级",
        "passed": True,  # 度量项，不是判定项
        "detail": ("N=%d；" % N) + "；".join(rows)
                  + " —— 余项尺度随 Y 指数增长而主项缓慢衰减，"
                    "这就是筛法在该问题上给不出非平凡下界的可量化形式",
    })
    return items


# --------------------------------------------------------------------------
# 6. 检查项：OM-P-NT-0003 Legendre 猜想（OPEN）
# --------------------------------------------------------------------------

def check_P3(minc=None, argmin=None):
    items = []
    if minc is None:
        _, prefix = sieve_prefix(WIN_LIMIT)
        minc = None
        for n in range(1, WIN_N + 1):
            c = prefix[(n + 1) ** 2] - prefix[n * n]
            if minc is None or c < minc:
                minc = c
                argmin = n
    items.append({
        "name": "P3.1 扫描区域内无反例：min_{n<=%d} c(n)=%d @ n=%d（c(n)>=1）"
                % (WIN_N, minc, argmin),
        "passed": minc >= 1,
        "detail": "范围内未发现反例；范围外未知（本项只可证伪，不构成证明）",
    })

    # BHP（Baker-Harman-Pintz, 2001）: [x, x+x^0.525] 内有素数，x 充分大。
    # Legendre 窗口长度 = 2n+1 = 2*sqrt(x)+1，需求指数 1/2 < 0.525。
    # 解 n^1.05 = 2n+1，得临界 n*（超出后窗口严格短于 BHP 所需长度）
    lo, hi = 2.0, 1e12
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if mid ** 1.05 > 2 * mid + 1:
            hi = mid
        else:
            lo = mid
    nstar = (lo + hi) / 2.0
    items.append({
        "name": "P3.2 需求指数 1/2 与当前最优 0.525 的量化差距（BHP）",
        "passed": True,  # 度量项
        "detail": ("窗口长度 2*sqrt(x)+1 对应指数 1/2；BHP 需 0.525。"
                   "n^1.05 超过 2n+1 的临界点约 n*=%.3e（x*≈%.3e），"
                   "此后 Legendre 窗口严格短于任何已知无条件短区间结果"
                   % (nstar, nstar * nstar)),
    })
    return items


# --------------------------------------------------------------------------
# 7. 检查项：OM-P-NT-0004 n^2+1 素数（OPEN）+ Bateman-Horn 数值（仅证伪）
# --------------------------------------------------------------------------

def check_P4():
    items = []
    N = N2_N
    cnt = 0
    first = []
    for n in range(1, N + 1):
        if is_prime_mr(n * n + 1):
            cnt += 1
            if len(first) < 8:
                first.append(n)
    items.append({
        "name": "P4.1 计数 A(%d)=#{n<=N : n^2+1 素数}（确定性 Miller-Rabin）" % N,
        "passed": True,  # 枚举事实，非判定
        "detail": "A(N)=%d，前若干个 n=%s" % (cnt, first),
    })

    linv = li_func(float(N))
    ratio_li = cnt / linv if linv else float("nan")
    ratio_nl = cnt * math.log(N) / N
    items.append({
        "name": "P4.2 Bateman-Horn 渐近的偏移（仅证伪：常数收敛极慢）",
        "passed": True,  # 渐近式无法用有限范围判定真/false，仅记录偏差
        "detail": ("A(N)/Li(N)=%.6f；A(N)/(N/log N)=%.6f。"
                   "BH 预言二者趋于 C_BH/2（Euler 积条件收敛、截断振荡），"
                   "有限 N 的偏差不构成成立/否定的证据" % (ratio_li, ratio_nl)),
    })

    # 局部因子截断值（诚实给多个截断，标注振荡）
    row = []
    for P in (100, 1000, 10000, 50000):
        pr = primes_upto(P)
        prod = 1.0
        for p in pr:
            prod *= (1.0 - omega_p(p) / float(p)) / (1.0 - 1.0 / float(p))
        row.append("P=%d:%.6f" % (P, prod))
    items.append({
        "name": "P4.3 BH 局部积截断值（条件收敛，截断值振荡，仅登记）",
        "passed": True,
        "detail": "C_BH 截断序列 " + ", ".join(row),
    })

    # Iwaniec(1978)：无穷多个 n 使 n^2+1 为 P_2（至多两个素因子）—— 文献结论，本引擎不重新证明
    p2 = 0
    for n in range(1, 3001):
        v = n * n + 1
        m = v
        big = 0
        d = 2
        while d * d <= m and big <= 2:
            while m % d == 0:
                m //= d
                big += 1
            d += 1
        if m > 1:
            big += 1
        if big <= 2:
            p2 += 1
    items.append({
        "name": "P4.4 P_2 层（Iwaniec 1978 的弱化结论）在 n<=3000 的实测占比",
        "passed": True,
        "detail": "n^2+1 至多两个素因子的 n 共 %d/3000；文献结论为'无穷多个'，"
                  "本项仅为实测计数，不重新证明" % p2,
    })
    return items


# --------------------------------------------------------------------------
# 8. 引擎接口（见 05-验证中心/01-引擎/README.md）
# --------------------------------------------------------------------------

def capabilities() -> dict:
    return {
        "name": "landau-scan",
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
        "window_scan_n": WIN_N,
        "n2plus1_scan_n": N2_N,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _item(name, ok, detail=""):
    return {"name": name, "passed": bool(ok), "detail": detail}


def run(record: dict, level: str = "L2", options: dict = None) -> dict:
    if level != "L2":
        return {"status": "SKIP", "engine": "landau-scan", "level": level,
                "reason": "本引擎仅实现 L2", "environment": environment()}
    rid = (record or {}).get("id")
    t0 = time.perf_counter()
    try:
        if rid == "OM-F-NT-0003":
            items, _mn, _am = check_F3()
        elif rid == "OM-F-NT-0004":
            items = check_F4()
        elif rid == "OM-P-NT-0003":
            items = check_P3()
        elif rid == "OM-P-NT-0004":
            items = check_P4()
        else:
            return {"status": "SKIP", "engine": "landau-scan", "level": "L2",
                    "reason": "未识别的记录 id: %s" % rid,
                    "environment": environment()}
    except Exception as exc:  # 引擎不得抛出
        return {"status": "ERROR", "engine": "landau-scan", "level": "L2",
                "reason": "验证异常: %r" % exc, "environment": environment()}

    # 分项标注性质，避免用同一个 "残差 0" 掩盖渐近度量项的真实偏差
    # （本册自查修复：此前 max_abs_residual 恒硬编码为 "0"，而 F4 的渐近项实测偏差为 3.04e-4）。
    METRIC_KW = ("偏差", "比值", "渐近", "占比", "截断序列", "差距")
    SCAN_KW = ("扫描", "计数 A")
    for it in items:
        blob = it["name"] + it.get("detail", "")
        if any(k in blob for k in METRIC_KW):
            it["kind"] = "metric"
        elif any(k in blob for k in SCAN_KW):
            it["kind"] = "scan"
        else:
            it["kind"] = "identity"

    n_id = sum(1 for it in items if it["kind"] == "identity")
    n_sc = sum(1 for it in items if it["kind"] == "scan")
    n_me = sum(1 for it in items if it["kind"] == "metric")
    id_ok = all(it["passed"] for it in items if it["kind"] == "identity")
    passed = sum(1 for it in items if it["passed"])
    status = "PASS" if passed == len(items) and items else "FAIL"

    return {
        "status": status,
        "engine": "landau-scan",
        "level": "L2",
        # 只有 identity 项才是"残差恒为 0"的精确整数恒等式；
        # metric/scan 项各自的偏差写在 detail 里，不能被这个字段掩盖。
        "max_abs_residual": ("0" if (n_id and id_ok) else "见各细项"),
        "identity_items": n_id,
        "scan_items": n_sc,
        "metric_items": n_me,
        "residual_policy": ("max_abs_residual 只覆盖 identity 类检查项（精确整数恒等式，实测残差 0）；"
                            "metric/scan 类为渐近与枚举度量，偏差见各该项的 detail，"
                            "且不构成对渐近式成立与否的判定"),
        "items": items,
        "environment": environment(),
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "notes": "PASS 仅表示在给定范围内未发现反例，不构成证明（红线一）。",
    }


# --------------------------------------------------------------------------
# 9. 自检 CLI
# --------------------------------------------------------------------------

IDS = ("OM-F-NT-0003", "OM-F-NT-0004", "OM-P-NT-0003", "OM-P-NT-0004")


def self_test(only_id=None, as_json=False):
    ids = (only_id,) if only_id else IDS
    results = []
    for rid in ids:
        res = run({"id": rid}, "L2")
        results.append(res)
    if as_json:
        print(json.dumps({"results": results, "environment": environment()},
                         ensure_ascii=False, indent=2))
        return results
    print("=" * 78)
    print("Landau 开放问题扫描引擎 · L2 自检  (window_n=%d, n2plus1_n=%d)"
          % (WIN_N, N2_N))
    print("=" * 78)
    for rid, res in zip(ids, results):
        print("[%s] %s  (%d ms)" % (res["status"], rid, res.get("duration_ms", 0)))
        for it in res.get("items", []):
            print("    - [%s] %s" % ("OK" if it["passed"] else "!!", it["name"]))
            print("        %s" % it["detail"])
        if res["status"] in ("SKIP", "ERROR"):
            print("    reason: %s" % res.get("reason"))
    print("-" * 78)
    print("提示：PASS = 范围内未发现反例，不等于证明（红线一）。")
    return results


def main(argv):
    only = None
    as_json = False
    for a in argv:
        if a == "--json":
            as_json = True
        elif a.startswith("--id="):
            only = a.split("=", 1)[1]
    self_test(only, as_json)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
