"""Query engine: embed → Qdrant search → build prompt."""

from qa_buddy.rag import vector_store as qdrant_client
from qa_buddy.config import config


SYSTEM_PROMPT = """You are **QA Buddy AI**, a senior QA engineering assistant for the company.
You have access to the company's test automation frameworks, test cases, JIRA bug history,
PRDs, meeting notes, and engineering knowledge base.

**Instructions:**
1. Answer based on the provided context. Do not make up information.
2. Cite sources using `[Source: filename | Folder: XX]` after each claim.
3. If you don't have enough context, say so.
4. Keep answers technical, actionable, and concise.
"""


def search(query: str, top_k: int = 4, source_filter: str = None) -> list[dict]:
    """Embed query and search Qdrant."""
    from qa_buddy.rag.embedder import embed
    vector = embed(query)
    return qdrant_client.search(vector, top_k=top_k, source_filter=source_filter)


def build_messages(query: str, chunks: list[dict], history: list[dict] = None) -> list[dict]:
    """Build message list for GROQ."""
    context_parts = []
    for i, c in enumerate(chunks):
        meta = c["metadata"]
        header = f"[Source {i+1} - {meta.get('file_path','unknown')} | Folder: {meta.get('folder_id','?')}]"
        context_parts.append(f"{header}\n```\n{c['content'][:2000]}\n```")

    context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for msg in history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": f"## Context\n{context}\n\n## Question\n{query}\n\n## Answer"})
    return messages
