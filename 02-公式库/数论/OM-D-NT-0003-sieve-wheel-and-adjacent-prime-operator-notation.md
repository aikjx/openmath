---
id: OM-D-NT-0003
title_zh: 筛、轮与相邻素数算子的记号
status: PROPOSED
---

# OM-D-NT-0003 · 筛、轮与相邻素数算子的记号

\[ P(Y)=\prod_{p\le Y}p,\qquad A_Y(N)=\#\{1\le n\le N:\ n^2+1\ \text{的素因子}>Y\},\qquad C_d(N)=\#\{1\le n\le N:\ d\mid n^2+1\},\qquad \omega(p)=\#\{r\bmod p:\ p\mid r^2+1\},\qquad \mathrm{NextPrime}(m)=\min\{q>m:\ q\ \text{是素数}\} \]

| 字段 | 值 |
| --- | --- |
| **ID** | OM-D-NT-0003 |
| **状态** | `PROPOSED`（记录级：本库结构良构，无本地复算） |
| **域** | NT（数论） |
| **录入** | 2026-10-11 |

## 一、要点

这一张卡把数论族里最容易互相污染的一组记号固定下来。三处必须写清：

一，`A(N)` 与 `A_Y(N)` 的差是被筛余项，而 `E(N,Y)` 是**补正项**而不是余项的界——OM-F-NT-0004 之所以把筛写成恒等式加爆炸余项，正是为了让读者看得见这一分工。二，`omega(p)` 只数同余类的个数，不数带权重的类，因此它在 p=2 处取 1，与 Legendre 符号口径差一枚；写成 1+legendre(-1/p) 才对奇素数成立。三，`j(M)` 与 `g_n <= j(p_n#)` 这条上界（OM-T-NT-0008）里，Jacobsthal 函数的定义必须取「任意连续 j(M) 个整数里至少有一个与 M 互素」的最小值；把窗口开闭写反会让界差 1，这也是本卡把定义钉在记号条目里的原因。

本卡把裸 `M` 也收了：它在 OM-T-NT-0006 里是轮模（一个具体的正整数参数），在本库其它处 `M` 另有他用（OM-D-GO-0001 的花体 M 是另一个串，不冲突）。这是本批唯一一次给单字母建条目，理由是它是**带口径的参数名**而非量词变量：该卡的陈述里 M 出现在 R_M 与 gcd(N,M)=1 两处并需要同一含义。e、i、n、k、r、s、d、b、c、g、z、theta、epsilon、sigma 等仍留在台账里不铸——它们是宿主的量词变量，全域定义会假绿别处的同名用法。

## 二、前提

- （无额外前提；见 `assumptions`）
- 默认约定：Y、N、m 为正整数，d 为正整数，M 为正方整数（轮模，常取 primorial M=p_r#）
- 默认约定：omega(p) 对 p=2 取 1、p 为奇素数时按 -1 是否为模 p 平方剩余取 2 或 0
- 默认约定：A(N) 与 E(N,Y) 的口径见 OM-F-NT-0004：后者是被筛误杀的补正项，不是余项的界

## 三、关系

- 用到：OM-D-NT-0002
- 相关：OM-F-NT-0004, OM-P-NT-0004, OM-T-NT-0003, OM-T-NT-0004, OM-T-NT-0005, OM-T-NT-0006, OM-T-NT-0007, OM-T-NT-0008

## 四、诚实边界

- 本条登记的是**文献中的结果**。本库既没有重做证明，也没有形式化绑定，所以 `evidence_level` 停在 L1；把它读成「本库证明了它」是错的，读成「它未被证明」同样是错的。
- 下条来源本轮**未经目录/DOI 逐条核对**，故 `fact_check.status: UNVERIFIED`；引用这些出处的人需要自行复核版本信息。
- 第 4 批记号卡：收 OM-F-NT-0004、OM-T-NT-0003..0008、OM-P-NT-0004 共用的 14 枚记号。只固定记号与口径，不新增数学主张；余项与补正的分工细节以宿主记录为准。

## 五、来源

- Halberstam, H. and Richert, H.-E., Sieve Methods, Academic Press (1974), ch.1（筛的记号、余项与补正的分工）
- Jacobsthal, E., Über eine Klasse von Funktionen, die bei manchen Problemen der Zahlentheorie auftreten, Symbolae Osloenses 13 (1934)（j(M) 的原始出处）
- Nagura, J., On the interval containing at least one prime number, Proceedings of the Imperial Academy of Japan 18 (1942)（相邻素数与窗口型结果）

## 六、复现

```bash
python -m openmath lint          # L0 结构
python -m openmath graph --check # 关系图与缺口判据（不写盘）
```

