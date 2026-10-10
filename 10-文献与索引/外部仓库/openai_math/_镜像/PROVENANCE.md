# 镜像来源与抓取日志（PROVENANCE）

**上游**：<https://github.com/openai/math>（Apache License 2.0，`LICENSE` 已镜像：11,357 B，
md5 前缀 `86d3f3a95c32`）
**pin**：`fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb`（= 抓取当日 `main` 的头指针；GitHub API 自报
`pushed_at = 2026-10-08T05:20:00Z`）
**抓取时刻**：2026-10-10 23:48 – 2026-10-11 00:20（本地钟，Asia/Shanghai）
**抓取范围**：**只有目录层与台账层**。未取 PDF、未取 `.tex` 正文、未取 `lean/OAI/**.lean`（122,458 个文件）。
**上游体积**（解释本库"为什么不整体镜像"）：GitHub API `repos/openai/math` 的 `size` = **822,061 KB**
（≈822 MB，该字段是仓库 git 目录体积、含全部历史），`default_branch = main`，`pushed_at = 2026-10-08T05:20:00Z`。
现取时刻 2026-10-11 00:25（本地钟）；该 JSON 只做本次读数用，未留档。

---

## 一、逐文件指纹

| 文件 | 字节 | md5 | 来源路径 |
| --- | --- | --- | --- |
| `CONTENTS.md` | 638,727 | `d4d03db99fd3db8a306ae2ab296c7af7` | `/CONTENTS.md` |
| `overview.tex` | 321,928 | `1a46f7a5a27a46bebbd200491eadb3a3` | `/overview.tex` |
| `formalization.yaml` | 79,482 | `3d2d0d37e7f01d3ab8eab7bc468b359d` | `/lean/formalization.yaml` |
| `history.md` | 2,281 | `169275d5b279f20a29fed9965e5092e7` | `/history.md` |
| `README.md` | 4,190 | `99d103e0fb2db330b3ccc76223466404` | `/README.md`（仓库根） |
| `lean-README.md` | 650 | `ad12f51fb9f439c06ecf9460d2c9119a` | `/lean/README.md` |
| `LICENSE` | 11,357 | `86d3f3a95c324c9479bd8986968f4327` | `/LICENSE` |
| `git_paths.txt.gz` | 908,791 | `844251200b05cb5cd543b92e74b8162d` | blobless clone 后 `git ls-tree -r --name-only HEAD`，**133,955 行** |
| `comparator_json/` | 416 份，`du -sk` = 565 | 拼接后 md5 `7c4b2ccec8cfcb4ba646e6b1f266e2f8` | `/lean/ComparatorChallenges/*.json` |
| `lean_probe/docs_003.md` | — | `3f51e406df3423e2b6250a2499c1c437` | `/lean/docs/003.md` |
| `lean_probe/docs_007.md` | — | `ca3a94e1a51201b27bf352e015e0b1e8` | `/lean/docs/007.md` |
| `lean_probe/docs_013.md` | — | `26f2c6aa28148477050fb7f711d6b2f9` | `/lean/docs/013.md` |
| `lean_probe/ComparatorChallenges_README.md` | 1,060 | `1c36f46aa1f3296d92cdaa56147ef9e7` | `/lean/ComparatorChallenges/README.md` |
| `lean_probe/lean-toolchain` | 25 | `fe6195d02cc4cc628ced5ae0aca74814` | `/lean/lean-toolchain`，内容逐字 `leanprover/lean4:v4.34.1` |
| `lean_probe/lakefile.lean` | 15,457 | `c8078fb22110e025937c45f02a84de9c` | `/lean/lakefile.lean`（30 条 `require`；`fixedToolchain := true`） |
| `lean_probe/lake-manifest.json` | 14,622 | `8c3ec864da5d9ce3cd9dcc22ad4bf601` | `/lean/lake-manifest.json`（42 个包，42/42 带 `rev`） |
| `withdrawal_notices/Algebraicity-of-Kuga-Satake-Correspondences-for-K3-Surfaces-October-3-2026.md` | 996 | `e31ef4062fc921110c5bf3790da6de51` | `/preprints/Algebraicity-of-Kuga-Satake-Correspondences-for-K3-Surfaces-October-3-2026/README.md`（撤回通告） |
| `withdrawal_notices/Algebraicity-of-Weil-classes-on-split-abelian-eightfolds-September-18-2026.md` | 1,385 | `2029df9087fe0893d595df6d4e97ec1b` | `/preprints/Algebraicity-of-Weil-classes-on-split-abelian-eightfolds-September-18-2026/README.md`（撤回通告） |
| `withdrawal_notices/The-rational-Hodge-conjecture-for-products-of-K3-surfaces-October-4-2026.md` | 1,069 | `0a22f2ac611b79d4e8734ff93dd12a18` | `/preprints/The-rational-Hodge-conjecture-for-products-of-K3-surfaces-October-4-2026/README.md`（撤回通告） |

