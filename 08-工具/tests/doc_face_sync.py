# -*- coding: utf-8 -*-
"""文档与版面的一致性仪器：文档里每一个「版面现印 N」的 N，必须由本脚本从版面复算。

为什么需要这一台（本轮现场理由）：`四层总览.md` 开头写着「所有计数点名版面」，
`CHANGELOG.md` 写着「文档只许引用这里印出的数」——**这两句话此前没有任何仪器守着**。
每轮靠铸造器/同步器里的临时断言，脚本一扔，文档就和版面分叉而全绿。
本轮实测分叉了两处（§八 印 31 枚而图里 30 行；§三 记号卡枚数与名单不符），
都是人读出来的，不是仪器点红的。这台仪器补的就是这一格。

判据形状（三条，缺一不可）：
  1. **逐条对照**：每条「声明」是一个闭集词表里的正则，命中到的数字必须等于版面复算值；
  2. **覆盖面非空**：每条声明必须至少命中 1 次——命中 0 次判 MISSING_CLAIM。
     「没有不一致」与「没检查任何东西」必须区分（扫描集不许为空）；
  3. **判据自己先过三格对照**：`--selftest` 拿两份临时副本喂给自己——
     改坏一个数必须红、删掉一行声明必须判 MISSING，两格都绿才算仪器通电。

它**只读**：绝不写任何文档。复现：`python 08-工具/tests/doc_face_sync.py`
"""

from __future__ import print_function

import io
import json
import os
import re
import sys
import tempfile

BS = chr(92)
# 注意：这里不能用 BS.join 也不许给相对路径打头加反斜杠——
# `os.path.join(HERE, "\\..\\..")` 在 Windows 上会被当成盘根锚定，静默解到 D:\ 去。
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FACE_REL = "10-文献与索引/知识图谱/_版面/graph_face.txt"
MFACE_REL = "10-文献与索引/知识图谱/_版面/graph_mutants_face.txt"
GJSON_REL = "10-文献与索引/知识图谱/graph.json"
# verify 的逐条判决面住在仓外 scratch（它不是语料，是一次仪器运行的存档）。
VERIFY_REL = "../scratch/VERIFY_L2_clean.txt"
VERIFY_TAGS = ("公式库 verify", "§八 verify", "CHANGELOG verify")
OV = "10-文献与索引/四层总览.md"
KG = "10-文献与索引/知识图谱/README.md"
IX = "10-文献与索引/README.md"
LIB = "02-公式库/README.md"
CH = "CHANGELOG.md"


def rd(rel, root=None):
    p = os.path.join(root or ROOT, rel.replace("/", BS))
    return io.open(p, "rb").read().decode("utf-8")


