export const $ = (selector) => document.querySelector(selector);
export const $$ = (selector) => [...document.querySelectorAll(selector)];

export const TAYLOR = "Taylor";
export const SUN_TZU = "Sun Tzu";

export const COLORS = {
  ink: "#2e3440",
  [TAYLOR]: { line: "#be616a", tint: "#f1d6d9", text: "t-ink" },
  [SUN_TZU]: { line: "#4f8584", fill: "#8fbbba", tint: "#d6e8e7", text: "s-ink" },
};

export const percent = (x) => `${Math.round(x * 100)}%`;
export const sideOf = (label) => (label.startsWith("Sun") ? SUN_TZU : TAYLOR);
export const guessOf = (pTaylor) => (pTaylor >= 0.5 ? TAYLOR : SUN_TZU);
export const confidence = (pTaylor) => Math.max(pTaylor, 1 - pTaylor);
export const named = (who) => `<b class="${COLORS[who].text}">${who}</b>`;
