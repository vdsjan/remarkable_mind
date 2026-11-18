// Remarkable Mind website: the configurator. All puzzle work happens in
// engine.js (a Web Worker running the Python generator through Pyodide).

const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid != null) n.append(kid);
  return n;
};

const STORE = "remarkable-mind-config-v1";
const PRESETS = [
  { key: "proef", label: "Proefpakket", hint: "3 per spel", fill: () => 3 },
  { key: "week", label: "Weekmix", hint: "5 per spel", fill: () => 5 },
  { key: "vol", label: "Volledig boek", hint: "25 per spel", fill: () => 25 },
  { key: "getallen", label: "Alleen getallen", hint: "10 per spel", cat: "getallen" },
  { key: "logica", label: "Alleen logica", hint: "10 per spel", cat: "logica" },
  { key: "ruimte", label: "Alleen ruimte", hint: "10 per spel", cat: "ruimte" },
  { key: "taal", label: "Alleen taal", hint: "10 per spel", cat: "taal" },
  { key: "leeg", label: "Alles op nul", hint: "", fill: () => 0 },
];

let manifest;
let state = { device: "paperpro", counts: {}, difficulty: "mix", plan: true,
              solutions: true, seed: 2026 };
let engine = null;
let engineReady = false;
let engineWaiters = [];
let busy = false;
let lastUrl = null;

// --- state ------------------------------------------------------------------------
function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || "null");
    if (saved && typeof saved === "object") state = { ...state, ...saved };
  } catch { /* private mode: start fresh */ }
  for (const g of manifest.games) {
    const n = Number(state.counts[g.key]);
    state.counts[g.key] = Number.isFinite(n) ? clamp(n) : 5;
  }
  if (!manifest.devices.some((d) => d.key === state.device)) state.device = "paperpro";
}

function saveState() {
  try { localStorage.setItem(STORE, JSON.stringify(state)); } catch { /* ignore */ }
}

const clamp = (n) => Math.max(0, Math.min(manifest.maxPerGame, Math.round(n) || 0));

// --- estimates (mirror mind/book.py closely enough for a summary) --------------------
function planDays() {
  if (!state.plan) return 0;
  const byCat = {};
  for (const g of manifest.games) {
    const n = state.counts[g.key];
    if (n > 0) (byCat[g.category] ||= []).push(n);
  }
  const cats = Object.values(byCat);
  if (!cats.length) return 0;
  let days = 30;
  const fits = (d) => cats.every((ns) =>
    ns.slice(0, Math.min(d, ns.length)).every((n) => n >= Math.ceil(d / ns.length)));
  while (days > 0 && !fits(days)) days--;
  return days >= 3 ? days : 0;
}

function estimate() {
  const move = state.device === "move";
  let puzzles = 0, games = 0, pages = 3 + (move ? 2 : 1);
  for (const g of manifest.games) {
    const n = state.counts[g.key];
    if (!n) continue;
    games++;
    puzzles += n;
    pages += 1 + n * g.parts + (state.solutions ? n : 0);
  }
  const days = planDays();
  if (days) pages += move ? 1 + Math.ceil(Math.max(0, days - 4) / 8) : Math.ceil(days / 15);
  pages += move ? Math.max(1, Math.ceil(games / 6)) : 1;
  if (state.solutions && puzzles) pages += 1;
  return { puzzles, games, pages: puzzles ? pages : 0, days };
}

// --- rendering ------------------------------------------------------------------------
function renderDevices() {
  const box = $("#devices");
  box.replaceChildren(...manifest.devices.map((d) => {
    const [w, h] = d.px;
    const card = el("button", {
      type: "button", class: "device", role: "radio",
      "aria-checked": String(state.device === d.key), "data-key": d.key,
      onclick: () => { state.device = d.key; update(); },
    },
      el("span", { class: "bezel", style: `aspect-ratio:${w}/${h}` },
        el("img", { src: `/img/preview/${d.key}-home.webp`, alt: "", loading: "lazy" })),
      el("span", { class: "device-name", text: d.key === "rm2" ? d.label : d.label.replace("reMarkable ", "") }),
      el("span", { class: "device-spec", text: `${d.screen} · ${w}×${h}` }));
    return card;
  }));
}

function renderPresets() {
  $("#presets").replaceChildren(...PRESETS.map((p) => el("button", {
    type: "button", class: "chip",
    onclick: () => {
      for (const g of manifest.games) {
        state.counts[g.key] = p.cat ? (g.category === p.cat ? 10 : 0) : p.fill(g);
      }
      update();
    },
  }, el("strong", { text: p.label }), p.hint ? el("small", { text: p.hint }) : null)));
}

