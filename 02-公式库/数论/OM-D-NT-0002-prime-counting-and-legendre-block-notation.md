---
id: OM-D-NT-0002
title_zh: 素数计数与 Legendre 分块的记号
status: PROPOSED
---

# OM-D-NT-0002 · 素数计数与 Legendre 分块的记号

\[ \pi(x)=\#\{p\le x:\ p\ \text{是素数}\},\qquad \phi(x,a)=\#\{1\le m\le x:\ \text{没有素因子}\le p_a\},\qquad \Delta\pi(N)=\pi(N)-\pi(N-1),\qquad g_n=p_{n+1}-p_n \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-NT-0002 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | NT（数论） |
| **录入** | 2026-10-11 |

## 一、要点

数论族里 17 张记录共用这一套记账语言：`pi` 数素数、`phi` 数筛剩的整数、`Delta pi` 把两者接成离散微积分。此前这三枚只活在宿主记录的 symbols 表里，本库的台账判据（记号没进任何 kind=definition 记录）因此一直为红。

要留的精度有三处。一，`phi(x,a)` 的 a 是**已筛素数的个数**而不是数值参数，递归式 phi(x,a)=phi(x,a-1)-phi(floor(x/p_a),a-1) 只在 a 走名单时成立；取 a=pi(floor(sqrt(x))) 才把 phi 变成 pi（见 OM-T-NT-0002）。二，`pi(x)` 与 `pi`（圆周率）是**两个不同的记号串**，本库按整串聚合，所以两条卡不会互相假绿——但这也意味着裸 `pi` 若在某处被读成计数函数就会串位。三，`phi(x, a)`（逗号后多一个空格）在本批之前确实存在于 OM-F-NT-0001 的表里：判据按字符串建，它就是一枚**独立**的未定义记号。本卡固定无空格写法，老记录那一处拼写随后单独整改并复扫（不静悄悄改，见 CHANGELOG）。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：x 为实数，N 为正整数；计数取左闭右开或按各卡正文注明的空隙约定
- 默认约定：a 为非负整数，a=0 时 phi(x,0)=floor(x)（不做任何筛除）
- 默认约定：p_1=2，素数按升序编号；本卡只固定编号，不引入任何第 n 素数的界

## 三、关系

- 用到：OM-D-NT-0001
- 相关：OM-F-NT-0001, OM-F-NT-0002, OM-F-NT-0003, OM-T-NT-0001, OM-T-NT-0002, OM-T-NT-0008

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡：把 OM-F-NT-0001/0002/0003、OM-T-NT-0001/0002/0008 与 OM-A-NT-0001 共用的 9 枚记号升成定义条目。本卡不新增任何数学主张，只固定记号与口径。

## 五、来源

- Hardy, G. H. and Wright, E. M., An Introduction to the Theory of Numbers, 5th ed., Oxford (1979), ch.XXII（Legendre 的 phi 与 pi(x) 的公式）
- Apostol, T. M., Introduction to Analytic Number Theory, Springer (1976), ch.3（素数分布一章里的 pi(x)、p_n 与间隙）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

