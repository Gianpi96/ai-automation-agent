'use client'

import { useState } from 'react'
import { Mail, Loader2, CheckCircle, AlertCircle, Tag, Zap, ThumbsUp, ThumbsDown } from 'lucide-react'
import { api } from '@/lib/api'
import clsx from 'clsx'

interface EmailResult {
  email: { id: string; sender: string; subject: string; body: string }
  classification: {
    category: string; urgency: string; sentiment: string
    requires_response: boolean; reasoning: string; confidence: number
  }
  draft?: { draft_id: string; subject: string; body: string; tone: string; approved: boolean }
  processing_time_ms: number
}

const URGENCY_COLOR: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const CATEGORY_COLOR: Record<string, string> = {
  complaint: 'bg-red-50 text-red-700',
  billing: 'bg-purple-50 text-purple-700',
  sales: 'bg-green-50 text-green-700',
  support: 'bg-blue-50 text-blue-700',
  inquiry: 'bg-sky-50 text-sky-700',
  spam: 'bg-gray-50 text-gray-500',
  other: 'bg-gray-50 text-gray-600',
}

const INBOX = [
  { id: 'email_001', sender: 'angry.customer@example.com', subject: 'URGENT: ordine sbagliato da 3 settimane!' },
  { id: 'email_002', sender: 'enterprise@bigcorp.com', subject: 'Interessati a prezzi enterprise' },
  { id: 'email_003', sender: 'user@example.com', subject: 'Come resetto la password?' },
]

export default function EmailPanel() {
  const [results, setResults] = useState<Record<string, EmailResult>>({})
  const [loading, setLoading] = useState<string | null>(null)
  const [approving, setApproving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async (emailId: string) => {
    setLoading(emailId)
    setError(null)
    try {
      const res = await api.processEmail(emailId) as EmailResult
      setResults((prev) => ({ ...prev, [emailId]: res }))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Errore elaborazione')
    } finally {
      setLoading(null)
    }
  }

  const handleApprove = async (draftId: string, emailId: string, approved: boolean) => {
    setApproving(draftId)
    try {
      await api.approveDraft(draftId, approved)
      setResults((prev) => ({
        ...prev,
        [emailId]: {
          ...prev[emailId],
          draft: prev[emailId].draft
            ? { ...prev[emailId].draft!, approved }
            : undefined,
        },
      }))
    } finally {
      setApproving(null)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Agente Email</h2>
      <p className="text-xs text-gray-400">Le bozze non vengono mai inviate automaticamente — richiedono la tua approvazione.</p>

      <div className="space-y-3">
        {INBOX.map((email) => {
          const result = results[email.id]
          const isLoading = loading === email.id

          return (
            <div key={email.id} className="border border-gray-100 rounded-lg overflow-hidden">
              {/* Email header row */}
              <div className="flex items-center gap-3 p-3">
                <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-800 truncate">{email.subject}</div>
                  <div className="text-xs text-gray-400 truncate">{email.sender}</div>
                </div>
                {!result && (
                  <button
                    onClick={() => handleProcess(email.id)}
                    disabled={isLoading}
                    className={clsx(
                      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-colors flex-shrink-0',
                      isLoading ? 'bg-gray-300 cursor-wait' : 'bg-brand-500 hover:bg-brand-600'
                    )}
                  >
                    {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                    {isLoading ? 'Analisi...' : 'Analizza'}
                  </button>
                )}
                {result && (
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                )}
              </div>

              {/* Classification result */}
              {result && (
                <div className="border-t border-gray-50 bg-gray-50/50 p-3 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', CATEGORY_COLOR[result.classification.category] || 'bg-gray-100 text-gray-600')}>
                      <Tag className="w-3 h-3 inline mr-1" />{result.classification.category}
                    </span>
                    <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', URGENCY_COLOR[result.classification.urgency] || 'bg-gray-100 text-gray-600')}>
                      urgenza: {result.classification.urgency}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                      {result.classification.sentiment}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 italic">{result.classification.reasoning}</p>

                  {/* Draft */}
                  {result.draft && (
                    <div className={clsx(
                      'rounded-lg border p-3 space-y-2',
                      result.draft.approved ? 'border-green-200 bg-green-50' : 'border-amber-100 bg-amber-50/40'
                    )}>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-gray-700">Bozza risposta</span>
                        {result.draft.approved
                          ? <span className="text-xs text-green-600 font-medium flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Approvata</span>
                          : <span className="text-xs text-amber-600">In attesa di approvazione</span>
                        }
                      </div>
                      <div className="text-xs text-gray-600 bg-white rounded p-2 border border-gray-100 whitespace-pre-wrap max-h-32 overflow-y-auto">
                        {result.draft.body}
                      </div>
                      {!result.draft.approved && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleApprove(result.draft!.draft_id, email.id, true)}
                            disabled={approving === result.draft.draft_id}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-500 text-white hover:bg-green-600 transition-colors"
                          >
                            <ThumbsUp className="w-3 h-3" /> Approva
                          </button>
                          <button
                            onClick={() => handleApprove(result.draft!.draft_id, email.id, false)}
                            disabled={approving === result.draft.draft_id}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                          >
                            <ThumbsDown className="w-3 h-3" /> Rifiuta
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {!result.draft && !result.classification.requires_response && (
                    <p className="text-xs text-gray-400">Nessuna risposta necessaria per questa email.</p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}
    </div>
  )
}
