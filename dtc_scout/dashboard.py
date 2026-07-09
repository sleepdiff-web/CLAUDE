"""Self-contained HTML dashboard: dark ad explorer + following ledger +
brand detail pages + swipe files.

Views (no server, all data embedded, double-click to open):
  Explore     masonry ad cards with filter chips (per-option counts)
  Following   sortable ledger of brands you follow — ad-activity sparkline,
              best sellers, avg ad life, median price
  Swipe files save any ad into named collections
Clicking a brand name anywhere opens its detail page: stat tiles, creative
pattern / awareness / offer mixes, catalog freshness, bestsellers, top ads.

Follows and swipe files persist in the browser's localStorage (this is an
internal tool; export/import can come later). Meta locks ad creatives behind
authenticated URLs, so cards are copy-first with a "View ad" link.
"""
from __future__ import annotations

import json

from .db import Database

_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>DTCScout — pre-vetted winning ads</title>
<style>
  :root {
    --bg: #101014; --panel: #17171c; --card: #1c1c22; --line: #2a2a32;
    --ink: #ececf1; --ink-2: #a2a2ae; --ink-3: #6e6e7a;
    --up: #7fd28b; --down: #e08a8a;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--ink);
         font: 13px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif; margin: 0; }
  a { color: inherit; }
  header { display: flex; align-items: baseline; gap: 22px; padding: 20px 28px 12px; }
  h1 { font-size: 19px; margin: 0; letter-spacing: -.01em; }
  nav a { color: var(--ink-3); text-decoration: none; font-size: 13px; margin-right: 16px;
          padding-bottom: 3px; cursor: pointer; }
  nav a.on { color: var(--ink); border-bottom: 2px solid var(--ink); }
  .sub { color: var(--ink-2); font-size: 12px; margin-left: auto; }
  .bar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
         padding: 12px 28px; position: sticky; top: 0; background: var(--bg);
         border-bottom: 1px solid var(--line); z-index: 5; }
  .chip { position: relative; }
  .chip select { appearance: none; background: var(--panel); color: var(--ink-2);
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
  .avatar { width: 30px; height: 30px; border-radius: 8px; flex: none; display: grid;
            place-items: center; font-weight: 700; font-size: 13px;
            background: var(--panel); border: 1px solid var(--line); }
  .who { min-width: 0; cursor: pointer; }
  .who b { display: block; font-size: 13px; white-space: nowrap; overflow: hidden;
           text-overflow: ellipsis; }
  .who:hover b { text-decoration: underline; }
  .who .niche { color: var(--ink-3); font-size: 11px; }
  .card-h .meta { margin-left: auto; text-align: right; color: var(--ink-3);
                  font-size: 11px; flex: none; }
  .headline { padding: 0 13px; font-weight: 600; font-size: 13px; }
  .body { padding: 4px 13px 0; color: var(--ink-2); font-size: 12px; display: -webkit-box;
          -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
  .tags { padding: 10px 13px 0; display: flex; flex-wrap: wrap; gap: 5px; }
  .tag { font-size: 10.5px; padding: 2px 8px; border-radius: 9px; background: var(--panel);
         border: 1px solid var(--line); color: var(--ink-2); }
  .tag.live { color: var(--up); border-color: #2c4432; }
  .card-f { display: flex; align-items: center; gap: 8px; margin-top: 11px;
            padding: 9px 13px; border-top: 1px solid var(--line); }
  .card-f .domain { color: var(--ink-3); font-size: 11px; text-transform: uppercase;
    letter-spacing: .04em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    text-decoration: none; }
  .btn { flex: none; font-size: 11.5px; font-weight: 600; color: var(--ink);
         text-decoration: none; background: var(--panel); border: 1px solid var(--line);
         border-radius: 8px; padding: 5px 10px; cursor: pointer; }
  .btn:hover { border-color: var(--ink-3); }
  .btn.right { margin-left: auto; }
  .heart { cursor: pointer; font-size: 14px; color: var(--ink-3); flex: none;
           background: none; border: none; padding: 2px; }
  .heart.on { color: #e77; }
  .empty { color: var(--ink-3); padding: 40px 28px; }
  /* ledger */
  table.ledger { width: calc(100% - 56px); margin: 18px 28px 40px; border-collapse: collapse; }
  .ledger th { text-align: left; font-size: 10.5px; letter-spacing: .06em; color: var(--ink-3);
    text-transform: uppercase; padding: 8px 10px; border-bottom: 1px solid var(--line);
    cursor: pointer; white-space: nowrap; }
  .ledger td { padding: 12px 10px; border-bottom: 1px solid var(--line);
               font-size: 12.5px; vertical-align: middle; }
  .ledger .b { font-weight: 600; cursor: pointer; }
  .ledger .b:hover { text-decoration: underline; }
  .ledger .d { color: var(--ink-3); font-size: 11px; }
  .delta.up { color: var(--up); } .delta.down { color: var(--down); }
  .thumbs { display: flex; gap: 4px; }
  .thumbs img { width: 30px; height: 30px; border-radius: 6px; object-fit: cover;
                border: 1px solid var(--line); background: var(--panel); }
  /* detail overlay */
  #detail { position: fixed; inset: 0; background: rgba(10,10,14,.72); z-index: 20;
            display: none; overflow: auto; }
  #detail.open { display: block; }
  .sheet { max-width: 980px; margin: 40px auto; background: var(--bg);
           border: 1px solid var(--line); border-radius: 16px; padding: 24px 28px 34px; }
  .sheet-h { display: flex; align-items: center; gap: 12px; }
  .sheet-h h2 { margin: 0; font-size: 18px; }
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
           gap: 10px; margin: 18px 0; }
  .tile { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 12px 14px; }
  .tile .k { font-size: 10.5px; letter-spacing: .06em; text-transform: uppercase;
             color: var(--ink-3); }
  .tile .v { font-size: 19px; font-weight: 700; margin-top: 2px; }
  .tile .s { font-size: 11px; color: var(--ink-3); }
  .cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 10px; }
  .panel { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
           padding: 12px 14px; }
  .panel h3 { margin: 0 0 10px; font-size: 11px; letter-spacing: .06em;
              text-transform: uppercase; color: var(--ink-3); }
  .mixrow { display: grid; grid-template-columns: 110px 1fr 58px; gap: 8px;
            align-items: center; margin: 6px 0; font-size: 12px; }
  .mixbar { height: 6px; border-radius: 3px; background: var(--panel); overflow: hidden; }
  .mixbar i { display: block; height: 100%; border-radius: 3px; background: var(--ink-2); }
  .mixrow .n { color: var(--ink-2); text-align: right; }
  .best { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
          gap: 10px; margin-top: 10px; }
  .prod { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
          overflow: hidden; font-size: 11px; }
  .prod img { width: 100%; aspect-ratio: 1; object-fit: cover; background: var(--panel);
              display: block; }
  .prod .noimg { width: 100%; aspect-ratio: 1; display: grid; place-items: center;
                 color: var(--ink-3); background: var(--panel); }
  .prod .t { padding: 6px 8px 1px; display: -webkit-box; -webkit-line-clamp: 2;
             -webkit-box-orient: vertical; overflow: hidden; }
  .prod .p { padding: 0 8px 7px; color: var(--ink-2); }
  svg.spark { display: block; }
  svg.spark path { fill: none; stroke: var(--ink-2); stroke-width: 2;
                   stroke-linecap: round; stroke-linejoin: round; }
  svg.spark.up path { stroke: var(--up); } svg.spark.down path { stroke: var(--down); }
</style></head><body>
<header>
  <h1>DTCScout</h1>
  <nav>
    <a data-view="explore" class="on">Explore</a>
    <a data-view="following">Following</a>
    <a data-view="swipes">Swipe files</a>
  </nav>
  <span class="sub" id="tagline"></span>
</header>
<div class="bar" id="bar"><span class="spacer"></span><span id="count"></span></div>
<div id="view"></div>
<div id="detail" onclick="if(event.target===this)this.classList.remove('open')"><div class="sheet" id="sheet"></div></div>
<script>
const DATA = __DATA__;
const brandById = Object.fromEntries(DATA.brands.map(b => [b.page_id, b]));
const ADS = DATA.ads.filter(a => brandById[a.page_id]);
const productsBy = {}, snapsBy = {};
for (const p of DATA.products) (productsBy[p.page_id] ||= []).push(p);
for (const s of DATA.snapshots) (snapsBy[s.page_id] ||= []).push(s);
document.getElementById('tagline').textContent =
  `${ADS.length.toLocaleString()} ads · ${DATA.brands.length.toLocaleString()} pre-vetted brands · run ${DATA.run_date}`;

// ---- persistence (localStorage) -------------------------------------------
const store = (k, v) => v === undefined ? JSON.parse(localStorage.getItem(k) || 'null') : localStorage.setItem(k, JSON.stringify(v));
let followed = new Set(store('dtc_followed') || []);
let swipes = store('dtc_swipes') || {};   // {fileName: [archive_id,...]}
const saveFollow = () => store('dtc_followed', [...followed]);
const saveSwipes = () => store('dtc_swipes', swipes);

// ---- helpers ----------------------------------------------------------------
const initials = n => (n || '?').split(/\\s+/).slice(0, 2).map(w => w[0] || '').join('').toUpperCase();
const fmt = n => (n == null ? '—' : Number(n).toLocaleString());
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function spark(values, w = 90, h = 26) {
  if (!values || values.length < 2) return `<span class="d">–</span>`;
  const min = Math.min(...values), max = Math.max(...values), span = (max - min) || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * (w - 4) + 2},${h - 3 - ((v - min) / span) * (h - 6)}`);
  const dir = values[values.length - 1] > values[0] ? 'up' : values[values.length - 1] < values[0] ? 'down' : '';
  return `<svg class="spark ${dir}" width="${w}" height="${h}" role="img"><path d="M${pts.join(' L')}"/></svg>`;
}
const heartBtn = pid =>
  `<button class="heart ${followed.has(pid) ? 'on' : ''}" title="Follow" onclick="toggleFollow('${pid}', this)">${followed.has(pid) ? '♥' : '♡'}</button>`;
function toggleFollow(pid, el) {
  followed.has(pid) ? followed.delete(pid) : followed.add(pid);
  saveFollow();
  el.classList.toggle('on'); el.textContent = followed.has(pid) ? '♥' : '♡';
  if (view === 'following') render();
}
function saveToSwipe(adId) {
  const names = Object.keys(swipes);
  const pick = prompt('Save to swipe file:\\n' + (names.length ? names.map((n, i) => `${i + 1}. ${n}`).join('\\n') + '\\n\\nType a number, or a new name:' : 'Type a name for your first swipe file:'));
  if (!pick) return;
  const name = /^\\d+$/.test(pick.trim()) && names[+pick.trim() - 1] ? names[+pick.trim() - 1] : pick.trim();
  swipes[name] ||= [];
  if (!swipes[name].includes(adId)) swipes[name].push(adId);
  saveSwipes();
}

// ---- ad card (shared by explore + swipes) -----------------------------------
function adCard(a, inSwipeFile) {
  const b = brandById[a.page_id];
  const tags = [
    !a.stop_date ? '<span class="tag live">● active</span>' : '',
    ...['awareness_level', 'visual_treatment', 'authority_figure', 'offer_type']
      .map(k => a[k]).filter(v => v && v !== 'unknown' && v !== 'none')
      .map(v => `<span class="tag">${v.replaceAll('_', ' ')}</span>`),
    b.is_subscription ? '<span class="tag">subscription brand</span>' : '',
    b.traffic_tier !== 'unknown' ? `<span class="tag">traffic: ${b.traffic_tier}</span>` : '',
  ].join('');
  const action = inSwipeFile
    ? `<button class="btn right" onclick="removeSwipe('${inSwipeFile}','${a.archive_id}')">Remove</button>`
    : `<button class="btn right" onclick="saveToSwipe('${a.archive_id}')">＋ Save</button>`;
  return `<div class="card">
    <div class="card-h">
      <span class="avatar">${initials(b.page_name)}</span>
      <span class="who" onclick="openDetail('${b.page_id}')"><b>${esc(b.page_name)}</b><span class="niche">${b.niche} · ${b.active_ads} active ads</span></span>
      <span class="meta">${fmt(a.eu_reach)} reach<br>${a.start_date || ''}</span>
      ${heartBtn(b.page_id)}
    </div>
    ${a.link_title ? `<div class="headline">${esc(a.link_title)}</div>` : ''}
    ${a.body ? `<div class="body">${esc(a.body)}</div>` : ''}
    <div class="tags">${tags}</div>
    <div class="card-f">
      <a class="domain" href="https://${b.domain}" target="_blank">${b.domain}</a>
      ${action}
      ${a.snapshot_url ? `<a class="btn" href="${a.snapshot_url}" target="_blank">View ad ↗</a>` : ''}
    </div>
  </div>`;
}

// ---- explore view -------------------------------------------------------------
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
const sortWrap = document.createElement('span'); sortWrap.className = 'chip';
const sortSel = document.createElement('select');
sortSel.innerHTML = `<option value="reach">Sort: reach</option><option value="recent">Sort: newest</option>`;
sortSel.onchange = () => render();
sortWrap.appendChild(sortSel); bar.appendChild(sortWrap);

function renderExplore(el) {
  let ads = ADS.filter(a => FILTERS.every(f => !state[f.key] || f.of(a) === state[f.key]));
  ads.sort(sortSel.value === 'recent'
    ? (x, y) => (y.start_date || '').localeCompare(x.start_date || '')
    : (x, y) => (y.eu_reach || 0) - (x.eu_reach || 0));
  document.getElementById('count').textContent = `${ads.length.toLocaleString()} results`;
  el.innerHTML = `<div class="grid">${ads.map(a => adCard(a)).join('')}</div>` ||
    '<p class="empty">No ads match.</p>';
}

// ---- following ledger ---------------------------------------------------------
let ledgerSort = {key: 'total_eu_reach', dir: -1};
function ledgerRow(b) {
  const snaps = snapsBy[b.page_id] || [];
  const series = snaps.map(s => s.active_ads);
  const delta = series.length > 1 ? series[series.length - 1] - series[0] : 0;
  const prods = (productsBy[b.page_id] || []).slice(0, 3);
  const priced = (productsBy[b.page_id] || []).map(p => p.price).filter(p => p != null).sort((a, c) => a - c);
  const med = priced.length ? priced[Math.floor(priced.length / 2)] : null;
  return `<tr>
    <td><span class="b" onclick="openDetail('${b.page_id}')">${esc(b.page_name)}</span>
        <div class="d">${b.domain} · ${b.niche}</div></td>
    <td>${b.traffic_tier}${b.traffic_rank ? ` <span class="d">#${fmt(b.traffic_rank)}</span>` : ''}</td>
    <td>${spark(series)} ${fmt(b.active_ads)}
        ${delta ? `<span class="delta ${delta > 0 ? 'up' : 'down'}">${delta > 0 ? '+' : ''}${delta}</span>` : ''}</td>
    <td><span class="thumbs">${prods.map(p => p.image ? `<img src="${p.image}" alt="">` : '').join('')}</span>
        <span class="d">${(productsBy[b.page_id] || []).length || '—'}</span></td>
    <td>${b.avg_ad_life != null ? b.avg_ad_life + 'd' : '—'}</td>
    <td>${med != null ? '$' + med : '—'}</td>
    <td>${heartBtn(b.page_id)}</td>
  </tr>`;
}
function renderFollowing(el) {
  let brands = DATA.brands.filter(b => followed.has(b.page_id));
  const note = brands.length ? '' :
    `<p class="empty">You're not following anyone yet — showing all listed brands. Click ♡ on any card or row to follow.</p>`;
  if (!brands.length) brands = [...DATA.brands];
  brands.sort((x, y) => ((y[ledgerSort.key] ?? -1) - (x[ledgerSort.key] ?? -1)) * -ledgerSort.dir);
  document.getElementById('count').textContent = `${brands.length} brands`;
  const TH = [['Brand', 'page_name'], ['Traffic', 'traffic_rank'], ['Ad activity', 'active_ads'],
              ['Best sellers', ''], ['Avg ad life', 'avg_ad_life'], ['Median price', ''], ['', '']];
  el.innerHTML = note + `<table class="ledger">
    <tr>${TH.map(([t, k]) => `<th onclick="sortLedger('${k}')">${t}</th>`).join('')}</tr>
    ${brands.map(ledgerRow).join('')}
  </table>`;
}
function sortLedger(key) {
  if (!key) return;
  ledgerSort = {key, dir: ledgerSort.key === key ? -ledgerSort.dir : -1};
  render();
}

