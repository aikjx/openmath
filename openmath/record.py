"""记录的加载与发现。

优先使用 PyYAML（若已安装），否则使用内置 yamlish 子集解析器，
保证核心功能在任何环境下都能运行。
"""

import os

from . import ids, yamlish

try:  # 可选依赖
    import yaml as _pyyaml
except Exception:  # pragma: no cover - 环境相关
    _pyyaml = None

BACKEND_PYYAML = "pyyaml"
BACKEND_YAMLISH = "yamlish"

SKIP_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "site",
    ".openmath-cache",
    ".pytest_cache",
}


def backend_name():
    return BACKEND_PYYAML if _pyyaml is not None else BACKEND_YAMLISH


def load_yaml(path):
    """加载单个 YAML 文件，返回 (data, error)。"""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return None, "读取失败: %s" % exc
    if _pyyaml is not None:
        try:
            return _pyyaml.safe_load(text), None
        except Exception as exc:
            return None, "PyYAML 解析失败: %s" % exc
    try:
        return yamlish.loads(text), None
    except yamlish.YamlishError as exc:
        return None, str(exc)


def find_root(start=None):
    """向上查找仓库根（含 00-宪章 目录的那一层）。"""
    current = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(current, "00-宪章")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def iter_record_files(root):
    """遍历全部记录文件（OM-*.yaml）。

    注意：只收集文件名以 OM- 开头且以 .yaml 结尾的文件。
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(filenames):
            if name.startswith("OM-") and name.endswith(".yaml"):
                yield os.path.join(dirpath, name)


def load_all(root=None):
    """加载全部记录。返回 (records, errors)。

    records: list[dict]，每项含 path / rel / data / id
    errors:  list[dict]，每项含 path / rel / error
    """
    root = root or find_root()
    if root is None:
        raise RuntimeError("未找到仓库根（缺少 00-宪章 目录），请在 openmath 仓库内运行。")
    records = []
    errors = []
    for path in iter_record_files(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        data, error = load_yaml(path)
        if error is not None or data is None:
            errors.append({"path": path, "rel": rel, "error": error or "空文件"})
            continue
        if not isinstance(data, dict):
            errors.append({"path": path, "rel": rel, "error": "顶层不是映射"})
            continue
        records.append({"path": path, "rel": rel, "data": data, "id": data.get("id")})
    return records, errors


def collect_ids(records):
    return {r["id"] for r in records if isinstance(r.get("id"), str)}


def by_id(records):
    """返回 id -> record 的映射（重复 ID 只保留首个，重复本身由 lint 报出）。"""
    out = {}
    for rec in records:
        identifier = rec.get("id")
        if isinstance(identifier, str) and identifier not in out:
            out[identifier] = rec
    return out


def validate_id(record):
    """校验单条记录的 ID 与文件名是否一致。返回错误列表。"""
    problems = []
    identifier = record.get("id")
    if not isinstance(identifier, str) or not identifier:
        problems.append("%s: 缺少 id 字段" % record["rel"])
        return problems
    try:
        ids.parse(identifier)
    except ids.IdError as exc:
        problems.append("%s: %s" % (record["rel"], exc))
        return problems
    base = os.path.basename(record["path"])[: -len(".yaml")]
    if not base.startswith(identifier):
        problems.append("%s: 文件名前缀与 id 不一致（期望以 %s 开头）" % (record["rel"], identifier))
    return problems
