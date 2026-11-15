import { readFileSync } from "node:fs";
import rough from "roughjs/bundled/rough.esm.js";

const gen = rough.generator();
const svg = readFileSync(0, "utf8");
let seed = 1;

const attrs = (s) => Object.fromEntries([...s.matchAll(/([\w:-]+)='([^']*)'|([\w:-]+)="([^"]*)"/g)]
  .map((m) => (m[1] ? [m[1], m[2]] : [m[3], m[4]])));

const bbox = (nums) => {
  const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
  return Math.min(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
};

const roundedRect = (x, y, w, h, r) => {
  r = Math.min(r, w / 2, h / 2);
  return `M${x + r},${y} H${x + w - r} A${r},${r} 0 0 1 ${x + w},${y + r} V${y + h - r} A${r},${r} 0 0 1 ${x + w - r},${y + h} `
    + `H${x + r} A${r},${r} 0 0 1 ${x},${y + h - r} V${y + r} A${r},${r} 0 0 1 ${x + r},${y} Z`;
};

function options(a, size) {
  const fill = a.fill ?? "black";
  const white = /^(white|#fff(fff)?)$/i.test(fill);
  const o = {
    seed: seed++, roughness: 1.1, bowing: 1,
    stroke: a.stroke ?? "none", strokeWidth: Number(a["stroke-width"] ?? 1),
  };
  if (fill !== "none") {
    o.fill = fill;
    o.fillStyle = a["data-fill"] ?? (white || size < 34 ? "solid" : "hachure");
    o.hachureGap = 7; o.fillWeight = 2.2; o.hachureAngle = -41;
  }
  if (a["stroke-dasharray"]) o.strokeLineDash = a["stroke-dasharray"].split(/[ ,]+/).map(Number);
  return o;
}

function draw(tag, a) {
  const n = (k) => Number(a[k] ?? 0);
  if (tag === "rect") {
    const [x, y, w, h] = [n("x"), n("y"), n("width"), n("height")];
    const o = options(a, Math.min(w, h));
    return n("rx") ? gen.path(roundedRect(x, y, w, h, n("rx")), o) : gen.rectangle(x, y, w, h, o);
  }
  if (tag === "circle") return gen.circle(n("cx"), n("cy"), 2 * n("r"), options(a, 2 * n("r")));
  if (tag === "line") return gen.line(n("x1"), n("y1"), n("x2"), n("y2"), options({ ...a, fill: "none" }, 0));
  const nums = (a.d.match(/-?\d*\.?\d+/g) ?? []).map(Number);
  return gen.path(a.d, options(a, bbox(nums)));
}

const keep = ["opacity", "fill-opacity"];
const out = svg.replace(/<(rect|circle|line|path)\b([^>]*?)\/>/g, (_, tag, body) => {
  const a = attrs(body);
  const extra = keep.filter((k) => a[k]).map((k) => `${k}='${a[k]}'`).join(" ");
  return gen.toPaths(draw(tag, a)).map((p) =>
    `<path d='${p.d}' stroke='${p.stroke}' stroke-width='${p.strokeWidth}' fill='${p.fill ?? "none"}' `
    + `stroke-linecap='round' stroke-linejoin='round' ${extra}/>`).join("");
});
process.stdout.write(out);