// ---- swipe files ---------------------------------------------------------------
let currentFile = null;
function renderSwipes(el) {
  const names = Object.keys(swipes);
  document.getElementById('count').textContent = `${names.length} files`;
  if (!names.length) { el.innerHTML = '<p class="empty">No swipe files yet — hit ＋ Save on any ad in Explore.</p>'; return; }
  if (!currentFile || !swipes[currentFile]) currentFile = names[0];
  const ads = swipes[currentFile].map(id => ADS.find(a => a.archive_id === id)).filter(Boolean);
  el.innerHTML = `<div style="padding: 14px 28px 0; display: flex; gap: 8px; align-items: center;">
      <span class="chip"><select onchange="currentFile=this.value; render()">
        ${names.map(n => `<option ${n === currentFile ? 'selected' : ''}>${esc(n)}</option>`).join('')}
      </select></span>
      <span class="sub">${ads.length} saved</span>
      <button class="btn" onclick="delSwipeFile()">Delete file</button>
    </div>
    <div class="grid">${ads.map(a => adCard(a, currentFile)).join('')}</div>`;
}
function removeSwipe(file, adId) {
  swipes[file] = swipes[file].filter(id => id !== adId);
  saveSwipes(); render();
}
function delSwipeFile() {
  if (currentFile && confirm(`Delete swipe file "${currentFile}"?`)) {
    delete swipes[currentFile]; currentFile = null; saveSwipes(); render();
  }
}

