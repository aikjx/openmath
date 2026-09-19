# -*- coding: utf-8 -*-
"""
数值求根（纯标准库）——对符号求解器无法处理的方程提供**数值 fallback**。

能力边界（诚实标注）：
  - 仅处理**单变量**方程；多变量不做。
  - 方法：区间扫描 + 二分。存在漏根风险：若在给定区间内同号且不相切，或根超出 [lo,hi]，则找不到。
  - 结果为**数值证据(L2)**，不是解析解、更不是证明。
  - 不支持不等式 <=/>=/</> 的求解，仅支持等号方程。
"""
from __future__ import annotations

import math
from .parser import parse_text, evaluate

DEFAULT_LO = -20.0
DEFAULT_HI = 20.0
DEFAULT_STEPS = 1600


def split_equation(raw: str):
    """在**顶层**（括号外）切分等式，返回 (lhs, rhs)；非等号方程返回 None。"""
    depth = 0
    for i, ch in enumerate(raw):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "=" and depth == 0:
            return raw[:i].strip(), raw[i + 1:].strip()
    return None


# 含这些词的"方程"实为逻辑/蕴含命题，不是代数恒等式，数值抽样对其无意义
LOGICAL_WORDS = ("implies", " and ", " or ", " iff ", "not ")


def verify_identity(raw: str, trials: int = 25, lo: float = 0.05, hi: float = 0.95,
                    seed: int = 20260919, tol: float = 1e-6) -> dict:
    """
    对**代数恒等式** lhs=rhs 做随机抽样数值验证（而非求根）。

    默认抽样区间为 [0.05,0.95]（单位区间），原因：反三角/对数等多值函数在 |z|>1 时
    会因**主分支约定不同**而出现虚假不符（见 pooled 实测：arctan/arcsin 恒等式在 z=2 时
    虚部符号相反），在单位区间内主分支一致，判定更可靠。调用方可放宽再试。
    """
    import random
    lower = raw.lower()
    if any(w in lower for w in LOGICAL_WORDS):
        return {"status": "skip", "reason": "含逻辑连接词/蕴含，非纯代数恒等式", "trials_checked": 0}
    parts = split_equation(raw)
    if parts is None:
        return {"status": "skip", "reason": "非等号关系", "trials_checked": 0}
    lhs_s, rhs_s = parts
    left = parse_text(lhs_s)
    right = parse_text(rhs_s)
    if not (left.parse_ok and right.parse_ok):
        return {"status": "skip", "reason": "两侧之一无法解析", "trials_checked": 0}

    vars_ = sorted(set(left.variables) | set(right.variables))
    rng = random.Random(seed)
    checked, maxdiff, worst = 0, 0.0, None
    for _ in range(trials):
        env = {}
        for vv in vars_:
            # CD 公式里的 i 通常是虚数单位，赋 1j 才是作者的意图
            env[vv] = 1j if vv == "i" else rng.uniform(lo, hi)
        try:
            lv = evaluate(left.ast, env)
            rv = evaluate(right.ast, env)
        except Exception:  # noqa: BLE001
            continue
        try:
            if isinstance(lv, complex) or isinstance(rv, complex):
                diff = abs(complex(lv) - complex(rv))
                scale = max(1.0, abs(complex(lv)))
            else:
                diff = abs(float(lv) - float(rv))
                scale = max(1.0, abs(float(lv)))
        except Exception:  # noqa: BLE001
            continue
        checked += 1
        rel = diff / scale
        if rel > maxdiff:
            maxdiff = rel
            worst = {k: repr(v) for k, v in env.items()}  # repr 避免 complex 不可序列化

    if checked == 0:
        return {"status": "unevaluable", "trials_checked": 0,
                "reason": "抽样点均无法求值（超出定义域或函数不被求值器支持）", "variables": vars_}
    return {
        "status": "holds" if maxdiff <= tol else "fails",
        "trials_checked": checked,
        "max_relative_diff": maxdiff,
        "worst_case_env": worst,
        "variables": vars_,
        "caveat": (f"仅在 [{lo},{hi}] 正实数域随机抽样(L2)；未覆盖负数与特殊点。"
                   f"'fails' 也可能是求值器局限所致，**不等于找到反例**；"
                   f"'holds' 也只是有限抽样证据，**绝非证明**。"),
    }


