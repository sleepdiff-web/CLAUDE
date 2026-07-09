"""Self-contained HTML dashboard: the filterable brand + ad browser.

Double-click the file to open — no server, all data embedded as JSON, filters
run client-side (niche, awareness level, subs vs one-time, authority figure,
traffic tier — the spec's headline filters).
"""
from __future__ import annotations

import json

from .db import Database

_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>DTCScout — pre-vetted brand database</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.5 -apple-system, system-ui, sans-serif; margin: 24px; max-width: 1200px; }
  h1 { font-size: 20px; } .muted { opacity: .65; }
  .filters { display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }
  .filters label { display: flex; flex-direction: column; font-size: 12px; gap: 2px; }
  select { padding: 4px 6px; }
  .brand { border: 1px solid rgba(128,128,128,.35); border-radius: 10px; padding: 14px 16px; margin: 10px 0; }
  .brand h2 { font-size: 16px; margin: 0 0 4px; }
  .stats { display: flex; gap: 18px; flex-wrap: wrap; font-size: 12px; margin: 6px 0; }
  .stats b { font-size: 15px; display: block; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }
  th, td { text-align: left; padding: 4px 8px; border-top: 1px solid rgba(128,128,128,.25); vertical-align: top; }
  .tag { display: inline-block; padding: 1px 7px; border-radius: 9px; background: rgba(128,128,128,.18); font-size: 11px; margin-right: 4px; }
  details summary { cursor: pointer; font-size: 13px; margin-top: 6px; }
  a { color: inherit; }
</style></head><body>
<h1>DTCScout <span class="muted">— pre-vetted fast-scaling DTC brands · run __RUN_DATE__</span></h1>
<div class="filters">
  <label>Niche <select id="f-niche"></select></label>
  <label>Awareness level <select id="f-awareness"></select></label>
  <label>Subs vs one-time <select id="f-offer"></select></label>
  <label>Authority figure <select id="f-authority"></select></label>
  <label>Traffic tier <select id="f-traffic"></select></label>
  <label>Sort brands <select id="f-sort">
    <option value="reach">EU reach (spend proxy)</option>
    <option value="new_ads">New ads (30d)</option>
    <option value="active">Active ads</option>
  </select></label>
</div>
<div id="list"></div>
<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const uniq = (rows, key) => [...new Set(rows.map(r => r[key]).filter(v => v && v !== 'unknown'))].sort();

function fillSelect(el, values) {
  el.innerHTML = '<option value="">all</option>' + values.map(v => `<option>${v}</option>`).join('');
}
fillSelect($('f-niche'), uniq(DATA.brands, 'niche'));
fillSelect($('f-awareness'), uniq(DATA.ads, 'awareness_level'));
fillSelect($('f-offer'), uniq(DATA.ads, 'offer_type'));
fillSelect($('f-authority'), uniq(DATA.ads, 'authority_figure').filter(v => v !== 'none'));
fillSelect($('f-traffic'), uniq(DATA.brands, 'traffic_tier'));

function render() {
  const f = {
    niche: $('f-niche').value, awareness: $('f-awareness').value,
    offer: $('f-offer').value, authority: $('f-authority').value,
    traffic: $('f-traffic').value, sort: $('f-sort').value,
  };
  let brands = DATA.brands.filter(b =>
    (!f.niche || b.niche === f.niche) && (!f.traffic || b.traffic_tier === f.traffic));
  const adsByBrand = {};
  for (const ad of DATA.ads) {
    if (f.awareness && ad.awareness_level !== f.awareness) continue;
    if (f.offer && ad.offer_type !== f.offer) continue;
    if (f.authority && ad.authority_figure !== f.authority) continue;
    (adsByBrand[ad.page_id] ||= []).push(ad);
  }
  // Ad-level filters narrow the brand list to brands with matching ads.
  if (f.awareness || f.offer || f.authority) brands = brands.filter(b => adsByBrand[b.page_id]);
  const keyFn = {reach: b => b.total_eu_reach, new_ads: b => b.new_ads_30d, active: b => b.active_ads}[f.sort];
  brands.sort((a, b) => keyFn(b) - keyFn(a));

  $('list').innerHTML = brands.map(b => {
    const ads = (adsByBrand[b.page_id] || []).slice(0, 15);
    const rows = ads.map(a => `<tr>
      <td>${(a.eu_reach || 0).toLocaleString()}</td>
      <td>${a.start_date}${a.stop_date ? '' : ' <span class="tag">active</span>'}</td>
      <td><span class="tag">${a.awareness_level}</span><span class="tag">${a.offer_type}</span>${a.authority_figure !== 'none' && a.authority_figure !== 'unknown' ? `<span class="tag">${a.authority_figure}</span>` : ''}</td>
      <td>${(a.link_title || '')}<div class="muted">${(a.body || '').slice(0, 180)}</div>
          ${a.snapshot_url ? `<a href="${a.snapshot_url}" target="_blank">view ad ↗</a>` : ''}</td>
    </tr>`).join('');
    return `<div class="brand">
      <h2>${b.page_name} <span class="muted">· <a href="https://${b.domain}" target="_blank">${b.domain}</a> · ${b.niche}</span></h2>
      <div>${b.is_subscription ? '<span class="tag">subscription</span>' : ''}${b.is_shopify ? '<span class="tag">shopify</span>' : ''}<span class="tag">traffic: ${b.traffic_tier}</span></div>
      <div class="stats">
        <span><b>${b.active_ads}</b>active ads</span>
        <span><b>${b.new_ads_30d}</b>new ads (30d)</span>
        <span><b>${(b.total_eu_reach || 0).toLocaleString()}</b>EU reach</span>
        <span><b>${b.first_ad_date || '—'}</b>first ad</span>
      </div>
      ${ads.length ? `<details><summary>Top ads by reach (${ads.length})</summary>
        <table><tr><th>Reach</th><th>Launched</th><th>Classification</th><th>Creative</th></tr>${rows}</table>
      </details>` : ''}
    </div>`;
  }).join('') || '<p class="muted">No brands match these filters.</p>';
}
document.querySelectorAll('select').forEach(el => el.addEventListener('change', render));
render();
</script></body></html>
"""


def render_dashboard(db: Database, run_date: str) -> str:
    brands = db.brands(status="listed")
    ads = [ad for b in brands for ad in db.ads_for_brand(b["page_id"], top_n=25)]
    payload = json.dumps({"brands": brands, "ads": ads}, ensure_ascii=False)
    return _TEMPLATE.replace("__RUN_DATE__", run_date).replace("__DATA__", payload)
