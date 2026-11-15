// LocaleOS front end. Plain JavaScript, no build step. Talks to server.py.

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
};
const pct = (x) => (x == null ? "n/a" : `${Math.round(x * 100)}%`);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

const EXAMPLE = {
  text: [
    "Welcome to Maple & Co!",
    "Free shipping on orders over $50.",
    "Your order number 48213 will arrive in 3 to 5 business days.",
    "You can return any item within 30 days for a full refund.",
    "Take 1 tablet twice a day with food.",
    "Break a leg at your interview tomorrow!",
  ].join("\n"),
  glossary: "Maple & Co",
};

const BAND = {
  review: { label: "Needs review", icon: "M8 1.8 14.6 13.4H1.4Z M8 6.2v3.4 M8 11.4v.2" },
  check: { label: "Worth a check", icon: "M1.6 8S4 3.6 8 3.6 14.4 8 14.4 8 12 12.4 8 12.4 1.6 8 1.6 8Z M8 6.4a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2" },
  clear: { label: "Looks fine", icon: "M3 8.4l3.2 3.2L13 4.6" },
};

const state = { status: null, last: null, onlyFlagged: false };

async function api(path, body) {
  const res = await fetch(path, body ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  } : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || "Something went wrong."), { data });
  return data;
}

// ── tabs ──────────────────────────────────────────────────────────────────

const tabs = [...document.querySelectorAll('[role="tab"]')];
function showTab(tab, focus = false) {
  tabs.forEach((t) => {
    const on = t === tab;
    t.setAttribute("aria-selected", on);
    t.tabIndex = on ? 0 : -1;
    $(t.getAttribute("aria-controls")).hidden = !on;
  });
  if (focus) tab.focus();
  history.replaceState(null, "", `#${tab.id.replace("tab-", "")}`);
  if (tab.id === "tab-evidence") loadEvidence();
  window.scrollTo(0, 0);
}
tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => showTab(tab));
  tab.addEventListener("keydown", (e) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (step) showTab(tabs[(i + step + tabs.length) % tabs.length], true);
  });
});

// ── composer ──────────────────────────────────────────────────────────────

function renderLanguages() {
  const row = el("div", "chips");
  for (const l of state.status.languages) {
    const label = el("label", "chip");
    const input = el("input");
    input.type = "checkbox"; input.value = l.name; input.checked = true;
    const span = el("span");
    span.append(el("b", null, l.native), el("small", null, l.name));
    label.append(input, span);
    row.append(label);
  }
  $("langs").append(row);
}

const chosenLanguages = () => [...document.querySelectorAll("#langs input:checked")].map((i) => i.value);

function loadExample() {
  $("source").value = EXAMPLE.text;
  $("glossary").value = EXAMPLE.glossary;
}
$("example").addEventListener("click", loadExample);

function showNotice(title, body) {
  $("notice").replaceChildren(el("h2", null, title), el("p", null, body));
  $("notice").hidden = false;
}

function setBanner(id, standin, trained) {
  const b = $(id);
  if (standin) {
    b.replaceChildren(el("strong", null, "Stand-in models. "),
      "Nothing on this page is a real translation or a real result. This mode only tests that the app works. Run the notebook in Colab for the real thing.");
  } else if (trained === false) {
    b.replaceChildren(el("strong", null, "The flagger is not trained yet. "),
      "Marks below use a rough rule of thumb. Run evaluate_qe.py to train it on real data.");
  }
  b.hidden = !(standin || trained === false);
}