def parse_face(t):
    """版面 -> 读数表。parse 不到任何一格都算仪器故障，不算「没有缺陷」。"""
    def one(rx, tag):
        # re.M 是必须的：`^typed edges` 在没有 MULTILINE 时只能匹配串首，
        # 于是版面明明印着这一行，仪器却判「没 parse 到」——假阳来自正则而不是来自语料。
        m = re.search(rx, t, re.M)
        if not m:
            raise AssertionError("版面格 %s 没 parse 到（版面变形了，判据要跟着改而不是跳过）" % tag)
        return [int(x) for x in m.groups()]

    v = {}
    v["records"] = one(r"record nodes \(OM-\*\.yaml\)\s*:\s*(\d+)", "record nodes")[0]
    v["docs"] = one(r"doc nodes[^:\n]*:\s*(\d+)", "doc nodes")[0]
    v["evidence"] = one(r"evidence docs[^:\n]*:\s*(\d+)", "evidence docs")[0]
    v["edges"] = one(r"^typed edges\s*:\s*(\d+)", "typed edges")[0]
    v["yaml_errors"] = one(r"YAML load errors\s*:\s*(\d+)", "YAML load errors")[0]
    v["nodes"], v["keys"] = one(r"nodes / unique keys\s*:\s*(\d+)\s*/\s*(\d+)", "nodes / unique keys")
    v["ep"] = one(r"edges both ends in graph\s*:\s*(\d+)\s*/\s*(\d+)", "both ends")
    v["ep_one"] = one(r"one end off graph\s*:\s*(\d+)", "one end")[0]
    v["ep_none"] = one(r"both ends off graph\s*:\s*(\d+)", "both ends off")[0]
    v["ep_self"] = one(r"collapsed to self-loop\s*:\s*(\d+)", "self-loop")[0]
    v["dom"] = one(r"domains with >=1 node\s*:\s*(\d+)\s*/\s*(\d+)", "domains with >=1 node")
    v["placed"] = one(r"domains placed\s*:\s*(\d+)\s*/\s*(\d+)", "domains placed")
    m = re.search(r"declared unplaced\s*:\s*([A-Z, ]+)", t)
    v["unplaced"] = [x.strip() for x in m.group(1).split(",")] if m else []
    sec = t.split("---- edge type census ----")[1].split("---- gap classes ----")[0]
    v["census"] = dict((n, int(x)) for n, x in re.findall(r"^  ([a-z_]+)\s*:\s*(\d+)", sec, re.M))
    gsec = t.split("---- gap classes ----")[1].split("---- charts ----")[0]
    # 严重度类要含连字符：`(\w+)` 在 `LEDGER-GAP` 的 `-` 处截断成 `LEDGER`，
    # 于是三枚 LEDGER-GAP 被算成 0 类红——判据的宽窄要由对象实际有的形状定，不由我采到的第一种定。
    v["gaps"] = dict((n, (int(x), s)) for n, x, s in
                     re.findall(r"^  ([A-Z_]+)\s*:\s*(\d+) : ([A-Z_-]+)", gsec, re.M))
    csec = t.split("---- charts ----")[1].split("---- domain placement ----")[0]
    v["chart"] = {}
    for name, blob in re.findall(r"^  (\S+) : (\{.*\})", csec, re.M):
        v["chart"][name] = json.loads(blob)
    # 版面内部自洽（仪器不许信自己 parse 出来的数——先要版面闭合）
    assert v["nodes"] == v["keys"], "版面 nodes != unique keys"
    assert v["ep"][1] == v["edges"], "端点普查的分母不是 typed edges"
    assert v["ep"][0] + v["ep_one"] + v["ep_none"] == v["edges"], "端点三格相加不等于总边数"
    assert sum(v["census"].values()) == v["edges"], "边型普查不等于总边数"
    assert v["chart"]["00-四层总览"]["domains_with_nodes"] == v["dom"][0], "图元数据与域读数不一致"
    return v


def parse_mutants(t):
    m = re.search(r"mutants=(\d+) caught=(\d+) not_caught=(\d+)", t)
    if not m:
        raise AssertionError("变异体版面没有 verdict 行")
    return [int(x) for x in m.groups()]


def parse_verify(records):
    """verify 那一跑的逐条判决面：文档抄了它的数，本函数就把那三个数复算一遍。
    判决行数不等于版面记录数＝这一跑没走完全程，前面印出的行不算凭据；载体不在＝判红，不算跳过。"""
    p = os.path.abspath(os.path.join(ROOT, VERIFY_REL.replace("/", BS)))
    if not os.path.exists(p):
        return None
    t = io.open(p, "rb").read().decode("utf-8")
    rows = re.findall(r"^(OM-\S+)\s+L2\s+(PASS|SKIP|FAIL)", t, re.M)
    if not rows:
        return None
    if len(rows) != records:
        # 不许在这里崩：崩了就是零判决，文档反而被放行。判它「不是凭据」，让三条声明各红一次。
        print("verify 判决行 %d ≠ 版面记录 %d：这一跑没走完全程，前面印出的行不构成凭据" % (len(rows), records))
        return None
    return [len([1 for _, s in rows if s == k]) for k in ("PASS", "SKIP", "FAIL")]


