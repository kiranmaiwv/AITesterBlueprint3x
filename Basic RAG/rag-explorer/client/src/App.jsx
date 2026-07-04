import { useState } from 'react';
import './App.css';

const API_BASE = 'http://localhost:4000/api';

function App() {
  const [status, setStatus] = useState('Ready to ingest');
  const [query, setQuery] = useState('What are the core goals of the product?');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sourceMode, setSourceMode] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [confluenceUrl, setConfluenceUrl] = useState('');

  const ingestSource = async () => {
    setLoading(true);
    setStatus(sourceMode === 'confluence' ? 'Fetching Confluence content...' : 'Ingesting document...');

    try {
      const formData = new FormData();
      if (sourceMode === 'upload' && selectedFile) {
        formData.append('file', selectedFile);
        formData.append('sourceType', 'upload');
      } else if (sourceMode === 'confluence' && confluenceUrl.trim()) {
        formData.append('confluenceUrl', confluenceUrl.trim());
        formData.append('sourceType', 'confluence');
      } else {
        formData.append('sourceType', 'pdf');
      }

      const response = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Ingestion failed');
      }

      const sourceLabel = selectedFile?.name || confluenceUrl.trim() || data.source || 'the selected source';
      setStatus(`Ingested ${data.chunks || 0} chunks from ${sourceLabel}`);
      setResult(null);
    } catch (error) {
      setStatus(`Ingestion failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runQuery = async () => {
    setLoading(true);
    setStatus('Retrieving top chunks and generating answer...');

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Query failed');
      }

      setResult(data);
      setStatus('Query complete');
    } catch (error) {
      setStatus(`Query failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero-card">
        <div>
          <p className="eyebrow">RAG Explorer</p>
          <h1>Visualize a simple retrieval-augmented generation flow</h1>
          <p className="subtext">
            Upload a PDF, Word document, or Confluence page, split it into chunks, embed it in
            Chroma, retrieve relevant passages, and answer questions with the context.
          </p>
        </div>
        <div className="status-pill">{status}</div>
      </header>

      <section className="step-flow">
        {[
          { label: 'PDF', detail: 'load document' },
          { label: 'Chunk', detail: 'split text' },
          { label: 'Embed', detail: 'Nomic vectors' },
          { label: 'Store', detail: 'ChromaDB' },
          { label: 'Retrieve', detail: 'top-4' },
          { label: 'Answer', detail: 'Groq LLM' },
        ].map((step, index) => (
          <div key={step.label} className="step-card">
            <div className="step-badge">{index + 1}</div>
            <div>
              <strong>{step.label}</strong>
              <p>{step.detail}</p>
            </div>
            {index < 5 && <div className="step-arrow">→</div>}
          </div>
        ))}
      </section>

      <section className="panel-grid">
        <div className="panel">
          <h2>1. Ingest a document</h2>
          <p>Choose a local file or a Confluence page URL to seed the retrieval index.</p>

          <div className="toggle-group" role="tablist" aria-label="Source type selector">
            <button
              type="button"
              className={`toggle-btn ${sourceMode === 'upload' ? 'active' : ''}`}
              onClick={() => setSourceMode('upload')}
            >
              Upload file
            </button>
            <button
              type="button"
              className={`toggle-btn ${sourceMode === 'confluence' ? 'active' : ''}`}
              onClick={() => setSourceMode('confluence')}
            >
              Confluence URL
            </button>
          </div>

          {sourceMode === 'upload' ? (
            <>
              <input
                className="file-input"
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
              <p className="helper">
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Upload a PDF or Word document.'}
              </p>
            </>
          ) : (
            <>
              <input
                className="url-input"
                type="url"
                value={confluenceUrl}
                placeholder="https://your-company.atlassian.net/wiki/spaces/SPACE/pages/12345/Page"
                onChange={(event) => setConfluenceUrl(event.target.value)}
              />
              <p className="helper">Paste a Confluence page URL to fetch and ingest its text.</p>
            </>
          )}

          <button onClick={ingestSource} disabled={loading}>
            {loading ? 'Working...' : 'Ingest source'}
          </button>
        </div>

        <div className="panel">
          <h2>2. Query the document</h2>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows="4"
          />
          <button onClick={runQuery} disabled={loading}>
            {loading ? 'Searching...' : 'Run RAG query'}
          </button>
        </div>
      </section>

      <section className="panel-grid lower-grid">
        <div className="panel">
          <h2>3. Retrieval pipeline</h2>
          {result ? (
            <div className="chunk-list">
              {result.retrieved_chunks?.map((chunk, index) => (
                <article key={index} className="chunk-card">
                  <strong>Chunk {index + 1}</strong>
                  <p>{chunk.chunk}</p>
                  <small>Distance: {chunk.distance?.toFixed(3)}</small>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty">No retrieval results yet. Run a query to see the top 4 chunks.</p>
          )}
        </div>

        <div className="panel">
          <h2>4. RAG answer</h2>
          {result ? (
            <div>
              <p className="answer-label">Question</p>
              <p>{result.query}</p>
              <p className="answer-label">Generated answer</p>
              <p>{result.answer}</p>
              <p className="answer-label">Retrieved context</p>
              <p>{result.retrieved_chunks?.[0]?.chunk}</p>
            </div>
          ) : (
            <p className="empty">The generated answer will appear here after retrieval.</p>
          )}
        </div>
      </section>
    </div>
  );
}

export default App;
