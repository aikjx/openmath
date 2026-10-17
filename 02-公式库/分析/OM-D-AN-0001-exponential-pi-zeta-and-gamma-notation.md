---
id: OM-D-AN-0001
title_zh: 指数、圆周率与 zeta/Gamma 的记号
status: PROPOSED
---

# OM-D-AN-0001 · 指数、圆周率与 zeta/Gamma 的记号

\[ \exp(z)=\sum_{n=0}^{\infty}z^{n}/n!\ (z\in\mathbb{C}),\qquad \zeta(s)=\sum_{n\ge 1}n^{-s}\ (\operatorname{Re}s>1),\qquad \Gamma(s)=\int_{0}^{\infty}t^{s-1}e^{-t}\,dt\ (\operatorname{Re}s>0) \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-AN-0001 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | AN（分析） |
| **录入** | 2026-10-11 |

## 一、要点

分析域此前有 3 张记录（欧拉恒等式、函数方程、欧拉公式一般形式）却**一张定义卡也没有**，而这三张记录的记号台账里有 4 枚红的：exp、pi、zeta、Gamma。

两处口径要钉住。一，`pi` 与数论的 `pi(x)` 是两个串（见 OM-D-NT-0002），本卡只定裸 `pi`；反过来，如果哪天有人把素数计数写成不带参数的 `pi`，按名聚合的判据会把它当成圆周率放过——这条风险写在 §八 的债里，不由本卡解决。二，zeta 与 Gamma 都按**延拓后的亚纯函数**登记，因为函数方程（OM-F-AN-0002）谈的是整个复平面上的对象；但收敛半平面的生长式也一并写进定义，免得读者以为本库跳过了延拓的构造步骤。

e、i、z、s、theta 五枚裸字母**没有**收进来：它们是 OM-F-AN-0001/0003 陈述里被量词或上下文绑定的变量，且 `i` 与 `e` 在本库他处另有同名用法（`e` 在 OM-T-TC-0001 指停机判定器索引）。全域定义它们＝制造假绿。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：exp 由级数定义，故它是整函数；对数式的多值性不在本卡口径内（OM-F-AN-0003 的一般形式讨论的正是这一层的商结构）
- 默认约定：zeta 与 Gamma 都取其**亚纯延拓**为默认对象，级数与积分只在各半平面给出生长式
- 默认约定：pi 取圆周长与直径之比，等价地取 2 倍 sin 的最小正零点；本卡不引入弧度制的额外约定

## 三、关系

- 相关：OM-F-AN-0001, OM-F-AN-0002, OM-F-AN-0003

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡：补 exp、pi、zeta、Gamma 四枚定义条目，并写明 zeta/Gamma 取延拓口径。本卡不含任何收敛性或有界性的新主张。

## 五、来源

- Euler, L., Introductio in analysin infinitorum (1748), pt.I（exp 的级数、pi 与 Gamma 的早期形态）
- Ahlfors, L. V., Complex Analysis, 3rd ed., McGraw-Hill (1966), ch.2（指数函数作为整函数的定义）
- Titchmarsh, E. C., The Theory of the Riemann Zeta-function, 2nd ed. revised by D. R. Heath-Brown, Oxford (1986), ch.I（zeta 的级式与延拓）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

