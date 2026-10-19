# -*- coding: utf-8 -*-
"""常驻判据：源文 ↔ 机读面 逐枚比对（列表项内容丢失通道）。

由来：第 11 批的一次性普查（`scratch/_t11_parse_audit.py`）发现并归还了一枚丢失，
但「源文与机读同文」这条性质当时没有任何常驻判据守着——lint 只判「是不是 list」，
图谱只从 str 项里抓 ID，两者都看不见「人类读到的一条」与「机器读到的一条」不同文。
本模块把那把尺接进包里，判据、口径与夹具原样搬过来，并按规矩配变异体对照：
三型各一枚夹具必须全部被点名，两张干净面必须 0 枚。

机制（本库自带的 YAML 子集 `openmath/yamlish.py`）：
    l:
      - >-
        甲行
        乙行
      - 单行
      =>  {'l': ['>-']}          —— 折叠体丢掉、第二枚也被吞
    l:
      - 甲行
        乙行
      =>  {'l': ['甲行']}        —— 续行丢掉
于是判据按 YAML 应有语义自己数一遍源文（列表项 = `- ` 开头的行，其后同项的续行拼回同一枚），
再与解析器给的面逐枚比：
  A) 枚数不等 ⇒ COUNT；
  B) 枚数相等但源文归一化串不是解析串的子串 ⇒ TEXT-LOSS；
  C) 解析成 dict 而源文本是散文（`: ` 把标量劈开）⇒ SPLIT。
"""
import io
import os
import re

try:
    from . import yamlish
except ImportError:  # 允许直接当脚本跑
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from openmath import yamlish

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LIST_FIELDS = ("assumptions", "tags", "symbols", "related", "equivalent_forms",
               "implications", "generalizations", "specializations", "contradicts",
               "uses", "sources", "msc", "partial_results", "characters_tested",
               "contributors", "verification", "fact_check", "caveat", "provenance")
_ITEM = re.compile(r"^(\s*)-\s+(.*)$")

# symbols／partial_results 这类字段**本来**就是映射表：dict 的键全在这张名单里才算合法映射。
MAP_KEYS = {"name", "meaning_zh", "type", "constraints", "statement", "direction", "note",
            "value", "year", "author", "result", "system", "method", "engine", "level",
            "passed", "script", "credential", "sources", "contributors", "note_zh", "rank",
            "domains", "label", "code", "status", "levels", "tolerance", "precision_digits",
            "sample_count", "seed", "max_abs_residual", "last_run", "checks", "skipped_points",
            "characters_tested", "tolerance_basis", "tolerance_note", "max_rel_residual",
            "min_scale_seen", "falsified_conventions", "generic_engine_verdict", "teeth",
            "bound_scanned", "violations", "segment_maxima", "cross_check", "symbols",
            "two_channel_disagreements", "fixed_point_undecided", "min_integer_slack",
            "max_A_k", "runner_up_A_k", "float_vs_dps_max_abs_diff", "legendre_windows",
            "implication_step_slack", "runtime_seconds", "ai_assisted", "ai_role", "note:",
            "prize", "resolution", "refutation", "fact_check", "verification"}


def norm(s):
    return re.sub(r"\s+", "", str(s)).strip()


def strip_comment(s):
    """去掉引号外的行尾注释：`- "11N05"   # 素数分布` 的源文项就是 11N05，
    把注释拼进源文会造出假阳（第一轮真造了 34 枚假阳，全在这型上）。"""
    out = []
    q = None
    for i, ch in enumerate(s):
        if q:
            out.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "'\"":
            q = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def source_items(lines, key):
    """按 YAML 应有语义取某个顶层键的列表项（续行拼回同一枚；内联流式序列按逗号枚）。"""
    items = []
    in_key = False
    cur = None
    for ln in lines:
        if not ln.strip() or strip_comment(ln).strip() == "":
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:", ln):
            in_key = (ln.split(":", 1)[0] == key)
            if not in_key:
                continue
            rest = strip_comment(ln.split(":", 1)[1].strip())
            if rest in ("[]", "{}"):
                continue
            if rest.startswith("[") and rest.endswith("]"):
                items.extend(x.strip().strip("'\"") for x in rest[1:-1].split(",") if x.strip())
            elif rest and not rest.startswith(">"):
                items.append(rest)
            continue
        if not in_key:
            continue
        m = _ITEM.match(ln)
        if m:
            if cur is not None:
                items.append(cur)
            cur = strip_comment(m.group(2))
            continue
        if cur is not None:
            cur += " " + strip_comment(ln)
    if cur is not None:
        items.append(cur)
    return [re.sub(r"^['\"]|['\"]$", "", x).strip() for x in items]


def intended_mapping(g):
    if not isinstance(g, dict):
        return False
    return all(k in MAP_KEYS for k in g)


def parsed_items(data, key):
    v = data.get(key)
    if isinstance(v, list):
        return v
    return None


