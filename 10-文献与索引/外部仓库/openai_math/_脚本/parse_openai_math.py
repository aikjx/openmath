# -*- coding: utf-8 -*-
"""Parse the pinned metadata mirror of https://github.com/openai/math into a table ledger.

Inputs (_镜像/, read-only): CONTENTS.md, overview.tex, formalization.yaml, history.md, README.md
Outputs (_生成/): families.csv, manuscripts.csv, by_subject.csv, stats.txt

Every aggregate quoted by the analysis documents is printed by this script into stats.txt.
Run:  python _脚本/parse_openai_math.py
"""
from __future__ import print_function

import csv
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


def parse_contents():
    """Return (families, manuscripts, diagnostics)."""
    text = read_text(CONTENTS)
    lines = text.splitlines()
    families = []
    manuscripts = []
    head_re = re.compile(r"^\*\*(\d{3})\.\s*(.+?)\.\*\*\s*(.*)$")
    link_re = re.compile(r"^&emsp;\[(.*?)\]\((.*?)\)")
    lean_re = re.compile(r"lean/docs/(\d{3})\.md")
    seen = {}
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
        lm = link_re.match(raw)
        if lm:
            title, path = lm.group(1), lm.group(2)
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
    diagnostics = {
        "family_head_lines": len(families),
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
    p("  manuscript link lines in CONTENTS.md        : %d" % diag["manuscript_link_lines"])
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
    p("  computed 300/719 = %.4f ; computed %d/372 = %.4f (families formalized)" % (
        300 / 719.0, diag["families_with_lean_doc_in_head"],
        diag["families_with_lean_doc_in_head"] / 372.0))
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
    keywords = ["goldbach", "chowla", "elliott", "prime gap", "prime gap", "twin", "sieve",
                "arithmetic progression", "squarefree", "square-free", "totient", "jacosthal",
                "jacobsthal", "zero-free", "riemann", "zeta", "l-function", "dirichlet",
                "circle method", "additive", "multiplicative function", "partition",
                "erdos", "ramsey", "collatz", "abc conjecture", "bsd", "hodge",
                "liouville", "mobius", "m\"obius", "density", "distribution of primes",
                "batalin", "maynard", "tao", "green"]
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
    with open(stats_path, "wb") as fh:
        fh.write(buf.getvalue().encode("utf-8"))
    sys.stdout.write(buf.getvalue())


if __name__ == "__main__":
    main()
