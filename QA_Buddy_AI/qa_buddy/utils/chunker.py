"""Chunking utilities for seed script."""

import os


def chunk_file(filepath, folder_id, folder_name):
    """Read a file and return chunks based on its type."""
    ext = os.path.splitext(filepath)[1].lower()
    # Build relative path from the 'data' segment onward
    fp = str(filepath)
    idx = fp.find("/data/")
    if idx == -1:
        idx = fp.find("\\data\\")
    rel_path = fp[idx+1:] if idx != -1 else os.path.basename(fp)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    if not text.strip():
        return []

    # Code files: semantic by function/class
    if ext in (".py", ".java", ".js", ".ts"):
        return _chunk_code(text, rel_path, ext)

    # CSV: per row
    if ext == ".csv":
        return _chunk_csv(text, rel_path)

    # Markdown: per heading
    if ext == ".md":
        return _chunk_markdown(text, rel_path)

    # Default: sliding window
    return _chunk_sliding(text, rel_path, chunk_size=768, overlap=150)


def _chunk_code(text, rel_path, ext):
    import re
    chunks = []
    lines = text.split("\n")
    patterns = [re.compile(r"^\s*(async\s+)?def\s+\w+\s*\("), re.compile(r"^\s*class\s+\w+")]
    start = 0
    in_chunk = False
    for i, line in enumerate(lines):
        if any(p.match(line) for p in patterns):
            if in_chunk and i > start:
                content = "\n".join(lines[start:i])
                if content.strip():
                    chunks.append({"content": content, "file_path": rel_path, "language": ext.lstrip(".")})
                start = i
            in_chunk = True
    if start < len(lines):
        content = "\n".join(lines[start:])
        if content.strip():
            chunks.append({"content": content, "file_path": rel_path, "language": ext.lstrip(".")})
    if not chunks:
        chunks.append({"content": text, "file_path": rel_path, "language": ext.lstrip(".")})
    return chunks


def _chunk_csv(text, rel_path):
    chunks = []
    lines = text.split("\n")
    if len(lines) > 1:
        header = lines[0]
        for line in lines[1:]:
            if line.strip():
                chunks.append({"content": f"{header}\n{line}", "file_path": rel_path, "language": "csv"})
    if not chunks:
        chunks.append({"content": text, "file_path": rel_path, "language": "csv"})
    return chunks


def _chunk_markdown(text, rel_path):
    import re
    chunks = []
    lines = text.split("\n")
    pattern = re.compile(r"^#{2,4}\s+")
    start = 0
    heading = ""
    for i, line in enumerate(lines):
        if pattern.match(line):
            if heading:
                content = "\n".join(lines[start:i])
                if content.strip():
                    chunks.append({"content": content, "file_path": rel_path, "language": "markdown"})
                start = i
            heading = line.strip()
    if start < len(lines):
        content = "\n".join(lines[start:])
        if content.strip():
            chunks.append({"content": content, "file_path": rel_path, "language": "markdown"})
    if not chunks:
        chunks.append({"content": text, "file_path": rel_path, "language": "markdown"})
    return chunks


def _chunk_sliding(text, rel_path, chunk_size=768, overlap=150):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        content = text[start:end]
        if content.strip():
            chunks.append({"content": content, "file_path": rel_path, "language": "text"})
        start += chunk_size - overlap
    return chunks
