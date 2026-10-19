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


def test_intra_edge_faithfulness():
    """01-域依赖：声明的同层边若端点未归层，以前被静默跳过，而版面 `intra_edges`
    数的是**声明数**——读数纹丝不动，图上少一条边。现在由印出的图自己数。"""
    from openmath import flowdocs
    sig = "-.->|同层互译|"
    g = {"tiers": {"ranks": [{"rank": 1, "domains": ["ST", "CT"], "label": "语言层"},
                             {"rank": 2, "domains": ["NA"], "label": "逼近层"}],
                   "intra": [("CT", "ST"), ("NA", "CB")],
                   "unplaced": ["CB"], "missing_placement": []},
         "nodes": [{"domain": "ST"}, {"domain": "CT"}, {"domain": "CB"}]}
    text, meta = flowdocs.chart_domain_tiers(g)
    assert meta["intra_edges"] == 2, "夹具没把两条声明喂进去"
    assert meta["intra_dropped"] == 1 and meta["intra_dropped_pairs"] == ["NA-CB"]
    assert "X_INTRA_NA_CB" in text and "DEFECT" in text
    drawn = sum(1 for l in text.split("\n") if sig in l)
    assert drawn == meta["intra_drawn"] == 1, "读数不是从图上数出来的"
    assert meta["intra_edges"] != meta["intra_drawn"], "这条夹具要的就是声明≠画出"

    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mmd = open(os.path.join(repo, "10-文献与索引", "知识图谱", "流程图",
                            "01-域依赖.mmd"), "rb").read().decode("utf-8")
    face = open(os.path.join(repo, "10-文献与索引", "知识图谱", "_版面",
                             "graph_face.txt"), "rb").read().decode("utf-8")
    real_drawn = sum(1 for l in mmd.split("\n") if sig in l)
    import re as _re
    declared = int(_re.search(r'"intra_edges": (\d+)', face).group(1))
    printed = int(_re.search(r'"intra_drawn": (\d+)', face).group(1))
    dropped = int(_re.search(r'"intra_dropped": (\d+)', face).group(1))
    assert declared == real_drawn == printed and dropped == 0, \
        "现语料上声明 %d／图上 %d／版面 %d（未画出 %d）" % (declared, real_drawn, printed, dropped)


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


def test_precision_tier_authority():
    """精度档的**归属**：记录声明的档位优先，调用方只有真的传了才覆盖（第 15 批登记的债）。
    旧形状是 cli 把 `default=50` 无条件塞进 options，于是声明 80 位的记录跑在 50 位——
    判决看着没变，但「PASS 是在哪把尺下拿的」被命令行拿走了。四臂各钉一件事：
      (a) 未问 ⇒ 用记录声明的 80，来源标 record；
      (b) 显式问 50 ⇒ 用 50，来源标 cli（覆盖仍然合法，但必须留名）；
      (c) options 里放 None（＝没传）⇒ 不许被当成「要 0 位」，仍走 record；
      (d) 声明 0（整数精确类记录，小数档对它无意义）⇒ 走兜底 50，绝不许按 0 位跑。
    PASS 那句还必须注明档位来源：来源一失踪，读数就重新变成「无主之尺」。"""
    from openmath import verify as verify_mod

    def rec(declared):
        cfg = {"sample_count": 2, "tolerance": "1e-40", "seed": 7,
               "sample_points": [{"x": 3}]}
        if declared is not None:
            cfg["precision_digits"] = declared
        return {"data": {"id": "OM-T-TEST-0001",
                         "sympy": "((x+1)**2 - (x**2 + 2*x + 1))",
                         "verification": {"levels": {"L2": cfg}}}}

    a = verify_mod.verify_l2(rec(80), None, {})
    assert a["environment"]["precision_digits"] == 80 and \
        a["environment"]["precision_source"] == "record", "声明档没被采纳：%r" % a["environment"]
    b = verify_mod.verify_l2(rec(80), None, {"precision_digits": 50})
    assert b["environment"]["precision_digits"] == 50 and \
        b["environment"]["precision_source"] == "cli", "显式覆盖失效：%r" % b["environment"]
    c = verify_mod.verify_l2(rec(80), None, {"precision_digits": None})
    assert c["environment"]["precision_digits"] == 80 and \
        c["environment"]["precision_source"] == "record", "None 被当成了要 0 位：%r" % c["environment"]
    d = verify_mod.verify_l2(rec(0), None, {})
    assert d["environment"]["precision_digits"] == verify_mod.DEFAULT_DPS and \
        d["environment"]["precision_source"] == "default", "声明 0 位没有走兜底：%r" % d["environment"]
    for tag, r in (("a", a), ("b", b), ("c", c), ("d", d)):
        assert r["status"] == "PASS", "%s 臂没跑成 PASS（夹具失效）：%s" % (tag, r.get("notes"))
        assert "档位来源=" in (r.get("notes") or ""), "%s 臂的 PASS 没注明档位来源：%r" % (tag, r.get("notes"))


