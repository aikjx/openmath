# -*- coding: utf-8 -*-
"""OM-P-NT-0003 哥德巴赫 · PWCV 中央筛结构的 L2 精确整数验证引擎。

验证性质：exact_integer_enumeration（全量枚举的精确整数恒等，非随机采样、非浮点近似）。
所有“残差”都是精确整数差，恒为 0 表示恒等成立；反例计数恒为 0 表示该结构断言无反例。

诚实声明（红线一/红线五；本库无 L4 形式化）：
  L2 PASS 只能证伪、不能证明。下列短证明（定理 A/B(ii)/D）即使为真，
  在本库证据体系内也停留在 L2，须经人类专家复核（L5）与形式化（L4）方可升级。

覆盖断言（E = 10^6, 10^7，全量）：
  A1 锚点：无序素对数 G(E) 等于已知值 5402 / 38807（残差须 0）。
  A2 定理A：递推筛到 sqrtE 的奇存活数 S == 直接素对计数 H_direct（残差须 0），且全部存活者两数皆素。
  A3 定理B(i)：全素数态(p>E^{1/3})被杀者=pk 且 k 素；k 非素反例须 0。
  A4 定理B(ii)+D：另一数 n=E-pk 为素或恰两大因子半素；半素最小因子 q1>z^-；反例须 0。

运行：python pwcv_goldbach_l2.py
依赖：numpy（环境 2.5.x）。独立基准：埃拉托色尼素数位图（不引用被测模型）。
"""
from __future__ import annotations
import json, math, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ANCHOR = {1_000_000: 5402, 10_000_000: 38807}


def primes_up_to(E: int):
    isp = np.ones(E + 1, dtype=bool)
    isp[:2] = False
    for i in range(2, int(math.isqrt(E)) + 1):
        if isp[i]:
            isp[i * i::i] = False
    return isp, np.nonzero(isp)[0]


def verify(E: int):
    isp, pa = primes_up_to(E)
    sqrtE = math.isqrt(E)
    thr = E ** (1.0 / 3.0)
    lo, hi = sqrtE + 1, E // 2
    nN = hi - lo + 1

    # A1 无序素对（直接、独立）
    mh = np.arange(2, hi + 1)
    G = int(np.sum(isp[mh] & isp[E - mh]))

    # A2 中央递推筛（奇候选）
    mask = np.ones(nN, dtype=bool)
    mask[1::2] = False
    K = 0
    k_nonprime = 0
    nprime = nsemi = 0
    q1_viol = 0
    c1_list = []
    logE = math.log(E)
    for p in pa:
        if p <= 2 or p > sqrtE:
            continue
        f0 = ((lo + p - 1) // p) * p
        i0 = np.arange(f0 - lo, nN, p)
        h0 = mask[i0]
        m0 = lo + i0[np.nonzero(h0)[0]]
        if E % p == 0:
            mE = np.empty(0, dtype=int)
            mask[i0] = False
        else:
            fE = lo + ((E % p) - lo) % p
            iE = np.arange(fE - lo, nN, p)
            hE = mask[iE]
            mE = lo + iE[np.nonzero(hE)[0]]
            mask[i0] = False
            mask[iE] = False
        if p <= thr:
            continue  # 递推对全部 p 进行；结构断言仅在全素数态收集
        zprev = int(pa[int(np.searchsorted(pa, p, side="left")) - 1])
        K += int(h0.sum()) + (int(hE.sum()) if E % p != 0 else 0)
        if len(m0):
            k_nonprime += int((~isp[m0 // p]).sum())
        if E % p != 0 and len(mE):
            k_nonprime += int((~isp[(E - mE) // p]).sum())
        ee = np.concatenate([E - m0, mE]) if (len(m0) + len(mE)) else np.empty(0, dtype=int)
        if not len(ee):
            continue
        nprime += int(isp[ee].sum())
        semis = ee[~isp[ee]]
        nsemi += len(semis)
        loq = int(np.searchsorted(pa, zprev, side="right"))
        for nv in semis:
            hiq = int(np.searchsorted(pa, math.isqrt(int(nv)), side="right"))
            seg = pa[loq:hiq]
            hit = seg[int(nv) % seg == 0]
            if len(hit):
                q1 = int(hit[0])
                c1_list.append(math.log(q1) / logE)
                if q1 <= zprev:
                    q1_viol += 1
            else:
                q1_viol += 1  # 分解失败也计为结构反例

    S = int(mask.sum())
    cm = np.arange(lo, hi + 1)
    H_direct = int(np.sum(isp[cm] & isp[E - cm]))
    all_prime = bool(np.all(isp[cm[mask]] & isp[E - cm[mask]]))
    c1 = np.array(c1_list) if c1_list else np.array([0.0])

    return {
        "E": E,
        "G_unordered": G,
        "G_anchor": ANCHOR[E],
        "resid_G": G - ANCHOR[E],
        "S_recursive": S,
        "H_direct_primepairs": H_direct,
        "resid_survive_minus_direct": S - H_direct,
        "all_survivors_prime_pairs": all_prime,
        "K_killed_full_prime_phase": K,
        "k_nonprime_counterexamples": k_nonprime,
        "n_prime": nprime,
        "n_semiprime": nsemi,
        "semi_frac": round(nsemi / K, 6) if K else None,
        "semiprime_over_H": round(nsemi / H_direct, 6) if H_direct else None,
        "q1_le_zprev_counterexamples": q1_viol,
        "c1_p50": round(float(np.median(c1)), 4),
        "c1_max": round(float(c1.max()), 4),
    }


def main():
    t0 = time.time()
    per_E = [verify(E) for E in sorted(ANCHOR)]
    ok = all(
        r["resid_G"] == 0
        and r["resid_survive_minus_direct"] == 0
        and r["all_survivors_prime_pairs"]
        and r["k_nonprime_counterexamples"] == 0
        and r["q1_le_zprev_counterexamples"] == 0
        for r in per_E
    )
    result = {
        "result": {
            "target_id": "OM-P-NT-0003",
            "level": "L2",
            "verification_kind": "exact_integer_enumeration",
            "status": "PASS" if ok else "FAIL",
            "engine": {"name": "pwcv_goldbach_l2.py", "version": "1.0"},
            "environment": {
                "python": platform.python_version(),
                "platform": sys.platform,
                "numpy": np.__version__,
            },
            "metrics": {
                "note": "残差/反例均为精确整数；0=恒等成立或无反例。全量枚举，非采样。",
                "per_E": per_E,
            },
            "caveat": [
                "L2 只能证伪不能证明（本库无 L4 形式化；红线五：AI 证明不作 L3+ 证据）。",
                "全量枚举上限 E=10^7；H(E)>0 的更广数值记录至 10^8（见配套研究文档），公开记录至 4e18。",
                "强哥德巴赫本身仍 OPEN；本结果仅核对中央筛结构恒等式，不蕴含渐近结论。",
            ],
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_ms": int((time.time() - t0) * 1000),
        }
    }
    out = Path(__file__).resolve().parents[1] / "03-结果" / "2026" / "09" / "OM-P-NT-0003-L2-20260911.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in per_E:
        print(json.dumps(r, ensure_ascii=False))
    print("OVERALL:", result["result"]["status"], "| saved:", out)


if __name__ == "__main__":
    main()
