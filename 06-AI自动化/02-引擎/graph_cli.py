"""统一 CLI 入口（企业级归一化）。

用法：
    python graph_cli.py build [root]         # 从 root 抽取并重建图谱
    python graph_cli.py stats                # 总览
    python graph_cli.py risk                 # 高风险卷册
    python graph_cli.py hubs                  # 枢纽排行
    python graph_cli.py verdicts              # 判决分布
    python graph_cli.py refutations          # 反驳热点
    python graph_cli.py sqlite <out.db>       # 导出 SQLite
    python graph_cli.py neighbors <id>       # 查邻居
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph import GraphStore  # noqa: E402
from openmath_sys.graph.extract import build_graph  # noqa: E402
from openmath_sys.graph import analyze  # noqa: E402
from openmath_sys.graph.db import save_sqlite, load_sqlite, stats_sqlite  # noqa: E402


GRAPH_JSON = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.json")
GRAPH_DB = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.db")


def cmd_build(args: list[str]) -> None:
    root = args[0] if args and not args[0].startswith("--") else r"D:\a10\aikjx\code\my_lib"
    incremental = "--incremental" in args
    state_path = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "extract_state.json")
    g, stats = build_graph(root, incremental=incremental, state_path=state_path)
    g.export(GRAPH_JSON)
    save_sqlite(g, GRAPH_DB)
    print("=== 图谱重建完成 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  增量模式: {'是' if incremental else '否（全量）'}")
    print(f"  JSON: {GRAPH_JSON}")
    print(f"  SQLite: {GRAPH_DB}")


def load() -> GraphStore:
    if os.path.exists(GRAPH_DB):
        return load_sqlite(GRAPH_DB)
    return GraphStore.load(GRAPH_JSON)


def cmd_stats(_: list[str]) -> None:
    g = load()
    print(f"节点: {len(g.nodes)}  边: {len(g.edges)}")
    print("按类型节点:", g.node_type_counts())
    print("按类型边:", g.edge_type_counts())


def cmd_risk(_: list[str]) -> None:
    print("=== 高风险卷册（被勘误审计）===")
    for label, cnt, _ in analyze.risk(load()):
        print(f"  [{cnt}] {label}")


def cmd_hubs(_: list[str]) -> None:
    print("=== 枢纽 top 20 ===")
    for label, deg, ntype, _ in analyze.hubs(load()):
        print(f"  [{deg:3d}] ({ntype}) {label}")


def cmd_verdicts(_: list[str]) -> None:
    print("=== 判决分布 ===")
    v = analyze.verdicts(load())
    for k in ("confirmed", "refuted", "mixed", "unknown", "total"):
        print(f"  {k}: {v[k]}")
    print(f"  验证率: {v['confirm_rate']}%   拒绝率: {v['refute_rate']}%")


def cmd_refutations(_: list[str]) -> None:
    print("=== 反驳热点 ===")
    for label, cnt, _ in analyze.refutations(load()):
        print(f"  [{cnt}] {label}")


def cmd_sqlite(args: list[str]) -> None:
    out = args[0] if args else GRAPH_DB
    save_sqlite(load(), out)
    print(f"已导出 SQLite: {out}")
    print(stats_sqlite(out))


def cmd_neighbors(args: list[str]) -> None:
    if not args:
        print("用法: neighbors <node_id>")
        return
    g = load()
    nid = args[0]
    if nid not in g.nodes:
        print(f"未找到: {nid}")
        return
    for e in g.neighbors(nid):
        other = e.dst if e.src == nid else e.src
        other_label = g.nodes[other].label if other in g.nodes else other
        direction = "→" if e.src == nid else "←"
        print(f"  {direction} [{e.etype}] {other_label}")


def cmd_search(args: list[str]) -> None:
    """FTS5 全文搜索节点。"""
    if not args:
        print("用法: search <keyword>")
        return
    from openmath_sys.graph.db import search_sqlite
    results = search_sqlite(GRAPH_DB, args[0], limit=20)
    if not results:
        print(f"未找到: {args[0]}")
        return
    print(f"=== 搜索 '{args[0]}' 命中 {len(results)} 条 ===")
    for r in results:
        print(f"  [{r['ntype']}] {r['label']}  ({r['node_id']})")


def cmd_import(args: list[str]) -> None:
    """从 CSV 导入业务数据（自动识别节点表/边表）。"""
    if not args:
        print("用法: import <csv_path>")
        return
    from openmath_sys.graph.csv_importer import auto_import
    g = load()
    n = auto_import(g, args[0])
    g.export(GRAPH_JSON)
    save_sqlite(g, GRAPH_DB)
    print(f"=== 导入完成 ===")
    print(f"  文件: {args[0]}")
    print(f"  导入: {n} 条")
    print(f"  总图: {len(g.nodes)} 节点 / {len(g.edges)} 边")


COMMANDS = {
    "build": cmd_build, "stats": cmd_stats, "risk": cmd_risk, "hubs": cmd_hubs,
    "verdicts": cmd_verdicts, "refutations": cmd_refutations, "sqlite": cmd_sqlite,
    "neighbors": cmd_neighbors, "search": cmd_search, "import": cmd_import,
}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    handler = COMMANDS.get(sys.argv[1])
    if not handler:
        print(f"未知命令: {sys.argv[1]}；可用: {list(COMMANDS)}")
        return
    handler(sys.argv[2:])


if __name__ == "__main__":
    main()