def test_verify_outlet_codec():
    """verify 出口的币种＝UTF-8，且这一条必须有牙。
    语料里有 25 种 GBK 编不出的字形（`²`×86、`−`×43、`⇒`×20…共 233 次，载体
    `scratch/T16_GLYPH_face.txt`），当前**没有一条命令把它们印出来**——所以登记的那条债
    「非 UTF-8 出口遇 `⊢` 崩」在现语料上复现不出来（六条命令在 `PYTHONIOENCODING=gbk` 下全 rc=0，
    载体 `scratch/T16_GBK_probe_face.txt`）。三臂把这条边界钉住，字形由语料现取、不打字：
      (a) 反对照：同一枚字形打在**没修**的出口（strict gbk）上必须 UnicodeEncodeError；
      (b) 修后：过 `cli._force_utf8_streams()` 之后同一枚字形必须落成 UTF-8 字节；
      (c) 现网：真命令 `verify --id OM-T-MP-0001` 在 gbk 环境下 rc=0 且 stdout 按 UTF-8 解得开。
    (a) 不响＝针看不见（恒绿）；(b) 不响＝修是空的；(c) 红＝有一天印 statement 的那天提前崩在这里。"""
    import glob as _glob
    import subprocess

    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    glyph = None
    for path in sorted(_glob.glob(os.path.join(repo, "02-公式库", "**", "*.yaml"), recursive=True)):
        text = open(path, "rb").read().decode("utf-8", "replace")
        for ch in text:
            if ord(ch) > 127:
                try:
                    ch.encode("gbk")
                except UnicodeEncodeError:
                    glyph = ch
                    break
        if glyph:
            break
    assert glyph is not None, "语料里找不到 GBK 编不出的字形：覆盖面名单变了，这条判据要跟着改而不是跳过"
    env = dict(os.environ, PYTHONIOENCODING="gbk")

    def run(src):
        p = subprocess.Popen([sys.executable, "-c", src, glyph], cwd=repo, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        blob = p.communicate()[0]        # 先等子进程结束再取 returncode：
        return p.returncode, blob        # `return p.returncode, p.communicate()[0]` 会先把 rc 读成 None

    rc_a, out_a = run("import sys\n"
                      "sys.stdout.reconfigure(encoding='gbk', errors='strict')\n"
                      "print(sys.argv[1])\n")
    assert rc_a != 0 and b"UnicodeEncodeError" in out_a, \
        "反对照不响：没修的出口也能印 `%s`，那这把针看不见任何东西（rc=%s）" % (glyph, rc_a)
    rc_b, out_b = run("import os, sys\n"
                      "sys.path.insert(0, os.getcwd())\n"
                      "from openmath.cli import _force_utf8_streams\n"
                      "_force_utf8_streams()\n"
                      "print(sys.argv[1])\n")
    assert rc_b == 0, "修后仍崩：%r" % out_b[-200:]
    assert glyph in out_b.decode("utf-8"), "修后字形没落成 UTF-8：%r" % out_b[:80]
    q = subprocess.Popen([sys.executable, "-m", "openmath", "verify", "--id", "OM-T-MP-0001"],
                         cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out_c = q.communicate()[0]
    text_c = out_c.decode("utf-8", "replace")
    assert q.returncode == 0 and "OM-T-MP-0001" in text_c and "\ufffd" not in text_c, \
        "真命令在 gbk 环境下没跑成或不可解：rc=%s %r" % (q.returncode, text_c[:120])


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