def _as_float(v):
    """把求值结果转成 float；复数或无法转换则返回 None。"""
    if isinstance(v, complex):
        if abs(v.imag) < 1e-12:
            return v.real
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if isinstance(f, float) and (math.isnan(f) or math.isinf(f)):
        return None
    return f


def find_roots_numeric(raw: str, lo: float = DEFAULT_LO, hi: float = DEFAULT_HI,
                       steps: int = DEFAULT_STEPS, var: str | None = None) -> dict:
    """对单变量方程 lhs=rhs 数值求根。返回状态与根列表。"""
    parts = split_equation(raw)
    if parts is None:
        return {"status": "skip", "reason": "非等号方程（可能为不等式）", "roots": []}
    lhs_s, rhs_s = parts

    whole = parse_text(raw)
    if not whole.parse_ok:
        return {"status": "skip", "reason": "整体无法解析", "roots": []}
    variables = whole.variables
    if len(variables) != 1:
        return {"status": "skip", "reason": f"变量数 {len(variables)}，本数值器仅处理单变量", "roots": []}
    v = var or variables[0]

    left = parse_text(lhs_s)
    right = parse_text(rhs_s)
    if not (left.parse_ok and right.parse_ok):
        return {"status": "skip", "reason": "两侧之一无法解析", "roots": []}

    def f(x):
        try:
            a = evaluate(left.ast, {v: x})
            b = evaluate(right.ast, {v: x})
        except Exception:  # noqa: BLE001
            return None
        fa, fb = _as_float(a), _as_float(b)
        if fa is None or fb is None:
            return None
        return fa - fb

    # 扫描网格
    xs, vals, bad = [], [], 0
    n = steps
    for i in range(n + 1):
        x = lo + (hi - lo) * i / n
        y = f(x)
        xs.append(x)
        vals.append(y)
        if y is None:
            bad += 1
    valid = [i for i, y in enumerate(vals) if y is not None]
    if len(valid) < 2:
        return {"status": "skip", "reason": "函数在区间内几乎处处不可求值（可能超出定义域）", "roots": []}

    roots = []
    # eps：早停阈值。收紧到 1e-11 以提高根的精度（1e-7 会让 π 之类根的误差达 1e-7 量级）。
    eps = 1e-11

    # 恰好落在网格点上的零点
    for i in valid:
        if abs(vals[i]) < eps:
            roots.append(round(xs[i], 10))

    # 相邻有效点之间的变号 -> 二分
    for k in range(len(valid) - 1):
        i, j = valid[k], valid[k + 1]
        if vals[i] is None or vals[j] is None:
            continue
        # 跳过该 x 区间中不可求值的部分过大
        if j - i > 1 and bad > 0:
            pass
        if vals[i] * vals[j] < 0:
            a, fa = xs[i], vals[i]
            b, fb = xs[j], vals[j]
            for _ in range(80):
                m = (a + b) / 2.0
                fm = f(m)
                if fm is None:
                    break
                if abs(fm) < eps or (b - a) < 1e-12:
                    a = m
                    break
                if fa * fm <= 0:
                    b, fb = m, fm
                else:
                    a, fa = m, fm
            roots.append(round((a + b) / 2.0, 10))

    # 去重
    uniq = []
    for r in sorted(roots):
        if not uniq or abs(r - uniq[-1]) > 1e-6:
            uniq.append(r)
    return {
        "status": "ok",
        "roots": uniq,
        "variable": v,
        "range": [lo, hi],
        "method": "区间扫描+二分",
        "caveat": "数值解(L2)，可能因步长/区间导致漏根；非解析解、非证明。",
    }
