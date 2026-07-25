import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { cosineSimilarity } from "./embeddings";

export interface Chunk {
  text: string;
  embedding: number[];
  metadata: Record<string, string>;
}

const EMBEDDINGS_PATH = join(process.cwd(), "embeddings.json");

let chunks: Chunk[] | null = null;

function loadChunks(): Chunk[] {
  if (chunks) return chunks;
  if (!existsSync(EMBEDDINGS_PATH)) {
    console.warn("embeddings.json not found. Run `npm run ingest` first.");
    return (chunks = []);
  }
  chunks = JSON.parse(readFileSync(EMBEDDINGS_PATH, "utf-8")) as Chunk[];
  return chunks;
}

export function searchSimilar(queryEmbedding: number[], topK = 5): Chunk[] {
  const all = loadChunks();
  const scored = all
    .map((c) => ({ chunk: c, score: cosineSimilarity(queryEmbedding, c.embedding) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
  return scored.map((s) => s.chunk);
}

export function chunkCount(): number {
  return loadChunks().length;
}
