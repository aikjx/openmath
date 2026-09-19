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
import re
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

# ---------------------------------------------------------------------------
# 恒等式验证器的**准入筛查**
#
# 教训（2026-09-19 审计）：把 CD 里的英文数学散文直接送进随机抽样会产生大量**假阴性**——
# 例如 `e = the sum as j ranges from 0 to infinity of 1/(j!)` 会把冠词 `the` 当成变量，
# `sin A cos B` 会把 `sin` 当成变量并被错误嵌套。这类"验证失败"与数学真伪无关，
# 只是解析器的局限。因此抽样之前必须先判定：这条式子**是否属于本验证器的能力范围**。
# ---------------------------------------------------------------------------

# 出现这些结构 → 不是初等代数恒等式（级数/积分/微分/集合/量词），抽样无意义
NON_ELEMENTARY_MARKERS = (
    "infinity", "ranges from", "sum as", "over the range", "w.r.t",
    "\\partial", "partial(", "int(", "{", "|",
    "grad", "curl", "laplacian", "div(",
)

# 出现在"变量表"里 → 说明英文散文词被误当成标识符
PROSE_STOPWORDS = frozenset(
    "the a an as at by for from in is of on or over range ranges sum to wrt with "
    "respect implies if then and not class set such that where given let mean "
    "bigfloat bigfloatprec infinity int div grad curl laplacian".split()
)

# 出现在"变量表"里 → 说明函数名未被求值器识别，被降级成了变量
KNOWN_FUNC_NAMES = frozenset(
    "sin cos tan sec csc cot sinh cosh tanh sech csch coth arcsin arccos arctan "
    "arcsec arccsc arccot arcsinh arccosh arctanh arcsech arccsch arccoth "
    "exp ln log sqrt abs gcd lcm max min floor ceil det".split()
)

# 允许出现的非常量多字符标识符（目前为空：求值器不支持隐式乘法，
# 长度≥2 的"变量"几乎必然是 `iz`/`ix` 这类未拆开的隐式乘积）
ALLOWED_MULTICHAR_VARS = frozenset()

# 求值器内置的常量名（此处的 e 与 pi 指自然常数与圆周率，i 指虚数单位）
CONSTANT_NAMES = frozenset({"e", "pi", "i"})


def screen_identity(raw: str) -> dict:
    """
    判定一条式子**是否适合**用随机抽样验证，返回筛查结论。

    这一步只做"能不能验"，不碰"对不对"。筛查不通过的式子一律不给出 holds/fails，
    因为此时的结论反映的是**求值器的局限**，而不是式子的数学性质。
    """
    lower = raw.lower()
    if any(w in lower for w in LOGICAL_WORDS):
        return {"decidable": False, "scope": "logic",
                "reason": "含逻辑连接词/蕴含，非纯代数恒等式", "suspect_variables": []}
    if any(m in lower for m in NON_ELEMENTARY_MARKERS):
        return {"decidable": False, "scope": "non_elementary",
                "reason": "含级数/积分/微分/集合/量词记号，超出抽样验证能力",
                "suspect_variables": []}
    parts = split_equation(raw)
    if parts is None:
        return {"decidable": False, "scope": "not_equation",
                "reason": "非等号关系", "suspect_variables": []}
    lhs_s, rhs_s = parts
    left, right = parse_text(lhs_s), parse_text(rhs_s)
    if not (left.parse_ok and right.parse_ok):
        return {"decidable": False, "scope": "unparsable",
                "reason": "两侧之一无法解析", "suspect_variables": []}

    vars_ = sorted(set(left.variables) | set(right.variables))

    # 先区分"待解方程"与"恒等式"：形如 f(x)=0 的是求解对象，不是恒真命题
    rhs_probe = parse_text(rhs_s)
    if rhs_probe.parse_ok and not rhs_probe.variables and vars_:
        try:
            rv = evaluate(rhs_probe.ast, {v: 1.0 for v in vars_})
            if abs(float(rv)) < 1e-12:
                return {"decidable": False, "scope": "equation",
                        "reason": "右侧为常数 0：这是待解方程，不是恒等式",
                        "suspect_variables": []}
        except Exception:  # noqa: BLE001
            pass

    suspect = []
    for v in vars_:
        vl = v.lower()
        if vl in PROSE_STOPWORDS:
            suspect.append((v, "英文散文词被当作变量"))
        elif vl in KNOWN_FUNC_NAMES:
            suspect.append((v, "函数名未被识别，降级为变量"))
        elif len(v) >= 2 and v not in ALLOWED_MULTICHAR_VARS:
            suspect.append((v, "多字符标识符（求值器不支持隐式乘法，疑为未拆开的乘积）"))

    # 反向检查：**原文里出现的字母 token 是否都被解析到了**。
    # 解析器遇到不认识的标识符会静默丢弃（如 `+iz` 中的 `iz`），
    # 此时式子结构已经变了，再抽样就是在验证一条**别的东西**。
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", raw))
    known = (PROSE_STOPWORDS | KNOWN_FUNC_NAMES | CONSTANT_NAMES |
             {v.lower() for v in vars_})
    unknown = sorted(t for t in tokens if t.lower() not in known and t not in vars_)
    # LaTeX 命令（\sqrt 等）不算未识别 token
    unknown = [t for t in unknown if not raw.lower().count("\\" + t.lower())]
    for t in unknown:
        suspect.append((t, "原文中的标识符未被解析到（可能被求值器静默丢弃）"))

    # 隐式乘法：求值器不支持。实测 `2z` 被当成常量 2（z 被丢弃）、`iz` 被合成一个变量，
    # 这两种情形都会让抽样验证的变成**另一条式子**，必须先拦下。
    # 注意：**不清洗单字母常量 i**——它恰恰是最需要被歧义检查抓住的记号
    # （`-i ln(x)` 这类写法里，i 后面接的是隐式乘法而不是函数调用）
    cleaned = raw
    for name in sorted((KNOWN_FUNC_NAMES | PROSE_STOPWORDS | {"e", "pi"}),
                       key=len, reverse=True):
        cleaned = re.sub(r"(?<![\w\\])" + re.escape(name) + r"(?![\w])", " ", cleaned, flags=re.I)
    # LaTeX 命令（\sqrt 等）整体是一个记号，剥离后再查相邻字母，避免把 "sqrt" 的
    # 字母串误判成隐式乘法
    cleaned = re.sub(r"\\[A-Za-z]+", " ", cleaned)
    for m in re.finditer(r"[0-9][A-Za-z]", cleaned):
        suspect.append((m.group(), "数字紧邻字母：求值器按常量处理，隐式乘法不会被拆开"))
    for m in re.finditer(r"[A-Za-z][A-Za-z]", cleaned):
        suspect.append((m.group(), "字母紧邻字母：求值器合成一个标识符，隐式乘法不会被拆开"))
    for m in re.finditer(r"\b[A-Za-z][A-Za-z0-9_]*\s+[A-Za-z\\(]", cleaned):
        suspect.append((m.group().strip(),
                        "标识符后接空白再接表达式：求值器只解释为函数调用，疑为隐式乘法"))

    if suspect:
        return {"decidable": False, "scope": "parse_suspect",
                "reason": "解析结构不可信，抽样验证的将不是原式", "suspect_variables": suspect}
    return {"decidable": True, "scope": "elementary", "reason": "可抽样判定",
            "suspect_variables": [], "variables": vars_}


