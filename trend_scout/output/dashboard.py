"""Generate a self-contained, offline HTML dashboard.

No server, no build step, no external assets: the whole thing is one .html file
with inline CSS + a little vanilla JS for sorting/filtering, and inline SVG
sparklines for each ingredient's trend. Double-click it to open in a browser.
"""
from __future__ import annotations

import html
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("trend_scout.output.dashboard")


def _sparkline_svg(values: list[float], width: int = 130, height: int = 34) -> str:
    """Inline SVG sparkline from a 0-100 interest series."""
    if not values:
        return '<span class="nodata">—</span>'
    n = len(values)
    if n == 1:
        values = values * 2
        n = 2
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    pad = 3
    w, h = width - 2 * pad, height - 2 * pad
    pts = []
    for i, v in enumerate(values):
        x = pad + (i / (n - 1)) * w
        y = pad + (1 - (v - lo) / span) * h
        pts.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(pts)
    last_x, last_y = pts[-1].split(",")
    rising = values[-1] >= values[0]
    color = "#16a34a" if rising else "#dc2626"
    area = f"{pad},{height-pad} {poly} {last_x},{height-pad}"
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'class="spark" preserveAspectRatio="none">'
        f'<polygon points="{area}" fill="{color}" fill-opacity="0.10"/>'
        f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.6"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.2" fill="{color}"/></svg>'
    )


def _badge(text: str, cls: str) -> str:
    return f'<span class="badge {cls}">{html.escape(text)}</span>'


def _row_html(r: dict[str, Any], series: list[float]) -> str:
    name = html.escape(str(r["ingredient"]))
    score = float(r.get("score", 0))
    growth = float(r.get("growth_pct", 0))
    growth_cls = "pos" if growth >= 0 else "neg"
    growth_txt = f"+{growth:.0f}%" if growth >= 0 else f"{growth:.0f}%"
    flags = ""
    if r.get("is_breakout"):
        flags += _badge("🔥 breakout", "breakout")
    if r.get("is_new"):
        flags += _badge("🆕 new", "new")
    row_cls = "is-breakout" if r.get("is_breakout") else ""
    # data-* attributes drive client-side sort/filter.
    return f"""<tr class="{row_cls}" data-name="{name.lower()}"
        data-score="{score}" data-growth="{growth}" data-breakout="{int(bool(r.get('is_breakout')))}">
      <td class="rank">{r.get('rank', '')}</td>
      <td class="name">{name}<div class="ctx">{html.escape(str(r.get('discovered_context','')))[:70]}</div></td>
      <td class="spark-cell">{_sparkline_svg(series)}</td>
      <td class="score"><div class="scorebar"><span style="width:{min(score,100):.0f}%"></span></div><b>{score:.0f}</b></td>
      <td class="growth {growth_cls}">{growth_txt}</td>
      <td class="flags">{flags}</td>
      <td class="src">{html.escape(str(r.get('source','')))}</td>
      <td class="links">
        <a href="{html.escape(str(r.get('kalodata_url','#')))}" target="_blank" rel="noopener">Kalodata</a>
        <a href="{html.escape(str(r.get('google_trends_url','#')))}" target="_blank" rel="noopener">Trends</a>
      </td>
    </tr>"""


