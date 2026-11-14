// LinguaBridge front end. Plain JavaScript, no build step.
// It talks to server.py through four endpoints (see the top of that file).

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
};

const QUESTIONS = {
  Spanish: "¿Cuántas veces al día debo tomar un medicamento si la receta dice «cada 8 horas»?",
  Hindi: "अगर दवा की पर्ची पर 'हर 8 घंटे' लिखा है तो मुझे दिन में कितनी बार दवा लेनी चाहिए?",
  Mandarin: "如果药方上写着“每8小时一次”，我一天应该吃几次药？",
  Arabic: "إذا كانت الوصفة تقول «كل 8 ساعات»، فكم مرة في اليوم يجب أن أتناول الدواء؟",
  Kurmanji: "Ger li ser reçeteyê \"her 8 saetan\" hatibe nivîsîn, divê ez rojê çend caran dermanê bixwim?",
};

const state = { lang: "Kurmanji", model: null, example: 0, pilot: null, status: null, renderId: 0 };

const langInfo = (name) => state.pilot.languages.find((l) => l.name === name);
const times = (x) => `${x.toFixed(1)}×`;
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

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
  if (tab.id === "tab-ask") enterAsk();
  window.scrollTo(0, 0);
}

tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => showTab(tab));
  tab.addEventListener("keydown", (e) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (step) showTab(tabs[(i + step + tabs.length) % tabs.length], true);
  });
});

// ── language chips (one shared choice, shown in all three sections) ───────

function renderChips() {
  for (const [id, allowEnglish] of [["langs-measure", true], ["langs-ask", false], ["langs-evidence", false]]) {
    const box = $(id);
    box.querySelector(".chips")?.remove();
    const row = el("div", "chips");
    for (const l of state.pilot.languages) {
      if (!allowEnglish && l.name === "English") continue;
      const label = el("label", "chip");
      const input = el("input");
      input.type = "radio";
      input.name = id;
      input.value = l.name;
      input.checked = l.name === state.lang;
      input.addEventListener("change", () => setLanguage(l.name));
      const span = el("span");
      const b = el("b", null, l.native);
      b.lang = l.name === "English" ? "en" : "";
      span.append(b, el("small", null, l.name));
      label.append(input, span);
      row.append(label);
    }
    box.append(row);
  }
}

function setLanguage(name) {
  state.lang = name;
  document.querySelectorAll(".chip input").forEach((i) => { i.checked = i.value === name; });
  $("message").value = state.pilot.sentences[name][state.example ?? 0];
  if (state.example === null) state.example = 0;
  applyDirection();
  measure(true);
  if (name !== "English") { $("question").value = QUESTIONS[name]; updateRouteHint(); resetAnswers(); }
  renderEvidence();
}

function applyDirection() {
  const dir = langInfo(state.lang).rtl ? "rtl" : "ltr";
  $("message").dir = dir;
  $("strip").dir = dir;
  $("question").dir = state.lang === "English" ? "ltr" : dir;
}

// ── measure ───────────────────────────────────────────────────────────────

function tile(tok, i) {
  const t = el("span", tok.partial ? "tok part" : "tok");
  t.style.setProperty("--i", Math.min(i, 30));
  if (tok.partial) {
    t.title = "Part of one character: this model splits a single letter into several tokens.";
    t.setAttribute("aria-label", "part of a character");
    return t;
  }
  for (const ch of tok.t) {            // show spaces, which are part of the token, as a faint dot
    if (ch === " ") t.append(el("span", "sp", "·"));
    else if (ch === "\n") t.append(el("span", "sp", "↵"));
    else t.append(ch);
  }
  return t;
}

function fillStrip(box, tokens, animate) {
  box.classList.toggle("reveal", animate);
  box.replaceChildren(...tokens.map(tile));
}

let typingTimer;
$("message").addEventListener("input", () => {
  state.example = null;
  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => measure(false), 220);
});

$("next-example").addEventListener("click", () => {
  state.example = ((state.example ?? -1) + 1) % state.pilot.sentences[state.lang].length;
  $("message").value = state.pilot.sentences[state.lang][state.example];
  measure(true);
});

