# -*- coding: utf-8 -*-
"""Parse the pinned metadata mirror of https://github.com/openai/math into a table ledger.

Inputs (_镜像/, read-only): CONTENTS.md, overview.tex, formalization.yaml, history.md, README.md
Outputs (_生成/): families.csv, manuscripts.csv, by_subject.csv, stats.txt

Every aggregate quoted by the analysis documents is printed by this script into stats.txt.
Run:  python _脚本/parse_openai_math.py
"""
from __future__ import print_function

import csv
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MIRROR = os.path.join(ROOT, "_镜像")
OUT = os.path.join(ROOT, "_生成")

CONTENTS = os.path.join(MIRROR, "CONTENTS.md")
OVERVIEW = os.path.join(MIRROR, "overview.tex")
FORMAL = os.path.join(MIRROR, "formalization.yaml")
HISTORY = os.path.join(MIRROR, "history.md")
README = os.path.join(MIRROR, "README.md")
LEANREADME = os.path.join(MIRROR, "lean-README.md")


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_text(path):
    return read_bytes(path).decode("utf-8", "replace")


def brace_arg(text, pos):
    """text[pos] must be '{'. Return (inner_text, index_after_closing_brace)."""
    assert text[pos] == "{"
    depth = 0
    start = pos + 1
    i = pos
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    raise ValueError("unbalanced brace at %d" % pos)


def tex_args(line, n):
    out = []
    i = 0
    for _ in range(n):
        while i < len(line) and line[i] != "{":
            i += 1
        if i >= len(line):
            return None
        val, i = brace_arg(line, i)
        out.append(val)
    return out


def parse_overview():
    """Return (subject_of_family {id: subject}, entry_title {id: title}, ordered subjects)."""
    text = read_text(OVERVIEW)
    subject_of = {}
    title_of = {}
    order = []
    current = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"\\cataloguesection\{", s)
        if m:
            args = tex_args(s[m.end() - 1:], 2)
            current = args[0]
            order.append((current, int(args[1])))
            continue
        if s.startswith("\\resultentry{"):
            args = tex_args(s[len("\\resultentry"):], 4)
            if args is None:
                raise ValueError("malformed resultentry: " + s[:80])
            fid = args[0]
            title_of[fid] = args[1]
            if current is None:
                raise ValueError("resultentry %s before any section" % fid)
            subject_of[fid] = current
    return subject_of, title_of, order


