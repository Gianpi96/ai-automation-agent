'use client'

import { useEffect, useState } from 'react'
import { WifiOff, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

export default function BackendBanner() {
  const [offline, setOffline] = useState(false)
  const [checking, setChecking] = useState(false)

  const check = async () => {
    try {
      await api.healthCheck()
      setOffline(false)
    } catch {
      setOffline(true)
    }
  }

  useEffect(() => {
    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [])

  if (!offline) return null

  return (
    <div className="bg-red-600 text-white px-4 py-2.5 flex items-center justify-center gap-3 text-sm">
      <WifiOff className="w-4 h-4 flex-shrink-0" />
      <span className="font-medium">Backend non raggiungibile — avvia il server con <code className="bg-red-700 px-1.5 py-0.5 rounded text-xs">uvicorn app.main:app --reload</code></span>
      <button
        onClick={async () => { setChecking(true); await check(); setChecking(false) }}
        className="flex items-center gap-1 bg-red-700 hover:bg-red-800 px-2.5 py-1 rounded text-xs font-medium transition-colors"
      >
        <RefreshCw className={`w-3 h-3 ${checking ? 'animate-spin' : ''}`} />
        Riprova
      </button>
    </div>
  )
}
