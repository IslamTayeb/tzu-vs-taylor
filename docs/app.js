const $ = (s) => document.querySelector(s);
const T = "Taylor", S = "Sun Tzu";
const TRANSFORMERS = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2";
const FAILED = "The model didn't load. Check your connection and reload the page.";
let M, rounds, i = 0, score = { you: 0, model: 0 }, locked = false, embedder, pending = 0;

const pct = (x) => `${Math.round(x * 100)}%`;
const side = (label) => (label.startsWith("Sun") ? S : T);
const ink = (who) => (who === T ? "t-ink" : "s-ink");
const fullName = (who) => (who === T ? "Taylor Swift" : "Sun Tzu");

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

function setBar(el, p) {
  el.querySelector(".fill").style.width = `${p * 100}%`;
}

function modelLine(p) {
  const who = p >= 0.5 ? T : S;
  const sure = Math.max(p, 1 - p);
  const hedge = sure < 0.56 ? " Basically a coin flip." : "";
  return `The model says <b class="${ink(who)}">${who}</b>, ${pct(sure)} sure.${hedge}`;
}

function showScore() {
  $("#score").textContent = `You ${score.you}, model ${score.model}`;
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
  setBar($("#bar"), 0.5);
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
  $("#reveal").hidden = false;
  requestAnimationFrame(() => requestAnimationFrame(() => setBar($("#bar"), r.p)));
  $("#next").textContent = i === rounds.length - 1 ? "See the score" : "Next";
  $("#next").focus({ preventScroll: true });
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
}

function go(view) {
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== view));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("on", a.dataset.go === view));
  history.replaceState(null, "", view === "play" ? location.pathname : `#${view}`);
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
    setBar($("#live-bar"), 0.5);
    if (embedder) $("#live-model").textContent = "Start typing.";
    return;
  }
  try {
    const p = await probTaylor(text);
    if (ticket !== pending) return;
    setBar($("#live-bar"), p);
    $("#live-model").innerHTML = modelLine(p);
  } catch {
    $("#live-model").textContent = FAILED;
  }
}

async function init() {
  M = await (await fetch("model.json")).json();
  rounds = M.rounds.concat(M.traps);

  $("#n-train").textContent = M.n_train;
  $("#n-test").textContent = M.n_test;
  $("#acc").textContent = pct(M.accuracy);
  $("#top-t").innerHTML = M.top.Taylor.slice(0, 8).map(([w]) => `<li>${w}</li>`).join("");
  $("#top-s").innerHTML = M.top["Sun Tzu"].slice(0, 8).map(([w]) => `<li>${w}</li>`).join("");
  $("#tries").innerHTML = M.traps.map((t) =>
    `<li><button data-try="${t.text.replace(/"/g, "&quot;")}">${t.text}<small>Really ${t.label}</small></button></li>`).join("");

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
    if ($("#play").hidden || e.metaKey || e.ctrlKey || e.target === $("#input")) return;
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
