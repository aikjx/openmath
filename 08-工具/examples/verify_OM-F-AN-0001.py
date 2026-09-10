# -*- coding: utf-8 -*-
"""OM-F-AN-0001 欧拉恒等式 e^{i*pi} + 1 = 0 的独立验证脚本。

用法：
    python 08-工具/examples/verify_OM-F-AN-0001.py

说明：
    本脚本输出**残差**，而不是简单的"通过"。
    残差的数量级必须与所设精度匹配（50 位精度 → 残差应在 1e-45 量级以下）。
    若你看到 1e-16 量级的"残差"，说明用的是双精度而非高精度，属于精度不足。
"""

import sys

try:
    import mpmath as mp
except ImportError:
    print("SKIP: 未安装 mpmath，无法执行 L2 验证。安装: pip install mpmath")
    sys.exit(0)


def main():
    mp.mp.dps = 50
    residual = mp.e ** (mp.mpc(0, 1) * mp.pi) + 1
    magnitude = abs(residual)

    print("OM-F-AN-0001 欧拉恒等式 e^{i*pi} + 1 = 0")
    print("-" * 60)
    print("精度         : %d 位有效数字" % mp.mp.dps)
    print("残差（复）   : %s" % mp.nstr(residual, 20))
    print("残差（模）   : %s" % mp.nstr(magnitude, 10))
    print("-" * 60)

    if magnitude < mp.mpf("1e-40"):
        print("L2 PASS: 残差在容差内。")
        print("诚实提醒: 这只是一个采样点的数值结果，且本恒等式是指数函数定义的")
        print("          直接推论——L2 通过几乎不提供信息量，不构成证明。")
        return 0
    print("L2 FAIL: 残差超出容差 %s" % mp.nstr(mp.mpf("1e-40"), 5))
    return 1


if __name__ == "__main__":
    sys.exit(main())