// ---- brand detail ----------------------------------------------------------------
function mixPanel(title, rows) {
  if (!rows.length) return '';
  const max = rows[0].pct || 1;
  return `<div class="panel"><h3>${title}</h3>` + rows.map(r => `
    <div class="mixrow"><span>${r.label.replaceAll('_', ' ')}</span>
      <span class="mixbar"><i style="width:${Math.max(4, 100 * r.pct / max)}%"></i></span>
      <span class="n">${r.count} · ${r.pct}%</span></div>`).join('') + '</div>';
}
function computeMix(ads, field) {
  const counts = {};
  for (const a of ads) { const v = a[field]; if (v && v !== 'unknown' && v !== 'none') counts[v] = (counts[v] || 0) + 1; }
  const total = Object.values(counts).reduce((s, n) => s + n, 0);
  return Object.entries(counts).sort((x, y) => y[1] - x[1])
    .map(([label, count]) => ({label, count, pct: Math.round(100 * count / total)}));
}
function openDetail(pid) {
  const b = brandById[pid];
  const ads = ADS.filter(a => a.page_id === pid).sort((x, y) => (y.eu_reach || 0) - (x.eu_reach || 0));
  const prods = productsBy[pid] || [];
  const snaps = snapsBy[pid] || [];
  const dates = prods.map(p => p.created_at).filter(Boolean).sort();
  document.getElementById('sheet').innerHTML = `
    <div class="sheet-h">
      <span class="avatar" style="width:40px;height:40px;font-size:16px">${initials(b.page_name)}</span>
      <div><h2>${esc(b.page_name)}</h2>
        <span class="d"><a href="https://${b.domain}" target="_blank">${b.domain}</a> · ${b.niche}
        ${b.is_shopify ? '· Shopify' : ''} ${b.is_subscription ? '· subscription' : ''}</span></div>
      <span style="margin-left:auto">${heartBtn(pid)}</span>
      <button class="btn" onclick="document.getElementById('detail').classList.remove('open')">✕ Close</button>
    </div>
    <div class="tiles">
      <div class="tile"><span class="k">Active ads</span><div class="v">${fmt(b.active_ads)}</div><span class="s">${fmt(b.total_ads)} all-time</span></div>
      <div class="tile"><span class="k">New ads · 30d</span><div class="v">${fmt(b.new_ads_30d)}</div><span class="s">launch velocity</span></div>
      <div class="tile"><span class="k">EU reach</span><div class="v">${fmt(b.total_eu_reach)}</div><span class="s">spend proxy</span></div>
      <div class="tile"><span class="k">Brand age</span><div class="v">${b.first_ad_date || '—'}</div><span class="s">oldest detected ad</span></div>
      <div class="tile"><span class="k">Median price</span><div class="v">${b.median_price != null ? '$' + b.median_price : '—'}</div><span class="s">${prods.length} products</span></div>
      <div class="tile"><span class="k">Avg ad life</span><div class="v">${b.avg_ad_life != null ? b.avg_ad_life + 'd' : '—'}</div><span class="s">days live</span></div>
      <div class="tile"><span class="k">Traffic</span><div class="v">${b.traffic_tier}</div><span class="s">${b.traffic_rank ? 'rank #' + fmt(b.traffic_rank) : 'Tranco unranked'}</span></div>
      <div class="tile"><span class="k">Ad activity</span><div class="v">${spark(snaps.map(s => s.active_ads), 120, 30)}</div><span class="s">active ads per run</span></div>
    </div>
    <div class="cols">
      ${mixPanel('Awareness mix', computeMix(ads, 'awareness_level'))}
      ${mixPanel('Creative format mix', computeMix(ads, 'visual_treatment'))}
      ${mixPanel('Offer mix', computeMix(ads, 'offer_type'))}
      ${dates.length ? `<div class="panel"><h3>Catalog freshness</h3>
        <div class="mixrow"><span>Newest product</span><span></span><span class="n">${dates[dates.length - 1]}</span></div>
        <div class="mixrow"><span>Oldest product</span><span></span><span class="n">${dates[0]}</span></div></div>` : ''}
    </div>
    ${prods.length ? `<h3 style="margin:20px 0 0;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)">Bestsellers (catalogue order)</h3>
      <div class="best">${prods.slice(0, 8).map(p => `<div class="prod">
        ${p.image ? `<img src="${p.image}" alt="">` : '<div class="noimg">no image</div>'}
        <div class="t">${esc(p.title)}</div><div class="p">${p.price != null ? '$' + p.price : ''}</div>
      </div>`).join('')}</div>` : ''}
    <h3 style="margin:20px 0 0;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)">Top ads by reach</h3>
    <div class="grid" style="padding:14px 0 0;column-width:280px">${ads.slice(0, 9).map(a => adCard(a)).join('')}</div>`;
  document.getElementById('detail').classList.add('open');
}

