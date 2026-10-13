"""统一资产抽取（企业级归一化）：文件名 + 内容级 一体化。

修复点（相对旧 extract_assets.py / content_extractor.py）：
1. CITES 边：T/J 编号全文挂边，不再要求"上游提示词"（旧版仅 4 条边）
2. CONFIRMS/REFUTES：不再挂自环边，落到 WORK.attrs['verdict']（confirmed/refuted/mixed）
3. 版本替代链：按文档类型分桶（新功能台账/集成说明/优化报告/诊断报告），同桶内串链
"""
from __future__ import annotations

import os
import re
from typing import Any

from .store import GraphStore


# ---- 正则 ----
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
TASK_RE = re.compile(r"\bT(\d{2})\b")
CLAIM_RE = re.compile(r"\bJ(\d{2})\b")
SCRIPT_RE = re.compile(r"scratch/[A-Za-z0-9_\-]+\.py")
CONFIRM_RE = re.compile(r"(已确证|已验证?|完全一致|闭合|与本机复跑逐位一致)")
REFUTE_RE = re.compile(r"(已拒|被拒|被排除|错位|OOM|卡死|漂移|未通过|不收敛)")
WIKI_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")  # [[目标]] 或 [[目标|别名]]

# 版本文档类型桶
VERSION_BUCKETS = [
    (re.compile(r"新功能台账"), "changelog"),
    (re.compile(r"集成说明"), "integration"),
    (re.compile(r"优化.*报告|优化分析"), "optimization"),
    (re.compile(r"诊断|裁决|审计"), "diagnosis"),
]


def classify_domain(filename: str) -> str:
    for rx, dom in DOMAIN_RULES:
        if rx.search(filename):
            return dom
    return "misc"


def version_bucket(filename: str) -> str | None:
    for rx, bucket in VERSION_BUCKETS:
        if rx.search(filename):
            return bucket
    return None


