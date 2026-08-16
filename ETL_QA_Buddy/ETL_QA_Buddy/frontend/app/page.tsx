import SampleSchema from "@/components/SampleSchema";
import TestGenerator from "@/components/TestGenerator";
import TestResults from "@/components/TestResults";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Home() {
  return (
    <>
      <header className="header">
        <h1>🧪 ETL QA Buddy</h1>
        <span className="badge">AI-powered ETL data quality testing</span>
      </header>

      <div className="container">
        <p className="hint">
          Backend: <code>{BACKEND_URL}</code> — set{" "}
          <code>NEXT_PUBLIC_BACKEND_URL</code> to point to your local FastAPI
          server.
        </p>

        <div className="grid">
          <SampleSchema backendUrl={BACKEND_URL} />
          <TestGenerator backendUrl={BACKEND_URL} />
        </div>

        <TestResults backendUrl={BACKEND_URL} />
      </div>
    </>
  );
}
