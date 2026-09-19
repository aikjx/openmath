# OpenMath 理论锻造报告：关系发现 · 反例搜索 · 理论体系网
> 生成时间：2026-09-19T21:39:12　|　生成者：`06-AI自动化/01-工作流/openmath_theory.py`（S7）
> **诚实声明**：本报告全部内容为 **L2 级候选关系**与有限对象上的精确计算，**不证明任何命题、不宣称发现新定理**。每一条关系的成立范围都仅限于被检验的对象集合。

## 0. 一句话结论
1. 机器在五族对象上共生成 **411** 条候选关系；通过留出集者 **343** 条。
2. 把这批通过者拿到**更大的对象库**上做外推检验，**29** 条当场被具体反例证伪——它们是本报告最有价值的部分。
3. 机器重发现 **5** 条已知定理（握手定理、χ≥ω、欧拉–庞加莱、α·χ≥|V|），这构成对搜索机制本身的**校准**。
4. 留出集直接证伪 **34** 条、另有 29 条在外推阶段证伪；所有反例均**保留**。
5. **没有证明任何东西**。被大规模检验洗过的候选里，只有第 7 节那一条例证充足到值得人工复核。

## 1. 方法：发现 -> 留出 -> 外推 -> 三层降噪
| 环节 | 做法 | 目的 |
|---|---|---|
| ① 对象库 | 为整数/图/群/划分/链复形各算一组**精确不变量**（有理算术） | 提供可比较的数据面 |
| ② C1 线性通道 | 枚举 ≤3 支撑 + 可选常数项，Q 上精确求秩，取零空间的原始整系数 | 找 Σc·inv = 0 |
| ③ C2 单项式通道 | 指数在 {−2,−1,1,2} 中搜 Π inv^e = 常数 | 找乘法关系 |
| ④ C3 不等式通道 | Graffiti 传统：X ≤ Y、X ≤ Y+Z、X ≤ Y·Z，要求**尖锐** | 找紧界 |
| ⑤ 留出集 | 按确定性规则每 4 个留 1 个不参与发现，只用于反例搜索 | 防止自证 |
| ⑥ 规模外推 | 用更大的库（整数≤160、划分≤11、图/群/复形加实例）重测通过者 | 防止小样本错觉 |
| ⑦ 三层降噪 | 定义式 / 由定义式线性张成 / 发现集上取常值 | 把重言式与巧合剔出候选 |

> **为什么必须做 ⑥**：Pólya 猜想、Mertens 猜想都在很大的范围内「没有反例」之后被推翻。只在自己构造的小库里自洽，是这套方法最容易犯的错。

## 2. 对象库
| 对象族 | 对象数 | 发现集 | 留出集 | 不变量数 | 被帕累托剔除 |
|---|---|---|---|---|---|
| 整数（算术函数） | 59 | 45 | 14 | 15 | 127 |
| 有限简单图 | 61 | 46 | 15 | 16 | 564 |
| 有限群 | 26 | 20 | 6 | 12 | 243 |
| 整数划分 | 66 | 50 | 16 | 12 | 174 |
| 有限链复形 | 14 | 11 | 3 | 14 | 404 |
本轮未触发不变量排除（各对象的不变量计算口径一致，可比）。

## 3. 校准：机器重新找到的已知定理
这是判断搜索机制有没有在瞎蒙的唯一硬指标。
| 对象族 | 已知定理 | 机器写出的形式 |
|---|---|---|
| 有限简单图 | 握手定理 | degree_sum - 2·edges = 0 |
| 有限简单图 | χ(G) ≥ ω(G)（色数不小于团数） | clique_number ≤ chromatic_number |
| 有限简单图 | α(G)·χ(G) ≥ |V| | vertices ≤ chromatic_number·independent_number |
| 整数划分 | λ 与 λ' 的不同部大小个数相等 | conjugate_distinct - distinct_parts = 0 |
| 有限链复形 | 欧拉-庞加莱公式（有限 CW 复形） | euler_betti - euler_cells = 0 |
> 反过来看，并非所有已知定理都能被召回：`φ(n) ≤ n` 因在库内从不取等（不满足尖锐性）而被 C3 的过滤挡掉，这是搜索设计上的取舍，不是数学判断。

