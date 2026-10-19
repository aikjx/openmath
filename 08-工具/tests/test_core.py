# -*- coding: utf-8 -*-
"""openmath 核心自检。

运行：
    python -m pytest 08-工具/tests -q
或（无 pytest 时）：
    python 08-工具/tests/test_core.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openmath import fidelity, ids, index as index_mod, record as record_mod, report, schema, yamlish  # noqa: E402


def test_id_parse_and_make():
    parsed = ids.parse("OM-F-NT-0001")
    assert parsed["kind"] == "F"
    assert parsed["domain"] == "NT"
    assert parsed["seq"] == 1
    assert ids.is_valid("OM-SYS-0007")
    assert not ids.is_valid("OM-F-NT-1")
    assert not ids.is_valid("OM-ZZ-0001")


def test_id_next_never_reuses():
    existing = {"OM-F-NT-0001", "OM-F-NT-0007"}
    assert ids.next_id("F", "NT", existing) == "OM-F-NT-0008"


def test_yamlish_roundtrip_basics():
    text = (
        "# 注释\n"
        "id: OM-F-AN-0001\n"
        "title_zh: \"欧拉恒等式\"\n"
        "status: VERIFIED(L3)\n"
        "assumptions:\n"
        "  - a: 1\n"
        "    b: 2\n"
        "symbols:\n"
        "  - name: \"s\"\n"
        "    type: complex\n"
        "notes: >-\n"
        "  折叠\n"
        "  文本\n"
        "list_inline: [1, 2, 3]\n"
        "flag: true\n"
        "empty: null\n"
    )
    data = yamlish.loads(text)
    assert data["id"] == "OM-F-AN-0001", "id: %r" % data.get("id")
    assert data["title_zh"] == "欧拉恒等式", "title: %r" % data.get("title_zh")
    assert data["status"] == "VERIFIED(L3)", "status: %r" % data.get("status")
    assert data["assumptions"][0] == {"a": 1, "b": 2}, "assumptions: %r" % data.get("assumptions")
    assert data["symbols"][0]["name"] == "s", "symbols: %r" % data.get("symbols")
    assert data["notes"] == "折叠 文本", "块标量 >- 应折叠为单行，实得 %r" % data.get("notes")
    assert data["list_inline"] == [1, 2, 3], "list: %r" % data.get("list_inline")
    assert data["flag"] is True, "flag: %r" % data.get("flag")
    assert data["empty"] is None, "empty: %r" % data.get("empty")


def test_yamlish_block_literal():
    text = "a: |\n  第一行\n  第二行\nb: 1\n"
    data = yamlish.loads(text)
    assert data["a"] == "第一行\n第二行\n", "块标量 | 应保留换行: %r" % data.get("a")
    assert data["b"] == 1


def test_engine_registry_loads():
    root = record_mod.find_root(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if root is None:
        return
    from openmath import engines

    registry = engines.load_registry(root)
    names = [e.get("name") for e in registry]
    assert "prime-pi-block" in names, "注册表应含 prime-pi-block，实得 %s" % names
    entry = engines.find_engine(registry, name="prime-pi-block")
    module = engines.load_module(entry, root)
    assert module is not None, "引擎模块加载失败"
    caps = module.capabilities()
    assert caps["name"] == "prime-pi-block"
    assert module.available() is True
    result = engines.run(entry, module, {"checks": [{"x": 100, "expected": 25}]}, "L2")
    assert result["status"] == "PASS", "pi(100) 应为 25，实得 %r" % result
    bad = engines.run(entry, module, {"checks": [{"x": 100, "expected": 26}]}, "L2")
    assert bad["status"] == "FAIL", "错误期望值必须报 FAIL，实得 %r" % bad
    empty = engines.run(entry, module, {"checks": []}, "L2")
    assert empty["status"] == "UNKNOWN", "空检查项不得计为 PASS，实得 %r" % empty


def test_repo_records_are_valid():
    """对真实仓库跑一次 L0：应无结构性错误。"""
    root = record_mod.find_root(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if root is None:
        return
    records, load_errors = record_mod.load_all(root)
    assert not load_errors, "存在无法解析的记录文件: %s" % load_errors
    issues, stats = schema.lint_all(records, load_errors, root)
    errors = [i for i in issues if i.level == "error"]
    assert not errors, "L0 校验失败: %s" % [str(i) for i in errors]
    assert stats["records"] >= 1


def test_index_and_report():
    root = record_mod.find_root(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if root is None:
        return
    records, _ = record_mod.load_all(root)
    built = index_mod.build(records)
    assert built["count"] == len(records)
    assert isinstance(built["dangling"], list)
    stats = report.stats(records)
    assert stats["records"] == len(records)
    assert "by_level" in stats
    text = report.render_text(stats)
    assert "条目总数" in text


def test_record_fidelity_resident():
    """常驻判据（第 12 批由一次性普查升格）：源文与机读面必须同文。
    lint 只判「是不是 list」、图谱只从 str 项里抓 ID，两者都看不见「人类读到一条、
    机器读到另一条」这一型损失，所以这条性质必须由这把尺常驻守着。
    同批配变异体对照：真语料字节上折一行续文，判据必须红。"""
    import io
    import re
    import shutil
    import tempfile

    scanned = fidelity.walk()
    assert scanned, "扫描集为空：判集塌缩时的「0 枚」与「没有缺陷」同形"
    r = fidelity.scan()
    assert r["scanned"] == len(scanned), "扫描分母与 walk 不同（%s vs %s）" % (r["scanned"], len(scanned))
    assert r["records"] == 0, "源文↔机读不同文的记录 %d 份：%s" % (r["records"], r["rows"][:5])
    rc, ok = fidelity.selftest()
    assert ok and rc == 0, "三型夹具漏网或干净面假阳：这台探针不得引用"

    target = None
    for rel, path in scanned:
        text = io.open(path, encoding="utf-8").read()
        if fidelity.audit_text(text):
            continue
        lines = text.replace("\r\n", "\n").split("\n")
        key = None
        for i, ln in enumerate(lines):
            m = re.match(r"^([A-Za-z_]\w*):", ln)
            if m:
                key = m.group(1)
                continue
            if key in fidelity.LIST_FIELDS and re.match(r"^  - [^>\s]", ln) and i + 1 < len(lines):
                target = (rel, path, text, i, key, lines)
                break
        if target:
            break
    assert target, "语料里找不到一枚可折叠的顶层列表项——这台尺已无对象可判"
    rel, path, text, i, key, lines = target
    assert not re.match(r"^\s{4,}\S", lines[i + 1]), "变异体没有真正折叠：下一行本就是续行"
    mut_lines = list(lines)
    mut_lines.insert(i + 1, u"    续文不许被吞")
    fl = fidelity.audit_text(u"\n".join(mut_lines))
    assert fl and key in [k for _t, k, _s, _d in fl], "折叠续文没被点名（尺子坏了）：%s" % (fl,)

    tmp = tempfile.mkdtemp()
    try:
        for name, body in (("clean", text), ("mutant", u"\n".join(mut_lines))):
            sub = os.path.join(tmp, name)
            os.makedirs(sub)
            with io.open(os.path.join(sub, os.path.basename(path)), "wb") as fh:
                fh.write(body.encode("utf-8"))
        clean = fidelity.scan(os.path.join(tmp, "clean"))
        assert clean["scanned"] == 1 and clean["records"] == 0, "同字节副本在临时目录里必须 0 枚：%s" % (clean,)
        got = fidelity.scan(os.path.join(tmp, "mutant"))
        assert got["scanned"] == 1 and got["records"] == 1, "变异体目录读数异常：%s" % (got,)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_all():
    failures = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print("PASS  %s" % name)
            except AssertionError as exc:
                failures += 1
                print("FAIL  %s: %s" % (name, exc))
    print("-" * 60)
    print("%s" % ("全部通过" if failures == 0 else "失败 %d 项" % failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_all())
