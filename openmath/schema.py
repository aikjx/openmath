"""L0 结构校验（schema lint）。

规则清单见 02-公式库/schema/记录schema.md 第七节。
本模块只做**结构**校验，不涉及数学正确性。
"""

import os
import re

from . import ids

REQUIRED_FIELDS = [
    "schema_version",
    "id",
    "kind",
    "title_zh",
    "title_en",
    "domain",
    "status",
    "evidence_level",
    "assumptions",
    "provenance",
    "revision",
    "created",
    "updated",
]

VALID_KINDS = set(ids.KINDS.values()) | {"programme"}

VALID_STATUS = {
    "DRAFT",
    "PROPOSED",
    "UNDER_REVIEW",
    "CONSENSUS",
    "CANONICAL",
    "CONDITIONAL",
    "DISPUTED",
    "FALSIFIED",
    "DEPRECATED",
    "OPEN",
    "PARTIAL",
    "RESOLVED",
    "RESOLVED_CA",
    "REFUTED",
    "UNDECIDABLE",
    "UNCOMPUTABLE",
    "ILL_POSED",
}

VALID_LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5", "L6"}

_VERIFIED_RE = re.compile(r"^VERIFIED\((L[0-6])\)$")

_PLACEHOLDER_RE = re.compile(r"^<.*>$")


class Issue(object):
    def __init__(self, level, target, message):
        self.level = level  # error | warning
        self.target = target
        self.message = message

    def __str__(self):
        return "[%s] %s: %s" % (self.level, self.target, self.message)

    def as_dict(self):
        return {"level": self.level, "target": self.target, "message": self.message}


def _check_required(record, issues):
    data = record["data"]
    for field in REQUIRED_FIELDS:
        if field not in data:
            issues.append(Issue("error", record["rel"], "缺少必填字段: %s" % field))


def _check_id(record, issues, all_ids):
    from . import record as record_mod  # 局部导入避免循环

    for problem in record_mod.validate_id(record):
        issues.append(Issue("error", record["rel"], problem.split(": ", 1)[-1]))
    identifier = record.get("id")
    if isinstance(identifier, str):
        # 重复 ID 需要全局信息，这里只标记，由调用方汇总
        if isinstance(all_ids, dict) and all_ids.get(identifier, 0) > 1:
            issues.append(Issue("error", record["rel"], "ID 重复: %s" % identifier))


def _check_enums(record, issues):
    data = record["data"]
    kind = data.get("kind")
    if kind is not None and kind not in VALID_KINDS:
        issues.append(Issue("error", record["rel"], "非法 kind: %r" % kind))
    domain = data.get("domain")
    if domain is not None and domain not in ids.DOMAINS and domain != "SYS":
        issues.append(Issue("error", record["rel"], "非法 domain: %r" % domain))
    level = data.get("evidence_level")
    if level is not None and level not in VALID_LEVELS:
        issues.append(Issue("error", record["rel"], "非法 evidence_level: %r" % level))
    status = data.get("status")
    if status is not None:
        if status.startswith("VERIFIED"):
            match = _VERIFIED_RE.match(status)
            if not match:
                issues.append(
                    Issue("error", record["rel"], "VERIFIED 必须写成 VERIFIED(Lx) 形式: %r" % status)
                )
            elif level is not None and match.group(1) != level:
                issues.append(
                    Issue(
                        "error",
                        record["rel"],
                        "status 中的等级 %s 与 evidence_level %s 不一致" % (match.group(1), level),
                    )
                )
        elif status not in VALID_STATUS:
            issues.append(Issue("error", record["rel"], "非法 status: %r" % status))


def _check_assumptions(record, issues):
    data = record["data"]
    if "assumptions" not in data:
        return
    value = data["assumptions"]
    if value is not None and not isinstance(value, list):
        issues.append(Issue("error", record["rel"], "assumptions 必须是列表（无假设请写 []）"))


def _check_provenance(record, issues):
    data = record["data"]
    prov = data.get("provenance")
    if not isinstance(prov, dict):
        return
    if prov.get("ai_assisted") is True:
        role = prov.get("ai_role")
        if not role:
            issues.append(
                Issue("error", record["rel"], "ai_assisted 为 true 时必须填写 ai_role")
            )
        level = data.get("evidence_level")
        verification = data.get("verification") or {}
        levels = verification.get("levels") or {}
        human_reviewed = False
        if isinstance(levels, dict):
            l4 = levels.get("L4")
            if isinstance(l4, dict):
                human_reviewed = bool(l4.get("human_reviewed"))
        if level in ("L4", "L5", "L6") and not human_reviewed:
            issues.append(
                Issue(
                    "error",
                    record["rel"],
                    "AI 生成内容不得达到 %s，除非 verification.levels.L4.human_reviewed 为 true" % level,
                )
            )


def _check_scripts(record, issues, root):
    data = record["data"]
    verification = data.get("verification") or {}
    levels = verification.get("levels") or {}
    if not isinstance(levels, dict):
        return
    for key in sorted(levels):
        entry = levels.get(key)
        if not isinstance(entry, dict):
            continue
        script = entry.get("script")
        if not script:
            continue
        if not isinstance(script, str):
            issues.append(Issue("error", record["rel"], "%s.script 必须是路径字符串" % key))
            continue
        if script.startswith("/") or ".." in script.split("/"):
            issues.append(Issue("error", record["rel"], "%s.script 路径不合法: %s" % (key, script)))
            continue
        if not os.path.exists(os.path.join(root, script.replace("/", os.sep))):
            issues.append(
                Issue("error", record["rel"], "%s.script 指向的文件不存在: %s" % (key, script))
            )


def _check_placeholders(record, issues):
    """检测未替换的模板占位符（形如 <...>）。"""
    data = record["data"]
    for field in ("title_zh", "title_en", "id", "domain"):
        value = data.get(field)
        if isinstance(value, str) and _PLACEHOLDER_RE.match(value.strip()):
            issues.append(Issue("error", record["rel"], "存在未替换的模板占位符: %s" % field))
    for key in ("title_zh", "title_en"):
        value = data.get(key)
        if isinstance(value, str) and not value.strip():
            issues.append(Issue("error", record["rel"], "%s 不能为空" % key))


def lint_record(record, root, all_ids=None):
    """校验单条记录，返回 Issue 列表。"""
    issues = []
    _check_required(record, issues)
    _check_id(record, issues, all_ids)
    _check_enums(record, issues)
    _check_assumptions(record, issues)
    _check_provenance(record, issues)
    _check_scripts(record, issues, root)
    _check_placeholders(record, issues)
    return issues


def lint_all(records, load_errors, root):
    """校验全部记录。返回 (issues, stats)。"""
    issues = []
    counts = {}
    for rec in records:
        identifier = rec.get("id")
        if isinstance(identifier, str):
            counts[identifier] = counts.get(identifier, 0) + 1
    for rec in records:
        issues.extend(lint_record(rec, root, counts))
    for err in load_errors:
        issues.append(Issue("error", err["rel"], err["error"]))
    errors = [i for i in issues if i.level == "error"]
    stats = {
        "records": len(records),
        "load_errors": len(load_errors),
        "errors": len(errors),
        "backend": None,
    }
    from . import record as record_mod

    stats["backend"] = record_mod.backend_name()
    return issues, stats