def verify_identity(raw: str, trials: int = 25, lo: float = 0.05, hi: float = 0.95,
                    seed: int = 20260919, tol: float = 1e-6) -> dict:
    """
    对**代数恒等式** lhs=rhs 做随机抽样数值验证（而非求根）。

    默认抽样区间为 [0.05,0.95]（单位区间），原因：反三角/对数等多值函数在 |z|>1 时
    会因**主分支约定不同**而出现虚假不符（见 pooled 实测：arctan/arcsin 恒等式在 z=2 时
    虚部符号相反），在单位区间内主分支一致，判定更可靠。调用方可放宽再试。
    """
    import random
    screen = screen_identity(raw)
    if not screen["decidable"]:
        return {
            "status": "not_decidable",
            "scope": screen["scope"],
            "reason": screen["reason"],
            "suspect_variables": [{"name": v, "why": w} for v, w in screen["suspect_variables"]],
            "trials_checked": 0,
            "caveat": ("未做抽样：本条超出随机抽样验证的能力范围。"
                       "此处不给 holds/fails，因为那样的结论反映的是求值器局限而非数学真伪。"),
        }
    parts = split_equation(raw)
    lhs_s, rhs_s = parts
    left = parse_text(lhs_s)
    right = parse_text(rhs_s)
    vars_ = screen["variables"]
    rng = random.Random(seed)
    checked, errors, maxdiff, worst = 0, 0, 0.0, None
    for _ in range(trials):
        env = {}
        for vv in vars_:
            # CD 公式里的 i 通常是虚数单位，赋 1j 才是作者的意图
            env[vv] = 1j if vv == "i" else rng.uniform(lo, hi)
        try:
            lv = evaluate(left.ast, env)
            rv = evaluate(right.ast, env)
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        try:
            if isinstance(lv, complex) or isinstance(rv, complex):
                diff = abs(complex(lv) - complex(rv))
                scale = max(1.0, abs(complex(lv)))
            else:
                diff = abs(float(lv) - float(rv))
                scale = max(1.0, abs(float(lv)))
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        checked += 1
        rel = diff / scale
        if rel > maxdiff:
            maxdiff = rel
            worst = {k: repr(v) for k, v in env.items()}  # repr 避免 complex 不可序列化

    if checked == 0:
        return {"status": "unevaluable", "trials_checked": 0, "eval_errors": errors,
                "reason": "抽样点均无法求值（超出定义域或函数不被求值器支持）", "variables": vars_}
    base = {
        "trials_checked": checked,
        "eval_errors": errors,
        "max_relative_diff": maxdiff,
        "worst_case_env": worst,
        "variables": vars_,
        "caveat": (f"仅在 [{lo},{hi}] 正实数域随机抽样(L2)；未覆盖负数与特殊点。"
                   f"'holds' 只是有限抽样证据，**绝非证明**。"),
    }
    # 只要有一个抽样点求值失败，结论就不能算可靠：可能是定义域问题，不是式子错
    if errors > 0:
        base.update({"status": "inconclusive",
                     "reason": f"{trials} 次抽样中有 {errors} 次无法求值，判定不可靠"})
        return base
    base.update({"status": "holds" if maxdiff <= tol else "fails"})
    if base["status"] == "fails" and re.search(r"\b(arc|ar)?(sin|cos|tan|sec|csc|cot)", raw, re.I):
        base["branch_warning"] = (
            "本条含多值（反三角/反双曲）函数：差异**可能**只是分支约定不同"
            "（尤其在分支切割 |z|>1 上，奇性都可能不保持），"
            "因此这里的 'fails' **不等于找到反例**，也不说明 CD 写错了。"
        )
    return base


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
