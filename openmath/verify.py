"""L2 数值验证与 L3 符号验证。

设计纪律（见 00-宪章/02-诚实红线.md）：
  * 依赖缺失时返回 SKIP，**绝不**返回 PASS；
  * 输出**残差**而非布尔值；
  * L2/L3 通过**永不**被解释为"证明"；
  * 样本求值失败记为 skipped，不计为通过。
"""

import platform
import random
import sys
import time

try:
    import sympy as sp
except Exception:  # pragma: no cover - 环境相关
    sp = None

DEFAULT_DPS = 50
DEFAULT_TOL = "1e-40"


def backends():
    return {
        "sympy": getattr(sp, "__version__", None) if sp is not None else None,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def _level_config(record, level):
    verification = (record or {}).get("verification") or {}
    levels = verification.get("levels") or {}
    entry = levels.get(level)
    return entry if isinstance(entry, dict) else {}


def _make_samples(symbols, config, count, seed):
    """生成采样点。记录中提供了 sample_points 时优先使用。"""
    provided = config.get("sample_points")
    if isinstance(provided, list) and provided:
        return [p for p in provided if isinstance(p, dict)], "record"
    if not symbols:
        return [{} for _ in range(count)], "none"
    rng = random.Random(seed)
    samples = []
    for _ in range(count):
        point = {}
        for sym in symbols:
            real = rng.uniform(-4.0, 4.0)
            imag = rng.uniform(-4.0, 4.0)
            point[str(sym)] = "(%r)+(%r)*I" % (real, imag)
        samples.append(point)
    return samples, "random"


def _to_complex_or_real(value):
    """把 sympy 数值转为 (abs, ok)。"""
    try:
        num = complex(value)
        if num != num:  # NaN
            return None, False
        if abs(num) == float("inf"):
            return None, False
        return abs(num), True
    except (TypeError, ValueError):
        return None, False


def verify_l2(record, root=None, options=None):
    """L2 高精度数值验证。"""
    options = options or {}
    started = time.time()
    data = record["data"]
    config = _level_config(data, "L2")
    dps = int(options.get("precision_digits") or config.get("precision_digits") or DEFAULT_DPS)
    seed = int(options.get("seed") or config.get("seed") or 20260910)
    count = int(options.get("sample_count") or config.get("sample_count") or 20)
    tol = float(options.get("tolerance") or config.get("tolerance") or DEFAULT_TOL)

    result = {
        "target_id": data.get("id"),
        "level": "L2",
        "status": "SKIP",
        "engine": {"name": "sympy/mpmath", "version": getattr(sp, "__version__", None)},
        "environment": {
            "python": platform.python_version(),
            "platform": sys.platform,
            "precision_digits": dps,
            "seed": seed,
        },
        "metrics": {},
        "samples": [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if sp is None:
        result["notes"] = "未安装 sympy/mpmath，L2 无法执行（安装: pip install sympy）"
        return _finish(result, started)
    expr_src = data.get("sympy")
    if not expr_src:
        result["notes"] = "记录未提供 sympy 表达式，L2 无法执行"
        return _finish(result, started)

    try:
        expr = sp.sympify(expr_src)
    except Exception as exc:
        result["status"] = "ERROR"
        result["notes"] = "sympy 表达式解析失败: %s" % exc
        return _finish(result, started)

    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    samples, origin = _make_samples(symbols, config, count, seed)

    residuals = []
    skipped = []
    worst_sample = None
    for point in samples:
        subs = {}
        ok = True
        for key, raw in point.items():
            try:
                subs[sp.Symbol(key)] = sp.sympify(str(raw)).evalf(dps)
            except Exception as exc:
                skipped.append({"point": point, "reason": "替换失败: %s" % exc})
                ok = False
                break
        if not ok:
            continue
        try:
            value = expr.subs(subs)
            numeric = sp.N(value, dps)
        except Exception as exc:
            skipped.append({"point": point, "reason": "求值失败: %s" % exc})
            continue
        magnitude, valid = _to_complex_or_real(numeric)
        if not valid:
            skipped.append({"point": point, "reason": "结果为 NaN/Inf（可能落在奇点）"})
            continue
        residuals.append(magnitude)
        if worst_sample is None or magnitude > worst_sample["residual"]:
            worst_sample = {"point": point, "residual": magnitude}

    result["metrics"] = {
        "sample_total": len(samples),
        "sample_evaluated": len(residuals),
        "sample_skipped": len(skipped),
        "sampling": origin,
        "tolerance": tol,
        "max_abs_residual": ("%.3e" % max(residuals)) if residuals else "",
        "median_abs_residual": ("%.3e" % _median(residuals)) if residuals else "",
    }
    result["skipped_samples"] = skipped[:10]
    if worst_sample is not None:
        result["samples"] = [
            {"point": worst_sample["point"], "residual": "%.3e" % worst_sample["residual"]}
        ]

    if not residuals:
        result["status"] = "UNKNOWN"
        result["notes"] = "全部采样点均无法求值，无法判定（请检查表达式定义域）"
        return _finish(result, started)

    failed = [r for r in residuals if r > tol]
    if failed:
        result["status"] = "FAIL"
        result["notes"] = (
            "%d/%d 个采样点残差超过容差 %g。这可能意味着条目有误，"
            "也可能是采样点落在奇点附近——需人工判断，不得自动改断言。"
            % (len(failed), len(residuals), tol)
        )
    else:
        result["status"] = "PASS"
        result["notes"] = (
            "在 %d 个采样点、%d 位精度下未发现反例。"
            "注意：L2 通过不构成证明（见 00-宪章/02-诚实红线.md 红线一）。"
            % (len(residuals), dps)
        )
    return _finish(result, started)


def verify_l3(record, root=None, options=None):
    """L3 符号验证。"""
    options = options or {}
    started = time.time()
    data = record["data"]
    config = _level_config(data, "L3")
    dps = int(options.get("precision_digits") or 50)

    result = {
        "target_id": data.get("id"),
        "level": "L3",
        "status": "SKIP",
        "engine": {"name": "sympy", "version": getattr(sp, "__version__", None)},
        "environment": {
            "python": platform.python_version(),
            "platform": sys.platform,
            "precision_digits": dps,
        },
        "metrics": {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if sp is None:
        result["notes"] = "未安装 sympy，L3 无法执行（安装: pip install sympy）"
        return _finish(result, started)
    expr_src = data.get("sympy")
    if not expr_src:
        result["notes"] = "记录未提供 sympy 表达式，L3 无法执行"
        return _finish(result, started)
    try:
        expr = sp.sympify(expr_src)
    except Exception as exc:
        result["status"] = "ERROR"
        result["notes"] = "sympy 表达式解析失败: %s" % exc
        return _finish(result, started)

    simplified = None
    try:
        simplified = sp.simplify(expr)
    except Exception as exc:
        simplified = None
        result["metrics"]["simplify_error"] = str(exc)[:200]

    symbolic_zero = False
    if simplified is not None:
        try:
            symbolic_zero = bool(sp.simplify(simplified) == 0)
        except Exception:
            symbolic_zero = False
    result["metrics"]["symbolic_zero"] = symbolic_zero

    if symbolic_zero:
        result["status"] = "PASS"
        result["metrics"]["method"] = "simplify(expr) == 0"
        result["notes"] = "符号恒等式在 SymPy 规则集下归零。注意：这仍不是形式化证明。"
        return _finish(result, started)

    # 符号化简未归零 → 回退到高精度数值交叉确认
    l2 = verify_l2(record, root, options)
    result["metrics"]["method"] = config.get("method") or "符号化简未归零，改用 L2 数值交叉确认"
    result["metrics"]["max_abs_residual"] = (l2.get("metrics") or {}).get("max_abs_residual", "")
    if l2.get("status") == "PASS":
        result["status"] = "PASS"
        result["notes"] = (
            "SymPy 符号化简未归零（可能超出其能力范围），"
            "已用 %d 位高精度数值交叉确认，最大残差 %s。证据强度以 L2 计，不得升格。"
            % (dps, result["metrics"]["max_abs_residual"])
        )
    else:
        result["status"] = l2.get("status", "UNKNOWN")
        result["notes"] = "符号化简未归零，且数值交叉确认亦未通过：%s" % l2.get("notes", "")
    return _finish(result, started)


def _median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def _finish(result, started):
    result["duration_ms"] = int((time.time() - started) * 1000)
    return result


ENGINES = {"L2": verify_l2, "L3": verify_l3}


def _try_external(record, level, root, options=None):
    """内置引擎不可用时，尝试注册表中的外部引擎（engines.yaml）。"""
    if root is None:
        return None
    from . import engines as engines_mod  # 局部导入避免循环

    config = _level_config(record["data"], level)
    wanted = config.get("engine")
    registry = engines_mod.load_registry(root)
    if not registry:
        return None
    entry = engines_mod.find_engine(
        registry,
        name=wanted,
        level=level,
        domain=record["data"].get("domain"),
    )
    if entry is None:
        return None
    module = engines_mod.load_module(entry, root)
    if module is None:
        return None
    return engines_mod.run(entry, module, record["data"], level, options)


def verify_record(record, level, root=None, options=None):
    engine = ENGINES.get(level)
    result = None
    if engine is not None:
        result = engine(record, root, options)
    if result is None or result.get("status") == "SKIP":
        external = _try_external(record, level, root, options)
        if external is not None:
            return external
    if result is not None:
        return result
    return {
        "target_id": (record or {}).get("id"),
        "level": level,
        "status": "SKIP",
        "notes": "该层级无可用引擎（L0 见 schema.lint，L4+ 见 05-验证中心/07-形式化）",
    }
