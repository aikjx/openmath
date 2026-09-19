"""知识库：汇集 OpenMath 符号语义与已处理的四维推理记录。"""
from __future__ import annotations

import json
import os
from typing import Iterable

from .models import LogicRecord, OMSymbol


class KnowledgeBase:
    def __init__(self) -> None:
        self.symbols: dict[str, OMSymbol] = {}
        self.records: list[LogicRecord] = []

    def add_symbols(self, syms: Iterable[OMSymbol]) -> None:
        for s in syms:
            self.symbols[s.name] = s

    def add_record(self, rec: LogicRecord) -> None:
        self.records.append(rec)

    def symbol_table(self) -> dict[str, OMSymbol]:
        return self.symbols

    def export(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {
            "symbols": [s.to_dict() for s in self.symbols.values()],
            "records": [r.to_dict() for r in self.records],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