def build_graph(root: str, incremental: bool = False, state_path: str | None = None) -> tuple[GraphStore, dict[str, Any]]:
    """从 root 目录抽取 .md 资产，构建完整 GraphStore。

    incremental=True 时读 state_path 的 mtime 缓存，跳过未变化文件的内容读取。
    """
    g = GraphStore()
    stats: dict[str, Any] = {"files": 0, "by_node_type": {}, "by_edge_type": {},
                              "files_read": 0, "files_skipped": 0}

    # 加载增量状态
    state: dict[str, float] = {}
    if incremental and state_path and os.path.exists(state_path):
        import json
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

    # 域节点
    for dom in ("tuft", "coalition", "zhiyu", "zhiyu_ws", "openuft", "goldbach", "misc"):
        g.upsert_node(f"domain:{dom}", "DATASET", f"域:{dom}")

    # 专家角色种子
    for pid, name in [
        ("archivist", "档案员"), ("formalizer", "形式化师"), ("computer", "计算师"),
        ("hound", "猎犬(反例)"), ("critic", "批评家"), ("skeptic", "怀疑论者"),
        ("translator", "翻译官"), ("historian", "历史学家"), ("teacher", "教师"),
        ("editor", "编辑"), ("arbiter", "仲裁者"), ("guardian", "监护人"),
    ]:
        g.upsert_node(f"persona:{pid}", "PERSONA", name)

    md_files = [f for f in os.listdir(root) if f.endswith(".md")]
    version_groups: dict[str, list] = {}

    for fn in md_files:
        path = os.path.join(root, fn)
        stats["files"] += 1
        dom = classify_domain(fn)
        work_id = f"work:{fn[:-3]}"
        g.upsert_node(work_id, "WORK", fn, domain=dom, path=path)
        g.add_edge(work_id, f"domain:{dom}", "BELONGS_TO", evidence=fn)

        # 勘误
        m_err = ERRATA_RE.search(fn)
        if m_err:
            aid = f"audit:errata#{m_err.group(1)}"
            g.upsert_node(aid, "AUDIT", f"勘误#{m_err.group(1)}", number=int(m_err.group(1)))
            g.add_edge(aid, work_id, "AUDITS", evidence=fn)

        # 预言/封存
        if any(k in fn for k in ("可检验预言", "封存结论", "观测判读", "最终封存", "预言清单")):
            fid = f"finding:{fn[:-3]}"
            g.upsert_node(fid, "FINDING", fn[:-3], kind="prediction")
            g.add_edge(fid, work_id, "DERIVES_FROM", evidence=fn)

        # 卷册归属
        m_juan = JUAN_RE.search(fn)
        if m_juan:
            juan_id = f"domain:juan_{m_juan.group(1)}"
            g.upsert_node(juan_id, "DATASET", f"卷{m_juan.group(1)}")
            g.add_edge(work_id, juan_id, "BELONGS_TO", evidence=fn)

        # 版本序列（按桶分组）
        m_ver = VERSION_RE.search(fn)
        if m_ver and dom in ("zhiyu", "zhiyu_ws"):
            bucket = version_bucket(fn) or "default"
            key = f"v{m_ver.group(1)}:{bucket}"
            version_groups.setdefault(key, []).append(
                ((int(m_ver.group(1)), int(m_ver.group(2))), work_id, fn)
            )

        # ---- 内容级抽取（增量模式：mtime 未变则跳过文件读取）----
        mtime = os.path.getmtime(path)
        if incremental and state.get(fn) == mtime:
            stats["files_skipped"] += 1
            continue
        stats["files_read"] += 1
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        state[fn] = mtime

        # T 任务 → THEOREM + CITES（全文扫，不要求上游提示词）
        for m in set(TASK_RE.findall(text)):
            tid = f"theorem:T{m}"
            if tid not in g.nodes:
                g.upsert_node(tid, "THEOREM", f"T{m} 任务", number=int(m))
            g.add_edge(work_id, tid, "CITES", evidence=f"{fn} 引用 T{m}")

        # J 论断 → CLAIM + EXTENDS
        for m in set(CLAIM_RE.findall(text)):
            jid = f"claim:J{m}"
            if jid not in g.nodes:
                g.upsert_node(jid, "CLAIM", f"J{m} 论断", number=int(m))
            g.add_edge(work_id, jid, "EXTENDS", evidence=f"{fn} 承接 J{m}")

        # [[wiki]] 双向链接 → CITES + REFERENCED_BY（对称边）
        for target, alias in set(WIKI_RE.findall(text)):
            target = target.strip()
            if not target:
                continue
            tid = f"work:{target}"
            if tid not in g.nodes:
                # 目标不存在时自动建 WORK 占位（双向链接核心）
                g.upsert_node(tid, "WORK", alias or target, domain="wiki_link")
            g.add_edge(work_id, tid, "CITES", evidence=f"{fn} [[{target}]]")
            g.add_edge(tid, work_id, "REFERENCED_BY", evidence=f"{fn} 被 [[{target}]] 引用")

        # scratch 脚本 → TOOL + USES
        for script in set(SCRIPT_RE.findall(text)):
            sid = f"tool:{script}"
            if sid not in g.nodes:
                g.upsert_node(sid, "TOOL", script, path=script)
            g.add_edge(work_id, sid, "USES", evidence=f"{fn} 复用 {script}")

        # 判决标记 → WORK.attrs['verdict']（不挂自环边）
        has_confirm = bool(CONFIRM_RE.search(text))
        has_refute = bool(REFUTE_RE.search(text))
        verdict = "mixed" if (has_confirm and has_refute) else \
                  "confirmed" if has_confirm else \
                  "refuted" if has_refute else "unknown"
        g.nodes[work_id].attrs["verdict"] = verdict

    # 版本替代链（同桶内按版本排序串链）
    for key, items in version_groups.items():
        items.sort(key=lambda x: x[0])
        for i in range(1, len(items)):
            g.add_edge(items[i][1], items[i - 1][1], "SUPERSEDES",
                       evidence=f"{items[i][2]} 替代 {items[i-1][2]}")

    stats["by_node_type"] = g.node_type_counts()
    stats["by_edge_type"] = g.edge_type_counts()
    stats["nodes"] = len(g.nodes)
    stats["edges"] = len(g.edges)

    # 写回增量状态
    if incremental and state_path:
        import json
        os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    return g, stats
