export interface Source {
  content: string
  file_path: string
  folder_id: string
  source: string
  score: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

export interface SSEData {
  type: 'token' | 'sources' | 'error' | 'done'
  content: any
}
