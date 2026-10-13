"""CSV 业务数据导入器：把企业 CSV 批量导入知识图谱。

CSV 格式约定：
- 列：node_id, ntype, label, [attrs...] 或 edge_src, edge_dst, etype, evidence
- 自动识别节点表 vs 边表（首列名判断）
"""
from __future__ import annotations

import csv
import os
from .store import GraphStore


def import_nodes_csv(g: GraphStore, csv_path: str) -> int:
    """从 CSV 导入节点。首列 node_id，次列 ntype，三列 label，其余为 attrs。"""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = row.get("node_id", "").strip()
            ntype = row.get("ntype", "ENTITY").strip()
            label = row.get("label", node_id).strip()
            if not node_id:
                continue
            attrs = {k: v for k, v in row.items()
                     if k not in ("node_id", "ntype", "label") and v.strip()}
            g.upsert_node(node_id, ntype, label, **attrs)
            count += 1
    return count


def import_edges_csv(g: GraphStore, csv_path: str) -> int:
    """从 CSV 导入边。列：edge_src, edge_dst, etype, [evidence]。"""
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row.get("edge_src", "").strip()
            dst = row.get("edge_dst", "").strip()
            etype = row.get("etype", "RELATED_TO").strip()
            evidence = row.get("evidence", "").strip()
            if not src or not dst:
                continue
            # 自动建端点节点
            if src not in g.nodes:
                g.upsert_node(src, "ENTITY", src)
            if dst not in g.nodes:
                g.upsert_node(dst, "ENTITY", dst)
            g.add_edge(src, dst, etype, evidence)
            count += 1
    return count


def auto_import(g: GraphStore, csv_path: str) -> int:
    """自动识别 CSV 类型（节点表 vs 边表）。"""
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        header = csv.reader(f).__next__()
    cols = set(c.strip().lower() for c in header)
    if "node_id" in cols and "ntype" in cols:
        return import_nodes_csv(g, csv_path)
    if "edge_src" in cols and "edge_dst" in cols:
        return import_edges_csv(g, csv_path)
    raise ValueError(f"无法识别 CSV 类型（列: {header}）")