$("go").addEventListener("click", async () => {
  const text = $("source").value;
  const languages = chosenLanguages();
  $("notice").hidden = true;
  if (!text.trim()) { showNotice("Paste some English text first", "One sentence or label per line works best."); return; }
  if (!languages.length) { showNotice("Pick at least one language", "Choose the languages you want to publish in."); return; }
  const btn = $("go");
  btn.disabled = true; btn.textContent = "Translating…";
  $("result").hidden = true; $("loading").hidden = false;
  $("go-hint").textContent = state.status.models.state === "loadable"
    ? "The first run downloads the models, which can take a few minutes." : "";
  try {
    const r = await api("/api/review", {
      text, languages, glossary: $("glossary").value.split(",").map((s) => s.trim()).filter(Boolean),
    });
    state.last = r;
    setBanner("banner", r.standin, r.trained);
    renderResult(true);
  } catch (e) {
    showNotice("The text couldn't be translated", `${e.message} ${e.data?.recovery || "Try again in a moment."}`);
  } finally {
    btn.disabled = false; btn.textContent = "Translate and check";
    $("loading").hidden = true; $("go-hint").textContent = "";
  }
});

// ── results ───────────────────────────────────────────────────────────────

function pill(band) {
  const p = el("span", `pill ${band}`);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 16 16"); svg.setAttribute("width", "13"); svg.setAttribute("height", "13");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", BAND[band].icon); path.setAttribute("fill", "none"); path.setAttribute("stroke", "currentColor");
  path.setAttribute("stroke-width", "1.7"); path.setAttribute("stroke-linecap", "round"); path.setAttribute("stroke-linejoin", "round");
  svg.append(path);
  p.append(svg, BAND[band].label);
  return p;
}

function renderResult(animate) {
  const r = state.last;
  const { review, check, clear } = r.counts;
  const total = review + check + clear;

  const h = $("headline");
  h.replaceChildren();
  if (review + check === 0) {
    h.append(`All ${total} translations look fine.`);
  } else {
    if (review) h.append(el("span", "risk", `${plural(review, "translation needs", "translations need")} a human.`), " ");
    if (check) h.append(`${review ? plural(check, "more is", "more are") : plural(check, "translation is", "translations are")} worth a quick check.`);
  }
  $("subline").textContent = `${total} translations checked. Open any line to see why it was marked, and what it says when translated back into English.`;

  const info = Object.fromEntries(state.status.languages.map((l) => [l.name, l]));
  const blocks = [];
  r.segments.forEach((seg, i) => {
    const items = seg.items.filter((it) => !state.onlyFlagged || it.band !== "clear");
    if (!items.length) return;
    const block = el("div", "segment");
    block.style.setProperty("--i", Math.min(i, 12));
    block.append(el("p", "src", seg.source));
    for (const it of items) {
      const d = el("details", `item is-${it.band}`);
      d.open = it.band === "review";
      const s = el("summary");
      const tr = el("span", "tr", it.translation);
      tr.dir = info[it.language].rtl ? "rtl" : "ltr";
      s.append(el("span", "lang", info[it.language].native), tr, pill(it.band));
      const why = el("div", "why");
      if (it.reasons.length) {
        const ul = el("ul");
        it.reasons.forEach((reason) => ul.append(el("li", null, reason)));
        why.append(ul);
      } else why.append("No warning signs found.");
      const back = el("p", "back");
      back.append(el("b", null, "Translated back into English"), it.back);
      why.append(back, el("p", "score", `Review score ${it.score.toFixed(2)} out of 1`));
      d.append(s, why);
      block.append(d);
    }
    blocks.push(block);
  });
  if (!blocks.length) blocks.push(el("p", "sub", "Nothing needs attention."));
  $("segments").replaceChildren(...blocks);
  $("result").classList.toggle("reveal", animate);
  $("result").hidden = false;
  $("export").disabled = review + check === 0;
}

function setFilter(only) {
  state.onlyFlagged = only;
  $("show-all").setAttribute("aria-pressed", !only);
  $("show-flagged").setAttribute("aria-pressed", only);
  renderResult(false);
}
$("show-all").addEventListener("click", () => setFilter(false));
$("show-flagged").addEventListener("click", () => setFilter(true));

