import { useState } from 'react'
import './App.css'
import Settings from './components/Settings'
import IssuePreview from './components/IssuePreview'
import StrategyDisplay from './components/StrategyDisplay'
import Toast, { showToast } from './components/Toast'

function App() {
  const [config, setConfig] = useState({
    jiraEmail: '',
    jiraToken: '',
    jiraUrl: '',
    groqKey: '',
    saveDir: './generated_strategies'
  })

  const [issueKey, setIssueKey] = useState('KAN-1')
  const [step, setStep] = useState('settings')
  const [issueData, setIssueData] = useState(null)
  const [strategyResult, setStrategyResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  const [hasEnvGroq, setHasEnvGroq] = useState(false)
  const [hasEnvJira, setHasEnvJira] = useState(false)

  const handleLoadEnv = async () => {
    const resp = await fetch('/api/env-config')
    const data = await resp.json()
    if (data.success) {
      const env = data.config
      setHasEnvGroq(env.hasGroqKey)
      setHasEnvJira(env.hasJiraToken)
      setConfig(prev => ({
        ...prev,
        jiraEmail: env.jiraEmail || prev.jiraEmail,
        jiraUrl: env.jiraUrl || prev.jiraUrl
      }))
      if (env.hasGroqKey) {
        showToast('✓ JIRA + GROQ credentials loaded from environment', 'success')
      } else if (!env.jiraEmail && !env.jiraUrl) {
        showToast('.env file is empty or missing. Check your .env file.', 'warning')
      }
    } else {
      throw new Error('Failed to load .env config')
    }
  }

  const handleConfigSave = (newConfig) => {
    setConfig(newConfig)
    setStep('preview')
    setError(null)
    setIssueData(null)
    setStrategyResult(null)
  }

  const handleFetchIssue = async () => {
    setLoading(true)
    setError(null)

    try {
      // JIRA token can come from Vercel env var - no need to send it from frontend
      const jiraToken = hasEnvJira ? '' : config.jiraToken

      if (!config.jiraUrl || !config.jiraEmail || (!jiraToken && !hasEnvJira)) {
        showToast('Please configure JIRA credentials in Settings first', 'warning')
        setStep('settings')
        setLoading(false)
        return
      }

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 15000)

      const response = await fetch('/api/fetch-issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          issueKey,
          jiraEmail: config.jiraEmail,
          jiraToken: jiraToken,
          jiraUrl: config.jiraUrl
        })
      })
      clearTimeout(timeoutId)

      const data = await response.json()

      if (!data.success) {
        const errorMsg = data.error || 'Failed to fetch issue'
        if (errorMsg.includes('404')) {
          showToast(`Issue "${issueKey}" not found. Check the issue key and try again.`, 'error')
        } else if (errorMsg.includes('401') || errorMsg.includes('AUTHENTICATED_FAILED')) {
          showToast('Authentication failed. Your JIRA API token may have expired.', 'error')
        } else if (errorMsg.includes('403')) {
          showToast('Permission denied. Your token may not have access.', 'error')
        } else {
          showToast(errorMsg, 'error')
        }
        setLoading(false)
        return
      }

      setIssueData(data.jira_issue)
      showToast(`✓ Fetched ${issueKey} successfully!`, 'success')
    } catch (err) {
      if (err.name === 'AbortError') {
        showToast('Request timed out after 15 seconds. Check your JIRA URL.', 'error')
      } else if (err.message.includes('Failed to fetch')) {
        showToast('Cannot connect to backend. Is the Flask server running?', 'error')
      } else {
        showToast(`Error: ${err.message}`, 'error')
      }
    }
    setLoading(false)
  }

  const handleGenerateStrategy = async (issue) => {
    setGenerating(true)
    setError(null)
    setStep('generating')

    try {
      // If GROQ key is set in env vars on server, don't send it (server will use its own)
      const groqKey = hasEnvGroq ? '' : config.groqKey

      if (!groqKey && !hasEnvGroq) {
        showToast('GROQ API key not configured. Add it in Settings.', 'warning')
        setStep('preview')
        setGenerating(false)
        return
      }

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 35000)

      const response = await fetch('/api/generate-strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          issueKey: issue.key || issueKey,
          jiraIssue: issue,
          groqKey: groqKey,
          saveDir: config.saveDir
        })
      })
      clearTimeout(timeoutId)

      const data = await response.json()

      if (!data.success) {
        const errorMsg = data.error || 'Failed to generate strategy'
        if (errorMsg.includes('rate') || errorMsg.includes('429')) {
          showToast('Rate limit hit. Please wait 60 seconds and retry.', 'warning')
        } else if (errorMsg.includes('401')) {
          showToast('Invalid GROQ API key. Check your credentials.', 'error')
        } else if (errorMsg.includes('timeout')) {
          showToast('Generation took too long. Try a simpler issue description.', 'error')
        } else {
          showToast(`Generation failed: ${errorMsg}`, 'error')
        }
        setStep('preview')
        setGenerating(false)
        return
      }

      setStrategyResult(data)
      setStep('result')
      showToast('✓ Test strategy generated successfully!', 'success')
    } catch (err) {
      if (err.name === 'AbortError') {
        showToast('Generation exceeded 35 seconds. Please try again.', 'error')
      } else if (err.message.includes('Failed to fetch')) {
        showToast('Backend connection lost. Is Flask server still running?', 'error')
      } else {
        showToast(`Error: ${err.message}`, 'error')
      }
      setStep('preview')
    }
    setGenerating(false)
  }

  const handleDownload = () => {
    if (!strategyResult?.strategy_content) return
    const element = document.createElement('a')
    const file = new Blob([strategyResult.strategy_content], { type: 'text/markdown' })
    element.href = URL.createObjectURL(file)
    element.download = `${issueKey}_TestStrategy.md`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
    showToast('✓ Strategy downloaded!', 'success')
  }

  const handleReset = () => {
    setStep('settings')
    setIssueData(null)
    setStrategyResult(null)
    setError(null)
  }

  return (
    <div className="app">
      <Toast />
      <header className="app-header">
        <h1>🚀 JIRA Test Strategy Auto-Generator</h1>
        <p>Generate comprehensive test strategies from JIRA issues using AI</p>
      </header>

      <main className="app-main">
        {error && <div className="error-banner">{error}</div>}

        {step === 'settings' && (
          <Settings
            config={config}
            onSave={handleConfigSave}
            issueKey={issueKey}
            onIssueKeyChange={setIssueKey}
            onLoadEnv={handleLoadEnv}
            hasEnvGroq={hasEnvGroq}
          />
        )}

        {step === 'preview' && (
          <IssuePreview
            issueKey={issueKey}
            issueData={issueData}
            loading={loading}
            generating={generating}
            onFetch={handleFetchIssue}
            onGenerate={handleGenerateStrategy}
            onBack={() => setStep('settings')}
          />
        )}

        {step === 'generating' && (
          <div className="generating-state">
            <div className="spinner"></div>
            <h2>Generating Test Strategy...</h2>
            <p>This may take up to 30 seconds</p>
            <p className="model-info">Using openai/gpt-oss-120b via GROQ</p>
          </div>
        )}

        {step === 'result' && (
          <StrategyDisplay
            strategyResult={strategyResult}
            issueKey={issueKey}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>✓ GROQ-powered | ✓ Real-time JIRA integration | ✓ Anti-hallucination mode</p>
      </footer>
    </div>
  )
}

export default App
