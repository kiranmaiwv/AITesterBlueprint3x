"use client";

import { useEffect, useState } from "react";

interface Column {
  name: string;
  type: string;
  not_null: boolean;
  primary_key: boolean;
}

interface Table {
  table: string;
  columns: Column[];
  row_count: number;
}

export default function SampleSchema({ backendUrl }: { backendUrl: string }) {
  const [tables, setTables] = useState<Table[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${backendUrl}/schema`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setTables(data.tables || []);
      } catch (e: any) {
        setError(
          "Could not reach backend. Start it with `uvicorn main:app --port 8000`."
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [backendUrl]);

  return (
    <div className="panel">
      <h2>
        <span className="dot" /> Schema Explorer
      </h2>
      {loading && <div className="loading">Loading schema…</div>}
      {error && <div className="hint">{error}</div>}
      {tables.map((t) => (
        <details className="table-block" key={t.table} open={t.table === "customers"}>
          <summary>
            <span>{t.table}</span>
            <span className="count">{t.row_count} rows</span>
          </summary>
          {t.columns.map((c) => (
            <div className="col-row" key={c.name}>
              <span className="col-name">
                {c.name}
                {c.primary_key && <span className="pk">PK</span>}
              </span>
              <span className="col-type">
                {c.type}
                {c.not_null ? " ·NN" : ""}
              </span>
            </div>
          ))}
        </details>
      ))}
    </div>
  );
}