## 4. 候选清单（通过留出集 + 通过规模外推）
### 4.1 恒等式类（全部）
| 对象族 | 通道 | 陈述 | 独立校验数 |
|---|---|---|---|
| 整数划分 | monomial | `conjugate_distinct·distinct_parts^-1 = 1` | 49 |
| 有限链复形 | linear | `has_torsion - torsion_count = 0` | 10 |

### 4.2 不等式：按族取最紧的若干条

**整数（算术函数）**：共 48 条，以下为项数最少的前 8 条。
| 陈述 | 右端项数 | 发现集最小间隙 |
|---|---|---|
| `Omega ≤ aliquot` | 1 | 1 |
| `Omega ≤ phi` | 1 | 1 |
| `P_plus ≤ rad` | 1 | 3 |
| `mu ≤ squarefree` | 1 | 2 |
| `n_over_rad ≤ aliquot` | 1 | 1 |
| `n_over_rad ≤ phi` | 1 | 1 |
| `omega ≤ Omega` | 1 | 1 |
| `p_minus ≤ P_plus` | 1 | 1 |

**有限简单图**：共 69 条，以下为项数最少的前 8 条。
| 陈述 | 右端项数 | 发现集最小间隙 |
|---|---|---|
| `chromatic_number ≤ vertices` | 1 | 1 |
| `components ≤ clique_number` | 1 | 1 |
| `components ≤ independent_number` | 1 | 1 |
| `connected ≤ spanning_trees` | 1 | 2 |
| `diameter ≤ edges` | 1 | 1 |
| `edges ≤ degree_sum` | 1 | 1 |
| `girth ≤ edges` | 1 | 1 |
| `girth ≤ vertices` | 1 | 1 |

**有限群**：共 54 条，以下为项数最少的前 8 条。
| 陈述 | 右端项数 | 发现集最小间隙 |
|---|---|---|
| `abelian ≤ center_size` | 1 | 1 |
| `abelian ≤ elements_at_exponent` | 1 | 1 |
| `abelian ≤ max_element_order` | 1 | 1 |
| `center_size ≤ class_number` | 1 | 2 |
| `class_number ≤ order` | 1 | 3 |
| `elements_at_exponent ≤ order` | 1 | 1 |
| `exponent ≤ order` | 1 | 2 |
| `involutions ≤ proper_subgroups_count` | 1 | 1 |

**整数划分**：共 61 条，以下为项数最少的前 8 条。
| 陈述 | 右端项数 | 发现集最小间隙 |
|---|---|---|
| `conjugate_distinct ≤ conjugate_length` | 1 | 1 |
| `conjugate_distinct ≤ largest_part` | 1 | 1 |
| `conjugate_distinct ≤ length` | 1 | 1 |
| `conjugate_length ≤ sum` | 1 | 1 |
| `distinct_parts ≤ conjugate_length` | 1 | 1 |
| `distinct_parts ≤ largest_part` | 1 | 1 |
| `distinct_parts ≤ length` | 1 | 1 |
| `durfee ≤ conjugate_length` | 1 | 1 |

**有限链复形**：共 109 条，以下为项数最少的前 8 条。
| 陈述 | 右端项数 | 发现集最小间隙 |
|---|---|---|
| `b0 ≤ betti_total` | 1 | 1 |
| `b0 ≤ c0` | 1 | 1 |
| `b1 ≤ c1` | 1 | 1 |
| `b2 ≤ b0` | 1 | 1 |
| `b2 ≤ c2` | 1 | 1 |
| `b2 ≤ dim` | 1 | 1 |
| `b2 ≤ euler_consistent` | 1 | 1 |
| `betti_total ≤ cell_total` | 1 | 2 |

