"use client";

import { useChat } from "ai/react";
import { FormEvent, useRef, useEffect } from "react";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, error } = useChat();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    if (!input.trim() || isLoading) return;
    handleSubmit(e);
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.h1}>Shopify Tester RAG</h1>
        <p style={styles.subtitle}>Ask questions about your Shopify test cases</p>
      </header>

      <div style={styles.chat}>
        {error && <p style={styles.error}>Error: {error.message}</p>}

        {messages.length === 0 && (
          <div style={styles.empty}>
            <p>Try asking something like:</p>
            <ul style={styles.suggestions}>
              <li onClick={() => handleSuggested("How do I test the login flow?")}>
                &quot;How do I test the login flow?&quot;
              </li>
              <li onClick={() => handleSuggested("What are the high priority test cases?")}>
                &quot;What are the high priority test cases?&quot;
              </li>
              <li onClick={() => handleSuggested("Show me test cases for forgot password")}>
                &quot;Show me test cases for forgot password&quot;
              </li>
            </ul>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} style={m.role === "user" ? styles.userMsg : styles.assistantMsg}>
            <strong>{m.role === "user" ? "You" : "RAG Bot"}</strong>
            <div style={styles.content}>{m.content}</div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form onSubmit={onSubmit} style={styles.form}>
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Ask about Shopify test cases..."
          style={styles.input}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()} style={styles.button}>
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );

  function handleSuggested(text: string) {
    const fakeEvent = { target: { value: text } } as React.ChangeEvent<HTMLInputElement>;
    handleInputChange(fakeEvent);
  }
}

const text = "#1a1a2e";

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 720,
    margin: "0 auto",
    height: "100dvh",
    display: "flex",
    flexDirection: "column",
    background: "#fff",
  },
  header: {
    padding: "20px 24px 12px",
    borderBottom: "1px solid #e0e0e0",
    background: "#1a1a2e",
    color: "#fff",
  },
  h1: { margin: 0, fontSize: "1.3rem", fontWeight: 600 },
  subtitle: { margin: "4px 0 0", fontSize: "0.85rem", opacity: 0.7 },
  chat: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 24px",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  empty: { color: "#888", textAlign: "center" as const, marginTop: 40 },
  suggestions: { listStyle: "none", padding: 0, cursor: "pointer", color: "#2563eb", textDecoration: "underline" },
  userMsg: {
    alignSelf: "flex-end",
    background: "#2563eb",
    color: "#fff",
    padding: "10px 14px",
    borderRadius: "16px 16px 4px 16px",
    maxWidth: "80%",
  },
  assistantMsg: {
    alignSelf: "flex-start",
    background: "#f0f0f0",
    color: text,
    padding: "10px 14px",
    borderRadius: "16px 16px 16px 4px",
    maxWidth: "80%",
  },
  content: { marginTop: 4, whiteSpace: "pre-wrap", fontSize: "0.95rem", lineHeight: 1.5 },
  error: { color: "#dc2626", padding: 8, background: "#fee2e2", borderRadius: 8, fontSize: "0.85rem" },
  form: {
    display: "flex",
    gap: 8,
    padding: "12px 24px",
    borderTop: "1px solid #e0e0e0",
    background: "#fff",
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: 24,
    border: "1px solid #ccc",
    fontSize: "0.95rem",
    outline: "none",
  },
  button: {
    padding: "10px 20px",
    borderRadius: 24,
    border: "none",
    background: "#2563eb",
    color: "#fff",
    fontWeight: 600,
    cursor: "pointer",
    fontSize: "0.9rem",
  },
};
