import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import { useChat } from './hooks/useChat'

export default function App() {
  const { messages, sendMessage } = useChat()
  const [_, setGroqKey] = useState('')

  const handleSetKey = (key: string) => {
    setGroqKey(key)
    // In a real app, pass this to the backend or store it
  }

  return <ChatWindow messages={messages} onSend={sendMessage} onSetKey={handleSetKey} />
}
