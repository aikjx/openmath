# 记录 Schema（v0.1）

> 本文件是**权威 schema 说明**。机器校验由 `openmath lint` 实现，本文件描述语义与判定规则。

## 一、通用字段（所有记录类型共有）

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | ✅ | 当前 `"0.1"` |
| `id` | string | ✅ | 格式 `OM-<类型>-<域>-<4位序号>`，见[编号规范](../../00-宪章/04-标识与编号规范.md) |
| `kind` | enum | ✅ | `definition` `formula` `theorem` `conjecture` `counterexample` `algorithm` `problem` `programme` |
| `title_zh` | string | ✅ | 中文标题（源语言） |
| `title_en` | string | ✅ | 英文标题 |
| `domain` | string | ✅ | 域代码，见编号规范 |
| `msc` | list[string] | ⬜ | MSC 2020 号，如 `11M06` |
| `status` | enum | ✅ | 见[证据等级标准](../../00-宪章/03-证据等级标准.md) 第三节 |
| `evidence_level` | enum | ✅ | `L0`–`L6` |
| `tags` | list[string] | ⬜ | 自由标签，用于图索引 |
| `assumptions` | list[string] | ✅ | **可为空数组，但字段必须存在**（[红线三](../../00-宪章/02-诚实红线.md)） |
| `provenance` | object | ✅ | 见下 |
| `revision` | int | ✅ | 从 1 起，每次内容变更 +1 |
| `created` | date | ✅ | `YYYY-MM-DD` |
| `updated` | date | ✅ | `YYYY-MM-DD` |

### `provenance` 对象

```yaml
provenance:
  ai_assisted: false        # 必填；true 时必须填 ai_role
  ai_role: ""               # drafting | translation | verification | full_generation
  sources:                  # 可选，文献来源
    - type: doi             # doi | arxiv | book | url
      value: "10.1090/..."
  contributors: ["github-id"]
```

**强制规则**（[红线五](../../00-宪章/02-诚实红线.md)）：`ai_assisted: true` 的记录，`evidence_level` 不得 ≥ `L4`，除非 `verification.L4.human_reviewed: true`。

## 二、公式专用字段（`kind: formula`）

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `latex` | string | ✅ | LaTeX 表达式（不含 `$`） |
| `sympy` | string | ⬜ | SymPy 可解析的表达式，供 L3 |
| `symbols` | list[object] | ✅ | 符号表，见下 |
| `domain_of_validity` | string | ⬜ | 适用范围的自然语言描述 |
| `specializations` | list | ⬜ | 特殊情形（引用其他 ID） |
| `generalizations` | list | ⬜ | 推广（引用其他 ID） |
| `related` | list[string] | ⬜ | 相关条目 ID |
| `verification` | object | ✅ | 见下 |
| `caveat` | string | ⬜ | 已知失效模式（数值/符号验证的陷阱） |

### `symbols` 元素

```yaml
symbols:
  - name: "s"
    meaning_zh: "复变量"
    type: complex        # real | complex | integer | natural | matrix | function | ...
    constraints: "Re(s) in (0,1) 时为临界带"
```

### `verification` 对象

```yaml
verification:
  levels:
    L2:
      passed: true
      engine: mpmath
      precision_digits: 50
      sample_count: 1000
      seed: 20260910
      max_abs_residual: "3.2e-49"
      script: "05-验证中心/03-结果/2026/09/OM-F-AN-0002-L2.py"
      last_run: "2026-09-10"
    L3:
      passed: true
      engine: sympy
      method: "simplify(lhs - rhs) == 0"
      script: "..."
  L4:
    passed: false
    system: ""
    note: "尚未形式化"
```

**关键**：`script` 必须指向一个**真实存在且可执行**的文件。`lint` 会检查路径存在性。

## 三、定理专用字段（`kind: theorem`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `statement_latex` | string | 定理陈述 |
| `hypotheses` | list[string] | 前提（比 `assumptions` 更细，逐条列出） |
| `conclusion_latex` | string | 结论 |
| `proof` | object | `{sketch, references[], formal: {...}}` |
| `is_conditional` | bool | 若为 true，必须在 `conditional_on` 中列出依赖的猜想 |
| `independent_of` | string | 若已知独立，填公理系统 |

## 四、猜想专用字段（`kind: conjecture / problem`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `statement_latex` | string | 陈述 |
| `proposed_by` | string | 提出者 |
| `proposed_year` | int | 提出年份（未知填 null，**不得猜**） |
| `current_status` | enum | `OPEN` `PARTIAL` `RESOLVED` `REFUTED` `UNDECIDABLE` `DISPUTED` |
| `partial_results` | list | 部分进展，含年份与作者 |
| `resolution` | object | 若已解决：年份、作者、方法、形式化状态 |
| `refutation` | object | 若已证伪：反例、年份、发现者 |
| `prize` | string | 奖金信息（如千禧年 100 万美元） |
| `equivalent_forms` | list[string] | 等价表述（引用 ID） |
| `implications` | list | 蕴含关系 |
| `fact_check` | object | `{status: VERIFIED | UNVERIFIED, sources[], note}` |

**强制规则**（[红线八](../../00-宪章/02-诚实红线.md)）：来源不明的近期声明必须 `fact_check.status: UNVERIFIED`。

## 五、纲领专用字段（`kind: programme`）

见 [04-数学统一场论/README.md](../../04-数学统一场论/README.md)，含 `axioms`、`scope`、`falsifiable_predictions`、`bridges`、`evaluation`。

## 六、JSON Schema（机器版）

`openmath lint` 内置等价校验（纯标准库实现），不依赖外部 JSON Schema 库。
若需与外部工具对接，可运行：

```bash
python -m openmath schema --export-json > 02-公式库/schema/openmath.schema.json
```

## 七、校验规则清单（L0）

`lint` 依次检查：

1. 文件可被解析（YAML/JSON）
2. `id` 与文件名一致
3. `id` 全局唯一
4. 必填字段齐全
5. 枚举值合法（`status`、`evidence_level`、`domain`、`kind`）
6. `status: VERIFIED` 必须带级别括号
7. `assumptions` 字段存在
8. `verification.script` 路径存在
9. 引用 ID 可解析（`related`、`specializations` 等）
10. `ai_assisted: true` 时不违反 L4 规则
11. 不得引用 `fact_check.status: UNVERIFIED` 的条目作为 L3+ 证据
12. 中文字段非空（防占位符提交）

任一项失败即 L0 不通过，CI 拒绝合并。
