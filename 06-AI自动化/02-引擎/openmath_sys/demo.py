"""OpenMath 综合处理系统 —— 可运行演示。

运行：python demo.py
演示覆盖四大模块：论文获取 / 方程解析 / 四维逻辑推理 / 最高权限算法调度。
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "src"))

from openmath_sys import (  # noqa: E402
    OpenMathProcessor, Authority, Algorithm,
)

# 演示用的数学方程（覆盖线性/二次/超越/含函数等形态）
DEMO_EXPRESSIONS = [
    "2*x + 3 = 7",
    "x^2 - 5*x + 6 = 0",
    "a*x^2 + b*x + c = 0",
    "power(2, 3) + sqrt(16)",
    "gcd(12, 18)",
    "sin(x) + cos(x)",
]


def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main() -> int:
    banner("OpenMath 综合处理系统 · 演示运行")
    proc = OpenMathProcessor(cds=["arith1", "relation1", "transc1"])
    print(f"[知识库] 已加载 OpenMath 符号 {len(proc.kb.symbols)} 个："
          f"{', '.join(sorted(proc.kb.symbols)) or '(网络不可用，已回退样例)'}")

    # 1) 论文获取
    banner("模块一 · 论文获取（arXiv 检索 + 启发式排序）")
    papers = proc.acquire_papers("OpenMath symbolic computation", max_results=8)
    if not papers:
        print("未获取到论文。")
    for i, p in enumerate(papers[:5], 1):
        print(f"  {i}. [{p.score:.2f}] {p.title}")
        print(f"     作者: {', '.join(p.authors)} | 分类: {','.join(p.categories)}")

    # 2)+3) 方程解析 + 四维推理
    banner("模块二/三 · 方程解析 + 四维逻辑处理框架")
    records = proc.reason_over(DEMO_EXPRESSIONS)
    for rec in records:
        print(f"\n  > 表达式: {rec.raw}")
        for f in rec.facets:
            print(f"      [{f.dimension}] {f.title}: {f.summary}")
            if f.dimension == "D4" and f.details.get("solve"):
                print(f"           求解 => {f.details['solve']}")
        print("      结论: " + " ".join(rec.conclusions))

    # 4) 最高权限算法调度
    banner("模块四 · 算法联盟最高权限处理模式 (Authority.SUPREME)")
    print("  调度器登记算法：")
    for a in proc.alliance.list_algorithms():
        print(f"    - {a['name']:18s} 需{a['level']:8s} safe={a['safe']}")
    reports = proc.run_alliance(records, mode=Authority.SUPREME)
    ok = sum(1 for r in reports for x in r if x.status == "ok")
    print(f"\n  对 {len(records)} 条记录执行 SUPREME 调度，成功算法调用 {ok} 次。")

    # 安全验证：演示一个被拒绝的不安全算法
    banner("安全验证 · 破坏性算法在任意模式下均被拒绝")
    # 假设会删除文件系统的算法 —— 仅示意，绝不真正执行
    def evil(rec):
        return "would delete files"
    proc.alliance.register(Algorithm("destructive_wipe", evil,
                                     Authority.SUPREME, "破坏性示例", safe=False))
    test = proc.alliance.dispatch(records[0], mode=Authority.SUPREME)
    refused = [r for r in test if r.algorithm == "destructive_wipe"]
    print(f"    destructive_wipe 状态: {refused[0].status} ({refused[0].note})")

    # 导出
    banner("产物导出")
    paths = proc.export(os.path.join(_HERE, "output"))
    print("  " + json.dumps(paths, ensure_ascii=False, indent=2).replace("\n", "\n  "))

    banner("完成")
    print("  说明：'最高权限'为算法联盟内部逻辑授权上限，不映射 OS 提权；")
    print("  '最优质论文'为关键词相关度+时效的启发式近似，非权威影响因子。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