def md_links(line):
    """Extract every [text](target) pair from one line.

    Regex alternatives were tried and rejected: a non-greedy `\\((.*?)\\)` truncates the
    one path that contains a paren (preprints/Sharp-integral-fillings-in-CAT(0)-spaces-...)
    and a greedy one refuses the single line whose link is followed by prose
    ('-- secondary writeup'), so the count silently changes with the ruler. Depth matching
    reads both. Returns list of (text, target) plus the number of links found.
    """
    out = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] != "[":
            i += 1
            continue
        j = i + 1
        while j < n and line[j] != "]":
            j += 1
        if j >= n or j + 1 >= n or line[j + 1] != "(":
            i += 1
            continue
        k = j + 2
        depth = 1
        while k < n and depth:
            if line[k] == "(":
                depth += 1
            elif line[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if depth:
            i = j + 2
            continue
        out.append((line[i + 1:j], line[j + 2:k]))
        i = k + 1
    return out


def parse_contents():
    """Return (families, manuscripts, diagnostics)."""
    text = read_text(CONTENTS)
    lines = text.splitlines()
    families = []
    manuscripts = []
    head_re = re.compile(r"^\*\*(\d{3})\.\s*(.+?)\.\*\*\s*(.*)$")
    lean_re = re.compile(r"lean/docs/(\d{3})\.md")
    seen = {}
    emsp_lines = []
    link_marker_total = 0
    link_anomalies = []
    cur = None
    for idx, raw in enumerate(lines):
        m = head_re.match(raw)
        if m:
            fid, title, rest = m.group(1), m.group(2), m.group(3)
            lean = sorted(set(lean_re.findall(rest)))
            if fid in seen:
                raise ValueError("duplicate family id %s at line %d" % (fid, idx + 1))
            seen[fid] = True
            cur = {
                "family": fid,
                "title": title,
                "head_line": idx + 1,
                "lean_doc_in_head": lean[0] if len(lean) == 1 else ("MULTI:" + ",".join(lean) if lean else ""),
                "n_lean_refs_in_head": len(lean),
                "description_len": len(rest),
                "head_text": raw,
                "n_manuscripts": 0,
            }
            families.append(cur)
            continue
        if raw.startswith("&emsp;"):
            links = md_links(raw)
            emsp_lines.append(idx + 1)
            link_marker_total += raw.count("](")
            if len(links) != 1:
                link_anomalies.append("line %d: %d links" % (idx + 1, len(links)))
            for title, path in links:
                entry = {
                    "family": cur["family"] if cur else "",
                    "title": title,
                    "path": path,
                    "dir": path.split("/")[1] if path.startswith("preprints/") and "/" in path[11:] else "",
                    "line": idx + 1,
                }
                if cur is not None:
                    cur["n_manuscripts"] += 1
                manuscripts.append(entry)
    # per-family lean docs: the lean/docs/NNN.md reference in that family's head line
    doc_refs = sorted(set(re.findall(r"lean/docs/(\d{3})\.md", text)))
    head_lean = {}
    for fam in families:
        ref = fam["lean_doc_in_head"]
        if ref and not ref.startswith("MULTI:"):
            head_lean[fam["family"]] = ref
    emsp_texts = [l for l in lines if l.startswith("&emsp;")]
    ng = re.compile(r"^&emsp;\[(.*?)\]\((.*?)\)")
    gr = re.compile(r"^&emsp;\[(.*?)\]\((.*)\)\s*$")
    ng_paths = set(ng.match(t).group(2) for t in emsp_texts if ng.match(t))
    gr_paths = set(gr.match(t).group(2) for t in emsp_texts if gr.match(t))
    depth_paths = set(m["path"] for m in manuscripts)
    diagnostics = {
        "family_head_lines": len(families),
        "ruler_nongreedy_lines": sum(1 for t in emsp_texts if ng.match(t)),
        "ruler_greedy_lines": sum(1 for t in emsp_texts if gr.match(t)),
        "ruler_nongreedy_paths": len(ng_paths),
        "ruler_greedy_paths": len(gr_paths),
        "ruler_B_minus_C": len(ng_paths - gr_paths),
        "ruler_C_minus_B": len(gr_paths - ng_paths),
        "ruler_depth_paths": len(depth_paths),
        "paths_nongreedy": sorted(ng_paths),
        "paths_greedy": sorted(gr_paths),
        "paths_depth": sorted(depth_paths),
        "emsp_lines": len(emsp_texts),
        "link_marker_total": link_marker_total,
        "link_anomalies": link_anomalies,
        "manuscript_link_lines": len(manuscripts),
        "lean_ref_number_mismatches": [
            "%s->%s" % (f["family"], f["lean_doc_in_head"]) for f in families
            if f["lean_doc_in_head"] and not f["lean_doc_in_head"].startswith("MULTI:")
            and f["lean_doc_in_head"] != f["family"]],
        "distinct_lean_doc_files_referenced": len(doc_refs),
        "families_with_lean_doc_in_head": len(head_lean),
        "doc_ref_numbers_set": doc_refs,
    }
    return families, manuscripts, diagnostics, head_lean


def parse_formalization():
    text = read_text(FORMAL)
    lines = text.splitlines()
    sources = []
    main_results = []
    related = []
    section = None
    cur = {}
    for raw in lines:
        if re.match(r"^[a-z_]+:", raw):
            section = raw.split(":")[0]
            continue
        s = raw.strip()
        if section == "sources" and s.startswith("- title:"):
            if cur:
                sources.append(cur)
            cur = {"title": s[len("- title:"):].strip().strip('"')}
        elif section == "sources" and s.startswith("id:") and cur:
            cur["id"] = s[len("id:"):].strip()
            cur["date"] = ""
            mm = re.search(r"(\w+-\d+-\d{4})", cur.get("id", ""))
            if mm:
                cur["date"] = mm.group(1)
            cur["in_preprints"] = cur["id"].startswith("../preprints/")
        elif section == "related_formalizations" and s.startswith("- id:"):
            related.append(s[len("- id:"):].strip())
        elif section == "status" and s.startswith("- comparator_config:"):
            if cur and cur.get("section") == "main_results":
                pass
            main_results.append({"comparator_config": s[len("- comparator_config:"):].strip()})
            cur = {"section": "main_results"}
        elif section == "status" and s.startswith("declaration:") and main_results:
            main_results[-1]["declaration"] = s[len("declaration:"):].strip()
        elif section == "status" and s.startswith("file:") and main_results:
            main_results[-1]["file"] = s[len("file:"):].strip()
    if cur and sources and "id" not in sources[-1]:
        pass
    # last source
    return sources, main_results, related


def parse_tree_paths():
    """Read the pinned physical-layer carrier (_镜像/git_paths.txt.gz).

    Produced by: git -c core.quotepath=false ls-tree -r --name-only HEAD
    of a blob:none shallow clone at commit fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb.
    """
    import gzip
    path = os.path.join(MIRROR, "git_paths.txt.gz")
    if not os.path.exists(path):
        return None
    with gzip.open(path, "rb") as fh:
        return [l.decode("utf-8").rstrip("\n") for l in fh.read().split(b"\n") if l.strip()]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    subject_of, entry_title, subject_order = parse_overview()
    families, manuscripts, diag, head_lean = parse_contents()
    sources, main_results, related = parse_formalization()

    fam_ids_contents = [f["family"] for f in families]
    fam_ids_overview = sorted(subject_of.keys())
    only_contents = sorted(set(fam_ids_contents) - set(fam_ids_overview))
    only_overview = sorted(set(fam_ids_overview) - set(fam_ids_contents))
    declared_range = "%s..%s" % (fam_ids_contents[0], fam_ids_contents[-1]) if fam_ids_contents else "empty"
    gap = [i for i in range(1, len(fam_ids_contents) + 1)
           if "%03d" % i not in set(fam_ids_contents)]

    formalized_families = sorted(set(head_lean))
    subject_family = {}
    for fid, subj in subject_of.items():
        subject_family.setdefault(subj, []).append(fid)

    with open(os.path.join(OUT, "families.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "subject", "title_overview", "title_contents",
                    "n_manuscripts", "lean_doc", "formalized", "head_line_in_contents"])
        for f in families:
            fid = f["family"]
            w.writerow([fid, subject_of.get(fid, ""), entry_title.get(fid, ""), f["title"],
                        f["n_manuscripts"], head_lean.get(fid, ""),
                        "YES" if fid in head_lean else "no", f["head_line"]])

    with open(os.path.join(OUT, "manuscripts.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "manuscript_title", "path", "dir_date", "line"])
        for m in manuscripts:
            w.writerow([m["family"], m["title"], m["path"], m["dir"], m["line"]])

    subj_dates = {}
    for m in manuscripts:
        mm = re.search(r"([A-Za-z]+-\d{1,2}-\d{4})$", m["dir"])
        d = mm.group(1) if mm else "unknown"
        subj = subject_of.get(m["family"], "unmapped")
        subj_dates.setdefault(subj, set()).add(d)

    with open(os.path.join(OUT, "by_subject.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["subject", "n_families", "n_manuscripts", "n_formalized_families",
                    "manuscript_dates"])
        for subj, _ in subject_order:
            fams = subject_family.get(subj, [])
            n_man = sum(f["n_manuscripts"] for f in families if f["family"] in set(fams))
            n_for = sum(1 for x in fams if x in head_lean)
            w.writerow([subj, len(fams), n_man, n_for,
                        "; ".join(sorted(subj_dates.get(subj, [])))])

    stats_path = os.path.join(OUT, "stats.txt")
    buf = io.StringIO()
    p = lambda *a: print(*a, file=buf)
    p("PARSE STATS -- generated by _脚本/parse_openai_math.py, do not edit")
    p("inputs (bytes/lines):")
    for path in (CONTENTS, OVERVIEW, FORMAL, HISTORY, README, LEANREADME):
        b = read_bytes(path)
        p("  %-22s %9d B  %6d lines  md5 %s" % (os.path.basename(path), len(b),
                                                 b.count(b"\n") + 1,
                                                 __import__("hashlib").md5(b).hexdigest()[:12]))
    p("")
    p("A. catalogue scale")
    p("  families parsed from CONTENTS.md head lines : %d   (%s)" % (diag["family_head_lines"], declared_range))
    p("  families parsed from overview.tex entries   : %d" % len(fam_ids_overview))
    p("  contiguous 001..N gaps in CONTENTS numbering: %s" % (gap if gap else "none"))
    p("  ids only in CONTENTS (not in overview)      : %s" % (only_contents if only_contents else "none"))
    p("  ids only in overview (not in CONTENTS)      : %s" % (only_overview if only_overview else "none"))
    p("  manuscript links (paren-depth matcher)      : %d" % diag["manuscript_link_lines"])
    p("  -- the same census under three rulers, computed here, not narrated:")
    p("     ruler A: lines starting with the indent marker : %d" % diag["emsp_lines"])
    p("     ruler B: non-greedy regex  \\((.*?)\\) matches   : %d" % diag["ruler_nongreedy_lines"])
    p("     ruler C: anchored greedy \\((.*)\\)$  matches     : %d" % diag["ruler_greedy_lines"])
    p("     distinct paths under B / C                       : %d / %d" % (
        diag["ruler_nongreedy_paths"], diag["ruler_greedy_paths"]))
    p("     paths in B but not C / in C but not B            : %d / %d" % (
        diag["ruler_B_minus_C"], diag["ruler_C_minus_B"]))
    p("     distinct paths under B / C / depth-matcher       : %d / %d / %d" % (
        diag["ruler_nongreedy_paths"], diag["ruler_greedy_paths"], diag["ruler_depth_paths"]))
    p("     literal '](' markers on those lines              : %d" % diag["link_marker_total"])
    p("     lines whose extracted link count != 1            : %s" % (diag["link_anomalies"] or "none"))
    p("  subject sections in overview.tex            : %d" % len(subject_order))
    p("  families with zero manuscripts              : %d" % sum(1 for f in families if f["n_manuscripts"] == 0))
    p("  manuscripts per family: min %d / max %d / mean %.2f" % (
        min(f["n_manuscripts"] for f in families), max(f["n_manuscripts"] for f in families),
        sum(f["n_manuscripts"] for f in families) / float(len(families))))
    p("  README.md asserts 719 manuscripts / 372 families; overview.tex asserts the same in its title block")
    p("")
    p("B. formalization ledger")
    p("  distinct lean/docs/NNN.md files referenced  : %d" % diag["distinct_lean_doc_files_referenced"])
    p("  families whose head cites a lean doc        : %d" % diag["families_with_lean_doc_in_head"])
    p("  families with MULTI lean refs in head       : %d" % sum(1 for f in families
                                                                if f["lean_doc_in_head"].startswith("MULTI:")))
    p("  formalization.yaml `sources:` titles        : %d" % len(sources))
    p("  sources whose id starts with ../preprints/  : %d" % sum(1 for s in sources if s.get("in_preprints")))
    p("  formalization.yaml `status.main_results`     : %d" % len(main_results))
    p("  distinct comparator_config among them       : %d" % len(set(m.get("comparator_config") for m in main_results)))
    p("  distinct .lean files among them             : %d" % len(set(m.get("file") for m in main_results)))
    p("  heads whose lean/doc number != family number: %s" % (diag["lean_ref_number_mismatches"] or "none"))
    p("  related_formalizations (imported libs)      : %d" % len(related))
    p("  history.md claim                            : 300 / 719 = ~42% top-line results formalized")
    n_for_fam = diag["families_with_lean_doc_in_head"]
    sum_man_of_formalized = sum(f["n_manuscripts"] for f in families if f["family"] in head_lean)
    p("  -- can the numerator 300 be reproduced from ANY mirrored layer?")
    p("     families flagged with a lean doc          : %d" % n_for_fam)
    p("     lean/docs/*.md referenced                 : %d" % diag["distinct_lean_doc_files_referenced"])
    p("     formalization.yaml sources                : %d" % len(sources))
    p("     formalization.yaml main_results decls     : %d" % len(main_results))
    p("     manuscripts inside flagged families       : %d   <- candidate for '300'" % sum_man_of_formalized)
    p("     equality 300 == manuscripts-in-flagged-families ? %s" % (sum_man_of_formalized == 300))
    p("  rates under each reading of the denominator:")
    p("     flagged families / 372 families           : %d / 372 = %.4f" % (n_for_fam, n_for_fam / 372.0))
    p("     flagged families / 719 manuscripts        : %d / 719 = %.4f" % (n_for_fam, n_for_fam / 719.0))
    p("     manuscripts-in-flagged / 719              : %d / 719 = %.4f" % (sum_man_of_formalized, sum_man_of_formalized / 719.0))
    p("     README 'top-line results' == 372 families, so 300/719 mixes a manuscript-weighted"
      " numerator with the manuscript count while naming results; %d/372 = %.4f is the"
      " family-level rate and %.4f the manuscript-level one" % (
        n_for_fam, n_for_fam / 372.0, sum_man_of_formalized / 719.0))
    p("  computed %d/719 = %.4f (lean docs referenced, if one per formalized result)" % (
        diag["distinct_lean_doc_files_referenced"], diag["distinct_lean_doc_files_referenced"] / 719.0))
    p("")
    p("C. by subject (families / manuscripts / formalized families)")
    for subj, _ in subject_order:
        fams = subject_family.get(subj, [])
        n_man = sum(f["n_manuscripts"] for f in families if f["family"] in set(fams))
        n_for = sum(1 for x in fams if x in head_lean)
        p("  %-46s %3d %4d %3d" % (subj, len(fams), n_man, n_for))
    p("  TOTAL                                        %3d %4d %3d" % (
        sum(len(v) for v in subject_family.values()),
        sum(f["n_manuscripts"] for f in families),
        len(head_lean)))
    p("")
    p("D. manuscript date stamps in preprints/ dir names (top counts)")
    datecount = {}
    for m in manuscripts:
        mm = re.search(r"([A-Za-z]+-\d{1,2}-\d{4})$", m["dir"])
        if mm:
            datecount[mm.group(1)] = datecount.get(mm.group(1), 0) + 1
        else:
            datecount["(no date stamp)"] = datecount.get("(no date stamp)", 0) + 1
    for d, c in sorted(datecount.items(), key=lambda kv: (-kv[1], kv[0])):
        p("  %-24s %d" % (d, c))
    p("  distinct dir names                          : %d" % len(set(m["dir"] for m in manuscripts)))
    p("  distinct pdf basenames                      : %d" % len(set(m["path"].rsplit("/", 1)[-1] for m in manuscripts)))
    p("")
    p("E. number-theory families (subject == 'Number theory'), formalization flagged")
    for fid in sorted(subject_family.get("Number theory", []), key=lambda x: int(x)):
        fam = [f for f in families if f["family"] == fid][0]
        p("  %s  lean=%-4s m=%d  %s" % (fid, "Y" if fid in head_lean else "-",
                                    fam["n_manuscripts"], entry_title.get(fid, "")))
    p("")
    p("F. keyword index over CONTENTS.md family head lines (family, subject, title)")
    p("   SCAN SET: %d family head lines only (%d B). Abstracts, PDFs and .tex bodies are NOT scanned;" % (
        diag["family_head_lines"], sum(len(f["head_text"]) + 1 for f in families)))
    p("            a 0-hit row is a statement about the head lines, not about the collection.")
    keywords = ["goldbach", "chowla", "elliott", "prime gap", "twin", "sieve",
                "arithmetic progression", "squarefree", "square-free", "totient",
                "jacobsthal", "zero-free", "riemann", "zeta", "l-function", "dirichlet",
                "circle method", "additive", "multiplicative function", "partition",
                "erdos", "ramsey", "collatz", "abc conjecture", "bsd", "hodge",
                "liouville", "mobius", "density", "distribution of primes",
                "batalin", "maynard", "tao", "green",
                "prime pairs", "estermann", "chen", "binary goldbach", "weak goldbach",
                "vinogradov", "singular series", "hardy", "littlewood",
                "logarithmic averaging", "logarithmically", "pretentious",
                "siegel zero", "landau-siegel", "sumset", "cram",
                "erd", "\u0151s", "obius", "m\u00f6bius", "\u00f6",
                "landau", "siegel", "quasipolynomial", "szemeredi", "szemer\u00e9di"]
    for kw in sorted(set(keywords)):
        hits = []
        for f in families:
            if kw in f["head_text"].lower():
                fid = f["family"]
                hits.append("%s(%s%s)" % (fid, subject_of.get(fid, "?"),
                                          "L" if fid in head_lean else "-"))
        p("  %-24s %3d hits: %s" % (kw, len(hits), ", ".join(hits) if hits else "NONE"))
    p("")
    p("G. dependency / companion graph signal")
    p("  heads that cite another result number      : %d" % sum(
        1 for f in families if re.search(r"[Rr]esult \d{3}|\bwith result\b|Together with", f["head_text"])))
    p("  titles containing 'Counterexample'/'Refut' : %d" % sum(
        1 for f in families if re.search(r"counterexample|refut|fails|no such|negative",
                                         f["head_text"].lower())))
    p("  heads naming 'Lean' formalization link     : %d" % len(head_lean))
    p("")
    p("H. physical layer (_镜像/git_paths.txt.gz, commit fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb)")
    paths = parse_tree_paths()
    if paths is None:
        p("  CARRIER ABSENT -- git_paths.txt.gz not in _镜像/, section H makes NO claim")
    else:
        pathset = set(paths)
        bytop = {}
        for x in paths:
            bytop[x.split("/")[0] if "/" in x else "(root)"] = bytop.get(x.split("/")[0] if "/" in x else "(root)", 0) + 1
        p("  tracked files                                : %d" % len(paths))
        for k in sorted(bytop, key=lambda k: -bytop[k]):
            p("    %-24s %d" % (k, bytop[k]))
        lean = [x for x in paths if x.startswith("lean/")]
        sub = {}
        for x in lean:
            sub[x.split("/")[1] if x.count("/") > 1 else "(lean root file)"] = \
                sub.get(x.split("/")[1] if x.count("/") > 1 else "(lean root file)", 0) + 1
        p("  lean/ subdirs (top): %s" % ", ".join("%s=%d" % kv for kv in
                                                  sorted(sub.items(), key=lambda kv: -kv[1])[:8]))
        docs_on_disk = sorted(x[len("lean/docs/"):] for x in paths
                              if x.startswith("lean/docs/") and x.endswith(".md"))
        p("  lean/docs/*.md on disk                     : %d" % len(docs_on_disk))
        p("  lean/docs/*.md referenced by CONTENTS      : %d" % diag["distinct_lean_doc_files_referenced"])
        p("  referenced docs missing on disk            : %s" % (
            sorted(set(d + ".md" for d in sorted(set(head_lean.values()))) - set(docs_on_disk)) or "none"))
        p("  docs on disk NOT referenced by CONTENTS     : %d  e.g. %s" % (
            len(set(docs_on_disk) - set(d + ".md" for d in sorted(set(head_lean.values())))),
            ", ".join(sorted(set(docs_on_disk) - set(d + ".md" for d in sorted(set(head_lean.values()))))[:6])))
        cc_json = [x for x in paths if x.startswith("lean/ComparatorChallenges/") and x.endswith(".json")]
        cc_lean = [x for x in paths if x.startswith("lean/ComparatorChallenges/") and x.endswith(".lean")]
        p("  ComparatorChallenges .json / .lean         : %d / %d" % (len(cc_json), len(cc_lean)))
        p("  OAI/*.lean proof sources                   : %d" % len(
            [x for x in paths if x.startswith("lean/OAI/") and x.endswith(".lean")]))
        oai_all = [x for x in paths if x.startswith("lean/OAI/")]
        oai_ns = collections.Counter(x.split("/")[2] for x in oai_all if x.count("/") > 2)
        oai_ext = collections.Counter(x.rsplit(".", 1)[-1] for x in oai_all if "." in x.rsplit("/", 1)[-1])
        p("  OAI/ namespace dirs (3rd level)            : %d  top: %s" % (
            len(oai_ns), ", ".join("%s=%d" % kv for kv in oai_ns.most_common(5))))
        p("  OAI/ file extensions                       : %s" % ", ".join(
            "%s=%d" % kv for kv in oai_ext.most_common(5)))
        p("  OAI/ distinct basenames                    : %d  top: %s" % (
            len(set(x.rsplit("/", 1)[-1] for x in oai_all)),
            ", ".join("%s=%d" % kv for kv in
                      collections.Counter(x.rsplit("/", 1)[-1] for x in oai_all).most_common(4))))
        pre = [x for x in paths if x.startswith("preprints/")]
        pre_dirs = sorted(set(x.split("/")[1] for x in pre if x.count("/") >= 2))
        p("  preprints/ files / dirs                    : %d / %d" % (len(pre), len(pre_dirs)))
        per_dir = {}
        for x in pre:
            if x.count("/") >= 2:
                per_dir[x.split("/")[1]] = per_dir.get(x.split("/")[1], 0) + 1
        vals = sorted(per_dir.values())
        p("  files per preprint dir: min %d / max %d / median %d" % (
            vals[0], vals[-1], vals[len(vals) // 2]))
        p("  README.md files / distinct dirs            : %d / %d" % (
            len([x for x in pre if x.rsplit("/", 1)[-1] == "README.md"]),
            len(set(x.split("/")[1] for x in pre
                    if "README.md" in x.split("/")))))
        p("  dirs holding a .bib                        : %d" % len(
            set(x.split("/")[1] for x in pre if x.endswith(".bib"))))
        p("  dirs holding paper.pdf                     : %d" % len(
            set(x.split("/")[1] for x in pre if x.rsplit("/", 1)[-1] == "paper.pdf")))
        p("  .pdf files in preprints/                   : %d" % len([x for x in pre if x.endswith(".pdf")]))
        pdf_base = collections.Counter(x.rsplit("/", 1)[-1] for x in pre if x.endswith(".pdf"))
        p("  .pdf distinct basenames                    : %d  top: %s" % (
            len(pdf_base), ", ".join("%s=%d" % kv for kv in pdf_base.most_common(5))))
        p("  .tex files in preprints/                   : %d" % len([x for x in pre if x.endswith(".tex")]))
        linked_dirs = set(m["dir"] for m in manuscripts if m["dir"])
        linked_paths = set(m["path"] for m in manuscripts)
        p("  I0 which ruler reads the map? paths not present on disk:")
        for label, key in (("non-greedy regex", "paths_nongreedy"),
                           ("anchored greedy regex", "paths_greedy"),
                           ("paren-depth matcher", "paths_depth")):
            miss = sorted(set(diag[key]) - pathset)
            p("     %-22s %d paths, %d absent from disk  %s" % (
                label, len(diag[key]), len(miss),
                (miss[:1] and "e.g. " + miss[0][:78]) or "-- all present"))
        p("  I1 map->disk: CONTENTS manuscript paths missing on disk : %d  %s" % (
            len(linked_paths - pathset),
            ", ".join(sorted(linked_paths - pathset)[:4]) if linked_paths - pathset else ""))
        p("  I2 map->disk: CONTENTS preprint dirs absent from disk   : %d  %s" % (
            len(linked_dirs - set(pre_dirs)),
            ", ".join(sorted(linked_dirs - set(pre_dirs))[:4]) if linked_dirs - set(pre_dirs) else ""))
        p("  I3 disk->map: preprint dirs on disk but not in CONTENTS : %d" % len(set(pre_dirs) - linked_dirs))
        p("     first 12 not-in-CONTENTS dirs: %s" % ", ".join(sorted(set(pre_dirs) - linked_dirs)[:12]))
        # I3b: classify those dirs WITHOUT a hand-typed name list. The only key available in
        # the dir name itself is its trailing date stamp, so 'older edition' means: the
        # title-slug (name minus stamp) is ALSO the slug of a dir that CONTENTS does link.
        _MON = r"-(January|February|March|April|May|June|July|August|September|October|November|December)-\d{1,2}-\d{4}$"
        slug = lambda d: re.sub(_MON, "", d)
        undated = sorted(d for d in set(pre_dirs) - linked_dirs if slug(d) == d)
        editions = sorted(d for d in set(pre_dirs) - linked_dirs
                          if slug(d) != d and slug(d) in set(slug(x) for x in linked_dirs))
        orphan_titles = sorted(d for d in set(pre_dirs) - linked_dirs if d not in set(editions))
        p("     I3b same title-slug as a LINKED dir (older/other-date edition) : %d" % len(editions))
        p("     I3b title-slug NOT in the map at all (withdrawn or unmapped)   : %d" % len(orphan_titles))
        for d in orphan_titles:
            p("          - %s" % d)
        p("     I3b dirs whose name carries no date stamp (slug == name)       : %d  %s" % (
            len(undated), ", ".join(undated[:4]) if undated else "none"))
        p("     I3b sum check: editions + orphans == I3 ? %s   (linked dirs total %d)" % (
            len(editions) + len(orphan_titles) == len(set(pre_dirs) - linked_dirs), len(linked_dirs)))
        # I3c: does the classification agree with the change log's own named withdrawals?
        hist = open(os.path.join(MIRROR, "history.md"), encoding="utf-8").read()
        named = re.findall(r"^- (.+?)$", hist, re.M)
        norm2 = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        hits = []
        for n in named:
            key = norm2(n)
            hit = [d for d in orphan_titles if norm2(slug(d)) == key]
            hits.append((n[:46], "MATCHES an orphan dir" if hit else "no orphan-dir match"))
        p("  I3c history.md bullet lines (%d) vs the I3b orphan set:" % len(named))
        for n, v in hits:
            p("     %-48s %s" % (n, v))
        p("  I4 family-number gaps %s -- do their names still live on disk?" % gap)
        withdrawn = ["Weil-classes", "Kuga", "products-of-K3", "Hodge-conjecture-for-products"]
        for w in withdrawn:
            hits = [d for d in pre_dirs if w.lower().replace("-", "") in d.lower().replace("-", "")]
            p("     substring %-28s dirs: %s" % (w, hits if hits else "none"))
        p("  reasoning_traces/ files                    : %d" % len(
            [x for x in paths if x.startswith("reasoning_traces/")]))
        paren_paths = [x for x in paths if "(" in x]
        paren_dirs = sorted(set("/".join(x.split("/")[:2]) for x in paren_paths))
        p("  I5 paths containing '(' anywhere on disk   : %d  (lean/: %d, preprints/: %d)" % (
            len(paren_paths),
            len([x for x in paren_paths if x.startswith("lean/")]),
            len([x for x in paren_paths if x.startswith("preprints/")])))
        p("     dirs holding them                      : %s" % (
            ", ".join(paren_dirs) if paren_dirs else "NONE"))
        p("  reproducibility pins on disk:")
        for pin in ("lean/lean-toolchain", "lean/lake-manifest.json", "lean/lakefile.lean",
                    "lean/LICENSE", "lean/patches/README.md"):
            p("     %-26s : %s" % (pin, "PRESENT" if pin in pathset else "ABSENT"))
        for no_pin in ("flake.nix", "default.nix", "Dockerfile", ".dockerignore"):
            n = len([x for x in paths if x.rsplit("/", 1)[-1] == no_pin])
            p("     %-26s : %d (container/nix reproducibility: %s)" % (
                no_pin, n, "NONE" if n == 0 else "present"))
        patches = sorted(x for x in paths if x.startswith("lean/patches/") and x.endswith(".patch"))
        p("     lean/patches/*.patch             : %d" % len(patches))
        p("       %s" % ", ".join(x.rsplit("/", 1)[-1][:-6].split("-lean4")[0] for x in patches))
        p("     imported libs declared in formalization.yaml : %d" % len(related))
        norm = lambda s: s.lower().replace("-", "").replace("_", "")
        rel_blob = norm(" ".join(related))
        unlisted = [x.rsplit("/", 1)[-1][:-6].split("-lean4")[0] for x in patches
                    if norm(x.rsplit("/", 1)[-1][:-6].split("-lean4")[0]) not in rel_blob]
        p("     patched libs NOT findable in the declared list : %d  %s" % (
            len(unlisted), unlisted if unlisted else "(each patch name maps to a declared repo)"))
        with open(os.path.join(OUT, "preprint_dirs.csv"), "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dir", "n_files", "in_contents_map", "why_not_in_map", "families", "lean_docs"])
            for d in pre_dirs:
                fams = sorted(set(m["family"] for m in manuscripts if m["dir"] == d))
                why = "" if d in linked_dirs else (
                    "older_edition_same_title" if d in set(editions) else
                    ("no_date_stamp" if slug(d) == d else "title_not_in_map"))
                w.writerow([d, per_dir.get(d, 0), "YES" if d in linked_dirs else "no", why,
                            ";".join(fams),
                            ";".join(head_lean[x] for x in fams if x in head_lean)])
        # I6: text-hygiene census over the .md layer. It lives here because writing the
        # PROVENANCE 2b epilogue injected a real zero byte into a ledger file via an
        # unescaped escape sequence in a Python string literal. The ledger layer must be
        # zero-free; the mirrored upstream .md files are counted but not judged.
        def nul_scan(base):
            found = []
            for r, ds, fs in os.walk(base):
                for x in sorted(fs):
                    if x.endswith(".md"):
                        fp = os.path.join(r, x)
                        with open(fp, "rb") as fh:
                            found.append((os.path.relpath(fp, ROOT).replace(os.sep, "/"),
                                          fh.read().count(bytes([0]))))
            return found
        scan = nul_scan(ROOT)
        PM = "_镜像/PROVENANCE.md"
        ledger = [(n, c) for n, c in scan if not n.startswith("_镜像/") or n == PM]
        upstr = [(n, c) for n, c in scan if n.startswith("_镜像/") and n != PM]
        p("  I6 zero-byte census over the .md layer  : ledger=%d files NUL=%d | mirrored=%d files NUL=%d" % (
            len(ledger), sum(c for _, c in ledger), len(upstr), sum(c for _, c in upstr)))
        p("     ledger files census-ed               : %s" % ", ".join(n for n, _ in sorted(ledger)))
        p("     nonzero ledger files                 : %s" % (
            ", ".join("%s=%d" % t for t in ledger if t[1]) or "NONE"))
        p("     nonzero mirrored files               : %s" % (
            ", ".join("%s=%d" % t for t in upstr if t[1]) or "NONE"))
        bad_ledger = sum(c for _, c in ledger)
        p("     ==> %s" % (
            "DEFECT: the ledger layer must be zero-free (PROVENANCE 2b epilogue)" if bad_ledger
            else "LEDGER LAYER ZERO-FREE -- judgement made over %d files, not vacuous" % len(ledger)))
    p("")
    p("I. Comparator declarations census (_镜像/comparator_json/*.json, 416 configs fetched at the same pin)")
    CJ = os.path.join(MIRROR, "comparator_json")
    if not os.path.isdir(CJ):
        p("  CARRIER ABSENT -- section I makes NO claim")
    else:
        import json as _json
        cfgs = {}
        for name in sorted(os.listdir(CJ)):
            if name.endswith(".json"):
                with open(os.path.join(CJ, name), "rb") as fh:
                    cfgs[name[:-5]] = _json.loads(fh.read().decode("utf-8"))
        STD = ("propext", "Quot.sound", "Classical.choice")
        p("  configs parsed                          : %d" % len(cfgs))
        key_need = ("challenge_module", "solution_module", "theorem_names",
                    "permitted_axioms", "enable_nanoda")
        for k in key_need:
            p("  configs carrying '%-18s': %d" % (k + "'", sum(1 for c in cfgs.values() if k in c)))
        axiom_count = {}
        for c in cfgs.values():
            for a in c.get("permitted_axioms", []):
                axiom_count[a] = axiom_count.get(a, 0) + 1
        p("  distinct axiom names in the union       : %d -> %s" % (
            len(axiom_count), ", ".join("%s=%d" % kv for kv in sorted(axiom_count.items()))))
        extra = dict((n, sorted(set(c.get("permitted_axioms", [])) - set(STD)))
                     for n, c in cfgs.items()
                     if set(c.get("permitted_axioms", [])) - set(STD))
        p("  configs permitting a NON-standard axiom : %d  %s" % (
            len(extra), (", ".join("%s:%s" % kv for kv in sorted(extra.items())[:8]) if extra else "")))
        empty_ax = [n for n, c in cfgs.items() if not c.get("permitted_axioms")]
        p("  configs with EMPTY permitted_axioms     : %d  %s" % (len(empty_ax), empty_ax[:6]))
        no_thm = [n for n, c in cfgs.items() if not c.get("theorem_names")]
        p("  configs with NO theorem_names           : %d  %s" % (len(no_thm), no_thm[:6]))
        p("  theorem declarations named in total     : %d" % sum(
            len(c.get("theorem_names", [])) for c in cfgs.values()))
        p("  configs also naming definition_names    : %d" % sum(
            1 for c in cfgs.values() if c.get("definition_names")))
        nanoda = sorted(n for n, c in cfgs.items() if c.get("enable_nanoda"))
        p("  configs with enable_nanoda = TRUE       : %d  %s" % (len(nanoda), nanoda[:12]))
        if paths is not None:
            lean_paths = [x for x in paths if x.startswith("lean/")]
            lset = set(lean_paths)
            unresolved = []
            for n, c in cfgs.items():
                mod = c.get("solution_module", "").replace(".", "/")
                if not mod:
                    continue
                cand = "lean/" + mod
                if not any(p2 == cand + ".lean" or p2.startswith(cand + "/") for p2 in lset):
                    unresolved.append((n, mod))
            p("  solution_module resolvable on disk    : %d / %d (unresolved: %d, e.g. %s)" % (
                len(cfgs) - len(unresolved), len(cfgs), len(unresolved),
                ", ".join(n for n, _ in unresolved[:4])))
            p("  NOTE unresolved != wrong: a module may live in a differently-named file;")
            p("       this row only says the naive path guess did not match.")
        with open(os.path.join(OUT, "comparator_axioms.csv"), "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["config", "n_theorems", "n_definitions", "permitted_axioms",
                        "non_standard_axioms", "enable_nanoda", "solution_module"])
            for n in sorted(cfgs):
                c = cfgs[n]
                w.writerow([n, len(c.get("theorem_names", [])), len(c.get("definition_names", [])),
                            "|".join(c.get("permitted_axioms", [])),
                            "|".join(sorted(set(c.get("permitted_axioms", [])) - set(STD))),
                            "TRUE" if c.get("enable_nanoda") else "false",
                            c.get("solution_module", "")])
    with open(stats_path, "wb") as fh:
        fh.write(buf.getvalue().encode("utf-8"))
    sys.stdout.write(buf.getvalue())


if __name__ == "__main__":
    main()
