# MEMORY.md — openmath 项目长期约定

## 引擎位置（重要，已变更）
- `openmath_sys` 引擎现收纳于仓库内：`06-AI自动化/02-引擎/openmath_sys/src`
- 旧位置 `my_lib/openmath_sys/`（仓库外）**已废弃**，不要再引用。
- 引擎零第三方依赖（纯标准库，Python 3.10+）。

## 摄取流水线
- 入口：`06-AI自动化/01-工作流/openmath_ingest.py`
- 运行解释器：受管 Python
  `C:/Users/mo/.workbuddy/binaries/python/versions/3.13.12/python.exe`
- OpenMath 官方 CD 共 **38 个**（GitHub API 核实）。
- 产物落点：`09-数据/openmath_cds/`（.ocd 快照 + catalog.json）、
  `09-数据/openmath_4d_analysis.json`、`10-文献与索引/arxiv_index.json`、
  `06-AI自动化/01-工作流/RUN_REPORT.md`。
- 联网失败时回退本地快照 `09-数据/openmath_cds/<name>.ocd`，不报错退出。

## 诚实红线（项目强制，任何产物不得违反）
- 所有 AI 产物必须带 `provenance.ai_assisted = true`。
- 证据等级：catalog=L0、analysis=L2、proof=L4-NOT_ACHIEVED（本库未产出证明）。
- 方程求解仅为计算校验(L2)；CMP 解析成功不代表被证明(L4)。
- arXiv 预印本 `fact_check.status = UNVERIFIED`，不得作为 L3+ 证据。
- 反例与失败样本必须保留并标注，不得静默删除。
- 不自称「完整/权威/终极」。

## 指标口径（易踩坑）
- CMP 可解析率须区分两种口径：
  - 全量口径：分母含自然语言描述型 CMP，数值偏低；
  - 方程型口径：仅统计「含关系运算符且含字母」的 CMP，才反映解析器真实能力。
- 引用该指标时必须标明是哪一种口径。
- **跨引擎不可直接同比**：当前引擎对表达式尾部残留记号一律报错；
  旧实现会静默丢弃尾部（曾致 `2 ln(x+...)` 被截断成常数 `2`，arcsech 假阴性）。
  故旧引擎的高可解析率含「静默截断」成分，数值下降不等于能力退化。
- **漂移根因已查清（2026-09-20）**：跨运行 `cmp_total` 曾出现 176–179 漂移。
  实测**本地快照并不陈旧**（38 个中 37 个与上游逐字节一致），
  真正风险是 `analyze()` 里的静默 `continue` 会无声跳过整个 CD，
  而报告仍显示「XML 解析失败 0」。现已登记 `cds_skipped`（含原因）
  并增加 `consistency` 校验（catalog 性质总数 vs 分析 cmp_total），
  不一致时报告会显式报警。**引用指标前先看这两项。**

## 量词前缀（2026-09-20 已在引擎侧修复）
- OpenMath CMP 惯用 `for all a | a + 0 = a`。旧问题：`for`/`all` 被当变量
  做隐式乘法、`|` 被词法扫描静默跳过，导致解析必失败。
- 现由引擎 `parser.py :: split_quantifier` 在 `parse_text` 入口剥离，
  约束变量记入 `MathExpr.quantified`（models.py 新增字段）。
- 已移除流水线侧重复的剥离逻辑，保持引擎为唯一职责方。
- 修复经 21 项用例验证（量词/回归/误剥离三类），零回归。

## 尾随句读（2026-09-20 已修复）
- CMP 常以句子标点结尾；孤立的 `.` 曾被词法扫描当成数字记号，
  抛 `could not convert string to float: '.'`。现由 `_SENTENCE_TAIL_RE`
  在 `parse_text` 剥掉结尾的 `.`/`,`/`;`（只处理结尾，不影响 `.5` 合法小数）。
- 注：该修复未提升 CMP 解析数（带句点的 CMP 本身多为散文），属正确性修复。

## 引擎残余能力上限（非 bug，属解析范围之外）
- **并列函数应用（2026-09-20 已实现）**：`sin A` 解析为 `sin(A)`（FuncCall），
  而非乘积 `sin·A`。实现两处：`parse_atom` 的 VAR 分支（内置函数名且后随原子 → 应用，
  作用域取到乘方层，故 `sin A^2` 读作 sin(A^2)）；
  `parse_juxta` 增加「内置函数名紧随其后 → 连写乘法」，支撑 `sin A cos B`、`2 sin x`。
  效果：CMP 方程型可解析率 0.3066 → 0.4609（本地快照实测）。
- **散文保护规则（刻意保留，勿放开）**：`factorial n`、`not true` 等多字母词相邻
  **不**插入乘号。放开会让英文散文被误判成乘积，假性抬高解析率，
  属「静默错误」，比解析失败更危险。
- 其他能力上限：lambda 表达式、LaTeX 记号（`\theta`）、绝对值 `|a|`、
  `product [1..n]`、链式关系（`a < b <= c`）、逻辑连接词（`and`/`such that`）、
  以及散文型 CMP。扩大支持均属功能扩展任务。

