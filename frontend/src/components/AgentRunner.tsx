'use client'

import { useState } from 'react'
import { Play, Loader2, CheckCircle, AlertCircle, Wrench, BarChart2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { AgentResult } from '@/types'
import clsx from 'clsx'

export default function AgentRunner() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AgentResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.runAgent(query) as AgentResult
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-base font-semibold text-gray-900 mb-4">Esegui Agente ReAct</h2>

      <div className="flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleRun()}
          placeholder="Cosa vuoi fare? Es: 'Cerca notizie su Python 3.14 e inviami una notifica'"
          className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          disabled={loading}
        />
        <button
          onClick={handleRun}
          disabled={loading || !query.trim()}
          className={clsx(
            'flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-all',
            loading || !query.trim()
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-brand-500 hover:bg-brand-600'
          )}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Elaborazione...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Esegui
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-100 rounded-lg p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-red-700">Errore</div>
            <div className="text-sm text-red-600 mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-3">
          <div className="bg-green-50 border border-green-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm font-semibold text-green-800">Risposta</span>
            </div>
            <p className="text-sm text-gray-800 leading-relaxed">{result.answer}</p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-gray-900">{result.iterations}</div>
              <div className="text-xs text-gray-500">Iterazioni</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-gray-900">
                {Math.round(result.confidence * 100)}%
              </div>
              <div className="text-xs text-gray-500">Confidenza</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-gray-900">
                {(result.total_duration_ms / 1000).toFixed(1)}s
              </div>
              <div className="text-xs text-gray-500">Durata</div>
            </div>
          </div>

          {result.tools_used.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Wrench className="w-3.5 h-3.5 text-gray-400" />
              {result.tools_used.map((t) => (
                <span
                  key={t}
                  className="text-xs bg-white border border-gray-200 px-2.5 py-1 rounded-full text-gray-600"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