// ---- router --------------------------------------------------------------------
let view = 'explore';
document.querySelectorAll('nav a').forEach(a => a.onclick = () => {
  view = a.dataset.view;
  document.querySelectorAll('nav a').forEach(x => x.classList.toggle('on', x === a));
  bar.style.display = view === 'explore' ? '' : 'none';
  render();
});
function render() {
  const el = document.getElementById('view');
  if (view === 'explore') renderExplore(el);
  else if (view === 'following') renderFollowing(el);
  else renderSwipes(el);
}
render();
</script></body></html>
"""


def render_dashboard(db: Database, run_date: str) -> str:
    from datetime import date

    from .analytics import avg_ad_life_days, median_price

    brands = db.brands(status="listed")
    ads, products, snapshots = [], [], []
    today = date.fromisoformat(run_date)
    for b in brands:
        brand_ads = db.ads_for_brand(b["page_id"], top_n=25)
        brand_products = db.products_for_brand(b["page_id"], top_n=12)
        b["median_price"] = median_price(brand_products)
        b["avg_ad_life"] = avg_ad_life_days(brand_ads, today)
        ads += brand_ads
        products += brand_products
        snapshots += db.snapshots_for_brand(b["page_id"])
    payload = json.dumps(
        {"brands": brands, "ads": ads, "products": products,
         "snapshots": snapshots, "run_date": run_date},
        ensure_ascii=False,
    )
    return _TEMPLATE.replace("__DATA__", payload)