def claims(v, mut, dc, da, vf):
    """声明词表：闭集。每条 (标签, 文档, 正则, 版面复算值)。
    正则一律从文档**当下那一句**抄来，不许凭记忆打字：抄不到就判 MISSING-CLAIM。
    代价是「改句子必须同批改判据」，收益是文档里的数没有「看不见」这一档。
    dc／da：从 graph.json 现推的「域 -> 记录节点数」与「域 -> 全部节点数」，它们是分母而不是我打的名单。"""
    cm = v["chart"]["00-四层总览"]
    lay = cm["layer_nodes"]
    c03 = v["chart"]["03-难题卡点"]
    g = v["gaps"]
    cen = v["census"]
    big = max(dc, key=lambda k: dc[k])          # 记录最多的域：双口径示例由它现推，不是我挑的
    order = [n for n, _ in sorted(cen.items(), key=lambda kv: -kv[1])]
    return [
        ("§一 台账规模", OV,
         r"机器可读记录 (\d+) 条、仅 md 的账本节点 (\d+) 份、验证文档 (\d+) 份、类型化边 (\d+) 条、"
         r"YAML 解析失败 (\d+) 份", [v["records"], v["docs"], v["evidence"], v["edges"], v["yaml_errors"]]),
        ("§一 端点解析", OV,
         r"两端都在图内 (\d+) / (\d+)，一端无载体 (\d+) 条，两端无载体 (\d+) 条，两端并成同一个键 (\d+) 条",
         [v["ep"][0], v["ep"][1], v["ep_one"], v["ep_none"], v["ep_self"]]),
        ("§一 键数", OV, r"`nodes / unique keys` 印 (\d+) / (\d+)", [v["nodes"], v["keys"]]),
        ("§一 跨层边", OV, r"跨层的真实边共 (\d+) 条，折叠成 (\d+) 条层间边",
         [cm["real_edges_between_layers"], cm["layer_edges"]]),
        ("§一 逻辑层", OV, r"\| 逻辑层 \| [^|]* \| (\d+) \|", [lay["逻辑层"]]),
        ("§一 方程层", OV, r"\| 方程层 \| [^|]* \| (\d+) \|", [lay["方程层"]]),
        ("§一 难题层", OV, r"\| 难题层 \| [^|]* \| (\d+) \|", [lay["难题层"]]),
        ("§二 域覆盖", OV, r"`domains with >=1 node` ＝ (\d+) / (\d+)", [v["dom"][0], v["dom"][1]]),
        ("§二 双口径", OV, "例如 `%s` 记录 (\\d+) 条、图上 (\\d+) 个节点" % big, [dc[big], da[big]]),
        ("§二 账本节点", OV, r"全库仅 md 的账本节点本轮 (\d+) 个", [v["docs"]]),
        ("§三 符号账", OV, r"从上一版的 \d+ 涨到版面的 (\d+) 枚", [g["UNDEFINED_SYMBOL"][0]]),
        ("§三 逻辑层涨幅", OV, r"逻辑层从 \d+ 涨到 (\d+)", [lay["逻辑层"]]),
        ("§四 难题层节点", OV, r"难题层节点 (\d+) 个（版面 `03-难题卡点`：难题节点 (\d+) 个、图上 (\d+) 个节点／(\d+) 条边）",
         [lay["难题层"], c03["problem_nodes"], c03["chart_nodes"], c03["edges"]]),
        ("§四 cites", OV, r"边类型 `cites`（版面现印 (\d+) 条）", [v["census"]["cites"]]),
        ("§五 缺口表", OV, r"\| `([A-Z_]+)` \| (DEFECT|LEDGER-GAP|ADVISORY) \| (\d+) \|", None),
        ("§六 变异体", OV, r"本轮 (\d+) 枚变异体全部被抓住（(\d+) caught / (\d+) not caught）", mut),
        ("§八 符号债", OV, r"`UNDEFINED_SYMBOL` (\d+) 枚：补", [g["UNDEFINED_SYMBOL"][0]]),
        ("§七 红类", OV, r"DEFECT/LEDGER-GAP 非空的 (\d+) 类",
         [len([k for k, (n, s) in g.items() if n and s in ("DEFECT", "LEDGER-GAP")])]),
        ("KG 节点键", KG, r"版面现印 record (\d+) 个、doc (\d+) 个", [v["records"], v["docs"]]),
        ("KG 键数", KG, r"`nodes / unique keys` ＝ (\d+) / (\d+)", [v["nodes"], v["keys"]]),
        ("KG 端点", KG, r"两端都在图内 (\d+) / (\d+)、一端无载体 (\d+)、两端无载体 (\d+)、\n两端并成一个键 (\d+)",
         [v["ep"][0], v["ep"][1], v["ep_one"], v["ep_none"], v["ep_self"]]),
        ("KG 归域", KG, r"归域 (\d+) / (\d+) 个（版面 `---- domain placement ----`，"
                        r"`declared unplaced` 原样点名 ([A-Z, ]+)），有节点在图上的域 (\d+) / (\d+) 个", None),
        ("KG contradicts", KG,
         r"`contradicts` 已实现\*\*（版面 `---- edge type census ----` 现印 (\d+) 条）", [cen["contradicts"]]),
        ("KG 复现 变异体", KG, r"graph_mutants\.py   # (\d+) 枚指名变异体", [mut[0]]),
        ("索引层 边型普查", IX,
         r"全库 (\d+) 条，其中 " + "、".join("`%s` (\\d+)" % t for t in order),
         [v["edges"]] + [cen[t] for t in order]),
        ("索引层 判据", IX, r"✅ (\d+) 类判据＋版面＋(\d+) 枚变异体", [len(g), mut[0]]),
        ("公式库 域覆盖", LIB, r"现印 \*\*(\d+) / (\d+)\*\*", [v["dom"][0], v["dom"][1]]),
        ("公式库 合计记录", LIB, r"\| \*\*合计\*\* \| \*\*(\d+)\*\* \| `python -m openmath lint` 现印 记录数 (\d+)",
         [v["records"], v["records"]]),
        # 名单本身由 graph.json 现推：域多一个或少一个，这条正则就抄不到句子——文档被迫跟着语料改。
        ("公式库 域名单", LIB, "已有条目的域：" + "、".join("`%s`×(\\d+)" % d for d in sorted(dc)) + "。",
         [dc[d] for d in sorted(dc)]),
        # ---- CHANGELOG：只判「第 3 批记录」那一条条目（见 main 的 scope），历史条目里的旧数不归本判据管 ----
        ("CHANGELOG 记录数", CH, r"台账从 \d+ 条涨到 \*\*(\d+) 条\*\*", [v["records"]]),
        ("CHANGELOG 域覆盖", CH, r"域覆盖 \*\*\d+ / \d+ → (\d+) / (\d+)\*\*", [v["dom"][0], v["dom"][1]]),
        ("CHANGELOG 图谱", CH, r"图谱 \*\*\d+ 节点／\d+ 边 → (\d+) 节点／(\d+) 边", [v["nodes"], v["edges"]]),
        ("CHANGELOG 冲突边", CH, r"`contradicts` 落地（版面现印 (\d+) 条）", [cen["contradicts"]]),
        ("CHANGELOG 推广边", CH, r"`generalizes` 落地（版面现印 (\d+) 条）", [cen["generalizes"]]),
        ("CHANGELOG 跨层边", CH, r"跨层真实边 (\d+) 条（上一版 \d+），折叠成 (\d+) 条层间边",
         [cm["real_edges_between_layers"], cm["layer_edges"]]),
        ("CHANGELOG 变异体", CH, r"变异体 (\d+) 枚全部被抓住（(\d+) caught / (\d+) not caught）", mut),
        ("CHANGELOG 符号账", CH, r"`UNDEFINED_SYMBOL` \d+ → \*\*(\d+)\*\* 枚", [g["UNDEFINED_SYMBOL"][0]]),
        ("CHANGELOG 逻辑层", CH, r"逻辑层 \d+ → (\d+) 个节点", [lay["逻辑层"]]),
        # ---- verify 通道：这三个数住在 scratch 的判决面上，不在版面里 ----
        ("§八 verify", OV, r"已复跑：\*\*(\d+) PASS／(\d+) SKIP／(\d+) FAIL\*\*", vf or [0, 0, 0]),
        ("公式库 verify", LIB, r"已复跑：\*\*(\d+) PASS／(\d+) SKIP／(\d+) FAIL\*\*", vf or [0, 0, 0]),
        ("CHANGELOG verify", CH, r"＝\*\*(\d+) PASS／(\d+) SKIP／(\d+) FAIL\*\*", vf or [0, 0, 0]),
    ]


