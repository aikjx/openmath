"""方程解析器：自包含的数学表达式词法/语法分析与求值。

支持：整数/浮点、变量、+ - * / ^、一元负号、括号、函数调用、
以及 '=' 关系（方程）。不依赖任何第三方库。
"""
from __future__ import annotations

import math
import cmath
import re
from typing import Any

from .models import MathExpr


# ---------------------------------------------------------------------------
# AST 节点
# ---------------------------------------------------------------------------
class _Node:
    pass


class Num(_Node):
    def __init__(self, v: float):
        self.v = float(v)

    def __repr__(self) -> str:
        return f"Num({self.v})"


class Var(_Node):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"Var({self.name})"


class BinOp(_Node):
    def __init__(self, op: str, left: _Node, right: _Node):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


class UnaryOp(_Node):
    def __init__(self, op: str, operand: _Node):
        self.op = op
        self.operand = operand

    def __repr__(self) -> str:
        return f"({self.op}{self.operand})"


class FuncCall(_Node):
    def __init__(self, name: str, args: list[_Node]):
        self.name = name
        self.args = args

    def __repr__(self) -> str:
        return f"{self.name}({self.args})"


class Relation(_Node):
    def __init__(self, op: str, left: _Node, right: _Node):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


# ---------------------------------------------------------------------------
# 词法分析 + 隐式乘法（token 层）
# ---------------------------------------------------------------------------
# 以前的做法是：numeric.py 的文本预处理器先补 `*` 再喂进来；parser 自己遇到
# `2z` 这种相邻因子会抛 ValueError，最终由 screen_identity 判成 not_decidable。
# 也就是说"隐式乘法"以前是被**识别成问题**而不是被**当成记法**。
#
# 现在在 token 层补齐它，配套的取舍有三条，都写在下面是非为了让持异议的人能推翻：
#   ① 只在"前一个 token 能结束一个因子、后一个 token 能开始一个因子"时插 `*`；
#   ② `VAR VAR`（如 `x y`）**不**补 —— 与多字符变量名（n、k? 见 task⑱ 注）
#      以及散文词（"the sum" 会被切成一串 VAR）无法区分，补了会凭空造出恒等式；
#   ③ FUNC 后紧跟 `(` 的情况 tokenizer 已经当成函数调用，不在这里重复处理。
#
# 边界表（prev 能否结束因子 / next 能否开始因子）：
#   能结束：NUM、VAR、FUNC、')'         能开始：NUM、VAR、FUNC、'('
_END = ("NUM", "VAR", "FUNC")
_START = ("NUM", "VAR", "FUNC")

# `_call_func` 支持的全部名字（含别名）与 Python 命名常量，供 split_letter_runs 排除。
# 与 _call_func 的分支必须保持同步：新增内置函数漏登记在这里，`sin` 可能被拆成 s*i*n。
# 这条同步由审计检查盯住（见 audit.py 的"内置函数名清单自洽"检查）。
_BUILTIN_FUNC_NAMES = frozenset({
    "plus", "minus", "times", "divide", "power", "abs", "sqrt",
    "exp", "ln", "log",
    "sin", "cos", "tan", "arcsin", "asin", "arccos", "acos", "arctan", "atan",
    "arcsec", "asec", "arccsc", "acsc", "arccot", "acot",
    "sec", "csc", "cot", "sinh", "cosh", "tanh", "sech", "csch", "coth",
    "arcsinh", "asinh", "arccosh", "acosh", "arctanh", "atanh",
    "arcsech", "asech", "arccsch", "acsch", "arccoth", "acoth",
    "gcd", "lcm", "max", "min", "floor", "ceil", "mod",
})
_NAMED_CONSTANTS = frozenset({"pi", "e", "tau", "phi", "inf", "nan"})
# 命名常量的**数值**（2026-09-21 新增）。
#
# 此前 _NAMED_CONSTANTS 只用来「别把这个名字拆成乘积」，**从未在求值时代入数值**。
# 后果是一类**假反例**：`exp(A) = e^A` 里的 `e` 被当成自由变量在 [0.05,0.95] 上
# 抽样，教科书真恒等式被判成 `fails`。假反例比拒答严重得多——拒答是"我不知道"，
# 假反例是"我断言它是错的"，后者会污染产物并让下游误以为找到了反例。
#
# 取值口径：pi/e/tau/phi 取 Python 双精度的标准值。若原文把 `e` 当普通变量
# （如偏心率），本条判定不适用——numeric.verify_identity 对此有**歧义回退**：
# 判 fails 时会再按"变量"读法试一次，两种读法结论相反则拒答而非硬判。
_CONSTANT_VALUES = {
    "pi": math.pi,
    "e": math.e,
    "tau": 2 * math.pi,
    "phi": (1 + math.sqrt(5)) / 2,
}
# inf / nan 不是可代入的有限常数：代入会让任何式子恒为 inf/nan，
# 于是"抽样结果全等"变成无意义。它们单独走不可抽样通道（见 numeric.screen_identity）。
_NONFINITE_NAMES = frozenset({"inf", "nan"})
# 允许参与连写切分的"单位"名（见 split_letter_runs 的判据说明）
_NAMED_UNITS = frozenset({"i", "e", "pi"})


