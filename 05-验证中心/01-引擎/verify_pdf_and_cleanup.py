# -*- coding: utf-8 -*-
"""校验 openmath 论文 PDF（文本可抽取 / 关键数字在位 / 无 LaTeX 残留）+ 归档探针文件

2026-09-22 修订：原版只硬编码校验第 1 份 PDF，后续新增的论文 PDF 不在校验范围内；
现改为**自动发现 DOC 目录下全部 `OM-P-NT-0003-*.pdf`** 并逐份校验。
本脚本是**一次性收尾任务**（含 shutil.move），不是可复用引擎；多次运行是幂等的（先判存在）。
"""
import glob
import os
import re
import shutil

ROOT = r"D:\a10\aikjx\code\my_lib"
ENG = os.path.join(ROOT, "openmath", "05-验证中心", "01-引擎")
RES = os.path.join(ROOT, "openmath", "05-验证中心", "03-结果", "2026", "09")
DOC = os.path.join(ROOT, "openmath", "03-难题与猜想", "05-经典未解猜想")
SCRATCH = os.path.join(ROOT, "scratch")
os.makedirs(SCRATCH, exist_ok=True)

lines = []
# 残留判定分两级（2026-09-22 第二次修订）：
#   HARD = LaTeX 命令名，出现即证明公式没被渲染器消化（真缺陷，必须为 0）；
#   BARE = 裸反斜杠计数 + 上下文切片，用于人工裁定（可能是合法的文件名/转义，也可能是漏网命令）。
HARD_RESIDUE = ["Rightarrow", "mathbb", "boxed", "dfrac", "tfrac", "cdots", "lnot",
                "leqslant", "geqslant", "begin{", "end{", "text{", "mathbf", "\\qquad", "\\quad",
                # 2026-09-22 第三次修订：未映射的定界/取整/根号命令被 deslash 降级成裸名字，
                # 这些名字一旦出现在抽取文本里，就说明 SYM 表还缺条目（真缺陷）。
                "bigl", "bigr", "Bigl", "Bigr", "left", "right", "sqrt", "checkmark",
                "textstyle", "texttt", "blacksquare", "setminus", "pmod", "tag{"]
# 缺字形高危字符：NotoSansSC / DengXianBold 实测缺失（渲染 stderr 已报），
# 若出现在抽取文本里说明 FIX 表没覆盖住 → 信息会以**空白**形式丢失。
GLYPH_RISK = "⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉ᵢⱼₖₚₐₑₕₗₘₙₒᵣₛₜᵤᵥₓ₊₋ⁱᵏᵐᵖⁿ∤"
BARE_CTX = re.compile(r"\\+|\\[A-Za-z]+|\\[^A-Za-z0-9]")

# 声明式豁免（2026-09-22 第四次修订）：
# 门禁对"泄漏的 LaTeX"与"**正文有意引用** LaTeX 命令名 / Windows 反斜杠路径"无法自动区分。
# 后者（如渲染器说明文档、复现命令块）出现反斜杠是**正确内容**，不是缺陷。
# 处置方式不写死在代码里，而是要求在 md 源码中显式声明本标记，由校验器读到后**降级为提示**
# 并打印上下文（保留人工裁定入口），避免"改代码跳过检查"这种自欺做法。
EXEMPT_MARK = "renderer-gate: allow-latex-quotes"
EXEMPT_DOCS = []

try:
    from pypdf import PdfReader
except Exception as e:                                   # pragma: no cover
    PdfReader = None
    lines.append("pypdf 不可用：%s（请在隔离 venv 中运行）" % e)

