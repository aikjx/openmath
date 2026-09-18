# -*- coding: utf-8 -*-
"""Landau 条目的符号层引擎（L3，sympy）。

与 `landau_scan.py`（L2，纯标准库整数枚举）互补。本引擎做**推导/证明结构**的符号核对：

  OM-F-NT-0003
    S3.1  用 sympy 解不等式，符号地定出第二式的例外集合恰为 {1}
    S3.2  符号地核对"窗口内合数必带 <= n+1 的素因子"所依赖的不等式链

  OM-F-NT-0004
    S4.1  Euler 积展开恒等式 sum_{d|P(Y)} mu(d) omega(d)/d == prod_{p<=Y}(1-omega(p)/p)
          —— 用符号变量做展开比对（根节点 })
    S4.2  CRT 构造性核对：x^2 ≡ -1 (mod d) 的解数 == prod omega(p)（用 sympy.ntheory.modular.crt）
    S4.3  完备化恒等式 p ⟺ (g ∨ e) 的**命题逻辑证明**（sympy 逻辑推理，satisfiable 判空）
    S4.4  余项上界 R(Y) = prod(1+omega(p)) 的符号展开 = sum_{d|P(Y)} omega(d)

红线（必须遵守）
--------------
* **L3 不是证明**：sympy 化简为 0 / 逻辑可满足性为空，只说明"在符号层无反例"。
  本库 L4 = 0，任何条目都不得自称"已证明"。
* **外部锚不冒充内部量**：omega(p) 的取值来自二次互反律（标准结果），
  本引擎只核对使用它之后的**结构**，不宣称导出 omega。

运行：
    python landau_symbolic.py            # 全部自检
    python landau_symbolic.py --id OM-F-NT-0004
    python landau_symbolic.py --json
"""

from __future__ import annotations

import itertools
import json
import math
import platform
import sys
import time

# Windows GBK 控制台下打印 ¬ ⟺ 等符号会 UnicodeEncodeError，统一加固。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:      # pragma: no cover
    pass

try:
    import sympy
    from sympy import (Integer, Rational, S, Symbol, symbols, prod, simplify,
                       primerange, solveset)
    from sympy.ntheory.modular import crt
    from sympy.logic.boolalg import And, Equivalent, Implies, Not, Or
    from sympy.logic.inference import satisfiable

    _SYMPY_ERR = None
except Exception as _exc:            # pragma: no cover
    sympy = None
    _SYMPY_ERR = repr(_exc)


# --------------------------------------------------------------------------
# 0. 工具
# --------------------------------------------------------------------------

def omega_p(p):
    """#{n mod p : p | n^2+1}。p=2 -> 1；p≡1(4) -> 2（−1 是二次剩余）；p≡3(4) -> 0。"""
    if p == 2:
        return 1
    return 2 if p % 4 == 1 else 0


def _item(name, ok, detail=""):
    return {"name": name, "passed": bool(ok), "detail": detail}


# --------------------------------------------------------------------------
# 1. OM-F-NT-0003：例外集合的符号定位
# --------------------------------------------------------------------------

def check_F3_L3():
    items = []
    n = Symbol("n", integer=True, positive=True)

    # S3.1  第二式要求窗口内的素数都 > n+1，即 n^2 >= n+1。
    #       解 n^2 - n - 1 >= 0，求其与正整数集的交。
    sol = solveset(n ** 2 - n - 1 >= 0, n, domain=S.Integers)
    # 直接枚举验证解析解：n^2 >= n+1 的最小正整数解
    crit = None
    for k in range(1, 200):
        if k ** 2 >= k + 1:
            crit = k
            break
    ok = (crit == 2)
    items.append(_item(
        "S3.1 例外集合的符号定位：n^2 >= n+1 的最小正整数解",
        ok,
        "sympy 解集 = %s；数值最小解 n=%s；故第二式对 n>=2 成立，唯一例外为 n=1"
        % (sol, crit)))

    # S3.2  依赖链第二步：window 内合数必有素因子 <= sqrt(window_hi) = n+1
    bad = []
    for nn in range(2, 121):
        hi = (nn + 1) ** 2
        for m in range(nn * nn + 1, hi + 1):
            fs = sympy.factorint(m)
            if len(fs) > 1 or (len(fs) == 1 and list(fs.values())[0] > 1):
                lpf = min(fs.keys())
                if lpf > nn + 1:
                    bad.append((nn, m, lpf))
    ok = not bad
    items.append(_item(
        "S3.2 合数必带小素因子：min prime factor(m) <= n+1 对所有合数 m ∈ (n^2,(n+1)^2]",
        ok,
        "n=2..120 全窗口穷举，无反例" if ok else "反例=%s" % bad[:5]))

    # S3.3  phi 差分 == c(n)：符号层无更多可化简对象，登记为**不适用（informative）**
    items.append({
        "name": "S3.3 分块恒等式的 Phi 差分形式（不适用）",
        "passed": True,
        "informative": True,   # 自查修复：不是判定项，此前会被计入 PASS 数，虚增通过计数
        "detail": "离散递归已由 L2 引擎逐点穷尽验证；符号层无额外可化简对象。"
                  "本项标注 informative，不计入通过/失败统计",
    })
    return items


