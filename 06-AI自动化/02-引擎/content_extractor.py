"""企业级内容级抽取：从 .md 正文抽取 T/J 编号实体、工具脚本、判决关系。

在文件名抽取（extract_assets.py）之上，深入正文：
- T<n>（TUFT 任务编号）→ THEOREM 实体；"继承 T07/T08" → CITES 上游
- J<n>（算法联盟论断）→ CLAIM 实体；"承接 J22" → EXTENDS
- scratch/xxx.py → TOOL 实体；"复用 xxx.py" → USES
- "已确证/已验/✓/完全一致" → CONFIRMS 边
- "已拒/被拒/排除/错位/OOM" → REFUTES 边

输出合并进 knowledge_graph.json（同 GraphStore 加载-抽取-回写）。
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph_store import GraphStore  # noqa: E402


TASK_RE = re.compile(r"\bT(\d{2})\b")          # T07 T08 ...
CLAIM_RE = re.compile(r"\bJ(\d{2})\b")         # J22 J23 ...
SCRIPT_RE = re.compile(r"scratch/[A-Za-z0-9_\-]+\.py")
CONFIRM_PATTERNS = re.compile(r"(已确证|已验证?|完全一致|✓\s*$|闭合|与本机复跑逐位一致)")
REFUTE_PATTERNS = re.compile(r"(已拒|被拒|被排除|错位|OOM|卡死|漂移|未通过|不收敛)")
UPSTREAM_HINT = re.compile(r"(继承|承接|上一轮|已确证|已验证|复用|沿用)")


def extract_content(root: str, g: GraphStore) -> dict:
    """读根目录 .md 正文，把内容级实体/关系合并进图。返回抽取统计。"""
    stats = {"files_scanned": 0, "theorems": 0, "claims": 0, "tools": 0,
             "confirm_edges": 0, "refute_edges": 0, "cites_edges": 0}

    md_files = [f for f in os.listdir(root) if f.endswith(".md")]
    for fn in md_files:
        path = os.path.join(root, fn)
        work_id = f"work:{fn[:-3]}"
        if work_id not in g.nodes:
            continue  # 跳过未入图的文件（如 reports 子目录）
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        stats["files_scanned"] += 1

        # T 编号 → THEOREM
        for m in set(TASK_RE.findall(text)):
            tid = f"theorem:T{m}"
            if tid not in g.nodes:
                g.upsert_node(tid, "THEOREM", f"T{m} 任务", number=int(m))
                stats["theorems"] += 1
            # 若当前文档引用上游 T，且当前文档是 WORK，则挂 CITES
            if UPSTREAM_HINT.search(text[:2000]):  # 只在前 2000 字找引用意图
                g.add_edge(work_id, tid, "CITES", evidence=f"{fn} 引用 T{m}")
                stats["cites_edges"] += 1

        # J 编号 → CLAIM
        for m in set(CLAIM_RE.findall(text)):
            jid = f"claim:J{m}"
            if jid not in g.nodes:
                g.upsert_node(jid, "CLAIM", f"J{m} 论断", number=int(m))
                stats["claims"] += 1
            g.add_edge(work_id, jid, "EXTENDS", evidence=f"{fn} 承接 J{m}")

        # scratch 脚本 → TOOL
        for script in set(SCRIPT_RE.findall(text)):
            sid = f"tool:{script}"
            if sid not in g.nodes:
                g.upsert_node(sid, "TOOL", script, path=script)
                stats["tools"] += 1
            g.add_edge(work_id, sid, "USES", evidence=f"{fn} 复用 {script}")

        # 判决标记 → CONFIRMS / REFUTES（指向当前 WORK 自身状态）
        if CONFIRM_PATTERNS.search(text):
            g.add_edge(work_id, work_id, "CONFIRMS", evidence="正文含已验证/闭合标记")
            stats["confirm_edges"] += 1
        if REFUTE_PATTERNS.search(text):
            g.add_edge(work_id, work_id, "REFUTES", evidence="正文含已拒/错位/OOM 标记")
            stats["refute_edges"] += 1

    return stats


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else r"D:\a10\aikjx\code\my_lib"
    graph_path = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.json")

    g = GraphStore.load(graph_path)
    stats = extract_content(root, g)
    g.export(graph_path)

    print("=== 内容级抽取完成 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  合并后节点: {len(g.nodes)}  边: {len(g.edges)}")


if __name__ == "__main__":
    main()
