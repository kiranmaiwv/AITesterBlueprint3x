import { useState, useCallback } from 'react'
import type { Message, Source } from '../types'
import { streamChat } from '../api/chat'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])

  const sendMessage = useCallback(async (query: string) => {
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: query }
    setMessages(prev => [...prev, userMsg])

    const assistantMsg: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: '', sources: [] }
    setMessages(prev => [...prev, assistantMsg])

    const history = messages.map(m => ({ role: m.role, content: m.content }))

    try {
      for await (const event of streamChat(query, history)) {
        if (event.type === 'token') {
          assistantMsg.content += event.content
          setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }])
        } else if (event.type === 'sources') {
          assistantMsg.sources = event.content as Source[]
          setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }])
        } else if (event.type === 'error') {
          assistantMsg.content = `Error: ${event.content}`
          setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }])
        }
      }
    } catch (err: any) {
      assistantMsg.content = `Error: ${err.message}`
      setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }])
    }
  }, [messages])

  return { messages, sendMessage }
}
