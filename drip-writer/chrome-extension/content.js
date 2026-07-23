// Drip Writer — content script.
// Injected when you click the toolbar icon. Builds a floating panel (in a
// shadow root so the page's CSS can't touch it) and types your text into
// whatever editable field you last clicked, like a human would.
(function () {
  "use strict";

  // Toggle if already injected.
  if (window.__dripWriter) { window.__dripWriter.toggle(); return; }

  // ---- track the page field you want to type into --------------------------
  const HOST_ID = "__drip-writer-host";
  let lastEditable = null;

  function isEditable(el) {
    if (!el || el.nodeType !== 1) return false;
    const tag = el.tagName;
    if (tag === "TEXTAREA") return !el.disabled && !el.readOnly;
    if (tag === "INPUT") {
      const t = (el.type || "text").toLowerCase();
      const ok = ["text","search","url","email","tel","password","number",""].includes(t);
      return ok && !el.disabled && !el.readOnly;
    }
    return !!el.isContentEditable;
  }

  // Remember the last real editable element the user focused, ignoring our panel.
  document.addEventListener("focusin", (e) => {
    const el = e.target;
    if (host && (el === host || host.contains(el))) return; // our own panel
    if (isEditable(el)) lastEditable = el;
  }, true);

  // ---- typing into a real field --------------------------------------------
  function insertText(el, ch) {
    el.focus();
    let ok = false;
    try { ok = document.execCommand("insertText", false, ch); } catch (e) {}
    if (ok) return;
    // Fallback for inputs/textareas where execCommand is unavailable.
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
      const start = el.selectionStart ?? el.value.length;
      const end = el.selectionEnd ?? el.value.length;
      const nv = el.value.slice(0, start) + ch + el.value.slice(end);
      setter.call(el, nv);
      const pos = start + ch.length;
      try { el.selectionStart = el.selectionEnd = pos; } catch (e) {}
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }

  function deleteBack(el) {
    el.focus();
    let ok = false;
    try { ok = document.execCommand("delete", false); } catch (e) {}
    if (ok) return;
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
      const pos = el.selectionStart ?? el.value.length;
      if (pos <= 0) return;
      const nv = el.value.slice(0, pos - 1) + el.value.slice(pos);
      setter.call(el, nv);
      try { el.selectionStart = el.selectionEnd = pos - 1; } catch (e) {}
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }

  // ---- human-typing engine -------------------------------------------------
  const NEIGH = {
    q:"wa",w:"qeas",e:"wrsd",r:"etdf",t:"ryfg",y:"tugh",u:"yihj",i:"uojk",o:"ipkl",p:"ol",
    a:"qwsz",s:"awedxz",d:"serfcx",f:"drtgvc",g:"ftyhbv",h:"gyujnb",j:"huikmn",k:"jiolm",l:"kop",
    z:"asx",x:"zsdc",c:"xdfv",v:"cfgb",b:"vghn",n:"bhjm",m:"njk",
    "1":"2","2":"13","3":"24","4":"35","5":"46","6":"57","7":"68","8":"79","9":"80","0":"9"
  };
  function wrongChar(ch) {
    const lower = ch.toLowerCase(), opts = NEIGH[lower];
    if (!opts) return null;
    const w = opts[Math.floor(Math.random() * opts.length)];
    return ch !== lower ? w.toUpperCase() : w;
  }
  function randn() { let s = 0; for (let i = 0; i < 3; i++) s += Math.random(); return (s / 3 - 0.5) * 2; }
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  let running = false, paused = false, cancelTok = 0;
  let typoCount = 0, doneChars = 0, totalChars = 0;

  function cfg() {
    return {
      wpm: +$("wpm").value,
      err: +$("err").value / 100,
      vary: +$("vary").value / 100,
      punct: $("tPunct").checked,
      think: $("tThink").checked,
      fix: $("tCorrect").checked
    };
  }
  const baseDelay = (wpm) => 60000 / (Math.max(5, wpm) * 5);
  const jitter = (ms, v) => Math.max(8, ms * (1 + randn() * v));

  async function wait(ms, tok) {
    let el = 0; const step = Math.min(ms, 40);
    while (el < ms) {
      if (tok !== cancelTok) throw "cancel";
      if (!paused) { await sleep(step); el += step; } else { await sleep(40); }
    }
    if (tok !== cancelTok) throw "cancel";
  }

  async function typeError(field, correct, c, tok) {
    const style = Math.random(), bd = baseDelay(c.wpm);
    if (style < 0.6) {
      const w = wrongChar(correct); if (w === null) return false;
      insertText(field, w); typoCount++; stats();
      if (!c.fix) return true;
      await wait(jitter(bd * (1.6 + Math.random() * 2), c.vary), tok);
      deleteBack(field);
      await wait(jitter(bd * 0.7, c.vary), tok);
      insertText(field, correct);
      return true;
    }
    if (style < 0.8) {
      insertText(field, correct); insertText(field, correct); typoCount++; stats();
      if (!c.fix) { deleteBack(field); return true; }
      await wait(jitter(bd * (1.4 + Math.random() * 1.5), c.vary), tok);
      deleteBack(field);
      return true;
    }
    const w = wrongChar(correct); if (w === null) return false;
    insertText(field, w); typoCount++; stats();
    if (!c.fix) { insertText(field, correct); return true; }
    await wait(jitter(bd * (1.5 + Math.random() * 1.6), c.vary), tok);
    deleteBack(field);
    await wait(jitter(bd * 0.7, c.vary), tok);
    insertText(field, correct);
    return true;
  }

  async function run() {
    const text = $("src").value;
    if (!text) { status("Paste some text first."); return; }
    const field = lastEditable;
    if (!isEditable(field)) {
      status("Click into a text box on the page first, then press Start.");
      return;
    }
    const tok = ++cancelTok;
    running = true; paused = false; typoCount = 0; doneChars = 0; totalChars = text.length;
    setButtons(); status("Typing…");
    const c = cfg();
    try {
      for (let i = 0; i < text.length; i++) {
        const ch = text[i], isLD = /[a-z0-9]/i.test(ch);
        if (isLD && Math.random() < c.err) {
          if (await typeError(field, ch, c, tok)) {
            doneChars++; stats();
            await wait(jitter(baseDelay(c.wpm), c.vary), tok);
            continue;
          }
        }
        insertText(field, ch); doneChars++; stats();
        let d = baseDelay(c.wpm);
        if (ch === " ") d *= 1.15;
        if (c.punct) {
          if (/[.!?]/.test(ch)) d *= 6 + Math.random() * 6;
          else if (/[,;:]/.test(ch)) d *= 2.5 + Math.random() * 2;
          else if (ch === "\n") d *= 4;
        }
        await wait(jitter(d, c.vary), tok);
        if (c.think && ch === " " && Math.random() < 0.03) {
          await wait(jitter(baseDelay(c.wpm) * (6 + Math.random() * 10), c.vary), tok);
        }
      }
      running = false; paused = false; setButtons(); status("Done ✓");
    } catch (e) { /* cancelled */ }
  }

  // ---- UI (shadow DOM) -----------------------------------------------------
  let root = null, host = null;
  const $ = (id) => root.getElementById(id);

  function stats() {
    $("stErr").textContent = typoCount;
    $("stProg").textContent = totalChars ? Math.round(doneChars / totalChars * 100) + "%" : "0%";
  }
  function status(msg) { $("status").textContent = msg; }
  function setButtons() {
    $("start").textContent = running ? "Restart" : "Start typing";
    $("pause").disabled = !running;
    $("pause").textContent = paused ? "Resume" : "Pause";
    $("stop").disabled = !running;
  }

  function build() {
    host = document.createElement("div");
    host.id = HOST_ID;
    host.style.cssText = "all:initial;position:fixed;top:16px;right:16px;z-index:2147483647;";
    root = host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host{ all:initial; }
        *{ box-sizing:border-box; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
        .panel{ width:320px; background:#161a22; color:#e8eaf1; border:1px solid #2a303c;
          border-radius:14px; box-shadow:0 12px 40px rgba(0,0,0,.45); overflow:hidden; font-size:13px; }
        .bar{ display:flex; align-items:center; justify-content:space-between; padding:10px 12px;
          background:#1c212b; cursor:move; user-select:none; border-bottom:1px solid #2a303c; }
        .bar .title{ font-weight:700; letter-spacing:.02em; }
        .bar .title small{ color:#5b9dff; font-family:ui-monospace,Menlo,monospace; font-size:10px; letter-spacing:.2em; margin-left:6px; }
        .x{ cursor:pointer; color:#8b93a4; font-size:16px; line-height:1; padding:2px 6px; border-radius:6px; }
        .x:hover{ background:#2a303c; color:#e8eaf1; }
        .body{ padding:12px; display:flex; flex-direction:column; gap:11px; }
        textarea{ width:100%; min-height:74px; resize:vertical; background:#1c212b; color:#e8eaf1;
          border:1px solid #2a303c; border-radius:9px; padding:9px 10px; font-size:13px; line-height:1.5; }
        textarea:focus{ outline:2px solid #5b9dff; outline-offset:1px; border-color:transparent; }
        .grid{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }
        .ctl{ display:flex; flex-direction:column; gap:4px; }
        .ctl .top{ display:flex; justify-content:space-between; align-items:baseline; }
        .ctl label{ font-size:10px; text-transform:uppercase; letter-spacing:.1em; color:#8b93a4; font-weight:600; }
        .ctl b{ font-family:ui-monospace,Menlo,monospace; font-size:12px; }
        input[type=range]{ width:100%; accent-color:#5b9dff; }
        .togs{ display:flex; flex-wrap:wrap; gap:6px; }
        .tog{ display:inline-flex; align-items:center; gap:6px; font-size:11.5px; background:#1c212b;
          border:1px solid #2a303c; padding:5px 8px; border-radius:999px; cursor:pointer; }
        .tog input{ accent-color:#5b9dff; }
        .btns{ display:flex; gap:7px; flex-wrap:wrap; }
        button{ flex:1; min-width:84px; border:1px solid #2a303c; background:#1c212b; color:#e8eaf1;
          padding:9px 10px; border-radius:9px; font-size:13px; font-weight:600; cursor:pointer; }
        button:hover:not(:disabled){ border-color:#5b9dff; }
        button:disabled{ opacity:.4; cursor:not-allowed; }
        button.primary{ background:#5b9dff; border-color:#5b9dff; color:#0e1014; }
        .foot{ display:flex; justify-content:space-between; align-items:center; color:#8b93a4; font-size:11px; }
        .foot .st{ color:#5fd39a; font-family:ui-monospace,Menlo,monospace; }
      </style>
      <div class="panel">
        <div class="bar" id="bar">
          <div class="title">Drip Writer <small>TYPES FOR YOU</small></div>
          <div class="x" id="close" title="Close">✕</div>
        </div>
        <div class="body">
          <textarea id="src" placeholder="Paste the text to type into the page…"></textarea>
          <div class="grid">
            <div class="ctl"><div class="top"><label>Speed</label><b><span id="wpmV">55</span> wpm</b></div><input id="wpm" type="range" min="15" max="140" value="55"></div>
            <div class="ctl"><div class="top"><label>Typos</label><b><span id="errV">4</span>%</b></div><input id="err" type="range" min="0" max="20" value="4"></div>
          </div>
          <div class="ctl"><div class="top"><label>Rhythm variance</label><b><span id="varV">35</span>%</b></div><input id="vary" type="range" min="0" max="80" value="35"></div>
          <div class="togs">
            <label class="tog"><input type="checkbox" id="tPunct" checked> Punctuation pauses</label>
            <label class="tog"><input type="checkbox" id="tThink" checked> Thinking pauses</label>
            <label class="tog"><input type="checkbox" id="tCorrect" checked> Fix typos</label>
          </div>
          <div class="btns">
            <button class="primary" id="start">Start typing</button>
            <button id="pause" disabled>Pause</button>
            <button id="stop" disabled>Stop</button>
          </div>
          <div class="foot">
            <span class="st" id="status">Click a text box, then Start.</span>
            <span>Typos <b id="stErr">0</b> · <b id="stProg">0%</b></span>
          </div>
        </div>
      </div>`;
    document.documentElement.appendChild(host);

    // wire controls
    $("wpm").oninput = () => $("wpmV").textContent = $("wpm").value;
    $("err").oninput = () => $("errV").textContent = $("err").value;
    $("vary").oninput = () => $("varV").textContent = $("vary").value;
    $("start").onclick = () => run();
    $("pause").onclick = () => {
      if (!running) return;
      paused = !paused; setButtons();
      status(paused ? "Paused." : "Typing…");
    };
    $("stop").onclick = () => {
      cancelTok++; running = false; paused = false; setButtons(); status("Stopped.");
    };
    $("close").onclick = () => api.toggle();

    // drag by the title bar
    const bar = $("bar");
    let dx = 0, dy = 0, dragging = false;
    bar.addEventListener("mousedown", (e) => {
      dragging = true;
      const r = host.getBoundingClientRect();
      dx = e.clientX - r.left; dy = e.clientY - r.top;
      host.style.right = "auto";
      e.preventDefault();
    });
    window.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      host.style.left = Math.max(0, e.clientX - dx) + "px";
      host.style.top = Math.max(0, e.clientY - dy) + "px";
    });
    window.addEventListener("mouseup", () => { dragging = false; });
  }

  const api = {
    toggle() {
      if (!host) { build(); return; }
      host.style.display = host.style.display === "none" ? "block" : "none";
    }
  };
  window.__dripWriter = api;
  build();
})();
