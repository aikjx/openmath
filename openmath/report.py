"""看板与统计（05-验证中心/05-看板）。

设计原则：暴露问题，不粉饰成绩。
SKIP 率、被证伪条目数、待核查项**必须**显示。
"""

import time


def stats(records, load_errors=None):
    load_errors = load_errors or []
    by_kind = {}
    by_level = {}
    by_status = {}
    by_domain = {}
    unverified = []
    for rec in records:
        data = rec["data"]
        identifier = rec.get("id") or rec["rel"]
        by_kind[data.get("kind") or "?"] = by_kind.get(data.get("kind") or "?", 0) + 1
        by_level[data.get("evidence_level") or "?"] = (
            by_level.get(data.get("evidence_level") or "?", 0) + 1
        )
        by_status[data.get("status") or "?"] = by_status.get(data.get("status") or "?", 0) + 1
        by_domain[data.get("domain") or "?"] = by_domain.get(data.get("domain") or "?", 0) + 1
        fact_check = (data.get("fact_check") or {}).get("status")
        if fact_check == "UNVERIFIED":
            unverified.append(identifier)
    return {
        "schema_version": "0.1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "records": len(records),
        "load_errors": len(load_errors),
        "by_kind": dict(sorted(by_kind.items())),
        "by_level": dict(sorted(by_level.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_domain": dict(sorted(by_domain.items())),
        "unverified_facts": sorted(unverified),
        "l4_count": by_level.get("L4", 0),
        "note": (
            "L4 及以上为 0 表示本库目前没有任何条目可被称为『已证明』。"
            "这是诚实披露，不是缺陷。"
        ),
    }


def render_text(stats_obj):
    lines = []
    lines.append("OpenMath 验证看板  %s" % stats_obj["generated"][:10])
    lines.append("-" * 60)
    lines.append("条目总数        %d" % stats_obj["records"])
    if stats_obj["load_errors"]:
        lines.append("加载失败        %d  ⚠️" % stats_obj["load_errors"])
    lines.append("类型分布        %s" % _fmt(stats_obj["by_kind"]))
    lines.append("证据等级分布    %s" % _fmt(stats_obj["by_level"]))
    lines.append("状态分布        %s" % _fmt(stats_obj["by_status"]))
    lines.append("-" * 60)
    lines.append("已形式化(L4+)   %d" % stats_obj["l4_count"])
    lines.append("待核查声明      %d" % len(stats_obj["unverified_facts"]))
    for item in stats_obj["unverified_facts"]:
        lines.append("                 - %s" % item)
    lines.append("-" * 60)
    lines.append(stats_obj["note"])
    return "\n".join(lines)


def _fmt(mapping):
    if not mapping:
        return "（空）"
    return "  ".join("%s:%d" % (k, v) for k, v in mapping.items())
