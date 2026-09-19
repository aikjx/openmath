"""方程解析器：自包含的数学表达式词法/语法分析与求值。

支持：整数/浮点、变量、+ - * / ^、一元负号、括号、函数调用、
以及 '=' 关系（方程）。不依赖任何第三方库。
"""
from __future__ import annotations

import math
import cmath
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
# 词法分析
# ---------------------------------------------------------------------------
def tokenize(s: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            tokens.append(("PAREN", c))
            i += 1
            continue
        if c == ",":
            tokens.append(("COMMA", ","))
            i += 1
            continue
        if c in "+-*/^=<>":
            # 合并双字符运算符 >= <= != ==
            if c in "<>=" and i + 1 < n and s[i + 1] in "=>":
                tokens.append(("OP", c + s[i + 1]))
                i += 2
                continue
            tokens.append(("OP", c))
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            tokens.append(("NUM", s[i:j]))
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
            i = j
            continue
        i += 1  # 跳过未知字符
    return tokens


# ---------------------------------------------------------------------------
# 语法分析（递归下降）
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def next(self) -> tuple[str, str]:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def parse(self) -> _Node:
        return self.parse_relation()

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
        return self.parse_power()

    def parse_power(self) -> _Node:
        """乘方层：底数是原子，指数允许带一元号（如 `2^-1`），右结合。"""
        node = self.parse_atom()
        t = self.peek()
        if t[0] == "OP" and t[1] == "^":
            self.next()
            node = BinOp("^", node, self.parse_unary())
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
        return float(math.gcd(int(round(args[0])), int(round(args[1]))))
    if name == "lcm":
        a, b = int(round(args[0])), int(round(args[1]))
        return float(a * b // math.gcd(a, b)) if a and b else 0.0
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
def parse_text(raw: str) -> MathExpr:
    raw = raw.strip()
    try:
        tokens = tokenize(raw)
        tree = Parser(tokens).parse()
        variables = sorted({n.name for n in _walk(tree) if isinstance(n, Var)})
        is_eq = isinstance(tree, Relation) and tree.op == "="
        return MathExpr(raw=raw, ast=tree, variables=variables,
                        is_equation=is_eq, parse_ok=True)
    except Exception as e:  # noqa: BLE001
        return MathExpr(raw=raw, parse_ok=False, error=str(e))