def write_dashboard(
    rows: list[dict[str, Any]],
    series_map: dict[str, list[float]],
    path: str | os.PathLike,
    *,
    geo: str = "",
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    total = len(rows)
    n_breakouts = sum(1 for r in rows if r.get("is_breakout"))
    n_new = sum(1 for r in rows if r.get("is_new"))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    region = geo or "Worldwide"

    body_rows = "\n".join(_row_html(r, series_map.get(r["ingredient"], [])) for r in rows)

    doc = _TEMPLATE.format(
        generated=generated,
        region=html.escape(region),
        total=total,
        breakouts=n_breakouts,
        new=n_new,
        rows=body_rows,
    )
    path.write_text(doc, encoding="utf-8")
    log.info("wrote dashboard (%d rows) -> %s", total, path)
    return path


_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TrendScout — trending ingredients</title>
<style>
  :root {{ --bg:#0f172a; --card:#1e293b; --line:#334155; --txt:#e2e8f0; --mut:#94a3b8; --accent:#38bdf8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--txt); }}
  header {{ padding:24px 28px 8px; }}
  h1 {{ margin:0; font-size:22px; letter-spacing:.3px; }}
  .sub {{ color:var(--mut); font-size:13px; margin-top:4px; }}
  .cards {{ display:flex; gap:14px; padding:16px 28px; flex-wrap:wrap; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
          padding:14px 18px; min-width:140px; }}
  .kpi .n {{ font-size:26px; font-weight:700; }}
  .kpi .l {{ color:var(--mut); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }}
  .kpi.fire .n {{ color:#fb923c; }} .kpi.new .n {{ color:#38bdf8; }}
  .toolbar {{ display:flex; gap:12px; align-items:center; padding:6px 28px 14px; flex-wrap:wrap; }}
  input[type=search] {{ background:var(--card); border:1px solid var(--line); color:var(--txt);
        border-radius:8px; padding:9px 12px; width:260px; font-size:14px; }}
  label.tog {{ color:var(--mut); font-size:14px; display:flex; gap:6px; align-items:center; cursor:pointer; }}
  .wrap {{ padding:0 28px 40px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card);
           border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
  th {{ text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.5px;
        color:var(--mut); padding:12px 12px; border-bottom:1px solid var(--line); cursor:pointer; user-select:none; }}
  th[data-sort]:hover {{ color:var(--accent); }}
  td {{ padding:11px 12px; border-bottom:1px solid var(--line); font-size:14px; vertical-align:middle; }}
  tr.is-breakout td {{ background:rgba(251,146,60,.08); }}
  tr:hover td {{ background:rgba(56,189,248,.06); }}
  .rank {{ color:var(--mut); width:38px; }}
  .name b, td.name {{ font-weight:600; }}
  .ctx {{ color:var(--mut); font-size:11px; font-weight:400; margin-top:2px; }}
  .growth.pos {{ color:#4ade80; font-weight:600; }} .growth.neg {{ color:#f87171; }}
  .scorebar {{ display:inline-block; width:70px; height:7px; background:#0b1220; border-radius:4px;
        vertical-align:middle; margin-right:8px; overflow:hidden; }}
  .scorebar span {{ display:block; height:100%; background:linear-gradient(90deg,#38bdf8,#818cf8); }}
  .badge {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:99px; margin-right:4px; }}
  .badge.breakout {{ background:rgba(251,146,60,.18); color:#fdba74; }}
  .badge.new {{ background:rgba(56,189,248,.18); color:#7dd3fc; }}
  .links a {{ color:var(--accent); text-decoration:none; margin-right:10px; font-size:13px; }}
  .links a:hover {{ text-decoration:underline; }}
  .src {{ color:var(--mut); font-size:12px; }}
  .nodata {{ color:var(--mut); }}
  footer {{ color:var(--mut); font-size:12px; padding:0 28px 30px; }}
  .empty {{ padding:30px; text-align:center; color:var(--mut); }}
</style></head>
<body>
<header>
  <h1>🌿 TrendScout — trending ingredients</h1>
  <div class="sub">{region} · generated {generated} · click a column to sort</div>
</header>
<div class="cards">
  <div class="kpi"><div class="n">{total}</div><div class="l">Ingredients scored</div></div>
  <div class="kpi fire"><div class="n">{breakouts}</div><div class="l">🔥 Breakouts</div></div>
  <div class="kpi new"><div class="n">{new}</div><div class="l">🆕 New this run</div></div>
</div>
<div class="toolbar">
  <input id="q" type="search" placeholder="Filter ingredients…">
  <label class="tog"><input type="checkbox" id="onlyBreak"> Breakouts only</label>
</div>
<div class="wrap">
<table id="tbl">
  <thead><tr>
    <th>#</th>
    <th data-sort="name">Ingredient</th>
    <th>Trend (90d)</th>
    <th data-sort="score">Score</th>
    <th data-sort="growth">Growth</th>
    <th>Flags</th>
    <th>Source</th>
    <th>Research</th>
  </tr></thead>
  <tbody>
{rows}
  </tbody>
</table>
<div class="empty" id="empty" style="display:none">No ingredients match your filter.</div>
</div>
<footer>Built by TrendScout · momentum = growth × sustained-not-spike · links open Kalodata &amp; Google Trends.</footer>
<script>
  const tbody = document.querySelector('#tbl tbody');
  const rows = () => Array.from(tbody.querySelectorAll('tr'));
  let sortKey = 'score', sortDir = -1;
  function applySort() {{
    const sorted = rows().sort((a,b) => {{
      let av=a.dataset[sortKey], bv=b.dataset[sortKey];
      if (sortKey!=='name') {{ av=parseFloat(av); bv=parseFloat(bv); }}
      return av<bv ? sortDir : av>bv ? -sortDir : 0;
    }});
    sorted.forEach((r,i)=>{{ tbody.appendChild(r); r.querySelector('.rank').textContent=i+1; }});
  }}
  document.querySelectorAll('th[data-sort]').forEach(th=>{{
    th.addEventListener('click',()=>{{ const k=th.dataset.sort;
      sortDir = (sortKey===k) ? -sortDir : (k==='name'?1:-1); sortKey=k; applySort(); applyFilter(); }});
  }});
  function applyFilter() {{
    const q=document.getElementById('q').value.toLowerCase();
    const only=document.getElementById('onlyBreak').checked;
    let shown=0;
    rows().forEach(r=>{{
      const ok = r.dataset.name.includes(q) && (!only || r.dataset.breakout==='1');
      r.style.display = ok ? '' : 'none'; if(ok) shown++;
    }});
    document.getElementById('empty').style.display = shown ? 'none':'block';
  }}
  document.getElementById('q').addEventListener('input', applyFilter);
  document.getElementById('onlyBreak').addEventListener('change', applyFilter);
  applySort();
</script>
</body></html>
"""
