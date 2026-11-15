const TRANSFORMERS = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2";
const EMBEDDER = "Xenova/all-MiniLM-L6-v2";

let weights;
let embedder;

export async function loadWeights() {
  weights = await (await fetch("model.json")).json();
  return weights;
}

export async function loadEmbedder() {
  if (!embedder) {
    const { pipeline } = await import(TRANSFORMERS);
    embedder = await pipeline("feature-extraction", EMBEDDER);
  }
  return embedder;
}

export async function chanceOfTaylor(text) {
  const embed = await loadEmbedder();
  const { data } = await embed(text, { pooling: "mean", normalize: true });
  let z = weights.intercept;
  for (let k = 0; k < weights.coef.length; k++) z += data[k] * weights.coef[k];
  return 1 / (1 + Math.exp(-z));
}