def standalone_letters(raw: str) -> set:
    """原式里**独立出现过的单字母**集合，供 `split_letter_runs` 作证据。

    之所以要单独抽出来：左右两侧会被**分别**解析（见 numeric.screen_identity），
    而 `exp(ix)` 只在右侧出现、独立的 `x` 却只在左侧出现。
    证据必须跨等号收集，否则 `ix` 拆不开。
    """
    tokens, _ws = scan_tokens(raw)
    return {t[1] for t in tokens if t[0] == "VAR" and len(t[1]) == 1}


def _segment_run(word: str, names: set) -> list[str] | None:
    """把 `word` 切成一串"已知名"的拼接；切不动返回 None（**不猜**）。

    `names` = 该式里独立出现过的单字母 ∪ 已知单位名（虚数单位 i、e、π）。
    长名优先匹配，所以 `pi` 不会被切成 `p`与`i`。
    """
    pieces: list[str] = []
    k = 0
    while k < len(word):
        hit = None
        for span in (2, 1):
            piece = word[k:k + span]
            if len(piece) == span and piece in names:
                hit = piece
                break
        if hit is None:
            return None
        pieces.append(hit)
        k += len(hit)
    return pieces


def split_letter_runs(tokens: list[tuple[str, str]],
                      ws_before: list[bool] | None = None,
                      context_letters: set | None = None,
                      ) -> tuple[list[tuple[str, str]], list[bool]]:
    """把「多个变量连写」的 token 拆成乘积：`iz` -> `i * z`。

    词法扫描会把连续字母整块吃成一个 VAR，所以 `exp(ix)` 里的 `ix` 会变成一个
    名叫 `ix` 的变量。要在 token 层拆开，必须回答「凭什么认为它是连写而不是
    一个变量名」。

    判据是**证据式的**：这个串必须能整段切分为「在该式别处**独立出现过的单字母**」
    或「已知单位名」（虚数单位 i、自然常数 e、圆周率 pi）的拼接，才认定它是连写。

    为什么要算上单位名：`cos(x) = (e^{ix}+e^{-ix})/2` 里的 `i` **从不独立出现**，
    只认"独立出现过的字母"会把 `ix` 留成一个名叫 ix 的变量。

    副作用是散文天然安全：`the`/`sum`/`ranges` 既非单位名、其字母也不独立出现，
    切不动就保持原样。这是刻意留的安全阀——宁可在 `xyz` 这类纯连写上漏拆，
    也不把 `the` 拆成 `t*h*e`。

    内置函数名与整体已知的常量名另行排除，避免 `pi` 被拆成 `p*i`。

    返回值同时带上同步更新过的 `ws_before`（拆出来的后续片段与原片段紧贴），
    否则后续 `insert_implicit_mul` 的"紧贴 vs 隔空白"判据会错位。
    """
    ws = list(ws_before) if ws_before is not None else [False] * len(tokens)
    standalone = {t[1] for t in tokens if t[0] == "VAR" and len(t[1]) == 1}
    if context_letters:
        standalone |= set(context_letters)
    names = standalone | _NAMED_UNITS
    out: list[tuple[str, str]] = []
    out_ws: list[bool] = []
    for idx, (kind, val) in enumerate(tokens):
        pieces = None
        if (kind == "VAR" and len(val) >= 2
                and val.lower() not in _BUILTIN_FUNC_NAMES
                and val.lower() not in _NAMED_CONSTANTS):
            pieces = _segment_run(val, names)
        if pieces is not None and len(pieces) > 1:
            for k2, piece in enumerate(pieces):
                if k2:
                    out.append(("OP", "*"))
                    out_ws.append(False)
                out.append(("VAR", piece))
                out_ws.append(ws[idx] if k2 == 0 else False)
        else:
            out.append((kind, val))
            out_ws.append(ws[idx])
    return out, out_ws