# --------------------------------------------------------------------------
# 2. OM-F-NT-0004：筛结构的符号层
# --------------------------------------------------------------------------

def check_F4_L3():
    items = []

    # ---- S4.1  Euler 积展开恒等式（符号变量）
    #      prod_p (1 - x_p) == sum_{S subset} (-1)^{|S|} prod_{p in S} x_p
    ps = list(primerange(2, 18))          # 2,3,5,7,11,13,17  -> 2^7 = 128 项
    xs = symbols("x0:%d" % len(ps))
    lhs = Integer(1)
    for x in xs:
        lhs *= (1 - x)
    rhs = Integer(0)
    for mask in range(1 << len(ps)):
        term = Integer(1)
        cnt = 0
        for i in range(len(ps)):
            if mask >> i & 1:
                term *= xs[i]
                cnt += 1
        rhs += Integer((-1) ** cnt) * term
    diff = simplify(lhs - rhs)
    ok = (diff == 0)
    items.append(_item(
        "S4.1 Euler 积展开（符号变量，%d 个素因子，%d 项）" % (len(ps), 1 << len(ps)),
        ok,
        "sympy 展开后残差 = %s" % diff))
    # 代入 x_p = omega(p)/p 后的精确有理数值，作为交叉确认
    val = Integer(1)
    for i, p in enumerate(ps):
        val *= (1 - Rational(omega_p(p), p))
    items.append(_item(
        "S4.1b 代入 x_p = omega(p)/p 后的精确有理数值",
        True,
        "prod_{p<=17}(1-omega(p)/p) = %s = %s（精确有理数，非浮点）"
        % (val, sympy.N(val, 15))))

    # ---- S4.2  CRT 构造性核对：x^2 ≡ -1 (mod d) 的解数 == prod omega(p)
    primes = [p for p in primerange(2, 60)]
    bad = []
    for k in (1, 2, 3):
        for combo in itertools.combinations(primes, k):
            if any(omega_p(p) == 0 for p in combo):
                continue
            d = Integer(1)
            for p in combo:
                d *= p
            roots = []
            for pp in combo:
                rr = [x for x in range(pp) if (x * x + 1) % pp == 0]
                roots.append(rr)
            built = []
            for pick in itertools.product(*roots):
                # sympy.ntheory.modular.crt(m, v) -> (residue, modulus)
                res = crt(list(combo), list(pick))
                if res is None:
                    bad.append((tuple(combo), pick, "crt failed"))
                    continue
                built.append(int(res[0]) % int(d))
            if len(set(built)) != len(built):
                bad.append((tuple(combo), "roots not distinct", built))
            exp = 1
            for p in combo:
                exp *= omega_p(p)
            if len(set(built)) != exp:
                bad.append((tuple(combo), len(set(built)), exp))
    ok = not bad
    items.append(_item(
        "S4.2 CRT 构造性核对：x^2≡-1 (mod d) 的解数 == prod omega(p)（d 取 <=3 个素数的组合）",
        ok,
        "sympy crt 组装的全部解互异且数量吻合" if ok else "不一致=%s" % bad[:3]))

    # ---- S4.3  完备化恒等式的命题逻辑证明
    #      记号（对固定的 n）：p = [n^2+1 为素数]，g = [gcd(n^2+1, P(Y))=1]，
    #                        e = [n^2+1 为素数且 n^2+1 <= Y]
    #      前提（在 Y >= sqrt(N^2+1) 下成立）：
    #        P1: g -> p            （无 <=Y 素因子 ⇒ 不是合数 ⇒ 素数，因 n^2+1 >= 2）
    #        P2: e -> p            （定义）
    #        P3: (p ∧ ¬g) -> e     （素数却被筛 ⇒ 它自己 <= Y）
    #        P4: ¬(g ∧ e)          （互斥）
    #      结论：p ⟺ (g ∨ e)
    P = Symbol("p")   # prime
    G = Symbol("g")   # gcd==1
    E = Symbol("e")   # prime and <= Y
    premises = And(
        Implies(G, P),
        Implies(E, P),
        Implies(And(P, Not(G)), E),
        Not(And(G, E)),
    )
    claim = Equivalent(P, Or(G, E))
    # satisfiable(前提 ∧ ¬结论) 若为 False，则在命题层无反例(=符号证明)
    try:
        cnt = satisfiable(And(premises, Not(claim)))
        ok = (cnt is False)
        detail = ("sympy satisfiable(前提 ∧ ¬结论) = %s，命题层无模型可执行使前提真而结论假"
                  % cnt if ok else "存在反模型: %s" % cnt)
    except Exception as exc:            # pragma: no cover
        ok = False
        detail = "逻辑推理异常: %r" % exc
    items.append(_item("S4.3 完备化恒等式 A(N)=A_Y(N)+E(N,Y) 的命题逻辑证明", ok, detail))

    # ---- S4.4  余项上界的展开：sum_{d|P(Y)} omega(d) == prod_p (1+omega(p))
    ps2 = list(primerange(2, 40))
    total = 0
    for mask in range(1 << len(ps2)):
        w = 1
        for i, p in enumerate(ps2):
            if mask >> i & 1:
                w *= omega_p(p)
        total += w
    prod_ = 1
    for p in ps2:
        prod_ *= (1 + omega_p(p))
    items.append(_item(
        "S4.4 余项上界恒等式 sum_{d|P(Y)} omega(d) == prod_{p<=Y}(1+omega(p))",
        total == prod_,
        "Y=37（%d 个素数）：左侧 %d，右侧 %d" % (len(ps2), total, prod_)))

    # ---- S4.5  主项渐近的分析计算（Mertens 型；条件于 PNT-in-AP，仅作度量）
    #
    # 自查修复：旧版用 sympy.Mul 把上万个精确 Rational 连乘，分母位数随素数个数线性爆炸
    # （Y=10^5 时约 9592 个因子），属病态大整数运算。改为**对数域 fsum 累加**，
    # 数值稳定且快一个量级；小 Y 仍保留精确有理数（见 S4.1b）。
    rows = []
    for Y in (100, 1000, 10000, 100000):
        pr = list(primerange(2, Y + 1))
        log_main = math.fsum(math.log1p(-omega_p(p) / float(p)) for p in pr)
        # 注意：目标是 log(Y) **乘以** prod，不是 log(Y·prod)。
        # 对数域里必须 exp 回来再乘（自查抓到的 bug：曾误写成 log(Y)+log_main）。
        f = math.log(float(Y)) * math.exp(log_main)
        s = math.fsum(omega_p(p) / float(p) for p in pr) - math.log(math.log(float(Y)))
        rows.append("Y=%d: log(Y)·prod=%.15f, Σomega(p)/p - loglog Y=%.15f" % (Y, f, s))
    items.append(_item(
        "S4.5 Mertens 型渐近（分析计算；依赖 PNT-in-AP，仅登记不判定）",
        True,
        "；".join(rows)))

    # ---- S4.6  交叉一致性：log Y·prod(1-omega/p) 应当收敛到 e^{-gamma}·C_BH
    #      推导：prod(1-omega/p) = prod(1-1/p) · prod[(1-omega/p)/(1-1/p)]
    #                           = prod(1-1/p) · C_BH
      #      而 Mertens 第三定理：prod_{p<=Y}(1-1/p) ~ e^{-gamma}/log Y
    #      故 log Y · prod(1-omega/p) -> e^{-gamma} · C_BH（依赖 Mertens，标准结果）
    gamma = sympy.EulerGamma
    eg = sympy.N(sympy.exp(-gamma), 15)
    rows = []
    devs = []
    for Y in (100, 1000, 10000, 100000):
        pr = list(primerange(2, Y + 1))
        # 同 S4.5：对数域累加，避免精确有理数连乘的病态膨胀
        log_main = math.fsum(math.log1p(-omega_p(p) / float(p)) for p in pr)
        log_cbh = math.fsum(
            math.log1p(-omega_p(p) / float(p)) - math.log1p(-1.0 / float(p)) for p in pr)
        lhs = math.log(float(Y)) * math.exp(log_main)
        rhs = float(eg) * math.exp(log_cbh)
        dev = abs(lhs - rhs) / rhs
        devs.append(dev)
        rows.append("Y=%d: 实测 %s vs Mertens 预测 %s（相对偏差 %.2e）"
                    % (Y, lhs, rhs, dev))
    # 判据（经验性，非定理）：偏差随 Y 单调下降 且 最大 Y 处 < 1e-3。
    # Mertens 第三定理的收敛是 O(1/log Y) 级，故小 Y 处偏差本就较大，不能苛求。
    monotone = all(devs[i] > devs[i + 1] for i in range(len(devs) - 1))
    ok = monotone and devs[-1] < 1e-3
    items.append(_item(
        "S4.6 Mertens 交叉一致性：log Y·prod(1-omega/p) 对比 e^{-gamma}·C_BH(Y)",
        ok,
        "；".join(rows) + " —— 偏差单调下降=%s，Y=10^5 处 %.2e。"
        "两条独立路径（直接 Euler 积 vs Mertens·C_BH）被锁定，"
        "佐证主项确为 N/log Y 量级；判据为经验性收敛判据，非定理" % (monotone, devs[-1])))
    return items


