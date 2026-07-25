#!/usr/bin/env python3
"""QA Buddy AI — Vercel serverless function."""

import sys, os, json, tempfile
from pathlib import Path

# ⚠ CRITICAL: Set TMPDIR before ANY library import (ONNX writes temp files)
tempfile.tempdir = "/tmp"
os.environ.setdefault("TMPDIR", "/tmp")
os.environ.setdefault("TEMP", "/tmp")
os.environ.setdefault("TMP", "/tmp")
os.environ.setdefault("ORT_TMPDIR", "/tmp/ort")
os.environ.setdefault("HF_HOME", "/tmp/hf")
os.environ.setdefault("HF_HUB_CACHE", "/tmp/hf/hub")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/cache")
os.environ.setdefault("FASTEMP_CACHE", "/tmp/fastembed")
for d in ["/tmp/ort", "/tmp/hf", "/tmp/hf/hub", "/tmp/cache", "/tmp/fastembed"]:
    try: os.makedirs(d, exist_ok=True)
    except: pass

# Make qa_buddy importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# Helper: read env with .env fallback
# ---------------------------------------------------------------------------
def getenv(key, default=""):
    val = os.environ.get(key)
    if val:
        return val
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    return default


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    from qa_buddy.config import config as cfg
    return jsonify({
        "status": "ok",
        "groq": cfg.is_groq_configured,
        "qdrant": cfg.is_qdrant_configured,
        "jira": cfg.is_jira_configured,
        "embedder": True,
    })


# ---------------------------------------------------------------------------
# Chat (SSE streaming)
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    from qa_buddy.rag.query_engine import search, build_messages
    from qa_buddy.connectors.groq_client import GroqClient

    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    history = data.get("history", [])

    if not query:
        return jsonify({"error": "query is required"}), 400

    def generate():
        try:
            # 1. Search Qdrant
            chunks = search(query, top_k=4)

            # 2. Build messages
            messages = build_messages(query, chunks, history)

            # 3. Stream from GROQ
            groq = GroqClient()
            full = ""
            for token in groq.stream(messages):
                full += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 4. Send sources
            yield f"data: {json.dumps({'type': 'sources', 'content': chunks})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Sources / Ingestion
# ---------------------------------------------------------------------------
@app.route("/api/sources", methods=["GET"])
def list_sources():
    from qa_buddy.rag.vector_store import get_client
    from qa_buddy.config import config as cfg
    try:
        client = get_client()
        info = client.get_collection(cfg.QDRANT_COLLECTION)
        count = info.points_count
    except Exception:
        count = 0
    return jsonify({"sources": [
        {"name": "all_sources", "folder": "01-10", "doc_count": count, "last_indexed": None}
    ]})


@app.route("/api/sources/ingest", methods=["POST"])
def trigger_ingest():
    """Placeholder: real ingestion runs via a separate local script that pushes to Qdrant Cloud."""
    return jsonify({"status": "ok", "message": "Ingestion runs locally via scripts/seed_qdrant.py"})


# ---------------------------------------------------------------------------
# Settings (read-only on Vercel; update via env vars)
# ---------------------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def settings_get():
    return jsonify({
        "groq_key": "***" + getenv("GROQ_API_KEY")[-4:] if getenv("GROQ_API_KEY") else "",
        "groq_model": getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
        "jira_url": getenv("JIRA_URL"),
        "jira_email": getenv("JIRA_EMAIL"),
        "jira_jql": getenv("JIRA_JQL"),
        "qdrant_url": getenv("QDRANT_URL", "").split(".")[0] + "..." if getenv("QDRANT_URL") else "",
        "openai_configured": bool(getenv("OPENAI_API_KEY")),
    })


# ---------------------------------------------------------------------------
# JIRA test
# ---------------------------------------------------------------------------
@app.route("/api/jira/test", methods=["POST"])
def jira_test():
    from qa_buddy.connectors.jira_connector import JiraConnector

    data = request.get_json(force=True) or {}
    jql = data.get("jql") or getenv("JIRA_JQL")
    url = data.get("url") or getenv("JIRA_URL")
    email = data.get("email") or getenv("JIRA_EMAIL")
    token = data.get("token") or getenv("JIRA_API_TOKEN")

    if not all([url, email, token]):
        return jsonify({"error": "JIRA credentials not configured"}), 400

    base = url.split("/jira/")[0] if "/jira/" in url else url
    base = base.split("/browse/")[0] if "/browse/" in base else base
    connector = JiraConnector(base, email, token)
    result = connector.search_issues(jql, max_results=5)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Vercel handler
# ---------------------------------------------------------------------------
