"""openmath 命令行入口。

命令：
    doctor   环境体检（哪些层级可用）
    lint     L0 结构校验
    verify   L2/L3 验证
    index    构建/检索索引
    fidelity 源文 ↔ 机读面逐枚比对（列表项内容丢失通道）
    status   看板
    new      从模板创建新记录
"""

import argparse
import io
import json
import os
import shutil
import sys

from . import fidelity as fidelity_mod, flowdocs, graph as graph_mod, ids, index as index_mod, record as record_mod, report as report_mod, schema, verify


def _stdout_utf8():
    """Windows GBK 控制台下保证中文可输出。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def cmd_doctor(args):
    root = record_mod.find_root()
    print("OpenMath doctor")
    print("-" * 60)
    print("Python       : %s" % sys.version.split()[0])
    print("仓库根       : %s" % (root or "未找到（请在仓库内运行）"))
    print("YAML 后端    : %s" % record_mod.backend_name())
    if record_mod.backend_name() == record_mod.BACKEND_YAMLISH:
        print("               提示：安装 PyYAML 可获得更完整的 YAML 支持（pip install pyyaml）")
    backends = verify.backends()
    for name in ("sympy",):
        value = backends.get(name)
        if value:
            print("可选依赖     : %s %s  ✅" % (name, value))
        else:
            print("可选依赖     : %s 未安装  → L2/L3 将标记为 SKIP" % name)
    print("已实现层级   : L0（结构） L2（数值） L3（符号）")
    print("未实现层级   : L1（部分） L4 L5 L6")
    if root:
        records, errors = record_mod.load_all(root)
        print("记录文件     : %d 条（加载失败 %d）" % (len(records), len(errors)))
    return 0


def cmd_lint(args):
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    records, load_errors = record_mod.load_all(root)
    issues, stats = schema.lint_all(records, load_errors, root)
    if args.json:
        print(
            json.dumps(
                {
                    "stats": stats,
                    "issues": [i.as_dict() for i in issues],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if stats["errors"] else 0
    print("OpenMath L0 结构校验  (YAML 后端: %s)" % stats["backend"])
    print("-" * 60)
    print("记录数       : %d" % stats["records"])
    print("加载失败     : %d" % stats["load_errors"])
    print("错误         : %d" % stats["errors"])
    if issues:
        print("-" * 60)
        for issue in issues:
            print(str(issue))
    if stats["errors"] == 0:
        print("-" * 60)
        print("L0 通过：全部记录结构合规。")
        print("提醒：L0 只说明格式对，与数学正确性无关。")
        return 0
    print("-" * 60)
    print("L0 未通过：请修正上述错误后重试。")
    return 1


def _force_utf8_streams():
    """把 verify 出口的币种钉成 UTF-8，容错走 backslashreplace。
    实测口径（第 16 批，载体 `scratch/T16_GBK_probe_face.txt`）：本轮逐条命令在强制
    `PYTHONIOENCODING=gbk` 下跑，`lint`／`fidelity`／`graph --check`／`index`／`verify`（含 `--json`）
    **全部 rc=0**——所以登记的那条债「非 UTF-8 出口遇 `⊢` 崩」在当前语料上复现不出来，不改口径就是假账。
    但语料里有 25 种 GBK 编不出的字形（`²`×86、`−`×43、`⇒`×20…，共 233 次，住在 26 份 yaml 的
    name/statement/notes 里，当前没有一条命令把它们印出来）。这条固定的就是那道边界：
    哪天把 statement 印进版面，宁可看到 `\\xb2` 也不许 UnicodeEncodeError 把这一条判决整个吃掉。"""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (ValueError, OSError, io.UnsupportedOperation):
            # 被 pytest／上层调用方换掉的流改不动：不改不许崩，判决比币种要紧。
            pass


def cmd_verify(args):
    _force_utf8_streams()
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    records, _ = record_mod.load_all(root)
    if args.id:
        wanted = set(args.id)
        records = [r for r in records if r.get("id") in wanted]
    if args.domain:
        records = [r for r in records if r["data"].get("domain") in set(args.domain)]
    if not records:
        print("没有匹配的记录。")
        return 0
    levels = args.level or ["L2"]
    # 只把**真被传了**的开关交给引擎：无条件塞默认值等于让命令行替记录决定精度档
    # （第 15 批登记的债；口径见 openmath/verify.py 的 _effective）。
    options = {}
    if args.precision is not None:
        options["precision_digits"] = args.precision
    if args.seed is not None:
        options["seed"] = args.seed
    if args.samples is not None:
        options["sample_count"] = args.samples
    exit_code = 0
    for rec in records:
        for level in levels:
            result = verify.verify_record(rec, level, root, options)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(
                    "%-14s %-3s %-6s  %s"
                    % (
                        result.get("target_id"),
                        level,
                        result.get("status"),
                        result.get("notes", ""),
                    )
                )
                metrics = result.get("metrics") or {}
                if metrics.get("max_abs_residual") and metrics.get("tolerance"):
                    print(
                        "               最大绝对残差 %s（容差 %s，已求值 %s/%s）"
                        % (
                            metrics.get("max_abs_residual"),
                            metrics.get("tolerance", ""),
                            metrics.get("sample_evaluated"),
                            metrics.get("sample_total"),
                        )
                    )
                elif metrics.get("max_abs_residual"):
                    print("               最大绝对残差 %s" % metrics.get("max_abs_residual"))
            if result.get("status") == "FAIL":
                exit_code = 1
            if result.get("status") == "ERROR":
                exit_code = 2
    return exit_code


def cmd_index(args):
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    if args.search or args.domain or args.level:
        existing = index_mod.load(root)
        if existing is None:
            print("索引尚未生成，先运行: python -m openmath index")
            return 1
        hits = index_mod.search(
            existing,
            keyword=args.search,
            domain=(args.domain[0] if args.domain else None),
            level=(args.level[0] if args.level else None),
        )
        for hit in hits:
            print(hit)
        print("（共 %d 条）" % len(hits))
        return 0
    records, _ = record_mod.load_all(root)
    built = index_mod.build(records)
    path = index_mod.write(built, root)
    print("索引已生成: %s" % path)
    print("条目数     : %d" % built["count"])
    print("悬空引用   : %d" % len(built["dangling"]))
    for ref in built["dangling"]:
        print("             - %s（被引用但不存在）" % ref)
    return 0


def cmd_fidelity(args):
    rc, text = fidelity_mod.report()
    print(text)
    if args.out:
        with io.open(args.out, "wb") as fh:
            fh.write((text + "\n").encode("utf-8"))
        print("面已落盘: %s" % args.out)
    return rc


def cmd_graph(args):
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    g = graph_mod.build(root)
    charts, meta = flowdocs.render_charts(g)
    rows = flowdocs.xref_md(g)
    face_text = flowdocs.face(g, meta, rows)
    defects = {name: count for name, (sev, count) in graph_mod.defect_counts(g).items()
               if sev == "DEFECT" and count}
    if args.check:
        faults = flowdocs.check_invariants(g, charts, meta, [], writes_expected=False, rows=rows)
        print(face_text, end="")
        for fault in faults:
            print("FAULT  %s" % fault)
        print("（--check：未写盘；DEFECT 类 %d，不变量故障 %d）" % (len(defects), len(faults)))
        return 1 if (faults or defects) else 0
    written = flowdocs.write_all(root, g, charts, meta, rows, face_text)
    faults = flowdocs.check_invariants(g, charts, meta, written, rows=rows)
    for relpath, size in written:
        print("已生成   : %s（%d B）" % (relpath, size))
    print(face_text, end="")
    for fault in faults:
        print("FAULT  %s" % fault)
    if defects and not faults:
        print("==> 生成物完好（rc=0 只证明这一点），但语料 DEFECT 类非空：%s —— "
              "判语料请看 `openmath graph --check`。" % ", ".join(sorted(defects)))
    return 1 if faults else 0


def cmd_status(args):
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    records, errors = record_mod.load_all(root)
    stats = report_mod.stats(records, errors)
    if args.format == "json":
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(report_mod.render_text(stats))
    if args.check:
        return 1 if stats["load_errors"] else 0
    return 0


def cmd_new(args):
    root = record_mod.find_root()
    if root is None:
        print("错误：未找到仓库根，请在 openmath 仓库内运行。")
        return 2
    kind_code = args.kind[0].upper()
    kind_map = {"F": "formula", "D": "definition", "T": "theorem", "C": "conjecture",
                "X": "counterexample", "A": "algorithm", "P": "problem"}
    if kind_code not in kind_map:
        print("未知类型码: %s（允许 %s）" % (kind_code, ", ".join(sorted(kind_map))))
        return 2
    domain = args.domain.upper()
    if domain not in ids.DOMAINS:
        print("未知域代码: %s（见 00-宪章/04-标识与编号规范.md）" % domain)
        return 2
    records, _ = record_mod.load_all(root)
    new_id = ids.next_id(kind_code, domain, record_mod.collect_ids(records))
    template = os.path.join(root, "02-公式库", "_模板", "公式模板.yaml")
    target_dir = os.path.join(root, "02-公式库", args.target or domain)
    os.makedirs(target_dir, exist_ok=True)
    slug = args.slug or "untitled"
    target = os.path.join(target_dir, "%s-%s.yaml" % (new_id, slug))
    if os.path.exists(target):
        print("目标文件已存在: %s" % target)
        return 1
    if os.path.exists(template):
        shutil.copyfile(template, target)
        with open(target, "r", encoding="utf-8") as handle:
            text = handle.read()
        text = text.replace("OM-F-<域>-<序号>", new_id)
        text = text.replace("domain: <域代码>", "domain: %s" % domain)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("id: %s\nkind: %s\ntitle_zh: \"\"\n" % (new_id, kind_map[kind_code]))
    print("已创建: %s" % os.path.relpath(target, root).replace("\\", "/"))
    print("提醒：请填写 title_zh / title_en / assumptions，并为 .yaml 配套同名 .md 说明。")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="openmath",
        description="OpenMath 开放数学联盟：分级验证与知识管理",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="环境体检").set_defaults(func=cmd_doctor)

    p_lint = sub.add_parser("lint", help="L0 结构校验")
    p_lint.add_argument("--json", action="store_true", help="输出 JSON")
    p_lint.set_defaults(func=cmd_lint)

    p_verify = sub.add_parser("verify", help="L2/L3 验证")
    p_verify.add_argument("--level", nargs="+", choices=["L2", "L3"], help="验证层级")
    p_verify.add_argument("--id", nargs="+", help="指定条目 ID")
    p_verify.add_argument("--domain", nargs="+", help="按域代码过滤")
    p_verify.add_argument("--precision", type=int, default=None,
                          help="有效数字位数；缺省＝记录自己声明的档位（未声明才用引擎兜底 50）")
    p_verify.add_argument("--seed", type=int, default=None,
                          help="随机种子；缺省＝记录声明的种子（未声明用 20260910）")
    p_verify.add_argument("--samples", type=int, default=None,
                          help="采样点数；缺省＝记录声明的 sample_count（未声明用 20）")
    p_verify.add_argument("--json", action="store_true", help="输出 JSON")
    p_verify.set_defaults(func=cmd_verify)

    p_index = sub.add_parser("index", help="构建/检索索引")
    p_index.add_argument("--search", help="关键词检索")
    p_index.add_argument("--domain", nargs="+", help="按域过滤")
    p_index.add_argument("--level", nargs="+", help="按证据等级过滤")
    p_index.set_defaults(func=cmd_index)

    p_graph = sub.add_parser("graph", help="知识图谱、关系流程图与缺口检测")
    p_graph.add_argument("--check", action="store_true", help="只判据不写盘（CI 模式）")
    p_graph.set_defaults(func=cmd_graph)

    p_fidelity = sub.add_parser("fidelity", help="源文 ↔ 机读面逐枚比对（列表项内容丢失）")
    p_fidelity.add_argument("--out", help="把判决面另存为该路径（字节写，不追加）")
    p_fidelity.set_defaults(func=cmd_fidelity)

    p_status = sub.add_parser("status", help="看板")
    p_status.add_argument("--format", choices=["text", "json"], default="text")
    p_status.add_argument("--check", action="store_true", help="CI 模式：有问题则返回非 0")
    p_status.set_defaults(func=cmd_status)

    p_new = sub.add_parser("new", help="从模板创建新记录")
    p_new.add_argument("kind", nargs=1, help="类型码：D/F/T/C/X/A/P")
    p_new.add_argument("--domain", required=True, help="域代码，如 NT")
    p_new.add_argument("--slug", help="英文短标识")
    p_new.add_argument("--target", help="目标子目录（默认用域代码）")
    p_new.set_defaults(func=cmd_new)

    return parser


def main(argv=None):
    _stdout_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
