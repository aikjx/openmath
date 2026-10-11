# 知识图谱

> 本目录是**生成物**的家：图数据、关系流程图、版面。除本 README 外全部由 `python -m openmath graph` 覆写，勿手改。
> 上一级 `../README.md` §二 的目录树此前就写了这份 README，但它一直不存在；2026-10-11 补上。

## 一、这里放什么

```
知识图谱/
├── README.md                  本文件（唯一手写）
├── graph.json                 节点＋类型化边（机器可读，图谱的唯一正本）
├── 流程图/                     5 张 Mermaid 关系流程图
│   ├── 00-四层总览.mmd          体系层／逻辑层／方程层／难题层
│   ├── 01-域依赖.mmd            20 个域的分层（读 01-数学体系/域依赖.yaml）
│   ├── 02-公式与定理依赖.mmd     记录之间的 implies/uses/specializes/generalizes/related
│   ├── 03-难题卡点.mmd          难题、攻坚账本、卡点与悬空引用
│   └── 04-桥接与旁证.mmd         桥接与验证文档的旁证边
└── _版面/
    ├── graph_face.txt          ★ 本轮所有计数的唯一载体
    └── graph_mutants_face.txt  ★ 变异体电池的验收日志
```

人读的交叉引用表写在 `../交叉引用索引/`（7 张），缺口明细写在其中的 `缺口检测.md`。

## 二、节点从哪来

| 节点类型 | 来源 | 说明 |
| --- | --- | --- |
| record | `02-公式库/**/OM-*.yaml` | 有 schema、有 `status`／`evidence_level`／`symbols` |
| doc | `OM-*.md` 且**无**同名 `.yaml` | 攻坚账本；`openmath index` 看不到它们，所以图上单列 |
| evidence | `05-验证中心/**` 的结果文档 | 以 `evidenced_by` 边挂到记录上 |

ID 的取值次序：frontmatter `id:` → 表头 `| **ID** | OM-… |` → 文件名里的号段。
文件名 markdown 链接（`[文本](OM-….md)`）**算一条引用边**——24 轮哥德巴赫攻坚就是这样互指的，
只按 ID 建边会把整条攻坚线看成不存在。

## 三、边类型

`related`／`specializes`／`generalizes`／`implies`／`uses`／`bridges`／`cites`／`evidenced_by`。
`../README.md` §六 还列着 `contradicts`：**未实现**，因为记录 schema 里没有「与谁冲突」字段。
每条边带 `via`（住在哪个字段／哪种链接里），所以「这条关系凭什么存在」是可查的。

## 四、复现与判据

```bash
python -m openmath graph            # 生成 14 份产物；rc=0 只说明生成物完好
python -m openmath graph --check    # 只判不写；DEFECT 或不变量故障则 rc=1
python 08-工具/tests/graph_mutants.py   # 9 枚指名变异体，逐类把判据打破
```

不变量（写在 `openmath/flowdocs.py` 的 `check_invariants`）：图不许空节点（EMPTY-CHART）、
生成物不许 0 字节（EMPTY-FILE）、版面与图里不许 CR／NUL／反斜杠、
`XREF-ROWS` 把每张表的行数与图谱现推的期望行数相比——渲染器不许自己证自己。

## 五、引用纪律

- 任何计数：点名 `_版面/graph_face.txt`，并写「当时读数」；版面每次重跑都会移动。
- 任何节点／边／状态：点名 `graph.json`。
- 任何「判据有效」的证据：点名 `_版面/graph_mutants_face.txt`。
- 版面末行的 verdict 是**语料**的判决，不是本目录的判决；`graph` 的 rc=0 不等于语料干净。
- 本目录的生成物不参与扫描集（扫描只认 `OM-*.yaml`／`OM-*.md`），所以重跑不会自指。
