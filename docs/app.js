import rough from "https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.esm.js";

const $ = (s) => document.querySelector(s);
const T = "Taylor", S = "Sun Tzu";
const INK = "#2e3440", RED = "#be616a", CYAN = "#8fbbba", TEAL = "#4f8584";
const TRANSFORMERS = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2";
const FAILED = "The model didn't load. Check your connection and reload the page.";
const SVG = "http://www.w3.org/2000/svg";
let M, rounds, i = 0, score = { you: 0, model: 0 }, locked = false, embedder, pending = 0;
const barValue = new Map();

const pct = (x) => `${Math.round(x * 100)}%`;
const side = (label) => (label.startsWith("Sun") ? S : T);
const ink = (who) => (who === T ? "t-ink" : "s-ink");
const fullName = (who) => (who === T ? "Taylor Swift" : "Sun Tzu");

function layer(el, cls) {
  const svg = document.createElementNS(SVG, "svg");
  if (cls) svg.classList.add(cls);
  el.prepend(svg);
  return svg;
}

function sketchBox(el, fill, seed, stroke = INK) {
  el.querySelectorAll(":scope > svg").forEach((s) => s.remove());
  const { width: w, height: h } = el.getBoundingClientRect();
  if (!w) return;
  if (fill) {
    const f = layer(el, "fillsvg");
    f.appendChild(rough.svg(f).rectangle(3, 3, w - 6, h - 6, { seed, stroke: "none", fill, fillStyle: "solid", roughness: 1.3 }));
  }
  const o = layer(el);
  o.appendChild(rough.svg(o).rectangle(2, 2, w - 4, h - 4, { seed, stroke, strokeWidth: stroke === INK ? 1.6 : 2.2, roughness: 1.3, bowing: 1.5 }));
}

function drawBar(el, p) {
  el.innerHTML = "";
  const w = el.clientWidth, h = el.clientHeight;
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  svg.style.overflow = "visible";
  el.appendChild(svg);
  const rc = rough.svg(svg);
  const x = Math.max(2, Math.min(w - 2, p * w));
  const opts = { seed: 7, stroke: "none", fillStyle: "hachure", hachureGap: 4, fillWeight: 2, roughness: 1.2 };
  if (x > 3) svg.appendChild(rc.rectangle(2, 2, x - 2, h - 4, { ...opts, fill: RED }));
  if (x < w - 3) svg.appendChild(rc.rectangle(x, 2, w - x - 2, h - 4, { ...opts, fill: CYAN, hachureAngle: 41 }));
  svg.appendChild(rc.rectangle(2, 2, w - 4, h - 4, { seed: 7, stroke: INK, strokeWidth: 1.6, roughness: 1.2 }));
  svg.appendChild(rc.line(w / 2, -5, w / 2, h + 5, { seed: 3, stroke: INK, strokeWidth: 1.2, roughness: 0.8 }));
}

