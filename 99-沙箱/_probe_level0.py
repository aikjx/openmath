# -*- coding: utf-8 -*-
"""临时探针：检查 CDCL 在 level 0 上的赋值是否与已知模型一致（不一致=零层传播不健全）。用完即删。"""
import importlib.util
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def load(prefix):
    for fn in os.listdir(HERE):
        if fn.startswith(prefix) and fn.endswith(".py"):
            spec = importlib.util.spec_from_file_location("m_" + prefix[:6],
                                                          os.path.join(HERE, fn))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    raise SystemExit("not found " + prefix)


sat = load("schur_SAT")
n, k = 13, 3
nv, clauses, V, ntri = sat.encode_schur(n, k)


def correct_model(nv, cls):
    assign = [0] * (nv + 1)

    def val(l):
        a = assign[abs(l)]
        return a if l > 0 else -a

    def rec():
        while True:
            ch = False
            for c in cls:
                un, satc, unit = 0, False, 0
                for l in c:
                    v = val(l)
                    if v == 1:
                        satc = True
                        break
                    if v == 0:
                        un += 1
                        unit = l
                if satc:
                    continue
                if un == 0:
                    return False
                if un == 1:
                    assign[abs(unit)] = 1 if unit > 0 else -1
                    ch = True
            if not ch:
                break
        t = 0
        for v in range(1, nv + 1):
            if assign[v] == 0:
                t = v
                break
        if t == 0:
            return True
        for w in (1, -1):
            snap = list(assign)
            assign[t] = w
            if rec():
                return True
            assign[:] = snap
        return False

    assert rec()
    return assign


model = correct_model(nv, clauses)
s = sat.CDCL(nv, clauses, seed=1)
st, _, _ = s.solve(deadline=time.time() + 5)
print("结果:", st, "conflicts", s.stats["conflicts"])

# 检查 UNSAT 时刻的全部赋值（不限 level 0）与参考模型是否冲突
bad = []
for v in range(1, nv + 1):
    if s.assign[v] != 0:
        if (s.assign[v] == 1) != (model[v] == 1):
            bad.append((v, s.assign[v], model[v], s.level[v], s.reason[v]))
print("与参考模型冲突的赋值数 =", len(bad))
for v, a, mref, lv, rs in bad[:15]:
    rc = s.clauses[rs] if rs >= 0 else None
    print("  var %3d 求解器=%2d 参考=%2d level=%d reason=%s %s"
          % (v, a, mref, lv, rs, rc))
