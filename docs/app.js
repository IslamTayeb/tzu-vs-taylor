const $ = (s) => document.querySelector(s);
const T = "Taylor", S = "Sun Tzu";
let M, rounds, i = 0, score = { you: 0, model: 0 }, locked = false;

const pct = (x) => `${Math.round(x * 100)}%`;
const side = (label) => (label.startsWith("Sun") ? S : T);
const cls = (who) => (who === T ? "t" : "s");

function tokens(text) {
  const uni = (text.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []);
  const bi = uni.slice(1).map((w, k) => `${uni[k]} ${w}`);
  return uni.concat(bi);
}

function score1(text) {
  const tf = new Map();
  for (const t of tokens(text)) if (M.vocab[t]) tf.set(t, (tf.get(t) || 0) + 1);
  let norm = 0;
  const w = [];
  for (const [t, n] of tf) {
    const [idf, coef] = M.vocab[t];
    const v = (1 + Math.log(n)) * idf;
    norm += v * v;
    w.push([t, v, coef]);
  }
  norm = Math.sqrt(norm) || 1;
  let z = M.intercept;
  for (const x of w) { x[1] /= norm; z += x[1] * x[2]; }
  return { p: 1 / (1 + Math.exp(-z)), parts: w.map(([t, v, c]) => [t, v * c]) };
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
  $("#model").innerHTML = modelLine(r.p) + (modelPick === truth ? "" : " Wrong too.");
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
  if (view === "fool") $("#input").focus();
  history.replaceState(null, "", view === "play" ? location.pathname : `#${view}`);
}

function live() {
  const text = $("#input").value.trim();
  if (!text) {
    setMeter($("#live-meter"), 0.5);
    $("#live-model").textContent = "Start typing.";
    $("#live-words").textContent = "";
    return;
  }
  const { p, parts } = score1(text);
  setMeter($("#live-meter"), p);
  $("#live-model").innerHTML = parts.length ? modelLine(p) : "It doesn't know any of these words, so it can only guess 50/50.";
  const top = parts.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6);
  $("#live-words").innerHTML = top.length
    ? "Pulling hardest: " + top.map(([t, v]) => `<span class="${v > 0 ? "t" : "s"}">${t}</span>`).join(", ")
    : "";
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