$("export").addEventListener("click", () => {
  const q = (s) => `"${String(s).replace(/"/g, '""')}"`;
  const rows = [["english", "language", "translation", "mark", "reasons", "translated back into english"].map(q).join(",")];
  for (const seg of state.last.segments) {
    for (const it of seg.items) {
      if (it.band === "clear") continue;
      rows.push([seg.source, it.language, it.translation, BAND[it.band].label, it.reasons.join(" "), it.back].map(q).join(","));
    }
  }
  const url = URL.createObjectURL(new Blob(["﻿" + rows.join("\n")], { type: "text/csv;charset=utf-8" }));
  const a = el("a"); a.href = url; a.download = "localeos-review-list.csv";
  document.body.append(a); a.click(); a.remove(); URL.revokeObjectURL(url);
});

// ── evidence ──────────────────────────────────────────────────────────────

let evidenceLoaded = false;
async function loadEvidence() {
  if (evidenceLoaded) return;
  let r;
  try { r = await api("/api/evidence"); } catch (e) {
    $("ev-empty").replaceChildren(el("h2", null, "The results couldn't be loaded"), el("p", null, `${e.message} Reload the page to try again.`));
    $("ev-empty").hidden = false;
    return;
  }
  evidenceLoaded = true;
  if (!r.available) {
    $("ev-lead").textContent = "This page fills in once the test has been run.";
    $("ev-empty").replaceChildren(el("h2", null, "No test results yet"),
      el("p", null, "Run build_dataset.py and then evaluate_qe.py (steps 2 and 3 of the Colab notebook). The results appear here: how many bad translations the flagger catches, per language, against three simpler methods."));
    $("ev-empty").hidden = false;
    return;
  }
  setBanner("ev-banner", r.standin, true);
  const ours = r.overall["LocaleOS flagger"], conf = r.overall["Translator confidence alone"];
  $("ev-title").textContent = `Reviewing the 20% we flag catches ${pct(ours.caught_at_20)} of the bad translations`;
  $("ev-lead").textContent = `Picking 20% at random would catch 20%. Using only the translator's own confidence catches ${pct(conf.caught_at_20)}. Tested on ${r.test_rows.toLocaleString("en-US")} translations the flagger never saw, across ${Object.keys(r.languages).length} languages.`;
  drawCurve(r);
  languageTable(r);
  humanTable(r);
  gallery(r);
  $("ev-body").hidden = false;
}

function drawCurve(r) {
  const W = 720, H = 360, L = 52, R = 190, T = 18, B = 52;
  const X = (b) => L + ((b - r.budgets[0]) / (r.budgets.at(-1) - r.budgets[0])) * (W - L - R);
  const Y = (v) => T + (1 - v) * (H - T - B);
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const add = (parent, tag, attrs, text) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (text !== undefined) n.textContent = text;
    parent.append(n);
    return n;
  };
  for (const v of [0, 0.25, 0.5, 0.75, 1]) {
    add(svg, "line", { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: "grid" });
    add(svg, "text", { x: L - 10, y: Y(v) + 4, "text-anchor": "end" }, pct(v));
  }
  r.budgets.forEach((b) => add(svg, "text", { x: X(b), y: H - B + 22, "text-anchor": "middle" }, pct(b)));
  add(svg, "text", { x: L, y: H - 6 }, "Share of translations a human reviews");
  const names = Object.keys(r.curve);
  const ends = names.map((n) => ({ n, y: Y(r.curve[n].at(-1)) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 17) ends[i].y = ends[i - 1].y + 17;
  const endY = Object.fromEntries(ends.map((e) => [e.n, e.y]));
  for (const n of [...names.filter((x) => x !== "LocaleOS flagger"), "LocaleOS flagger"]) {
    const sel = n === "LocaleOS flagger";
    const g = add(svg, "g", { class: sel ? "is-sel" : "" });
    const pts = r.budgets.map((b, i) => [X(b), Y(r.curve[n][i])]);
    add(g, "polyline", { class: `ln${n === "Random" ? " dash" : ""}`, points: pts.map((p) => p.join(",")).join(" ") });
    pts.forEach(([x, y], i) => {
      add(g, "circle", { class: "dot", cx: x, cy: y, r: sel ? 4.5 : 2.5 });
      if (sel && i < pts.length - 1) add(g, "text", { class: "val", x, y: y - 11, "text-anchor": "middle" }, pct(r.curve[n][i]));
    });
    add(g, "text", { class: "lbl", x: pts.at(-1)[0] + 14, y: endY[n] + 4.5 }, n === "Random" ? "Picking at random" : n);
  }
  $("chart").replaceChildren(svg);
  $("chart").setAttribute("aria-label", "Line chart: share of bad translations caught against share of translations reviewed, for the LocaleOS flagger and three simpler methods.");
  $("chart-caption").textContent = "Share of the bad translations a human would see, if they review only the translations each method ranks as riskiest. Higher is better.";
}

function table(id, head, rows) {
  const t = $(id);
  t.replaceChildren();
  const thead = el("thead"), hr = el("tr");
  head.forEach((h) => { const th = el("th", null, h); th.scope = "col"; hr.append(th); });
  thead.append(hr);
  const tbody = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    row.forEach((c, i) => { const cell = el(i ? "td" : "th", i === 1 && row.sel ? "is-sel" : null, c); if (!i) cell.scope = "row"; tr.append(cell); });
    tbody.append(tr);
  }
  t.append(thead, tbody);
}

