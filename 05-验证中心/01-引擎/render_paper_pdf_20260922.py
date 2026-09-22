# -*- coding: utf-8 -*-
"""把 openmath 记录 md 渲染成 CJK PDF 论文稿（自定义渲染器，不依赖 write_html）"""
import os
import re
import sys

from fpdf import FPDF

_DEF_SRC = (r"D:\a10\aikjx\code\my_lib\openmath\03-难题与猜想\05-经典未解猜想"
            r"\OM-P-NT-0003-前缀覆盖前沿与一般缺口引理_20260922.md")
_DEF_OUT = (r"D:\a10\aikjx\code\my_lib\openmath\03-难题与猜想\05-经典未解猜想"
            r"\OM-P-NT-0003-前缀覆盖前沿与一般缺口引理_20260922.pdf")
# 允许多论文复用同一渲染器：
#   python render_paper_pdf_20260922.py [源.md] [目标.pdf]
SRC = sys.argv[1] if len(sys.argv) > 1 else _DEF_SRC
OUT = sys.argv[2] if len(sys.argv) > 2 else _DEF_OUT
FD = r"C:\Windows\Fonts"

SYM = [
    (r"\\mathbb\{P\}", "ℙ"), (r"\\mathbb\{Z\}", "ℤ"), (r"\\mathbb\{N\}", "ℕ"),
    (r"\\varnothing", "∅"), (r"\\lambda", "λ"), (r"\\Lambda", "Λ"),
    (r"\\Delta", "Δ"), (r"\\pi", "π"), (r"\\Sigma", "Σ"), (r"\\sum", "Σ"),
    (r"\\prod", "Π"), (r"\\infty", "∞"), (r"\\leqslant", "≤"), (r"\\geqslant", "≥"),
    (r"\\le(?![a-zA-Z])", "≤"), (r"\\ge(?![a-zA-Z])", "≥"),
    (r"\\longrightarrow", "⟶"), (r"\\Longleftrightarrow", "⟺"),
    (r"\\Longrightarrow", "⟹"), (r"\\Rightarrow", "⟹"), (r"\\implies", "⟹"),
    (r"\\Longleftarrow", "⟸"), (r"\\Leftarrow", "⟸"),
    (r"\\mathbb\s*\{?([PNZRCQ])\}?", r"\1"),
    (r"\\iff", "⟺"), (r"\\Longleftrightarrow", "⟺"),
    (r"\\to(?![a-zA-Z])", "→"),
    (r"\\times", "×"), (r"\\cdot", "·"), (r"\\ldots", "…"), (r"\\dots", "…"),
    (r"\\cdots", "…"), (r"\\lnot", "非"), (r"\\neg", "非"),
    (r"\\qquad", "    "), (r"\\quad", "  "), (r"\\;", " "), (r"\\,", " "),
    (r"\\forall", "∀"), (r"\\exists", "∃"), (r"\\notin", "∉"),
    (r"\\subseteq", "⊆"), (r"\\subset", "⊂"), (r"\\cup", "∪"), (r"\\cap", "∩"),
    (r"\\in(?![a-zA-Z])", "∈"), (r"\\square", "□"), (r"\\boxed", ""),
    (r"\\limsup", "limsup"), (r"\\max", "max"), (r"\\min", "min"),
    (r"\\lim(?![a-zA-Z])", "lim"), (r"\\sup", "sup"), (r"\\inf", "inf"),
    (r"\\approx", "≈"), (r"\\sim", "~"), (r"\\wedge", "∧"),
    # ---- 2026-09-22 补：多行展示公式 \[...\] 与 cases/对齐环境里的 LaTeX ----
    (r"\\begin\{[a-zA-Z]*\}", " "), (r"\\end\{[a-zA-Z]*\}", " "),
    (r"\\\\", " ; "),                       # cases 的行分隔符，必须在通用去反斜杠之前
    (r"\\mid", "|"), (r"\\nmid", "!|"), (r"\\equiv", "≡"), (r"\\neq", "≠"),
    (r"\\pm", "±"), (r"\\mp", "∓"), (r"\\propto", "∝"), (r"\\perp", "⊥"),
    # 希腊字母（旧记录大量使用；缺映射会直接把 \rho 之类打进 PDF）
    (r"\\alpha", "α"), (r"\\beta", "β"), (r"\\gamma", "γ"), (r"\\delta", "δ"),
    (r"\\epsilon", "ε"), (r"\\varepsilon", "ε"), (r"\\zeta", "ζ"), (r"\\eta", "η"),
    (r"\\theta", "θ"), (r"\\vartheta", "θ"), (r"\\iota", "ι"), (r"\\kappa", "κ"),
    (r"\\mu", "μ"), (r"\\nu", "ν"), (r"\\xi", "ξ"), (r"\\rho", "ρ"),
    (r"\\sigma", "σ"), (r"\\tau", "τ"), (r"\\upsilon", "υ"), (r"\\phi", "φ"),
    (r"\\varphi", "φ"), (r"\\chi", "χ"), (r"\\psi", "ψ"), (r"\\omega", "ω"),
    (r"\\Gamma", "Γ"), (r"\\Theta", "Θ"), (r"\\Xi", "Ξ"), (r"\\Phi", "Φ"),
    (r"\\Psi", "Ψ"), (r"\\Omega", "Ω"),
    (r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2"),
    (r"\\text\{([^{}]*)\}", r"\1"), (r"\\mathrm\{([^{}]*)\}", r"\1"),
    # ---- 2026-09-22 第三次补：按 `scratch/census_commands.txt` 的**实测频次表**补全 ----
    # 依据：8 份 20260922 md 里 \\命令名 的全量普查（不是凭印象猜）。旧版对这 20 余个
    # 命令无映射，于是 deslash 把它们降级成裸名字（`\\bigr`→"bigr"、`\\mathbf`→"mathbf"），
    # 直接以普通文字排进 PDF —— 这是继"展示公式未处理"之后的第二类残留来源。
    (r"\\[bB]ig[lr]", ""), (r"\\[bB]igg[lr]", ""),        # \\bigl \\bigr \\Bigl \\Bigr：纯定界修饰
    (r"\\left", ""), (r"\\right", ""),
    (r"\\textstyle", ""), (r"\\displaystyle", ""), (r"\\limits", ""),
    (r"\\bigcup", "∪"), (r"\\bigcap", "∩"), (r"\\setminus", "−"),
    # ↑ `\setminus` 本应打 "∖"(U+2216)，实测 NotoSansSC **缺该字形**（门禁抓到），
    #   降级为数学上同样标准的差集写法 "X − Y"（U+2212 有字形）。
    (r"\\lfloor", "["), (r"\\rfloor", "]"), (r"\\lceil", "["), (r"\\rceil", "]"),
    # ↑ 取整括号 ⌊⌋⌈⌉(U+230A/B/8/9) 实测缺字形，降级为方括号（与 floor/ceil 的常见 ASCII 写法一致）。
    (r"\\langle", "⟨"), (r"\\rangle", "⟩"),
    (r"\\ll(?![a-zA-Z])", "≪"), (r"\\gg(?![a-zA-Z])", "≫"),
    (r"\\supset(?![a-zA-Z])", "⊃"), (r"\\supseteq", "⊇"),
    (r"\\mapsto", "→"), (r"\\checkmark", "✓"), (r"\\blacksquare", "■"),
    # ↑ `\mapsto` 本应打 "↦"(U+21A6)，实测缺字形；→(U+2192) 有字形。
    (r"\\pmod\s*\{?([^{}]*)\}?", r" (mod \1)"),
    (r"\\sqrt\s*\{([^{}]*)\}", r"√(\1)"), (r"\\sqrt\s*([A-Za-z0-9])", r"√\1"),
    (r"\\tag\{([^{}]*)\}", r"  [\1]"),                     # \\tag{...} 是公式编号，保留为 [编号]
    (r"\\S(?![A-Za-z])", "§"), (r"\\arg(?![a-zA-Z])", "arg"),
    (r"\\texttt\{([^{}]*)\}", r"\1"), (r"\\mathbf\{([^{}]*)\}", r"\1"),
    (r"\\mathbf\s*([A-Za-z0-9])", r"\1"), (r"\\boldsymbol\{([^{}]*)\}", r"\1"),
    (r"\\mathcal\{([^{}]*)\}", r"\1"), (r"\\overline\{([^{}]*)\}", r"\1"),
    (r"\\operatorname\{([^{}]*)\}", r"\1"), (r"\\mathop\{([^{}]*)\}", r"\1"),
]

# Noto Sans SC 缺失的双线体/长箭头/表情符号 → 安全替代
FIX = {"⟺": "<=>", "⟹": "=>", "⟸": "<=", "ℙ": "P", "ℤ": "Z",
       "⇒": "=>", "⇐": "<=", "⟶": "->", "⟵": "<-",
       "✅": "[OK]", "❌": "[X]"}

# 字体缺字形的 Unicode 上下标 → ASCII（2026-09-22 第三次修复）
# 依据：渲染 stderr 明确报 NotoSansSC / DengXianBold **缺少** ⁶ ₁ ₖ ᵢ ∤ ₊ ₃ ₚ ᵏ ⁱ ₈ … 等字形，
# 而 md 正文里这些字符是**内容**（如 `αᵢ`、`pₖ`、`E₀`）。缺字形时 fpdf2 会静默画空白，
# 属于**信息丢失**（比排版瑕疵更严重），故必须在送字体之前映射成 ASCII 等价写法。
for _i, _c in enumerate("₀₁₂₃₄₅₆₇₈₉"):
    FIX.setdefault(_c, "_%d" % _i)
for _i, _c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹"):
    FIX.setdefault(_c, "^%d" % _i)
FIX.update({
    "ᵢ": "_i", "ⱼ": "_j", "ₖ": "_k", "ₚ": "_p", "ₐ": "_a", "ₑ": "_e", "ₕ": "_h",
    "ₗ": "_l", "ₘ": "_m", "ₙ": "_n", "ₒ": "_o", "ᵣ": "_r", "ₛ": "_s", "ₜ": "_t",
    "ᵤ": "_u", "ᵥ": "_v", "ₓ": "_x", "₊": "_+", "₋": "_-", "₌": "_=",
    "₍": "_(", "₎": "_)", "ⁿ": "^n", "ᵏ": "^k", "ᵐ": "^m", "ᵖ": "^p",
    "ⁱ": "^i", "ʲ": "^j", "ʳ": "^r", "ˢ": "^s", "ᵗ": "^t",
    "∤": "!|",          # 双保险：即使 SYM 没吃掉 \\nmid，裸 ∤ 也不会落到缺字形上
    # 实测两款字体都缺的符号 → 公认的 ASCII 等价写法（双保险：raw 字符也兜住）
    "∅": "Ø",           # U+2205 空集（DengXianBold 缺）；Ø 在 Latin-1 区，两款字体都有
    "∖": "−", "↦": "→", "⌊": "[", "⌋": "]", "⌈": "[", "⌉": "]",
})


def clean_math(t):
    for pat, rep in SYM:
        t = re.sub(pat, rep, t)
    t = t.replace("&", " ")          # cases/aligned 的对齐符
    t = t.replace("{", "").replace("}", "").replace("\\", "")
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip(" $")


def deslash(s):
    """兜底清理：正文/表格/标题里**没有被 `$...$` 包住**的 LaTeX 片段。

    缺陷背景（2026-09-22 第二次修复）：`clean_math` 只在 `$...$` / `$$...$$` / `\\[...\\]`
    内部生效；但记录 md 的表头与表格单元格里大量存在**裸 LaTeX**，例如
        `（... 全阶容斥和 = \\|X\\|）`、`$H \\ge 186-334+208-43=17$`（后者在内，前者在外）
    以及 `\\mathbf{-3}`、`\\bigl|`、`\\setminus`、`\\pmod`。这些不再经 clean_math，
    于是反斜杠原样排进 PDF（旧记录残留 `\\` 计数恰好来自此处）。

    本函数分两级，保证**最终正文里不存在任何反斜杠**：
      ① 先重跑一遍 SYM 符号表（能认出来的命令映射成真符号）；
      ② 去掉花括号后，把「反斜杠 + 字母」的命令名降级为纯名字（`\\mathbf` → `mathbf`），
         再把所有剩余反斜杠（`\\| \\{ \\_ \\, \\\\` 等非字母后继）直接删除。

    注意：只作用于 `plain()` 路径；`pre` 代码块走 `ascii_safe()`，**保留原始反斜杠**
    以维持文件路径/转义的真值（本库 md 的代码块里确有 Windows 路径）。
    """
    for pat, rep in SYM:
        s = re.sub(pat, rep, s)
    s = s.replace("{", "").replace("}", "").replace("&", " ")
    s = re.sub(r"\\([A-Za-z]+)", r"\1", s)   # 未识别命令：留名字、去反斜杠
    s = s.replace("\\", "")                  # 剩余反斜杠（标点后继/孤反斜杠）一律清除
    return s


_CODE_SPANS = []


def _stash_code(s):
    """把行内代码 `` `...` `` 暂存为占位符。

    缺陷背景（2026-09-22 第四次修复）：`deslash()` 会把正文里所有反斜杠清掉，
    连**行内代码里被有意引用的命令名/路径**也一起清掉——
    例如记录里写 `` `\\boxed` ``（本意是"作者在说这个 LaTeX 命令"）会被渲染成 `boxed`，
    `` `\\\\` `` 会渲染成空串。行内代码是**逐字内容**，必须原样保留。
    处理：先暂存，走完整条清理链后再还原；还原时只做两件安全替换——
    `\\|` → `|`（md 表格转义竖线）与 FIX 字形替换（反斜杠是 ASCII，无缺字形风险）。
    """

    def rep(m):
        _CODE_SPANS.append(m.group(1))
        return "\x02%d\x02" % (len(_CODE_SPANS) - 1)

    return re.sub(r"`([^`]+)`", rep, s)


def _restore_code(s):
    def rep(m):
        t = _CODE_SPANS[int(m.group(1))]
        t = t.replace("\\|", "|")
        for a, b in FIX.items():
            t = t.replace(a, b)
        return t

    return re.sub("\x02(\\d+)\x02", rep, s)


def plain(s):
    # `\\|` 是 md 表格里对基数竖线 `|X|` 的转义写法。旧版直接 `|`→空格，把基数符号
    # 一并吃掉（`$\\|X\\|$` 渲染成 ` X `）。改为先用占位符保护，行尾再还原为可见 `|`。
    PIPE = "\x01"
    s = _stash_code(s)
    s = s.replace("\\|", PIPE)
    s = re.sub(r"\$([^$]+)\$",
               lambda m: " " + clean_math(m.group(1)).replace("|", PIPE) + " ", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = s.replace("|", " ").strip()          # 真正的 md 列分隔竖线
    s = deslash(s)
    s = s.replace(PIPE, "|")
    s = _restore_code(s)                     # 行内代码逐字还原（保留其中的反斜杠）
    for a, b in FIX.items():
        s = s.replace(a, b)
    return s


def strip_front_matter(md):
    """去掉开头的 YAML front matter（--- id/title/status ---），
    否则 id/title_zh 等会作为普通段落排进正文（老版的噪声来源之一）"""
    return re.sub(r"\A\s*---\s*\n.*?\n---\s*\n", "", md, flags=re.S)


def collapse_display_math(md):
    """把（可能跨行的）展示公式折叠为单独一段并清理。

    支持两种定界符：`$$...$$`（本库新记录用）与 `\\[...\\]`（旧记录用）。
    缺陷背景（2026-09-22 修复）：老版只在 plain() 里处理**单行** `$...$`，
    于是跨行 `$$...$$` 与全部 `\\[...\\]` 完全没被处理 —— `\\boxed`/`\\mathbb`/`\\frac`
    等原样进入 PDF，成为真正的排版缺陷（旧记录 PDF 里残留上百处）。
    """
    md = re.sub(r"\$\$(.+?)\$\$",
                lambda m: "\n\n" + clean_math(m.group(1)) + "\n\n", md, flags=re.S)
    md = re.sub(r"\\\[(.+?)\\\]",
                lambda m: "\n\n" + clean_math(m.group(1)) + "\n\n", md, flags=re.S)
    return md


def wrap(pdf, text, width):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if pdf.get_string_width(cur + ch) <= width:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    lines.append(cur)
    return lines or [""]


def parse(md):
    """→ 块列表：[('h',lvl,text)] [('p',text)] [('li',text)] [('pre',[lines])]
                 [('hr',)] [('tbl',header,rows)]"""
    blocks, i, L = [], 0, md.split("\n")
    while i < len(L):
        s = L[i].strip()
        # HTML 注释必须显式跳过：否则 `<!-- ... -->` 会被当成普通段落排进 PDF。
        # （校验器的"声明式豁免"标记就写在注释里，故这条是豁免机制的前置条件。）
        if s.startswith("<!--"):
            while i < len(L) and "-->" not in L[i]:
                i += 1
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(L) and not L[i].strip().startswith("```"):
                buf.append(L[i])
                i += 1
            i += 1
            blocks.append(("pre", buf))
            continue
        if s.startswith("|") and i + 1 < len(L) and set(L[i + 1].strip()) <= set("|-: "):
            head = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(L) and L[i].strip().startswith("|"):
                rows.append([c.strip() for c in L[i].strip().strip("|").split("|")])
                i += 1
            blocks.append(("tbl", head, rows))
            continue
        if not s:
            i += 1
            continue
        if s == "---":
            blocks.append(("hr",))
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            blocks.append(("h", len(m.group(1)), m.group(2)))
            i += 1
            continue
        if s.startswith("- "):
            while i < len(L) and L[i].strip().startswith("- "):
                blocks.append(("li", L[i].strip()[2:]))
                i += 1
            continue
        if s.startswith("> "):
            buf = []
            while i < len(L) and L[i].strip().startswith(">"):
                buf.append(L[i].strip()[1:].strip())
                i += 1
            blocks.append(("p", " ".join(buf)))
            continue
        if re.match(r"^\d+\.\s", s):
            while i < len(L) and re.match(r"^\d+\.\s", L[i].strip()):
                blocks.append(("li", re.sub(r"^\d+\.\s", "", L[i].strip())))
                i += 1
            continue
        blocks.append(("p", s))
        i += 1
    return blocks


def main():
    pdf = FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_font("Deng", "", os.path.join(FD, "NotoSansSC-VF.ttf"))
    pdf.add_font("Deng", "B", os.path.join(FD, "Dengb.ttf"))
    pdf.add_page()
    M = 16.0
    CW = 210 - 2 * M
    H1, H2, H3, PS = 15.0, 13.0, 11.5, 10.0
    LH = 5.0

    def ascii_safe(s):
        """只做安全符号替换（供代码块/pre 使用，不走 plain 的数学清理）"""
        for a, b in FIX.items():
            s = s.replace(a, b)
        return s

    def para(text, size=PS, bold=False, indent=0.0, bullet=False):
        w = CW - indent
        prefix = ("• " if bullet else "")
        # 必须先 set_font 再 wrap：wrap 依赖 pdf.get_string_width 的**当前字体**度量，
        # 顺序颠倒会用上一段的字号/字重算换行宽度（2026-09-22 修复的缺陷）。
        pdf.set_font("Deng", "B" if bold else "", size)
        lines = wrap(pdf, prefix + text, w)
        pdf.set_x(M + indent)
        pdf.multi_cell(w, LH * size / PS, "\n".join(lines))

    def table(head, rows):
        ncol = len(head)
        pdf.set_font("Deng", "", 8.6)
        nat = []
        for c in range(ncol):
            vals = [plain(head[c])] + [plain(r[c]) if c < len(r) else "" for r in rows]
            nat.append(max(pdf.get_string_width(v) for v in vals) + 8)
        tot = sum(nat)
        cols = [max(14.0, x / tot * CW) for x in nat]
        sc = CW / sum(cols)
        cols = [c * sc for c in cols]

        def draw_row(cells, bold=False, fill=False):
            pdf.set_font("Deng", "B" if bold else "", 8.6)
            hts = []
            for c in range(ncol):
                txt = plain(cells[c]) if c < len(cells) else ""
                hts.append(len(wrap(pdf, txt, cols[c] - 2.4)) * 4.0 + 1.6)
            h = max(hts)
            if pdf.get_y() + h > 280:
                pdf.add_page()
            y0, x0 = pdf.get_y(), M
            if fill:
                pdf.set_fill_color(243, 242, 238)
            for c in range(ncol):
                pdf.set_xy(x0, y0)
                pdf.cell(cols[c], h, "", border="LTRB", fill=fill)
                txt = plain(cells[c]) if c < len(cells) else ""
                pdf.set_font("Deng", "B" if bold else "", 8.6)
                for k, ln in enumerate(wrap(pdf, txt, cols[c] - 2.4)):
                    pdf.set_xy(x0 + 1.2, y0 + 0.8 + k * 4.0)
                    pdf.cell(cols[c] - 2.4, 4.0, ln)
                x0 += cols[c]
            pdf.set_xy(M, y0 + h)

        draw_row(head, bold=True, fill=True)
        for r in rows:
            draw_row(r)
        pdf.set_xy(M, pdf.get_y() + 2)

    body = collapse_display_math(
        strip_front_matter(open(SRC, encoding="utf-8").read()))
    for b in parse(body):
        if b[0] == "h":
            pdf.set_font("Deng", "B", {1: H1, 2: H2, 3: H3}.get(b[1], H3))
            if pdf.get_y() > 255:
                pdf.add_page()
            pdf.set_x(M)
            pdf.multi_cell(CW, {1: 7.5, 2: 6.5, 3: 6.0}.get(b[1], 6.0), plain(b[2]))
            pdf.ln(1.2)
        elif b[0] == "p":
            para(plain(b[1]))
        elif b[0] == "li":
            para(plain(b[1]), indent=4.0, bullet=True)
        elif b[0] == "hr":
            pdf.ln(1.5)
            pdf.set_draw_color(150, 150, 150)
            y = pdf.get_y()
            pdf.line(M, y, M + CW, y)
            pdf.ln(2.5)
        elif b[0] == "pre":
            pdf.set_font("Deng", "", 8.0)
            h = len(b[1]) * 3.6 + 2.5
            if pdf.get_y() + h > 280:
                pdf.add_page()
            y0 = pdf.get_y()
            pdf.set_fill_color(246, 246, 243)
            pdf.rect(M, y0, CW, h, style="F")
            for k, ln in enumerate(b[1]):
                pdf.set_xy(M + 2, y0 + 1.2 + k * 3.6)
                # 代码块也要过一遍安全替换，否则 ⇒ / ✅ / ℙ 等会触发缺字形（老版直接输出裸行）
                pdf.cell(CW - 4, 3.6, ascii_safe(ln))
            pdf.set_xy(M, y0 + h + 1.5)
        elif b[0] == "tbl":
            table(b[1], b[2])

    pdf.output(OUT)
    print("OK %s %d bytes pages=%d" % (OUT, os.path.getsize(OUT), pdf.page_no()))


if __name__ == "__main__":
    main()
