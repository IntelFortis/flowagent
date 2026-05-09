import { useState, useEffect, useCallback } from 'react'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

let toastId = 0
let listeners: ((toast: Toast) => void)[] = []

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  const toast: Toast = { id: ++toastId, message, type }
  listeners.forEach(fn => fn(toast))
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Toast) => {
    setToasts(prev => [...prev, toast])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== toast.id))
    }, 3000)
  }, [])

  useEffect(() => {
    listeners.push(addToast)
    return () => { listeners = listeners.filter(l => l !== addToast) }
  }, [addToast])

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-16 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`pointer-events-auto px-4 py-3 rounded-lg shadow-lg border text-sm font-medium animate-slide-in-right ${
            toast.type === 'success' ? 'bg-green-500/15 border-green-500/30 text-green-400' :
            toast.type === 'error' ? 'bg-red-500/15 border-red-500/30 text-red-400' :
            'bg-blue-500/15 border-blue-500/30 text-blue-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {toast.type === 'success' ? (
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            ) : toast.type === 'error' ? (
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            ) : (
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            )}
            {toast.message}
          </div>
        </div>
      ))}
    </div>
  )
}
