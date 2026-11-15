import { $, $$, COLORS, TAYLOR, SUN_TZU } from "./common.js";
import { loadWeights } from "./model.js";
import { box, bar, doodle } from "./sketch.js";
import { startGame, guess, next, restart, isWaitingForGuess, canGoNext } from "./play.js";
import { listTraps, openFool, update } from "./fool.js";

function drawAll() {
  $$(".doodle").forEach(doodle);
  for (const who of [TAYLOR, SUN_TZU]) {
    box($(`.pick[data-pick="${who}"]`), { fill: COLORS[who].tint, stroke: COLORS[who].line, seed: who.length });
  }
  $$(".go").forEach((b, k) => box(b, { fill: "#e5e9f0", seed: 20 + k }));
  $$(".tries button").forEach((b, k) => box(b, { fill: COLORS[b.dataset.side].tint, stroke: COLORS[b.dataset.side].line, seed: 40 + k }));
  box($("#field"), { seed: 30 });
  if (!$("#fool").hidden && !$("#live-bar").childElementCount) bar($("#live-bar"), 0.5);
}

function show(view) {
  $$(".view").forEach((v) => (v.hidden = v.id !== view));
  $$("nav a").forEach((a) => a.classList.toggle("on", a.dataset.go === view));
  drawAll();
  if (view === "fool") openFool();
}

function route() {
  show(location.hash === "#fool" ? "fool" : "play");
}

async function init() {
  const weights = await loadWeights();
  listTraps(weights.traps);
  startGame(weights);

  document.addEventListener("click", (e) => {
    const pick = e.target.closest("[data-pick]");
    const sample = e.target.closest("[data-try]");
    const link = e.target.closest("[data-go]");
    if (pick) guess(pick.dataset.pick);
    if (sample) { $("#input").value = sample.dataset.try; update(); }
    if (link) { e.preventDefault(); location.hash = link.dataset.go === "fool" ? "fool" : ""; route(); }
  });
  $("#next").addEventListener("click", next);
  $("#again").addEventListener("click", () => { location.hash = ""; restart(); route(); });
  $("#input").addEventListener("input", update);
  document.addEventListener("keydown", (e) => {
    if (isWaitingForGuess()) {
      if (e.key === "ArrowLeft") guess(TAYLOR);
      if (e.key === "ArrowRight") guess(SUN_TZU);
    } else if (canGoNext() && (e.key === "Enter" || e.key === " ") && !e.target.closest?.("button")) {
      e.preventDefault();
      next();
    }
  });

  let timer;
  addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(drawAll, 120); });
  addEventListener("hashchange", route);
  document.addEventListener("redraw", drawAll);
  document.fonts.ready.then(drawAll);
  route();
}

init();
