# -*- coding: utf-8 -*-
"""
数论计算实验（把突破路线图 Top 方法从"未实现"变成"可运行"）
==============================================================

上一轮 `openmath_coalition.py` 给出的突破路线图 Top4 为：
    asymptotic_estimation / sieve_theory / modular_analysis / rad_computation
本脚本把它们在 `openmath_sys/numbertheory.py` 中实现后**实际运行**，产出 L2 计算证据。

五个实验：
  E1  rad 计算与 ABC 三元组质量搜索        -> rad_computation
  E2  哥德巴赫分拆穷举验证                 -> sieve_theory（具体筛法应用）
  E3  孪生素数筛                           -> sieve_theory（具体筛法应用）
  E4  π(x) 与 x/ln x、li(x) 的渐近对照     -> asymptotic_estimation
  E5  Collatz 停止时间的模类统计           -> modular_analysis

诚实红线：
  - 所有结果为 **L2 计算证据**，**不构成任何证明**。
  - 穷举验证只在给定上限内成立；上限之外无任何断言。
  - "实现 method X" 指实现了该方法的**一个具体可用版本**，
    不等于掌握了对应的完整数学理论（见各实验的 scope 字段）。
"""
from __future__ import annotations

import json
import os
import sys
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE
for _ in range(2):
    REPO = os.path.dirname(REPO)
# 引擎已收纳进本仓库：06-AI自动化/02-引擎/openmath_sys/
sys.path.insert(0, os.path.join(REPO, "06-AI自动化", "02-引擎", "openmath_sys", "src"))

from openmath_sys.numbertheory import (  # noqa: E402
    search_abc_triples, goldbach_profile, twin_prime_profile,
    prime_count_asymptotics, collatz_modular_profile,
)

DATA_DIR = os.path.join(REPO, "09-数据")
GEN_AT = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
PROVENANCE = {
    "ai_assisted": True,
    "note": "由 AI 代理基于 openmath_sys 引擎自动生成，未经人类复核，不得作为 L3+ 证据。",
}
HONESTY = ("全部结果为 L2 计算证据：**不构成任何数学证明**。"
           "穷举/数值验证仅在给定搜索上限内有效，上限之外不作任何断言。")

# ---- 实验规模（可在性能与覆盖间调整） --------------------------------------
ABC_C_MAX = 3000
GOLDBACH_LIMIT = 10000
TWIN_LIMIT = 200000
PI_LIMIT = 100000
COLLATZ_N_MAX = 20000
COLLATZ_MODULUS = 6


def main():
    exp = {}

    print(f"[E1] rad 计算 / ABC 三元组质量搜索（c <= {ABC_C_MAX}）...")
    exp["E1_abc_quality"] = {
        "method_id": "rad_computation",
        "scope": "精确实现 rad(n)（定义本身，无简化）；并搜索 c<=C_MAX 内 quality>1 的 ABC 三元组。",
        "conjecture": "ABC",
        **search_abc_triples(c_max=ABC_C_MAX, top_k=8),
    }

    print(f"[E2] 哥德巴赫分拆穷举验证（n <= {GOLDBACH_LIMIT}）...")
    exp["E2_goldbach"] = {
        "method_id": "sieve_theory",
        "scope": "仅实现**哥德巴赫分拆计数**这一具体筛法应用；**不是** Selberg 筛/大筛法等一般理论。",
        "conjecture": "GC",
        **goldbach_profile(limit=GOLDBACH_LIMIT, sample_step=1000),
    }

    print(f"[E3] 孪生素数筛（<= {TWIN_LIMIT}）...")
    exp["E3_twin_primes"] = {
        "method_id": "sieve_theory",
        "scope": "仅实现孪生素数筛这一具体应用；非一般解析筛法。",
        "conjecture": "TPC",
        **twin_prime_profile(limit=TWIN_LIMIT),
    }

    print(f"[E4] 素数计数渐近对照（<= {PI_LIMIT}）...")
    exp["E4_prime_asymptotics"] = {
        "method_id": "asymptotic_estimation",
        "scope": "仅实现 π(x) 与 x/ln x、li(x) 的**数值对照**；非一般渐近展开推导工具。",
        "conjecture": None,
        **prime_count_asymptotics(limit=PI_LIMIT),
    }

    print(f"[E5] Collatz 模类统计（n <= {COLLATZ_N_MAX}, mod {COLLATZ_MODULUS}）...")
    exp["E5_collatz_modular"] = {
        "method_id": "modular_analysis",
        "scope": "按剩余类统计 Collatz 停止时间分布，是最朴素的模类统计；不提供证明方向。",
        "conjecture": "COLLATZ",
        **collatz_modular_profile(n_max=COLLATZ_N_MAX, modulus=COLLATZ_MODULUS),
    }

    doc = {
        "meta": {
            "generated_by": "06-AI自动化/01-工作流/openmath_experiments.py",
            "generated_at": GEN_AT,
            "provenance": PROVENANCE,
            "honesty": HONESTY,
            "engine": "openmath_sys/numbertheory.py",
            "purpose": "把突破路线图 Top4 方法（rad_computation / sieve_theory / "
                       "asymptotic_estimation / modular_analysis）实际实现并运行，产出 L2 证据。",
            "limits": {
                "abc_c_max": ABC_C_MAX, "goldbach_limit": GOLDBACH_LIMIT,
                "twin_limit": TWIN_LIMIT, "pi_limit": PI_LIMIT,
                "collatz_n_max": COLLATZ_N_MAX,
            },
        },
        "experiments": exp,
    }

    out = os.path.join(DATA_DIR, "nt_experiments.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2, default=str)

    # ---- 简报 ---------------------------------------------------------------
    e1 = exp["E1_abc_quality"]
    print(f"     quality>1 的三元组 {e1['triples_with_quality_above_1']} 个；"
          f"最高 q = {e1['top_by_quality'][0]['quality'] if e1['top_by_quality'] else 'N/A'}"
          f"  ({e1['top_by_quality'][0]['a']}+{e1['top_by_quality'][0]['b']}"
          f"={e1['top_by_quality'][0]['c']})" if e1['top_by_quality'] else "")
    e2 = exp["E2_goldbach"]
    print(f"     哥德巴赫：limit 内全部偶数均有分拆 = {e2['all_even_have_partition']}；"
          f"最少分拆 {e2['min_partitions']['count']} 出现在 n={e2['min_partitions']['n']}")
    print(f"     孪生素数：{exp['E3_twin_primes']['twin_pairs']} 对"
          f"（最大 {exp['E3_twin_primes']['largest_pair']}）")
    e4 = exp["E4_prime_asymptotics"]
    lx = e4.get("at_largest_x") or {}
    print(f"     π(x) 对照（最大检查点 x={lx.get('x')}）："
          f"li 误差 {lx.get('rel_err_li', 0) * 100:.2f}%  vs  "
          f"x/ln x 误差 {lx.get('rel_err_x_over_ln', 0) * 100:.2f}%"
          f"（小 x 处 li 反而更差，属正常现象）")
    print(f"     Collatz 模类均值：{exp['E5_collatz_modular']['overall_mean_steps']} 步")
    print(f"[OK] 已写：{out}")


if __name__ == "__main__":
    main()