def insert_implicit_mul(tokens: list[tuple[str, str]],
                        ws_before: list[bool] | None = None,
                        ) -> list[tuple[str, str]]:
    """在相邻因子的 token 之间补乘法记号。返回新列表，不改动入参。

    补出来的记号有两种，**优先级不同**：

    - `JUXTA`：两个因子**紧贴**（中间无空白）。它比 `*` 和 `/` 结合得更紧，
      于是 `1/2i` 是 `1/(2i)` 而不是 `(1/2)*i`。
    - `OP *`：两个因子**隔了空白**（如 `2 ln(x)`）。与显式写的 `*` 同优先级。

    这个区分不是我们拍的：`sin(x) = (e^{ix} − e^{−ix})/(2i)` 这条恒等式
    若按"垫片一律等价于显式 `*`"处理，右侧会变成 `(…)/2·i`，多出一个 `-1` 因子，
    真恒等式会被判成 fails（2026-09-19 实测到的回归，见 CHANGELOG 第五轮）。
    Mathematica 用同一套约定（有空白=普通乘，无空白=紧贴合）。
    """
    out: list[tuple[str, str]] = []
    for idx, tok in enumerate(tokens):
        if out:
            kind, val = tok
            if ((kind in _START or (kind == "PAREN" and val == "("))
                    and implicit_mul_needed(out[-1], tok)):
                tight = True if ws_before is None else not ws_before[idx]
                out.append(("JUXTA", "*") if tight else ("OP", "*"))
        out.append(tok)
    return out


def implicit_mul_needed(prev: tuple[str, str],
                        nxt: tuple[str, str]) -> bool:
    """是否需要在这两个相邻 token 之间补 `*`（导出以便独立审计逐格对照）。"""
    pk, pv = prev
    nk, nv = nxt
    prev_ends = pk in _END or (pk == "PAREN" and pv == ")")
    if not prev_ends:
        return False
    next_starts = nk in _START or (nk == "PAREN" and nv == "(")
    if not next_starts:
        return False
    # 取值 ②：两个 VAR 相邻只在**两边都是单字母**时补 ——
    #     多字符 token 之间（`pi r^2`、散文词序列 `the sum`）无法与多字符变量名区分，
    #     补了会把散文静默变成乘积。`pi r^2` 因此仍然解析失败（报错好过静默截断成 pi）。
    if pk == "VAR" and nk == "VAR" and not (len(pv) == 1 and len(nv) == 1):
        return False
    # FUNC 后面紧跟的 `(` 是**它的实参表**，不是乘积因子
    if pk == "FUNC" and nk == "PAREN" and nv == "(":
        return False
    # 内置函数名后面接的也不是乘积因子，而是它的**实参**（`cos 2A` → cos(2A)）。
    # 这里不插乘号，交给 parse_atom 的并列函数应用分支处理。
    #
    # 不加这一条会静默读错：`cos 2A` 的 token 流是 [VAR cos, NUM 2, VAR A]，
    # 原逻辑在 `cos` 与 `2` 之间补了紧贴乘号，于是整式被读成 cos·2·A，
    # 二倍角恒等式 cos 2A = cos²A − sin²A 永远判不出来（只会判成"函数名降级为变量"）。
    # 注意 `2 sin x` 不受影响：那里的 `2` 在前、函数名在后，乘号补在 2 与 sin 之间。
    if pk == "VAR" and pv.lower() in _BUILTIN_FUNC_NAMES:
        return False
    return True


def tokenize(s: str) -> list[tuple[str, str]]:
    """词法扫描。只需记号流时用这个；需要空白信息的用 `scan_tokens`。"""
    return scan_tokens(s)[0]


def scan_tokens(s: str) -> tuple[list[tuple[str, str]], list[bool]]:
    """词法扫描，同时记录每个记号**之前是否紧贴空白**。

    `ws_before[i]` 为真 ⟺ 第 i 个记号在原文里前面有空白。
    `insert_implicit_mul` 需要它来区分紧贴乘法与隔空白乘法——两者优先级不同。
    """
    tokens: list[tuple[str, str]] = []
    ws_before: list[bool] = []
    pending_ws = False
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            pending_ws = True
            i += 1
            continue
        if c in "()":
            tokens.append(("PAREN", c))
            ws_before.append(pending_ws)
            pending_ws = False
            i += 1
            continue
        if c == ",":
            tokens.append(("COMMA", ","))
            ws_before.append(pending_ws)
            pending_ws = False
            i += 1
            continue
        if c in "+-*/^=<>":
            # 合并双字符运算符 >= <= != ==
            if c in "<>=" and i + 1 < n and s[i + 1] in "=>":
                tokens.append(("OP", c + s[i + 1]))
                ws_before.append(pending_ws)
                pending_ws = False
                i += 2
                continue
            tokens.append(("OP", c))
            ws_before.append(pending_ws)
            pending_ws = False
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append(("NUM", s[i:j]))
            ws_before.append(pending_ws)
            pending_ws = False
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            name = s[i:j]
            k = j
            while k < n and s[k].isspace():
                k += 1
            if k < n and s[k] == "(":
                tokens.append(("FUNC", name))
            else:
                tokens.append(("VAR", name))
            ws_before.append(pending_ws)
            pending_ws = False
            i = j
            continue
        i += 1  # 跳过未知字符（不计为空隙，避免 \sqrt 之类被误判成"隔空白"）
    return tokens, ws_before