async function measure(animate) {
  const id = ++state.renderId;
  const text = $("message").value;
  const total = state.pilot.sentences[state.lang].length;
  $("basis-hint").textContent = state.example === null ? "Your own text" : `Sentence ${state.example + 1} of ${total}`;

  if (!text.trim()) {
    $("headline").textContent = "Type or paste a message to price it.";
    $("subline").textContent = "";
    fillStrip($("strip"), [], false);
    $("strip-count").textContent = "";
    $("english-block").hidden = true;
    $("legend").replaceChildren();
    return;
  }

  let r;
  try {
    r = await api("/api/measure", { text, language: state.lang, model: state.model, example: state.example });
  } catch (e) {
    if (id !== state.renderId) return;
    $("headline").textContent = "That message couldn't be measured.";
    $("subline").textContent = `${e.message} Check that the server is still running, then try again.`;
    return;
  }
  if (id !== state.renderId) return;       // a newer request has already been drawn

  const n = r.count, en = r.english_count, ratio = n / en;
  const isEnglish = state.lang === "English";
  const extra = isEnglish ? 0 : Math.max(0, n - en);

  // headline
  const h = $("headline");
  h.replaceChildren();
  if (isEnglish) {
    h.append(`This message takes ${plural(n, "token")}. English is the baseline every other language is compared with.`);
  } else {
    h.append(`In ${state.lang} this message takes ${plural(n, "token")}. In English it takes ${en}. `);
    if (ratio >= 1.08) h.append(el("span", "tax", `That is ${times(ratio)} the price.`));
    else if (ratio <= 0.95) h.append(el("span", "even", "On this model it costs less than English."));
    else h.append(el("span", "even", "About the same price as English."));
  }
  $("subline").textContent = isEnglish ? `Counted on ${state.model}.`
    : r.basis === "translation"
      ? `Counted on ${state.model}, against this sentence's own English translation.`
      : `Counted on ${state.model}. The English figure is an estimate from the average we measured on 12 sentences.`;

  // strips
  fillStrip($("strip"), r.tokens, animate);
  $("strip-count").textContent = plural(n, "token");
  const tiles = [...$("strip").children];
  const paint = () => { if (id === state.renderId) tiles.forEach((t, i) => t.classList.toggle("tax", i >= en && extra > 0)); };
  if (animate && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setTimeout(paint, Math.min(tiles.length, 30) * 14 + 240);   // the extra pieces colour in after they land
  } else paint();

  $("english-block").hidden = !r.english;
  if (r.english) {
    fillStrip($("english-strip"), r.english.tokens, animate);
    $("english-count").textContent = plural(r.english.tokens.length, "token");
  }

  // legend
  const legend = [];
  if (!isEnglish) {
    const base = el("li"); base.append(el("i"), "what English pays");
    legend.push(base);
    if (extra > 0) {
      const tax = el("li"); tax.append(el("i", "tax"), `the language tax: ${plural(extra, "extra token")}`);
      legend.push(tax);
    }
  }
  if (r.tokens.some((t) => t.partial)) {
    const part = el("li"); part.append(el("i", "part"), "a fragment of one character");
    legend.push(part);
  }
  $("legend").replaceChildren(...legend);

  updateModels(r.per_model, isEnglish);
}

function renderModels() {
  const list = el("div", "model-list");
  for (const m of state.pilot.models) {
    const label = el("label", "model");
    const input = el("input");
    input.type = "radio"; input.name = "model"; input.value = m.name; input.checked = m.name === state.model;
    input.addEventListener("change", () => { state.model = m.name; measure(false); });
    const row = el("span");
    const name = el("span", "name", m.name);
    name.append(el("small", null, String(m.year)));
    const track = el("span", "track");
    track.append(el("span", "fill-en"), el("span", "fill-tax"));
    row.append(name, track, el("span", "nums"));
    label.append(input, row);
    label.dataset.model = m.name;
    list.append(label);
  }
  $("models").append(list);
}

function updateModels(perModel, isEnglish) {
  const max = Math.max(...perModel.map((m) => m.count));
  for (const m of perModel) {
    const row = document.querySelector(`.model[data-model="${CSS.escape(m.model)}"]`);
    const base = isEnglish ? m.count : Math.min(m.count, m.english_count);
    row.querySelector(".fill-en").style.width = `${(base / max) * 100}%`;
    row.querySelector(".fill-tax").style.width = `${((m.count - base) / max) * 100}%`;
    const nums = row.querySelector(".nums");
    nums.replaceChildren(el("b", null, String(m.count)), ` token${m.count === 1 ? "" : "s"}`);
    if (!isEnglish) nums.append(` · ${times(m.ratio)} English`);
  }
}