function languageTable(r) {
  const rows = Object.entries(r.languages).map(([lang, m]) => Object.assign([
    lang, pct(m["LocaleOS flagger"].caught_at_20), pct(m["Translator confidence alone"].caught_at_20),
    pct(m["Longest sentences first"].caught_at_20), pct(r.unseen_language?.[lang]?.caught_at_20), String(m.n),
  ], { sel: true }));
  table("lang-table", ["Language", "LocaleOS flagger", "Confidence alone", "Longest first", "Flagger, never trained on this language", "Tested"], rows);
  const cap = el("caption", null, "Bad translations caught when a human reviews the riskiest 20%");
  $("lang-table").prepend(cap);
}

function humanTable(r) {
  if (!r.human) return;
  const rows = Object.entries(r.human).map(([lang, h]) => [lang, String(h.rated), String(h.human_bad), pct(h.agreement), pct(h.bad_caught), pct(h.flags_correct)]);
  table("human-table", ["Language", "Rated", "Speaker said bad", "Flagger agreed", "Bad ones it flagged", "Flags that were right"], rows);
  $("human-block").hidden = false;
}

function gallery(r) {
  const box = $("gallery");
  box.replaceChildren();
  for (const [lang, f] of Object.entries(r.failures)) {
    const d = el("details");
    d.append(el("summary", null, `${lang}: its ${f.missed.length + f.false_alarms.length} worst calls`));
    for (const [title, cases] of [["Bad translations it scored safest", f.missed], ["Good translations it scored riskiest", f.false_alarms]]) {
      d.append(el("h3", null, title));
      for (const c of cases) {
        const box2 = el("div", "case");
        for (const [k, v] of [["English", c.source], ["Machine translation", c.translation], ["Professional translation", c.reference], ["Machine translation, back into English", c.back]]) {
          box2.append(el("b", null, k), el("span", null, v));
        }
        box2.append(el("b", null, `Review score ${c.score.toFixed(2)}`));
        d.append(box2);
      }
    }
    box.append(d);
  }
}

// ── start ─────────────────────────────────────────────────────────────────

(async function start() {
  try {
    state.status = await api("/api/status");
  } catch (e) {
    showNotice("LocaleOS couldn't reach its server", "Start it with “python server.py”, then reload this page.");
    return;
  }
  renderLanguages();
  loadExample();
  setBanner("banner", state.status.standin, state.status.flagger_trained);
  if (state.status.models.state === "unavailable") {
    showNotice("The translation model can't run on this machine",
      `${state.status.models.reason} Open LocaleOS_Colab.ipynb in Google Colab with a T4 GPU to translate. The evidence page works everywhere once the test has been run.`);
    $("go").disabled = true;
  }
  const wanted = tabs.find((t) => t.id === `tab-${location.hash.slice(1)}`);
  if (wanted) showTab(wanted);
})();
