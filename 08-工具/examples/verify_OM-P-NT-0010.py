# -*- coding: utf-8 -*-
"""OM-P-NT-0010 Andrica 猜想的独立验证脚本（第 11 批）。

    猜想：A_k := sqrt(p_{k+1}) - sqrt(p_k) < 1   对一切 k >= 1
    整数判据（本脚本的主判决，全程不用浮点）：(g_k - 1)^2 < 4 p_k,  g_k := p_{k+1} - p_k

这台仪器要办四件事，每件都配一把独立的尺：

1) **把「实数形式」与「整数形式」的等价性自己证一遍**，不靠注释里那句推导。
   两条独立通道同时判每个间隙：
   (a) 平方路线 (g-1)^2 < 4p；
   (b) 定点平方根路线：s = isqrt(p << 2t)（t=60）给 sqrt(p) 的严格下界 s/2^t，
       且 sqrt(p) < (s+1)/2^t。于是 (g-1)*2^t < 2s 是可判的严格通过条件、
       (g-1)*2^t >= (2s+2) 是严格否决条件，中间宽度 2/2^t 的缝记「未决」并枚出来
       ——未决数若非零，本脚本不判 PASS（宁可红，不假装绿）。
   两通道逐格同判才算「等价式没写反」。

2) **上确界在哪一格**：浮点只用来筛候选（名次可能因 1e-16 而错），前 20 名候选
   再由 mpmath 50 dps 复核，印冠亚军与它们的差；分段极大值一并印出看衰减。

3) **第二口径复核**：随机样本上 50 dps 与 double 的同判性，并印两套读数的最大差。

4) **为什么「间隙形式」不是 Legendre 猜想的等价形式**（本批要修的错标）：
   Legendre 每个窗口 (n^2,(n+1)^2] 只用到 k = pi(n^2) 那一枚间隙，
   于是扫描范围内**绝大多数间隙压根不在 Legendre 的管辖里**——
   本脚本现数这个覆盖率（枚数与百分比），并把「Andrica => Legendre」那一步
   逐窗口机械执行：先核整数化的界步 4 p_k <= (n^2 - p_k + 2n)^2（即 (sqrt(p_k)+1)^2 <= (n+1)^2），
   再核对窗口非空。

诚实红线（红线一）：PASS 只表示**扫描范围内未发现反例**，不表示猜想成立，
也不构成任何进展。有限扫描对全称命题的证明价值为零。

用法：cd openmath && PYTHONIOENCODING=utf-8 python 08-工具/examples/verify_OM-P-NT-0010.py [上界]
退出码：0＝全部判定通过；1＝有判定不过；2＝前置条件缺失（未装 mpmath）。
"""
import bisect
import math
import random
import sys
import time

try:
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 mpmath，无法执行 50 dps 通道。安装: pip install mpmath")
    sys.exit(2)

DPS = 50
FP_BITS = 60          # 定点平方根的标度位数 2^60
TOP_CAND = 20         # 浮点筛出的候选名次
RANDOM_SAMPLE = 2000  # 50 dps 与 double 交叉的随机样本枚数
mp.mp.dps = DPS

BOUND = 10 ** 7
for _arg in sys.argv[1:]:
    if _arg.isdigit():
        BOUND = int(_arg)
assert BOUND >= 10 ** 5, "上界太小，分段读数与覆盖率没有意义"


