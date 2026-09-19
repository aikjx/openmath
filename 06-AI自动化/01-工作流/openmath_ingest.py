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

变更记录：
  - v2：CD 由 10 个扩至 20 个；analyze 改为优先读本地快照（避免二次联网）；
        增加 complex/set 的 JSON 序列化兜底。
  - v3 (2026-09-19)：
        1) CD 扩至官方全量 38 个（GitHub API 核实）；
        2) ingest_cds 增加「本地快照回退」——联网失败时改用本地 .ocd，
           修复 linalg1/set1 等已入库 CD 被记成符号数 0 的数据倒退缺陷；
        3) 为 parse_ocd 增加异常兜底，单个非标准 CD 不再中断整条流水线；
        4) 删除 analyze 中的死代码块；
        5) 保留未解析 CMP 反例样本（诚实红线：不静默丢弃）；
        6) meta 增加 evidence_level 显式证据等级标注；
        7) 运行报告增加官方覆盖率、缺失清单与上一轮增量对比。
"""
from __future__ import annotations

import datetime
import json
import os
import sys

# ---- 定位仓库根与 openmath_sys 引擎 ------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):  # 06-AI自动化/01-工作流 -> openmath 仓库根
    REPO = os.path.dirname(REPO)
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "openmath_sys", "src"))

from openmath_sys.fetcher import (  # noqa: E402
    fetch_openmath_cd_raw, fetch_arxiv, parse_ocd, rank_papers,
)
from openmath_sys.parser import parse_text  # noqa: E402
from openmath_sys.logic_framework import FourDimLogicEngine  # noqa: E402

# ---- 配置 -------------------------------------------------------------------
# 官方全量清单（38 个），来源 GitHub API：
#   https://api.github.com/repos/OpenMath/CDs/contents/cd/Official （2026-09-19 探测）
# 演进：第一轮 10 个 -> 第二轮 20 个 -> 第三轮 38 个（官方全量）。
#   第二轮补充：linalg1(矩阵/向量算术)、set1(集合运算)、nums1(数系常数)、
#     integer1(整数)、fns2(更多函数)、list1(列表)、multiset1(多重集)、
#     limit1(极限)、minmax1(最值)、veccalc1(向量微积分)。
#   第三轮补充：altenc、bigfloat1、error、interval1、mathmlattr、mathmltypes、
#     meta、metagrp、metasig、piece1、quant1、relation3、rounding1、
#     s_data1、s_dist1、scscp1、scscp2、sts。
# 注1：arith2 上游 raw 与 API 两种方式均 404，不属官方 38 个之列，已移出清单。
# 注2：linalg1、set1 在 2026-09-19 探测时联网抓取失败，改由本地快照回退补齐。
# 注3：部分 CD 为纯符号声明（如 meta/scscp1/scscp2/sts/interval1 等），
#      CMP 性质数为 0 属正常现象，非抓取失败。
CD_NAMES = [
    "alg1", "altenc", "arith1", "bigfloat1", "calculus1", "complex1", "error",
    "fns1", "fns2", "integer1", "interval1", "limit1", "linalg1", "linalg2",
    "list1", "logic1", "mathmlattr", "mathmltypes", "meta", "metagrp",
    "metasig", "minmax1", "multiset1", "nums1", "piece1", "quant1",
    "relation1", "relation3", "rounding1", "s_data1", "s_dist1", "scscp1",
    "scscp2", "set1", "setname1", "sts", "transc1", "veccalc1",
]
OFFICIAL_CD_TOTAL = len(CD_NAMES)

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

# 未解析 CMP 反例样本保留上限（避免产物过大）
UNPARSED_SAMPLE_CAP = 30


def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _json_default(o):
    """让 complex / set 等不可序列化类型能落盘为可读字符串。"""
    if isinstance(o, complex):
        if o.imag == 0:
            return str(o.real)
        return f"{o.real}+{o.imag}j"
    if isinstance(o, set):
        return sorted(o, key=str)
    if isinstance(o, (bytes,)):
        return o.decode("utf-8", "replace")
    return str(o)


def _dump(obj, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default))


def _meta(extra: dict | None = None) -> dict:
    m = {
        "generated_by": "06-AI自动化/01-工作流/openmath_ingest.py",
        "generated_at": _stamp(),
        "provenance": {
            "ai_assisted": True,
            "note": "由 AI 代理基于 openmath_sys 引擎自动生成，未经人类复核，不得作为 L3+ 证据。",
        },
        "evidence_level": {
            "catalog": "L0",
            "analysis": "L2",
            "proof": "L4-NOT_ACHIEVED",
            "note": "本流水线不产出 L4 证明；方程求解仅为数值/符号计算校验(L2)。",
        },
        "honesty": (
            "本文件为 L0/L2 级数据处理产物，非证明；方程求解为计算校验(L2)。"
            "CD 性质(CMP)解析成功不代表被证明；arXiv 论文为预印本，状态 UNVERIFIED。"
        ),
    }
    if extra:
        m.update(extra)
    return m


def _cds_dir() -> str:
    return os.path.join(REPO, "09-数据", "openmath_cds")


def _read_local(name: str) -> str | None:
    """读取本地已有 CD 快照；不存在或损坏则返回 None。"""
    p = os.path.join(_cds_dir(), f"{name}.ocd")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# 1) 下载并整理 OpenMath CD
# ---------------------------------------------------------------------------
def ingest_cds() -> dict:
    os.makedirs(_cds_dir(), exist_ok=True)
    catalog: list[dict] = []

    for name in CD_NAMES:
        raw = fetch_openmath_cd_raw(name, timeout=10)
        origin = "network" if raw else None
        if not raw:
            # 联网失败 -> 回退本地已有快照，避免已入库 CD 被记成符号数 0（数据倒退）
            raw = _read_local(name)
            origin = "local_snapshot" if raw else None

        entry = {
            "name": name,
            "source_url": CD_BASE_URL.format(name=name),
            "fetched": raw is not None,
            "origin": origin,
            "symbols": [],
            "symbol_count": 0,
            "property_count": 0,
            "parse_error": None,
        }
        if raw:
            if origin == "network":
                with open(os.path.join(_cds_dir(), f"{name}.ocd"), "w", encoding="utf-8") as f:
                    f.write(raw)
            try:
                syms = parse_ocd(raw)
            except Exception as e:  # noqa: BLE001
                # 单个 CD 结构异常不应中断整条流水线；如实记录
                syms = []
                entry["parse_error"] = f"{type(e).__name__}: {e}"
            entry["symbols"] = [
                {"name": s.name, "description": s.description, "n_properties": len(s.properties)}
                for s in syms
            ]
            entry["symbol_count"] = len(syms)
            entry["property_count"] = sum(len(s.properties) for s in syms)
        catalog.append(entry)

    net = sum(1 for e in catalog if e["origin"] == "network")
    loc = sum(1 for e in catalog if e["origin"] == "local_snapshot")
    miss = sum(1 for e in catalog if e["origin"] is None)
    pfail = sum(1 for e in catalog if e["parse_error"])
    return {
        "meta": _meta({
            "coverage": {
                "official_total": OFFICIAL_CD_TOTAL,
                "from_network": net,
                "from_local_snapshot": loc,
                "missing": miss,
                "xml_parse_failed": pfail,
                "note": (
                    "官方全量清单由 GitHub API 探测得到；联网失败者回退本地快照，"
                    "两者皆无才记为 missing；解析失败如实记录，不静默丢弃。"
                ),
            }
        }),
        "cds": catalog,
    }


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
    cmp_total = 0
    cmp_equation_like = 0
    cmp_parsed = 0
    equations: list[dict] = []
    seen_raw: set[str] = set()
    unparsed_samples: list[dict] = []

    def try_add(raw: str, source: str):
        nonlocal cmp_parsed, cmp_equation_like
        if raw in seen_raw:
            return
        if not any(op in raw for op in ["=", "<=", ">=", "!=", "<", ">"]):
            return
        if not any(c.isalpha() for c in raw):
            return
        # 仅通过「含关系运算符且含字母」筛选的 CMP 计为方程型候选
        cmp_equation_like += 1
        rec = parse_text(raw)
        if not rec.parse_ok:
            # 保留反例样本（诚实红线：不静默删除）
            if len(unparsed_samples) < UNPARSED_SAMPLE_CAP:
                unparsed_samples.append({"raw": raw, "source": source})
            return
        cmp_parsed += 1
        seen_raw.add(raw)
        equations.append({"raw": raw, "source": source})

    # 优先读本地快照，离线也可重跑；本地缺失再回退联网
    for cd in cds_catalog["cds"]:
        name = cd["name"]
        raw = _read_local(name) or fetch_openmath_cd_raw(name, timeout=10)
        if not raw:
            continue
        try:
            syms = parse_ocd(raw)
        except Exception:  # noqa: BLE001
            continue
        for s in syms:
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
            "cmp_equation_like": cmp_equation_like,
            "cmp_parsed": cmp_parsed,
            "parsed_rate": round(cmp_parsed / cmp_total, 4) if cmp_total else 0.0,
            "parsed_rate_equation_like": (
                round(cmp_parsed / cmp_equation_like, 4) if cmp_equation_like else 0.0
            ),
            "note": (
                "parsed_rate 分母为全部 CMP（含自然语言描述型），故偏低；"
                "parsed_rate_equation_like 仅统计通过「含关系运算符且含字母」筛选的"
                "方程型 CMP，更能反映解析器真实能力。两者均不代表被证明(L4)。"
            ),
        },
        "unparsed_samples": {
            "count_capped": len(unparsed_samples),
            "cap": UNPARSED_SAMPLE_CAP,
            "samples": unparsed_samples,
            "note": "解析失败的 CMP 反例样本（上限截断），按诚实红线保留并标注，不静默删除。",
        },
        "equations_analyzed": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def _load_prev_stats() -> dict | None:
    """读取上一轮产物作为增量基线；无上一轮产物则返回 None。"""
    cat_path = os.path.join(_cds_dir(), "catalog.json")
    ana_path = os.path.join(REPO, "09-数据", "openmath_4d_analysis.json")
    prev: dict = {}
    try:
        with open(cat_path, encoding="utf-8") as f:
            cat = json.load(f)
        lst = cat.get("cds", [])
        cov = cat.get("meta", {}).get("coverage", {})
        prev["cd_count"] = cov.get("from_network", sum(1 for c in lst if c.get("fetched")))
        prev["symbols"] = sum(c.get("symbol_count", 0) for c in lst)
    except Exception:  # noqa: BLE001
        return None
    try:
        with open(ana_path, encoding="utf-8") as f:
            ana = json.load(f)
        prev["rate"] = ana.get("coverage", {}).get("parsed_rate")
    except Exception:  # noqa: BLE001
        prev["rate"] = None
    return prev


def main() -> int:
    print("[流水线] 启动 OpenMath 自动摄取（AI 辅助，需人类复核）")
    engine = FourDimLogicEngine()

    prev = _load_prev_stats()

    cds = ingest_cds()
    cov = cds["meta"]["coverage"]
    total_sym = sum(c["symbol_count"] for c in cds["cds"])
    print(f"[1/3] CD 下载整理：官方 {cov['official_total']} 个；联网 {cov['from_network']}、"
          f"本地回退 {cov['from_local_snapshot']}、缺失 {cov['missing']}；"
          f"符号 {total_sym} 个（XML 解析失败 {cov['xml_parse_failed']}）")

    papers = ingest_papers()
    print(f"[2/3] 论文下载整理：去重后 {papers['stats']['total']} 篇")

    analysis = analyze(cds, engine)
    print(f"[3/3] 四维分析：CMP 可解析 {analysis['coverage']['cmp_parsed']}"
          f"/{analysis['coverage']['cmp_total']}"
          f"({analysis['coverage']['parsed_rate']})；方程型口径 "
          f"{analysis['coverage']['cmp_parsed']}/{analysis['coverage']['cmp_equation_like']}"
          f"({analysis['coverage']['parsed_rate_equation_like']})；"
          f"分析方程 {analysis['equations_analyzed']} 条")

    # 写盘
    _dump(cds, os.path.join(_cds_dir(), "catalog.json"))
    _dump(papers, os.path.join(REPO, "10-文献与索引", "arxiv_index.json"))
    _dump(analysis, os.path.join(REPO, "09-数据", "openmath_4d_analysis.json"))

    _write_report(cds, papers, analysis, prev)
    print("[完成] 产物已写入 09-数据/ 与 10-文献与索引/，报告见 06-AI自动化/01-工作流/RUN_REPORT.md")
    return 0


def _write_report(cds: dict, papers: dict, analysis: dict, prev: dict | None) -> None:
    cov = cds["meta"]["coverage"]
    lines = [
        "# OpenMath 自动摄取 · 运行报告",
        "",
        f"- 生成时间：{_stamp()}",
        "- 性质：AI 辅助自动生成，**未经人类复核**，不构成证明。",
        "",
        "## 1. 内容字典(CD) 摄取",
        f"- 官方全量 {cov['official_total']} 个；联网抓取 {cov['from_network']} 个；"
        f"本地快照回退 {cov['from_local_snapshot']} 个；缺失 {cov['missing']} 个；"
        f"XML 解析失败 {cov['xml_parse_failed']} 个。",
        f"- 符号合计 {sum(c['symbol_count'] for c in cds['cds'])} 个。",
        "",
    ]

    miss = [c["name"] for c in cds["cds"] if c["origin"] is None]
    if miss:
        lines.append(f"- 缺失（联网与本地均无）：{', '.join(miss)}")
    loc = [c["name"] for c in cds["cds"] if c["origin"] == "local_snapshot"]
    if loc:
        lines.append(f"- 走本地快照回退：{', '.join(loc)}")
    pfail = [c["name"] for c in cds["cds"] if c["parse_error"]]
    if pfail:
        lines.append(f"- XML 解析失败（如实记录）：{', '.join(pfail)}")
    lines.append("")

    lines += [
        "## 2. 论文索引",
        f"- 去重后 {papers['stats']['total']} 篇；分类分布见 arxiv_index.json。",
        "- 注意：arXiv 预印本 `fact_check.status = UNVERIFIED`，不得作为 L3+ 证据。",
        "",
        "## 3. 四维逻辑分析",
        f"- CD 性质(CMP)可解析 {analysis['coverage']['cmp_parsed']}"
        f"/{analysis['coverage']['cmp_total']}（率 {analysis['coverage']['parsed_rate']}，"
        f"分母含自然语言描述型 CMP）。",
        f"- 其中方程型 CMP（含关系运算符且含字母）{analysis['coverage']['cmp_equation_like']} 条，"
        f"可解析率 {analysis['coverage']['parsed_rate_equation_like']}"
        f"（更能反映解析器真实能力）。",
        f"- 共分析方程 {analysis['equations_analyzed']} 条（含内置种子）。",
        f"- 未解析 CMP 反例保留 {len(analysis['unparsed_samples']['samples'])} 条"
        f"（上限 {analysis['unparsed_samples']['cap']}），按诚实红线保留并标注。",
        "- 方程求解为计算校验(L2)，非证明(L4)。",
        "",
        "## 4. 与上一轮对比（增量）",
    ]
    if prev:
        lines += [
            f"- CD 入册数：{prev.get('cd_count')} → {cov['from_network'] + cov['from_local_snapshot']}",
            f"- 符号数：{prev.get('symbols')} → {sum(c['symbol_count'] for c in cds['cds'])}",
            f"- CMP 可解析率：{prev.get('rate')} → {analysis['coverage']['parsed_rate']}",
        ]
    else:
        lines.append("- 无上一轮基线（首次运行）。")
    lines.append("")

    lines += [
        "## 5. 产物清单",
        "- `09-数据/openmath_cds/<name>.ocd` 原始快照",
        "- `09-数据/openmath_cds/catalog.json` 符号目录",
        "- `09-数据/openmath_4d_analysis.json` 四维分析",
        "- `10-文献与索引/arxiv_index.json` 论文索引",
    ]
    with open(os.path.join(_HERE, "RUN_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
