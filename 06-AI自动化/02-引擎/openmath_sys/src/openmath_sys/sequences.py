"""
序列理论引擎：在**整数序列**上发现递推关系、超几何闭式与增长率。

与 theoryforge 的分工
--------------------
- `theoryforge` 找的是**同一对象内部**不变量之间的静态关系（如 χ ≥ ω）。
- 本模块找的是**沿参数 n 演化**的动态关系：a(n) 如何用前面的项表示。

三条通道
--------
- C1 常系数线性递推（C-finite）：a(n) = c1·a(n-1) + ... + ck·a(n-k)（可带常数项）
- C2 一阶有理（超几何）递推：a(n+1)/a(n) = P(n)/Q(n)
- C3 增长率：指数底 λ 或多项式次数 k（L2 数值估计，含 Richardson 外推与稳定性）

检验策略
--------
发现集只取前 `DISCOVERY_LEN` 项，**后续项一律不参与发现**，只用于外推检验。
另跑一遍更小的发现集（前 `STRESS_LEN` 项）做压力测试：小样本上拟合出来的
递推若在全量上不成立，即为"过拟合反例"，必须保留并列出第一个失败的 n。

诚实口径
--------
所有结论都是**有限项上的事实**，外推再多也不是证明。见 SCOPE_NOTE / EVIDENCE_NOTE。
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Tuple

SCOPE_NOTE = (
    "本模块在**有限项整数序列**上搜索递推形式。所有结论的论域严格是"
    "'已生成的这些项'：通过外推检验只说明在给定长度内没有找到反例，"
    "**不证明**该递推对所有 n 成立（检验集之外永远是未知）。"
)

EVIDENCE_NOTE = (
    "证据等级 L2（计算证据）。C1/C2 的系数由精确有理高斯消元得到，"
    "外推检验是精确整数比较（相等即相等，无容差）；C3 增长率是浮点数值估计，"
    "只给区间与稳定性，不给确定值。"
)

N_TERMS = 60          # 每个序列生成的项数
DISCOVERY_LEN = 30    # 发现集长度（其余为外推检验集）
STRESS_LEN = 15       # 压力测试的发现集长度（更小，用于暴露过拟合）
MAX_ORDER = 4         # C1 搜索的最高阶数
COEF_BOUND = 10 ** 6  # 系数分子/分母的绝对值上界（防过拟合）


# ===========================================================================
# 1. 精确有理线性代数（不依赖第三方库）
# ===========================================================================
def _rref(mat: List[List[Fraction]]) -> Tuple[int, List[int], List[List[Fraction]]]:
    """行最简形。返回 (秩, 主元列, 化简后的矩阵)。"""
    m = [row[:] for row in mat]
    rows = len(m)
    cols = len(m[0]) if m else 0
    piv: List[int] = []
    r = 0
    for c in range(cols):
        p = None
        for i in range(r, rows):
            if m[i][c] != 0:
                p = i
                break
        if p is None:
            continue
        m[r], m[p] = m[p], m[r]
        pv = m[r][c]
        m[r] = [x / pv for x in m[r]]
        for i in range(rows):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        piv.append(c)
        r += 1
        if r == rows:
            break
    return r, piv, m


def _solve_exact(A: List[List[Fraction]], b: List[Fraction]) -> Dict[str, Any]:
    """精确求解 A x = b。返回相容性与解（唯一解时才给 solution）。"""
    if not A:
        return {"consistent": True, "unique": False, "rank": 0}
    n = len(A[0])
    aug = [A[i][:] + [b[i]] for i in range(len(A))]
    rank, piv, R = _rref(aug)
    for i in range(len(R)):
        if all(R[i][c] == 0 for c in range(n)) and R[i][n] != 0:
            return {"consistent": False, "unique": False, "rank": rank}
    free = [c for c in range(n) if c not in piv]
    if free:
        return {"consistent": True, "unique": False, "rank": rank, "free_cols": free}
    sol = [Fraction(0)] * n
    for i, c in enumerate(piv):
        sol[c] = R[i][n]
    return {"consistent": True, "unique": True, "rank": rank, "solution": sol}


def _nullspace(A: List[List[Fraction]]) -> List[List[Fraction]]:
    """齐次系统 A x = 0 的一组基（精确）。"""
    if not A:
        return []
    n = len(A[0])
    aug = [row[:] + [Fraction(0)] for row in A]
    _rank, piv, R = _rref(aug)
    free = [c for c in range(n) if c not in piv]
    basis: List[List[Fraction]] = []
    for fc in free:
        v = [Fraction(0)] * n
        v[fc] = Fraction(1)
        for i, c in enumerate(piv):
            v[c] = -R[i][fc]
        basis.append(v)
    return basis


def _frac_str(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _coef_ok(c: Fraction) -> bool:
    return abs(c.numerator) <= COEF_BOUND and abs(c.denominator) <= COEF_BOUND


# ===========================================================================
# 2. 序列库（纯标准库生成，全部精确整数）
# ===========================================================================
def _sieve(limit: int) -> List[int]:
    flag = [True] * (limit + 1)
    flag[0] = flag[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if flag[i]:
            for j in range(i * i, limit + 1, i):
                flag[j] = False
    return [i for i in range(limit + 1) if flag[i]]


def _factorize(n: int) -> Dict[int, int]:
    f: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def _partitions_p(n: int) -> List[int]:
    """划分数 p(n)，用五边形数递推（Euler）。"""
    p = [1] + [0] * n
    for i in range(1, n + 1):
        s, k = 0, 1
        while True:
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            if g1 > i and g2 > i:
                break
            sign = 1 if k % 2 == 1 else -1
            if g1 <= i:
                s += sign * p[i - g1]
            if g2 <= i:
                s += sign * p[i - g2]
            k += 1
        p[i] = s
    return p


def _collatz_steps(n: int) -> int:
    s = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        s += 1
    return s


def build_sequences(n_terms: int = N_TERMS) -> List[Dict[str, Any]]:
    """生成序列库。每项含 id/名称/前 n_terms 项/索引起点/说明。"""
    seqs: List[Dict[str, Any]] = []

    def add(sid: str, cn: str, terms: List[int], base: int, note: str) -> None:
        seqs.append({"id": sid, "name": sid, "cn": cn, "terms": terms[:n_terms],
                     "index_base": base, "note": note})

    primes = _sieve(max(2000, 40 * n_terms))

    # --- 素数与计数 ---
    pset = set(primes)
    cnt, running = 0, []
    for n in range(0, n_terms + 2):
        if n in pset:
            cnt += 1
        running.append(cnt)
    add("primes_count", "素数计数 π(n)", running[:n_terms], 0, "不大于 n 的素数个数")
    add("prime_gaps", "相邻素数间隙", [primes[i + 1] - primes[i]
                                       for i in range(n_terms)], 1,
        "第 n 个与第 n+1 个素数之差")

    # --- 算术函数（索引从 1 起）---
    phi, sigma, tau, omega, bigomega, mu, rad = [], [], [], [], [], [], []
    for n in range(1, n_terms + 2):
        f = _factorize(n)
        t = 1
        s = 1
        r = 1
        for p_, e in f.items():
            t *= (e + 1)
            s *= (p_ ** (e + 1) - 1) // (p_ - 1)
            r *= p_
        phi.append(n // r * r // n if False else sum(1 for k in range(1, n + 1)
                                                     if _gcd(k, n) == 1))
        sigma.append(s)
        tau.append(t)
        omega.append(len(f))
        bigomega.append(sum(f.values()))
        mu.append(0 if any(e > 1 for e in f.values()) else (-1) ** (len(f) % 2))
        rad.append(r)
    add("euler_phi", "欧拉函数 φ(n)", phi[:n_terms], 1, "不超过 n 且与 n 互素的正整数个数")
    add("sigma", "约数和 σ(n)", sigma[:n_terms], 1, "n 的全部正约数之和")
    add("tau", "约数个数 τ(n)", tau[:n_terms], 1, "n 的正约数个数")
    add("omega", "不同素因子个数 ω(n)", omega[:n_terms], 1, "计重数为 1")
    add("bigomega", "带重数素因子个数 Ω(n)", bigomega[:n_terms], 1, "计重数")
    add("mobius", "莫比乌斯函数 μ(n)", mu[:n_terms], 1,
        "含平方因子时为 0，否则 (-1)^(素因子个数)")
    add("radical", "根式 rad(n)", rad[:n_terms], 1, "n 的不同素因子之积")

    # --- 经典递推序列 ---
    fib = [0, 1]
    while len(fib) < n_terms + 2:
        fib.append(fib[-1] + fib[-2])
    add("fibonacci", "斐波那契数列", fib[:n_terms], 0, "F(0)=0, F(1)=1")

    luc = [2, 1]
    while len(luc) < n_terms + 2:
        luc.append(luc[-1] + luc[-2])
    add("lucas", "卢卡斯数列", luc[:n_terms], 0, "L(0)=2, L(1)=1")

    trib = [0, 0, 1]
    while len(trib) < n_terms + 2:
        trib.append(trib[-1] + trib[-2] + trib[-3])
    add("tribonacci", "三项斐波那契", trib[:n_terms], 0, "T(0)=0, T(1)=0, T(2)=1")

    add("powers_of_two", "2 的幂", [2 ** n for n in range(n_terms)], 0, "a(n)=2^n")
    add("mersenne", "梅森数", [2 ** n - 1 for n in range(n_terms)], 0, "a(n)=2^n-1")
    add("squares", "平方数", [n * n for n in range(n_terms)], 0, "a(n)=n^2")
    add("triangular", "三角形数", [n * (n + 1) // 2 for n in range(n_terms)], 0,
        "a(n)=n(n+1)/2")

    fact = [1]
    for n in range(1, n_terms):
        fact.append(fact[-1] * n)
    add("factorial", "阶乘", fact[:n_terms], 0, "a(n)=n!")

    # C(n) = C(n-1)·(4n-2)/(n+1)，C(0)=1 → 1,1,2,5,14,...
    cat = [1]
    for n in range(1, n_terms):
        cat.append(cat[-1] * (4 * n - 2) // (n + 1))
    add("catalan", "卡特兰数", cat[:n_terms], 0, "C(n)=1/(n+1)·binomial(2n,n)")

    # binomial(2n,n) = binomial(2n-2,n-1)·(4n-2)/n → 1,2,6,20,70,...
    cen = [1]
    for n in range(1, n_terms):
        cen.append(cen[-1] * (4 * n - 2) // n)
    add("central_binomial", "中心二项式系数", cen[:n_terms], 0, "binomial(2n,n)")

    der = [1, 0]
    for n in range(2, n_terms):
        der.append(n * der[-1] + (-1) ** n)
    add("derangements", "错排数", der[:n_terms], 0, "D(n)=n·D(n-1)+(-1)^n")

    mot = [1, 1]
    for n in range(2, n_terms):
        mot.append(((2 * n + 1) * mot[-1] + (3 * n - 3) * mot[-2]) // (n + 2))
    add("motzkin", "莫茨金数", mot[:n_terms], 0, "组合数学中的经典非 C-有限序列")

    bell = [1]
    row = [1]
    for _ in range(n_terms - 1):
        new = [row[-1]]
        for j in range(len(row)):
            new.append(new[-1] + row[j])
        row = new
        bell.append(row[0])
    add("bell", "贝尔数", bell[:n_terms], 0, "集合划分数")

    add("collatz_steps", "Collatz 停时", [_collatz_steps(n) for n in range(1, n_terms + 1)],
        1, "从 n 出发回到 1 所需步数")

    ppar = _partitions_p(n_terms + 1)
    add("partition", "划分数 p(n)", ppar[:n_terms], 0, "n 的整数拆分个数")

    # --- 未列入校准表的一组（用于检验机器能否独立发现）---
    per = [3, 0, 2]
    while len(per) < n_terms:
        per.append(per[-2] + per[-3])
    add("perrin", "Perrin 序列", per[:n_terms], 0, "P(0)=3, P(1)=0, P(2)=2")

    pad = [1, 0, 0]
    while len(pad) < n_terms:
        pad.append(pad[-2] + pad[-3])
    add("padovan", "Padovan 序列", pad[:n_terms], 0, "P(0)=1, P(1)=P(2)=0")

    jac = [0, 1]
    while len(jac) < n_terms:
        jac.append(jac[-1] + 2 * jac[-2])
    add("jacobsthal", "Jacobsthal 序列", jac[:n_terms], 0, "J(0)=0, J(1)=1")

    fps, acc = [], 0
    for v in fib[:n_terms]:
        acc += v
        fps.append(acc)
    add("fib_prefix_sum", "斐波那契前缀和", fps[:n_terms], 0, "Σ_{k≤n} F(k)")

    # --- 前缀和型（期望阴性：它们不是 C-有限也不是超几何）---
    phi_sum, acc = [], 0
    for v in phi[:n_terms]:
        acc += v
        phi_sum.append(acc)
    add("phi_prefix_sum", "φ 的前缀和", phi_sum[:n_terms], 1, "Σ_{k≤n} φ(k)")

    tau_sum, acc = [], 0
    for v in tau[:n_terms]:
        acc += v
        tau_sum.append(acc)
    add("tau_prefix_sum", "τ 的前缀和", tau_sum[:n_terms], 1, "Σ_{k≤n} τ(k)（除数求和问题）")

    return seqs


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


# ===========================================================================
# 3. 已知递推校准表（用于判断机器是否"重新发现"了教科书结果）
# ===========================================================================
KNOWN_RECURRENCES: List[Dict[str, Any]] = [
    {"id": "fib_rec", "seq": "fibonacci", "channel": "linear", "order": 2,
     "coeffs": [1, 1], "const": 0, "name": "斐波那契递推 F(n)=F(n-1)+F(n-2)"},
    {"id": "luc_rec", "seq": "lucas", "channel": "linear", "order": 2,
     "coeffs": [1, 1], "const": 0, "name": "卢卡斯递推 L(n)=L(n-1)+L(n-2)"},
    {"id": "trib_rec", "seq": "tribonacci", "channel": "linear", "order": 3,
     "coeffs": [1, 1, 1], "const": 0, "name": "三项递推 T(n)=T(n-1)+T(n-2)+T(n-3)"},
    {"id": "pow2_rec", "seq": "powers_of_two", "channel": "linear", "order": 1,
     "coeffs": [2], "const": 0, "name": "等比递推 a(n)=2a(n-1)"},
    {"id": "mersenne_rec", "seq": "mersenne", "channel": "linear", "order": 1,
     "coeffs": [2], "const": 1, "name": "非齐次递推 a(n)=2a(n-1)+1"},
    # 注意常数项：**n^2 的二阶差分是 2 而不是 0**，三角形数是 1。
    # （2026-09-19：初始版本把常数项写成 0，机器算出 2/1 时一度被当成"未识别的候选"，
    #  核对后确认是校准表写错，机器是对的。参考值必须独立验算，不能凭印象。）
    {"id": "sq_rec", "seq": "squares", "channel": "linear", "order": 2,
     "coeffs": [2, -1], "const": 2, "name": "二阶差分恒为 2：a(n)=2a(n-1)-a(n-2)+2"},
    {"id": "tri_rec", "seq": "triangular", "channel": "linear", "order": 2,
     "coeffs": [2, -1], "const": 1, "name": "二阶差分恒为 1：a(n)=2a(n-1)-a(n-2)+1"},
    {"id": "fact_hyp", "seq": "factorial", "channel": "hyper",
     "P": [1, 1], "Q": [1], "name": "超几何闭式 a(n+1)/a(n)=n+1"},
    {"id": "cat_hyp", "seq": "catalan", "channel": "hyper",
     "P": [2, 4], "Q": [2, 1], "name": "超几何闭式 a(n+1)/a(n)=(4n+2)/(n+2)"},
    {"id": "cen_hyp", "seq": "central_binomial", "channel": "hyper",
     "P": [2, 4], "Q": [1, 1], "name": "超几何闭式 a(n+1)/a(n)=(4n+2)/(n+1)"},
    {"id": "pow2_hyp", "seq": "powers_of_two", "channel": "hyper",
     "P": [2], "Q": [1], "name": "等比：a(n+1)/a(n)=2（由定义直接可得）"},
    {"id": "sq_hyp", "seq": "squares", "channel": "hyper",
     "P": [1, 2, 1], "Q": [0, 0, 1], "name": "a(n+1)/a(n)=(n+1)^2/n^2（由定义直接可得）"},
    {"id": "tri_hyp", "seq": "triangular", "channel": "hyper",
     "P": [2, 1], "Q": [0, 1], "name": "a(n+1)/a(n)=(n+2)/n（由定义直接可得）"},
]

# 未列入校准表、但**已知满足**常系数递推的序列。
# 它们不进 KNOWN_RECURRENCES，是为了让机器"独立发现"后再由人工复核：
# 若机器在这些序列上找不出递推，说明搜索能力不足；找出来则进人工复核队列。
UNLISTED_POSITIVE = {
    "perrin": "Perrin 序列 a(n)=a(n-2)+a(n-3)",
    "padovan": "Padovan 序列 a(n)=a(n-2)+a(n-3)",
    "jacobsthal": "Jacobsthal 序列 a(n)=a(n-1)+2a(n-2)",
    "fib_prefix_sum": "斐波那契前缀和，满足非齐次递推 a(n)=a(n-1)+a(n-2)+1",
}

# 期望为"阴性"的序列：它们本就不满足常系数/超几何递推，
# 机器若在这些序列上什么都没找到，是**正确**的而不是缺陷。
# 注意作用域：这是 **C1/C2** 的期望阴性集，不是"这些序列没有结构"。
# 2026-09-19 口径修正：初版把 derangements / motzkin 也放进这里，注释写成
# "它们本就不满足常系数/超几何递推"——那句话对，但把它们当"无结构"是错的：
# 加上 C4 后立刻发现两者都满足**多项式系数**递推（见 KNOWN_PRECURENCES）。
# 教训：说"阴性"时必须写清是对哪个通道阴性，否则换一条通道就会自相矛盾。
EXPECTED_NEGATIVE = {
    "primes_count", "prime_gaps", "euler_phi", "sigma", "tau", "omega", "bigomega",
    "mobius", "radical", "bell", "collatz_steps", "partition",
    "phi_prefix_sum", "tau_prefix_sum",
}

# C4 的期望阴性：这些序列**不是 P-recursive**（生成函数非 D-finite），
# C4 在上面找不到东西是正确结果。其中 bell（egf = e^(e^x−1)）与
# partition（gf = 1/(q;q)_∞）是教科书级的非 D-finite 例子，是最好的校准件。
P_RECURSIVE_NEGATIVE = {
    "primes_count", "prime_gaps", "euler_phi", "sigma", "tau", "omega", "bigomega",
    "mobius", "radical", "bell", "collatz_steps", "partition",
    "phi_prefix_sum", "tau_prefix_sum",
}


# ===========================================================================
# 4. C1：常系数线性递推（可带常数项，即非齐次中的常数非齐次）
# ===========================================================================
def discover_linear(terms: List[int], discovery_len: int = DISCOVERY_LEN,
                    max_order: int = MAX_ORDER,
                    affine: bool = True) -> List[Dict[str, Any]]:
    """
    搜索 a(n) = c1·a(n-1) + ... + ck·a(n-k) [+ c0]。

    发现集只取前 discovery_len 项；求得系数后**必须**在后续项上外推检验。
    """
    out: List[Dict[str, Any]] = []
    n_total = len(terms)
    if discovery_len >= n_total:
        discovery_len = max(max_order + 3, n_total - 5)

    for k in range(1, max_order + 1):
        n_eq = discovery_len - k
        n_unk = k + (1 if affine else 0)
        if n_eq < n_unk + 3:
            continue
        A: List[List[Fraction]] = []
        b: List[Fraction] = []
        for n in range(k, discovery_len):
            row = [Fraction(terms[n - i]) for i in range(1, k + 1)]
            if affine:
                row.append(Fraction(1))
            A.append(row)
            b.append(Fraction(terms[n]))
        sol = _solve_exact(A, b)
        if not sol.get("unique"):
            # 已知盲区的一次显式修补：发现集上取常值的序列在 k=1/affine 下**欠定**
            # （所有方程线性等价），会被"要求解唯一"直接过滤掉，一个候选都不报。
            # 常数序列确实满足 a(n)=a(n-1)，所以这里显式报出，并标 DEGENERATE
            # ——它的价值不在"发现了新东西"，而在"不再静默漏掉"。
            if (k == 1 and affine
                    and len(set(terms[:discovery_len])) == 1):
                failed_at = None
                for n in range(discovery_len, n_total):
                    if terms[n] != terms[n - 1]:
                        failed_at = {"n": n, "expected": int(terms[n]),
                                     "predicted": int(terms[n - 1])}
                        break
                out.append({
                    "channel": "linear", "order": 1, "affine": True,
                    "coeffs": ["1"], "const": "0",
                    "statement": "a(n) = a(n-1)",
                    "discovery_len": discovery_len,
                    "n_equations": n_eq,
                    "n_extrapolation_checks": n_total - discovery_len,
                    "survived_extrapolation": failed_at is None,
                    "first_failure": failed_at,
                    "recognition": None, "evidence": "L2",
                    "degenerate": True,
                    "degenerate_note": ("发现集上取常值，k=1 的仿射方程欠定，"
                                        "此处显式报出以免静默漏检；此类候选无信息量"),
                })
            continue
        c = sol["solution"]
        if not all(_coef_ok(x) for x in c):
            continue
        const = c[-1] if affine else Fraction(0)
        coeffs = c[:k] if affine else c
        if all(x == 0 for x in coeffs):
            continue

        # 外推检验：只用发现集之外的项
        failed_at = None
        for n in range(discovery_len, n_total):
            pred = sum(coeffs[i] * terms[n - 1 - i] for i in range(k)) + const
            if pred != terms[n]:
                failed_at = {"n": n + 0, "expected": int(terms[n]),
                             "predicted": _frac_str(pred)}
                break
        survived = failed_at is None
        n_check = n_total - discovery_len
        rec = _recognize_linear(terms[0], coeffs, const)

        parts: List[str] = []
        for i in range(k):
            c = coeffs[i]
            if c == 0:
                continue
            if c == 1:
                parts.append(f"a(n-{i + 1})")
            elif c == -1:
                parts.append(f"-a(n-{i + 1})")
            else:
                parts.append(f"{_frac_str(c)}·a(n-{i + 1})")
        terms_txt = " + ".join(parts).replace("+ -", "- ") if parts else "0"
        rhs = terms_txt + (f" + {_frac_str(const)}" if const != 0 else "")
        out.append({
            "channel": "linear", "order": k, "affine": affine,
            "coeffs": [_frac_str(x) for x in coeffs],
            "const": _frac_str(const),
            "statement": f"a(n) = {rhs}" if terms_txt else "（全零系数，已弃）",
            "discovery_len": discovery_len,
            "n_equations": n_eq,
            "n_extrapolation_checks": n_check,
            "survived_extrapolation": survived,
            "first_failure": failed_at,
            "recognition": rec,
            "evidence": "L2",
        })
    return out


def _fmt_coef(c: Fraction) -> str:
    if c == 1:
        return ""
    if c == -1:
        return "-"
    return _frac_str(c)


def _recognize_linear(a0: int, coeffs: List[Fraction], const: Fraction) -> Optional[Dict[str, str]]:
    """与已知递推表比对。**不猜测**：匹配不上就返回 None。"""
    for rec in KNOWN_RECURRENCES:
        if rec["channel"] != "linear":
            continue
        if len(rec["coeffs"]) != len(coeffs):
            continue
        if [Fraction(x) for x in rec["coeffs"]] != list(coeffs):
            continue
        if Fraction(rec["const"]) != const:
            continue
        return {"known_id": rec["id"], "known_name": rec["name"],
                "note": "该递推是教科书已知结果，此处由搜索独立重新发现（机制校准件）"}
    return None


# ===========================================================================
# 5. C2：一阶有理（超几何）递推
# ===========================================================================
HYPER_DEGREES = [(0, 1), (1, 1), (0, 2), (1, 2), (2, 2), (2, 1)]


def discover_hypergeometric(terms: List[int],
                            discovery_len: int = DISCOVERY_LEN) -> List[Dict[str, Any]]:
    """
    搜索 a(n+1)/a(n) = P(n)/Q(n)，其中 deg P ≤ 2，deg Q ≤ 2。

    做法：把 P、Q 的系数合起来作为未知向量，对每个 n 列出齐次线性方程
        Σ_j p_j n^j · a(n) − Σ_j q_j n^j · a(n+1) = 0
    取零空间；维数必须为 1（唯一方向），否则说明该形式不唯一或未定。
    """
    out: List[Dict[str, Any]] = []
    n_total = len(terms)
    if discovery_len >= n_total - 1:
        discovery_len = n_total - 6
    if discovery_len < 6:
        return out

    for dp, dq in HYPER_DEGREES:
        n_unk = (dp + 1) + (dq + 1)
        n_eq = discovery_len - 1
        if n_eq < n_unk + 3:
            continue
        A: List[List[Fraction]] = []
        for n in range(discovery_len - 1):
            row: List[Fraction] = []
            for j in range(dp + 1):
                row.append(Fraction(terms[n]) * Fraction(n) ** j)
            for j in range(dq + 1):
                row.append(-Fraction(terms[n + 1]) * Fraction(n) ** j)
            A.append(row)
        basis = _nullspace(A)
        if len(basis) != 1:
            continue
        v = basis[0]
        if not all(_coef_ok(x) for x in v):
            continue
        # 归一化：整体缩放使所有系数为互素整数（分母通分后除以 gcd）
        den = 1
        for x in v:
            den = den * x.denominator // _gcd(den, x.denominator)
        ints = [int(x * den) for x in v]
        g = 0
        for x in ints:
            g = _gcd(g, abs(x))
        if g == 0:
            continue
        ints = [x // g for x in ints]
        P = ints[:dp + 1]
        Q = ints[dp + 1:]
        if all(x == 0 for x in Q):
            continue

        # 外推检验
        failed_at = None
        for n in range(discovery_len - 1, n_total - 1):
            pv = sum(P[j] * n ** j for j in range(dp + 1))
            qv = sum(Q[j] * n ** j for j in range(dq + 1))
            if qv == 0:
                failed_at = {"n": n, "detail": "分母 Q(n) 在该点为 0，比值无定义"}
                break
            if terms[n] * pv != terms[n + 1] * qv:
                failed_at = {"n": n, "detail":
                             f"P(n)·a(n)={pv * terms[n]} ≠ Q(n)·a(n+1)={qv * terms[n + 1]}"}
                break
        survived = failed_at is None
        rec = _recognize_hyper(P, Q)
        out.append({
            "channel": "hyper", "degP": dp, "degQ": dq,
            "P": P, "Q": Q,
            "statement": f"a(n+1)/a(n) = ({_poly_str(P)}) / ({_poly_str(Q)})",
            "discovery_len": discovery_len,
            "n_equations": n_eq,
            "n_extrapolation_checks": (n_total - 1) - (discovery_len - 1),
            "survived_extrapolation": survived,
            "first_failure": failed_at,
            "recognition": rec,
            "evidence": "L2",
        })
    return _dedup_hyper(out)


def _dedup_hyper(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    同一有理函数会被不同的 (degP, degQ) 组合重复找到（例如 `2/1` 在 (0,1) 与 (1,1)
    下都成立）。用"在固定点上的取值序列"做指纹去重，保留次数最低且通过检验的那一条。
    """
    seen: Dict[Tuple[Fraction, ...], Dict[str, Any]] = {}
    for c in cands:
        P, Q = c["P"], c["Q"]
        key: List[Fraction] = []
        valid = True
        for n in range(1, 16):
            qv = sum(Q[j] * n ** j for j in range(len(Q)))
            if qv == 0:
                valid = False
                break
            key.append(Fraction(sum(P[j] * n ** j for j in range(len(P))), qv))
        if not valid:
            continue
        k = tuple(key)
        cur = seen.get(k)
        if cur is None:
            seen[k] = c
            continue
        better = ((c["survived_extrapolation"] and not cur["survived_extrapolation"]) or
                  (c["survived_extrapolation"] == cur["survived_extrapolation"] and
                   (c["degP"] + c["degQ"]) < (cur["degP"] + cur["degQ"])))
        if better:
            seen[k] = c
    return sorted(seen.values(), key=lambda c: (not c["survived_extrapolation"],
                                                c["degP"] + c["degQ"], c["degP"]))


