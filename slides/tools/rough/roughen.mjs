import { readFileSync } from "node:fs";
import rough from "roughjs/bundled/rough.esm.js";

const gen = rough.generator();
const svg = readFileSync(0, "utf8");
const width = Number(svg.match(/viewBox=['"][\d.-]+ [\d.-]+ ([\d.]+)/)?.[1] ?? 1000);
const scale = (Number(process.argv[2] ?? 1) * width) / 1000;
let seed = 1;
const wobble = (thin) => (thin < 15 * scale ? 0.15 : thin < 40 * scale ? 0.5 : 1.2);

const attrs = (s) => {
  const a = Object.fromEntries([...s.matchAll(/([\w:-]+)='([^']*)'|([\w:-]+)="([^"]*)"/g)]
    .map((m) => (m[1] ? [m[1], m[2]] : [m[3], m[4]])));
  for (const rule of (a.style ?? "").split(";")) {
    const [k, v] = rule.split(":").map((t) => t?.trim());
    if (k && v) a[k] = v;
  }
  return a;
};

const size = (nums) => {
  const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
  return Math.min(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
};

const pill = (x, y, w, h) => {
  const r = h / 2;
  return `M${x + r},${y} H${x + w - r} A${r},${r} 0 0 1 ${x + w - r},${y + h} H${x + r} A${r},${r} 0 0 1 ${x + r},${y} Z`;
};

function options(a, extent, kind) {
  const fill = a.fill ?? "black";
  const o = {
    seed: seed++, roughness: wobble(extent), bowing: 1, maxRandomnessOffset: 2 * scale,
    stroke: a.stroke ?? "none", strokeWidth: Number(a["stroke-width"] ?? 1),
  };
  if (fill !== "none" && !fill.startsWith("url")) {
    o.fill = fill;
    const plain = /^(white|#fff(fff)?)$/i.test(fill) || kind === "box" || extent < 40 * scale;
    o.fillStyle = a["data-fill"] ?? (plain ? "solid" : "hachure");
    o.hachureGap = 4 * scale; o.fillWeight = 1.5 * scale; o.hachureAngle = -41;
  }
  const dash = a["stroke-dasharray"];
  if (dash && dash !== "none") o.strokeLineDash = dash.split(/[ ,]+/).map(Number);
  return o;
}

function draw(tag, a) {
  const n = (k) => Number(a[k] ?? 0);
  if (tag === "rect") {
    const [x, y, w, h] = [n("x"), n("y"), n("width"), n("height")];
    if (n("rx") >= h / 2 - 0.5) return gen.path(pill(x, y, w, h), { ...options(a, h, "box"), roughness: wobble(h) });
    return gen.rectangle(x, y, w, h, { ...options(a, Math.min(w, h), a["data-fill"] ? "shape" : "box"),
      roughness: wobble(Math.min(w, h)) });
  }
  if (tag === "circle") return gen.circle(n("cx"), n("cy"), 2 * n("r"), options(a, 2 * n("r")));
  if (tag === "line") {
    const length = Math.hypot(n("x2") - n("x1"), n("y2") - n("y1"));
    return gen.line(n("x1"), n("y1"), n("x2"), n("y2"), options({ ...a, fill: "none" }, length));
  }
  const nums = (a.d.match(/-?\d*\.?\d+(e-?\d+)?/g) ?? []).map(Number);
  const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
  const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
  return gen.path(a.d, { ...options(a, span < 40 * scale ? 0 : size(nums)), roughness: wobble(Math.min(span, size(nums) || span)) });
}

const keep = ["opacity", "fill-opacity", "stroke-opacity", "clip-path", "transform", "stroke-dasharray"];
const out = svg.replace(/<(rect|circle|line|path)\b([^>]*?)\/>/g, (whole, tag, body) => {
  const a = attrs(body);
  if (a.id || (tag === "path" && !a.d)) return whole;
  const extra = keep.filter((k) => a[k]).map((k) => `${k}="${a[k]}"`).join(" ");
  return gen.toPaths(draw(tag, a)).map((p) =>
    `<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill ?? "none"}" `
    + `stroke-linecap="round" stroke-linejoin="round" ${extra}/>`).join("");
});
process.stdout.write(out);
