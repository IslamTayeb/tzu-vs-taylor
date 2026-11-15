import rough from "https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.esm.js";
import { COLORS, TAYLOR, SUN_TZU } from "./common.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const INK = COLORS.ink;
const RED = COLORS[TAYLOR].line;
const CYAN = COLORS[SUN_TZU].fill;

function svgIn(parent, { className, viewBox, onTop = false } = {}) {
  const svg = document.createElementNS(SVG_NS, "svg");
  if (className) svg.classList.add(className);
  if (viewBox) svg.setAttribute("viewBox", viewBox);
  onTop ? parent.append(svg) : parent.prepend(svg);
  return svg;
}

export function box(el, { fill, stroke = INK, seed = 1 }) {
  el.querySelectorAll(":scope > svg").forEach((svg) => svg.remove());
  const { width: w, height: h } = el.getBoundingClientRect();
  if (!w) return;
  if (fill) {
    const back = svgIn(el, { className: "fillsvg" });
    back.append(rough.svg(back).rectangle(5, 5, w - 10, h - 10, { seed, fill, fillStyle: "solid", stroke: "none" }));
  }
  const front = svgIn(el, { onTop: true });
  const width = stroke === INK ? 1.6 : 2.2;
  front.append(rough.svg(front).rectangle(4, 4, w - 8, h - 8, { seed, stroke, strokeWidth: width, roughness: 1.2, bowing: 1 }));
}

export function bar(el, pTaylor) {
  el.innerHTML = "";
  const w = el.clientWidth, h = el.clientHeight;
  const svg = svgIn(el);
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  const rc = rough.svg(svg);
  const split = Math.min(w - 2, Math.max(2, pTaylor * w));
  const hatch = { seed: 7, stroke: "none", fillStyle: "hachure", hachureGap: 4, fillWeight: 2 };
  if (split > 3) svg.append(rc.rectangle(2, 2, split - 2, h - 4, { ...hatch, fill: RED }));
  if (split < w - 3) svg.append(rc.rectangle(split, 2, w - split - 2, h - 4, { ...hatch, fill: CYAN, hachureAngle: 41 }));
  svg.append(rc.rectangle(2, 2, w - 4, h - 4, { seed: 7, stroke: INK, strokeWidth: 1.6 }));
  svg.append(rc.line(w / 2, -5, w / 2, h + 5, { seed: 3, stroke: INK, strokeWidth: 1.2, roughness: 0.8 }));
}

export function animateBar(el, from, to, ms = 700) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return bar(el, to);
  const start = performance.now();
  const frame = (now) => {
    const t = Math.min(1, (now - start) / ms);
    bar(el, from + (to - from) * (1 - (1 - t) ** 3));
    if (t < 1 && el.dataset.target === String(to)) requestAnimationFrame(frame);
  };
  el.dataset.target = String(to);
  requestAnimationFrame(frame);
}

export function doodle(el) {
  el.innerHTML = "";
  const svg = svgIn(el, { viewBox: "0 0 44 44" });
  const rc = rough.svg(svg);
  const line = { stroke: INK, strokeWidth: 1.3, roughness: 1.1, seed: 5 };
  const hatched = (fill) => ({ ...line, fill, fillStyle: "hachure", hachureGap: 2.5, fillWeight: 1 });
  const parts = el.dataset.doodle === "guitar"
    ? [
        rc.circle(22, 33, 20, hatched(RED)),
        rc.circle(22, 21, 15, hatched(RED)),
        rc.circle(22, 28, 5, { ...line, fill: "#fff", fillStyle: "solid" }),
        rc.rectangle(20.5, 3, 3, 15, line),
        rc.rectangle(18.5, 0, 7, 4, line),
      ]
    : [
        rc.polygon([[22, 1], [25, 7], [25, 29], [19, 29], [19, 7]], hatched(CYAN)),
        rc.rectangle(12, 29, 20, 3.5, { ...line, fill: INK, fillStyle: "solid" }),
        rc.rectangle(20.5, 33, 3, 7, line),
        rc.circle(22, 42, 4, line),
      ];
  svg.append(...parts);
}

export function marks(root = document) {
  root.querySelectorAll(".mark:empty").forEach((el) => {
    const svg = svgIn(el, { viewBox: "0 0 24 24" });
    const rc = rough.svg(svg);
    const ok = el.dataset.ok === "true";
    const stroke = { stroke: ok ? "#3b7d4a" : "#b4412f", strokeWidth: 2.6, roughness: 1, seed: ok ? 2 : 4 };
    if (ok) svg.append(rc.linearPath([[4, 13], [10, 19], [21, 5]], stroke));
    else svg.append(rc.line(5, 5, 19, 19, stroke), rc.line(19, 5, 5, 19, stroke));
  });
}