def _poly_str(coef: List[int]) -> str:
    parts = []
    for j, c in enumerate(coef):
        if c == 0:
            continue
        if j == 0:
            parts.append(str(c))
        elif j == 1:
            parts.append(f"{c}n" if abs(c) != 1 else ("n" if c > 0 else "-n"))
        else:
            parts.append(f"{c}n^{j}" if abs(c) != 1 else (f"n^{j}" if c > 0 else f"-n^{j}"))
    return " + ".join(parts) if parts else "0"


def _trim_poly(coef: List[int]) -> List[int]:
    """去掉多项式尾部的零系数，使 `1+0n` 与 `1` 被视为同一多项式。"""
    c = list(coef)
    while len(c) > 1 and c[-1] == 0:
        c.pop()
    return c


def _recognize_hyper(P: List[int], Q: List[int]) -> Optional[Dict[str, str]]:
    P, Q = _trim_poly(P), _trim_poly(Q)
    for rec in KNOWN_RECURRENCES:
        if rec["channel"] != "hyper":
            continue
        rp, rq = _trim_poly(list(rec["P"])), _trim_poly(list(rec["Q"]))
        if len(rp) != len(P) or len(rq) != len(Q):
            continue
        # 归一化只定到整体非零倍，故按"成比例"判定，而不是逐个系数相等
        a = [Fraction(x) for x in P]
        b = [Fraction(x) for x in rp]
        c = [Fraction(x) for x in Q]
        d = [Fraction(x) for x in rq]
        scale = None
        ok = True
        for x, y in list(zip(a, b)) + list(zip(c, d)):
            if y == 0:
                if x != 0:
                    ok = False
                    break
                continue
            s = x / y
            if scale is None:
                scale = s
            elif s != scale:
                ok = False
                break
        if ok and scale is not None:
            return {"known_id": rec["id"], "known_name": rec["name"],
                    "note": "教科书已知的超几何闭式，由搜索独立重新发现（机制校准件）"}
    return None


