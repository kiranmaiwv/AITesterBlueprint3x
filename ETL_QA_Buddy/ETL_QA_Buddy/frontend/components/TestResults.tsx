"use client";

import { useState } from "react";

interface TestResult {
  name: string;
  nodeid?: string;
  outcome: string;
  message: string;
}

interface AllResults {
  summary: { total: number; passed: number; failed: number };
  tests: TestResult[];
  raw_output?: string;
}

export default function TestResults({ backendUrl }: { backendUrl: string }) {
  const [results, setResults] = useState<AllResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runAll = async () => {
    setLoading(true);
    setError("");
    setResults(null);
    try {
      const res = await fetch(`${backendUrl}/run-all-tests`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data);
    } catch (e: any) {
      setError("Could not reach backend. Is it running on " + backendUrl + " ?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="full-width panel">
      <h2>
        <span className="dot" /> Full Test Suite Results
      </h2>
      <div className="btn-row">
        <button className="btn" onClick={runAll} disabled={loading}>
          {loading ? "Running…" : "Run All Tests"}
        </button>
      </div>
      {error && <div className="hint">{error}</div>}

      {results && (
        <>
          <div className="summary-pills">
            <span className="pill total">Total: {results.summary.total}</span>
            <span className="pill passed">Passed: {results.summary.passed}</span>
            <span className="pill failed">Failed: {results.summary.failed}</span>
          </div>
          <table className="results">
            <thead>
              <tr>
                <th>Test</th>
                <th>Status</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {results.tests.map((t) => (
                <tr key={t.nodeid || t.name}>
                  <td>{t.name}</td>
                  <td>
                    <span
                      className={`status-badge ${
                        t.outcome === "passed" ? "pass" : "fail"
                      }`}
                    >
                      {t.outcome === "passed" ? "PASS" : "FAIL"}
                    </span>
                  </td>
                  <td className="msg">{t.message || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