function renderCategories() {
  const box = $("#categories");
  box.replaceChildren(...manifest.categories.map((cat) => {
    const list = manifest.games.filter((g) => g.category === cat.key);
    return el("section", { class: "cat", style: `--cat:${cat.color}` },
      el("header", { class: "cat-head" },
        el("img", { src: `/img/cat_${cat.key}.webp`, alt: "", loading: "lazy", width: 64, height: 64 }),
        el("div", {},
          el("h4", { text: cat.name }),
          el("p", { text: cat.blurb })),
        el("button", { type: "button", class: "btn btn-small cat-all", "data-cat": cat.key,
          onclick: () => {
            const on = list.every((g) => state.counts[g.key] > 0);
            for (const g of list) state.counts[g.key] = on ? 0 : Math.max(5, state.counts[g.key]);
            update();
          } }, "Alles")),
      el("ul", { class: "games" }, list.map((g) => el("li", {
        class: "game", "data-key": g.key, title: g.rules.join(" "),
      },
        el("img", { src: `/img/icons/${g.key}.png`, alt: "", width: 40, height: 40 }),
        el("div", { class: "game-text" },
          el("strong", { text: g.name }),
          el("small", { text: g.tagline })),
        el("div", { class: "stepper" },
          el("button", { type: "button", "aria-label": `Minder ${g.name}`,
            onclick: () => { state.counts[g.key] = clamp(state.counts[g.key] - 1); update(); } }, "−"),
          el("input", { type: "number", min: 0, max: manifest.maxPerGame, inputmode: "numeric",
            "aria-label": `Aantal ${g.name}`, value: state.counts[g.key],
            onchange: (e) => { state.counts[g.key] = clamp(Number(e.target.value)); update(); } }),
          el("button", { type: "button", "aria-label": `Meer ${g.name}`,
            onclick: () => { state.counts[g.key] = clamp(state.counts[g.key] + 1); update(); } }, "+"))))));
  }));
}

function renderDifficulty() {
  $("#difficulty").replaceChildren(...Object.entries(manifest.difficulties).map(([k, label]) =>
    el("button", { type: "button", role: "radio", "data-key": k,
      onclick: () => { state.difficulty = k; update(); } }, label)));
}

function renderReady() {
  $("#ready").replaceChildren(...manifest.devices.map((d) => {
    const [w, h] = d.px;
    return el("article", { class: "ready-card" },
      el("span", { class: "bezel", style: `aspect-ratio:${w}/${h}` },
        el("img", { src: `/img/preview/${d.key}-puzzle.webp`, alt: `Voorbeeldpagina op de ${d.label}`, loading: "lazy" })),
      el("h3", { text: d.label }),
      el("p", { text: `${d.screen} · ${d.download.pages} pagina's · ${String(d.download.mb).replace(".", ",")} MB` }),
      el("a", { class: "btn btn-ink", href: `/${d.download.file}`, download: true }, "Download PDF"));
  }));
  $("#cats-art").replaceChildren(...manifest.categories.map((c) =>
    el("li", { style: `--cat:${c.color}` },
      el("img", { src: `/img/cat_${c.key}.webp`, alt: "", loading: "lazy" }),
      el("span", { text: c.name }))));
}

function update() {
  for (const card of document.querySelectorAll(".device")) {
    card.setAttribute("aria-checked", String(card.dataset.key === state.device));
  }
  for (const li of document.querySelectorAll(".game")) {
    const n = state.counts[li.dataset.key];
    li.classList.toggle("off", n === 0);
    const input = $("input", li);
    if (Number(input.value) !== n) input.value = n;
  }
  for (const b of document.querySelectorAll("#difficulty button")) {
    b.setAttribute("aria-checked", String(b.dataset.key === state.difficulty));
  }
  $("#opt-plan").checked = state.plan;
  $("#opt-solutions").checked = state.solutions;
  if (Number($("#opt-seed").value) !== state.seed) $("#opt-seed").value = state.seed;

  const dev = manifest.devices.find((d) => d.key === state.device);
  const est = estimate();
  $("#sum-device").textContent = dev.label;
  $("#sum-puzzles").textContent = est.puzzles;
  $("#sum-games").textContent = est.games;
  $("#sum-pages").textContent = est.pages ? `±${est.pages}` : "0";
  const notes = [];
  if (state.plan && est.puzzles) {
    notes.push(est.days ? `Dagplan van ${est.days} dagen.` : "Te weinig puzzels voor een dagplan.");
  }
  if (dev.mono) notes.push("Zwart-wit editie in grijstinten.");
  if (state.device === "move") notes.push("Pagina's in 9:16 voor het 7,3-inch scherm.");
  $("#sum-note").textContent = notes.join(" ");
  $("#make").disabled = busy || est.puzzles === 0;
  $("#make").textContent = est.puzzles === 0 ? "Kies minstens één puzzel" : "Maak mijn PDF";
  saveState();
}

// --- engine -------------------------------------------------------------------------------
function startEngine() {
  if (engine) return;
  engine = new Worker(new URL("./engine.js", import.meta.url), { type: "module" });
  engine.onmessage = (e) => onEngine(e.data);
  engine.onerror = (e) => fail(`De rekenmotor kon niet starten (${e.message || "onbekende fout"}).`);
  engine.postMessage({ type: "init", manifest });
}