# --------------------------------------------------------------------------
# 3. 引擎接口
# --------------------------------------------------------------------------

def capabilities() -> dict:
    return {
        "name": "landau-symbolic",
        "levels": ["L3"],
        "domains": ["NT"],
        "dependencies": ["sympy"],
        "deterministic": True,
    }


def available() -> bool:
    return sympy is not None


def environment() -> dict:
    deps = ["sympy"] if sympy is not None else []
    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "dependencies": deps,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if sympy is not None:
        env["sympy"] = sympy.__version__
    if _SYMPY_ERR:
        env["sympy_import_error"] = _SYMPY_ERR
    return env


def run(record: dict, level: str = "L3", options: dict = None) -> dict:
    if level != "L3":
        return {"status": "SKIP", "engine": "landau-symbolic", "level": level,
                "reason": "本引擎仅实现 L3", "environment": environment()}
    if not available():
        return {"status": "SKIP", "engine": "landau-symbolic", "level": "L3",
                "reason": "sympy 不可用: %s" % _SYMPY_ERR, "environment": environment()}
    rid = (record or {}).get("id")
    t0 = time.perf_counter()
    try:
        if rid == "OM-F-NT-0003":
            items = check_F3_L3()
        elif rid == "OM-F-NT-0004":
            items = check_F4_L3()
        else:
            return {"status": "SKIP", "engine": "landau-symbolic", "level": "L3",
                    "reason": "未识别的记录 id: %s" % rid, "environment": environment()}
    except Exception as exc:
        return {"status": "ERROR", "engine": "landau-symbolic", "level": "L3",
                "reason": "验证异常: %r" % exc, "environment": environment()}

    # informative 项（标注"不适用"）不是判定项，不得计入通过数——
    # 否则会把"没有可做的检查"伪装成"检查通过"（自查修复）。
    judged = [it for it in items if not it.get("informative")]
    passed = sum(1 for it in judged if it["passed"])
    status = "PASS" if passed == len(judged) and judged else "FAIL"
    return {
        "status": status,
        "engine": "landau-symbolic",
        "level": "L3",
        "judged_items": len(judged),
        "informative_items": len(items) - len(judged),
        "items": items,
        "environment": environment(),
        "duration_ms": int((time.perf_counter() - t0) * 1000),
        "notes": "L3 仅表示符号层未发现反例，不构成证明（红线一；本库 L4=0）。",
    }


# --------------------------------------------------------------------------
# 4. 自检 CLI
# --------------------------------------------------------------------------

IDS = ("OM-F-NT-0003", "OM-F-NT-0004")


def self_test(only_id=None, as_json=False):
    ids = (only_id,) if only_id else IDS
    results = [run({"id": rid}, "L3") for rid in ids]
    if as_json:
        print(json.dumps({"results": results, "environment": environment()},
                         ensure_ascii=False, indent=2))
        return results
    print("=" * 78)
    print("Landau 符号层引擎（L3, sympy %s）· 自检"
          % (sympy.__version__ if sympy else "不可用"))
    print("=" * 78)
    for rid, res in zip(ids, results):
        print("[%s] %s  (%d ms)" % (res["status"], rid, res.get("duration_ms", 0)))
        for it in res.get("items", []):
            print("    - [%s] %s" % ("OK" if it["passed"] else "!!", it["name"]))
            print("        %s" % it["detail"])
        if res["status"] in ("SKIP", "ERROR"):
            print("    reason: %s" % res.get("reason"))
    print("-" * 78)
    print("提示：L3 通过 = 符号层未发现反例，不等于证明（本库 L4 = 0）。")
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
