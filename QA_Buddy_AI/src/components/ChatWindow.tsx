import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../types'
import SourceCard from './SourceCard'
import ChatInput from './ChatInput'
import SettingsPanel from './SettingsPanel'

interface Props {
  messages: Message[]
  onSend: (q: string) => void
  onSetKey: (k: string) => void
}

export default function ChatWindow({ messages, onSend, onSetKey }: Props) {
  const [showSettings, setShowSettings] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  return (
    <div className="cc">
      <div className="ch">
        <h1>🧪 QA Buddy AI</h1>
        <div className="ha"><span className="badge">Hybrid RAG</span><button className="sb" onClick={() => setShowSettings(true)} title="Settings">⚙️</button></div>
      </div>
      <div className="msgs">
        {messages.length === 0 && (
          <div className="empty">
            <div className="ei">🧪</div>
            <h2>Ask a QA question</h2>
            <p>Search across your Selenium framework, Playwright tests, JIRA bugs, test cases, PRDs, and more.</p>
            <div className="ex">
              <button onClick={() => onSend('How do I handle OAuth2 login in Selenium?')}>OAuth2 in Selenium</button>
              <button onClick={() => onSend('What are common test failure patterns?')}>Test failure patterns</button>
              <button onClick={() => onSend('Show me test coverage for login module')}>Test coverage</button>
            </div>
          </div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`msg ${msg.role}`}>
            <div className="av">{msg.role === 'user' ? '👤' : '🤖'}</div>
            <div className="bub">
              {msg.role === 'assistant' ? <ReactMarkdown>{msg.content || ''}</ReactMarkdown> : <p>{msg.content}</p>}
              {msg.sources && <SourceCard sources={msg.sources} />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={onSend} loading={false} />
      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} onSetKey={onSetKey} />}
    </div>
  )
}