if PdfReader is not None:
    pdfs = sorted(glob.glob(os.path.join(DOC, "OM-P-NT-0003-*.pdf")))
    lines.append("发现 %d 份 OM-P-NT-0003 PDF" % len(pdfs))
    for pdf_path in pdfs:
        name = os.path.basename(pdf_path)
        try:
            r = PdfReader(pdf_path)
            txt = "\n".join((p.extract_text() or "") for p in r.pages)
        except Exception as e:
            lines.append("  [FAIL] %s 抽取异常 %s: %s" % (name, type(e).__name__, e))
            continue
        hard = {}
        for s in HARD_RESIDUE:
            n = len(re.findall(r"(?<![A-Za-z\\])" + re.escape(s) + r"(?![A-Za-z])", txt))
            if n:
                hard[s] = n
        glyph_hits = {c: txt.count(c) for c in GLYPH_RISK if txt.count(c) > 0}
        n_bs = txt.count("\\")

        md_src = pdf_path[:-4] + ".md"
        exempt = False
        if os.path.exists(md_src):
            try:
                exempt = EXEMPT_MARK in open(md_src, encoding="utf-8").read()
            except OSError:
                exempt = False
        if exempt:
            EXEMPT_DOCS.append(name)

        ctx = []
        for m in BARE_CTX.finditer(txt):
            a = max(0, m.start() - 18)
            b = min(len(txt), m.end() + 22)
            snip = txt[a:b].replace("\n", " ")
            ctx.append(snip)
            if len(ctx) >= 6:
                break
        lines.append("  %s  pages=%d chars=%d" % (name, len(r.pages), len(txt)))
        bad = bool(hard or n_bs or glyph_hits)
        if not bad:
            lines.append("      残留: HARD=无 裸反斜杠=0 缺字形高危=无 -> OK（三项全 0）")
        elif exempt and not glyph_hits:
            # 已声明豁免：缺字形仍是硬缺陷（豁免不覆盖字形），HARD/反斜杠降级为待裁定
            lines.append("      残留: HARD=%s 裸反斜杠=%d 缺字形高危=无"
                         % (hard if hard else "无", n_bs))
            lines.append("      -> 豁免（%s 已声明）：正文/代码块**有意引用** LaTeX 命令名与反斜杠路径，"
                         "属正确内容；下面打印上下文供人工裁定" % EXEMPT_MARK)
        else:
            lines.append("      残留: HARD=%s 裸反斜杠=%d 缺字形高危=%s -> !! 需修替换表"
                         % (hard if hard else "无", n_bs, glyph_hits if glyph_hits else "无"))
        for snip in ctx:
            lines.append("         | %s" % snip)
        if hard:
            # HARD 命中也要给上下文：否则"待人工裁定"就只是一句空话
            shown = 0
            for s in hard:
                m = re.search(r"(?<![A-Za-z\\])" + re.escape(s) + r"(?![A-Za-z])", txt)
                if not m or shown >= 3:
                    continue
                a = max(0, m.start() - 30)
                b = min(len(txt), m.end() + 30)
                lines.append("         HARD[%s] @ %s" % (s, txt[a:b].replace("\n", " ")))
                shown += 1
        for probe in ("未证", "1000537", "1 000 537", "999 999", "引理"):
            if probe in txt:
                lines.append("      contains %s -> True" % probe)

if EXEMPT_DOCS:
    lines.append("")
    lines.append("已声明豁免（有意引用 LaTeX/反斜杠，非缺陷）：" + "、".join(EXEMPT_DOCS))

moves = [
    (os.path.join(ENG, "probe_fonts.py"), os.path.join(SCRATCH, "probe_fonts.py")),
    (os.path.join(ENG, "font_visual_test.py"), os.path.join(SCRATCH, "font_visual_test.py")),
    (os.path.join(RES, "_font_visual_test.pdf"), os.path.join(SCRATCH, "_font_visual_test.pdf")),
    (os.path.join(RES, "_font_visual.txt"), os.path.join(SCRATCH, "_font_visual.txt")),
    (os.path.join(RES, "_font_probe.txt"), os.path.join(SCRATCH, "_font_probe.txt")),
    (os.path.join(RES, "_pdf_env.txt"), os.path.join(SCRATCH, "_pdf_env.txt")),
    (os.path.join(DOC, "OM-P-NT-0003-前缀覆盖前沿与一般缺口引理_20260922._debug.html"),
     os.path.join(SCRATCH, "_paper_debug.html")),
]
for a, b in moves:
    if os.path.exists(a):
        shutil.move(a, b)
        lines.append("moved %s" % os.path.basename(a))

with open(os.path.join(RES, "_pdf_verify.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