def check(doc_texts, v, mut, dc, da, vf):
    """返回 (判决行, 红数)。doc_texts: {文档: 文本}——selftest 从这里注入临时副本。"""
    lines, red = [], 0
    g = v["gaps"]
    for tag, doc, rx, exp in claims(v, mut, dc, da, vf):
        text = doc_texts.get(doc)
        if text is None:
            lines.append("MISSING-DOC  %s｜%s 不在盘上" % (tag, doc))
            red += 1
            continue
        if tag in VERIFY_TAGS and vf is None:
            lines.append("MISSING-CARRIER %s｜判决面 %s 不在盘上，文档却引用了它的数" % (tag, VERIFY_REL))
            red += 1
            continue
        hits = re.findall(rx, text)
        # 只有一组的正则 findall 会退化成字符串：`for x in "19"` 是逐字符，
        # 于是文档正确印 19 也会被判成 (1, 9)——假阳来自解析器，不来自语料。先统一成元组。
        hits = [(h,) if isinstance(h, str) else h for h in hits]
        if not hits:
            lines.append("MISSING-CLAIM %s｜%s 里没找到这条声明（词表是闭集：改写句子必须同时改写判据）" % (tag, doc))
            red += 1
            continue
        if tag == "§五 缺口表":
            seen = {}
            for name, sev, num in hits:
                seen[name] = (int(num), sev)
            for name in sorted(g):
                want = g[name]
                got = seen.get(name)
                if got is None:
                    lines.append("MISSING-ROW  §五 缺口表缺 `%s`（版面 %d 枚／%s）" % (name, want[0], want[1]))
                    red += 1
                elif got != want:
                    lines.append("MISMATCH     §五 `%s`：文档 (%d, %s) ≠ 版面 (%d, %s)"
                                 % (name, got[0], got[1], want[0], want[1]))
                    red += 1
            for name in sorted(set(seen) - set(g)):
                lines.append("EXTRA-ROW    §五 `%s`：文档有这一行而版面没有" % name)
                red += 1
            if not red:
                lines.append("OK           §五 缺口表｜%d 行 ×（枚数, 严重度）逐格与版面相符" % len(g))
            continue
        if tag == "KG 归域":
            a, b, names, d1, d2 = hits[0]
            got = [x.strip() for x in names.split(",")]
            # 「归域」与「有节点」是两件事：前者问域有没有被分进某一层，后者问这一层里有没有记录。
            if ((int(a), int(b)) != (v["placed"][0], v["placed"][1]) or got != v["unplaced"]
                    or (int(d1), int(d2)) != (v["dom"][0], v["dom"][1])):
                lines.append("MISMATCH     KG 归域：文档 (%s/%s, %s, %s/%s) ≠ 版面 (%d/%d, %s, %d/%d)"
                             % (a, b, names, d1, d2, v["placed"][0], v["placed"][1],
                                ",".join(v["unplaced"]), v["dom"][0], v["dom"][1]))
                red += 1
            else:
                lines.append("OK           KG 归域｜%s / %s，未归层名单逐字相符 %s，有节点 %s / %s"
                             % (a, b, names, d1, d2))
            continue
        bad = [tuple(int(x) for x in h) for h in hits if [int(x) for x in h] != exp]
        if bad:
            # 题面说「复算值」而不是「版面」：verify 那三条复算自判决面，不是版面（标签失效而数字仍对＝假账）。
            lines.append("MISMATCH     %s｜文档 %s ≠ 复算值 %s（命中 %d 处，%d 处不符）"
                         % (tag, "；".join(str(b) for b in bad), exp, len(hits), len(bad)))
            red += 1
        else:
            lines.append("OK           %s｜%s（%d 处命中全部相符）" % (tag, exp, len(hits)))
    return lines, red


