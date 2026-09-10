# -*- coding: utf-8 -*-
"""
对 critique 提出的关键点做可计算验证：
  A. 「0-1-∞ 运算表」是否 associative？若不结合，则标准分析/数论基础不适用。
  B. x/ln x 的「密度极值点 e^2」到底算得对不对？它描述的是真实素数还是近似函数？
"""
import math

# ---------- A. 0-1-∞ 乘法表（取自文档原文）----------
mult = {('0','0'):'0', ('0','1'):'0', ('0','8'):'1',
        ('1','1'):'1', ('1','8'):'8', ('8','8'):'8'}   # '8' 代表 ∞
def m(a, b):
    k = (a, b) if (a, b) in mult else (b, a)
    return mult[k]

print("=== A. 结合律检查（用文档自己的乘法表）===")
print("0 * 8 =", m('0', '8'), "   (文档声称 =1)")
print("8 * 8 =", m('8', '8'), "   (文档声称 =8)")
left  = m(m('0', '8'), '8')     # (0*8)*8
right = m('0', m('8', '8'))     # 0*(8*8)
print("(0*8)*8 =", left)
print("0*(8*8) =", right)
print("=> 结合律成立? ", left == right,
      "  （不等 => 该乘法【不结合】，标准代数推论全部失效）")

# ---------- B. x/ln x 密度极值点 ----------
def rho(x):  # rho(x) = d/dx (x/ln x) = (ln x - 1)/(ln x)^2
    return (math.log(x) - 1) / (math.log(x) ** 2)

xs = [i * 0.005 for i in range(400, 10001)]   # 2.0 .. 50.0
best = max(xs, key=rho)
print("\n=== B. 密度函数 rho(x)=d/dx(x/ln x) 的极值 ===")
print("扫描 argmax(x) =", round(best, 4), "  理论 e^2 =", round(math.e ** 2, 4))
print("=> 框架说'极值在 e^2'：作为【对函数 x/ln x 的微积分】是【算对的】。")

# 真实素数密度 1/ln x 是单调递减的，根本没有峰
print("\n真实素数密度近似 1/ln x（应单调下降）:")
for x in [3, math.e ** 2, 10, 100, 1000]:
    print(f"  1/ln({x:7.3f}) = {1/math.log(x):.4f}")

# 真实素数在滑动窗口里的密度（离散、无 e^2 峰值）
def primes_upto(n):
    s = [True] * (n + 1); s[0] = s[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            for j in range(i * i, n + 1, i):
                s[j] = False
    return [i for i, v in enumerate(s) if v]

P = primes_upto(3000)
print("\n实际素数密度（窗口 [x, x+20] 内素数数 /20）:")
for x in [3, 7, math.e ** 2, 15, 50, 100, 500]:
    cnt = sum(1 for p in P if x <= p < x + 20)
    print(f"  x={x:7.2f}: {cnt/20:.3f}")
print("=> 真实素数密度在 e^2≈7.39 附近【无特殊峰值】，峰值论是对近似函数的误读。")