## 5. 反例台账（本报告最有价值的部分）
### 5.1 留出席位上直接失败的
| 对象族 | 陈述 | 反例对象 | 反例值 |
|---|---|---|---|
| 有限简单图 | `bipartite ≤ connected` | graph:C4+P3 | 1 > 0 |
| 有限简单图 | `components ≤ bipartite+girth` | graph:K2+K2+K2 | 2 > 1 |
| 有限简单图 | `diameter ≤ clique_number+independent_number` | graph:P8 | 7 > 6 |
| 有限简单图 | `diameter ≤ independent_number+max_degree` | graph:P8 | 7 > 6 |
| 有限简单图 | `girth ≤ clique_number+spanning_trees` | graph:C4+P3 | 4 > 2 |
| 有限简单图 | `min_degree ≤ girth+spanning_trees` | graph:K2+K2+K2 | 1 > 0 |
| 有限简单图 | `bipartite ≤ components·connected` | graph:C4+P3 | 1 > 0 |
| 有限群 | `exponent ≤ max_element_order+proper_subgroup_order_types` | group:D5 | 10 > 8 |
| 有限群 | `involutions ≤ center_size+proper_subgroup_order_types` | group:D5 | 5 > 4 |
| 有限群 | `involutions ≤ elements_at_exponent+proper_subgroup_order_types` | group:D5 | 5 > 3 |
| 有限群 | `max_element_order ≤ class_number` | group:D5 | 5 > 4 |
| 有限群 | `involutions ≤ center_size·proper_subgroup_order_types` | group:D5 | 5 > 3 |
| 有限群 | `max_element_order ≤ center_size·class_number` | group:D5 | 5 > 4 |
| 有限群 | `order ≤ class_number+max_element_order` | group:D5 | 10 > 9 |
| 有限链复形 | `b1 ≤ dim` | complex:wedge_two_circles | 2 > 1 |
| 有限链复形 | `b1 ≤ b0+b2` | complex:wedge_two_circles | 2 > 1 |
| 有限链复形 | `b1 ≤ b2+euler_consistent` | complex:wedge_two_circles | 2 > 1 |
| 有限链复形 | `has_torsion ≤ euler_betti` | complex:wedge_two_circles | 0 > -1 |
| 有限链复形 | `has_torsion ≤ euler_cells` | complex:wedge_two_circles | 0 > -1 |
| 有限链复形 | `torsion_count ≤ euler_betti` | complex:wedge_two_circles | 0 > -1 |

（另有 14 条，见 `theory_forge.json`）