# ---------------------------------------------------------------------------
# 语法分析（递归下降）
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def peek_at(self, k: int) -> tuple[str, str]:
        """向前看第 k 个记号（k=0 等价于 peek）。越界返回 (None, None)。

        函数幂记号 `cos^2 A` 需要看两个记号（`^` 与其后的指数）才能确定，
        而 peek() 只能看一个。
        """
        i = self.pos + k
        return self.tokens[i] if i < len(self.tokens) else (None, None)

    def next(self) -> tuple[str, str]:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def parse(self) -> _Node:
        node = self.parse_relation()
        if self.pos != len(self.tokens):
            # 旧实现会把尾巴上的记号静默丢掉。实测后果：`2 ln(x + ...)` 被截断成
            # 常数 `2`（arcsech 假阴性的根因）。现在尾巴一律报错，让上层判断。
            raise ValueError(
                "表达式后面还有未消费的记号："
                + repr(self.tokens[self.pos:self.pos + 4]))
        return node

    def parse_relation(self) -> _Node:
        left = self.parse_expr()
        t = self.peek()
        if t[0] == "OP" and t[1] in ("=", "<", ">", "<=", ">=", "!=", "=="):
            self.next()
            right = self.parse_expr()
            return Relation(t[1], left, right)
        return left

    def parse_expr(self) -> _Node:
        node = self.parse_term()
        while True:
            t = self.peek()
            if t[0] == "OP" and t[1] in ("+", "-"):
                self.next()
                node = BinOp(t[1], node, self.parse_term())
            else:
                break
        return node

    def parse_term(self) -> _Node:
        node = self.parse_factor()
        while True:
            t = self.peek()
            if t[0] == "OP" and t[1] in ("*", "/"):
                self.next()
                node = BinOp(t[1], node, self.parse_factor())
            else:
                break
        return node

    def parse_factor(self) -> _Node:
        # 保留旧名以维持调用链（term -> factor -> unary）；乘方已在 parse_power 中处理
        return self.parse_unary()

    def parse_unary(self) -> _Node:
        """
        一元层：符号的作用域是**乘方**，而不是整个项。

        写法 `-x^2` 在数学上恒等于 -(x^2)，不是 (-x)^2。旧实现把 `-` 绑定到
        parse_unary() 之后再做乘方，于是 `-x^2` 被算成 (-x)^2 = x^2，
        对含负号的任何多项式都是**静默错误**（2026-09-19 审计中发现并修正）。
        连续符号（如 `--x`、`3 - -2`）仍由递归处理。
        """
        t = self.peek()
        if t[0] == "OP" and t[1] in ("+", "-"):
            self.next()
            return UnaryOp(t[1], self.parse_unary())
        return self.parse_juxta()

    def parse_power(self) -> _Node:
        """乘方层：底数是原子，指数允许带一元号（如 `2^-1`），右结合。"""
        node = self.parse_atom()
        t = self.peek()
        if t[0] == "OP" and t[1] == "^":
            self.next()
            node = BinOp("^", node, self.parse_unary())
        return node

    def parse_juxta(self) -> _Node:
        """紧贴隐式乘法层：`2z`、`(a)(b)`、`1/2i` 里的 `2i`。

        比 `*` 和 `/` 结合得更紧，所以 `1/2i` 读作 `1/(2i)`。
        这一层不放 heated debate：约定本身有争议（`1/2x` 怎么写都有人用），
        选这条是因为它让真恒等式判对；反面就是读 `1/2x` 的人会理解错。
        这条约定写在 CHANGELOG 第五轮，允许被推翻。
        """
        node = self.parse_power()
        while True:
            t = self.peek()
            if t[0] == "JUXTA":
                self.next()
                node = BinOp("*", node, self.parse_power())
            elif t[0] == "VAR" and t[1].lower() in _BUILTIN_FUNC_NAMES:
                # 内置函数名紧随其后：`insert_implicit_mul` 因为它是函数名而没插乘号，
                # 于是这里会残留记号。这些写法本应读作连写：
                #   `sin A cos B` -> sin(A)*cos(B)；`2 sin x` -> 2*sin(x)
                # 限定只对内置函数名生效，散文词连写（保护规则）不受影响。
                node = BinOp("*", node, self.parse_power())
            else:
                break
        return node

    def parse_bare_arg(self) -> _Node:
        """并列函数应用的实参：`sin A` 的 `A`、`cos 2A` 的 `2A`。

        实参取**紧贴单项式**：从乘方层起步（所以 `sin A^2` 仍是 sin(A²)），
        再把紧贴（JUXTA）相连的数字/字母因子吸收进来（所以 `cos 2A` = cos(2·A)）。

        为什么**不吸收函数名**：一旦吸收，`sin A cos B` 会变成 sin(A·cos(B))——
        把两个并列的函数应用吞成一个，于是真恒等式 sinA cosB + cosA sinB = sin(A+B)
        会被判错。标准记号里 `sin A cos B` 就是两个函数相乘，不是嵌套。
        """
        node = self.parse_power()
        while self.peek()[0] == "JUXTA":
            nxt = self.peek_at(1)
            if nxt[0] not in ("NUM", "VAR"):
                break
            if nxt[0] == "VAR" and nxt[1].lower() in _BUILTIN_FUNC_NAMES:
                break
            self.next()                      # 消费 JUXTA
            node = BinOp("*", node, self.parse_power())
        return node

    def parse_atom(self) -> _Node:
        t = self.next()
        if t[0] == "PAREN" and t[1] == "(":
            node = self.parse_relation()
            self.next()  # 消费 ')'
            return node
        if t[0] == "NUM":
            return Num(t[1])
        if t[0] == "VAR":
            # 标准记号的**并列函数应用**：`sin A` 读作 sin(A)，而不是乘积 sin·A。
            # 仅对内置函数名生效；普通多字母词相邻（如 "not true"、"factorial n"）
            # 仍不插入乘号——那是刻意设计，用来避免把英文散文误判成乘积，不可放开。
            if t[1].lower() in _BUILTIN_FUNC_NAMES:
                nxt = self.peek()
                # ① 函数幂记号：`cos^2 A` → (cos A)^2（2026-09-21 新增）
                #    标准记号里 `cos²A` 读作 (cos A)²，而不是 cos²·A。
                #    只认**数字**指数：`cos^2` 是记号，`cos^n` 不是。
                if nxt[0] == "OP" and nxt[1] == "^" and self.peek_at(1)[0] == "NUM":
                    self.next()                                   # 消费 ^
                    expo = Num(self.next()[1])                    # 消费指数
                    # `insert_implicit_mul` 会在**指数**与实参之间补一个乘号
                    # （`cos^2 A` → cos^2*A、`cos^2(A)` → cos^2*(A)），因为它只看
                    # 相邻两格、不知道前面是函数幂记号。这里必须吃掉它，否则整式被读成
                    # (cos^2)·A —— 又变回"函数名被当变量"，二倍角恒等式仍判不出来。
                    if self.peek()[0] in ("OP", "JUXTA") and self.peek()[1] == "*":
                        self.next()
                    return BinOp("^", FuncCall(t[1], [self.parse_bare_arg()]), expo)
                # ② 并列函数应用：`sin A cos B`、`cos 2A`
                if nxt[0] in ("NUM", "VAR", "FUNC"):
                    return FuncCall(t[1], [self.parse_bare_arg()])
            return Var(t[1])
        if t[0] == "FUNC":
            self.next()  # 消费 '('
            args: list[_Node] = []
            if not (self.peek()[0] == "PAREN" and self.peek()[1] == ")"):
                args.append(self.parse_relation())
                while self.peek()[0] == "COMMA":
                    self.next()
                    args.append(self.parse_relation())
            self.next()  # 消费 ')'
            return FuncCall(t[1], args)
        raise ValueError(f"unexpected token {t}")