// ── ask ───────────────────────────────────────────────────────────────────

function enterAsk() {
  if (state.lang === "English") setLanguage("Kurmanji");
  if (state.status.ask.state === "unavailable") {
    showNotice("The answer models can't run on this machine",
      `${state.status.ask.reason} Open LinguaBridge_Colab.ipynb in Google Colab with a T4 GPU to use this section. Measuring the tax and the evidence work everywhere.`);
    $("ask-btn").disabled = true;
  }
}

function showNotice(title, body) {
  const box = $("ask-notice");
  box.replaceChildren(el("h2", null, title), el("p", null, body));
  box.hidden = false;
}

function resetAnswers() {
  $("answers").hidden = true;
  if (state.status?.ask.state !== "unavailable") $("ask-notice").hidden = true;
}

function updateRouteHint() {
  const r = state.pilot.routes[state.lang];
  if (!r) { $("route-hint").textContent = ""; return; }
  const via = r.route === "bridged" ? "over the bridge" : "directly";
  if (state.pilot.routes_measured && r.direct_accuracy != null && r.bridged_accuracy != null) {
    const pct = (x) => `${Math.round(x * 100)}%`;
    $("route-hint").textContent = `We send ${state.lang} questions ${via}: bridged answered ${pct(r.bridged_accuracy)} of test questions correctly, direct ${pct(r.direct_accuracy)}.`;
  } else {
    $("route-hint").textContent = `We would send ${state.lang} questions ${via}. That choice is provisional until our accuracy test has run.`;
  }
}

function skeleton() {
  const s = el("span", "skeleton");
  s.append(el("i"), el("i"), el("i"));
  return s;
}

$("ask-btn").addEventListener("click", async () => {
  const question = $("question").value.trim();
  if (!question) { showNotice("Type a question first", "Write it in the language you picked above."); return; }
  const btn = $("ask-btn");
  btn.disabled = true; btn.textContent = "Asking…";
  $("ask-notice").hidden = true;
  $("answers").hidden = false;
  for (const id of ["direct-text", "bridged-text"]) $(id).replaceChildren(skeleton());
  for (const id of ["direct-tokens", "bridged-tokens", "bridged-en-q", "bridged-en-a"]) $(id).textContent = "";
  $("route-hint").textContent = "The first question downloads the models, which can take a few minutes.";
  try {
    const r = await api("/api/ask", { question, language: state.lang });
    const dir = langInfo(state.lang).rtl ? "rtl" : "ltr";
    $("direct-text").textContent = r.direct.answer; $("direct-text").dir = dir;
    $("bridged-text").textContent = r.bridged.answer; $("bridged-text").dir = dir;
    $("direct-tokens").textContent = `${r.direct.tokens} model tokens`;
    $("bridged-tokens").textContent = `${r.bridged.tokens} model tokens`;
    $("bridged-en-q").textContent = r.bridged.english_question;
    $("bridged-en-a").textContent = r.bridged.english_answer;
    updateRouteHint();
  } catch (e) {
    $("answers").hidden = true;
    showNotice("The question couldn't be answered", `${e.message} ${e.data?.recovery || "Try again in a moment."}`);
    updateRouteHint();
  } finally {
    btn.disabled = false; btn.textContent = "Ask both ways";
  }
});

// ── evidence ──────────────────────────────────────────────────────────────