# ===========================================================================
# 6. C3：增长率（数值估计，带稳定性）
# ===========================================================================
def _lstsq(xs: List[float], ys: List[float]) -> Tuple[float, float, float]:
    """一元最小二乘 y = a·x + b，返回 (a, b, 残差平方和)。"""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0, my, sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    sse = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys))
    return a, b, sse


def estimate_growth(terms: List[int]) -> Dict[str, Any]:
    """
    估计增长类型：**指数模型**与**多项式模型**两个假设做最小二乘，比残差。

    - 指数模型：log a(n) ≈ n·log λ + c  → 残差小则判指数增长，底数 λ = e^a
    - 多项式模型：log a(n) ≈ k·log n + c → 残差小则判多项式增长，次数 k = a

    两个模型的残差都大时判为"其他/未知"（如 exp(√n) 型的划分数会落在这一类）。

    全部是 L2 数值证据：只给估计值、两模型残差比与窗口稳定性，**不给确定结论**。
    """
    import math
    n_total = len(terms)
    tail_start = max(2, n_total - max(8, n_total // 3))
    pts = [(n, terms[n]) for n in range(tail_start, n_total) if terms[n] > 1]
    if len(pts) < 5:
        return {"type": "unknown", "reason": "尾部可用于取对数的项不足 5 个（含零项或过小）",
                "evidence": "L2"}

    ns = [float(n) for n, _ in pts]
    logs = [math.log(v) for _, v in pts]
    a_exp, _b1, sse_exp = _lstsq(ns, logs)
    lns = [math.log(n) for n in ns]
    a_poly, _b2, sse_poly = _lstsq(lns, logs)
    mean_log = sum(logs) / len(logs)
    sst = sum((y - mean_log) ** 2 for y in logs)

    # 超指数判据：log a(n)/n 在后半窗口显著大于前半（阶乘、贝尔数属于此类）
    half = len(pts) // 2
    slope_first = sum(logs[i] / ns[i] for i in range(half)) / max(1, half)
    slope_second = sum(logs[i] / ns[i] for i in range(half, len(pts))) / max(1, len(pts) - half)
    # 相对增幅与绝对增幅都要满足：抓 n! 这类超指数，同时避免卡特兰数被误判。
    # 实测 log a(n)/n 在 [40,60] 上：n! 由 3.21 升到 3.47（相对 1.08、绝对 0.26），
    # 卡特兰数由 1.248 升到 1.284（相对 1.03、绝对 0.036）→ 后者不应判为超指数。
    super_exp = (slope_second > slope_first * 1.05
                 and slope_second - slope_first > 0.05)

    base = {
        "n_points": len(pts),
        "window": [tail_start, n_total - 1],
        "sse_exponential_model": round(sse_exp, 8),
        "sse_polynomial_model": round(sse_poly, 8),
        "total_variance_sst": round(sst, 8),
        "evidence": "L2",
        "method": ("尾部项分别拟合 log a(n)~n（指数）与 log a(n)~log n（多项式），"
                   "比较残差平方和；再用 log a(n)/n 的走向识别超指数型"),
        "caveat": ("有限窗口内的数值比较：两模型残差接近时结论不可靠；"
                   "拟合优度不足时本模块宁可判 'neither'，也不硬给一个类型。"),
    }
    best_sse = min(sse_exp, sse_poly)
    if super_exp:
        base.update({"type": "super_exponential",
                     "log_over_n_first_half": round(slope_first, 4),
                     "log_over_n_second_half": round(slope_second, 4),
                     "note": "增长快于任何 λ^n（如 n!、贝尔数）"})
    elif sst > 0 and best_sse / sst > 0.05:
        base.update({"type": "neither",
                     "relative_residual_of_better_model": round(best_sse / sst, 4),
                     "slightly_better": "exponential" if sse_exp < sse_poly else "polynomial",
                     "note": ("两个模型都不拟合（残差占总方差 > 5%），"
                              "常见于 n/log n、exp(sqrt n) 一类的中间型增长")})
    elif sse_exp < sse_poly:
        ratio = (sse_poly / sse_exp) if sse_exp > 0 else float("inf")
        lam = math.exp(a_exp)
        base.update({"type": "exponential", "base_lambda": round(lam, 6),
                     "residual_ratio": round(ratio, 3)})
        if ratio < 1.5:
            base["weak_evidence"] = "两模型残差比 < 1.5，指数型的优势不明显，此判定脆弱"
        if lam < 1.5:
            base["subexponential_warning"] = (
                f"估计底数 λ≈{lam:.3f} 接近 1：窗口内无法区分'真指数增长'与"
                f"exp(sqrt n)、n^(log n) 这类次指数增长，此处不应当作结论使用")
    else:
        ratio = (sse_exp / sse_poly) if sse_poly > 0 else float("inf")
        base.update({"type": "polynomial_like", "degree_estimate": round(a_poly, 4),
                     "residual_ratio": round(ratio, 3)})
        if ratio < 1.5:
            base["weak_evidence"] = "两模型残差比 < 1.5，多项式型的优势不明显，此判定脆弱"
    return base


# ===========================================================================
# 6.5 由递推反推增长率：C1 → 特征多项式 → 特征根 → 增长底数
# ===========================================================================
# 这一节把三条通道里原本**互相独立**的 C1 与 C3 接上了。
#
# 原理（教科书结论，此处不声称证明）：
#   若 a(n) = c₁a(n-1) + … + c_k a(n-k)（+ 常数 d），则齐次部分的特征多项式为
#       x^k − c₁ x^(k−1) − … − c_k
#   记其根为 r₁,…,r_k。则
#     · 若 max|rᵢ| > 1，增长为 |r_max|^n（常数项只贡献低阶项或 n^m 项，不改变主项）；
#     · 若主根模 = 1 且 1 是 m 重根，齐次情形增长 ~ n^(m−1)，
#       带非零常数项时增长 ~ n^m（平方数即此例：x²−2x+1=(x−1)²，d=2 → n²）。
#
# 这样得到的底数是**由递推结构决定的**，不依赖尾部窗口拟合，
# 因此可以用来给 C3 的数值估计作交叉检验，也能消解"λ 接近 1 时无法区分
# 指数与次指数"的那类警告——只要递推本身已经被外推检验接受。
POLY_ROOT_ITERS = 400
POLY_ROOT_TOL = 1e-13


def characteristic_polynomial(coeffs: List[Any]) -> List[float]:
    """由 a(n)=c₁a(n-1)+…+c_k a(n-k) 给出特征多项式（**高次在前**）。

    返回 [1, −c₁, −c₂, …, −c_k]。
    """
    return [1.0] + [-float(Fraction(c)) for c in coeffs]


def _eval_monic(c: List[complex], z: complex, n: int) -> complex:
    """Horner 求值：z^n + c[0]z^(n−1) + … + c[n−1]。"""
    v = 1.0 + 0j
    for i in range(n):
        v = v * z + c[i]
    return v


def polynomial_roots(coefs_high_first: List[float],
                     iters: int = POLY_ROOT_ITERS,
                     tol: float = POLY_ROOT_TOL) -> List[complex]:
    """Durand–Kerner（Weierstrass）迭代求全部复根。**数值**方法，非精确。"""
    n = len(coefs_high_first) - 1
    if n <= 0:
        return []
    lead = coefs_high_first[0]
    if abs(lead) < 1e-300:
        raise ValueError("首项系数为零，不是合法多项式")
    c = [complex(x) / complex(lead) for x in coefs_high_first[1:]]
    roots = [(0.4 + 0.9j) ** k for k in range(n)]
    for _ in range(iters):
        new: List[complex] = []
        for i, z in enumerate(roots):
            num = _eval_monic(c, z, n)
            den = 1.0 + 0j
            for j, w in enumerate(roots):
                if j != i:
                    den *= (z - w)
            new.append(z - num / den if abs(den) > 1e-300 else z)
        if max(abs(new[i] - roots[i]) for i in range(n)) < tol:
            roots = new
            break
        roots = new
    return roots


def growth_from_recurrence(coeffs: List[Any], const: Any) -> Dict[str, Any]:
    """由 C1 递推的系数直接推出增长率类型与底数（数值求根，L2）。"""
    try:
        poly = characteristic_polynomial(coeffs)
        roots = polynomial_roots(poly)
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        return {"type": "unknown", "reason": f"特征多项式求根失败：{exc}",
                "evidence": "L2"}
    if not roots:
        return {"type": "unknown", "reason": "阶数为 0", "evidence": "L2"}

    moduli = [abs(r) for r in roots]
    r_max = max(moduli)
    # 1 的重数（用于主根模≈1 时的多项式次数）
    tol = 1e-8
    mult_one = sum(1 for r in roots if abs(abs(r) - 1.0) < tol and abs(r.imag) < tol)
    d = Fraction(const)
    base: Dict[str, Any] = {
        "evidence": "L2",
        "method": ("由 a(n)=c₁a(n-1)+…+c_k a(n-k)(+d) 的特征多项式 "
                   "x^k−c₁x^(k−1)−…−c_k 求根（Durand–Kerner），取最大模为主项"),
        "characteristic_polynomial_high_first": [round(x, 10) for x in poly],
        "root_moduli": [round(m, 8) for m in sorted(moduli, reverse=True)],
        "caveat": ("根由**数值迭代**得到，是近似值（不是精确代数数）；"
                   "递推系数本身是精确有理的，但求根步骤不是。"),
    }
    if r_max > 1.0 + 1e-9:
        base.update({"type": "exponential", "base_exact_from_recurrence": round(r_max, 8),
                     "note": "主项由递推结构唯一确定，不依赖尾部窗口拟合"})
        return base
    # 主根模 ≈ 1（含复数单位根，如周期序列）：增长至多是多项式
    # 次数公式（可直接用 Δ 算子验证）：设 1 是 m 重根。
    #   · 齐次 (d=0)：(E−1)^m a = 0 ⇒ a 为次数 ≤ m−1 的多项式；
    #   · 常数强迫 (d≠0)：(E−1)^m a = d ⇒ 需要次数恰为 m（因 (E−1) 使次数降 1）。
    #   平方数是原型：a(n)=2a(n−1)−a(n−2)+2 ⇒ (E−1)²a=2 ⇒ a ~ n²，即 m=2。
    #   （初版误写成 m+1，被与窗口拟合的对账打出 deg=3 vs 2.0，据此改正。）
    deg = max(mult_one if d != 0 else mult_one - 1, 0)
    base.update({"type": "polynomial_like", "degree_from_recurrence": deg,
                 "multiplicity_of_root_1": mult_one,
                 "affine_const_nonzero": d != 0,
                 "note": ("主根模为 1：齐次情形 ~ n^(m−1)，"
                          "带非零常数项时 ~ n^m（m 为 1 的重数）")})
    return base


def reconcile_growth(growth: Dict[str, Any],
                     lin_cands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """把 C3 的窗口估计与 C1 的结构推演对账。

    返回两者是否一致、以及在有递推证据时是否消解了次指数警告。
    """
    survived = [c for c in lin_cands
                if c.get("survived_extrapolation") and c["channel"] == "linear"]
    if not survived:
        return {"available": False,
                "reason": "该序列没有通过外推检验的 C1 递推，无法用结构推演对账"}
    c = survived[0]
    rec_g = growth_from_recurrence(c["coeffs"], c["const"])
    out: Dict[str, Any] = {
        "available": True,
        "recurrence_used": c["statement"],
        "recurrence_implied": rec_g,
        "window_estimate_type": growth.get("type"),
        "evidence": "L2",
    }
    if rec_g.get("type") == "unknown":
        out["agrees"] = None
        out["note"] = "结构侧求根失败，无法对账"
        return out

    agrees = rec_g["type"] == growth.get("type")
    detail: Dict[str, Any] = {}
    if rec_g["type"] == "exponential" and growth.get("base_lambda") is not None:
        exact = rec_g["base_exact_from_recurrence"]
        got = growth["base_lambda"]
        detail = {"base_from_recurrence": exact, "base_from_window": got,
                  "relative_gap": round(abs(exact - got) / exact, 6)}
        # 纯指数型 C-finite 的窗口偏差应远小于 1%；超过 1% 说明二者至少有一方有问题
        agrees = agrees and detail["relative_gap"] < 0.01
    elif rec_g["type"] == "polynomial_like" and growth.get("degree_estimate") is not None:
        detail = {"degree_from_recurrence": rec_g["degree_from_recurrence"],
                  "degree_from_window": growth["degree_estimate"],
                  "absolute_gap": round(abs(rec_g["degree_from_recurrence"]
                                            - growth["degree_estimate"]), 4)}
        agrees = agrees and detail["absolute_gap"] < 0.15
    out["agrees"] = agrees
    out["detail"] = detail
    # 递推给出的底数 > 1.2 时，"λ 接近 1、无法区分指数与次指数"的警告即被消解
    if (growth.get("subexponential_warning")
            and rec_g.get("type") == "exponential"
            and rec_g.get("base_exact_from_recurrence", 0) > 1.2):
        out["resolves_subexp_warning"] = True
        out["resolution_note"] = (
            f"窗口估计的次指数警告在此消解：递推 {c['statement']} 的特征根给出"
            f"确定底数 {rec_g['base_exact_from_recurrence']}，增长确为指数型。"
            f"（警告本身没错——单看数值窗口确实分不出来；是递推证据补上了缺口。）")
    else:
        out["resolves_subexp_warning"] = False
    out["note"] = ("两条独立路径（尾部窗口拟合 vs 递推特征根）是否指向同一结论；"
                   "一致不代表正确，但**不一致一定有问题**。")
    return out


# ===========================================================================
# 6.6 C4：多项式系数递推（P-recursive / holonomic）
# ===========================================================================
# C2 只能拿一阶有理（超几何）闭式，覆盖面太窄：错排数、莫茨金数都拿不到。
# C4 把它们纳入：找
#       p_0(n)·a(n) + p_1(n)·a(n-1) + … + p_k(n)·a(n-k) = 0
# 其中 p_i 是 n 的次数 ≤ max_deg 的多项式。
#
# 序列 P-recursive ⟺ 其（普通）生成函数 D-finite（满足线性 ODE）。
# 这条等价性是教科书结论，此处**只引用不证明**。它同时给出了本通道的
# **期望阴性**校准件：贝尔数的指数生成函数是 e^(e^x−1)，非 D-finite；
# 划分数 p(n) 的生成函数 1/(q;q)_∞ 亦非 D-finite。所以 C4 在它们身上
# 找不到东西是**正确结果**，不是失败。
P_ORDER_MAX = 3      # 最大阶数 k
P_DEG_MAX = 2        # p_i(n) 的最大次数
P_TERM_ABS_BOUND = 10 ** 45  # 项太大时精确消元会爆，跳过并如实记录


# ===========================================================================
# 6.7b C4 的模素数消元（取代精确有理消元）
# ---------------------------------------------------------------------------
# 为什么换：隔项抽样 a(2n) 会让项在原序列第 30 项就超过 1e45，Fraction 消元
# 的分母呈指数膨胀。旧版做法是「超过 P_TERM_ABS_BOUND 就跳过」——写在 reason
# 里算诚实，但它让两组长不出结果的原因变成「我们放弃了」而不是「它没有」。
# 这是**归因错误**：上一轮把它写成「能力缺口，根因 P_DEG_MAX 过小」，实测并不是。
#
# 换成三段式：模若干大素数消元 → 有理重建 → **精确整数复核**。
# 复核是精确的，所以放得再宽也不会放进假阳性；重建失败只导致漏报，不会错报。
# ===========================================================================
# 梅森素数指数（2^e − 1 为素数）。运行时仍用 Miller–Rabin 验一遍：
# 万一记错、放进合数，后面的精确复核也只会让结果变少，不会变错。
_MERSENNE_EXPONENTS = (61, 89, 107, 127)
_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
             53, 59, 61, 67, 71, 73, 79, 83, 89, 97)


def _is_probable_prime(n: int) -> bool:
    """Miller–Rabin（前 25 个素数作基）。足够本用途：合数漏过也只影响候选量。"""
    if n < 2:
        return False
    for p in _MR_BASES:
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def mod_primes() -> List[int]:
    ps = []
    for e in _MERSENNE_EXPONENTS:
        p = 2 ** e - 1
        if _is_probable_prime(p):
            ps.append(p)
    return ps


def _nullspace_mod(A: List[List[int]], p: int) -> List[List[int]]:
    """齐次系统 A·x ≡ 0 (mod p) 的一组基。p 为素数时非零元必可逆。"""
    if not A:
        return []
    n = len(A[0])
    rows = [[x % p for x in row] for row in A]
    piv: List[int] = []
    r = 0
    for c in range(n):
        sel = None
        for i in range(r, len(rows)):
            if rows[i][c]:
                sel = i
                break
        if sel is None:
            continue
        rows[r], rows[sel] = rows[sel], rows[r]
        inv = pow(rows[r][c], p - 2, p)
        rows[r] = [(x * inv) % p for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c]:
                f = rows[i][c]
                rows[i] = [(a - f * b) % p for a, b in zip(rows[i], rows[r])]
        piv.append(c)
        r += 1
        if r == len(rows):
            break
    free = [c for c in range(n) if c not in piv]
    basis: List[List[int]] = []
    for fc in free:
        v = [0] * n
        v[fc] = 1
        for i, c in enumerate(piv):
            v[c] = (-rows[i][fc]) % p
        basis.append(v)
    return basis


def rational_reconstruct(x: int, p: int) -> Optional[Fraction]:
    """由 x ≡ num·den⁻¹ (mod p) 还原 num/den。

    |num| ≤ sqrt(p/2) 且 0 < den ≤ sqrt(p/2) 时解唯一；不存在则返回 None —— **不猜**。
    """
    x %= p
    if x == 0:
        return Fraction(0)
    bound = math.isqrt(p // 2)
    u0, u1 = p, 0
    v0, v1 = x, 1
    while abs(v0) > bound or abs(v1) > bound:
        if v0 == 0:
            return None
        q = u0 // v0
        u0, v0 = v0, u0 - q * v0
        u1, v1 = v1, u1 - q * v1
    num, den = v0, v1
    if den < 0:
        num, den = -num, -den
    if den == 0 or abs(num) > COEF_BOUND or den > COEF_BOUND:
        return None
    if (num - x * den) % p != 0:
        return None
    g = _gcd(abs(num), den)
    if g == 0:
        return None
    return Fraction(num // g, den // g)


def _prec_nullspace_candidates(
        A: List[List[int]], n_unk: int
) -> Tuple[List[Tuple[List[int], int]], Dict[str, Any]]:
    """跨多个大素数求零空间，重建为**整数**系数向量。

    返回 (候选表[(向量, 多少个素数重建出同一个结果)], 诊断)。
    零空间维数不为 1 的素数直接弃用：维数 >1 意味着方程不足以定出形式。
    """
    diag: Dict[str, Any] = {"nullity_by_prime": {}, "primes_examined": 0,
                            "n_reconstruct_failed": 0}
    seen: Dict[Tuple[int, ...], int] = {}
    for p in mod_primes():
        diag["primes_examined"] += 1
        bs = _nullspace_mod(A, p)
        diag["nullity_by_prime"][str(p.bit_length())] = len(bs)
        if len(bs) != 1:
            continue
        v = bs[0]
        nz = next((i for i, x in enumerate(v) if x), None)
        if nz is None:
            continue
        inv = pow(v[nz], p - 2, p)
        fr: List[Optional[Fraction]] = [
            rational_reconstruct((x * inv) % p, p) for x in v]
        if any(x is None for x in fr):
            diag["n_reconstruct_failed"] += 1
            continue
        fr = [x for x in fr if x is not None]  # 收窄类型，非空已保证
        den = 1
        for x in fr:
            den = den * x.denominator // _gcd(den, x.denominator)
            if den > COEF_BOUND:
                diag["n_reconstruct_failed"] += 1
                break
        else:
            ints = [int(x * den) for x in fr]
            g = 0
            for x in ints:
                g = _gcd(g, abs(x))
            if g == 0:
                continue
            ints = [x // g for x in ints]
            if any(abs(x) > COEF_BOUND for x in ints):
                diag["n_reconstruct_failed"] += 1
                continue
            # 整体变号是同一个关系，统一归一到「首个非零元为正」
            first_nz = next((x for x in ints if x != 0), 0)
            if first_nz < 0:
                ints = [-x for x in ints]
            seen[tuple(ints)] = seen.get(tuple(ints), 0) + 1
    cands = sorted(seen.items(), key=lambda kv: -kv[1])
    return [([int(x) for x in k], c) for k, c in cands], diag


def discover_polynomial_recurrence(terms: List[int],
                                   discovery_len: int = DISCOVERY_LEN,
                                   max_order: int = P_ORDER_MAX,
                                   max_deg: int = P_DEG_MAX,
                                   ) -> List[Dict[str, Any]]:
    """C4：搜索 Σ_i p_i(n)·a(n-i) = 0，deg p_i ≤ max_deg。

    做法与 C2 同构：把所有 p_i 的系数排成一个未知向量，对每个 n 列一个齐次
    方程，取零空间。零空间维数必须**恰好为 1**——大于 1 说明方程不足以定出
    形式（欠定），报出来就是过拟合。
    """
    out: List[Dict[str, Any]] = []
    n_total = len(terms)
    if discovery_len >= n_total:
        discovery_len = max(max_order + 6, n_total - 6)
    if discovery_len < 8:
        return out

    for k in range(1, max_order + 1):
        for deg in range(0, max_deg + 1):
            n_unk = (k + 1) * (deg + 1)
            n_eq = discovery_len - k
            if n_eq < n_unk + 4:      # 留出余量，宁可欠报也不过拟合
                continue
            A: List[List[int]] = []
            for n in range(k, discovery_len):
                row: List[int] = []
                for i in range(k + 1):
                    a = terms[n - i]
                    row.extend(a * n ** j for j in range(deg + 1))
                A.append(row)
            vecs, diag = _prec_nullspace_candidates(A, n_unk)
            for ints, n_agree in vecs:
                polys = [ints[i * (deg + 1):(i + 1) * (deg + 1)]
                         for i in range(k + 1)]
                if all(x == 0 for x in polys[0]):
                    continue   # p_0 ≡ 0：解不出 a(n)，不是递推

                def _resid(n: int) -> int:
                    s = 0
                    for i in range(k + 1):
                        pv = sum(polys[i][j] * n ** j for j in range(deg + 1))
                        s += pv * terms[n - i]
                    return s

                # 精确复核（发现集内）。模消元只保证 mod p 相容；是否真在 ℚ 上
                # 成立必须用整数重算一遍，算不过就丢。这一步是把「不猜」落到实处的
                # 地方：Fermat 逆、有理重建都可能失真，但整数复核不会。
                if any(_resid(n) != 0 for n in range(k, discovery_len)):
                    continue

                # 外推检验：发现集之外的每一项都必须让 Σ p_i(n)·a(n-i) 恰为 0
                failed_at = None
                n_check = 0
                for n in range(discovery_len, n_total):
                    s = _resid(n)
                    n_check += 1
                    if s != 0:
                        failed_at = {"n": n,
                                     "detail": f"Σ p_i(n)·a(n-i) = {s} ≠ 0"}
                        break
                parts = []
                for i in range(k + 1):
                    ps = _poly_str(polys[i])
                    if ps == "0":
                        continue
                    parts.append(f"({ps})·a(n-{i})" if i else f"({ps})·a(n)")
                out.append({
                    "channel": "prec", "order": k, "deg": deg,
                    "polys": polys,
                    "statement": (" + ".join(parts).replace("+ -", "- ")
                                  + " = 0"),
                    "discovery_len": discovery_len,
                    "n_equations": n_eq,
                    "n_extrapolation_checks": n_check,
                    "survived_extrapolation": failed_at is None,
                    "first_failure": failed_at,
                    # 所有 p_i 都是常数多项式时，这条 C4 其实退化成 C1（常系数）
                    "subsumes_linear": all(all(x == 0 for x in p[1:])
                                           for p in polys),
                    "recognition": _recognize_prec(polys),
                    "solver": ("modular-elimination + rational-reconstruction "
                               "+ exact-integer-recheck"),
                    "n_primes_agreeing": n_agree,
                    "evidence": "L2",
                })
    return _dedup_prec(out)


def _dedup_prec(cands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """同一条递推会被 (k,deg) 与 (k,deg+1) 重复报出，按多项式去尾零后去重。"""
    seen: Dict[str, Dict[str, Any]] = {}
    for c in cands:
        if c.get("skipped"):
            continue
        key = "|".join(",".join(str(x) for x in _trim_poly(p)) for p in c["polys"])
        if key not in seen:
            seen[key] = c
        else:
            # 保留更"低阶低次"的那一版（更可能是真形式而非过拟合）
            old = seen[key]
            if (c["order"], c["deg"]) < (old["order"], old["deg"]):
                seen[key] = c
    skipped = [c for c in cands if c.get("skipped")]
    return sorted(seen.values(), key=lambda c: (c["order"], c["deg"])) + skipped


# C4 的已知形式对照表（教科书递推，用于校准；匹配不上就 None，不猜）
# 系数一律**低次在前**：[c0, c1] 表示 c0 + c1·n。
# （初版把错排数/莫茨金/卡特兰三组的符号全写反了，被"机器找到的形式 vs 表"
#   对不上暴露出来；下面每组都已在小 n 上手算验过。）
KNOWN_PRECURENCES: List[Dict[str, Any]] = [
    # D(n) − (n−1)D(n−1) − (n−1)D(n−2) = 0
    {"id": "derangements_prec", "seq": "derangements",
     "polys": [[1], [1, -1], [1, -1]],
     "name": "错排数 D(n) = (n−1)·(D(n−1)+D(n−2))"},
    # (n+2)M(n) − (2n+1)M(n−1) − (3n−3)M(n−2) = 0
    {"id": "motzkin_prec", "seq": "motzkin",
     "polys": [[2, 1], [-1, -2], [3, -3]],
     "name": "莫茨金数 (n+2)M(n) = (2n+1)M(n−1) + (3n−3)M(n−2)"},
    # (n+1)C(n) − 2(2n−1)C(n−1) = 0
    {"id": "catalan_prec", "seq": "catalan",
     "polys": [[1, 1], [2, -4]],
     "name": "卡特兰数 (n+1)C(n) = 2(2n−1)C(n−1)"},
    # n·C(n) − 2(2n−1)C(n−1) = 0
    {"id": "central_binomial_prec", "seq": "central_binomial",
     "polys": [[0, 1], [2, -4]],
     "name": "中心二项式 n·C(n) = 2(2n−1)C(n−1)"},
    # a(n) − n·a(n−1) = 0
    {"id": "factorial_prec", "seq": "factorial",
     "polys": [[1], [0, -1]],
     "name": "阶乘 a(n) = n·a(n−1)"},
]


def _recognize_prec(polys: List[List[int]]) -> Optional[Dict[str, str]]:
    """与已知表比对；允许整体差一个 −1 倍（归一化只定符号到"首非零为正"，
    而表中给出的是最自然的写法，两者可能差一个整体符号）。"""
    got = [_trim_poly(p) for p in polys]
    neg = [[-x for x in p] for p in got]
    for rec in KNOWN_PRECURENCES:
        want = [_trim_poly(p) for p in rec["polys"]]
        if got == want or neg == want:
            return {"known_id": rec["id"], "known_name": rec["name"],
                    "note": "教科书已知的多项式系数递推，由搜索独立重新发现（校准件）"}
    return None


# ===========================================================================
# 6.7 变换算子下的封闭性（S9 的"套娃"层）
# ===========================================================================
# 把序列空间看成**对象**，把经典变换看成**算子**，问两个问题：
#   Q1 封闭性：若 a 有性质 P（C-finite / P-recursive），变换后是否还能**找到** P？
#   Q2 不动点：哪些序列在某个变换下不变？
#
# 教科书结论（只引用，不证明）：C-finite 与 P-recursive（holonomic）类在
# 差分、部分和、二项变换下都是**封闭**的。所以：
#   · 变换后**找不到**，不是"性质丢失"，而是**我的搜索失败了**——
#     这恰恰是本层最该报出来的东西，因为它暴露搜索能力的边界。
#   · 变换后**找到了**，才是封闭性的正面证据。
TRANSFORMS: Dict[str, Any] = {
    "diff": ("差分 Δa(n)=a(n+1)−a(n)", lambda a: [a[i + 1] - a[i] for i in range(len(a) - 1)]),
    "prefix_sum": ("部分和 S(n)=Σ_{k≤n} a(k)",
                   lambda a: [sum(a[:i + 1]) for i in range(len(a))]),
    "binomial": ("二项变换 b(n)=Σ_k C(n,k)a(k)",
                 lambda a: [sum(math.comb(n, k) * a[k] for k in range(n + 1))
                            for n in range(len(a))]),
    "inv_binomial": ("逆二项变换 b(n)=Σ_k (−1)^(n−k)C(n,k)a(k)",
                     lambda a: [sum((-1) ** (n - k) * math.comb(n, k) * a[k]
                                    for k in range(n + 1))
                                for n in range(len(a))]),
    "even_subseq": ("偶数项子序列 b(n)=a(2n)", lambda a: a[::2]),
    "multiply_n": ("乘自变量 b(n)=n·a(n)",
                   lambda a: [n * a[n] for n in range(len(a))]),
}

# 这三个变换在理论上对 C-finite / P-recursive **都封闭**；
# 其余（偶数项子序列、乘 n）只对部分子类封闭，不作为封闭性判据。
CLOSED_TRANSFORMS = {"diff", "prefix_sum", "binomial"}


def _has(terms: List[int], channel: str) -> bool:
    if channel == "linear":
        return any(c.get("survived_extrapolation")
                   for c in discover_linear(terms))
    return any(c.get("survived_extrapolation")
               for c in discover_polynomial_recurrence(terms))


def transform_closure(n_terms: int = N_TERMS) -> Dict[str, Any]:
    """对每个序列施加每个变换，检查性质是否被**找到**、以及是否不动。"""
    seqs = build_sequences(n_terms + 2)
    rows: List[Dict[str, Any]] = []
    for s in seqs:
        base_lin = _has(s["terms"], "linear")
        base_prec = _has(s["terms"], "prec")
        for tf, (_cn, fn) in TRANSFORMS.items():
            try:
                tv = fn(s["terms"])
            except (IndexError, ValueError, OverflowError):
                continue
            if len(tv) < 20:      # 项数太少，搜索无意义
                continue
            after_lin = _has(tv, "linear")
            after_prec = _has(tv, "prec")
            # 输出可能**退化**：逆二项变换会把多项式型序列打成几乎全零
            # （Σ(−1)^(n−k)C(n,k)·k^d = 0 对 n > d 成立）。这类输出不是
            # "性质丢失"，是"输出本身没内容了"，必须分开记。
            tail = tv[len(tv) // 2:]
            degenerate_out = (all(x == 0 for x in tail)
                              or len(set(tail)) <= 2)
            # 变换常使递推阶数上升（部分和 +1 阶、乘 n 可翻倍）。
            # 所以对"丢失"的项用**放宽的阶数上限**再搜一次：
            # 若放宽后找到了，根因就是阶数上限，不是性质丢失。
            relaxed_lin = None
            relaxed_prec = None
            if base_lin and not after_lin and not degenerate_out:
                relaxed_lin = any(c.get("survived_extrapolation")
                                  for c in discover_linear(tv, max_order=MAX_ORDER + 3))
            if base_prec and not after_prec and not degenerate_out:
                relaxed_prec = any(c.get("survived_extrapolation")
                                   for c in discover_polynomial_recurrence(
                                       tv, max_order=P_ORDER_MAX + 2))
            m = min(len(s["terms"]), len(tv))
            rows.append({
                "seq": s["id"], "transform": tf,
                "before": {"cfinite": base_lin, "precursive": base_prec},
                "after": {"cfinite": after_lin, "precursive": after_prec},
                "degenerate_output": degenerate_out,
                "relaxed_order_recovered": {"cfinite": relaxed_lin,
                                            "precursive": relaxed_prec},
                "is_fixed_point": s["terms"][:m] == tv[:m],
                "cfinite_lost": (base_lin and not after_lin
                                 and not degenerate_out and not relaxed_lin),
                "precursive_lost": (base_prec and not after_prec
                                    and not degenerate_out and not relaxed_prec),
            })

    per_tf: Dict[str, Any] = {}
    for tf, (cn, _fn) in TRANSFORMS.items():
        rs = [r for r in rows if r["transform"] == tf]
        if not rs:
            continue
        lost_c = [r["seq"] for r in rs if r["cfinite_lost"]]
        lost_p = [r["seq"] for r in rs if r["precursive_lost"]]
        gained_c = [r["seq"] for r in rs
                    if not r["before"]["cfinite"] and r["after"]["cfinite"]]
        degen = [r["seq"] for r in rs if r["degenerate_output"]]
        recov = [r["seq"] for r in rs
                 if r["relaxed_order_recovered"]["cfinite"]
                 or r["relaxed_order_recovered"]["precursive"]]
        per_tf[tf] = {
            "cn": cn, "n_tested": len(rs),
            "n_fixed_points": sum(1 for r in rs if r["is_fixed_point"]),
            "fixed_points": [r["seq"] for r in rs if r["is_fixed_point"]],
            "cfinite_lost": lost_c, "precursive_lost": lost_p,
            "cfinite_gained": gained_c,
            "degenerate_output": degen,
            "recovered_by_relaxed_order": recov,
            "degenerate_note": ("变换后输出几乎全零（逆二项变换会把多项式型序列打零），"
                                "不计入「丢失」——那是输出没内容，不是性质丢了。"),
            "relaxed_note": ("放宽阶数上限后又能找到 ⇒ 根因是**阶数上限**，"
                             "不是性质丢失；这类同样不计入「丢失」。"),
            "is_closed_by_theory": tf in CLOSED_TRANSFORMS,
            "closure_verdict": (
                "理论封闭；本轮搜索在其上" +
                ("全部保持" if not (lost_c or lost_p)
                 else f"丢失 {len(lost_c)} 条 C-finite / {len(lost_p)} 条 P-recursive"
                      "——这是**搜索失败**的证据，不是性质丢失")
                if tf in CLOSED_TRANSFORMS else
                "该变换在理论上不对全类封闭，本层只记录观测，不作封闭性判据"),
        }

    return {
        "scope": ("变换只作用于**已生成的前 n_terms 项**；变换后序列同样是有限项，"
                  "所有「找到 / 没找到」都只在这有限项上有意义。"),
        "evidence": "L2",
        "n_transforms": len(TRANSFORMS),
        "n_rows": len(rows),
        "per_transform": per_tf,
        "rows": rows,
        "reading_note": (
            "「丢失」一栏要反着读：对理论封闭的变换，丢失 = 我的搜索没跟上，"
            "它是**搜索能力的探针**，不是数学结论。"),
    }


# ===========================================================================
# 6.8 元检验：证伪机制本身**会不会真的响**
# ===========================================================================
# 为什么需要这一节
# ----------------
# 真实序列库跑下来，"外推证伪"一直是 0。这很容易被读成"没有过拟合"，
# 但真相是：C1/C2 只有在发现集上**精确相容且解唯一**时才报候选，
# 不相容的（随机噪声、素数分拆数等）根本走不到外推检验那一步，
# 于是 FALSIFIED_BY_EXTRAPOLATION 这个状态**结构上不可达**。
#   实测：60 项随机噪声 → C1 报 0 条、C2 报 0 条。
#
# 所以 0 证伪的正确解读是"没有候选进入检验"，而不是"没有过拟合"。
# 要判断证伪机制是不是空转，只能**自己造一个必然破功的序列**丢进去：
# 前 k 项严格满足某递推、第 break_at 项起破功，看引擎能不能报出来、
# 并且把第一个失败点定位到 break_at。
#
# 这是"把方法用在自己身上"的元检验，不是序列理论的一部分。
SYNTH_RECURRENCES = [
    {"id": "syn_ord2", "order": 2, "coeffs": [1, 2], "const": 1, "init": [1, 1],
     "name": "a(n)=a(n-1)+2a(n-2)+1"},
    {"id": "syn_ord3", "order": 3, "coeffs": [1, 1, 1], "const": 0, "init": [0, 1, 1],
     "name": "a(n)=a(n-1)+a(n-2)+a(n-3)"},
]


def synthetic_broken_sequence(order: int = 2, break_at: int = 40,
                              n_terms: int = 60, mode: str = "once",
                              coeffs: Optional[List[int]] = None,
                              const: int = 1,
                              init: Optional[List[int]] = None) -> List[int]:
    """造一个**必然破功**的序列：前 break_at 项严格满足给定递推，之后破坏。

    mode="once"        只在 break_at 处扰动一次，之后仍按同递推（以新值为初值）继续；
    mode="persistent"  从 break_at 起每一项都在递推值上再加一项，持续不成立。
    """
    if coeffs is None:
        coeffs = [1, 2][:order] if order == 2 else [1] * order
    if init is None:
        init = [1] * order
    terms = list(init)
    for n in range(order, n_terms):
        terms.append(sum(coeffs[i] * terms[n - 1 - i] for i in range(order)) + const)
    if mode == "once":
        # 在 break_at 处改一个数，之后以新值为初值继续按同递推生成
        terms[break_at] += 1
        for n in range(break_at + 1, n_terms):
            terms[n] = sum(coeffs[i] * terms[n - 1 - i]
                           for i in range(order)) + const
    elif mode == "persistent":
        for n in range(break_at, n_terms):
            terms[n] += (n - break_at + 1)
    else:
        raise ValueError(f"未知 mode：{mode}")
    return terms


def meta_test_falsification(n_terms: int = 60,
                            discovery_len: int = DISCOVERY_LEN) -> Dict[str, Any]:
    """元检验：把必然破功的序列丢进引擎，看证伪通道响不响、定位准不准。"""
    cases: List[Dict[str, Any]] = []
    for spec in SYNTH_RECURRENCES:
        order = spec["order"]
        for mode in ("once", "persistent"):
            for break_at in (discovery_len + 10, n_terms - 5):
                terms = synthetic_broken_sequence(
                    order=order, break_at=break_at, n_terms=n_terms, mode=mode,
                    coeffs=spec["coeffs"], const=spec["const"], init=spec["init"])
                cands = discover_linear(terms, discovery_len=discovery_len)
                falsified = [c for c in cands
                             if not c.get("survived_extrapolation")]
                hit = None
                for c in falsified:
                    ff = c.get("first_failure") or {}
                    if ff.get("n") == break_at:
                        hit = c
                        break
                cases.append({
                    "case": f"{spec['id']}/{mode}/break@{break_at}",
                    "recurrence": spec["name"],
                    "break_at": break_at,
                    "mode": mode,
                    "n_candidates": len(cands),
                    "n_falsified": len(falsified),
                    "located_exactly": hit is not None,
                    "reported_first_failure": (
                        falsified[0].get("first_failure") if falsified else None),
                })
    n_ok = sum(1 for c in cases if c["located_exactly"])
    return {
        "why": ("C1/C2 只在发现集上精确相容且解唯一时才报候选，因此真实序列上"
                "「外推证伪」恒为 0——那是**没有候选进入检验**，不是没有过拟合。"
                "本节用必然破功的合成序列检验该通道本身是否可达。"),
        "n_cases": len(cases),
        "n_located_exactly": n_ok,
        "all_passed": n_ok == len(cases),
        "cases": cases,
        "verdict": ("证伪通道可达且定位准确" if n_ok == len(cases) else
                    f"证伪通道有问题：{len(cases) - n_ok}/{len(cases)} 个用例未能定位"),
        "evidence": "L2",
    }


# ===========================================================================
# 7. 单序列分析 + 总入口
# ===========================================================================
def _mark_redundant(lin: List[Dict[str, Any]], hyp: List[Dict[str, Any]],
                    prec: List[Dict[str, Any]]) -> None:
    """把 C4 报出的、实为 C1/C2 推论的形式标记出来，**不**当作新候选。

    不这么做的话候选数会虚高（实测 4 → 17），而其中 14 条只是把 C1 已经
    找到的常系数递推用 deg=0 的多项式重写了一遍。形式变了，信息量没变。
    """
    has_lin = any(c.get("survived_extrapolation") for c in lin)
    has_hyp = any(c.get("survived_extrapolation") for c in hyp)
    for c in prec:
        if c.get("skipped"):
            continue
        if c.get("subsumes_linear") and has_lin:
            c["redundant"] = "CONSEQUENCE_OF_C1"
            c["redundant_note"] = (
                "C4 在 deg=0 时退化成常系数齐次递推；该序列的常系数递推"
                "已由 C1 报出，此条是它的推论，不重复计数")
        elif c.get("order") == 1 and has_hyp:
            c["redundant"] = "CONSEQUENCE_OF_C2"
            c["redundant_note"] = (
                "一阶 P-recursive 与一阶有理（超几何）闭式是同一件事的两种写法："
                "a(n+1)/a(n)=P/Q ⟺ Q(n)·a(n+1) − P(n)·a(n) = 0；"
                "该序列的 C2 闭式已报出，此条不重复计数")


def _classify(cand: Dict[str, Any]) -> str:
    if not cand.get("survived_extrapolation"):
        return "FALSIFIED_BY_EXTRAPOLATION"
    if cand.get("degenerate"):
        return "DEGENERATE"
    # 已知形式优先于冗余判定：catalan / central_binomial / factorial 的 C4 形式
    # 既是教科书已知、又是 C2 的推论，若先判冗余就会丢掉 5 条里的 3 条召回。
    if cand.get("recognition"):
        return "KNOWN_RECURRENCE_REDISCOVERED"
    if cand.get("redundant"):
        return cand["redundant"]
    return "CANDIDATE_UNVERIFIED"


def analyze_sequence(seq: Dict[str, Any]) -> Dict[str, Any]:
    terms = seq["terms"]
    lin = discover_linear(terms)
    hyp = discover_hypergeometric(terms)
    prec = discover_polynomial_recurrence(terms)
    # 压力测试：用更小的发现集再跑一遍，暴露"小样本过拟合"
    stress_lin = discover_linear(terms, discovery_len=STRESS_LEN)
    stress_hyp = discover_hypergeometric(terms, discovery_len=STRESS_LEN)
    stress_prec = discover_polynomial_recurrence(terms, discovery_len=STRESS_LEN)
    for c in stress_lin:
        c["is_stress_test"] = True
    for c in stress_hyp:
        c["is_stress_test"] = True
    for c in stress_prec:
        c["is_stress_test"] = True

    _mark_redundant(lin, hyp, prec)
    allc = lin + hyp + prec
    for c in allc:
        c["status"] = _classify(c)

    growth = estimate_growth(terms)
    # C1 与 C3 的对账：递推的特征根 vs 尾部窗口拟合
    reconcile = reconcile_growth(growth, lin)
    accepted = [c for c in allc if c["status"] == "CANDIDATE_UNVERIFIED"]
    known = [c for c in allc if c["status"] == "KNOWN_RECURRENCE_REDISCOVERED"]
    falsified_main = [c for c in allc
                      if c["status"] == "FALSIFIED_BY_EXTRAPOLATION"]
    falsified_stress = [c for c in stress_lin + stress_hyp + stress_prec
                        if not c.get("survived_extrapolation")]
    # C1/C2 单独的候选数：EXPECTED_NEGATIVE 是**对 C1/C2** 定义的，
    # 拿它去判全通道候选会把 C4 的合法发现误当成假警报。
    accepted_c12 = [c for c in lin + hyp if c["status"] == "CANDIDATE_UNVERIFIED"]

    return {
        "id": seq["id"], "cn": seq["cn"], "note": seq["note"],
        "index_base": seq["index_base"],
        "n_terms": len(terms),
        "first_terms": terms[:12],
        "linear": lin, "hyper": hyp, "prec": prec,
        "stress": {"linear": stress_lin, "hyper": stress_hyp, "prec": stress_prec,
                   "n_falsified": len(falsified_stress),
                   "falsified_samples": [
                       {"statement": c["statement"], "first_failure": c["first_failure"]}
                       for c in falsified_stress[:5]]},
        "growth": growth,
        "growth_vs_recurrence": reconcile,
        "n_accepted": len(accepted),
        "n_accepted_c12": len(accepted_c12),
        "n_known_rediscovered": len(known),
        "n_falsified": len(falsified_main),
        "found_anything": bool(lin or hyp or prec),
    }


def analyze_all(n_terms: int = N_TERMS) -> Dict[str, Any]:
    seqs = build_sequences(n_terms)
    results = [analyze_sequence(s) for s in seqs]

    n_known = sum(r["n_known_rediscovered"] for r in results)
    n_cand = sum(r["n_accepted"] for r in results)
    n_false = sum(r["n_falsified"] for r in results)
    n_stress = sum(r["stress"]["n_falsified"] for r in results)

    # C1↔C3 对账：两条独立路径（递推特征根 / 尾部窗口拟合）是否指向同一结论
    rec_avail = [r for r in results if r["growth_vs_recurrence"]["available"]]
    rec_agree = [r["id"] for r in rec_avail
                 if r["growth_vs_recurrence"].get("agrees") is True]
    rec_disagree = [r["id"] for r in rec_avail
                    if r["growth_vs_recurrence"].get("agrees") is False]
    rec_resolved = [r["id"] for r in results
                    if r["growth_vs_recurrence"].get("resolves_subexp_warning")]
    # 同一条递推可能被两条通道各自认领一次（如 catalan 的 C2 闭式与 C4 闭式），
    # 所以「按候选计」与「按序列计」必须分开报，否则会重复计数。
    n_seq_with_known = sum(1 for r in results if r["n_known_rediscovered"] > 0)
    n_redundant = sum(1 for r in results for c in r["prec"] if c.get("redundant"))

    # 校准：期望阳性的序列是否被召回？期望阴性的序列是否确实没找到？
    expected_pos = {rec["seq"] for rec in KNOWN_RECURRENCES}
    # 只统计 C1/C2 通道的认领。初版用 n_known_rediscovered（含 C4），
    # 于是 derangements / motzkin 被算进 C1/C2 的召回，算出 **1.2** 这种
    # 大于 1 的召回率。召回率超过 1 本身就是口径错了的信号。
    recalled = {r["id"] for r in results
                if any(c.get("recognition") for c in r["linear"] + r["hyper"])}
    missed = sorted(expected_pos - recalled)
    # 未列入校准表但已知有递推的序列：机器若独立发现，进人工复核队列
    unlisted_found = {r["id"]: UNLISTED_POSITIVE[r["id"]]
                      for r in results if r["id"] in UNLISTED_POSITIVE
                      and (r["linear"] or r["hyper"])}
    unlisted_missed = sorted(set(UNLISTED_POSITIVE) - set(unlisted_found))
    # 注意用 n_accepted_c12：EXPECTED_NEGATIVE 是**对 C1/C2** 定义的
    false_alarm = sorted(r["id"] for r in results
                         if r["id"] in EXPECTED_NEGATIVE and r["n_accepted_c12"] > 0)
    true_negative = sorted(r["id"] for r in results
                           if r["id"] in EXPECTED_NEGATIVE and r["n_accepted_c12"] == 0)

    # C4 校准：期望阳性 = 教科书里的 P-recursive 递推；期望阴性 = 非 D-finite
    prec_expected = {rec["seq"] for rec in KNOWN_PRECURENCES}
    prec_recalled = {r["id"] for r in results
                     if any(c.get("recognition") for c in r["prec"])}
    prec_missed = sorted(prec_expected - prec_recalled)
    prec_cand = {r["id"] for r in results
                 if any(c["status"] == "CANDIDATE_UNVERIFIED" for c in r["prec"])}
    prec_false_alarm = sorted(prec_cand & P_RECURSIVE_NEGATIVE)
    prec_true_negative = sorted(P_RECURSIVE_NEGATIVE - prec_cand - prec_recalled)

    return {
        "scope": SCOPE_NOTE,
        "evidence": EVIDENCE_NOTE,
        "generated_at_note": "由 sequences.analyze_all 生成",
        "parameters": {"n_terms": n_terms, "discovery_len": DISCOVERY_LEN,
                       "stress_len": STRESS_LEN, "max_order": MAX_ORDER,
                       "coef_bound": COEF_BOUND},
        "sequences": results,
        "calibration": {
            "expected_positive": sorted(expected_pos),
            "recalled": sorted(recalled),
            "missed": missed,
            "recall_rate": round(len(recalled) / len(expected_pos), 4) if expected_pos else 0.0,
            "expected_negative": sorted(EXPECTED_NEGATIVE),
            "true_negative": true_negative,
            "false_alarm": false_alarm,
            "unlisted_positive": sorted(UNLISTED_POSITIVE),
            "unlisted_found": unlisted_found,
            "unlisted_missed": unlisted_missed,
            "unlisted_note": (
                "这些序列已知满足常系数递推，但**故意不写进校准表**，"
                "用来检验机器能否独立发现；发现结果进人工复核队列。"),
            "false_alarm_note": (
                "在期望阴性的序列上若报出 CANDIDATE_UNVERIFIED，通常是**小样本巧合**，"
                "本表把它们单列出来，因为那意味着搜索空间仍需收窄。"),
            "scope_warning": (
                "「期望阴性」必须写明是对**哪个通道**阴性。derangements / motzkin "
                "对 C1/C2 阴性，但对 C4 阳性——初版笼统地把它们归入阴性集，"
                "加上 C4 后即自相矛盾。现已按通道分开登记。"),
            "c4": {
                "expected_positive": sorted(prec_expected),
                "recalled": sorted(prec_recalled),
                "missed": prec_missed,
                "recall_rate": (round(len(prec_recalled) / len(prec_expected), 4)
                                if prec_expected else 0.0),
                "expected_negative": sorted(P_RECURSIVE_NEGATIVE),
                "true_negative": prec_true_negative,
                "false_alarm": prec_false_alarm,
                "note": (
                    "C4 的期望阴性不是「我猜它找不到」，而是**有理由认为它不存在**："
                    "序列 P-recursive ⟺ 其普通生成函数 D-finite；贝尔数的指数生成函数 "
                    "e^(e^x−1) 与划分数的生成函数 1/(q;q)_∞ 都不是 D-finite。"
                    "所以 C4 在它们身上报不出东西是**正确结果**。"),
            },
        },
        "summary": {
            "n_sequences": len(results),
            "n_known_rediscovered": n_known,
            "n_sequences_with_known": n_seq_with_known,
            "n_candidates": n_cand,
            "n_redundant_marked": n_redundant,
            "n_falsified_main": n_false,
            "n_falsified_stress": n_stress,
            "counting_note": (
                "n_known_rediscovered 按**候选**计，同一条递推被两条通道各自认领时"
                "会重复；n_sequences_with_known 按**序列**计，看总量用后者。"),
        },
        "growth_reconciliation": {
            "n_reconcilable": len(rec_avail),
            "n_agree": len(rec_agree),
            "n_disagree": len(rec_disagree),
            "disagreeing": rec_disagree,
            "n_subexp_warning_resolved": len(rec_resolved),
            "resolved": rec_resolved,
            "note": ("同一序列的增长率用两条**互相独立**的路径各算一次："
                     "C3 在尾部窗口上做对数拟合（数值、有窗口偏差），"
                     "C1 由递推的特征多项式求根（结构决定、但求根仍是数值）。"
                     "一致不代表正确，不一致则说明至少一方有问题。"),
        },
    }


__all__ = [
    "SCOPE_NOTE", "EVIDENCE_NOTE", "N_TERMS", "DISCOVERY_LEN", "STRESS_LEN",
    "build_sequences", "discover_linear", "discover_hypergeometric",
    "estimate_growth", "analyze_sequence", "analyze_all",
    "characteristic_polynomial", "polynomial_roots", "growth_from_recurrence",
    "reconcile_growth", "discover_polynomial_recurrence", "meta_test_falsification",
    "transform_closure", "TRANSFORMS", "CLOSED_TRANSFORMS",
    "KNOWN_RECURRENCES", "EXPECTED_NEGATIVE", "KNOWN_PRECURENCES",
    "P_RECURSIVE_NEGATIVE",
]
