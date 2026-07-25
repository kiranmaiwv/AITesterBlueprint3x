import type { SSEData } from '../types'

export async function* streamChat(query: string, history: { role: string; content: string }[] = []) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history }),
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    for (const line of buffer.split('\n')) {
      if (!line.startsWith('data: ')) { buffer = line; continue }
      try {
        yield JSON.parse(line.slice(6)) as SSEData
      } catch {}
    }
    buffer = ''
  }
}

export async function fetchHealth() {
  const r = await fetch('/api/health')
  return r.json()
}

export async function fetchSettings() {
  const r = await fetch('/api/settings')
  return r.json()
}

export async function testJiraConnection(jql: string, url: string, email: string, token: string) {
  const r = await fetch('/api/jira/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jql, url, email, token }),
  })
  return r.json()
}