function renderEvidence() {
  const { models, tax, languages } = state.pilot;
  const langs = languages.map((l) => l.name).filter((l) => l !== "English");
  const sel = state.lang === "English" ? null : state.lang;

  // chart
  const W = 720, H = 380, L = 44, R = 132, T = 18, B = 58;
  const top = Math.ceil(Math.max(...models.flatMap((m) => langs.map((l) => tax[m.name][l]))) * 2) / 2;
  const X = (i) => L + (i * (W - L - R)) / (models.length - 1);
  const Y = (v) => T + ((top - v) / (top - 0.5)) * (H - T - B);
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
  for (let v = 1; v <= top; v++) {
    add(svg, "line", { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: v === 1 ? "base" : "grid" });
    add(svg, "text", { x: L - 10, y: Y(v) + 4, "text-anchor": "end" }, `${v}×`);
  }
  add(svg, "text", { x: L + 6, y: Y(1) + 17 }, "English");
  models.forEach((m, i) => {
    add(svg, "text", { x: X(i), y: H - B + 24, "text-anchor": i === 0 ? "start" : "middle" }, m.name);
    add(svg, "text", { x: X(i), y: H - B + 42, "text-anchor": i === 0 ? "start" : "middle" }, String(m.year));
  });
  // end labels, nudged apart so none overlap
  const ends = langs.map((l) => ({ l, y: Y(tax[models.at(-1).name][l]) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 17) ends[i].y = ends[i - 1].y + 17;
  const endY = Object.fromEntries(ends.map((e) => [e.l, e.y]));
  for (const l of [...langs.filter((x) => x !== sel), ...(sel ? [sel] : [])]) {   // selected line drawn last, on top
    const g = add(svg, "g", { class: l === sel ? "is-sel" : "" });
    const pts = models.map((m, i) => [X(i), Y(tax[m.name][l])]);
    add(g, "polyline", { class: "ln", points: pts.map((p) => p.join(",")).join(" ") });
    pts.forEach(([x, y], i) => {
      add(g, "circle", { class: "dot", cx: x, cy: y, r: l === sel ? 4.5 : 3 });
      if (l === sel) add(g, "text", { class: "val", x, y: y - 11, "text-anchor": i === 0 ? "start" : "middle" }, times(tax[models[i].name][l]));
    });
    const last = pts.at(-1);
    if (Math.abs(endY[l] - last[1]) > 2) add(g, "line", { class: "grid", x1: last[0] + 6, y1: last[1], x2: last[0] + 14, y2: endY[l] });
    add(g, "text", { class: "lbl", x: last[0] + 18, y: endY[l] + 4.5 }, l);
  }
  $("chart").replaceChildren(svg);

  const first = models[0], lastM = models.at(-1);
  if (sel) {
    const a = tax[first.name][sel], b = tax[lastM.name][sel];
    const change = Math.round((1 - b / a) * 100);
    const verdict = change >= 25 ? `${change}% cheaper` : change >= 8 ? `only ${change}% cheaper` : "almost unchanged";
    $("chart-caption").textContent = `${sel} went from ${times(a)} English on ${first.name} (${first.year}) to ${times(b)} on ${lastM.name} (${lastM.year}): ${verdict}.`;
    $("chart").setAttribute("aria-label", `Line chart of the token tax for five languages across four tokenizers. ${$("chart-caption").textContent}`);
  } else {
    $("chart-caption").textContent = "Pick a language above to follow its line.";
    $("chart").setAttribute("aria-label", "Line chart of the token tax for five languages across four tokenizers.");
  }

  // table
  const table = $("tax-table");
  table.querySelector("thead")?.remove();
  table.querySelector("tbody")?.remove();
  const thead = el("thead"), hr = el("tr");
  hr.append(el("th", null, "Model"));
  for (const l of langs) { const th = el("th", l === sel ? "is-sel" : null, l); th.scope = "col"; hr.append(th); }
  thead.append(hr);
  const tbody = el("tbody");
  for (const m of models) {
    const tr = el("tr");
    const th = el("th", null, m.name); th.scope = "row"; th.append(el("small", null, String(m.year)));
    tr.append(th);
    for (const l of langs) tr.append(el("td", l === sel ? "is-sel" : null, `${tax[m.name][l].toFixed(2)}×`));
    tbody.append(tr);
  }
  table.append(thead, tbody);

  $("routes-status").textContent = state.pilot.routes_measured
    ? "Which route each language takes is set by our measured accuracy on the Belebele test."
    : "Which route each language takes is still a provisional guess. It becomes a measured choice when the accuracy test has run.";
}

// ── start ─────────────────────────────────────────────────────────────────

(async function start() {
  try {
    [state.pilot, state.status] = await Promise.all([api("/api/pilot"), api("/api/status")]);
  } catch (e) {
    $("headline").textContent = "LinguaBridge couldn't reach its server.";
    $("subline").textContent = "Start it with “python server.py”, then reload this page.";
    return;
  }
  state.model = state.pilot.models.at(-1).name;          // newest tokenizer first
  renderChips();
  renderModels();
  $("message").value = state.pilot.sentences[state.lang][state.example];
  $("question").value = QUESTIONS[state.lang];
  applyDirection();
  updateRouteHint();
  renderEvidence();
  const wanted = tabs.find((t) => t.id === `tab-${location.hash.slice(1)}`);
  if (wanted) showTab(wanted);
  measure(true);
})();
