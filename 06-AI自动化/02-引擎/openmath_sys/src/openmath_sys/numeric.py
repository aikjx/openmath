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
from .parser import (parse_text, evaluate, standalone_letters,
                     _CONSTANT_VALUES, _NONFINITE_NAMES, _BUILTIN_FUNC_NAMES,
                     FuncCall, Var, BinOp, UnaryOp)

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

# 散文词分成两档，因为 `a` / `an` 同时是**最常用的数学变量名**。
#
# 旧逻辑把 `a` 无条件当散文词，于是 `lcm(a,b) = a*b/gcd(a,b)` 这类式子永远停在
# not_decidable——被拦下的不是"数学上不可判"，而是"英文冠词恰好和变量名同形"。
# 这是把**求值器的命名习惯**误当成了**式子的性质**。
#
# 现在的判据需要**共现证据**：`a` 只有在同一条原文里还出现了"硬散文词"
# （the / such / that / sum / of …）时才判为散文；否则按变量处理。
# `the sum of x = x` 仍然被拒（the/sum/of 都在硬档里），不会被这次放宽漏过去。
AMBIGUOUS_PROSE_WORDS = frozenset({"a", "an"})
HARD_PROSE_WORDS = PROSE_STOPWORDS - AMBIGUOUS_PROSE_WORDS

# 需要**整数**自变量的函数。gcd/lcm 的定义域是整数：在 [0.05,0.95] 上抽实数，
# int(round(x)) 只会得到 0 或 1，gcd 恒为 0、分母为 0，式子直接变成 unevaluable。
# 检测到这些函数时，抽样域必须整体切到正整数，并在结论里如实标注。
# 注意：floor/ceil/round **不在**这张表里——它们在实数上有定义，
# 恒等式 `floor(x)+floor(x+1/2) = floor(2x)` 需要实数抽样才能验，
# 把它们归进"整数函数"反而会把这类式子的抽样域压成整数，验不出东西。
INTEGER_FUNC_NAMES = frozenset({"gcd", "lcm", "mod", "factorial", "binom",
                                "choose"})

# 整数域抽样的范围（闭区间，正整数）。选 1..60：足够大以使 gcd/lcm 的取值有区分度，
# 又足够小以避免 a*b 溢出 float 精度（60*60=3600，远小于 2^53）。
INT_LO, INT_HI = 1, 60

# 多值函数（各有两条主分支）。**只有**含这些函数的式子才可能出现
# "整体差一个符号"的分支伪影，因此"纯符号翻转 → 分支降级"只对它们生效。
#
# 为什么必须限定：`for all a,b | a - b = b - a` 在**每一个**抽样点上都满足
# rv = −lv（因为 a−b 恒等于 −(b−a)），但它是**真的假恒等式**——
# 交换律套到减法上不成立，必须判 fails。若不限定函数范围，
# 这条降级规则就会变成给反例开脱的后门（2026-09-21 实测踩到过）。
# 判据用**解析出的函数名**而不是正则扫字符串，避免散文里出现同名子串时误命中。
MULTIVALUED_FUNCS = frozenset({
    "arcsin", "asin", "arccos", "acos", "arctan", "atan",
    "arcsec", "asec", "arccsc", "acsc", "arccot", "acot",
    "arcsinh", "asinh", "arccosh", "acosh", "arctanh", "atanh",
    "arcsech", "asech", "arccsch", "acsch", "arccoth", "acoth",
})

# 出现在"变量表"里 → 说明函数名未被求值器识别，被降级成了变量
# 这张表是**承诺表**：列进去的名字必须真的被 parser._call_func 实现。
# 曾经 max/min/floor/ceil 在这里但求值器没实现，式子走到执行层才抛
# unknown function，整条退化成 unevaluable——筛查层以为支持、执行层才炸，
# 比干脆不声明更糟。`det` 因求值器没有矩阵类型而移出本表：
# 未声明的 det 会在筛查阶段就被拦下（解析成多字符标识符 → parse_suspect），
# 拒答原因明确，好过执行时炸。审计 §⑦ 有一条检查保证这里不再出现空洞承诺。
KNOWN_FUNC_NAMES = frozenset(
    "sin cos tan sec csc cot sinh cosh tanh sech csch coth arcsin arccos arctan "
    "arcsec arccsc arccot arcsinh arccosh arctanh arcsech arccsch arccoth "
    "exp ln log sqrt abs gcd lcm max min floor ceil".split()
)

# 允许出现的非常量多字符标识符（目前为空：求值器不支持隐式乘法，
# 长度≥2 的"变量"几乎必然是 `iz`/`ix` 这类未拆开的隐式乘积）
ALLOWED_MULTICHAR_VARS = frozenset()

