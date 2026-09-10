"""标识与编号：解析、校验、分配。

ID 格式（见 00-宪章/04-标识与编号规范.md）：
    OM-<类型>-<域代码>-<4位序号>      例：OM-F-NT-0001
    OM-SYS-<4位序号>                  例：OM-SYS-0007（统一纲领，无域代码）
"""

import re

KINDS = {
    "D": "definition",
    "F": "formula",
    "T": "theorem",
    "C": "conjecture",
    "X": "counterexample",
    "A": "algorithm",
    "P": "problem",
}

DOMAINS = {
    "FD": "数学基础与逻辑",
    "ST": "集合论",
    "CT": "范畴论",
    "AL": "代数",
    "GR": "群论与表示论",
    "NT": "数论",
    "TG": "几何与拓扑",
    "AN": "分析",
    "PR": "概率论",
    "SC": "统计与数据科学",
    "CB": "组合数学",
    "GT": "图论",
    "NA": "数值分析",
    "IT": "信息论与编码",
    "DS": "动力系统与混沌",
    "MP": "数学物理",
    "GO": "博弈论与优化",
    "OR": "运筹与系统科学",
    "TC": "理论计算机科学",
    "XS": "交叉与新兴",
}

_PATTERN = re.compile(r"^OM-(?P<kind>[A-Z]{1,3})-(?:(?P<domain>[A-Z]{2})-)?(?P<seq>\d{4})$")


class IdError(ValueError):
    """ID 非法。"""


def parse(identifier):
    """解析 ID，返回 dict(kind, domain, seq)。非法则抛 IdError。"""
    if not isinstance(identifier, str):
        raise IdError("ID 必须是字符串，收到: %r" % (identifier,))
    match = _PATTERN.match(identifier.strip())
    if not match:
        raise IdError(
            "ID 格式非法: %r，应为 OM-<类型>-<域代码>-<4位序号> 或 OM-SYS-<4位序号>" % identifier
        )
    kind = match.group("kind")
    domain = match.group("domain")
    if kind == "SYS":
        if domain is not None:
            raise IdError("OM-SYS 不带域代码: %r" % identifier)
        return {"kind": kind, "domain": None, "seq": int(match.group("seq"))}
    if kind not in KINDS:
        raise IdError("未知类型码: %r（允许: %s, SYS）" % (kind, ", ".join(sorted(KINDS))))
    if domain is None:
        raise IdError("缺少域代码: %r" % identifier)
    if domain not in DOMAINS:
        raise IdError("未知域代码: %r（见 00-宪章/04-标识与编号规范.md）" % domain)
    return {"kind": kind, "domain": domain, "seq": int(match.group("seq"))}


def is_valid(identifier):
    try:
        parse(identifier)
        return True
    except IdError:
        return False


def kind_name(kind):
    if kind == "SYS":
        return "programme"
    return KINDS.get(kind, "unknown")


def make(kind, domain, seq):
    """按规范生成 ID 字符串。"""
    if kind == "SYS":
        return "OM-SYS-%04d" % int(seq)
    if kind not in KINDS:
        raise IdError("未知类型码: %r" % kind)
    if domain not in DOMAINS:
        raise IdError("未知域代码: %r" % domain)
    return "OM-%s-%s-%04d" % (kind, domain, int(seq))


def next_id(kind, domain, existing):
    """在已有 ID 集合中分配下一个可用序号（序号永不回收）。"""
    if kind == "SYS":
        prefix = "OM-SYS-"
        used = [i for i in existing if isinstance(i, str) and i.startswith(prefix)]
        seqs = []
        for item in used:
            try:
                seqs.append(parse(item)["seq"])
            except IdError:
                continue
        return make("SYS", None, (max(seqs) + 1) if seqs else 1)
    if domain not in DOMAINS:
        raise IdError("未知域代码: %r" % domain)
    prefix = "OM-%s-%s-" % (kind, domain)
    seqs = []
    for item in existing:
        if not isinstance(item, str) or not item.startswith(prefix):
            continue
        try:
            seqs.append(parse(item)["seq"])
        except IdError:
            continue
    return make(kind, domain, (max(seqs) + 1) if seqs else 1)
