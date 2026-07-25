import { readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { parse } from "url";

const CSV_PATH = join(import.meta.dirname!, "../../Shopify_TestCases_1000.csv");
const OUT_PATH = join(import.meta.dirname!, "..", "embeddings.json");

interface Chunk {
  text: string;
  embedding: number[];
  metadata: Record<string, string>;
}

function parseCSV(text: string): Record<string, string>[] {
  const lines = text.trim().split("\n");
  const headers = parseCSVLine(lines[0]!);
  return lines.slice(1).map((line) => {
    const fields = parseCSVLine(line);
    const row: Record<string, string> = {};
    headers.forEach((h, i) => (row[h] = fields[i] ?? ""));
    return row;
  });
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (const ch of line) {
    if (ch === '"') { inQuotes = !inQuotes; continue; }
    if (ch === "," && !inQuotes) { result.push(current.trim()); current = ""; continue; }
    current += ch;
  }
  result.push(current.trim());
  return result;
}

function chunkRow(row: Record<string, string>): string[] {
  const text =
    `TID: ${row.TID}\n` +
    `Scenario: ${row.Scenario}\n` +
    `Description: ${row["TestCase Description"]}\n` +
    `PreCondition: ${row.PreCondition}\n` +
    `TestSteps: ${row.TestSteps}\n` +
    `ExpectedResult: ${row["Expected Result"]}\n` +
    `Priority: ${row.Priority}\n` +
    `Is Automated: ${row["Is Automated"]}`;

  // Chunk size = 1000, overlap = 200 (matching LangFlow pipeline)
  const chunkSize = 1000;
  const overlap = 200;
  const chunks: string[] = [];
  let i = 0;
  while (i < text.length) {
    chunks.push(text.slice(i, i + chunkSize));
    i += chunkSize - overlap;
  }
  return chunks.length ? chunks : [text];
}

async function embedTexts(texts: string[]): Promise<number[][]> {
  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) {
    console.error("❌ MISTRAL_API_KEY environment variable is required");
    process.exit(1);
  }

  // Mistral embed supports batch requests
  const results: number[][] = [];
  const batchSize = 20;
  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    console.log(`  Embedding batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(texts.length / batchSize)} (${batch.length} texts)...`);
    const res = await fetch("https://api.mistral.ai/v1/embeddings", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({ model: "mistral-embed", input: batch }),
    });
    if (!res.ok) {
      const err = await res.text();
      console.error(`❌ MistralAI API error: ${err}`);
      process.exit(1);
    }
    const json = await res.json();
    results.push(...json.data.map((d: { embedding: number[] }) => d.embedding));
  }
  return results;
}

async function main() {
  console.log("📄 Reading CSV...");
  const csv = readFileSync(CSV_PATH, "utf-8");
  const rows = parseCSV(csv);
  console.log(`  Found ${rows.length} rows`);

  console.log("✂️  Chunking rows...");
  const textChunks: { text: string; metadata: Record<string, string> }[] = [];
  for (const row of rows) {
    const texts = chunkRow(row);
    for (const t of texts) {
      textChunks.push({ text: t, metadata: { tid: row.TID ?? "", scenario: row.Scenario ?? "", priority: row.Priority ?? "" } });
    }
  }
  console.log(`  Created ${textChunks.length} chunks`);

  console.log("🔮 Generating embeddings via MistralAI...");
  const embeddings = await embedTexts(textChunks.map((c) => c.text));

  const chunks: Chunk[] = textChunks.map((c, i) => ({
    text: c.text,
    embedding: embeddings[i]!,
    metadata: c.metadata,
  }));

  writeFileSync(OUT_PATH, JSON.stringify(chunks));
  console.log(`✅ Saved ${chunks.length} chunks to embeddings.json`);
}

main().catch((err) => {
  console.error("❌", err);
  process.exit(1);
});
