"""Self-contained HTML dashboard: dark, masonry ad-card explorer.

Layout modeled on the commercial ad-spy tools: a filter-chip bar up top
(niche, awareness, visual treatment, authority, subs vs one-time, traffic
tier), a live results count, and a masonry grid of ad cards each headed by
its brand. Double-click the file to open — no server, all data embedded,
filters run client-side.

Note: Meta only serves ad creatives behind authenticated snapshot URLs, so
cards are copy-first with a "View ad" link into the Ad Library itself.
"""
from __future__ import annotations

import json

from .db import Database

_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>DTCScout — pre-vetted winning ads</title>
<style>
  :root {
    --bg: #101014; --panel: #17171c; --card: #1c1c22; --line: #2a2a32;
    --ink: #ececf1; --ink-2: #a2a2ae; --ink-3: #6e6e7a; --accent: #e6e6ee;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--ink);
         font: 13px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif; margin: 0; }
  header { padding: 20px 28px 0; }
  h1 { font-size: 19px; margin: 0; letter-spacing: -.01em; }
  .sub { color: var(--ink-2); font-size: 12px; margin-top: 2px; }
  .bar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
         padding: 14px 28px; position: sticky; top: 0; background: var(--bg);
         border-bottom: 1px solid var(--line); z-index: 5; }
  .chip { position: relative; }
  .chip select {
    appearance: none; background: var(--panel); color: var(--ink-2);
    border: 1px solid var(--line); border-radius: 18px; padding: 6px 26px 6px 12px;
    font: 12px/1 inherit; cursor: pointer; }
  .chip select.on { color: var(--ink); border-color: var(--ink-3); background: var(--card); }
  .chip::after { content: "▾"; position: absolute; right: 11px; top: 7px;
                 font-size: 9px; color: var(--ink-3); pointer-events: none; }
  .spacer { flex: 1; }
  #count { color: var(--ink-2); font-size: 12px; }
  .grid { column-width: 300px; column-gap: 14px; padding: 18px 28px 40px; }
  .card { break-inside: avoid; background: var(--card); border: 1px solid var(--line);
          border-radius: 14px; margin: 0 0 14px; overflow: hidden; }
  .card-h { display: flex; align-items: center; gap: 9px; padding: 11px 13px 9px; }
  .avatar { width: 30px; height: 30px; border-radius: 8px; flex: none;
            display: grid; place-items: center; font-weight: 700; font-size: 13px;
            background: var(--panel); border: 1px solid var(--line); color: var(--ink); }
  .card-h .who { min-width: 0; }
  .card-h b { display: block; font-size: 13px; white-space: nowrap;
              overflow: hidden; text-overflow: ellipsis; }
  .card-h .niche { color: var(--ink-3); font-size: 11px; }
  .card-h .meta { margin-left: auto; text-align: right; color: var(--ink-3);
                  font-size: 11px; flex: none; }
  .headline { padding: 0 13px; font-weight: 600; font-size: 13px; }
  .body { padding: 4px 13px 0; color: var(--ink-2); font-size: 12px;
          display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical;
          overflow: hidden; }
  .tags { padding: 10px 13px 0; display: flex; flex-wrap: wrap; gap: 5px; }
  .tag { font-size: 10.5px; padding: 2px 8px; border-radius: 9px;
         background: var(--panel); border: 1px solid var(--line); color: var(--ink-2); }
  .tag.live { color: #9ee2a8; border-color: #2c4432; }
  .card-f { display: flex; align-items: center; gap: 8px; margin-top: 11px;
            padding: 9px 13px; border-top: 1px solid var(--line); }
  .card-f .domain { color: var(--ink-3); font-size: 11px; text-transform: uppercase;
                    letter-spacing: .04em; white-space: nowrap; overflow: hidden;
                    text-overflow: ellipsis; text-decoration: none; }
  .card-f .view { margin-left: auto; flex: none; font-size: 11.5px; font-weight: 600;
                  color: var(--ink); text-decoration: none; background: var(--panel);
                  border: 1px solid var(--line); border-radius: 8px; padding: 5px 10px; }
  .card-f .view:hover { border-color: var(--ink-3); }
  .empty { color: var(--ink-3); padding: 40px 28px; }
</style></head><body>
<header>
  <h1>DTCScout</h1>
  <div class="sub" id="tagline"></div>
</header>
<div class="bar" id="bar"><span class="spacer"></span><span id="count"></span></div>
<div class="grid" id="grid"></div>
<script>
const DATA = __DATA__;
const brandById = Object.fromEntries(DATA.brands.map(b => [b.page_id, b]));
// Only show ads whose brand is listed.
const ADS = DATA.ads.filter(a => brandById[a.page_id]);
document.getElementById('tagline').textContent =
  `${ADS.length.toLocaleString()} ads from ${DATA.brands.length.toLocaleString()} pre-vetted scaling brands · run ${DATA.run_date}`;

// ---- filter chips (each option shows its result count, spy-tool style) ----
const FILTERS = [
  {key: 'niche',            label: 'Niche',            of: a => brandById[a.page_id].niche},
  {key: 'awareness_level',  label: 'Awareness',        of: a => a.awareness_level},
  {key: 'visual_treatment', label: 'Visual treatment', of: a => a.visual_treatment},
  {key: 'authority_figure', label: 'Authority',        of: a => a.authority_figure},
  {key: 'offer_type',       label: 'Subs vs one-time', of: a => a.offer_type},
  {key: 'traffic_tier',     label: 'Monthly traffic',  of: a => brandById[a.page_id].traffic_tier},
  {key: 'active',           label: 'Activity',         of: a => a.stop_date ? 'stopped' : 'active'},
];
const state = {};
const bar = document.getElementById('bar');
for (const f of FILTERS) {
  const counts = {};
  for (const a of ADS) { const v = f.of(a); if (v && v !== 'unknown' && v !== 'none') counts[v] = (counts[v] || 0) + 1; }
  const opts = Object.entries(counts).sort((x, y) => y[1] - x[1]);
  if (!opts.length) continue;
  const wrap = document.createElement('span'); wrap.className = 'chip';
  const sel = document.createElement('select');
  sel.innerHTML = `<option value="">${f.label}</option>` +
    opts.map(([v, n]) => `<option value="${v}">${v.replaceAll('_', ' ')} · ${n.toLocaleString()}</option>`).join('');
  sel.onchange = () => { state[f.key] = sel.value; sel.classList.toggle('on', !!sel.value); render(); };
  wrap.appendChild(sel); bar.insertBefore(wrap, bar.querySelector('.spacer'));
}
// sort chip
const sortWrap = document.createElement('span'); sortWrap.className = 'chip';
const sortSel = document.createElement('select');
sortSel.innerHTML = `<option value="reach">Sort: reach</option>
  <option value="recent">Sort: newest</option>`;
sortSel.onchange = render;
sortWrap.appendChild(sortSel); bar.appendChild(sortWrap);

const initials = name => (name || '?').split(/\\s+/).slice(0, 2).map(w => w[0] || '').join('').toUpperCase();

function render() {
  let ads = ADS.filter(a => FILTERS.every(f => !state[f.key] || f.of(a) === state[f.key]));
  ads.sort(sortSel.value === 'recent'
    ? (x, y) => (y.start_date || '').localeCompare(x.start_date || '')
    : (x, y) => (y.eu_reach || 0) - (x.eu_reach || 0));
  document.getElementById('count').textContent = `${ads.length.toLocaleString()} results`;
  document.getElementById('grid').innerHTML = ads.map(a => {
    const b = brandById[a.page_id];
    const tags = [
      !a.stop_date ? '<span class="tag live">● active</span>' : '',
      ...['awareness_level', 'visual_treatment', 'authority_figure', 'offer_type']
        .map(k => a[k]).filter(v => v && v !== 'unknown' && v !== 'none')
        .map(v => `<span class="tag">${v.replaceAll('_', ' ')}</span>`),
      b.is_subscription ? '<span class="tag">subscription brand</span>' : '',
      b.traffic_tier !== 'unknown' ? `<span class="tag">traffic: ${b.traffic_tier}</span>` : '',
    ].join('');
    return `<div class="card">
      <div class="card-h">
        <span class="avatar">${initials(b.page_name)}</span>
        <span class="who"><b>${b.page_name}</b><span class="niche">${b.niche} · ${b.active_ads} active ads</span></span>
        <span class="meta">${(a.eu_reach || 0).toLocaleString()} reach<br>${a.start_date || ''}</span>
      </div>
      ${a.link_title ? `<div class="headline">${a.link_title}</div>` : ''}
      ${a.body ? `<div class="body">${a.body}</div>` : ''}
      <div class="tags">${tags}</div>
      <div class="card-f">
        <a class="domain" href="https://${b.domain}" target="_blank">${b.domain}</a>
        ${a.snapshot_url ? `<a class="view" href="${a.snapshot_url}" target="_blank">View ad ↗</a>` : ''}
      </div>
    </div>`;
  }).join('') || '<p class="empty">No ads match these filters.</p>';
}
render();
</script></body></html>
"""


def render_dashboard(db: Database, run_date: str) -> str:
    brands = db.brands(status="listed")
    ads = [ad for b in brands for ad in db.ads_for_brand(b["page_id"], top_n=25)]
    payload = json.dumps(
        {"brands": brands, "ads": ads, "run_date": run_date}, ensure_ascii=False
    )
    return _TEMPLATE.replace("__DATA__", payload)
