import { $, sideOf, guessOf, confidence, percent, named } from "./common.js";
import { loadEmbedder, chanceOfTaylor } from "./model.js";
import { bar } from "./sketch.js";

const FAILED = "The model didn't load. Check your connection and reload the page.";
let latest = 0;
let ready = false;

export function listTraps(traps) {
  $("#tries").innerHTML = traps.map((t) => `
    <li><button class="sketch" data-side="${sideOf(t.label)}" data-try="${t.text.replaceAll('"', "&quot;")}">
      <span>${t.text}<small>really ${t.label}</small></span>
    </button></li>`).join("");
}

export async function openFool() {
  $("#input").focus();
  try {
    await loadEmbedder();
    ready = true;
    await update();
  } catch {
    $("#live-model").textContent = FAILED;
  }
}

function fitToText(input) {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
  document.dispatchEvent(new Event("redraw"));
}

export async function update() {
  fitToText($("#input"));
  const text = $("#input").value.trim();
  const ticket = ++latest;
  if (!text) {
    bar($("#live-bar"), 0.5);
    if (ready) $("#live-model").textContent = "Start typing.";
    return;
  }
  try {
    const p = await chanceOfTaylor(text);
    if (ticket !== latest) return;
    bar($("#live-bar"), p);
    $("#live-model").innerHTML = `The model says ${named(guessOf(p))}, ${percent(confidence(p))} sure.`;
  } catch {
    $("#live-model").textContent = FAILED;
  }
}
