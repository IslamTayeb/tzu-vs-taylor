import { $, $$, COLORS, TAYLOR, SUN_TZU, percent, sideOf, guessOf, confidence, named } from "./common.js";
import { animateBar, bar, marks } from "./sketch.js";

let rounds = [];
let stats = {};
let index = 0;
let score = { you: 0, model: 0 };
let answered = false;

const redraw = () => document.dispatchEvent(new Event("redraw"));
const mark = (ok) => `<i class="mark" data-ok="${ok}" role="img" aria-label="${ok ? "right" : "wrong"}"></i>`;

export function startGame(weights) {
  rounds = weights.rounds;
  stats = { tested: weights.n_test, accuracy: weights.accuracy };
  index = 0;
  score = { you: 0, model: 0 };
  showRound();
}

export const isWaitingForGuess = () => !answered && !$("#play").hidden;
export const canGoNext = () => answered && !$("#play").hidden && !$("#reveal").hidden;

function showScore() {
  $("#score").textContent = `you ${score.you}, model ${score.model}`;
}

function showRound() {
  answered = false;
  $("#round").textContent = `${index + 1} of ${rounds.length}`;
  $("#line").textContent = rounds[index].text;
  $("#line").hidden = $("#picks").hidden = false;
  $("#reveal").hidden = $("#end").hidden = true;
  $$(".pick").forEach((b) => { b.disabled = false; b.classList.remove("chosen"); });
  showScore();
  redraw();
}

export function guess(pick) {
  if (answered) return;
  answered = true;

  const round = rounds[index];
  const truth = sideOf(round.label);
  const modelPick = guessOf(round.p);
  score.you += pick === truth;
  score.model += modelPick === truth;

  $$(".pick").forEach((b) => { b.disabled = true; b.classList.toggle("chosen", b.dataset.pick === pick); });
  $("#answer").innerHTML = `It's <span class="${COLORS[truth].text}">${truth === TAYLOR ? "Taylor Swift" : SUN_TZU}</span>.`;
  $("#you-said").innerHTML = `${named(pick)} ${mark(pick === truth)}`;
  $("#model-said").innerHTML = `${named(modelPick)}, ${percent(confidence(round.p))} sure ${mark(modelPick === truth)}`;
  $("#next span").textContent = index === rounds.length - 1 ? "See the score" : "Next";
  $("#reveal").hidden = false;
  marks($("#reveal"));
  showScore();
  redraw();

  bar($("#bar"), 0.5);
  animateBar($("#bar"), 0.5, round.p);
  $("#next").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

export function next() {
  if (!answered) return;
  index += 1;
  if (index < rounds.length) return showRound();

  $("#line").hidden = $("#picks").hidden = $("#reveal").hidden = true;
  $("#round").textContent = "";
  const verdict = score.you > score.model ? "You beat the model." : score.you === score.model ? "Tie." : "The model wins.";
  $("#final").textContent = `You ${score.you}, model ${score.model}. ${verdict}`;
  $("#end-note").textContent = `On ${stats.tested} random lines it had never seen, the model got ${percent(stats.accuracy)} right. Now try to fool it.`;
  $("#end").hidden = false;
  redraw();
}

export function restart() {
  index = 0;
  score = { you: 0, model: 0 };
  showRound();
}