# 求值器内置的常量名（此处的 e 与 pi 指自然常数与圆周率，i 指虚数单位）
CONSTANT_NAMES = frozenset({"e", "pi", "i"})

# 备用抽样域：|z|>1。arcsec/arccsc/arccoth 这类函数要求自变量落在单位圆外才有实/主值，
# 在 [0.05,0.95] 上判不出结果属**定义域问题**，不是式子错，故允许补试一次。
ALT_LO, ALT_HI = 1.2, 5.0


# 用于隐式乘法检测的函数名选择支（长名优先，避免 `arc` 抢在 `arcsin` 之前匹配）
_FUNC_ALT = "|".join(sorted(KNOWN_FUNC_NAMES, key=len, reverse=True))


def _word_at(text: str, i: int) -> str:
    """返回 text[i] 所在的**完整连续字母串**，用于判断标识符边界。"""
    j = i
    while j > 0 and text[j - 1].isalpha():
        j -= 1
    k = i
    while k < len(text) and text[k].isalpha():
        k += 1
    return text[j:k]


def normalize_implicit_mul(raw: str) -> tuple:
    """
    把文本中**高置信度**的隐式乘法补成显式 `*`，返回 `(新文本, 改动说明列表)`。

    定位：这是 screen_identity 拒答之后的**补救手段**，且规范化后必须重新走一遍筛查。
    因此即便此处判断有误，后果也只是"继续拒答"，不会凭空造出 holds/fails。

    启用的三条规则（都要求紧邻且边界明确）：

    - R1 数字紧跟标识符或左括号：`2z` → `2*z`，`2(1+z)` → `2*(1+z)`
    - R1b 数字**隔空白**紧邻函数/左括号：`2 ln(x)` → `2*ln(x)`
      （实测：不补的话求值器会把整条式子静默截断成常数 `2`，这是 arcsech 假阴性的根因）
    - R2 右括号紧跟标识符/数字/左括号：`(1+z)w` → `(1+z)*w`，`(a)(b)` → `(a)*(b)`
    - R3 独立出现的单字母 `i` 与相邻标识符：`iz` → `i*z`（前提是 `i` 在式中另有独立出现，
      说明它确实是虚数单位或变量，而不是 `pi`/`is` 这类词的一部分）
    - R4 单字母标识符**隔空白**紧邻函数：`-i ln(x)` → `-i*ln(x)`

    刻意**不**处理 `f(x)` 这种"单字母紧邻左括号"的形态——那更可能是函数调用而非乘积，
    误插会直接制造假阴性。这是本函数保守性的关键取舍。
    """
    text = raw
    changes: list = []
    before = text

    # R1：数字紧跟标识符/左括号
    text = re.sub(r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)(?=[A-Za-z(])", r"\1*", text)
    if text != before:
        changes.append("R1 数字与标识符之间的隐式乘法")

    # R1b：数字 + 空白 + 函数名/LaTeX 命令/左括号
    before = text
    text = re.sub(r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)\s+(?=(?:" + _FUNC_ALT +
                  r")\s*\(|\\[A-Za-z]+\s*\(|\()", r"\1*", text)
    if text != before:
        changes.append("R1b 数字与后续函数之间的隐式乘法")

    # R2：右括号紧跟标识符/数字/左括号
    before = text
    text = re.sub(r"\)(?=[A-Za-z0-9(])", ")*", text)
    if text != before:
        changes.append("R2 右括号与后续因子之间的隐式乘法")

    # R4：单字母标识符 + 空白 + 函数名/LaTeX 命令
    before = text
    text = re.sub(r"(?<![A-Za-z0-9_.])([A-Za-z])\s+(?=(?:" + _FUNC_ALT +
                  r")\s*\(|\\[A-Za-z]+\s*\()", r"\1*", text)
    if text != before:
        changes.append("R4 变量与后续函数之间的隐式乘法")

    # R3：独立单字母 i 的隐式乘法（仅在 i 另有独立出现时才启用）
    if re.search(r"(?<![A-Za-z0-9_.])i(?![A-Za-z0-9_.])", text):
        before = text

        def _r3fwd(m):
            w = _word_at(text, m.start())
            if w in PROSE_STOPWORDS or w in KNOWN_FUNC_NAMES:
                return "i"          # `is`/`in`/`int` 这类散文词，不是乘法
            return "i*"

        def _r3bwd(m):
            w = _word_at(text, m.start())
            # 只接受"恰好两个字母且末位为 i"的形态，且排除 pi/ei 等常量名
            if len(w) != 2 or w[1] != "i" or w in CONSTANT_NAMES:
                return "i"
            if w in PROSE_STOPWORDS or w in KNOWN_FUNC_NAMES:
                return "i"
            return "*i"

        text = re.sub(r"(?<![A-Za-z0-9_.])i(?=[A-Za-z])", _r3fwd, text)
        text = re.sub(r"(?<=[A-Za-z])i(?![A-Za-z0-9_.])", _r3bwd, text)
        if text != before:
            changes.append("R3 虚数单位 i 与相邻标识符之间的隐式乘法")

    return text, changes


# `for all a,b | a*(b+c) = a*b + a*c` 这类**全称量化式**在 CD 里大量出现
# （实测 30 条未解析样本里有 10 条纯粹是被 `for all ... |` 前缀卡住的）。
# 前缀本身不改变式子的数学内容——它只是声明"以下变量是全称约束的"。
# 所以这里把它剥掉、把**约束变量表一并留下**，剩下的主体按普通恒等式抽样。
#
# 只认 `for all <变量表> |` 这一种形式，且主体必须干净：
# 出现存在量词 / 蕴含 / 条件句 / 并列关系，一律不剥（那是另一回事，
# 剥了以后抽样验证的将是**别的东西**）。
_QUANT_PREFIX_RE = re.compile(
    r"^\s*(?:for\s+all|forall)\s+"
    r"(?:(?:integers?|reals?|complex|natural|positive|non-?zero|nonzero)\s+)*"
    r"([A-Za-z][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z][A-Za-z0-9_]*)*)\s*(?:\||:)\s*",
    re.I,
)
# 主体里出现这些 → 不是"纯全称代数恒等式"，不剥
_QUANT_BODY_BLOCKERS = (
    "there exist", "there does not exist", "there is no", "implies", "whenever",
    " if ", " then ", " and ", " or ", "such that", "iff",
)


def strip_universal_quantifier(raw: str) -> tuple | None:
    """剥掉 `for all ... |` 全称前缀，返回 (约束变量表, 主体)；不适用则返回 None。

    返回的**主体**可以直接交给 screen_identity / verify_identity；
    约束变量表要一起记进结论——它说明的是"这条式子主张对所有这些变量成立"，
    而抽样只覆盖了**主体里真正出现的**那些变量（没出现的变量不影响等式真假，
    但结论里必须写清楚，不能让读者以为全部约束变量都被抽到了）。
    """
    m = _QUANT_PREFIX_RE.match(raw)
    if not m:
        return None
    body = raw[m.end():].strip()
    if not body:
        return None
    low = body.lower()
    if any(b in low for b in _QUANT_BODY_BLOCKERS):
        return None
    bound = [v.strip() for v in m.group(1).split(",")]
    # 主体必须是**单个**等式：存在第二个关系运算符说明这是并列命题
    if len(re.findall(r"=|<=|>=|!=|<|>", body)) != 1:
        return None
    return bound, body


# 函数式写法的逻辑连接词。`not(not(x))=x` 这类句子用的是函数调用外形，
# 用词表里的 `not `（带尾空格）匹配不到，会漏到"未定义函数符号"去。
# 归到 logic 档才是诚实的：它是逻辑命题，不是代数恒等式，与真假无关。
_LOGICAL_CONNECTIVES = frozenset(
    {"not", "and", "or", "implies", "iff", "xor", "exists", "forall", "in"})


def _contains_call(node) -> bool:
    """AST 中是否含函数调用。"""
    if isinstance(node, FuncCall):
        return True
    if isinstance(node, BinOp):
        return _contains_call(node.left) or _contains_call(node.right)
    if isinstance(node, UnaryOp):
        return _contains_call(node.operand)
    return False


def _has_nested_call(node) -> bool:
    """AST 中是否存在**嵌套函数应用**（一次调用的实参里又出现调用，如 f(g(x))）。"""
    if isinstance(node, FuncCall):
        return any(_contains_call(a) or _has_nested_call(a) for a in node.args)
    if isinstance(node, BinOp):
        return _has_nested_call(node.left) or _has_nested_call(node.right)
    if isinstance(node, UnaryOp):
        return _has_nested_call(node.operand)
    return False


def _contains_symbol(node, name: str) -> bool:
    """AST 中是否出现该标识符（作为变量、或作为被调用的函数名）。"""
    low = name.lower()
    if isinstance(node, Var):
        return node.name.lower() == low
    if isinstance(node, FuncCall):
        return node.name.lower() == low or any(
            _contains_symbol(a, name) for a in node.args)
    if isinstance(node, BinOp):
        return _contains_symbol(node.left, name) or _contains_symbol(node.right, name)
    if isinstance(node, UnaryOp):
        return _contains_symbol(node.operand, name)
    return False


def classify_unknown_symbols(left, right):
    """
    识别**不是恒等式**的三类语句，避免它们落进笼统的 parse_suspect
    （2026-09-21 新增）。判据全部基于解析树的结构证据，不靠正则猜。

    - `definitional`：左侧在**定义一个新符号**（`complex_cartesian(x,y) = x + iy`、
      `identity(x) = x`、`bigfloat(m,r,e)=m*r^e`）。右端不含该符号 ⇒ 这是定义式，
      不是恒真命题。对定义式判 holds 是**循环论证**（拿定义去"验证"定义），必须拒答。
    - `higher_order`：含**函数值变量**（同一个字母既当函数名又被当数值变量，如
      `left_compose(f,g)(x) = f(g(x))` 里的 f、g）或**嵌套函数应用**（`f(g(x))`）。
      抽样求值器会把函数名当数值变量代入，验证的不是原式。
    - `unknown_function`：其余"对未定义函数符号做调用"的情形（`f(x)=f(x)`、
      `x = real(x+iy)`）。求值器无从取它的值。

    返回 None 表示没有未定义符号（可继续后续筛查）。
    """
    used = list(left.functions) + list(right.functions)
    unknown = sorted({f for f in used if f.lower() not in _BUILTIN_FUNC_NAMES})
    if not unknown:
        return None
    logic_hits = sorted(f for f in unknown if f.lower() in _LOGICAL_CONNECTIVES)
    if logic_hits:
        return {"decidable": False, "scope": "logic",
                "reason": ("含逻辑连接词 " + "/".join(logic_hits) +
                           "（函数式写法）：这是逻辑命题，不是代数恒等式"),
                "suspect_variables": []}
    called = {f.lower() for f in used}
    value_vars = ({v.lower() for v in left.variables}
                  | {v.lower() for v in right.variables})
    func_valued = sorted(called & value_vars)
    nested = _has_nested_call(left.ast) or _has_nested_call(right.ast)
    if func_valued or nested:
        parts = []
        if func_valued:
            parts.append("函数值变量 " + "/".join(func_valued))
        if nested:
            parts.append("嵌套函数应用")
        return {"decidable": False, "scope": "higher_order",
                "reason": ("含" + "、".join(parts) +
                           "：抽样求值器把函数名当数值变量代入，验证的不是原式"),
                "suspect_variables": []}
    head = left.ast.name if isinstance(left.ast, (FuncCall, Var)) else None
    if (head is not None and head.lower() in {u.lower() for u in unknown}
            and not _contains_symbol(right.ast, head)):
        return {"decidable": False, "scope": "definitional",
                "reason": (f"该语句在定义新符号 {head}（左端是新符号的调用、右端不含它）："
                           "这是定义式，不是待验证的恒等式"),
                "suspect_variables": []}
    return {"decidable": False, "scope": "unknown_function",
            "reason": ("含未定义的函数符号 " + "/".join(unknown) +
                       "：求值器无从取它的值，抽样验证的不是原式"),
            "suspect_variables": []}


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
    # 隐式乘法的证据要跨等号收集：`exp(ix)` 只在右侧、独立的 `x` 只在左侧。
    # 若分别解析，`ix` 就会因为没有本地证据而保持为一个名叫 ix 的变量。
    ctx = standalone_letters(raw)
    left, right = parse_text(lhs_s, ctx), parse_text(rhs_s, ctx)
    if not (left.parse_ok and right.parse_ok):
        return {"decidable": False, "scope": "unparsable",
                "reason": "两侧之一无法解析", "suspect_variables": []}

    vars_ = sorted(set(left.variables) | set(right.variables))

    # 命名常量**不是变量**（2026-09-21 修）。
    #
    # 解析器一直认得 e/pi/tau/phi 这几个名字（用来决定"别把它们拆成乘积"），
    # 却从没在求值时代入数值，于是它们落进 vars_ 被当自由变量抽样：
    # `exp(A) = e^A` 里的 e 被抽成 0.2578…，教科书真恒等式判成 **fails**。
    # 这类**假反例**（断言一个真命题是错的）比拒答危险得多，必须从根上断掉。
    consts = [v for v in vars_ if v in _CONSTANT_VALUES]
    nonfinite = [v for v in vars_ if v in _NONFINITE_NAMES]
    sample_vars = [v for v in vars_ if v not in _CONSTANT_VALUES and v not in _NONFINITE_NAMES]
    if nonfinite:
        return {"decidable": False, "scope": "nonfinite",
                "reason": ("含非有限量 " + "/".join(nonfinite) +
                           "（inf/nan）：代入后任何式子都恒为 inf/nan，抽样判定没有意义"),
                "suspect_variables": [], "constants": consts}

    # 先区分"待解方程"与"恒等式"：形如 f(x)=0 的是求解对象，不是恒真命题。
    #
    # 判据不能只看"右侧是 0"——`for all a | 0*a = 0` 和 `for all a | a+(-a) = 0`
    # 的右侧同样是 0，但它们是**恒等式**（左侧恒等于 0），不是待解方程。
    # 旧逻辑只看右侧，把这两类一起误杀。真正的判据是左侧**是否随变量变化**：
    # 取几个抽样点，左侧取值不变 → 它是常数左端，属恒等式；左侧取值变了 →
    # 才是"求哪些 x 使 f(x)=0"。这条判据用数值证据，不靠形式猜测。
    rhs_probe = parse_text(rhs_s)
    if rhs_probe.parse_ok and not rhs_probe.variables and vars_:
        try:
            rv = float(evaluate(rhs_probe.ast, {v: 1.0 for v in vars_}))
        except Exception:  # noqa: BLE001
            rv = None
        if rv is not None and abs(rv) < 1e-12:
            lhs_probe = parse_text(lhs_s, ctx)
            lhs_constant = False
            if lhs_probe.parse_ok:
                probes = []
                for t in (0.3, 1.7, 4.1):
                    env_p = {v: (_CONSTANT_VALUES[v] if v in _CONSTANT_VALUES
                                 else (1j if v == "i" else t)) for v in vars_}
                    try:
                        probes.append(complex(evaluate(lhs_probe.ast, env_p)))
                    except Exception:  # noqa: BLE001
                        probes.append(None)
                if all(p is not None for p in probes):
                    lhs_constant = all(abs(p - probes[0]) < 1e-9 for p in probes)
            if not lhs_constant:
                return {"decidable": False, "scope": "equation",
                        "reason": "右侧为常数 0 且左侧随变量变化：这是待解方程，不是恒等式",
                        "suspect_variables": []}

    # 定义式 / 函数值变量 / 未定义函数符号——单列分类，不再混进 parse_suspect。
    # 放在"待解方程"判定之后，是为了不改动 `f(x)=0` 这类式子的既有归类（方程优先）。
    nonid = classify_unknown_symbols(left, right)
    if nonid is not None:
        return nonid

    # `a` / `an` 是歧义档：必须找到**同句共现的硬散文词**才判为散文，
    # 否则它就是一个普通的变量名（见 AMBIGUOUS_PROSE_WORDS 的注释）。
    raw_words = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", lower))
    prose_context = bool(raw_words & HARD_PROSE_WORDS)

    suspect = []
    # 常量不参与"是否像变量"的检查：`e` 命中 HARD_PROSE_WORDS（英文停止词表）纯属
    # 巧合，它在这里是欧拉数。若哪天真的把 e 当变量用，下面的歧义回退会兜住。
    for v in sample_vars:
        vl = v.lower()
        if vl in HARD_PROSE_WORDS:
            suspect.append((v, "英文散文词被当作变量"))
        elif vl in AMBIGUOUS_PROSE_WORDS and prose_context:
            suspect.append((v, "英文散文词被当作变量（同句另有散文词，疑为叙述句而非公式）"))
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
    # 解析器已把连写拆成乘积的情形（`ix` → `i*x`）不应算"未被解析到"：
    # 那些字母都在 vars_ 里，拆开反而是**正确**结果。缺这一步会把
    # `sin(x) = (e^{ix} − e^{−ix})/(2i)` 判成 parse_suspect，进而退化到
    # normalize_implicit_mul 那条把优先级做错的旧路上去。
    unknown = [t for t in unknown if not set(t) <= set(vars_)]
    for t in unknown:
        suspect.append((t, "原文中的标识符未被解析到（可能被求值器静默丢弃）"))

    # 隐式乘法：**解析器现在已经支持**（见 parser.insert_implicit_mul /
    # split_letter_runs），所以这四条正则不再是"一律拦下"，而是"解析器没拆开才拦"。
    #
    # 判据是最后的变量清单：若所有变量都是单字母（或白名单里的多字符名），说明
    # `2z` / `iz` / `2 ln(x)` 这类连写都已被拆成乘积，没有标识符被吞掉。
    # 旧逻辑无条件拦下的后果是：这些真恒等式永远停在 not_decidable；
    # 而如果被母线上的 normalize_implicit_mul 改写成松散的 `2*i`，
    # `1/2i` 会变成 `(1/2)*i`，把**真恒等式判成 fails**（第五轮实测的回归）。
    #
    # 另一个副作用（也是必须的）：通过这道关的式子走的是 raw 原文，
    # 不再经过 normalize_implicit_mul —— 那个函数补的是**松散** `*`，
    # 会把 `/2i` 改写成 `/2*i`，优先级从「紧贴」掉回「普通乘」。
    # 解析出来了但是**多字符**的变量 = 连写没被拆开（或本就是未知标识符）
    unresolved = [v for v in sample_vars
                  if len(v) >= 2 and v not in ALLOWED_MULTICHAR_VARS]
    if unresolved:
        cleaned = raw
        for name in sorted((KNOWN_FUNC_NAMES | PROSE_STOPWORDS | {"e", "pi"}),
                           key=len, reverse=True):
            cleaned = re.sub(r"(?<![\w\\])" + re.escape(name) + r"(?![\w])",
                             " ", cleaned, flags=re.I)
        # LaTeX 命令（\sqrt 等）整体是一个记号，剥离后再查相邻字母，避免把 "sqrt"
        # 的字母串误判成隐式乘法
        cleaned = re.sub(r"\\[A-Za-z]+", " ", cleaned)
        for m in re.finditer(r"[0-9][A-Za-z]", cleaned):
            suspect.append((m.group(),
                            "数字紧邻字母：解析器未拆开，可能变成两个不相干的记号"))
        for m in re.finditer(r"[A-Za-z][A-Za-z]", cleaned):
            suspect.append((m.group(),
                            "字母紧邻字母：解析器未拆开，连写被当成单个标识符"))
        for m in re.finditer(r"[0-9]\s+[A-Za-z\(]", cleaned):
            suspect.append((m.group().strip(),
                            "数字隔空白紧邻标识符：解析器未拆开，式子会被截断成常数"))
        for m in re.finditer(r"\b[A-Za-z][A-Za-z0-9_]*\s+[A-Za-z\(]", cleaned):
            suspect.append((m.group().strip(),
                            "标识符后接空白再接表达式：疑为隐式乘法且解析器未处理"))

    if suspect:
        # 拒答理由必须写出**具体是哪一类**（诚实红线）。
        # 此前九条拒答共用一句"解析结构不可信"，把三类完全不同的毛病
        # （未定义函数名 / 数字紧邻字母没拆开 / 标识符被静默丢弃）说成同一个，
        # 读报告的人无法判断该去修哪里。这里按实际触发的类别合成，
        # 并把触发到的原文片段一并写进去。
        causes: list[str] = []
        for tok, why in suspect:
            key = why.split("：")[0].split("（")[0]
            if key not in causes:
                causes.append(key)
        toks = [t for t, _ in suspect]
        return {"decidable": False, "scope": "parse_suspect",
                "reason": ("解析结构不可信（" + "；".join(causes) + "），"
                           "抽样验证的将不是原式"),
                "causes": causes, "offending_tokens": toks,
                "suspect_variables": suspect, "constants": consts}

    # 整数函数（gcd/lcm/…）要求自变量是整数：继续用实数抽样只会得到 0/0。
    int_funcs = sorted((set(left.functions) | set(right.functions)) & INTEGER_FUNC_NAMES)
    return {"decidable": True, "scope": "elementary", "reason": "可抽样判定",
            "suspect_variables": [], "variables": sample_vars,
            "constants": consts, "symbols_seen": vars_,
            "integer_funcs": int_funcs,
            "n_variables": len(sample_vars)}


def verify_identity(raw: str, trials: int = 25, lo: float = 0.05, hi: float = 0.95,
                    seed: int = 20260919, tol: float = 1e-6,
                    _alt_tried: bool = False, _ignore_constants: bool = False) -> dict:
    """
    对**代数恒等式** lhs=rhs 做随机抽样数值验证（而非求根）。

    默认抽样区间为 [0.05,0.95]（单位区间），原因：反三角/对数等多值函数在 |z|>1 时
    会因**主分支约定不同**而出现虚假不符（见 pooled 实测：arctan/arcsin 恒等式在 z=2 时
    虚部符号相反），在单位区间内主分支一致，判定更可靠。调用方可放宽再试。
    """
    import random
    quant = None
    stripped = strip_universal_quantifier(raw)
    if stripped is not None:
        bound, body = stripped
        pre = screen_identity(body)
        if not pre["decidable"]:
            # 前缀剥掉了主体仍不可判：如实给出**主体**的拒答原因，
            # 而不是笼统甩一句"含量词"——后者听上去像量词本身不可处理，
            # 实际上真正卡住的是主体。
            return {
                "status": "not_decidable",
                "scope": pre["scope"],
                "reason": pre["reason"],
                "suspect_variables": [{"name": v, "why": w}
                                      for v, w in pre["suspect_variables"]],
                "quantifier": {"bound_variables": bound, "body": body},
                "trials_checked": 0,
                "caveat": ("已剥掉全称量词前缀，但**主体**仍超出抽样验证的能力范围，故拒答。"
                           "此处不给 holds/fails，因为那样的结论反映的是求值器局限而非数学真伪。"),
            }
        quant = {"bound_variables": bound, "body": body,
                 "sampled_variables": pre["variables"],
                 "note": ("全称量词前缀已剥离；抽样只覆盖**主体中实际出现**的变量，"
                          "未在主体中出现的约束变量不影响等式真假，但也**没有被抽到**。")}
        raw = body

    screen = screen_identity(raw)
    if not screen["decidable"]:
        # 补救：先尝试把隐式乘法补成显式的，再重新筛查。
        # 若规范化后仍不可判定，才维持拒答——**不会**因为规范化而放宽判准。
        norm, changes = normalize_implicit_mul(raw)
        if changes and norm != raw and screen_identity(norm)["decidable"]:
            out = verify_identity(norm, trials=trials, lo=lo, hi=hi, seed=seed, tol=tol)
            out["normalized_from"] = raw
            out["normalizations"] = changes
            out["caveat"] = (out.get("caveat", "") +
                             " 判定前已把原文中的隐式乘法补成显式（" + "；".join(changes) + "）。")
            return out
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
    ctx = standalone_letters(raw)
    left = parse_text(lhs_s, ctx)
    right = parse_text(rhs_s, ctx)
    vars_ = screen["variables"]
    consts = list(screen.get("constants", []))
    if _ignore_constants:
        # 歧义回退用：把命名常量当**自由变量**再抽一遍（见下文 fails 分支）
        vars_ = sorted(set(vars_) | set(consts))
        consts = []
    # gcd/lcm 之类只在整数上有意义，切成整数抽样域（见 INTEGER_FUNC_NAMES 注释）
    int_mode = bool(screen.get("integer_funcs"))
    slo, shi = (INT_LO, INT_HI) if int_mode else (lo, hi)
    rng = random.Random(seed)
    checked, errors, maxdiff, worst = 0, 0, 0.0, None
    flip_points, eval_points = 0, 0
    for _ in range(trials):
        env = {}
        # 命名常量先代入（e/pi/tau/phi），再抽自由变量，两者互不重叠。
        for cc in consts:
            env[cc] = _CONSTANT_VALUES[cc]
        for vv in vars_:
            # CD 公式里的 i 通常是虚数单位，赋 1j 才是作者的意图
            if vv == "i":
                env[vv] = 1j
            elif int_mode:
                env[vv] = float(rng.randint(slo, shi))
            else:
                env[vv] = rng.uniform(slo, shi)
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
        # 记录"纯符号翻转"的点数：rv ≈ −lv 是所有点上的一致模式时，
        # 差异来自**主分支选取**（arcsec/arccosh 这类多值函数各有两条分支），
        # 不是原式写错了。见下面 fails 的分支降级。
        try:
            if abs(complex(lv) + complex(rv)) <= 1e-9 * max(1.0, abs(complex(lv))):
                flip_points += 1
        except Exception:  # noqa: BLE001
            pass
        eval_points += 1
        rel = diff / scale
        if rel > maxdiff:
            maxdiff = rel
            worst = {k: repr(v) for k, v in env.items()}  # repr 避免 complex 不可序列化

    if checked == 0:
        return {"status": "unevaluable", "trials_checked": 0, "eval_errors": errors,
                "reason": "抽样点均无法求值（超出定义域或函数不被求值器支持）", "variables": vars_}
    if int_mode:
        domain_desc = f"[{slo},{shi}] 正整数"
        caveat = (f"仅在 {domain_desc}域随机抽样(L2)；未覆盖 0、负数与大整数，"
                  f"也未覆盖自变量为 0 的退化情形。"
                  f"因为式中含 {'/'.join(screen['integer_funcs'])} 等只对整数有定义的函数，"
                  f"实数抽样会退化成 0/0，故改用整数域。"
                  f"'holds' 只是有限抽样证据，**绝非证明**。")
    else:
        domain_desc = f"[{slo},{shi}] 正实数"
        caveat = (f"仅在 {domain_desc}域随机抽样(L2)；未覆盖负数与特殊点。"
                  f"'holds' 只是有限抽样证据，**绝非证明**。")
    base = {
        "trials_checked": checked,
        "eval_errors": errors,
        "max_relative_diff": maxdiff,
        "worst_case_env": worst,
        "variables": vars_,
        "constants_bound": consts,
        "sign_flip_points": flip_points,
        "sampling_domain": {"mode": "integer" if int_mode else "real",
                            "lo": slo, "hi": shi,
                            "integer_funcs": screen.get("integer_funcs", []),
                            "n_variables": len(vars_)},
        "caveat": caveat,
    }
    if consts:
        base["caveat"] += (f" 命名常量 {'/'.join(consts)} 按标准数值代入"
                           f"（e=2.718…、pi=3.141…），**未被抽样**；"
                           f"若原文把该字母当普通变量用，本条判定不适用。")
    if quant:
        base["quantifier"] = quant
    # 只要有一个抽样点求值失败，结论就不能算可靠：可能是定义域问题，不是式子错
    if errors > 0:
        base.update({"status": "inconclusive",
                     "reason": f"{trials} 次抽样中有 {errors} 次无法求值，判定不可靠"})
        return base
    base.update({"status": "holds" if maxdiff <= tol else "fails"})

    # 多值函数在 |z|>1 分支上抽样才可能吻合（arcsec/arccsc/arccoth 要求 |z|>1）。
    # 这里**只在默认域判不出 holds 时**补试一个域，且要求补试域上零求值错误，
    # 否则维持原判定：宁可少判一条，也不把"换个域碰巧对上"说成恒成立。
    if (base["status"] != "holds" and not _alt_tried
            and re.search(r"arc(sin|cos|tan|sec|csc|cot)", raw, re.I)):
        alt = verify_identity(raw, trials=trials, lo=ALT_LO, hi=ALT_HI, seed=seed, tol=tol,
                              _alt_tried=True)
        if alt.get("status") == "holds" and alt.get("eval_errors", 1) == 0:
            alt["verified_domain"] = [ALT_LO, ALT_HI]
            alt["domain_note"] = (
                f"默认域 [{lo},{hi}] 上不成立，而在 |z|>1 的域 [{ALT_LO},{ALT_HI}] 上吻合；"
                f"反三角/反双曲函数在单位区间内取值落在另一分支，属定义域差异而非式子错。"
                f"默认域的判定为 {base['status']}（最大相对差 {maxdiff:.3e}），一并保留。"
            )
            alt["default_domain_verdict"] = base["status"]
            alt["default_domain_max_relative_diff"] = maxdiff
            return alt
        base["alt_domain_verdict"] = alt.get("status")
        base["alt_domain_max_relative_diff"] = alt.get("max_relative_diff")

    # ---- 常量歧义回退（2026-09-21 新增）----
    # `e`/`pi` 既可能是自然常数，也可能是普通变量（偏心率、概率…）。
    # 默认按常数读；但如果因此判 fails，就按"变量"再抽一遍：两种读法结论相反时，
    # 正确动作是**拒答**而不是硬判——因为此时错的是我们的读法，不是原式。
    if base["status"] == "fails" and consts and not _ignore_constants:
        alt_c = verify_identity(raw, trials=trials, lo=lo, hi=hi, seed=seed, tol=tol,
                                _alt_tried=_alt_tried, _ignore_constants=True)
        base["constant_variable_reading_verdict"] = alt_c.get("status")
        if alt_c.get("status") == "holds":
            base.update({
                "status": "not_decidable",
                "scope": "ambiguous_constant",
                "reason": ("常量/变量读法歧义：" + "/".join(consts) +
                           " 按标准常数代入时判 fails，按普通变量抽样时判 holds；"
                           "两种读法结论相反，故拒答而不硬判"),
            })
            return base

    # ---- 分支纯符号翻转 → 降级为拒答（2026-09-21 新增）----
    # 多值函数（反三角/反双曲）各有两条主分支。若**每一个**抽样点上都恰好
    # rv ≈ −lv，那是分支选取的签名，而**不是**"找到了反例"。
    # 例：`arcsec z = i*arcsech z` —— z=0.5 时 lhs=−1.3169i、rhs=+1.3169i，
    # 只是另一个分支，原式在换分支后成立。
    #
    # 这条降级**不是**给反例开脱：只要有一点不是纯符号翻转（数值不同、或符号相同），
    # 就仍判 fails。也就是说它只吃掉"整体差一个符号"这一种模式。
    funcs_used = set(left.functions) | set(right.functions)
    if (base["status"] == "fails" and eval_points > 0
            and flip_points == eval_points
            and (funcs_used & MULTIVALUED_FUNCS)):
        base.update({
            "status": "not_decidable",
            "scope": "branch",
            "reason": (f"{eval_points}/{eval_points} 个抽样点上两侧恒为相反数（纯符号翻转），"
                       f"且式中含多值函数 {'/'.join(sorted(funcs_used & MULTIVALUED_FUNCS))}："
                       "这是主分支选取的差异，不是反例"),
            "branch_functions": sorted(funcs_used & MULTIVALUED_FUNCS),
        })
        return base

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
