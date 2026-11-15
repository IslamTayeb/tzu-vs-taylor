const $ = (s) => document.querySelector(s);
const T = "Taylor", S = "Sun Tzu";
let M, rounds, i = 0, score = { you: 0, model: 0 }, locked = false;

const pct = (x) => `${Math.round(x * 100)}%`;
const side = (label) => (label.startsWith("Sun") ? S : T);
const cls = (who) => (who === T ? "t" : "s");

const TRANSFORMERS = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2";
let embedder, pending = 0;

async function loadEmbedder() {
  if (embedder) return embedder;
  const { pipeline } = await import(TRANSFORMERS);
  embedder = await pipeline("feature-extraction", "Xenova/all-MiniLM-L6-v2");
  return embedder;
}

async function probTaylor(text) {
  const out = await (await loadEmbedder())(text, { pooling: "mean", normalize: true });
  let z = M.intercept;
  for (let k = 0; k < M.coef.length; k++) z += out.data[k] * M.coef[k];
  return 1 / (1 + Math.exp(-z));
}

function setMeter(el, p) {
  el.querySelector(".fill").style.width = `${p * 100}%`;
}

function modelLine(p) {
  const who = p >= 0.5 ? T : S;
  const sure = Math.max(p, 1 - p);
  const hedge = sure < 0.56 ? " That's a coin flip." : "";
  return `The model says <span class="${cls(who)}">${who}</span>, ${pct(sure)} sure.${hedge}`;
}

function showRound() {
  const r = rounds[i];
  locked = false;
  $("#round").textContent = `Line ${i + 1} of ${rounds.length}`;
  $("#score").textContent = `You ${score.you}  ·  Model ${score.model}`;
  $("#line").textContent = r.text;
  $("#reveal").hidden = true;
  $("#end").hidden = true;
  $("#choices").hidden = false;
  $("#line").hidden = false;
  document.querySelectorAll(".pick").forEach((b) => { b.disabled = false; b.classList.remove("chosen"); });
  setMeter($("#meter"), 0.5);
}

function guess(pick) {
  if (locked) return;
  locked = true;
  const r = rounds[i];
  const truth = side(r.label);
  const modelPick = r.p >= 0.5 ? T : S;
  score.you += pick === truth;
  score.model += modelPick === truth;
  document.querySelectorAll(".pick").forEach((b) => {
    b.disabled = true;
    if (b.dataset.pick === pick) b.classList.add("chosen");
  });
  const who = r.label === "Taylor" ? "Taylor Swift" : r.label;
  $("#verdict").innerHTML = `${pick === truth ? "Right." : "Wrong."} It's <span class="${cls(truth)}">${who}</span>.`;
  $("#model").innerHTML = modelLine(r.p) + (modelPick === truth ? "" : " It's wrong.");
  $("#note").textContent = r.note;
  $("#score").textContent = `You ${score.you}  ·  Model ${score.model}`;
  $("#reveal").hidden = false;
  requestAnimationFrame(() => requestAnimationFrame(() => setMeter($("#meter"), r.p)));
  $("#next").textContent = i === rounds.length - 1 ? "See the score" : "Next line";
  $("#next").focus({ preventScroll: true });
}

function next() {
  if (!locked) return;
  i += 1;
  if (i < rounds.length) return showRound();
  $("#line").hidden = true;
  $("#choices").hidden = true;
  $("#reveal").hidden = true;
  $("#round").textContent = "Done";
  $("#end-lede").textContent = `On ${M.n_test} lines it had never seen, the model was right ${pct(M.accuracy)} of the time. We picked these lines to show where it slips.`;
  const verdict = score.you > score.model ? "You beat the model." : score.you === score.model ? "A tie." : "The model wins.";
  $("#final").textContent = `You ${score.you}, model ${score.model}. ${verdict}`;
  $("#end").hidden = false;
}

function restart() {
  i = 0;
  score = { you: 0, model: 0 };
  showRound();
}

function go(view) {
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== view));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("on", a.dataset.go === view));
  if (view === "fool") {
    $("#input").focus();
    loadEmbedder().then(() => { if (!$("#input").value.trim()) $("#live-model").textContent = "Start typing."; else live(); })
      .catch(() => { $("#live-model").textContent = "The model didn't load. Check your connection and reload the page."; });
  }
  history.replaceState(null, "", view === "play" ? location.pathname : `#${view}`);
}

async function live() {
  const text = $("#input").value.trim();
  const ticket = ++pending;
  if (!text) {
    setMeter($("#live-meter"), 0.5);
    if (embedder) $("#live-model").textContent = "Start typing.";
    return;
  }
  try {
    const p = await probTaylor(text);
    if (ticket !== pending) return;
    setMeter($("#live-meter"), p);
    $("#live-model").innerHTML = modelLine(p);
  } catch {
    $("#live-model").textContent = "The model didn't load. Check your connection and reload the page.";
  }
}

async function init() {
  M = await (await fetch("model.json")).json();
  rounds = M.rounds.concat(M.traps);

  $("#n-lines").textContent = `${M.n_train + M.n_test}`;
  $("#n-test").textContent = `${M.n_test}`;
  $("#acc").textContent = pct(M.accuracy);
  $("#top-t").innerHTML = M.top.Taylor.slice(0, 10).map(([w]) => `<li>${w}</li>`).join("");
  $("#top-s").innerHTML = M.top["Sun Tzu"].slice(0, 10).map(([w]) => `<li>${w}</li>`).join("");
  $("#tries").innerHTML = M.traps.map((t) =>
    `<li><button data-try="${t.text.replace(/"/g, "&quot;")}">${t.text}<small>Really ${t.label}</small></button></li>`).join("");

  document.addEventListener("click", (e) => {
    const g = e.target.closest("[data-go]");
    if (g) { e.preventDefault(); go(g.dataset.go); }
    const p = e.target.closest("[data-pick]");
    if (p) guess(p.dataset.pick);
    const t = e.target.closest("[data-try]");
    if (t) { $("#input").value = t.dataset.try; live(); $("#input").focus(); }
  });
  $("#next").addEventListener("click", next);
  $("#again").addEventListener("click", () => { go("play"); restart(); });
  $("#input").addEventListener("input", live);
  document.addEventListener("keydown", (e) => {
    if ($("#play").hidden || e.metaKey || e.ctrlKey) return;
    const k = e.key.toLowerCase();
    if (!locked && k === "t") guess(T);
    else if (!locked && k === "s") guess(S);
    else if (locked && k === "enter" && document.activeElement !== $("#next")) next();
  });

  const start = location.hash.slice(1);
  if (["fool", "how"].includes(start)) go(start);
  showRound();
}

init();