### 5.2 通过留出集、却在更大规模上崩掉的
这批最能说明问题：它们在小库里「完全成立」，只因为库里缺一个够大的对象。
| 对象族 | 陈述 | 反例对象 | 反例值 |
|---|---|---|---|
| 有限简单图 | `avg_degree ≤ chromatic_number+clique_number` | graph:K5x5 | K5x5: 5 > 4 |
| 有限简单图 | `avg_degree ≤ clique_number+diameter` | graph:K5x5 | K5x5: 5 > 4 |
| 有限简单图 | `independent_number ≤ clique_number+max_degree` | graph:C10 | C10: 5 > 4 |
| 有限简单图 | `max_degree ≤ chromatic_number+independent_number` | graph:W9 | W9: 8 > 7 |
| 有限简单图 | `min_degree ≤ components+spanning_trees` | graph:K5+K5 | K5+K5: 4 > 2 |
| 有限简单图 | `triangles ≤ degree_sum` | graph:K9 | K9: 84 > 72 |
| 有限简单图 | `triangles ≤ clique_number+spanning_trees` | graph:K5+K5 | K5+K5: 20 > 5 |
| 有限简单图 | `avg_degree ≤ chromatic_number·clique_number` | graph:K5x5 | K5x5: 5 > 4 |
| 有限简单图 | `avg_degree ≤ clique_number·diameter` | graph:K5x5 | K5x5: 5 > 4 |
| 有限简单图 | `edges ≤ clique_number·vertices` | graph:K5x5 | K5x5: 25 > 20 |
| 有限简单图 | `min_degree ≤ clique_number·diameter` | graph:K5x5 | K5x5: 5 > 4 |
| 有限简单图 | `triangles ≤ avg_degree·max_degree` | graph:K9 | K9: 84 > 64 |
| 有限简单图 | `triangles ≤ clique_number·min_degree` | graph:K9 | K9: 84 > 72 |
| 有限群 | `class_number ≤ center_size+proper_subgroup_order_types` | group:D7 | D7: 5 > 4 |
| 有限群 | `involutions ≤ min_generators+proper_subgroup_order_types` | group:D7 | D7: 7 > 5 |
| 有限群 | `involutions ≤ min_generators·proper_subgroup_order_types` | group:D7 | D7: 7 > 6 |
| 整数划分 | `conjugate_distinct ≤ durfee+ones` | part:(4+3+2) | λ⊢9:(4+3+2): 3 > 2 |
| 整数划分 | `distinct_parts ≤ durfee+ones` | part:(4+3+2) | λ⊢9:(4+3+2): 3 > 2 |
| 整数划分 | `durfee ≤ conjugate_distinct+distinct_parts` | part:(3+3+3) | λ⊢9:(3+3+3): 3 > 2 |
| 整数划分 | `conjugate_rank ≤ durfee+ones` | part:(2+2+2+2+2) | λ⊢10:(2+2+2+2+2): 3 > 2 |
| 有限链复形 | `has_torsion - torsion_count = 0` | complex:double_torsion_cw | 残差 -1 |
| 有限链复形 | `c2 ≤ b1+c0` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `c2 ≤ b2+c0` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `torsion_count ≤ b0` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `torsion_count ≤ euler_consistent` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `torsion_count ≤ b1+has_torsion` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `torsion_count ≤ b2+has_torsion` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `c1 ≤ betti_total·c0` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |
| 有限链复形 | `torsion_count ≤ b0·euler_consistent` | complex:double_torsion_cw | double_torsion_cw: 2 > 1 |

### 5.3 一次自查出来的事故（保留记录）
首轮压力测试中，图族报告了 28 条「证伪」，其中 15 条是**假的**：当时 `_max_independent` 在顶点数 > 12 时返回哨兵值 `-1`，导致 `clique_number` 出现 `-1` 之类的非法取值，进而制造出一堆伪反例。改为精确分支限界算法后重跑，图族真实被证伪数降到 13 条。**教训**：
1. 不变量算不出来时宁可**排除该对象**，也不要塞一个「看起来是数」的哨兵；
2. 反例在被信任之前，必须先确认它背后的数据是合法计算出来的。

## 6. 理论体系网：每个族内部谁由谁决定
| 对象族 | 对象数 | 不变量数 | 秩（线性独立的最大个数） | 可被表出的不变量 |
|---|---|---|---|---|
| 整数（算术函数） | 59 | 15 | 14 | sigma |
| 有限简单图 | 61 | 16 | 15 | edges |
| 有限群 | 26 | 12 | 12 | — |
| 整数划分 | 66 | 12 | 8 | distinct_parts、largest_part、rank、length |
| 有限链复形 | 14 | 14 | 7 | euler_consistent、torsion_count、betti_total、euler_betti、euler_cells |
> **重要**：「独立基」是**库内**概念。换一批对象，主元列就会变。它回答的是「这批数据里有多少信息量」，不是「这些不变量在理论上独立」。

## 7. 一条值得人工复核的候选
**陈述**：划分 λ 与其共轭划分 λ′ 的**不同部大小个数**相等（机器写出形式：`conjugate_distinct − distinct_parts = 0`）

**数值支持**：本轮在 n ≤ 20 的全部 2713 个划分上穷举，反例 0 个。

理由草案（AI 起草，**未经人工复核**，不得称为证明）：

