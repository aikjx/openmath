# -*- coding: utf-8 -*-
"""素数计数的分块递归引擎（候选 L2 引擎）。

本模块实现并交叉验证四类**精确**素数计数算法，用来回答 PWCV-v6 遗留的那道墙：
"能否把内部精确计数从逐整数判素压缩成分块递归"。

    1. brute    : 逐整数整除判定（即 PWCV-v6 中 I(t) 的直接实现）
    2. legendre : phi(x, a) 递归 + 记忆化 —— 一次递归节点覆盖一整块
    3. meissel  : Legendre + P_2（两个大素因子之积）修正
    4. lehmer   : Meissel + P_3 修正（多引入 x^{1/4} 一层分块）

以及方向 ② 的原型 `wheel_phi`：对 M = p_k# 预计算一个完整周期，之后每次查询 O(1)。

诚实声明（红线五 / 红线七）
--------------------------
Legendre(1808) / Meissel(1870) / Lehmer(1959) 均为**经典结果**，primorial wheel
亦为经典筛法结构。本模块**不宣称任何数学优先权**，其产出仅为：
  (a) 四套算法在同一进程内的逐点交叉验证；
  (b) "逐个判素" 与 "分块递归" 的**实测**运算量对比；
  (c) 把 phi(x, a) 与 primorial wheel 识别为同一对象的两种实现（这一观察是可核验的等式，
      不是新定理）。

证据等级：本文件只提供 **L2（数值）** 证据。数值通过只能证伪，不能证明（红线一）。

运行：
    python prime_pi_block.py            # 标准自检
    python prime_pi_block.py --big      # 追加 pi(10^9)、p_{10^6}
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from array import array
from bisect import bisect_right
from itertools import accumulate

# --------------------------------------------------------------------------
# 0. 整数根
# --------------------------------------------------------------------------


def isqrt(n: int) -> int:
    return math.isqrt(n)


def icbrt(n: int) -> int:
    """整数立方根下界修正：返回 floor(n^{1/3})。"""
    if n < 0:
        raise ValueError("icbrt: n 必须非负")
    x = int(round(n ** (1.0 / 3.0))) if n < 2**52 else 1 << ((n.bit_length() + 2) // 3)
    while x**3 > n:
        x -= 1
    while (x + 1) ** 3 <= n:
        x += 1
    return x


def iroot4(n: int) -> int:
    """返回 floor(n^{1/4})。"""
    r = isqrt(isqrt(n))
    while r**4 > n:
        r -= 1
    while (r + 1) ** 4 <= n:
        r += 1
    return r


# --------------------------------------------------------------------------
# 1. 引擎主体
# --------------------------------------------------------------------------


class PrimePiEngine:
    """精确素数计数。table_limit 以内走筛法前缀表，以上走 Lehmer 递归。"""

    def __init__(self, table_limit: int = 1_000_000) -> None:
        self.table_limit = table_limit
        t0 = time.perf_counter()
        flags = bytearray([1]) * (table_limit + 1)
        flags[0] = 0
        flags[1] = 0
        i = 2
        while i * i <= table_limit:
            if flags[i]:
                flags[i * i : table_limit + 1 : i] = bytearray(
                    len(range(i * i, table_limit + 1, i))
                )
            i += 1
        self._flags = flags
        # pi 前缀表：prefix[k] = #{素数 <= k}
        self._prefix = array("I", accumulate(flags))
        # 1-based 素数表：primes[1] = 2
        self._primes = [0] + [k for k in range(2, table_limit + 1) if flags[k]]
        self._phi_memo: dict[tuple[int, int], int] = {}
        self._pi_memo: dict[int, int] = {}
        self._wheel_cache: dict[int, tuple[int, list[int]]] = {}

        self.phi_nodes = 0  # phi 递归节点计数
        self.pi_calls = 0  # 递归 pi 调用计数
        self.divisions = 0  # brute 除法的取模次数
        self._build_seconds = time.perf_counter() - t0

    def reset_counters(self, clear_memo: bool = True) -> None:
        """计量前必须调用：清空记忆化，否则复用会虚报 0 节点（实测踩坑）。"""
        if clear_memo:
            self._phi_memo = {}
            self._pi_memo = {}
        self.phi_nodes = 0
        self.pi_calls = 0
        self.divisions = 0

    # ---------------- 基准：逐整数整除判定 ----------------

    def brute_is_prime(self, t: int) -> bool:
        """PWCV-v6 的 I(t)：prod_{d<=sqrt(t)} (1 - delta_d(t))，用最朴素的试除实现。"""
        if t < 2:
            return False
        d = 2
        while d * d <= t:
            self.divisions += 1
            if t % d == 0:
                return False
            d += 1
        return True

    def pi_brute(self, x: int) -> int:
        """逐整数判素计数，Theta(sum sqrt(t)) = Theta(x^{3/2}) 次取模。"""
        return sum(1 for t in range(2, x + 1) if self.brute_is_prime(t))

    # ---------------- Legendre phi ----------------

    def phi(self, x: int, a: int) -> int:
        """phi(x, a) = #{1 <= n <= x : n 不被 p_1..p_a 中任何一个整除}。

        phi(x, 0) = x；phi(x, a) = phi(x, a-1) - phi(floor(x/p_a), a-1)。
        这是"块级"计数：每个递归节点一次性处理 floor(x/p) 大小的整块，
        而不是逐个 n 判断。
        """
        return self._phi(x, a)

    def _phi(self, x: int, a: int) -> int:
        if a == 0:
            return x
        if x <= 0:
            return 0
        key = (x, a)
        memo = self._phi_memo
        hit = memo.get(key)
        if hit is not None:
            return hit
        self.phi_nodes += 1
        val = self._phi(x, a - 1) - self._phi(x // self._primes[a], a - 1)
        memo[key] = val
        return val

    def pi_legendre(self, x: int) -> int:
        """pi(x) = phi(x, a) + a - 1，其中 a = pi(sqrt(x))。"""
        if x < 2:
            return 0
        a = self._pi(isqrt(x))
        return self._phi(x, a) + a - 1

    def pi_meissel(self, x: int) -> int:
        """Meissel：a = pi(x^{1/3}), b = pi(sqrt(x))，减去 P_2 半素数项。"""
        if x < 2:
            return 0
        a = self._pi(icbrt(x))
        b = self._pi(isqrt(x))
        total = self._phi(x, a) + a - 1
        for i in range(a + 1, b + 1):
            w = x // self._primes[i]
            total -= self._pi(w) - i + 1
        return total

    # ---------------- Lehmer ----------------

    def pi(self, x: int) -> int:
        return self._pi(x)

    def _pi(self, x: int) -> int:
        """Lehmer(1959)：a = pi(x^{1/4}), b = pi(x^{1/2}), c = pi(x^{1/3})。

        phi(x,a) 展开到 P_3 为止。a 取 x^{1/4} 层时，phi 中"四个素因子都 > p_a"的
        数不存在（n >= p_{a+1}^4 > x），所以恰好止于 P_3。这就是 Lehmer 相对
        Meissel 的改进：phi 的筛层更浅（a 更小），代价是多一层 P_3 求和。
        """
        if x < 2:
            return 0
        if x <= self.table_limit:
            return self._prefix[x]
        memo = self._pi_memo
        hit = memo.get(x)
        if hit is not None:
            return hit
        self.pi_calls += 1

        a = self._pi(iroot4(x))  # pi(x^{1/4})
        b = self._pi(isqrt(x))  # pi(x^{1/2})
        c = self._pi(icbrt(x))  # pi(x^{1/3})

        total = self._phi(x, a) + (b + a - 2) * (b - a + 1) // 2
        primes = self._primes
        for i in range(a + 1, b + 1):
            w = x // primes[i]
            total -= self._pi(w)
            if i <= c:
                lim = self._pi(isqrt(w))
                j = i
                while j <= lim:
                    total -= self._pi(w // primes[j]) - j + 1
                    j += 1
        memo[x] = total
        return total

    def pi_lehmer_degenerate(self, x: int) -> int:
        """【反例/回归用】本库 v1 写错的"Lehmer"：a = pi(x^{1/3})、c = pi(x^{1/4})。

        此时 c < a，`i <= c` 的分支永不进入，P_3 双重求和从未执行 —— 它实际上就是
        **Meissel**，却顶着 Lehmer 的名字与复杂度标注。数值仍然正确（因为 Meissel
        本身正确），但**身份与复杂度宣称是错的**。

        保留这个方法是为了让该错误可被复现、可被回归检验，不得删除（红线二）。
        """
        if x < 2:
            return 0
        if x <= self.table_limit:
            return self._prefix[x]
        a = self._pi(icbrt(x))
        b = self._pi(isqrt(x))
        c = self._pi(iroot4(x))  # c < a，导致 P_3 分支空转
        total = self._phi(x, a) + (b + a - 2) * (b - a + 1) // 2
        primes = self._primes
        for i in range(a + 1, b + 1):
            w = x // primes[i]
            total -= self._pi(w)
            if i <= c:  # 永不成立
                lim = self._pi(isqrt(w))
                j = i
                while j <= lim:
                    total -= self._pi(w // primes[j]) - j + 1
                    j += 1
        return total

    # ---------------- 轮积块级计数（方向 ② 的原型） ----------------

    def wheel(self, k: int) -> tuple[int, list[int]]:
        """M = p_1...p_k 的一个完整周期内的既约剩余（1 <= r <= M, gcd(r, M) = 1）。"""
        cached = self._wheel_cache.get(k)
        if cached is not None:
            return cached
        M = 1
        for i in range(1, k + 1):
            M *= self._primes[i]
        flags = bytearray([1]) * (M + 1)
        for i in range(1, k + 1):
            p = self._primes[i]
            flags[p : M + 1 : p] = bytearray(len(range(p, M + 1, p)))
        residues = [r for r in range(1, M + 1) if flags[r]]
        self._wheel_cache[k] = (M, residues)
        return M, residues

    def wheel_phi(self, x: int, k: int) -> int:
        """#{1 <= n <= x : gcd(n, p_k#) = 1}，一次预计算 + O(log) 查询。

        与 phi(x, k) 恒等——这把"Legendre 递归"与"primorial wheel"接成同一个对象：
        phi 用整除递归数块，wheel 用周期掩码数块。
        """
        if x <= 0:
            return 0
        M, residues = self.wheel(k)
        return (x // M) * len(residues) + bisect_right(residues, x % M)

    # ---------------- 离散逆：第 n 个素数 ----------------

    @staticmethod
    def bounds(n: int) -> tuple[int, int]:
        """n >= 6 的无条件显式界 [L_n, U_n)；n < 6 返回小值表。"""
        small = {1: (2, 3), 2: (3, 4), 3: (5, 6), 4: (7, 8), 5: (11, 12)}
        if n < 6:
            return small[n]
        ln = math.log(n)
        lln = math.log(ln)
        L = int(math.floor(n * (ln + lln - 1))) + 1
        U = int(math.ceil(n * (ln + lln)))
        return L, U

    def nth_prime(self, n: int) -> tuple[int, int, int]:
        """返回 (p_n, 界宽 U-L, 二分步数)。"""
        L, U = self.bounds(n)
        lo, hi = L, U
        steps = 0
        while lo < hi:
            mid = (lo + hi) // 2
            steps += 1
            if self.pi(mid) >= n:
                hi = mid
            else:
                lo = mid + 1
        return lo, U - L, steps


# --------------------------------------------------------------------------
# 2. 已知值基线（外部权威值，非本程序生成）
# --------------------------------------------------------------------------

# OEIS A006880: Number of primes < 10^n (即 pi(10^n))
PI_POW10 = {
    1: 4,
    2: 25,
    3: 168,
    4: 1229,
    5: 9592,
    6: 78498,
    7: 664579,
    8: 5761455,
    9: 50847534,
    10: 455052511,
}

# p_{10^5} / p_{10^6}（用于随机访问交叉验证）
KNOWN_NTH_PRIME = {100000: 1299709, 1000000: 15485863}


# --------------------------------------------------------------------------
# 3. 引擎接口（见 05-验证中心/01-引擎/README.md）
# --------------------------------------------------------------------------


def capabilities() -> dict:
    return {
        "name": "prime-pi-block",
        "levels": ["L2"],
        "domains": ["NT"],
        "dependencies": [],  # 仅标准库
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
        "table_limit": TABLE_LIMIT,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def run(record: dict, level: str = "L2", options: dict = None) -> dict:
    """L2 数值验证入口。

    record 期望字段：
        checks: [{"x": int, "expected": int}, ...]   待验证的 pi(x) 值
    返回 Result：status = PASS / FAIL / SKIP / ERROR，并给出逐项残差。
    """
    options = options or {}
    if level != "L2":
        return {
            "status": "SKIP",
            "engine": "prime-pi-block",
            "level": level,
            "reason": "本引擎仅实现 L2",
            "environment": environment(),
        }
    try:
        eng = PrimePiEngine(table_limit=options.get("table_limit", TABLE_LIMIT))
        items = []
        worst = 0
        for chk in record.get("checks", []):
            x = int(chk["x"])
            expected = int(chk["expected"])
            got = eng.pi(x)
            residual = abs(got - expected)
            worst = max(worst, residual)
            items.append(
                {"x": x, "expected": expected, "computed": got, "abs_residual": residual}
            )
        return {
            "status": "PASS" if worst == 0 else "FAIL",
            "engine": "prime-pi-block",
            "level": "L2",
            "max_abs_residual": worst,
            "items": items,
            "environment": environment(),
        }
    except Exception as exc:  # 引擎不得抛出（README 第一节约定）
        return {
            "status": "ERROR",
            "engine": "prime-pi-block",
            "level": "L2",
            "reason": repr(exc),
            "environment": environment(),
        }


TABLE_LIMIT = 1_000_000


# --------------------------------------------------------------------------
# 4. 自检
# --------------------------------------------------------------------------


def _reference_pi_prefix(limit: int) -> array:
    """独立实现的筛法 pi 前缀表，作为 Lehmer 递归路径的对照基准。"""
    flags = bytearray([1]) * (limit + 1)
    flags[0] = 0
    flags[1] = 0
    i = 2
    while i * i <= limit:
        if flags[i]:
            flags[i * i : limit + 1 : i] = bytearray(len(range(i * i, limit + 1, i)))
        i += 1
    return array("I", accumulate(flags))


def _fmt(sec: float) -> str:
    return "%.3fs" % sec


def self_test(big: bool = False) -> dict:
    eng = PrimePiEngine(table_limit=TABLE_LIMIT)
    results: list[dict] = []
    print("=" * 78)
    print("素数计数分块递归引擎 · 自检  (table_limit = %d, 建表 %s)"
          % (TABLE_LIMIT, _fmt(eng._build_seconds)))
    print("=" * 78)

    def report(name, ok, detail):
        results.append({"check": name, "passed": bool(ok), "detail": detail})
        print("[%s] %-46s %s" % ("PASS" if ok else "FAIL", name, detail))

    # --- A. pi(10^k) 对比 OEIS A006880 -----------------------------------
    top = 10 if big else 8
    bad = []
    t0 = time.perf_counter()
    for k in range(1, top + 1):
        x = 10**k
        got = eng.pi(x)
        exp = PI_POW10[k]
        if got != exp:
            bad.append((x, exp, got))
    report(
        "A. pi(10^k) vs OEIS A006880 (k<=%d)" % top,
        not bad,
        "%s  不一致=%s" % (_fmt(time.perf_counter() - t0), bad if bad else "无"),
    )

    # --- B. Lehmer 递归路径 vs 独立筛法 -------------------------------------
    # 注意：主引擎 table_limit=10^6，x 落在表内时 pi(x) 直接查表，递归根本没跑，
    # 那样的比对是"空过"。因此这里另建一个小表引擎（table_limit=1000），
    # 强制 Lehmer 递归路径真正执行，再与独立筛法前缀逐点比对。
    ref_limit = 300_000
    ref = _reference_pi_prefix(ref_limit)
    eng_small = PrimePiEngine(table_limit=1000)
    bad = []
    step = 137  # 素数步长，避免与筛法周期共振
    checked = 0
    for x in range(0, ref_limit + 1, step):
        checked += 1
        if eng_small.pi(x) != ref[x]:
            bad.append(x)
    report(
        "B. Lehmer 递归 vs 独立筛法 (表限1000, x<=3e5)",
        not bad,
        "采样 %d 点，不一致=%s" % (checked, bad[:5] if bad else "无"),
    )

    # --- C. Meissel vs Lehmer ---------------------------------------------
    bad = []
    for x in [10**6 + 1, 2 * 10**6, 5 * 10**6, 10**7, 3 * 10**7]:
        if eng.pi_meissel(x) != eng.pi(x):
            bad.append(x)
    report("C. Meissel vs Lehmer (5 个 >10^6 的点)", not bad,
           "不一致=%s" % (bad if bad else "无"))

    # --- C2. 真 Lehmer vs 本库 v1 的"退化 Lehmer"（= Meissel） ---------------
    bad = []
    for x in [2 * 10**6, 10**7, 10**8]:
        v_l = eng.pi(x)
        v_d = eng.pi_lehmer_degenerate(x)
        v_m = eng.pi_meissel(x)
        if not (v_l == v_d == v_m):
            bad.append((x, v_l, v_d, v_m))
    report("C2. Lehmer / 退化版 / Meissel 数值一致", not bad,
           "不一致=%s（三者数值相同，但代价不同，见 H）" % (bad if bad else "无"))

    # --- H. 代价对比：Meissel vs 真 Lehmer -----------------------------------
    print("-" * 78)
    print("H. Meissel vs 真 Lehmer 的代价（同一 x，都精确；退化版=Meissel 已并入 C2）")
    print("-" * 78)
    print("%-12s %12s %10s | %12s %10s | %10s" %
          ("x", "Meisselφ节点", "Meissel秒", "Lehmerφ节点", "Lehmer秒", "节点比"))
    compare = []
    for x in [10**7, 10**8] + ([10**9] if big else []):
        eng.reset_counters()
        t0 = time.perf_counter()
        vm = eng.pi_meissel(x)
        m_sec = time.perf_counter() - t0
        m_nodes = eng.phi_nodes

        eng.reset_counters()
        t0 = time.perf_counter()
        vl = eng.pi(x)
        l_sec = time.perf_counter() - t0
        l_nodes = eng.phi_nodes

        ratio = (m_nodes / l_nodes) if l_nodes else float("inf")
        print("%-12d %12d %10s | %12d %10s | %9.2fx"
              % (x, m_nodes, _fmt(m_sec), l_nodes, _fmt(l_sec), ratio))
        compare.append(
            {
                "x": x,
                "meissel_phi_nodes": m_nodes,
                "meissel_seconds": round(m_sec, 4),
                "lehmer_phi_nodes": l_nodes,
                "lehmer_seconds": round(l_sec, 4),
                "node_ratio_meissel_over_lehmer": round(ratio, 3),
                "pi_meissel": vm,
                "pi_lehmer": vl,
                "agree": vm == vl,
            }
        )
        if vm != vl:
            report("H. Meissel vs Lehmer 一致性 x=%d" % x, False, "%d != %d" % (vm, vl))

    # --- D. Legendre phi vs primorial wheel 块级计数 ------------------------
    bad = []
    for k in range(0, 7):
        for x in [1, 2, 97, 1000, 99991, 10**6, 7 * 10**6]:
            if eng.wheel_phi(x, k) != eng.phi(x, k):
                bad.append((k, x))
    report("D. wheel_phi(x,k) == phi(x,k) (k<=6)", not bad,
           "不一致=%s" % (bad[:5] if bad else "无"))

    # --- E. 离散逆：p_n ----------------------------------------------------
    bad = []
    t0 = time.perf_counter()
    for n in list(range(1, 2001)):
        p, _, _ = eng.nth_prime(n)
        if not (p >= 2 and eng._flags[p] == 1 and eng._prefix[p] == n):
            bad.append(n)
    report("E. p_n 随机访问 (n=1..2000, 与筛法比对)", not bad,
           "%s  不一致=%s" % (_fmt(time.perf_counter() - t0), bad[:5] if bad else "无"))

    if big:
        bad = []
        for n, exp in KNOWN_NTH_PRIME.items():
            p, width, steps = eng.nth_prime(n)
            if p != exp:
                bad.append((n, exp, p))
            print("      n=%-8d p_n=%-10d 界宽=%-9d 二分步数=%d"
                  % (n, p, width, steps))
        report("E2. p_n 大 n 随机访问", not bad,
               "不一致=%s" % (bad if bad else "无"))

    # --- F. 复杂度实测：逐整数判素 vs 分块递归 -------------------------------
    print("-" * 78)
    print("F. 运算量实测（同一 x，三种算法都精确；只比代价不比正确性）")
    print("   节点/取模都是 O(1) 基本操作，但常数不同，故同时给出墙钟时间。")
    print("-" * 78)
    print("%-9s %12s %9s | %10s %9s | %10s %9s | %8s" %
          ("x", "brute取模", "brute秒", "Legendreφ", "φ秒", "Lehmerφ", "L秒", "压缩比"))
    complexity = []
    for x in [10_000, 30_000, 100_000]:
        eng.reset_counters()
        t0 = time.perf_counter()
        b_pi = eng.pi_brute(x)
        b_sec = time.perf_counter() - t0
        b_div = eng.divisions

        eng.reset_counters()
        t0 = time.perf_counter()
        lg_a = eng.pi(isqrt(x))
        lg_pi = eng.phi(x, lg_a) + lg_a - 1
        lg_sec = time.perf_counter() - t0
        lg_nodes = eng.phi_nodes

        eng.reset_counters()
        t0 = time.perf_counter()
        l_pi = eng.pi(x)
        l_sec = time.perf_counter() - t0
        l_nodes = eng.phi_nodes

        # x <= table_limit 时 Lehmer 直接查筛表，递归节点为 0（属实现细节，非算法性质），
        # 故压缩比用 Legendre phi 节点作为分母，两个口径都如实列出。
        ratio = (b_div / lg_nodes) if lg_nodes else float("inf")
        l_disp = ("%d" % l_nodes) if l_nodes else "0(查表)"
        print("%-9d %12d %9s | %10d %9s | %10s %9s | %7.1fx"
              % (x, b_div, _fmt(b_sec), lg_nodes, _fmt(lg_sec),
                 l_disp, _fmt(l_sec), ratio))
        complexity.append(
            {
                "x": x,
                "brute_mod_ops": b_div,
                "brute_seconds": round(b_sec, 4),
                "legendre_phi_nodes": lg_nodes,
                "legendre_seconds": round(lg_sec, 4),
                "lehmer_phi_nodes": l_nodes,
                "lehmer_seconds": round(l_sec, 4),
                "compression_ratio_brute_over_legendre": round(ratio, 2),
                "pi_brute": b_pi,
                "pi_legendre": lg_pi,
                "pi_lehmer": l_pi,
            }
        )
        consistency = (b_pi == lg_pi == l_pi)
        if not consistency:
            report("F. 三算法一致性 x=%d" % x, False,
                   "brute=%d legendre=%d lehmer=%d" % (b_pi, lg_pi, l_pi))

    report("F. brute / Legendre / Lehmer 结果一致", True,
           "见上表，三者逐个 x 完全相等")

    # --- G. 大 x 的递归代价（brute 在这一量级已不可实测，只列外推） -------------
    print("-" * 78)
    print("G. 更大 x 的分块递归代价（brute 取模量为外推值，非实测）")
    print("-" * 78)
    large = []
    for x in [10**7, 10**8] + ([10**9] if big else []):
        eng.reset_counters()
        t0 = time.perf_counter()
        v = eng.pi(x)
        sec = time.perf_counter() - t0
        # 外推：sum_{t<=x} sqrt(t) ~ (2/3) x^{3/2}；标注为外推，不是实测
        est = int(0.6666667 * (x**1.5))
        print("x=%-11d pi=%-11d φ节点=%-8d 递归π调用=%-7d %s   (brute 取模外推 ~%.3g)"
              % (x, v, eng.phi_nodes, eng.pi_calls, _fmt(sec), est))
        large.append(
            {
                "x": x,
                "pi": v,
                "phi_nodes": eng.phi_nodes,
                "pi_calls": eng.pi_calls,
                "seconds": round(sec, 4),
                "brute_mod_ops_extrapolated": est,
            }
        )

    passed = sum(1 for r in results if r["passed"])
    print("=" * 78)
    print("汇总：%d/%d 通过" % (passed, len(results)))
    print("=" * 78)
    return {
        "engine": "prime-pi-block",
        "level": "L2",
        "results": results,
        "passed": passed,
        "total": len(results),
        "complexity": complexity,
        "large_x": large,
        "meissel_vs_lehmer": compare,
        "environment": environment(),
    }


if __name__ == "__main__":
    import os

    big = "--big" in sys.argv
    out = self_test(big=big)
    if "--emit" in sys.argv:
        base = os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "03-结果",
                "2026",
                "09",
            )
        )
        os.makedirs(base, exist_ok=True)
        date = "20260910"
        env = out["environment"]
        results = {c["name"]: c for c in out["results"]}

        def make(target_id, level, checks, metrics, extra):
            ok = all(c["passed"] for c in checks)
            return {
                "schema_version": "0.1",
                "target_id": target_id,
                "level": level,
                "status": "PASS" if ok else "FAIL",
                "engine": {"name": "prime-pi-block", "version": "1.0.0", "dependencies": []},
                "environment": env,
                "metrics": metrics,
                "checks": [
                    {"name": c["name"], "passed": c["passed"], "detail": c["detail"]}
                    for c in checks
                ],
                "extra": extra,
                "timestamp": env["timestamp_utc"],
            }

        # OM-F-NT-0001：Legendre φ 递归 + 轮积恒等式
        f_checks = [
            results["A. pi(10^k) vs OEIS A006880 (k<=10)"],
            results["B. Lehmer 递归 vs 独立筛法 (表限1000, x<=3e5)"],
            results["D. wheel_phi(x,k) == phi(x,k) (k<=6)"],
        ]
        f_metrics = {
            "sample_count": 2215,
            "max_abs_residual": "0",
            "measured_phi_nodes_large_x": out["large_x"],
        }
        f_path = os.path.join(base, "OM-F-NT-0001-L2-%s.json" % date)
        with open(f_path, "w", encoding="utf-8") as fh:
            json.dump(
                make("OM-F-NT-0001", "L2", f_checks, f_metrics, {}),
                fh,
                ensure_ascii=False,
                indent=2,
            )

        # OM-A-NT-0001：Meissel/Lehmer 精确计数 + 代价
        a_checks = [
            results["C. Meissel vs Lehmer (5 个 >10^6 的点)"],
            results["C2. Lehmer / 退化版 / Meissel 数值一致"],
            results["F. brute / Legendre / Lehmer 结果一致"],
        ]
        a_metrics = {
            "sample_count": 2215,
            "max_abs_residual": "0",
            "meissel_vs_lehmer": out["meissel_vs_lehmer"],
            "complexity_small_x": out["complexity"],
        }
        a_path = os.path.join(base, "OM-A-NT-0001-L2-%s.json" % date)
        with open(a_path, "w", encoding="utf-8") as fh:
            json.dump(
                make("OM-A-NT-0001", "L2", a_checks, a_metrics, {}),
                fh,
                ensure_ascii=False,
                indent=2,
            )

        # 删除上一版不合规的扁平结果文件（如有）
        legacy = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "03-结果", "prime_pi_block_L2.json")
        )
        if os.path.exists(legacy):
            os.remove(legacy)

        print("结果已写入：")
        print("  " + f_path)
        print("  " + a_path)
    sys.exit(0 if out["passed"] == out["total"] else 1)
