import { useState, useEffect } from 'react'
import { fetchSettings, testJiraConnection } from '../api/chat'

interface Props { onClose: () => void; onSetKey: (key: string) => void }

export default function SettingsPanel({ onClose, onSetKey }: Props) {
  const [tab, setTab] = useState<'sources'|'settings'>('sources')
  const [settings, setSettings] = useState<any>({})
  const [key, setKey] = useState('')
  const [jira, setJira] = useState({ url: '', email: '', token: '', jql: '' })
  const [jiraResult, setJiraResult] = useState<any>(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    fetchSettings().then(setSettings).catch(() => {})
  }, [])

  const handleTestJira = async () => {
    const r = await testJiraConnection(jira.jql, jira.url, jira.email, jira.token)
    setJiraResult(r)
  }

  const handleSetKey = () => {
    if (key) {
      onSetKey(key)
      setMsg('✅ GROQ key saved')
    }
  }

  return (
    <div className="so" onClick={onClose}>
      <div className="sp" onClick={e => e.stopPropagation()}>
        <div className="sh"><h2>⚙️ QA Buddy Settings</h2><button onClick={onClose}>✕</button></div>
        <div className="stabs">
          <button className={tab==='sources'?'active':''} onClick={() => setTab('sources')}>System</button>
          <button className={tab==='settings'?'active':''} onClick={() => setTab('settings')}>Connection</button>
        </div>
        {tab === 'sources' && (
          <div className="sb">
            <p>QA Buddy uses <strong>Qdrant Cloud</strong> for vector storage and <strong>OpenAI embeddings</strong>.</p>
            <p>Data is ingested via a local script that pushes embeddings to the cloud.</p>
            <hr/>
            <p><strong>Status:</strong></p>
            <ul>
              <li>GROQ: {settings.groq_key ? '✅' : '❌'}</li>
              <li>OpenAI Embeddings: {settings.openai_configured ? '✅' : '❌'}</li>
              <li>Qdrant: {settings.qdrant_url ? '✅' : '❌'}</li>
              <li>JIRA: {settings.jira_url ? '✅' : '❌'}</li>
            </ul>
          </div>
        )}
        {tab === 'settings' && (
          <div className="sf">
            <h3>GROQ API Key</h3>
            <div className="key-row">
              <input placeholder="gsk_..." value={key} onChange={e => setKey(e.target.value)} />
              <button onClick={handleSetKey}>Save</button>
            </div>
            <h3>Test JIRA</h3>
            <input placeholder="URL" value={jira.url} onChange={e => setJira({...jira, url: e.target.value})} />
            <input placeholder="Email" value={jira.email} onChange={e => setJira({...jira, email: e.target.value})} />
            <input placeholder="API Token" type="password" value={jira.token} onChange={e => setJira({...jira, token: e.target.value})} />
            <input placeholder="JQL" value={jira.jql} onChange={e => setJira({...jira, jql: e.target.value})} />
            <button onClick={handleTestJira}>Test Connection</button>
            {jiraResult && <pre className="jr">{JSON.stringify(jiraResult, null, 2).slice(0, 500)}</pre>}
            {msg && <div className="sm">{msg}</div>}
          </div>
        )}
      </div>
    </div>
  )
}
