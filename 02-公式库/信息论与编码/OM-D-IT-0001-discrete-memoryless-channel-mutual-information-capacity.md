---
id: OM-D-IT-0001
title_zh: 离散无记忆信道、互信息与容量
status: PROPOSED
---

# OM-D-IT-0001 · 离散无记忆信道、互信息与容量

\[ C=\sup_{p(x)}\ I(X;Y),\qquad I(X;Y)=\sum_{x,y}p(x,y)\log\frac{p(x,y)}{p(x)p(y)} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-IT-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | IT（信息论与编码） |
| **录入** | 2026-10-11 |

## 一、要点

容量是对**输入分布**取的上确界，不是信道的固定属性表上的一个数——这一点是 Shannon 第一定理的核心：可传输的极限由「最好的输入分布」给出。互信息写成 KL 散度的形式更见其意义：它是联合分布与乘积分布的距离，所以它度量的是「知道 Y 减少了多少关于 X 的不确定」。边界：本卡按有限字母表、无记忆的口径定义；连续信道（AWGN）需要功率约束下的微分熵版本，不在本条范围内。

## 二、前提

- 信道无记忆：p(y^n|x^n)=prod_i p(y_i|x_i)
- 输入输出字母表有限
- 默认约定：log 取 2 的底，故单位为 bit；对任何 0 的概率约定 0 log 0 = 0

## 三、关系

- 用到：OM-D-PR-0001
- 相关：OM-T-IT-0001, OM-D-PR-0001

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 本条同时为 OM-T-IT-0001 的 C、I、R、X、Y 与 p(x) 六个记号补定义条目；n（码长）沿用 NT 各卡已有的同名记号，故不另立拼写。

## 五、来源

- Shannon, C. E., A Mathematical Theory of Communication (1948), §4-10
- Cover and Thomas, Elements of Information Theory, 2nd ed. (2006), ch.8

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

