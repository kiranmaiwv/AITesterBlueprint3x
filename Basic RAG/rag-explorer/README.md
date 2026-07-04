# RAG Explorer

A simple Retrieval-Augmented Generation demo app that shows the full RAG flow:
- ingest a document or Confluence page
- split text into chunks
- embed chunks in ChromaDB
- retrieve the top relevant chunks
- answer questions with an LLM-backed result

## Project structure

- `client/` - React + Vite frontend
- `server/` - Express backend and Python ingestion/query pipeline
- `data/` - document folder used by default when no file is uploaded

## Setup

### 1. Install backend dependencies

```bash
cd "Basic RAG/rag-explorer/server"
npm install
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd "Basic RAG/rag-explorer/client"
npm install
```

### 3. Create your `.env` file

Copy `server/.env.example` to `server/.env` and fill in your values.

## Environment variables

The backend supports these environment variables:

```env
PORT=4000
PYTHON_BIN=/usr/local/bin/python3
PDF_PATH=../data/YourDocument.pdf
GROQ_API_KEY=
CONFLUENCE_USERNAME=
CONFLUENCE_API_TOKEN=
```

### Variable details

- `PORT` - port for the Express server (default: `4000`)
- `PYTHON_BIN` - optional Python interpreter used to run `rag_pipeline.py`
- `PDF_PATH` - optional path to a PDF file to ingest by default. If unset, the backend will search `Basic RAG/data` for the first PDF.
- `GROQ_API_KEY` - optional API key for Groq chat completion. If unset, answers are generated from a fallback static response.
- `CONFLUENCE_USERNAME` / `CONFLUENCE_API_TOKEN` - optional credentials for private Confluence pages. If set, ingesting a Confluence URL will use Basic auth.

## How to run

### Backend

```bash
cd "Basic RAG/rag-explorer/server"
node server.js
```

### Frontend

```bash
cd "Basic RAG/rag-explorer/client"
npm run dev
```

Then open the browser at the URL shown by Vite.

## Ingestion modes

The app supports:
- uploading a PDF file
- uploading a Word `.doc` or `.docx` file
- ingesting a Confluence page by URL
- default PDF ingestion from `Basic RAG/data`

## Notes

- The backend writes temporary text files only during ingestion and removes them after the Python pipeline runs.
- `Basic RAG/rag-explorer/server/rag_pipeline.py` uses ChromaDB plus a sentence-transformer embedding model.
- If `GROQ_API_KEY` is omitted, the query route still works but returns a simple grounded fallback answer.
