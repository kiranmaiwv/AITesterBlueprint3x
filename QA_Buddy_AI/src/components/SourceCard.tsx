import type { Source } from '../types'

const LABELS: Record<string,string> = {'01':'📁 Selenium','02':'📁 Playwright','03':'📁 Test Cases','04':'📁 JIRA','05':'📁 Docs','06':'📁 Figma','07':'📁 Notes','08':'📁 Charts','09':'📁 PRD','10':'📁 Jenkins'}

export default function SourceCard({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null
  return (
    <div className="sources">
      <div className="st">Sources</div>
      <div className="sg">
        {sources.map((s, i) => (
          <div key={i} className="sc">
            <div className="sp">{s.file_path}</div>
            <div className="sm"><span>{LABELS[s.folder_id] || s.folder_id}</span><span>{(s.score * 100).toFixed(0)}%</span></div>
            <div className="sx">{s.content.slice(0, 200)}...</div>
          </div>
        ))}
      </div>
    </div>
  )
}
