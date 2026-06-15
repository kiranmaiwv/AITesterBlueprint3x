import './IssuePreview.css'

function IssuePreview({ issueKey, issueData, loading, generating, onFetch, onGenerate, onBack }) {
  return (
    <div className="preview-container">
      <button className="btn-back" onClick={onBack}>← Back to Settings</button>

      <div className="preview-card">
        <h2>📋 JIRA Issue Preview</h2>

        {!issueData && !loading && (
          <div className="no-preview">
            <p>Click the button below to fetch issue details</p>
            <button className="btn-fetch" onClick={onFetch} disabled={loading}>
              Fetch Issue: {issueKey}
            </button>
          </div>
        )}

        {loading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Fetching issue from JIRA...</p>
          </div>
        )}

        {issueData && (
          <div className="issue-details">
            <div className="detail-row">
              <span className="label">Key:</span>
              <span className="value">{issueData.key}</span>
            </div>

            <div className="detail-row">
              <span className="label">Summary:</span>
              <span className="value">{issueData.summary}</span>
            </div>

            <div className="detail-row">
              <span className="label">Type:</span>
              <span className="badge">{issueData.issue_type}</span>
            </div>

            <div className="detail-row">
              <span className="label">Status:</span>
              <span className="badge status">{issueData.status}</span>
            </div>

            {issueData.priority && (
              <div className="detail-row">
                <span className="label">Priority:</span>
                <span className="badge priority">{issueData.priority}</span>
              </div>
            )}

            {issueData.description && (
              <div className="detail-section">
                <span className="label">Description:</span>
                <div className="description">
                  {issueData.description.substring(0, 500)}
                  {issueData.description.length > 500 && '...'}
                </div>
              </div>
            )}

            <button
              className="btn-generate"
              onClick={() => onGenerate(issueData)}
              disabled={generating}
            >
              {generating ? (
                <span className="btn-generating">
                  <span className="spinner-small"></span>
                  Generating...
                </span>
              ) : (
                '✨ Generate Test Strategy'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default IssuePreview
