"""从 my_lib 研究资产（报告文件名）自动抽取统一知识图谱首批实体与关系。

抽取规则（基于 my_lib 根目录已观察到的命名模式）：
- 每个 .md 报告 → WORK 实体（按前缀归类域：TUFT/算法联盟/织域平台/openmath/goldbach）
- 「勘误#N / 勘误N」 → AUDIT 实体，AUDITS 指向被审计对象
- 「可检验预言/封存结论/观测判读」 → FINDING 实体
- 版本序列（织域平台 vX.Y / ws_vX.Y） → SUPERSEDES 链
- 卷册（openuft_卷X_） → BELONGS_TO 卷域
- 专家角色（00-专家联盟/README） → PERSONA 实体（手工种子）

输出：output/knowledge_graph.json
"""
from __future__ import annotations

import os
import re
import sys

# 允许以脚本方式直接运行（openmath_sys 是 src 布局）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "openmath_sys", "src"))

from openmath_sys.graph_store import GraphStore  # noqa: E402


# 域映射：文件名前缀 → 域 node_id
DOMAIN_RULES = [
    (re.compile(r"^TUFT", re.I), "tuft"),
    (re.compile(r"^算法联盟", re.I), "coalition"),
    (re.compile(r"^织域平台", re.I), "zhiyu"),
    (re.compile(r"^openuft", re.I), "openuft"),
    (re.compile(r"^pwcv_goldbach", re.I), "goldbach"),
    (re.compile(r"^ws_v", re.I), "zhiyu_ws"),
    (re.compile(r"^全域统一场论", re.I), "tuft"),
    (re.compile(r"^分支B", re.I), "tuft"),
]

ERRATA_RE = re.compile(r"勘误\s*#?(\d+)", re.I)
VERSION_RE = re.compile(r"v(\d+)\.(\d+)", re.I)
JUAN_RE = re.compile(r"卷([一二三四五六七八九十]+)", re.I)


def classify_domain(filename: str) -> str:
    for rx, dom in DOMAIN_RULES:
        if rx.search(filename):
            return dom
    return "misc"


def extract(root: str) -> GraphStore:
    g = GraphStore()

    # 域节点
    for dom in ("tuft", "coalition", "zhiyu", "openmath", "goldbach", "openuft", "zhiyu_ws", "misc"):
        g.upsert_node(f"domain:{dom}", "DATASET", f"域:{dom}")

    # 专家角色种子（来自 00-专家联盟/README）
    personas = [
        ("archivist", "档案员"), ("formalizer", "形式化师"), ("computer", "计算师"),
        ("hound", "猎犬(反例)"), ("critic", "批评家"), ("skeptic", "怀疑论者"),
        ("translator", "翻译官"), ("historian", "历史学家"), ("teacher", "教师"),
        ("editor", "编辑"), ("arbiter", "仲裁者"), ("guardian", "监护人"),
    ]
    for pid, name in personas:
        g.upsert_node(f"persona:{pid}", "PERSONA", name)

    md_files = [f for f in os.listdir(root) if f.endswith(".md")]
    version_groups: dict[str, list[tuple[tuple[int, int], str, str]]] = {}

    for fn in md_files:
        path = os.path.join(root, fn)
        dom = classify_domain(fn)
        nid = f"work:{fn[:-3]}"
        g.upsert_node(nid, "WORK", fn, domain=dom, path=path)
        g.add_edge(nid, f"domain:{dom}", "BELONGS_TO", evidence=fn)

        # 勘误 → AUDIT
        m_err = ERRATA_RE.search(fn)
        if m_err:
            err_no = m_err.group(1)
            aid = f"audit:errata#{err_no}"
            g.upsert_node(aid, "AUDIT", f"勘误#{err_no}", number=int(err_no))
            g.add_edge(aid, nid, "AUDITS", evidence=fn)

        # 预言/封存/判读 → FINDING
        if any(k in fn for k in ("可检验预言", "封存结论", "观测判读", "最终封存", "预言清单")):
            fid = f"finding:{fn[:-3]}"
            g.upsert_node(fid, "FINDING", fn[:-3], kind="prediction")
            g.add_edge(fid, nid, "DERIVES_FROM", evidence=fn)

        # 卷册归属
        m_juan = JUAN_RE.search(fn)
        if m_juan:
            juan_id = f"domain:openfantu_juan{m_juan.group(1)}"
            g.upsert_node(juan_id, "DATASET", f"卷{m_juan.group(1)}")
            g.add_edge(nid, juan_id, "BELONGS_TO", evidence=fn)

        # 版本序列（织域平台/ws）
        m_ver = VERSION_RE.search(fn)
        if m_ver and dom in ("zhiyu", "zhiyu_ws"):
            major = m_ver.group(1)
            key = f"zhiyu_v{major}"
            version_groups.setdefault(key, []).append(
                ((int(m_ver.group(1)), int(m_ver.group(2))), nid, fn)
            )

    # 版本替代链（同主版本内按次版本排序，前者被后者替代）
    for key, items in version_groups.items():
        items.sort(key=lambda x: x[0])
        for i in range(1, len(items)):
            prev_nid = items[i - 1][1]
            cur_nid = items[i][1]
            g.add_edge(cur_nid, prev_nid, "SUPERSEDES", evidence=f"{items[i][2]} 替代 {items[i-1][2]}")

    return g


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else r"D:\a10\aikjx\code\my_lib"
    out_dir = os.path.join(os.path.dirname(__file__), "openmath_sys", "output")
    out_path = os.path.join(out_dir, "knowledge_graph.json")

    g = extract(root)
    g.export(out_path)

    stats = {
        "nodes": len(g.nodes),
        "edges": len(g.edges),
        "by_node_type": g.node_type_counts(),
        "by_edge_type": g.edge_type_counts(),
    }
    print("=== 统一研究知识图谱抽取完成 ===")
    print(f"输出: {out_path}")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