function setBar(el, p, animate = true) {
  const from = barValue.get(el) ?? 0.5;
  barValue.set(el, p);
  if (!animate || matchMedia("(prefers-reduced-motion: reduce)").matches) return drawBar(el, p);
  const t0 = performance.now(), dur = 700;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    const e = 1 - (1 - k) ** 3;
    drawBar(el, from + (p - from) * e);
    if (k < 1 && barValue.get(el) === p) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function doodle(el) {
  el.innerHTML = "";
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 44 44");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  el.appendChild(svg);
  const rc = rough.svg(svg);
  const line = { stroke: INK, strokeWidth: 1.3, roughness: 1.1, seed: 5 };
  const add = (n) => svg.appendChild(n);
  if (el.dataset.doodle === "guitar") {
    const body = { ...line, fill: RED, fillStyle: "hachure", hachureGap: 2.6, fillWeight: 1 };
    add(rc.circle(22, 33, 20, body));
    add(rc.circle(22, 21, 15, body));
    add(rc.circle(22, 28, 5, { ...line, fill: "#fff", fillStyle: "solid" }));
    add(rc.rectangle(20.5, 3, 3, 15, line));
    add(rc.rectangle(18.5, 0, 7, 4, line));
    add(rc.line(19, 38, 25, 38, line));
  } else {
    add(rc.polygon([[22, 1], [25, 7], [25, 29], [19, 29], [19, 7]], { ...line, fill: CYAN, fillStyle: "hachure", hachureGap: 2.4, fillWeight: 1 }));
    add(rc.line(22, 7, 22, 27, { ...line, strokeWidth: 0.8 }));
    add(rc.rectangle(12, 29, 20, 3.5, { ...line, fill: INK, fillStyle: "solid" }));
    add(rc.rectangle(20.5, 33, 3, 7, line));
    add(rc.circle(22, 42, 4, line));
  }
}

function sketchAll() {
  document.querySelectorAll(".doodle").forEach(doodle);
  sketchBox($(".pick.t"), "#f1d6d9", 11, RED);
  sketchBox($(".pick.s"), "#d6e8e7", 12, TEAL);
  document.querySelectorAll(".go").forEach((b, k) => sketchBox(b, "#e5e9f0", 20 + k));
  sketchBox($("#field"), null, 30);
  document.querySelectorAll(".tries button").forEach((b, k) => sketchBox(b, b.dataset.side === T ? "#f1d6d9" : "#d6e8e7", 40 + k, b.dataset.side === T ? RED : TEAL));
  for (const el of [$("#bar"), $("#live-bar")]) if (el.offsetParent) drawBar(el, barValue.get(el) ?? 0.5);
}

async function loadEmbedder() {
  if (!embedder) {
    const { pipeline } = await import(TRANSFORMERS);
    embedder = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
  }
  return embedder;
}

async function probTaylor(text) {
  const out = await (await loadEmbedder())(text, { pooling: "mean", normalize: true });
  let z = M.intercept;
  for (let k = 0; k < M.coef.length; k++) z += out.data[k] * M.coef[k];
  return 1 / (1 + Math.exp(-z));
}

function modelLine(p) {
  const who = p >= 0.5 ? T : S;
  const sure = Math.max(p, 1 - p);
  const hedge = sure < 0.56 ? " Basically a coin flip." : "";
  return `The model says <b class="${ink(who)}">${who}</b>, ${pct(sure)} sure.${hedge}`;
}

function showScore() {
  $("#score").textContent = `you ${score.you}, model ${score.model}`;
}

function showRound() {
  const r = rounds[i];
  locked = false;
  $("#round").textContent = `${i + 1} of ${rounds.length}`;
  showScore();
  $("#line").textContent = r.text;
  $("#line").hidden = $("#picks").hidden = false;
  $("#reveal").hidden = $("#end").hidden = true;
  document.querySelectorAll(".pick").forEach((b) => { b.disabled = false; b.classList.remove("chosen"); });
  barValue.set($("#bar"), 0.5);
  sketchAll();
}

function guess(pick) {
  if (locked) return;
  locked = true;
  const r = rounds[i];
  const truth = side(r.label);
  const modelRight = (r.p >= 0.5 ? T : S) === truth;
  score.you += pick === truth;
  score.model += modelRight;
  document.querySelectorAll(".pick").forEach((b) => {
    b.disabled = true;
    b.classList.toggle("chosen", b.dataset.pick === pick);
  });
  $("#answer").innerHTML = `${pick === truth ? "Yes" : "Nope"}, it's <span class="${ink(truth)}">${fullName(truth)}</span>.`;
  $("#model").innerHTML = modelLine(r.p) + (modelRight ? "" : " Wrong.");
  $("#note").textContent = r.label.includes("(") ? r.note : "";
  showScore();
  $("#next").querySelector("span").textContent = i === rounds.length - 1 ? "See the score" : "Next";
  $("#reveal").hidden = false;
  sketchAll();
  drawBar($("#bar"), 0.5);
  setBar($("#bar"), r.p);
}

function next() {
  if (!locked) return;
  i += 1;
  if (i < rounds.length) return showRound();
  $("#line").hidden = $("#picks").hidden = $("#reveal").hidden = true;
  $("#round").textContent = "";
  const verdict = score.you > score.model ? "You beat the model." : score.you === score.model ? "Tie." : "The model wins.";
  $("#final").textContent = `You ${score.you}, model ${score.model}. ${verdict}`;
  $("#end-note").textContent = `We picked tricky lines on purpose. On ${M.n_test} random lines it had never seen, it got ${pct(M.accuracy)} right.`;
  $("#end").hidden = false;
  sketchAll();
}

function go(view) {
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== view));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("on", a.dataset.go === view));
  history.replaceState(null, "", view === "play" ? location.pathname : `#${view}`);
  sketchAll();
  if (view !== "fool") return;
  $("#input").focus();
  loadEmbedder()
    .then(() => ($("#input").value.trim() ? live() : ($("#live-model").textContent = "Start typing.")))
    .catch(() => ($("#live-model").textContent = FAILED));
}

async function live() {
  const text = $("#input").value.trim();
  const ticket = ++pending;
  if (!text) {
    setBar($("#live-bar"), 0.5, false);
    if (embedder) $("#live-model").textContent = "Start typing.";
    return;
  }
  try {
    const p = await probTaylor(text);
    if (ticket !== pending) return;
    setBar($("#live-bar"), p, false);
    $("#live-model").innerHTML = modelLine(p);
  } catch {
    $("#live-model").textContent = FAILED;
  }
}

async function init() {
  M = await (await fetch("model.json")).json();
  rounds = M.rounds.concat(M.traps);

  $("#tries").innerHTML = M.traps.map((t) =>
    `<li><button class="sketch" data-side="${side(t.label)}" data-try="${t.text.replace(/"/g, "&quot;")}"><span>${t.text}<small>really ${t.label}</small></span></button></li>`).join("");

  document.addEventListener("click", (e) => {
    const g = e.target.closest("[data-go]");
    if (g) { e.preventDefault(); go(g.dataset.go); }
    const p = e.target.closest("[data-pick]");
    if (p) guess(p.dataset.pick);
    const t = e.target.closest("[data-try]");
    if (t) { $("#input").value = t.dataset.try; live(); }
  });
  $("#next").addEventListener("click", next);
  $("#again").addEventListener("click", () => { i = 0; score = { you: 0, model: 0 }; go("play"); showRound(); });
  $("#input").addEventListener("input", live);
  document.addEventListener("keydown", (e) => {
    if ($("#play").hidden || locked || e.target === $("#input")) return;
    if (e.key === "ArrowLeft") guess(T);
    else if (e.key === "ArrowRight") guess(S);
  });
  let resizeTimer;
  addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(sketchAll, 120); });
  document.fonts.ready.then(sketchAll);

  showRound();
  const route = () => go(location.hash === "#fool" ? "fool" : "play");
  addEventListener("hashchange", route);
  if (location.hash === "#fool") route();
}

init();