# ---------------------------------------------------------------------------
# 函数求值
# ---------------------------------------------------------------------------
def _call_func(name: str, args: list[float]) -> float:
    """求值内置函数。**复数感知**：任一参数为 complex 时改用 cmath，
    否则继续用 math。这使得 exp(i*x) 之类的欧拉公式可被求值。"""
    name = name.lower()
    # 复数感知：只要任一参数是复数，就用 cmath 分派
    cx = any(isinstance(a, complex) for a in args)
    m = cmath if cx else math
    if name in ("plus",):
        return args[0] + args[1]
    if name in ("minus",):
        return args[0] - args[1]
    if name in ("times",):
        return args[0] * args[1]
    if name in ("divide",):
        return args[0] / args[1]
    if name in ("power",):
        return args[0] ** args[1]
    if name == "abs":
        return abs(args[0])
    if name == "sqrt":
        # 负实数的 sqrt 在复数域有定义（sqrt(-x)=sqrt(x)i），回退到 cmath 而非报错
        if not cx and args[0] < 0:
            return cmath.sqrt(args[0])
        return m.sqrt(args[0])
    if name == "exp":
        return m.exp(args[0])
    if name in ("ln", "log"):
        # 负实数的对数在复数域有定义（ln(-x) = ln x + i*pi），回退到 cmath 而非报错。
        # 旧实现直接抛 math domain error，使 `arccoth(z) = (ln(-1-z)-ln(1-z))/2`
        # 这类在 |z|>1 上完全成立的恒等式被判成"不可求值"（2026-09-19 审计修正）。
        if not cx and any(a < 0 for a in args):
            m = cmath
        if len(args) == 1:
            return m.log(args[0])
        return m.log(args[0]) / m.log(args[1])  # log(base, x)
    if name == "sin":
        return m.sin(args[0])
    if name == "cos":
        return m.cos(args[0])
    if name == "tan":
        return m.tan(args[0])

    # ---- 扩展：三角/双曲及其反函数（OpenMath transc1 大量使用） ----
    # _f：优先实数域 math；定义域溢出时回退到 cmath（复数扩展），从而可以处理
    # 反三角在 |x|>1 时应取复值的情形。sec/csc/cot 等无原生实现的用标准倒数定义。
    def _f(fn_name, *a):
        if cx:
            return getattr(cmath, fn_name)(*a)
        try:
            return getattr(math, fn_name)(*a)
        except (ValueError, OverflowError):
            return getattr(cmath, fn_name)(*a)

    if name in ("arcsin", "asin"):
        return _f("asin", args[0])
    if name in ("arccos", "acos"):
        return _f("acos", args[0])
    if name in ("arctan", "atan"):
        return _f("atan", args[0])
    if name in ("arcsec", "asec"):        # arcsec x = arccos(1/x)
        return _f("acos", 1 / args[0])
    if name in ("arccsc", "acsc"):        # arccsc x = arcsin(1/x)
        return _f("asin", 1 / args[0])
    if name in ("arccot", "acot"):        # arccot x = arctan(1/x)
        return _f("atan", 1 / args[0])
    if name == "sec":                     # sec x = 1/cos x
        return 1 / _f("cos", args[0])
    if name == "csc":                     # csc x = 1/sin x
        return 1 / _f("sin", args[0])
    if name == "cot":                     # cot x = 1/tan x
        return 1 / _f("tan", args[0])
    if name == "sinh":
        return _f("sinh", args[0])
    if name == "cosh":
        return _f("cosh", args[0])
    if name == "tanh":
        return _f("tanh", args[0])
    if name == "sech":
        return 1 / _f("cosh", args[0])
    if name == "csch":
        return 1 / _f("sinh", args[0])
    if name == "coth":
        return 1 / _f("tanh", args[0])
    if name in ("arcsinh", "asinh"):
        return _f("asinh", args[0])
    if name in ("arccosh", "acosh"):
        return _f("acosh", args[0])
    if name in ("arctanh", "atanh"):
        return _f("atanh", args[0])
    if name in ("arcsech", "asech"):      # arcsech x = arccosh(1/x)
        return _f("acosh", 1 / args[0])
    if name in ("arccsch", "acsch"):      # arccsch x = arcsinh(1/x)
        return _f("asinh", 1 / args[0])
    if name in ("arccoth", "acoth"):      # arccoth x = arctanh(1/x)
        return _f("atanh", 1 / args[0])

    if name == "gcd":
        # 逐次取 gcd，支持 n 元；自变量经 int(round()) 取整（gcd 只在整数上有定义）
        g = 0
        for x in args:
            g = math.gcd(g, int(round(x)))
        return float(g)
    if name == "lcm":
        # lcm 同样支持 n 元：lcm(a,b,c) = lcm(lcm(a,b),c)
        v = 1
        for x in args:
            xi = int(round(x))
            v = v * xi // math.gcd(v, xi) if (v and xi) else 0
        return float(v)
    # max/min：numeric.KNOWN_FUNC_NAMES 早就声明了这两个名字，但求值器没有实现，
    # 于是调用时抛 unknown function，整条式子退化成 unevaluable。
    # 声明与实现不一致是比"不支持"更糟的状态——筛查层以为支持、执行层才炸。
    if name in ("max", "min"):
        if not args:
            raise ValueError(f"{name} requires at least one argument")
        return float(max(args) if name == "max" else min(args))
    if name == "mod":
        if args[1] == 0:
            raise ValueError("mod by zero")
        return float(int(round(args[0])) % int(round(args[1])))
    if name == "floor":
        return float(math.floor(args[0]))
    if name == "ceil":
        return float(math.ceil(args[0]))
    raise ValueError(f"unknown function {name}")