`_生成/` 由 `_脚本/parse_openai_math.py` 现算，不在本表登记指纹（重跑即变，指纹没有意义）；
其自报行数与体积写在 `stats.txt` 的 inputs 块里。

---

## 二、抓取事故三枚（如实记录；②b 是 ② 的事后复测，不单列第四枚）

**① 同名覆盖。** 首轮用一条循环把 `/README.md` 与 `/lean/README.md` 都按 `basename` 落盘，
后者静默覆盖了前者：落盘文件 650 B，而 GitHub API 声明根 README 应为 **4,190 B**。
发现方式正是**把 API 声明的尺寸与盘上字节并读**，不是读内容。
现已分成 `README.md`（4,190 B）与 `lean-README.md`（650 B），两行都进上表。
⇒ 教训：抓多文件到同一目录时，`basename` 不是键；要么保留原路径层级，要么加前缀。

**② 截断未报错。** 先试 GitHub Trees API（`?recursive=1`）拿物理层，`curl` 写出
4,845,568 B 后被传输中断截断，**curl 返回 0**，直到 `json.load` 才暴露
（`Unterminated string starting at line 133814`）。该文件已删除，物理层改用
blobless clone（`--filter=blob:none --no-checkout --depth 1`）+ `git ls-tree`，秒级完成。
⇒ 教训：**网络写盘的成功判据是"能否被解析"，不是退出码**。
**②b 事后复测（2026-10-11）。** 更早还有一回：Trees API 那份"看着写全了"的响应（**5,767,159 B**）
曾被留成 `_镜像/repo_tree.json`，工作树里现已删掉，只在 openmath 自己的 git 历史里
（`git -C ../../../.. show "HEAD:10-文献与索引/外部仓库/openai_math/_镜像/repo_tree.json"` 可取回）。
本轮把它取回逐字节量了一遍，**下列每个数都由 `scratch/RT_probe_face.txt` 印出**（该面 rc=0，
末尾还并列断言了本节引用的 8 个读数，现推与已印同值）：

| 读数 | 值 | 口径 |
| --- | --- | --- |
| 文件字节 | 5,767,159 B | `len(stdout)`；与 `git show \| wc -c` 同值 |
| 其中 NUL（0x00） | **4,183,058 B = 72.53%** | `count(b"\x00")`；`find`..`rfind` 之差＋1 与总数**相等 ⇒ 连成一段** |
| 空洞起点 | 字节 **1,543,150**（第 **38,733** 行） | `json.loads` 的报错位置 |
| 空洞之后 | 从一条 URL 的**中间**接上（`…penai/math/git/blobs/889925…`） | 取末个 NUL 后 60 B |
| `"path"` 键 | **4,982** 条（`"type"` 键同为 4,982） | 子串计数 `b'"path":'` |
| 应有路径数 | **133,955** | `_生成/stats.txt` H 段 `tracked files` 行 |
| 覆盖率 / 缺失 | **3.72%** ／ **128,973** 条 | 4,982 ÷ 133,955；133,955 − 4,982 |
| `"truncated"` 字段 | 出现 **0** 次 | 子串计数；文件不以 `}` 结束，末 40 B 停在 `https://api.github.com/repos/openai/math` |

⇒ 这一型比 ② 更危险：**尺寸看着像成功，七成是零填充，而它不会报错**。它能报出一份
**看似完整**的 4,982 条清点，少掉 128,973 条却**没有任何字段会说它截断**（`truncated` 压根没写进来）。
所以本库物理层的清点判据只认 `git ls-tree --name-only`（H 段），Trees API 一律不作源；
`04-下载与复核操作手册.md` §二 坑② 已把这条写进"不要做的事"。
⇒ **本节写作时自己就踩了一次**：Python 串里的 `\x00` 少打一层反斜杠，把这枚真 NUL 写进了台账本身（就是上面那一格的口径列，落在第 66 行）。它由本轮的“文件里 NUL=1”读数抓出并已修掉，修后本文件 `count(b"\x00") == 0`。**这份文档现在就是它自己那条判据的样本**，引用这格时把这条一起抄走。


