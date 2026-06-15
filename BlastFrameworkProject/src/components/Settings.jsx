import { useState, useEffect } from 'react'
import { showToast } from './Toast'
import './Settings.css'

function Settings({ config, onSave, issueKey, onIssueKeyChange, onLoadEnv, hasEnvGroq, hasEnvJira }) {
  const [form, setForm] = useState(config)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loadingEnv, setLoadingEnv] = useState(false)

  // Sync when config prop changes (e.g., from env load)
  useEffect(() => {
    setForm(config)
  }, [config])

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const handleLoadEnv = async () => {
    setLoadingEnv(true)
    try {
      await onLoadEnv()
      showToast('✓ Credentials loaded from .env', 'success')
    } catch (err) {
      showToast('Could not load .env: ' + err.message, 'error')
    }
    setLoadingEnv(false)
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    const errors = []
    if (!form.jiraEmail || !form.jiraEmail.includes('@')) {
      errors.push('Valid email address required')
    }
    if (!form.jiraToken || form.jiraToken.length < 10) {
      errors.push('JIRA API token appears invalid (too short)')
    }
    if (!form.jiraUrl || !form.jiraUrl.includes('atlassian')) {
      errors.push('JIRA URL should contain "atlassian"')
    }
    if (!hasEnvGroq && (!form.groqKey || !form.groqKey.startsWith('gsk_'))) {
      errors.push('GROQ key should start with "gsk_"')
    }
    if (!issueKey || !issueKey.trim()) {
      errors.push('Issue key is required (e.g., KAN-1)')
    }

    if (errors.length > 0) {
      showToast(errors.join('\n'), 'warning', 6000)
      return
    }

    onSave(form)
    showToast('✓ Configuration saved', 'success')
  }

  return (
    <div className="settings-container">
      <div className="settings-card">
        <h2>⚙️ Configuration</h2>

        <div className="env-load-bar">
          <span>Load saved credentials from .env file</span>
          <button
            type="button"
            className="btn-env"
            onClick={handleLoadEnv}
            disabled={loadingEnv}
          >
            {loadingEnv ? 'Loading...' : '📂 Load from .env'}
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <fieldset>
            <legend>JIRA Configuration</legend>

            <div className="form-group">
              <label htmlFor="jiraEmail">
                Email <span className="required">*</span>
              </label>
              <input
                id="jiraEmail"
                type="email"
                placeholder="your@email.com"
                value={form.jiraEmail}
                onChange={(e) => handleChange('jiraEmail', e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="jiraToken">
                API Token{!hasEnvJira && <span className="required"> *</span>}
              </label>
              {hasEnvJira ? (
                <div className="env-active">✓ JIRA API token is configured on the server (Vercel env var)</div>
              ) : (
                <input
                  id="jiraToken"
                  type="password"
                  placeholder="Enter your JIRA API token"
                  value={form.jiraToken}
                  onChange={(e) => handleChange('jiraToken', e.target.value)}
                  required
                />
              )}
              <small>Get from: Account Settings → Security → API tokens</small>
            </div>

            <div className="form-group">
              <label htmlFor="jiraUrl">
                JIRA URL <span className="required">*</span>
              </label>
              <input
                id="jiraUrl"
                type="url"
                placeholder="https://your-instance.atlassian.net"
                value={form.jiraUrl}
                onChange={(e) => handleChange('jiraUrl', e.target.value)}
                required
              />
              <small>Your JIRA instance or project URL</small>
            </div>
          </fieldset>

          <fieldset>
            <legend>GROQ API Configuration</legend>

            <div className="form-group">
              <label htmlFor="groqKey">
                GROQ API Key{!hasEnvGroq && <span className="required"> *</span>}
              </label>
              {hasEnvGroq ? (
                <div className="env-active">✓ GROQ key is configured on the server (Vercel env var)</div>
              ) : (
                <input
                  id="groqKey"
                  type="password"
                  placeholder="gsk_..."
                  value={form.groqKey}
                  onChange={(e) => handleChange('groqKey', e.target.value)}
                  required
                />
              )}
              <small>Get from: <a href="https://console.groq.com/keys" target="_blank">console.groq.com</a></small>
            </div>
          </fieldset>

          <button
            type="button"
            className="btn-advanced"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? '▼' : '▶'} Advanced Settings
          </button>

          {showAdvanced && (
            <fieldset>
              <legend>Advanced</legend>
              <div className="form-group">
                <label htmlFor="saveDir">Save Directory</label>
                <input
                  id="saveDir"
                  type="text"
                  placeholder="./generated_strategies"
                  value={form.saveDir}
                  onChange={(e) => handleChange('saveDir', e.target.value)}
                />
              </div>
            </fieldset>
          )}

          <fieldset>
            <legend>JIRA Issue</legend>
            <div className="form-group">
              <label htmlFor="issueKey">Issue Key</label>
              <input
                id="issueKey"
                type="text"
                placeholder="KAN-1"
                value={issueKey}
                onChange={(e) => onIssueKeyChange(e.target.value)}
              />
              <small>Enter the JIRA issue key to generate a strategy for</small>
            </div>
          </fieldset>

          <button type="submit" className="btn-primary">
            Continue to Preview
          </button>
        </form>
      </div>
    </div>
  )
}

export default Settings
