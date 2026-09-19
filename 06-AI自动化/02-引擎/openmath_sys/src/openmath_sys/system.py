"""总编排器：把检索、解析、四维推理、最高权限调度串联为统一流水线。"""
from __future__ import annotations

import json
import os
from typing import Iterable

from .models import Authority, LogicRecord, OMSymbol, Paper
from .fetcher import fetch_arxiv, fetch_openmath_cd
from .logic_framework import FourDimLogicEngine
from .scheduler import build_default_alliance
from .knowledge import KnowledgeBase


class OpenMathProcessor:
    def __init__(self, cds: Iterable[str] | None = None) -> None:
        self.kb = KnowledgeBase()
        self.engine = FourDimLogicEngine()
        self.alliance = build_default_alliance()
        self.papers: list[Paper] = []
        # 预载常用 OpenMath CD 语义
        for name in (cds or ["arith1", "relation1", "transc1"]):
            syms = fetch_openmath_cd(name)
            if syms:
                self.kb.add_symbols(syms)
        self.engine.symbol_table = self.kb.symbol_table()

    # --- 1) 论文获取 -------------------------------------------------------
    def acquire_papers(self, query: str, max_results: int = 8) -> list[Paper]:
        self.papers = fetch_arxiv(query, max_results=max_results)
        return self.papers

    # --- 2) 方程解析 + 3) 四维推理 ---------------------------------------
    def reason_over(self, expressions: Iterable[str]) -> list[LogicRecord]:
        records: list[LogicRecord] = []
        for raw in expressions:
            rec = self.engine.process(raw, self.kb.symbol_table())
            self.kb.add_record(rec)
            records.append(rec)
        return records

    # --- 4) 最高权限算法调度 ---------------------------------------------
    def run_alliance(self, records: list[LogicRecord],
                     mode: Authority = Authority.SUPREME) -> list[list]:
        return [self.alliance.dispatch(rec, mode) for rec in records]

    # --- 汇总导出 ---------------------------------------------------------
    def export(self, out_dir: str) -> dict:
        os.makedirs(out_dir, exist_ok=True)
        kb_path = os.path.join(out_dir, "knowledge.json")
        self.kb.export(kb_path)
        papers_path = os.path.join(out_dir, "papers.json")
        with open(papers_path, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self.papers], f, ensure_ascii=False, indent=2)
        return {"knowledge": kb_path, "papers": papers_path}
