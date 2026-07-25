import { useState, FormEvent, KeyboardEvent, useRef, useEffect } from 'react'

interface Props {
  onSend: (q: string) => void
  loading: boolean
}

export default function ChatInput({ onSend, loading }: Props) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 160)}px`
    }
  }, [value])

  const submit = (e?: FormEvent) => {
    e?.preventDefault()
    if (!value.trim() || loading) return
    onSend(value.trim())
    setValue('')
  }

  return (
    <form onSubmit={submit} className="ci">
      <textarea ref={ref} value={value} onChange={e => setValue(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submit())} placeholder="Ask a QA question..." rows={1} />
      <button type="submit" disabled={loading || !value.trim()}>{loading ? '...' : '→'}</button>
    </form>
  )
}
