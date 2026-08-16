"use client";

import { useState } from "react";

const EXAMPLES = [
  "Check all customer emails are unique",
  "Verify no NULL values in order total_amount",
  "Ensure all order customer_ids exist in customers table",
  "Check ETL log has no failed pipeline runs",
  "Validate all product prices are greater than zero",
];

interface RunResult {
  passed: boolean;
  output: string;
  error: string;
}

export default function TestGenerator({ backendUrl }: { backendUrl: string }) {
  const [description, setDescription] = useState("");
  const [testCode, setTestCode] = useState("");
  const [genLoading, setGenLoading] = useState(false);
  const [runLoading, setRunLoading] = useState(false);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [error, setError] = useState("");

  const generate = async () => {
    if (!description.trim()) return;
    setGenLoading(true);
    setError("");
    setRunResult(null);
    setTestCode("");
    try {
      const res = await fetch(`${backendUrl}/generate-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTestCode(data.test_code || "");
    } catch (e: any) {
      setError("Could not reach backend at " + backendUrl + ".");
    } finally {
      setGenLoading(false);
    }
  };

  const runTest = async () => {
    if (!testCode.trim()) return;
    setRunLoading(true);
    setError("");
    setRunResult(null);
    try {
      const res = await fetch(`${backendUrl}/run-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test_code: testCode }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRunResult(data);
    } catch (e: any) {
      setError("Could not reach backend at " + backendUrl + ".");
    } finally {
      setRunLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>
        <span className="dot" /> AI Test Generator
      </h2>
      <textarea
        placeholder="Describe your ETL test in plain English…"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="chips">
        {EXAMPLES.map((ex) => (
          <span key={ex} className="chip" onClick={() => setDescription(ex)}>
            {ex}
          </span>
        ))}
      </div>
      <div className="btn-row">
        <button className="btn" onClick={generate} disabled={genLoading}>
          {genLoading ? "Generating…" : "Generate Test"}
        </button>
        <button
          className="btn secondary"
          onClick={runTest}
          disabled={runLoading || !testCode}
        >
          {runLoading ? "Running…" : "Run This Test"}
        </button>
      </div>

      {error && <div className="hint">{error}</div>}

      {testCode && (
        <>
          <pre className="code">{testCode}</pre>
          <p className="hint">
            Review the generated pytest function, then click “Run This Test”.
          </p>
        </>
      )}

      {runResult && (
        <div className={`result-box ${runResult.passed ? "pass" : "fail"}`}>
          <span className={`status-badge ${runResult.passed ? "pass" : "fail"}`}>
            {runResult.passed ? "PASS" : "FAIL"}
          </span>
          <pre className="code" style={{ marginTop: 10 }}>
            {runResult.output || runResult.error || "(no output)"}
          </pre>
        </div>
      )}
    </div>
  );
}