**③ `-l` 会诱发按需取回。** 在 blobless clone 上跑 `git ls-tree -r -l`（要 blob 尺寸）
在 2 分钟内不返回，被手动终止；同一仓库 `--name-only` 瞬间出全 133,955 行。
本库**没有**测得 `-l` 的真实耗时与最终字节，故只登记症状与替代方案，不解释成因细节。
可比读数只有 `.git` 体积：clone 完 **4.4 MB** → 终止那次 `-l` 之后 **5.1 MB**，
说明 `-l` 确已按需取回过对象，但**取回了哪些 blob 未清点**（`git count-objects -v` 未在该轮跑）。

---

## 三、实测抓取成本（用于 04 号文档的成本表）

| 动作 | 命令要点 | 实测 |
| --- | --- | --- |
| 目录层镜像 | 8 个 `curl` 到 raw.githubusercontent | 约 1.0 MB，秒级 |
| 物理层清单 | blobless + `--no-checkout --depth 1` clone，clone 完 `.git` = **4.4 MB** | 秒级 |
| 同上，`-l` 被终止后复测 | 同一 `.git` 复测 = **5.1 MB** | 2 分钟未返回，手动终止（见 §二③） |
| 全量 json | `git sparse-checkout set --no-cone '/lean/ComparatorChallenges/*.json'` + `git checkout HEAD`，此后 `.git` = **25,270 KB / 65 个 pack** | **3.175 s**（`time` 实测），416 文件 |
| 单篇稿件（007） | 同上，pattern 换成该目录 `/**` | `sparse-checkout set` **20.488 s**；落盘 **21 个文件**，`du -sk` = **1,133** |
| 单篇稿件（013） | 同上（`set` + `checkout` 一起计时） | **21.280 s**；落盘 **14 个文件**，`du -sk` = **1,053** |
| 撤回第 1 件（1 个目录） | `set --no-cone` 给 **1** 个 pattern + `checkout HEAD` | **3.844 s**；落盘 1 目录 / 2 文件（README 1,385 B + `paper.pdf` 3,687 B） |
| 撤回第 2、3 件（2 个目录） | `set` 换成另外 **2** 个 pattern | **2.299 s**；落盘 2 目录 / 4 文件，**上一轮那个目录从工作树消失**（`set` 是替换语义） |
| 撤回三件一起 | `set` 给 **3** 个 pattern（对象此前已按需取回过） | **1.002 s**；落盘 3 目录 / 6 文件 |

上表两次的 `du -sk` 里绝大部分是那份 PDF：007 的 `final.pdf` = **819,391 B**（注意它不叫 `paper.pdf`），013 的 `paper.pdf` = **764,239 B**；而三份撤回件目录里的 PDF 只有 3,687 / 3,831 / 3,864 B（1 页通告）。
**未测**：`lake build`／`comparator` 的运行时间与内存（本机无 Lean 工具链）。

---

## 四、复现步骤

```bash
# 1) 目录层
for f in README.md CONTENTS.md history.md overview.tex; do
  curl -sfL -o "$f" "https://raw.githubusercontent.com/openai/math/main/$f"
done
curl -sfL -o lean-README.md      https://raw.githubusercontent.com/openai/math/main/lean/README.md
curl -sfL -o formalization.yaml  https://raw.githubusercontent.com/openai/math/main/lean/formalization.yaml
curl -sfL -o LICENSE             https://raw.githubusercontent.com/openai/math/main/LICENSE

# 2) 物理层清单（不要用 -l，见 §二③）
git clone --filter=blob:none --no-checkout --depth 1 https://github.com/openai/math.git repo
git -C repo -c core.quotepath=false ls-tree -r --name-only HEAD | gzip -9 > git_paths.txt.gz

# 3) 台账与全部数字
python ../_脚本/parse_openai_math.py     # 写 ../_生成/{stats.txt,*.csv}

# 4) 只要某几个目录（例如三份撤回通告）：不用 Trees API，不用 -l，一次给全 pattern
git -C repo sparse-checkout set --no-cone \
  '/preprints/Algebraicity-of-Weil-classes-on-split-abelian-eightfolds-September-18-2026/**' \
  '/preprints/Algebraicity-of-Kuga-Satake-Correspondences-for-K3-Surfaces-October-3-2026/**' \
  '/preprints/The-rational-Hodge-conjecture-for-products-of-K3-surfaces-October-4-2026/**'
git -C repo checkout HEAD
```

**`sparse-checkout set` 是替换语义**：新的 pattern 列表会**从工作树里删掉**上一次物化的目录
（实测：第三次只留 2 个目录时，先前取回的 `the-additive-indecomposability-…` 目录消失）。
要同时保留就多写 pattern，别指望它是追加。

**注意**：`_生成/stats.txt` 的 H/I 段依赖 `git_paths.txt.gz` 与 `comparator_json/`；
两者缺席时脚本**明写 "CARRIER ABSENT"** 并让该段不作任何主张（不会静默给 0）。
