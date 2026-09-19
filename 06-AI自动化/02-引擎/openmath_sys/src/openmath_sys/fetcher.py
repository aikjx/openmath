"""论文与 OpenMath 内容字典检索模块。

- 论文：优先通过 arXiv API (export.arxiv.org) 检索数学类论文，
  按关键词相关度 + 时效做启发式排序（"优质"为启发式近似，非权威影响因子）。
- OpenMath CD：解析 .ocd XML 提取符号定义；网络不可用时回退到内置样例。
所有网络调用均带超时与异常兜底，保证系统离线可运行。
"""
from __future__ import annotations

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Iterable

from .models import OMSymbol, Paper

_SAMPLE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "sample_data")
)


# ===========================================================================
# arXiv 论文检索
# ===========================================================================
def fetch_arxiv(query: str, max_results: int = 10, timeout: int = 8) -> list[Paper]:
    try:
        url = ("http://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(f"all:{query}")
               + f"&start=0&max_results={max_results}&sortBy=relevance")
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8")
        return parse_arxiv_atom(xml_text)
    except Exception as e:  # noqa: BLE001
        # 网络不可用 -> 回退到内置样例
        sample = load_bundled_arxiv()
        return rank_papers(sample, query.split())


def parse_arxiv_atom(xml_text: str) -> list[Paper]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []
    for entry in root.findall("a:entry", ns):
        pid = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
        title = " ".join((entry.findtext("a:title", default="", namespaces=ns) or "").split())
        summary = " ".join((entry.findtext("a:summary", default="", namespaces=ns) or "").split())
        authors = [a.findtext("a:name", default="", namespaces=ns).strip()
                   for a in entry.findall("a:author", ns)]
        published = (entry.findtext("a:published", default="", namespaces=ns) or "").strip()
        cats = [c.get("term") for c in entry.findall("a:category", ns) if c.get("term")]
        pdf = None
        for l in entry.findall("a:link", ns):
            if l.get("title") == "pdf":
                pdf = l.get("href")
        papers.append(Paper(paper_id=pid, title=title, authors=authors,
                            summary=summary, url=pid, pdf_url=pdf,
                            published=published, categories=cats or []))
    return papers


def rank_papers(papers: list[Paper], keywords: Iterable[str]) -> list[Paper]:
    kws = [k.lower() for k in keywords if k]
    for p in papers:
        text = (p.title + " " + p.summary).lower()
        score = sum(text.count(k) for k in kws)
        # 时效轻微加权
        if p.published and p.published >= "2020":
            score += 0.5
        p.score = round(score, 3)
    return sorted(papers, key=lambda x: x.score, reverse=True)


def load_bundled_arxiv() -> list[Paper]:
    path = os.path.join(_SAMPLE_DIR, "arxiv_sample.xml")
    if os.path.exists(path):
        return parse_arxiv_atom(open(path, encoding="utf-8").read())
    return []


# ===========================================================================
# OpenMath 内容字典检索
# ===========================================================================
_CD_BASE = "https://raw.githubusercontent.com/OpenMath/CDs/master/cd/Official/{name}.ocd"


def fetch_openmath_cd_raw(name: str, timeout: int = 8) -> str | None:
    """下载某个 OpenMath 内容字典的原始 .ocd XML 文本；失败返回 None。"""
    try:
        url = _CD_BASE.format(name=name)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception:  # noqa: BLE001
        # 回退到内置样例（仅 arith1 有样例）
        path = os.path.join(_SAMPLE_DIR, f"{name}.ocd")
        if os.path.exists(path):
            return open(path, encoding="utf-8").read()
        return None


def fetch_openmath_cd(name: str, timeout: int = 8) -> list[OMSymbol]:
    raw = fetch_openmath_cd_raw(name, timeout=timeout)
    if raw:
        return parse_ocd(raw)
    return []


def parse_ocd(xml_text: str) -> list[OMSymbol]:
    root = ET.fromstring(xml_text)

    def local(el) -> str:
        return el.tag.split("}")[-1]

    cd_name = "unknown"
    for el in root.iter():
        if local(el) == "CDName" and el.text:
            cd_name = el.text.strip()
            break

    syms: list[OMSymbol] = []
    for el in root.iter():
        if local(el) != "CDDefinition":
            continue
        nm = None
        desc = ""
        props: list[str] = []
        for child in el:
            t = local(child)
            if t == "Name" and child.text:
                nm = child.text.strip()
            elif t == "Description" and child.text:
                desc = " ".join(child.text.split())
            elif t == "CMP" and child.text:
                props.append(" ".join(child.text.split()))
        if nm:
            syms.append(OMSymbol(name=nm, cd=cd_name, description=desc, properties=props))
    return syms
