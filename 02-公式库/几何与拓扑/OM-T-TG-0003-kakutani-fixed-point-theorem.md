---
id: OM-T-TG-0003
title_zh: 角谷不动点定理
status: PROPOSED
---

# OM-T-TG-0003 · 角谷不动点定理

\[ \Phi:K\multimap K,\ \text{上半连续、值非空凸闭}\ \Longrightarrow\ \exists x\in K:\ x\in\Phi(x) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-T-TG-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | TG（几何与拓扑） |
| **录入** | 2026-10-11 |

## 一、要点

Brouwer 是这条定理在「值为单点」时的特例，所以图上记的是 generalizes 边：单值连续映射自动满足上半连续与凸值（点是凸的）。它之所以是博弈论的引擎，是因为「最佳应对」一般是**一组**策略而不是一个：纳什均衡正好是最佳应对集值映射的不动点。边界：上半连续性不可弱化，且结论只给存在性；本卡不登记任何计算均衡的算法正确性（那需要额外的结构假设）。

## 二、前提

- K 为 R^n 中的非空紧凸集
- 集值映射上半连续
- 每个值都是非空凸闭集
- 默认约定：「不动点」在这里指 x 属于像集 \Phi(x)，而不是 \Phi(x) 是单点

## 三、关系

- 推广（本条把下列各条推广开）：OM-T-TG-0001
- 用到：OM-T-TG-0001
- 相关：OM-T-GO-0002

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- generalizes 是本库第一条用到该边型的记录间关系；yaml 里的键名是 generalizations，边型才叫 generalizes——发射器原先只认 related／uses／implications／contradicts 四个键，所以这条边在键名写错时是被静默丢掉的（图上少一条边不会报错，是本轮自己踩的坑）。箭头由 flowdocs.ARROW 渲染，若某型箭头在 ARROW 里缺失，不变量 TYPE-UNRENDERED 会当场点名（第 2 轮的教训）。

## 五、来源

- Kakutani, S., A generalization of the Brouwer fixed point theorem (1941)
- Border, K. C., Competitive Economics (2023), ch.5

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