## 引擎改动的验证闸门（重要）
- 改动 `openmath_sys` 引擎后，**必须**跑
  `06-AI自动化/01-工作流/openmath_audit.py`（S8 独立审计），
  确认「4452 项全过 + 自核验 6 项全过」再引用指标。
- 审计只证明「两套独立算法在给定对象集上一致」，**不证明结论正确**；
  `AUDIT_REPORT.md` 第 5 节列了审计自身盲区，引用前应读。
- 接手续做时，第一步应核查上轮修复是否被并发会话回滚
  （grep `split_quantifier` / `_SENTENCE_TAIL_RE` / `MathExpr.quantified`）。

## 环境注意
- 该仓库存在并发修改（其他自动化/会话同时写入）。
  运行或改动前建议先确认引擎与脚本的当前状态，避免基于过期前提操作。
- Bash 环境出现过 PATH 异常（`ls`/`dirname` not found），
  可改用 PowerShell 执行；PowerShell 对中文 stdout 有编码问题，
  建议脚本内写文件再读取。

## 子项目 projects/silent-monitor（Rust 无感监听工具，2026-09-21 新建）
- 位置：`projects/silent-monitor/`（`D:/a10/aikjx/code/my_lib/openmath/projects/silent-monitor`）。
- GitHub（独立开源，2026-09-21 已推送）：https://github.com/aikjx/silent-monitor
  （公开仓库，默认分支 main，提交人 aikjx <aikjx@users.noreply.github.com>，含初始 feat 提交 + Cargo.lock 提交）。
  推送凭据走 `~/.git-credentials` 的 github.com token；本环境 push 须用
  `git -c credential.helper= -c credential.helper=store` 绕过 helper-selector，否则卡死。
- 性质：纯标准库、零第三方依赖的 Rust 新手向小工具；与 openmath 引擎无关，是独立 demo。
- 能力：后台无感监听（DETACHED_PROCESS / process_group 守护），间隔可调
  （`--quick`=60s、`--slow`=600s、`-i <秒>` 自定义），日志写 `silent-monitor.log`。
- 一键关闭：`silent-monitor stop` → 读 `silent-monitor.pid` 调 taskkill/kill 杀进程并清 PID；
  另用 `silent-monitor.stop` 信号文件做优雅退出兜底。
- 验证：`cargo build` 通过；实跑 start→(多心跳)→stop 确认进程无残留、PID 清理。
- 改监听逻辑：编辑 `src/main.rs` 里 `run_loop` 中 `log_line(&msg)` 处。

## 子项目 xiaobai（原 xiaobai_voice，独立开源）
- 源：`D:/a10/aikjx/gitcode/infotopograph/projects/xiaobai_voice`。
  注意 `infotopograph` 本身是 **`aikjx/mox` 仓库的本地克隆**（远端：gitcode.com/aikjx/mox 与 github.com/aikjx/mox）。
- 独立开源副本：`D:/a10/aikjx/gitcode/xiaobai` → **https://github.com/aikjx/xiaobai**
  （公开，main，Apache-2.0 LICENSE，65 文件，提交人 aikjx）。
- **品牌决策（2026-09-22）**：产品定位为「每个人的 AI 伙伴与助手」，品牌 =「小白（Xiaobai）」；
  `voice` 只作能力模块名（Python 包名 `xiaobai_voice` 不改，代码不动）。
- 已于 2026-09-22 将仓库由 `xiaobai_voice` 重命名为 `xiaobai`（PATCH /repos，旧链接自动 301 重定向）；
  本地目录同步改为 `gitcode/xiaobai`；README 顶部改为「小白 · 每个人的 AI 伙伴与助手」并突出离线/隐私；
  仓库 description + topics 已更新。
- 策略：robocopy 复制出去后建独立仓库推送，**未改动 mox 仓库**；故 mox 内与独立副本各有一份，需用户决定是否从 mox 解绑。
- 内容：离线语音服务（ASR Paraformer-zh+sherpa-onnx；TTS CosyVoice2/Fish-Speech-S2/浏览器兜底）
  + Rust 核心 `xiaobai_core`（PyO3：dsp/intent/operators/config/models）+ 桌面小白浮窗 + 快捷键。
- **mox 品牌痕迹已向后兼容清理（2026-09-22，提交 c8571a8）**：
  对外品牌（配置/日志/模型目录、环境变量、UI 文案、作者）迁移为新品牌 `xiaobai`
  （`%APPDATA%\xiaobai`、`~/.xiaobai/models/voice`、`XIAOBAI_*` 环境变量），
  并保留 `mox/xiaobai`、`~/.mox/...`、`MOX_*` 作为 **legacy 回退**（新路径缺失时自动沿用旧路径，不丢用户数据）。
  **刻意保留不变**：`mox-system`/`mox-expert` 后端桥、`MoxAdmin` RBAC 角色名、`voice_proxy` 端口 13130 —— 改了会破坏与 mox 后端的互通。
  验证：`compileall` + `cargo check` 均 exit=0。
- 仍开放（待用户决定）：是否从 mox 仓库解绑该子目录；是否彻底移除 mox 后端桥引用（会断互通，不建议）。
- 推送凭据同 silent-monitor：`-c credential.helper= -c credential.helper=store` 绕过 helper-selector。