def sieve(limit):
    """埃氏筛（切片版）。返回 [0,limit) 内的素数表。"""
    flags = bytearray(b"\x01") * limit
    flags[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if flags[i]:
            start = i * i
            flags[start:limit:i] = bytearray(len(range(start, limit, i)))
    return [i for i in range(limit) if flags[i]]


def fixed_point_channel(p, g):
    """独立于平方路线的严格判定：True=满足 A<1，False=违反，None=定点缝内未决。"""
    scale = 1 << FP_BITS
    s = math.isqrt(p << (2 * FP_BITS))       # floor(sqrt(p) * 2^FP_BITS)
    lhs = (g - 1) * scale
    if lhs < 2 * s:
        return True
    if lhs >= 2 * s + 2:
        return False
    return None


def selftest():
    """变异体：这台尺必须能被一个人为造出的反例打断，否则全绿不算证据。

    夹具是纯算术的 (p, g) 对（两把尺只吃这两个整数，不必要求 p+g 真是素数）：
      M1 (7, 7)：A = sqrt(14)-sqrt(7) = 1.309... > 1 ⇒ 两通道都必须判违反；
      M2 (7, 4)：真实间隙 7→11，A = 0.6708 < 1 ⇒ 两通道都必须判通过；
      M3 (3, 2) ：真实间隙 3→5，A = 0.5040 < 1 ⇒ 同上。
    若 M1 不被抓住⇒尺坏了；若 M2/M3 被抓⇒尺过紧（会把真数据判红）。
    """
    print("=== 变异体自检（--selftest）===")
    ok = True
    for (p, g, want, name) in [(7, 7, False, "M1 造出的反例"),
                               (7, 4, True, "M2 真间隙 7->11"),
                               (3, 2, True, "M3 真间隙 3->5")]:
        sq = (g - 1) ** 2 < 4 * p
        fp = fixed_point_channel(p, g)
        hit = (sq == want) and (fp is not None and fp == want)
        print("%s (p=%d,g=%d)：平方通道=%s 定点通道=%s 期望=%s ⇒ %s"
              % (name, p, g, sq, fp, want, "被抓住/判对" if hit else "判错（尺坏）"))
        ok = ok and hit
    print("=== 自检汇总：%s ===" % ("PASS（正例不误伤、反例必响）" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    t0 = time.time()
    print("=== OM-P-NT-0010 Andrica 猜想 L2 检验（第 11 批）===")
    print("扫描上界 p_k < %d（命令行第 1 参数可改），dps=%d，定点标度 2^%d"
          % (BOUND, DPS, FP_BITS))
    primes = sieve(BOUND)
    n = len(primes)
    print("素数枚数 pi(%d) = %d（内置筛现算）" % (BOUND, n))
    gaps = [primes[i + 1] - primes[i] for i in range(n - 1)]
    total_pairs = len(gaps)
    print("相邻对（间隙）数 = %d" % total_pairs)

    # ---- 判定 1：两通道逐格同判 --------------------------------------------
    viol_sq, viol_fp, undecided, disagree = [], [], [], []
    slack_min, slack_min_k = None, None
    for k in range(total_pairs):
        p = primes[k]
        g = gaps[k]
        a = (g - 1) ** 2 < 4 * p
        if not a:
            viol_sq.append((k + 1, p, g))
        b = fixed_point_channel(p, g)
        if b is None:
            undecided.append((k + 1, p, g))
        elif b is False:
            viol_fp.append((k + 1, p, g))
        if b is not None and a != b:
            disagree.append((k + 1, p, g, a, b))
        sl = 4 * p - (g - 1) ** 2            # 到反证线的整数余量（>0 即满足）
        if slack_min is None or sl < slack_min:
            slack_min, slack_min_k = sl, (k + 1, p, g)
    print("[判定1a] 平方通道 (g-1)^2 < 4p：违反 %d 枚%s"
          % (len(viol_sq), "" if not viol_sq else " 例：%r" % (viol_sq[:3],)))
    print("[判定1b] 定点通道：违反 %d 枚／未决 %d 枚（未决带宽 2/2^%d）"
          % (len(viol_fp), len(undecided), FP_BITS))
    print("[判定1c] 两通道不同判 %d 枚%s" % (len(disagree), "" if not disagree else " %r" % (disagree[:3],)))
    print("[判定1d] 最小整数余量 4p_k-(g_k-1)^2 = %d @ k=%d（p=%d, g=%d）"
          % (slack_min, slack_min_k[0], slack_min_k[1], slack_min_k[2]))
    j1 = (not viol_sq) and (not viol_fp) and (not undecided) and (not disagree) and slack_min > 0
    print("[判定1] %s" % ("PASS（两把独立的尺在全部 %d 枚间隙上逐格同意）" % total_pairs if j1 else "FAIL"))

    # ---- 判定 2：上确界与分段趋势 ------------------------------------------
    fl = [math.sqrt(primes[i + 1]) - math.sqrt(primes[i]) for i in range(total_pairs)]
    order = sorted(range(total_pairs), key=lambda i: -fl[i])[:TOP_CAND]
    hi = []
    for i in order:
        a = mp.sqrt(mp.mpf(primes[i + 1])) - mp.sqrt(mp.mpf(primes[i]))
        hi.append((a, i + 1, primes[i], primes[i + 1], gaps[i]))
    hi.sort(key=lambda r: -r[0])
    best = hi[0]
    print("[判定2a] 50 dps 复核后的最大 A_k（浮点只用于筛 %d 名候选）：" % TOP_CAND)
    print("   A_%d = %s   （p_%d=%d, p_%d=%d, g=%d）"
          % (best[1], mp.nstr(best[0], 30), best[1], best[2], best[1] + 1, best[3], best[4]))
    print("   亚军 A_%d = %s（冠亚军差 %s）"
          % (hi[1][1], mp.nstr(hi[1][0], 30), mp.nstr(hi[0][0] - hi[1][0], 10)))
    print("   候选里 A_k > 0.6 的枚数 = %d／%d" % (sum(1 for r in hi if r[0] > mp.mpf("0.6")), len(hi)))
    segs = []
    for lo, upto in [(0, 10 ** 2), (10 ** 2, 10 ** 3), (10 ** 3, 10 ** 4),
                     (10 ** 4, 10 ** 5), (10 ** 5, 10 ** 6), (10 ** 6, total_pairs)]:
        upto = min(upto, total_pairs)
        if upto <= lo:
            continue
        m = max(fl[lo:upto])
        segs.append((lo, upto, m))
        print("   分段 k∈[%d,%d)：max A_k = %.6f" % (lo, upto, m))
    tail = max(fl[10 ** 6:]) if total_pairs > 10 ** 6 else None
    j2 = (best[0] < 1) and all(m < 1 for _, _, m in segs)
    print("[判定2] %s（尾段 k>1e6 的极大值 %s；衰减趋势见上）"
          % ("PASS" if j2 else "FAIL",
             ("%.6f" % tail) if tail is not None else "不适用"))

    # ---- 判定 3：50 dps 与 double 的第二口径 -------------------------------
    rand = random.Random(0)
    picks = rand.sample(range(total_pairs), min(RANDOM_SAMPLE, total_pairs))
    bad = 0
    worst = mp.mpf(0)
    for i in picks:
        a50 = mp.sqrt(mp.mpf(primes[i + 1])) - mp.sqrt(mp.mpf(primes[i]))
        if (a50 < 1) != (fl[i] < 1):
            bad += 1
        d = abs(a50 - mp.mpf(repr(fl[i])))
        if d > worst:
            worst = d
    print("[判定3] 随机 %d 枚（seed=0）50 dps 与 double 同判：不同判 %d 枚，两套读数最大差 %.3e"
          % (len(picks), bad, float(worst)))
    j3 = (bad == 0)

    # ---- 判定 4：Andrica => Legendre 机械执行 + 覆盖率 ----------------------
    nmax = int(math.isqrt(BOUND - 1)) - 1        # 需 (n+1)^2 <= BOUND-1
    empty = 0
    cmin, cmin_n = None, None
    used_k = set()
    bind_min, bind_arg = None, None
    ceil_min, ceil_arg = None, None
    for nn in range(1, nmax + 1):
        a2, b2 = nn * nn, (nn + 1) * (nn + 1)
        idx = bisect.bisect_right(primes, a2)    # pi(n^2)：<= n^2 的素数枚数
        c = bisect.bisect_left(primes, b2) - idx  # 窗口 (n^2,(n+1)^2) 内的素数枚数
        used_k.add(idx)
        if c == 0:
            empty += 1
        if cmin is None or c < cmin:
            cmin, cmin_n = c, nn
        if 1 <= idx < len(primes):
            pk = primes[idx - 1]
            gk = primes[idx] - pk
            sl_a = 4 * pk - (gk - 1) ** 2
            if sl_a > 0 and (bind_min is None or sl_a < bind_min):
                bind_min, bind_arg = sl_a, (nn, pk, gk, c)
            # 界步：4 p_k <= (n^2 - p_k + 2n)^2  <=>  (sqrt(p_k)+1)^2 <= (n+1)^2
            cl = (a2 - pk + 2 * nn) ** 2 - 4 * pk
            if cl >= 0 and (ceil_min is None or cl < ceil_min):
                ceil_min, ceil_arg = cl, (nn, pk)
            if cl < 0:
                print("   [界步负值] n=%d p_k=%d 推导不闭合——不该发生" % (nn, pk))
    cover = 100.0 * len(used_k) / total_pairs
    print("[判定4a] 窗口 n=1..%d：空窗 %d 个，min c(n) = %s @ n=%s" % (nmax, empty, cmin, cmin_n))
    print("[判定4b] Andrica 那一步在被触及间隙上的最小整数余量 4p_k-(g-1)^2 = %s @ n=%s p_k=%s g=%s c(n)=%s"
          % (bind_min, bind_arg[0] if bind_arg else None, bind_arg[1] if bind_arg else None,
             bind_arg[2] if bind_arg else None, bind_arg[3] if bind_arg else None))
    print("[判定4c] 界步最小余量 (n^2-p_k+2n)^2-4p_k = %s @ n=%s p_k=%s（非负⇒推导闭合）"
          % (ceil_min, ceil_arg[0] if ceil_arg else None, ceil_arg[1] if ceil_arg else None))
    print("[判定4d] 覆盖率：%d 个窗口只触及 %d 枚不同间隙＝全库 %d 枚的 %.4f%%；"
          "其余 %.4f%% 的间隙即便违反 Andrica 也不在任何 Legendre 窗口的管辖内 ⇒ 两命题不等价（本库未在反方向证过）"
          % (nmax, len(used_k), total_pairs, cover, 100.0 - cover))
    j4 = (empty == 0) and (cmin is not None and cmin >= 1) and (ceil_min is not None and ceil_min >= 0)
    print("[判定4] %s" % ("PASS（机械推导在每个窗口上闭合）" if j4 else "FAIL"))

    # ---- 与第二台仪器交叉：OM-P-NT-0009 的 landau_scan 读数 ----------------
    sub = []
    for nn in range(1, min(2000, nmax) + 1):
        a2, b2 = nn * nn, (nn + 1) * (nn + 1)
        c = bisect.bisect_left(primes, b2) - bisect.bisect_right(primes, a2)
        sub.append((c, nn))
    m2 = min(sub)
    print("[交叉] 只算 n=1..%d：min c(n) = %d @ n=%d（OM-P-NT-0009 的 landau_scan 旧面在 n=1..2000 上印 2 @ n=1）"
          % (len(sub), m2[0], m2[1]))

    ok = j1 and j2 and j3 and j4
    print("=== 判定汇总：%s ｜ 判定1=%s 判定2=%s 判定3=%s 判定4=%s ｜ 耗时 %.1fs ==="
          % ("ALL PASS" if ok else "NOT PASS", j1, j2, j3, j4, time.time() - t0))
    print("注（红线一）：以上全部 PASS 只说明上界以内没有反例；Andrica 猜想仍是 OPEN，"
          "本面不构成任何进展，也不得被引作「已证明」。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
