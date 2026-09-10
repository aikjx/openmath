"""引擎注册表：插件发现与加载。

引擎可以位于：
  * Python 包内（openmath/engines/<name>.py）
  * 仓库内任意路径（由 engines.yaml 的 path 指定，相对于仓库根）

新增引擎不需要修改本模块，只需在
`05-验证中心/01-引擎/engines.yaml` 中注册一个条目。
"""

import importlib.util
import os
import sys

from . import yamlish

REGISTRY_PATH = "05-验证中心/01-引擎/engines.yaml"

try:
    import yaml as _pyyaml
except Exception:  # pragma: no cover
    _pyyaml = None


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if _pyyaml is not None:
        return _pyyaml.safe_load(text)
    return yamlish.loads(text)


def load_registry(root):
    """返回启用且可用的引擎条目列表。"""
    path = os.path.join(root, REGISTRY_PATH)
    if not os.path.exists(path):
        return []
    data = _load_yaml(path)
    entries = (data or {}).get("engines") or []
    return [e for e in entries if isinstance(e, dict) and e.get("enabled", True)]


def load_module(entry, root):
    """按 path（相对仓库根）或 module 名加载引擎模块。失败返回 None。"""
    path = entry.get("path")
    name = entry.get("name") or "engine"
    if path:
        full = os.path.join(root, path.replace("/", os.sep))
        if not os.path.exists(full):
            return None
        try:
            spec = importlib.util.spec_from_file_location("openmath_ext_" + str(name), full)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None
    module_name = entry.get("module")
    if module_name:
        try:
            return importlib.import_module(module_name)
        except Exception:
            return None
    return None


def find_engine(registry, name=None, level=None, domain=None):
    """按名称（优先）或 层级+域 匹配引擎条目。"""
    if name:
        for entry in registry:
            if entry.get("name") == name:
                return entry
        return None
    for entry in registry:
        levels = entry.get("levels") or []
        domains = entry.get("domains") or []
        if level and levels and level not in levels:
            continue
        if domain and domains and "*" not in domains and domain not in domains:
            continue
        return entry
    return None


def run(entry, module, record, level, options=None):
    """调用引擎的 run()，并保证不向外抛出异常（异常转为 ERROR）。"""
    options = options or {}
    try:
        if hasattr(module, "available") and not module.available():
            return {
                "target_id": (record or {}).get("id"),
                "level": level,
                "status": "SKIP",
                "engine": entry.get("name"),
                "notes": "引擎依赖不满足（available() 返回 False）",
            }
        result = module.run(record, level, options)
        if not isinstance(result, dict):
            return {
                "target_id": (record or {}).get("id"),
                "level": level,
                "status": "ERROR",
                "engine": entry.get("name"),
                "notes": "引擎 run() 未返回 dict",
            }
        result.setdefault("engine", entry.get("name"))
        result.setdefault("level", level)
        result.setdefault("target_id", (record or {}).get("id"))
        # 安全护栏：若引擎声明了 items 但一个都没检查，不得报 PASS
        if result.get("status") == "PASS" and isinstance(result.get("items"), list):
            if not result["items"]:
                result["status"] = "UNKNOWN"
                result["notes"] = (
                    "引擎未执行任何检查项（items 为空），不得计为通过。"
                    "请在记录中提供结构化的 checks，或直接运行引擎自检。"
                )
        return result
    except Exception as exc:  # 引擎不得抛出
        return {
            "target_id": (record or {}).get("id"),
            "level": level,
            "status": "ERROR",
            "engine": entry.get("name"),
            "notes": "引擎异常: %r" % exc,
        }