def selftest(v, mut, dc, da, vf):
    """三格对照：改坏一个多组数、改坏一个单组数、删掉一行声明。都不红＝仪器没电。"""
    ov = rd(OV)
    n1 = len(claims(v, mut, dc, da, vf))

    def tamper(text, rx, bump):
        m = re.search(rx, text)
        if not m:
            raise AssertionError("自检的靶子不在文档里（正则 %s）——自检自己先要能通电" % rx)
        return text[:m.start()] + m.group(0).replace(m.group(1), str(int(m.group(1)) + bump)) + text[m.end():]

    # 格 1：多组声明里的记录数挪一位
    _, red1 = check({OV: tamper(ov, r"机器可读记录 (\d+) 条", 1)}, v, mut, dc, da, vf)
    # 格 2：删掉「§一 键数」这一整条声明
    m2 = re.search(r"`nodes / unique keys` 印 \d+ / \d+", ov)
    deleted = ov[:m2.start()] + "（这一格本轮被删掉，用来验覆盖面判据）" + ov[m2.end():]
    l2, red2 = check({OV: deleted}, v, mut, dc, da, vf)
    miss2 = len([x for x in l2 if x.startswith("MISSING-CLAIM")])
    # 格 3：单组声明（表格里的一格 19）挪一位——这一型曾经被逐字符解析器放过，
    # 因为 `for x in "19"` 给 (1,9)，正确的 19 反而红；那么错的 20 就更得红。
    _, red3 = check({OV: tamper(ov, r"\| 逻辑层 \| [^\n]*? \| (\d+) \|", 1)}, v, mut, dc, da, vf)
    # 格 4：verify 通道自己也得有牙——把判决面抄进文档的 PASS 数挪一位，必须红在这一条上。
    l4, red4 = check({LIB: tamper(rd(LIB), r"已复跑：\*\*(\d+) PASS", 1)}, v, mut, dc, da, vf)
    hit4 = len([x for x in l4 if x.startswith("MISMATCH") and "公式库 verify" in x])
    tooth4 = hit4 >= 1 or (vf is None and red4 >= 1)   # 载体缺席时它自己已经判红，这一格不必再要求 MISMATCH
    ok = red1 >= 1 and miss2 >= 1 and red3 >= 1 and tooth4
    print("自检四格对照（判据不许自己证自己）：")
    print("  格 1 改坏一个数 → 红 %d 条（要求 ≥1）：%s" % (red1, "通过" if red1 else "仪器看不见篡改"))
    print("  格 2 删掉一行声明 → MISSING-CLAIM %d 条（要求 ≥1）：%s" % (miss2, "通过" if miss2 else "覆盖面判据是恒绿的"))
    print("  格 3 改坏单组声明 → 红 %d 条（要求 ≥1）：%s" % (red3, "通过" if red3 else "单组命中被逐字符解析，这一型看不见"))
    print("  格 4 改坏 verify 抄来的数 → 红在这一条上 %d 次（要求 ≥1）：%s"
          % (hit4, "通过" if tooth4 else "verify 通道没有牙"))
    print("  覆盖面分母：声明词表 %d 条，真跑时全部要在文档里命中" % n1)
    return ok


