import os
import json
import sys
import re
import urllib.request
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

PDF_PATH = os.environ.get('PDF_PATH', '')
SOURCE_TYPE = os.environ.get('SOURCE_TYPE', 'pdf')
SOURCE_PATH = os.environ.get('SOURCE_PATH', '')
SOURCE_NAME = os.environ.get('SOURCE_NAME', 'document.txt')
DB_PATH = Path(__file__).resolve().parent / 'chroma_db'
COLLECTION_NAME = 'rag_explorer_docs'
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

client = chromadb.PersistentClient(path=str(DB_PATH))
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)


def split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def ingest_text_document(text, source_name):
    chunks = split_text(text)

    ids = [f'chunk-{i}' for i in range(len(chunks))]
    metadatas = [{'source': source_name, 'chunk_index': i} for i in range(len(chunks))]

    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return {
        'status': 'ingested',
        'source': source_name,
        'chunks': len(chunks),
        'collection': COLLECTION_NAME,
    }


def ingest_pdf():
    if not PDF_PATH:
        raise SystemExit('No PDF path provided')

    if not os.path.exists(PDF_PATH):
        raise SystemExit(f'PDF not found: {PDF_PATH}')

    reader = PdfReader(PDF_PATH)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or '')
    text = '\n\n'.join(pages)
    return ingest_text_document(text, os.path.basename(PDF_PATH))


def ingest_source():
    if SOURCE_TYPE == 'text' and SOURCE_PATH:
        text = Path(SOURCE_PATH).read_text(encoding='utf-8', errors='ignore')
        return ingest_text_document(text, SOURCE_NAME or os.path.basename(SOURCE_PATH))
    return ingest_pdf()


def generate_answer(query, chunks):
    context = '\n\n'.join(chunk['chunk'] for chunk in chunks)
    api_key = os.environ.get('GROQ_API_KEY')

    if api_key:
        payload = {
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You answer questions using the provided document context. Be concise and grounded in the context.',
                },
                {
                    'role': 'user',
                    'content': f'Question: {query}\n\nContext:\n{context}',
                },
            ],
            'temperature': 0.2,
        }

        req = urllib.request.Request(
            'https://api.groq.com/openai/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
        except Exception:
            pass

    return (
        'The retrieved passages suggest the answer is grounded in the uploaded PRD context. '
        'Use the highlighted chunks above to verify the response.'
    )


def query_document(query):
    results = collection.query(query_texts=[query], n_results=4)
    documents = results.get('documents', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    distances = results.get('distances', [[]])[0]

    retrieved_chunks = [
        {
            'chunk': doc,
            'metadata': meta,
            'distance': dist,
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    return {
        'query': query,
        'retrieved_chunks': retrieved_chunks,
        'answer': generate_answer(query, retrieved_chunks),
    }


if __name__ == '__main__':
    if '--ingest' in sys.argv:
        print(json.dumps(ingest_source()))
    elif '--query' in sys.argv:
        query_text = ' '.join(sys.argv[sys.argv.index('--query') + 1:])
        print(json.dumps(query_document(query_text)))
    else:
        print(json.dumps({'status': 'noop'}))
