import { useState, useEffect, useCallback } from 'react'
import './Toast.css'

let toastIdCounter = 0
let addToastFn = null

export function showToast(message, type = 'info', duration = 4000) {
  if (addToastFn) {
    addToastFn({ id: ++toastIdCounter, message, type, duration })
  }
}

function Toast() {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toast) => {
    setToasts(prev => [...prev, toast])
  }, [])

  useEffect(() => {
    addToastFn = addToast
    return () => { addToastFn = null }
  }, [addToast])

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  useEffect(() => {
    const timers = toasts.map(t =>
      setTimeout(() => removeToast(t.id), t.duration)
    )
    return () => timers.forEach(clearTimeout)
  }, [toasts])

  if (toasts.length === 0) return null

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div key={toast.id} className={`toast toast-${toast.type}`}>
          <span className="toast-icon">
            {toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : toast.type === 'warning' ? '⚠️' : 'ℹ️'}
          </span>
          <span className="toast-message">{toast.message}</span>
          <button className="toast-close" onClick={() => removeToast(toast.id)}>×</button>
        </div>
      ))}
    </div>
  )
}

export default Toast