def evaluate(node: _Node, env: dict | None = None) -> Any:
    env = env or {}
    if isinstance(node, Num):
        return node.v
    if isinstance(node, Var):
        if node.name in env:
            return env[node.name]
        raise ValueError(f"unbound variable {node.name}")
    if isinstance(node, UnaryOp):
        v = evaluate(node.operand, env)
        return -v if node.op == "-" else v
    if isinstance(node, BinOp):
        l, r = evaluate(node.left, env), evaluate(node.right, env)
        if node.op == "+":
            return l + r
        if node.op == "-":
            return l - r
        if node.op == "*":
            return l * r
        if node.op == "/":
            return l / r
        if node.op == "^":
            return l ** r
    if isinstance(node, FuncCall):
        return _call_func(node.name, [evaluate(a, env) for a in node.args])
    if isinstance(node, Relation):
        l, r = evaluate(node.left, env), evaluate(node.right, env)
        if node.op in ("=", "=="):
            return l == r
        if node.op == "<":
            return l < r
        if node.op == ">":
            return l > r
        if node.op == "<=":
            return l <= r
        if node.op == ">=":
            return l >= r
        if node.op == "!=":
            return l != r
    raise ValueError("cannot evaluate node")


# ---------------------------------------------------------------------------
# 结构分析
# ---------------------------------------------------------------------------
def _walk(node: _Node):
    yield node
    for child in getattr(node, "left", None), getattr(node, "right", None), getattr(node, "operand", None):
        if isinstance(child, _Node):
            yield from _walk(child)
    for a in getattr(node, "args", []) or []:
        if isinstance(a, _Node):
            yield from _walk(a)


