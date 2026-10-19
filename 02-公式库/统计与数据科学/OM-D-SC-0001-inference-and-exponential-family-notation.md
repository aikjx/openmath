---
id: OM-D-SC-0001
title_zh: 统计推断与指数族的记号：得分函数、Fisher 信息与自然参数
status: PROPOSED
---

# OM-D-SC-0001 · 统计推断与指数族的记号：得分函数、Fisher 信息与自然参数

\[ score(\theta)=(d/d\theta)\log p(X;\theta),\qquad I_1(\theta)=E_\theta[score^2]=-(d^2/d\theta^2)\log p,\qquad I_n(\theta)=n\,I_1(\theta),\qquad p(x;\eta)=\exp(\eta T(x)-A(\eta)) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-SC-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | SC（统计与数据科学） |
| **录入** | 2026-10-18 |

## 一、要点

`OM-T-SC-0001`（本域首枚记录）在它的 symbols 表里用了三枚**结构名**：`score`、`I_n`、`eta`。图谱的判据只认「出现在某张 `kind: definition` 记录的 symbols 里」为已定义，所以这三枚铸卡之前一直挂在 `UNDEFINED_SYMBOL` 名单上（版面现印 18 → 中途 21 枚，凭据 `scratch/T13_GRAPH_regen.txt` 的缺口分档）。本卡把它们升成定义条目，符号账按第 4 批裁定回到 18 枚——净涨 0，不是靠删掉记录里的 symbols 做出来的。

三处精度要留。一，`I(theta)` 与 `I_n(theta)` 是**两个量**：前者是单次观测的 Fisher 信息，后者是 n 次的总和，i.i.d. 时 `I_n = n·I_1`；`OM-T-SC-0001` 的机器读数取 n=1 与 n=3 两档，把下界写成 `1/I(theta)` 而样本量却是 3，就会差三倍。二，`score` 的期望为零**不是恒等式而是正则条件的产物**（求导与积分交换），本卡固定记号、不担保哪族模型满足它——`OM-T-SC-0001` 的尺度族读数里 `|E[score]|=1.1317766e-58` 那一枚就是这条交换律的现场见证（载体 `scratch/T13_SC0001_face.txt` 判定4）。三，换坐标要带 Jacobian：自然参数坐标里 Fisher 信息是配分函数的曲率 `d²A/dη²`，回到 `q` 坐标须乘 `(dq/deta)²`，二项族两条通道之差的最大值 `2.7369111e-48`（同一载体判定1b）量的就是这一步换算在 15 组 `(m,q)` 上是否闭合。

按第 4 批裁定，**裸字母不铸**：`theta`、`sigma`、`q`、`m`、`T` 五枚仍留在名单外，不进本卡的 symbols——它们要么是标准希腊字母要么是通用估计量记号，铸卡只会把台账灌成与数学无关的字符表。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：记号只在支配模型＋求导与积分可交换（正则条件）这一语境里有意义，本卡不判定哪些模型满足该交换律
- 默认约定：`A(eta)` 是对数配分函数，自然参数化下它的二阶导就是该族在 eta 坐标里的 Fisher 信息；本卡不引入任何关于 A 的界
- 默认约定：索引 n 记观测个数、theta 记被微分的那个参数

## 三、关系

- 用到：OM-D-PR-0001, OM-D-PR-0002
- 相关：OM-T-SC-0001, OM-D-IT-0001

## 四、诚实边界

- 本条登记的是**文献中的记号约定**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了这些记号合法」是错的，读成「这些记号有争议」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本卡**不新增任何数学主张**，只固定记号与口径。它与 `OM-T-SC-0001` 的关系是「用」而不是「证」：那条记录的 L2 读数不由本卡担保。
- `OM-D-IT-0001`（离散无记忆信道的互信息与容量）里的 `I` 是信息量记号，与本卡的 `I_n`（Fisher 信息）**同名不同物**；两串写法不同（`I` 与 `I_n`），判据按整串聚合，所以不会互相假绿——但人读的时候必须分辨。

## 五、来源

- Cramer, H., Mathematical Methods of Statistics, 2nd ed., Princeton (1946), ch.XVIII（得分函数与 Fisher 信息的记号）
- Lehmann, E. L. and Casella, G., Theory of Point Estimation, 2nd ed., Springer (1998), ch.I.6（指数族、自然参数与对数配分函数 A(eta)）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph         # 关系图与缺口判据（写盘：graph.json／流程图／版面）
python -m openmath verify --level L2   # 逐条判决面（定义卡无检查项，判 SKIP）
```
