#!/usr/bin/env python3
"""Seed Qdrant Cloud with local data files.
Run this locally (not on Vercel) to push embeddings to Qdrant Cloud."""

import os, sys, json
from pathlib import Path

# Add project root so qa_buddy is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from qa_buddy.rag.embedder import embed_batch
from qa_buddy.rag.vector_store import ensure_collection
from qa_buddy.config import config
from qdrant_client.models import PointStruct
from qa_buddy.utils.chunker import chunk_file


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FOLDER_MAP = {
    "01_selenium_repo": "01",
    "02_playwright_repo": "02",
    "03_test_cases": "03",
    "04_jira_tickets": "04",
    "05_company_pdfs": "05",
    "06_figma_designs": "06",
    "07_meeting_notes": "07",
    "08_lucid_charts": "08",
    "09_prd_srs_docs": "09",
    "10_jenkins_logs": "10",
}


def ingest_folder(folder_name: str, folder_id: str):
    folder_path = DATA_DIR / folder_name
    if not folder_path.exists():
        print(f"  Skipping {folder_name}: not found")
        return 0

    files = sorted(folder_path.rglob("*"))
    text_files = [f for f in files if f.is_file() and f.suffix in (".py", ".java", ".js", ".ts", ".csv", ".xlsx", ".pdf", ".md", ".txt", ".log", ".json", ".xml")]

    if not text_files:
        print(f"  No files in {folder_name}")
        return 0

    all_chunks = []
    for fpath in text_files:
        try:
            chunks = chunk_file(fpath, folder_id, folder_name)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"    Error reading {fpath.name}: {e}")

    if not all_chunks:
        return 0

    print(f"  Chunked into {len(all_chunks)} pieces, embedding...")

    texts = [c["content"] for c in all_chunks]
    vectors = embed_batch(texts)

    points = []
    for i, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        points.append(PointStruct(
            id=abs(hash(f"{folder_id}:{chunk['content'][:50]}:{i}")) % (2**63),
            vector=vector,
            payload={
                "content": chunk["content"],
                "file_path": chunk["file_path"],
                "folder_id": folder_id,
                "source": folder_name,
                "language": chunk.get("language", "text"),
            },
        ))

    ensure_collection()
    from qa_buddy.rag.vector_store import upsert_points
    upsert_points(points)
    print(f"  ✓ {len(points)} points upserted to Qdrant Cloud")
    return len(points)


def main():
    print("=== QA Buddy AI — Seed Qdrant Cloud ===\n")

    if not config.is_qdrant_configured:
        print("❌ QDRANT_URL / QDRANT_API_KEY not set. Set them in .env")
        sys.exit(1)

    total = 0
    for folder_name, folder_id in FOLDER_MAP.items():
        print(f"[{folder_id}] {folder_name}...")
        count = ingest_folder(folder_name, folder_id)
        total += count

    print(f"\n=== Done! {total} total chunks seeded to Qdrant Cloud ===")


if __name__ == "__main__":
    main()
