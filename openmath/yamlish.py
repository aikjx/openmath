"""最小 YAML 子集解析器（零依赖）。

本模块存在的理由：openmath 的核心功能必须能在一台干净的机器上跑起来，
而 PyYAML 不是标准库。若已安装 PyYAML，record 模块会优先使用它；
否则回退到本解析器。

支持的子集（覆盖本库全部记录文件）：
  - 注释（整行与行尾，引号内的 # 不算注释）
  - key: value（标量：字符串/整数/浮点/布尔/null）
  - 引号字符串（单引号与双引号）
  - 嵌套映射（缩进）
  - 序列（- 开头；元素可为标量或映射）
  - 行内列表 [a, b] 与行内映射 {a: 1}
  - 块标量 |、|-、>、>-

不刻意支持：锚点、别名、多文档、复杂标签、流式折叠。
这些在本库的记录文件中不会出现；若出现，请安装 PyYAML。
"""


class YamlishError(ValueError):
    """YAML 子集解析失败。"""


def _strip_comment(line):
    """去掉行尾注释，保留引号内的 # 字符。"""
    out = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "#":
            # 行尾注释：要求前一字符为空或行首
            if not out or out[-1] in " \t":
                break
        out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _tokenize(text):
    """把文本切分为 (indent, content) 序列，丢弃空行与整行注释。"""
    tokens = []
    for raw in text.splitlines():
        if raw.strip() in ("---", "..."):
            continue
        stripped = raw.lstrip()
        if not stripped:
            continue
        content = _strip_comment(stripped)
        if not content.strip():
            continue
        indent = len(raw) - len(stripped)
        tokens.append((indent, content))
    return tokens


def _smart_split(text):
    """按逗号分割，忽略引号与括号内的逗号。"""
    parts = []
    buf = []
    depth = 0
    quote = None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            continue
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_scalar(text):
    raw = text.strip()
    if raw == "":
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p) for p in _smart_split(inner)]
    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1].strip()
        if not inner:
            return {}
        out = {}
        for part in _smart_split(inner):
            key, sep, val = part.partition(":")
            if not sep:
                continue
            out[str(_parse_scalar(key))] = _parse_scalar(val)
        return out
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_block(tokens, index, indent, marker):
    """收集块标量内容。marker 为 |、|-、>、>- 之一。返回 (文本, 新索引)。"""
    fold = marker.startswith(">")
    strip_trailing = marker.endswith("-")
    lines = []
    while index < len(tokens) and tokens[index][0] > indent:
        lines.append(tokens[index][1])
        index += 1
    if fold:
        return " ".join(lines), index
    text = "\n".join(lines)
    if text and not strip_trailing:
        text += "\n"
    return text, index


def _parse_map(tokens, index, indent):
    result = {}
    while index < len(tokens):
        cur_indent, content = tokens[index]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            # 不应出现（应已被嵌套解析消费），跳过以防死循环
            index += 1
            continue
        if content.startswith("- ") or content == "-":
            break
        key, sep, rest = content.partition(":")
        if not sep:
            index += 1
            continue
        key = str(_parse_scalar(key.strip()))
        rest = rest.strip()
        if rest in ("|", "|-", ">", ">-"):
            index += 1
            value, index = _parse_block(tokens, index, indent, rest)
            result[key] = value
            continue
        if rest == "":
            nxt = index + 1
            if nxt < len(tokens) and tokens[nxt][0] > indent:
                value, index = _parse_nodes(tokens, nxt, tokens[nxt][0])
                result[key] = value
            else:
                result[key] = None
                index += 1
            continue
        result[key] = _parse_scalar(rest)
        index += 1
    return result, index


def _parse_seq(tokens, index, indent):
    result = []
    while index < len(tokens):
        cur_indent, content = tokens[index]
        if cur_indent < indent:
            break
        if not (content.startswith("- ") or content == "-"):
            break
        item = content[2:].strip() if content.startswith("- ") else ""
        if item == "":
            nxt = index + 1
            if nxt < len(tokens) and tokens[nxt][0] > cur_indent:
                value, index = _parse_nodes(tokens, nxt, tokens[nxt][0])
                result.append(value)
            else:
                result.append(None)
                index += 1
            continue
        if item[:1] in ("\"", "'") or ":" not in item:
            result.append(_parse_scalar(item))
            index += 1
            continue
        # 行内起始的映射项：把首键虚拟到 cur_indent + 2 层级
        virtual_indent = cur_indent + 2
        sub = [(virtual_indent, item)]
        cursor = index + 1
        while cursor < len(tokens) and tokens[cursor][0] >= virtual_indent:
            sub.append(tokens[cursor])
            cursor += 1
        value, _ = _parse_map(sub, 0, virtual_indent)
        result.append(value)
        index = cursor
    return result, index


def _parse_nodes(tokens, index, indent):
    if tokens[index][1].startswith("- ") or tokens[index][1] == "-":
        return _parse_seq(tokens, index, indent)
    return _parse_map(tokens, index, indent)


def loads(text):
    """解析 YAML 子集文本，返回 Python 对象。"""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    try:
        value, index = _parse_nodes(tokens, 0, tokens[0][0])
    except Exception as exc:  # pragma: no cover - 防御性
        raise YamlishError("YAML 子集解析失败: " + str(exc)) from exc
    if index != len(tokens):
        raise YamlishError(
            "YAML 子集解析中断于第 %d 个 token（共 %d），可能存在不支持的语法；请安装 PyYAML。"
            % (index, len(tokens))
        )
    return value


def load(stream):
    """从文件对象读取并解析。"""
    return loads(stream.read())