记 λ 的不同部大小为 r_1 > r_2 > … > r_k，各自重数为 m_1,…,m_k。
共轭定义为 λ′_j = #{i : λ_i ≥ j}。当 j 从 1 起逐步增大时，这个计数
先在 j ≤ r_k 时等于 ℓ(λ)；每当 j 越过某个部大小 r_s，计数就减少 m_s。
因此在 j 的正值范围内，该计数恰好取到 1 + (k−1) = k 个互异的值
（首值 ℓ(λ)，之后每越过一个互异部大小下降一次，且每次下降量 m_s > 0，
故取值两两不同）。于是 λ′ 的不同部大小个数也是 k。

**状态**：CANDIDATE_UNVERIFIED（附论证草案，待人工复核后方可升级）。按红线五，AI 起草的论证最多算 L1 结构检查，**不得**据此改写状态。

## 8. 自核验（把方法用在自己的产物上）
| 结果 | 检查项 | 说明 |
|---|---|---|
| ✓ | 候选关系不得带有'已证明'类状态 | 本 pipeline 只允许 CANDIDATE/FALSIFIED/DEGENERATE/DEFINITIONAL/IMPLIED/KNOWN_REDISCOVERED 等状态 |
| ✓ | 候选须标注证据等级与有限域限制 | 防止把 L2 的有限证据读成 L3/L4 的结论 |
| ✓ | 每族必须切分留出集并跑规模外推压力测试 | 防止只用发现集自证——那等于没有检验 |
| ✓ | 被证伪候选必须保留具体反例（不得删除/改写） | 诚实红线二：反例优先，保留比结论更重要 |
| ✓ | 产物须标注 provenance.ai_assisted=true | 诚实红线五：AI 生成内容必须标注且不得单独作为证据 |
| ✓ | 禁用夸大/虚假声明词 | 扫描词表 ['最全面', '最高权限', '已证明黎曼', '我们证明了', '彻底解决', '穷尽全部数学']；否定式使用（如'并非穷尽'）属诚实表述，计入 benign_honest_negations，不计违规 |
共 **6** 项检查，违规 **0** 项。

## 9. 已知缺陷与保留项
1. **支配过滤是记账式的，不是蕴含判定**：C3 的帕累托收敛按「是否更紧」剔除候选，它可能误删「松但现在、将来却重要」的关系；被删的东西仍完整保留在 `theory_forge.json` 的 `dominated_inequalities` 里，未丢弃。
2. **尖锐性过滤会放过真命题**：`φ(n) ≤ n` 之类的严格不等式因为从不取等而不会被召回。
3. **群族零产出**：在线性/单项式通道上，群族没找到任何 ≤3 支撑的精确关系，其不变量矩阵在这些对象上满秩。这是**如实记录**的阴性结果，不是调参失败。
4. **`library_artifact_risk` 只是提示**：当参与不变量在发现集上取值极少时标记为高风险，这是启发式，不构成任何判定。
5. **本轮没有给任何未解猜想增加处理方向**：这些对象与黎曼/ BSD / 霍奇等猜想所需结构不在同一尺度上。会算 D₄ 的中心不等于能攻击任何猜想——这一点在上一轮报告里已经说清楚，此处重申。
6. **本轮顺带修掉引擎里的一个实错**：`structure.py` 此前把群的**指数**取成元素阶的**最大值**（对 S₃ 会得出 3，正确值应为 lcm(2,3)=6）。现已改为最小公倍数，并把旧口径保留在 `max_element_order` 字段以免悄悄抹掉历史取值。这条错误是本轮在做群族关系发现、核对「为什么 D₅ 的指数只有 5」时才暴露出来的——说明把同一个对象放进机器去搜索，确实能逼出手工整理时看不见的错。

## 10. 结论
1. **5 条已知定理被重发现**，说明这套「枚举不变量 + 精确关系检验」的机器是能工作的。
2. **29 条候选在规模外推时被反例打掉**，说明「在自己的小库里自洽」几乎不值钱；两级反例搜索缺一不可。
3. 剔除定义式与退化项后，真正留给人类看的候选不超过个位数，其中只有第 7 节那一条例证足够扎实到值得复核。
4. 这条流水线的产出类型是 **L2 候选供给**，不是定理产出。把两者的距离压缩掉才是进步，把两者的距离说没了就是违规。