def degree_of(node: _Node, var: str) -> float:
    if isinstance(node, Num):
        return 0
    if isinstance(node, Var):
        return 1 if node.name == var else 0
    if isinstance(node, UnaryOp):
        return degree_of(node.operand, var)
    if isinstance(node, BinOp):
        if node.op in ("+", "-"):
            return max(degree_of(node.left, var), degree_of(node.right, var))
        if node.op == "*":
            return degree_of(node.left, var) + degree_of(node.right, var)
        if node.op == "/":
            return degree_of(node.left, var) - degree_of(node.right, var)
        if node.op == "^":
            if isinstance(node.left, Var) and node.left.name == var and isinstance(node.right, Num):
                return int(node.right.v)
            if isinstance(node.left, Num) and isinstance(node.right, Num):
                return 0
            return degree_of(node.left, var) * (node.right.v if isinstance(node.right, Num) else 1)
    if isinstance(node, FuncCall):
        return float("inf")  # 超越函数
    return 0


def classify(node: _Node, variables: list[str]) -> str:
    if not variables:
        return "constant"
    # 对方程，以 lhs - rhs 作为形态判定对象（多项式标准形式）
    target = node
    if isinstance(node, Relation) and node.op == "=":
        target = BinOp("-", node.left, node.right)
    if any(degree_of(target, v) == float("inf") for v in variables):
        return "transcendental"
    # 取各变量最大次数中的最大值（单一变量场景即该变量次数）
    deg = max((degree_of(target, v) for v in variables), default=0)
    if deg == 1:
        return "linear"
    if deg == 2:
        return "quadratic"
    if deg > 2:
        return f"polynomial(deg={int(deg)})"
    return "other"


# ---------------------------------------------------------------------------
# 多项式系数提取（用于求解）
# ---------------------------------------------------------------------------
def _add_poly(a: dict, b: dict) -> dict:
    out: dict = {}
    for k in set(a) | set(b):
        av, bv = a.get(k, 0), b.get(k, 0)
        if isinstance(av, tuple) or isinstance(bv, tuple):
            out[k] = av if isinstance(av, tuple) else bv
        else:
            out[k] = av + bv
    return {k: v for k, v in out.items() if v != 0}


def _mul_poly(a: dict, b: dict) -> dict:
    out: dict = {}
    for d1, c1 in a.items():
        for d2, c2 in b.items():
            d = d1 + d2
            c = c1 * c2
            if d in out:
                out[d] = (out[d][0], out[d][1]) if isinstance(out[d], tuple) else out[d] + c
            else:
                out[d] = c
    return {k: v for k, v in out.items() if v != 0}


def poly_coeffs(node: _Node, var: str) -> dict:
    """把节点按变量 var 提取为 {次数: 系数} 字典；系数为 ('param', name) 表示含其它参数。"""
    if isinstance(node, Num):
        return {0: node.v}
    if isinstance(node, Var):
        if node.name == var:
            return {1: 1.0}
        return {0: ("param", node.name)}
    if isinstance(node, UnaryOp):
        d = poly_coeffs(node.operand, var)
        return {k: (-v if node.op == "-" else v) for k, v in d.items()}
    if isinstance(node, BinOp):
        if node.op == "+":
            return _add_poly(poly_coeffs(node.left, var), poly_coeffs(node.right, var))
        if node.op == "-":
            return _add_poly(poly_coeffs(node.left, var),
                             {k: -v for k, v in poly_coeffs(node.right, var).items()})
        if node.op == "*":
            return _mul_poly(poly_coeffs(node.left, var), poly_coeffs(node.right, var))
        if node.op == "/":
            r = poly_coeffs(node.right, var)
            if set(r.keys()) == {0} and isinstance(r[0], (int, float)):
                c = r[0]
                return {k: v / c for k, v in poly_coeffs(node.left, var).items()}
            raise ValueError("non-constant divisor")
        if node.op == "^":
            if isinstance(node.left, Var) and node.left.name == var and isinstance(node.right, Num):
                return {int(node.right.v): 1.0}
            if isinstance(node.left, Num) and isinstance(node.right, Num):
                return {0: node.left.v ** node.right.v}
            raise ValueError("unsupported power")
    if isinstance(node, FuncCall):
        raise ValueError(f"transcendental function {node.name}")
    if isinstance(node, Relation):
        raise ValueError("relation is not a polynomial")
    raise ValueError("unknown node")


