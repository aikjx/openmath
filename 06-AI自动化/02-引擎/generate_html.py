"""生成自包含 HTML 图谱浏览器（人人爱用：双击即开，无外部依赖）。

读 knowledge_graph.json → 内嵌数据 + 原生 SVG 力导向 → 单文件 HTML。
- 默认渲染 hubs top 80 + 直接邻居（避免 537 节点全图爆炸）
- 按节点类型着色，搜索过滤，hover 高亮邻居，点击看详情
"""
from __future__ import annotations

import json
import os
from collections import Counter

GRAPH_JSON = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "knowledge_graph.json")
OUT_HTML = os.path.join(os.path.dirname(__file__), "openmath_sys", "output", "graph_browser.html")

# 节点类型配色
COLORS = {
    "WORK": "#3b82f6", "THEOREM": "#f97316", "CLAIM": "#22c55e",
    "AUDIT": "#ef4444", "FINDING": "#eab308", "PERSONA": "#a855f7",
    "TOOL": "#06b6d4", "DATASET": "#94a3b8",
}


def main() -> None:
    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data["nodes"]
    edges = data["edges"]

    # 度排行
    degree = Counter()
    for e in edges:
        degree[e["src"]] += 1
        degree[e["dst"]] += 1

    # 默认集：top 80 枢纽 + 它们直接邻居
    top_ids = {nid for nid, _ in degree.most_common(80)}
    neighbor_ids = set(top_ids)
    for e in edges:
        if e["src"] in top_ids or e["dst"] in top_ids:
            neighbor_ids.add(e["src"])
            neighbor_ids.add(e["dst"])

    sub_nodes = [n for n in nodes if n["node_id"] in neighbor_ids]
    sub_node_ids = {n["node_id"] for n in sub_nodes}
    sub_edges = [e for e in edges if e["src"] in sub_node_ids and e["dst"] in sub_node_ids]

    stats = data.get("stats", {})

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>统一研究知识图谱浏览器</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #f8fafc; color: #0f172a; }}
  header {{ background: #1e293b; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }}
  header h1 {{ font-size: 16px; }}
  header .stats {{ font-size: 12px; color: #94a3b8; }}
  .toolbar {{ padding: 10px 20px; background: #fff; border-bottom: 1px solid #e2e8f0; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
  .toolbar input {{ padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; width: 240px; }}
  .legend {{ display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; }}
  .legend span {{ display: inline-flex; align-items: center; gap: 4px; }}
  .legend i {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  .main {{ display: flex; height: calc(100vh - 110px); }}
  #graph {{ flex: 1; background: #fff; }}
  .detail {{ width: 300px; padding: 16px; background: #fff; border-left: 1px solid #e2e8f0; overflow-y: auto; font-size: 13px; }}
  .detail h3 {{ font-size: 14px; margin-bottom: 8px; }}
  .detail .meta {{ color: #64748b; font-size: 12px; margin-bottom: 8px; }}
  .detail ul {{ list-style: none; }}
  .detail li {{ padding: 4px 0; border-bottom: 1px solid #f1f5f9; }}
  .edge-line {{ stroke: #cbd5e1; stroke-width: 0.5; }}
  .node {{ cursor: pointer; }}
  .node text {{ font-size: 9px; fill: #475569; pointer-events: none; }}
  .node circle {{ stroke: #fff; stroke-width: 1.5; }}
  .highlight {{ stroke: #0f172a !important; stroke-width: 2 !important; }}
  .filter-btn {{ padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 12px; background: #fff; cursor: pointer; font-size: 11px; }}
  .filter-btn.active {{ background: #3b82f6; color: #fff; border-color: #3b82f6; }}
</style>
</head>
<body>
<header>
  <h1>统一研究知识图谱浏览器</h1>
  <div class="stats">节点 {stats.get('nodes', len(nodes))} · 边 {stats.get('edges', len(edges))} · 渲染 {len(sub_nodes)} 节点 / {len(sub_edges)} 边</div>
</header>
<div class="toolbar">
  <input id="search" placeholder="搜索节点标签（如 goldbach / T09 / 勘误）">
  <div class="legend">
    {''.join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in COLORS.items())}
  </div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;font-size:11px;">
    <button class="filter-btn active" data-domain="all">全部</button>
    <button class="filter-btn" data-domain="tuft">TUFT</button>
    <button class="filter-btn" data-domain="coalition">算法联盟</button>
    <button class="filter-btn" data-domain="zhiyu">织域平台</button>
    <button class="filter-btn" data-domain="goldbach">Goldbach</button>
    <button class="filter-btn" data-domain="openuft">OpenUFT</button>
  </div>
</div>
<div class="main">
  <svg id="graph"></svg>
  <div class="detail" id="detail"><h3>点击节点查看详情</h3><div class="meta">hover 高亮邻居</div></div>
</div>
<script>
const NODES = {json.dumps(sub_nodes, ensure_ascii=False)};
const EDGES = {json.dumps(sub_edges, ensure_ascii=False)};
const COLORS = {json.dumps(COLORS)};

const svg = document.getElementById('graph');
const W = svg.clientWidth, H = svg.clientHeight;
svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);

// 初始化位置（环形）
const positions = {{}};
NODES.forEach((n, i) => {{
  const angle = (i / NODES.length) * Math.PI * 2;
  positions[n.node_id] = {{ x: W/2 + Math.cos(angle) * W * 0.35, y: H/2 + Math.sin(angle) * H * 0.35, vx: 0, vy: 0 }};
}});

// 简易力导向（150 帧收敛）
for (let iter = 0; iter < 150; iter++) {{
  // 斥力
  for (const a of NODES) for (const b of NODES) {{
    if (a.node_id === b.node_id) continue;
    const pa = positions[a.node_id], pb = positions[b.node_id];
    const dx = pa.x - pb.x, dy = pa.y - pb.y;
    const d = Math.sqrt(dx*dx + dy*dy) + 0.01;
    const force = 2000 / (d * d);
    pa.vx += (dx / d) * force; pa.vy += (dy / d) * force;
  }}
  // 弹簧
  for (const e of EDGES) {{
    const pa = positions[e.src], pb = positions[e.dst];
    if (!pa || !pb) continue;
    const dx = pb.x - pa.x, dy = pb.y - pa.y;
    const d = Math.sqrt(dx*dx + dy*dy) + 0.01;
    const force = (d - 100) * 0.02;
    pa.vx += (dx / d) * force; pa.vy += (dy / d) * force;
    pb.vx -= (dx / d) * force; pb.vy -= (dy / d) * force;
  }}
  // 积分
  for (const n of NODES) {{
    const p = positions[n.node_id];
    p.vx *= 0.9; p.vy *= 0.9;
    p.x += p.vx; p.y += p.vy;
    p.x = Math.max(20, Math.min(W-20, p.x));
    p.y = Math.max(20, Math.min(H-20, p.y));
  }}
}}

// 渲染边
const edgeG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
EDGES.forEach(e => {{
  const pa = positions[e.src], pb = positions[e.dst];
  if (!pa || !pb) return;
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', pa.x); line.setAttribute('y1', pa.y);
  line.setAttribute('x2', pb.x); line.setAttribute('y2', pb.y);
  line.setAttribute('class', 'edge-line');
  line.dataset.src = e.src; line.dataset.dst = e.dst;
  edgeG.appendChild(line);
}});
svg.appendChild(edgeG);

// 渲染节点
const nodeG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
NODES.forEach(n => {{
  const p = positions[n.node_id];
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('class', 'node');
  g.dataset.id = n.node_id;
  g.setAttribute('transform', `translate(${{p.x}},${{p.y}})`);
  const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  c.setAttribute('r', n.ntype === 'DATASET' ? 6 : 4);
  c.setAttribute('fill', COLORS[n.ntype] || '#94a3b8');
  const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  t.setAttribute('dy', -8);
  t.setAttribute('text-anchor', 'middle');
  t.textContent = n.label.length > 18 ? n.label.slice(0, 18) + '…' : n.label;
  g.appendChild(c); g.appendChild(t);
  g.addEventListener('click', () => showDetail(n));
  g.addEventListener('mouseenter', () => highlight(n.node_id));
  g.addEventListener('mouseleave', () => unhighlight());
  nodeG.appendChild(g);
}});
svg.appendChild(nodeG);

function neighbors(id) {{
  const set = new Set([id]);
  EDGES.forEach(e => {{
    if (e.src === id) set.add(e.dst);
    if (e.dst === id) set.add(e.src);
  }});
  return set;
}}

function highlight(id) {{
  const ns = neighbors(id);
  document.querySelectorAll('.node').forEach(g => {{
    g.querySelector('circle').classList.toggle('highlight', ns.has(g.dataset.id));
  }});
}}

function unhighlight() {{
  document.querySelectorAll('.node circle').forEach(c => c.classList.remove('highlight'));
}}

function showDetail(n) {{
  const ns = neighbors(n.node_id);
  const detail = document.getElementById('detail');
  const rel = EDGES.filter(e => e.src === n.node_id || e.dst === n.node_id)
    .map(e => {{
      const other = e.src === n.node_id ? e.dst : e.src;
      const on = NODES.find(x => x.node_id === other);
      const label = on ? on.label : other;
      const dir = e.src === n.node_id ? '→' : '←';
      return `<li>${{dir}} [${{e.etype}}] ${{label}}</li>`;
    }}).join('');
  detail.innerHTML = `<h3>${{n.label}}</h3>
    <div class="meta">类型: ${{n.ntype}} · ID: ${{n.node_id}}</div>
    ${{n.attrs && n.attrs.verdict ? `<div class="meta">判决: ${{n.attrs.verdict}}</div>` : ''}}
    <h4 style="margin:10px 0 4px;font-size:12px;">关联 (${{ns.size-1}})</h4>
    <ul>${{rel || '<li>无</li>'}}</ul>`;
}}

// 搜索
document.getElementById('search').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  applyFilters(q, currentDomain);
}});

// 域过滤
let currentDomain = 'all';
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentDomain = btn.dataset.domain;
    applyFilters(document.getElementById('search').value.toLowerCase(), currentDomain);
  }});
}});

function applyFilters(q, domain) {{
  document.querySelectorAll('.node').forEach(g => {{
    const n = NODES.find(x => x.node_id === g.dataset.id);
    const matchQ = !q || n.label.toLowerCase().includes(q);
    const matchDomain = domain === 'all' || (n.attrs && n.attrs.domain === domain);
    g.style.display = (matchQ && matchDomain) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"=== 图谱浏览器已生成 ===")
    print(f"输出: {OUT_HTML}")
    print(f"渲染集: {len(sub_nodes)} 节点 / {len(sub_edges)} 边（top 80 枢纽 + 邻居）")
    print(f"全图: {len(nodes)} 节点 / {len(edges)} 边")


if __name__ == "__main__":
    main()
