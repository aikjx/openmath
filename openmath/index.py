"""交叉引用索引的构建与检索。

索引是**生成物**：请勿手工编辑 02-公式库/索引/ 下的文件。
"""

import json
import os
import time

INDEX_DIR = "02-公式库/索引"


def build(records):
    by_domain = {}
    by_kind = {}
    by_level = {}
    by_status = {}
    by_tag = {}
    references = {}
    for rec in records:
        data = rec["data"]
        identifier = rec.get("id")
        domain = data.get("domain") or "?"
        kind = data.get("kind") or "?"
        level = data.get("evidence_level") or "?"
        status = data.get("status") or "?"
        by_domain.setdefault(domain, []).append(identifier)
        by_kind.setdefault(kind, []).append(identifier)
        by_level.setdefault(level, []).append(identifier)
        by_status.setdefault(status, []).append(identifier)
        for tag in data.get("tags") or []:
            by_tag.setdefault(str(tag), []).append(identifier)
        refs = set()
        for key in ("related", "specializations", "generalizations", "equivalent_forms"):
            value = data.get(key) or []
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.startswith("OM-"):
                        refs.add(item)
        references[identifier] = sorted(refs)

    def _sorted(mapping):
        return {k: sorted(v) for k, v in sorted(mapping.items())}

    return {
        "schema_version": "0.1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(records),
        "by_domain": _sorted(by_domain),
        "by_kind": _sorted(by_kind),
        "by_level": _sorted(by_level),
        "by_status": _sorted(by_status),
        "by_tag": _sorted(by_tag),
        "references": {k: references[k] for k in sorted(references)},
        "dangling": sorted(
            {
                ref
                for refs in references.values()
                for ref in refs
                if ref not in references
            }
        ),
    }


def write(index, root):
    target = os.path.join(root, INDEX_DIR)
    os.makedirs(target, exist_ok=True)
    path = os.path.join(target, "index.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, indent=2, sort_keys=False)
    return os.path.relpath(path, root).replace("\\", "/")


def load(root):
    path = os.path.join(root, INDEX_DIR, "index.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def search(index, keyword=None, domain=None, level=None, kind=None):
    """在已有索引中检索，返回 ID 列表。"""
    if index is None:
        return []
    pool = None
    for key, value in (("by_domain", domain), ("by_level", level), ("by_kind", kind)):
        if value:
            group = index.get(key, {}).get(value, [])
            pool = set(group) if pool is None else (pool & set(group))
    candidates = sorted(pool) if pool is not None else sorted(
        {i for group in index.get("by_domain", {}).values() for i in group}
    )
    if not keyword:
        return candidates
    needle = keyword.lower()
    return [i for i in candidates if needle in str(i).lower()]
