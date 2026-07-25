import { streamText } from "ai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { embedTexts } from "@/lib/embeddings";
import { searchSimilar, chunkCount } from "@/lib/vector-store";

const groq = createOpenAICompatible({
  name: "groq",
  baseURL: "https://api.groq.com/openai/v1",
  apiKey: process.env.GROQ_API_KEY,
});

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();
  const question = messages[messages.length - 1]?.content;

  if (!question || chunkCount() === 0) {
    return streamText({
      model: groq("llama-3.1-8b-instant"),
      messages: [
        {
          role: "system",
          content:
            chunkCount() === 0
              ? "The knowledge base has not been loaded yet. Ask the admin to run `npm run ingest` first."
              : "You are a helpful assistant.",
        },
        { role: "user", content: String(question) },
      ],
    }).toDataStreamResponse();
  }

  // 1. Embed the user's question
  const [queryEmbedding] = await embedTexts([String(question)]);

  // 2. Retrieve top 5 similar chunks
  const similar = searchSimilar(queryEmbedding!, 5);
  const context = similar.map((c) => c.text).join("\n\n---\n\n");

  // 3. Build the RAG prompt (matching the LangFlow pipeline)
  const systemPrompt = `Your task will be to prepare a proper answer for whatever the user has asked and whatever context you get from the knowledge base.

User query ${question}
Context ${context}`;

  return streamText({
    model: groq("llama-3.1-8b-instant"),
    system: systemPrompt,
    messages,
    temperature: 0.1,
  }).toDataStreamResponse();
}