def changelog_scope(ch):
    """CHANGELOG 是倒序台账：本轮的数只住在「批记录」那一条条目里，历史条目讲的是当时。
    取那条标题到下一条 `### ` 标题之间的区域当判定面；取不到就返回 None，由 main 判红而不是静默跳过。"""
    lines = ch.split("\n")
    heads = [(i, l) for i, l in enumerate(lines) if l.startswith("### ")]
    want = [(i, l) for i, l in heads if "批记录" in l]
    if not want:
        return None, None
    i, h = want[0]
    nxt = [j for j, _ in heads if j > i]
    return "\n".join(lines[i:nxt[0] if nxt else len(lines)]), h


def main():
    only_selftest = "--selftest" in sys.argv
    v = parse_face(rd(FACE_REL))
    mut = parse_mutants(rd(MFACE_REL))
    gj = json.loads(rd(GJSON_REL))
    assert len(gj["nodes"]) == v["nodes"] and len(gj["edges"]) == v["edges"], \
        "第二口径失败：graph.json 与版面不同值"
    # 域 -> 记录节点数：直接读 graph.json 节点自带的 `domain` 字段（不解析号段，
    # 号段形状变了也不会让这里静默数错）。
    dc, da, nodom = {}, {}, 0
    for n in gj["nodes"]:
        d = n.get("domain")
        if not d:
            # doc 节点可以没有域（桥接类账本就挂在号段域之外）；record 节点不许。
            assert n.get("node_type") != "record", "记录 %s 没有 domain 字段——域名单复算无从下手" % n["id"]
            nodom += 1
            continue
        da[d] = da.get(d, 0) + 1
        if n.get("node_type") == "record":
            dc[d] = dc.get(d, 0) + 1
    assert sum(dc.values()) == v["records"], "域名单复算不等于版面记录数"
    assert sum(da.values()) + nodom == v["nodes"], "域名单（全部节点）＋无域节点不等于版面节点数"
    vf = parse_verify(v["records"])
    print("verify 通道：%s" % ("判决面缺席（三条声明将判 MISSING-CARRIER）" if vf is None else "PASS／SKIP／FAIL＝%s" % vf))
    if not selftest(v, mut, dc, da, vf):
        print("==> 仪器自检不过：判定面一律不可引用")
        return 2
    if only_selftest:
        return 0
    docs = {}
    for rel in [OV, KG, IX, LIB, CH]:
        docs[rel] = rd(rel)
    scope, head = changelog_scope(docs[CH])
    if scope is None:
        print("==> CHANGELOG 里没有「批记录」条目（历史条目不归本判据管），判定面塌缩，不放行")
        return 1
    docs[CH] = scope
    print("CHANGELOG 判定面＝条目「%s」（%d 行）" % (head, len(scope.split("\n"))))
    lines, red = check(docs, v, mut, dc, da, vf)
    print("\n".join(lines))
    n_claims = len(claims(v, mut, dc, da, vf))
    oks = len([x for x in lines if x.startswith("OK")])
    print("---- 判决 ----")
    print("声明词表 %d 条，相符 %d 条，红 %d 条（含 MISSING／EXTRA／MISMATCH）" % (n_claims, oks, red))
    print("版面读数：记录 %d／节点 %d／边 %d／域 %d/%d／变异体 %s" % (
        v["records"], v["nodes"], v["edges"], v["dom"][0], v["dom"][1], mut))
    if red:
        print("==> 文档与版面分叉：以版面为准改文档（或按版面变形同批改词表），本面不得放行")
        return 1
    print("==> 全符：文档里每一条「版面现印」的数都能被这台仪器复算")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