function whenReady() {
  return engineReady ? Promise.resolve() : new Promise((res) => engineWaiters.push(res));
}

let currentId = 0;
let onBuild = null;

function onEngine(msg) {
  if (msg.type === "status") {
    setStage("engine", msg.text);
  } else if (msg.type === "ready") {
    engineReady = true;
    engineWaiters.splice(0).forEach((f) => f());
  } else if (msg.type === "progress" && msg.id === currentId) {
    setStage(msg.stage, `${msg.done} / ${msg.total}`, msg.done / msg.total);
  } else if ((msg.type === "done" || msg.type === "error") && onBuild && (msg.id === currentId || msg.id == null)) {
    onBuild(msg);
  }
}

const STAGES = ["engine", "puzzels", "pagina's"];
const WEIGHT = { engine: [0, 0.12], puzzels: [0.12, 0.72], "pagina's": [0.72, 1] };

function setStage(stage, detail, frac = 0) {
  const idx = STAGES.indexOf(stage);
  document.querySelectorAll(".progress-steps li").forEach((li, i) => {
    li.classList.toggle("done", i < idx);
    li.classList.toggle("active", i === idx);
  });
  if (stage === "puzzels") $("#p-puz").textContent = detail;
  if (stage === "pagina's") $("#p-pag").textContent = detail;
  const [a, b] = WEIGHT[stage];
  $("#p-fill").style.width = `${Math.round((a + (b - a) * frac) * 100)}%`;
}

function fail(text) {
  busy = false;
  $("#progress").hidden = true;
  $("#error").hidden = false;
  $("#error").textContent = `Er ging iets mis: ${text}`;
  update();
}

async function make() {
  if (busy) return;
  busy = true;
  update();
  $("#error").hidden = true;
  $("#result").hidden = true;
  $("#progress").hidden = false;
  $("#p-puz").textContent = "";
  $("#p-pag").textContent = "";
  setStage(engineReady ? "puzzels" : "engine", engineReady ? "" : "Rekenmotor laden");
  startEngine();
  await whenReady();
  const spec = {
    device: state.device, difficulty: state.difficulty, plan: state.plan,
    solutions: state.solutions, seed: state.seed,
    counts: Object.fromEntries(Object.entries(state.counts).filter(([, n]) => n > 0)),
  };
  const id = ++currentId;
  setStage("puzzels", "");
  const msg = await new Promise((res) => { onBuild = res; engine.postMessage({ type: "build", id, spec }); });
  onBuild = null;
  busy = false;
  if (msg.type === "error") {
    console.error(msg.detail);
    fail(msg.message);
    return;
  }
  const dev = manifest.devices.find((d) => d.key === spec.device);
  const name = `RemarkableMind${dev.suffix || "-PaperPro"}-${spec.seed}.pdf`;
  if (lastUrl) URL.revokeObjectURL(lastUrl);
  lastUrl = URL.createObjectURL(new Blob([msg.pdf], { type: "application/pdf" }));
  const a = $("#download");
  a.href = lastUrl;
  a.download = name;
  const s = msg.stats;
  $("#result-meta").textContent =
    `${s.puzzles} puzzels · ${s.pages} pagina's · ${String(s.mb).replace(".", ",")} MB · ` +
    `klaar in ${Math.max(1, Math.round(s.browserSeconds))} s`;
  $("#progress").hidden = true;
  $("#result").hidden = false;
  $("#result").scrollIntoView({ behavior: "smooth", block: "nearest" });
  update();
}

// --- wiring -------------------------------------------------------------------------------------
async function main() {
  manifest = await fetch("/py/manifest.json", { cache: "no-cache" }).then((r) => r.json());
  loadState();
  renderDevices();
  renderPresets();
  renderCategories();
  renderDifficulty();
  renderReady();
  $("#version").textContent = `versie ${manifest.version}`;
  $("#opt-plan").addEventListener("change", (e) => { state.plan = e.target.checked; update(); });
  $("#opt-solutions").addEventListener("change", (e) => { state.solutions = e.target.checked; update(); });
  $("#opt-seed").addEventListener("change", (e) => {
    state.seed = Math.max(1, Math.min(999999, Math.round(Number(e.target.value)) || 2026));
    update();
  });
  $("#seed-dice").addEventListener("click", () => {
    state.seed = 1 + Math.floor(Math.random() * 999999);
    update();
  });
  $("#make").addEventListener("click", make);
  // warm up the engine as soon as someone starts configuring
  $("#maak").addEventListener("pointerdown", startEngine, { once: true });
  update();
  if ("serviceWorker" in navigator && location.protocol === "https:") {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

main().catch((err) => {
  console.error(err);
  document.body.prepend(el("p", { class: "error", text: "De pagina kon niet laden. Probeer het opnieuw." }));
});
