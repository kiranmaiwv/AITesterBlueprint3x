import { useState } from 'react'
import { showToast } from './Toast'
import './StrategyDisplay.css'

function StrategyDisplay({ strategyResult, issueKey, onDownload, onReset }) {
  const [showFull, setShowFull] = useState(false)

  if (!strategyResult?.strategy_content) {
    return (
      <div className="result-container">
        <div className="result-card error">
          <h2>⚠️ No Strategy Generated</h2>
          <p>Something went wrong. Please try again.</p>
          <button className="btn-reset" onClick={onReset}>← Back to Settings</button>
        </div>
      </div>
    )
  }

  const metadata = strategyResult.steps?.groq_generation
  const validation = strategyResult.steps?.validation
  const content = strategyResult.strategy_content

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      showToast('✓ Copied to clipboard!', 'success')
    } catch {
      showToast('Failed to copy to clipboard', 'error')
    }
  }

  return (
    <div className="result-container">
      <div className="result-card success">
        <div className="result-header">
          <h2>✅ Test Strategy Generated!</h2>
          <p className="result-issue">Issue: <strong>{issueKey}</strong></p>
        </div>

        {metadata && (
          <div className="metadata">
            <div className="meta-item">
              <span className="meta-label">Generation Time:</span>
              <span>{metadata.generation_time_ms}ms</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Tokens Used:</span>
              <span>{metadata.tokens_used}</span>
            </div>
            {validation && (
              <div className="meta-item">
                <span className="meta-label">Word Count:</span>
                <span>{validation.statistics?.word_count || 'N/A'}</span>
              </div>
            )}
          </div>
        )}

        <div className="strategy-preview">
          <h3>📄 {showFull ? 'Full Strategy' : 'Strategy Preview'}</h3>
          <div className="content">
            {showFull ? content : content.substring(0, 800)}
          </div>
          {content.length > 800 && (
            <button className="btn-toggle-preview" onClick={() => setShowFull(!showFull)}>
              {showFull ? '▲ Show Less' : '▼ Show Full Strategy'}
            </button>
          )}
        </div>

        <div className="actions">
          <button className="btn-download" onClick={onDownload}>
            ⬇️ Download Markdown
          </button>
          <button className="btn-copy" onClick={handleCopy}>
            📋 Copy to Clipboard
          </button>
          <button className="btn-new" onClick={onReset}>
            ✨ Generate New Strategy
          </button>
        </div>

        <div className="success-info">
          <h3>✓ What's Next?</h3>
          <ul>
            <li>Download the test strategy markdown file</li>
            <li>Import it into your testing tool of choice</li>
            <li>Share with your QA team</li>
            <li>Use as a template for test plan creation</li>
          </ul>
        </div>
      </div>

      <button className="btn-reset-footer" onClick={onReset}>← Back to Settings</button>
    </div>
  )
}

export default StrategyDisplay