def audit_text(text):
    """返回 [(型, 键, 位置, 说明)]；空表＝这一份源文与机读同文。"""
    lines = text.replace("\r\n", "\n").split("\n")
    faults = []
    try:
        data = yamlish.loads(text)
    except Exception as exc:
        return [("PARSE-ERROR", "-", "-", str(exc)[:80])]
    for key in LIST_FIELDS:
        src = source_items(lines, key)
        got = parsed_items(data, key)
        if not src or got is None:
            continue
        if len(src) != len(got):
            faults.append(("COUNT", key, "%d→%d" % (len(src), len(got)),
                           "丢失源文：%s" % "｜".join(x[:40] for x in src[len(got):])))
            continue
        for i, (s, g) in enumerate(zip(src, got)):
            if isinstance(g, dict):
                if intended_mapping(g):
                    continue
                if norm(s) and norm(s)[:24] not in norm(str(g)):
                    faults.append(("SPLIT", key, "#%d" % (i + 1), s[:60]))
            elif isinstance(g, str):
                if norm(s) and norm(s) not in norm(g):
                    faults.append(("TEXT-LOSS", key, "#%d" % (i + 1),
                                   "解析止于：%s ‖ 源文续到：%s"
                                   % (g[:40], s[len(g):60] if len(s) > len(g) else s[:60])))
    return faults


def walk(root=None):
    root = root or ROOT
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "_镜像"]
        for fn in sorted(filenames):
            if fn.endswith(".yaml") and fn.startswith("OM-"):
                p = os.path.join(dirpath, fn)
                out.append((os.path.relpath(p, root).replace("\\", "/"), p))
    return sorted(out)


def scan(root=None):
    files = walk(root)
    tally = {}
    rows = []
    n_rec = 0
    for rel, path in files:
        fl = audit_text(io.open(path, encoding="utf-8").read())
        if fl:
            n_rec += 1
            for t, key, slot, detail in fl:
                tally[t] = tally.get(t, 0) + 1
                rows.append("%-10s｜%s｜%s｜%s｜%s" % (t, rel, key, slot, detail))
    return dict(scanned=len(files), records=n_rec, tally=tally, rows=rows,
                whitelist=len(MAP_KEYS), fields=len(LIST_FIELDS))


FIXTURES = [
    ("COUNT／TEXT-LOSS（列表项续行）",
     u"assumptions:\n  - 甲行\n    乙行续文不许丢\n  - 丙行\n", "COUNT"),
    ("COUNT（列表项 >- 吞后项）",
     u"assumptions:\n  - >-\n    甲\n    乙\n  - 单行\n", "COUNT"),
    ("SPLIT（散文里的 : 被劈成 dict）",
     u"assumptions:\n  - 记号 g_k := p_{k+1} - p_k 的定义\n", "SPLIT"),
]
CLEAN_FACES = [
    ("正对照（全单行的干净面）", u"assumptions:\n  - \"甲：单行\"\n  - \"乙：单行\"\n"),
    ("正对照（引号后带行尾注释）", u"msc:\n  - \"11N05\"   # 素数分布\n  - \"11A41\"   # 素数\n"),
]


def selftest(printer=None):
    """变异体对照：三型各一枚必须被点名，两张干净面必须 0 枚。返回 (rc, 判决行)。"""
    say = printer or (lambda s: None)
    ok = True
    for name, txt, want in FIXTURES:
        types = sorted(set(t for t, _k, _s, _d in audit_text(txt)))
        hit = want in types
        ok = ok and hit
        say("%s｜夹具 %s｜期望点名 %s｜实得 %s｜%s"
            % ("RED" if hit else "INVALID", name, want, types or "无判决",
               "被点名" if hit else "漏网（探针坏了）"))
    for name, txt in CLEAN_FACES:
        fl = audit_text(txt)
        ok = ok and not fl
        say("%s｜夹具 %s｜期望 0 枚｜实得 %d 枚｜%s"
            % ("GREEN" if not fl else "INVALID", name, len(fl),
               "对" if not fl else "过紧（假阳）"))
    return (0 if ok else 1), ok


def report(out=None):
    lines = []
    r = scan()
    lines.append("=== 源文 ↔ 机读面 逐枚比对（常驻判据）===")
    lines.append("口径：只比**顶层键**的列表项；比对键 %d 枚，白名单 %d 枚键，内联 []／{} 不算枚。"
                 % (r["fields"], r["whitelist"]))
    lines.append("被扫记录份数：%d（只扫 OM-*.yaml，跳过 _镜像 与点目录）" % r["scanned"])
    lines.append("有丢失的记录：%d 份／被扫 %d 份" % (r["records"], r["scanned"]))
    lines.append("分型合计：%s" % ("／".join("%s=%d" % kv for kv in sorted(r["tally"].items())) or "无"))
    for row in r["rows"][:40]:
        lines.append(row)
    if len(r["rows"]) > 40:
        lines.append("…其余 %d 条从略（总数已在上行现印）" % (len(r["rows"]) - 40))
    rc_st, ok_st = selftest(lines.append)
    lines.append("自检（三型夹具必须响、两张干净面必须 0 枚）：%s（rc=%d）" % ("PASS" if ok_st else "FAIL", rc_st))
    lines.append("判决：rc=%d（有丢失的记录 %d 份）" % (1 if r["records"] else 0, r["records"]))
    text = "\n".join(lines)
    if out is not None:
        out.write((text + "\n").encode("utf-8"))
    return r["records"] and 1 or 0, text