def solve_poly(coeffs: dict, var: str) -> dict:
    """对 coeffs 表示的单变量多项式求解。"""
    if any(isinstance(v, tuple) for v in coeffs.values()):
        return {"solvable": False, "reason": "含未绑定参数，无法数值求解"}
    deg = max(coeffs.keys()) if coeffs else 0
    if deg == 1:
        a = coeffs.get(1, 0.0)
        b = coeffs.get(0, 0.0)
        if a == 0:
            return {"solvable": False, "reason": "退化为常数"}
        return {"solvable": True, "roots": [-b / a]}
    if deg == 2:
        a = coeffs.get(2, 0.0)
        b = coeffs.get(1, 0.0)
        c = coeffs.get(0, 0.0)
        disc = b * b - 4 * a * c
        if disc < 0:
            import cmath
            r1 = (-b + cmath.sqrt(disc)) / (2 * a)
            r2 = (-b - cmath.sqrt(disc)) / (2 * a)
            return {"solvable": True, "roots": [complex(r1), complex(r2)], "complex": True}
        return {"solvable": True, "roots": [(-b + math.sqrt(disc)) / (2 * a),
                                             (-b - math.sqrt(disc)) / (2 * a)]}
    return {"solvable": False, "reason": f"暂不支持 {int(deg)} 次及以上的通用求解"}


# ---------------------------------------------------------------------------
# 对外入口
# ---------------------------------------------------------------------------
# OpenMath 内容字典(CMP)惯用全称量词前缀，形如：
#   "for all a | a + 0 = a"
#   "for all integers a,b | lcm(a,b) = a*b/gcd(a,b)"
# 解析器不含量词语法：'for'/'all' 会被词法扫描当成变量并触发隐式乘法，
# 而 '|' 因不在运算符表内被静默跳过，最终报「表达式后面还有未消费的记号」。
# 故在入口处识别并剥离该前缀，约束变量记入 MathExpr.quantified 以免语义丢失。
_QUANT_PREFIX_RE = re.compile(r"^\s*for\s+all\s+(?P<vars>[^|]*?)\s*\|\s*", re.I)

# 变量声明里常见的类型/修饰词，提取约束变量时剔除
# （注意：不含 a/an 等可作为变量名的单词）
_QUANT_TYPE_WORDS = frozenset({
    "integer", "integers", "real", "reals", "rational", "rationals",
    "complex", "natural", "number", "numbers", "positive", "negative",
    "nonzero", "non-zero", "in", "set", "such", "that",
})


def split_quantifier(raw: str) -> tuple[str, list[str]]:
    """拆分 OpenMath 全称量词前缀，返回 (剩余语句, 约束变量列表)。

    无前缀时原样返回 (raw, [])。启发式处理：仅剥离前缀以便做 L2 计算校验，
    不构造量词语义，不构成证明(L4)。
    """
    m = _QUANT_PREFIX_RE.match(raw)
    if not m:
        return raw, []
    body = raw[m.end():]
    variables: list[str] = []
    for part in m.group("vars").replace(";", ",").split(","):
        for tok in part.split():
            tok = tok.strip("().")
            if not tok or not re.fullmatch(r"[A-Za-z_]\w*", tok):
                continue
            if tok.lower() in _QUANT_TYPE_WORDS:
                continue
            if tok not in variables:
                variables.append(tok)
    return body, variables


# CMP 常以句子标点结尾（"a + 0 = a." / "x^2 = 4,"）。孤立的 '.' 会被词法扫描
# 当成数字记号，进而抛 "could not convert string to float: '.'"；
# 结尾的逗号/分号则会成为未消费记号。这里统一剥掉结尾的句子标点。
# 注意只处理**结尾**，不影响 ".5" 这类合法小数。
_SENTENCE_TAIL_RE = re.compile(r"[\s.,;]+$")


def parse_text(raw: str, context: set | None = None) -> MathExpr:
    raw = raw.strip()
    body, quantified = split_quantifier(raw)
    body = _SENTENCE_TAIL_RE.sub("", body)
    try:
        tokens, ws = scan_tokens(body)
        tokens, ws = split_letter_runs(tokens, ws, context_letters=context)
        tokens = insert_implicit_mul(tokens, ws)
        tree = Parser(tokens).parse()
        variables = sorted({n.name for n in _walk(tree) if isinstance(n, Var)})
        funcs = sorted({n.name.lower() for n in _walk(tree)
                        if isinstance(n, FuncCall)})
        is_eq = isinstance(tree, Relation) and tree.op == "="
        return MathExpr(raw=raw, ast=tree, variables=variables,
                        functions=funcs, is_equation=is_eq, parse_ok=True,
                        quantified=quantified)
    except Exception as e:  # noqa: BLE001
        return MathExpr(raw=raw, parse_ok=False, error=str(e),
                        quantified=quantified)
