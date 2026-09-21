# -*- coding: utf-8 -*-
"""一次性补丁 2：替换残留的旧实验 7，并用程序化网格三角化替换手写的环面。"""
import io

P = (r"D:/a10/aikjx/code/my_lib/openmath/06-AI自动化/02-引擎/"
     r"openmath_sys/src/openmath_sys/millennium_lab.py")

NEW_HOMOLOGY = '''def exp_homology_sphere() -> Dict[str, Any]:
    """S³（4-单形边界，5 顶点）的同调：期望 b=(1,0,0,1)。

    **必要不充分**：存在同调球面（如 Poincaré 同调球面）其 H_* 与 S³ 相同
    但基本群非平凡。庞加莱猜想已由 Perelman 证明，此处**不重复证明**，
    只用它来校准同调计算代码。
    """
    from itertools import combinations
    maximal = [c for c in combinations(range(5), 4)]     # d4 的 5 个四面体
    cd = _chain_data(maximal, 3)
    return {
        "id": "homology_sphere_check",
        "problem": "POINCARE",
        "complex": "boundary of 4-simplex (5 vertices, homeomorphic to S3)",
        "betti": cd["betti"],
        "harmonic_dim": cd["harmonic_dim"],
        "expected_betti": [1, 0, 0, 1],
        "matches": cd["betti"] == [1, 0, 0, 1],
        "hodge_identity_holds": cd["betti"] == cd["harmonic_dim"],
        "caveat": (
            "同调条件**只是必要不充分**：Poincare 同调球面的 H_* 与 S3 相同，"
            "但基本群非平凡（120 阶），因此不同胚于 S3。"
            "庞加莱猜想已由 Perelman（2002-2003，Ricci 流 + 手术）证明；"
            "本仓库不声称贡献，此实验只用于校准同调计算代码。"
        ),
    }


'''

# 1) 替换旧的实验 7
s = io.open(P, encoding="utf-8").read()
start = s.index("# ---------------------------------------------------------------------------\n# 实验 7")
end = s.index("# ---------------------------------------------------------------------------\n# 汇总")
s = s[:start] + NEW_HOMOLOGY + s[end:]

# 2) 环面改用程序化生成的 m×m 网格三角化（手写的那份有重复单形，算出 b=[1,3,0]）
old_torus_start = s.index('        ("triangulated torus (= T²)", [')
old_torus_end = s.index("    ]\n    results = []")
new_torus = '''        ("torus grid 3x3 (= T²)", _torus_triangles(3), 2, [1, 2, 1]),
'''
s = s[:old_torus_start] + new_torus + s[old_torus_end:]

# 3) 插入 _torus_triangles 生成器（放在 exp_combinatorial_hodge 之前）
gen = '''def _torus_triangles(m: int = 3) -> List[Tuple[int, ...]]:
    """环面的 m×m 网格三角化：每个方格切成两个三角形，指标对 m 取模。

    为什么不手写单形表：手写的那份出现重复单形（同一顶点集被放了两次），
    于是算出 b=[1,3,0] 而不是 [1,2,1]。程序化生成能保证
      · 顶点数 m²，边数 3m²，面数 2m²
      · 欧拉示性数 V−E+F = 0（环面的正确值，可自检）
    """
    v = lambda i, j: (i % m) * m + (j % m)
    tris = []
    for i in range(m):
        for j in range(m):
            a, b = v(i, j), v(i + 1, j)
            c, d = v(i, j + 1), v(i + 1, j + 1)
            tris.append(tuple(sorted((a, b, c))))
            tris.append(tuple(sorted((b, d, c))))
    seen, out = set(), []
    for t in tris:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


'''
s = s.replace("def exp_combinatorial_hodge() -> Dict[str, Any]:",
              gen + "def exp_combinatorial_hodge() -> Dict[str, Any]:", 1)

io.open(P, "w", encoding="utf-8").write(s)
print("patched2; length", len(s))
