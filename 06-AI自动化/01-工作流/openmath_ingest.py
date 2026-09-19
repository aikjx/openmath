#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenMath 自动摄取流水线（AI 辅助，需人类复核）

功能（一条命令完成）：
  1. 下载   : 抓取 OpenMath 官方内容字典(CD) 与 arXiv 数学论文
  2. 整理   : 字典原始文件快照 -> 09-数据/openmath_cds/；论文去重索引 -> 10-文献与索引/
  3. 分析   : 解析 CD 中的数学性质(CMP) 与示例方程，跑四维逻辑框架(句法/语义/结构/计算)
  4. 运行   : 产物全部落到本仓库对应目录，并生成运行报告

诚实约束（见 00-宪章/02-诚实红线.md）：
  - 所有产物 provenance.ai_assisted = true，未经人类复核。
  - 方程求解为计算校验(L2)，绝不构成"证明"；CD 性质解析成功不代表被证明。
  - arXiv 预印本 fact_check.status = UNVERIFIED，不得作为 L3+ 证据。
  - 本流水线不修改任何既有条目 status，不自称"完整/权威/终极"。
"""
from __future__ import annotations

import datetime
import json
import os
import sys

# ---- 定位仓库根与 openmath_sys 引擎 ------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(3):  # 06-AI自动化/01-工作流 -> repo root
    REPO = os.path.dirname(REPO)
sys.path.insert(0, os.path.join(REPO, "openmath_sys", "src"))

from openmath_sys.fetcher import (  # noqa: E402
    fetch_openmath_cd_raw, fetch_arxiv, parse_ocd, rank_papers,
)
from openmath_sys.parser import parse_text  # noqa: E402
from openmath_sys.logic_framework import FourDimLogicEngine  # noqa: E402

# ---- 配置 -------------------------------------------------------------------
CD_NAMES = [
    "arith1", "relation1", "transc1", "linalg2", "calculus1",
    "logic1", "setname1", "complex1", "alg1", "fns1",
]
QUERIES = [
    "OpenMath", "symbolic computation",
    "computer algebra system", "mathematical knowledge management",
]
MAX_PER_QUERY = 8
CD_BASE_URL = "https://raw.githubusercontent.com/OpenMath/CDs/master/cd/Official/{name}.ocd"

# 仅作演示种子的示例方程（明确标注为内置种子，非来自文献）
CANONICAL_SEED = [
    "2*x + 3 = 7",
    "x^2 - 5*x + 6 = 0",
    "a*x^2 + b*x + c = 0",
    "power(2, 3) + sqrt(16)",
    "gcd(12, 18)",
    "sin(x) + cos(x)",
    "lcm(4, 6) = 12",
]


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _meta(extra: dict | None = None) -> dict:
    m = {
        "generated_by": "06-AI自动化/01-工作流/openmath_ingest.py",
        "generated_at": _stamp(),
        "provenance": {
            "ai_assisted": True,
            "note": "由 AI 代理基于 openmath_sys 引擎自动生成，未经人类复核，不得作为 L3+ 证据。",
        },
        "honesty": (
            "本文件为 L0/L2 级数据处理产物，非证明；方程求解为计算校验(L2)。"
            "CD 性质(CMP)解析成功不代表被证明；arXiv 论文为预印本，状态 UNVERIFIED。"
        ),
    }
    if extra:
        m.update(extra)
    return m


# ---------------------------------------------------------------------------
# 1) 下载并整理 OpenMath CD
# ---------------------------------------------------------------------------
def ingest_cds() -> dict:
    cds_dir = os.path.join(REPO, "09-数据", "openmath_cds")
    os.makedirs(cds_dir, exist_ok=True)
    catalog: list[dict] = []
    for name in CD_NAMES:
        raw = fetch_openmath_cd_raw(name, timeout=10)
        entry = {
            "name": name,
            "source_url": CD_BASE_URL.format(name=name),
            "fetched": raw is not None,
            "symbols": [],
            "symbol_count": 0,
            "property_count": 0,
        }
        if raw:
            with open(os.path.join(cds_dir, f"{name}.ocd"), "w", encoding="utf-8") as f:
                f.write(raw)
            syms = parse_ocd(raw)
            entry["symbols"] = [
                {"name": s.name, "description": s.description, "n_properties": len(s.properties)}
                for s in syms
            ]
            entry["symbol_count"] = len(syms)
            entry["property_count"] = sum(len(s.properties) for s in syms)
        catalog.append(entry)
    return {"meta": _meta(), "cds": catalog}


# ---------------------------------------------------------------------------
# 2) 下载并整理 arXiv 论文
# ---------------------------------------------------------------------------
def ingest_papers() -> dict:
    seen: dict[str, dict] = {}
    for q in QUERIES:
        papers = fetch_arxiv(q, max_results=MAX_PER_QUERY, timeout=10)
        papers = rank_papers(papers, q.split())
        for p in papers:
            if p.paper_id not in seen:
                seen[p.paper_id] = p.to_dict()
            else:
                # 合并命中查询，取较高分
                seen[p.paper_id]["score"] = max(seen[p.paper_id]["score"], p.score)
    papers = sorted(seen.values(), key=lambda x: x["score"], reverse=True)

    by_cat: dict[str, int] = {}
    for p in papers:
        for c in p.get("categories", []):
            by_cat[c] = by_cat.get(c, 0) + 1

    return {
        "meta": _meta({
            "fact_check": {
                "status": "UNVERIFIED",
                "note": "arXiv 预印本，未经同行评议，不得作为本库 L3+ 证据依据。",
            },
            "queries": QUERIES,
        }),
        "stats": {"total": len(papers), "by_category": by_cat},
        "papers": papers,
    }


# ---------------------------------------------------------------------------
# 3) 四维逻辑分析
# ---------------------------------------------------------------------------
def analyze(cds_catalog: dict, engine: FourDimLogicEngine) -> dict:
    # 从 CD 性质(CMP)中提取可解析方程
    cmp_total = 0
    cmp_parsed = 0
    equations: list[dict] = []
    seen_raw: set[str] = set()

    def try_add(raw: str, source: str):
        nonlocal cmp_parsed
        if raw in seen_raw:
            return
        if not any(op in raw for op in ["=", "<=", ">=", "!=", "<", ">"]):
            return
        if not any(c.isalpha() for c in raw):
            return
        rec = parse_text(raw)
        if not rec.parse_ok:
            return
        cmp_parsed += 1
        seen_raw.add(raw)
        equations.append({"raw": raw, "source": source})

    for cd in cds_catalog["cds"]:
        for sym in cd["symbols"]:
            # 注意：symbols 中只存了 n_properties，需回源 CMP 文本
            pass

    # 回源：重新抓取并解析 CMP 文本（catalog 仅存了计数）
    for cd in cds_catalog["cds"]:
        name = cd["name"]
        raw = fetch_openmath_cd_raw(name, timeout=10)
        if not raw:
            continue
        for s in parse_ocd(raw):
            cmp_total += len(s.properties)
            for prop in s.properties:
                try_add(prop, f"CD:{name}/{s.name}")

    # 合并内置种子
    for raw in CANONICAL_SEED:
        if raw not in seen_raw:
            seen_raw.add(raw)
            equations.append({"raw": raw, "source": "seed(内置示例)"})

    # 跑四维框架
    results = []
    for eq in equations:
        rec = engine.process(eq["raw"])
        d3 = next((f for f in rec.facets if f.dimension == "D3"), None)
        d4 = next((f for f in rec.facets if f.dimension == "D4"), None)
        results.append({
            "raw": eq["raw"],
            "source": eq["source"],
            "variables": rec.facets[0].details.get("variables") if rec.facets else [],
            "is_equation": rec.facets[0].details.get("is_equation") if rec.facets else False,
            "classification": d3.details.get("classification") if d3 else None,
            "solve": d4.details.get("solve") if d4 else None,
            "conclusions": rec.conclusions,
        })

    return {
        "meta": _meta(),
        "coverage": {
            "cmp_total": cmp_total,
            "cmp_parsed": cmp_parsed,
            "parsed_rate": round(cmp_parsed / cmp_total, 4) if cmp_total else 0.0,
            "note": "cmp_parsed 为 CMP 文本中被本解析器成功解析的比例；解析成功不代表被证明(L4)。",
        },
        "equations_analyzed": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    print("[流水线] 启动 OpenMath 自动摄取（AI 辅助，需人类复核）")
    engine = FourDimLogicEngine()

    cds = ingest_cds()
    ok_cds = sum(1 for c in cds["cds"] if c["fetched"])
    total_sym = sum(c["symbol_count"] for c in cds["cds"])
    print(f"[1/3] CD 下载整理：{ok_cds}/{len(CD_NAMES)} 个成功，符号 {total_sym} 个")

    papers = ingest_papers()
    print(f"[2/3] 论文下载整理：去重后 {papers['stats']['total']} 篇")

    analysis = analyze(cds, engine)
    print(f"[3/3] 四维分析：CMP 可解析 {analysis['coverage']['cmp_parsed']}"
          f"/{analysis['coverage']['cmp_total']}"
          f"({analysis['coverage']['parsed_rate']})；分析方程 {analysis['equations_analyzed']} 条")

    # 写盘
    with open(os.path.join(REPO, "09-数据", "openmath_cds", "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(cds, f, ensure_ascii=False, indent=2)
    with open(os.path.join(REPO, "10-文献与索引", "arxiv_index.json"), "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    with open(os.path.join(REPO, "09-数据", "openmath_4d_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    _write_report(cds, papers, analysis)
    print("[完成] 产物已写入 09-数据/ 与 10-文献与索引/，报告见 06-AI自动化/01-工作流/RUN_REPORT.md")
    return 0


def _write_report(cds: dict, papers: dict, analysis: dict) -> None:
    lines = [
        "# OpenMath 自动摄取 · 运行报告",
        "",
        f"- 生成时间：{_stamp()}",
        "- 性质：AI 辅助自动生成，**未经人类复核**，不构成证明。",
        "",
        "## 1. 内容字典(CD) 摄取",
        f"- 成功 {sum(1 for c in cds['cds'] if c['fetched'])}/{len(cds['cds'])} 个；"
        f"符号合计 {sum(c['symbol_count'] for c in cds['cds'])} 个。",
        "",
        "## 2. 论文索引",
        f"- 去重后 {papers['stats']['total']} 篇；分类分布见 arxiv_index.json。",
        "- 注意：arXiv 预印本 `fact_check.status = UNVERIFIED`，不得作为 L3+ 证据。",
        "",
        "## 3. 四维逻辑分析",
        f"- CD 性质(CMP)可解析 {analysis['coverage']['cmp_parsed']}"
        f"/{analysis['coverage']['cmp_total']}（率 {analysis['coverage']['parsed_rate']}）。",
        f"- 共分析方程 {analysis['equations_analyzed']} 条（含内置种子）。",
        "- 方程求解为计算校验(L2)，非证明(L4)。",
        "",
        "## 4. 产物清单",
        "- `09-数据/openmath_cds/<name>.ocd` 原始快照",
        "- `09-数据/openmath_cds/catalog.json` 符号目录",
        "- `09-数据/openmath_4d_analysis.json` 四维分析",
        "- `10-文献与索引/arxiv_index.json` 论文索引",
    ]
    with open(os.path.join(_HERE, "RUN_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
