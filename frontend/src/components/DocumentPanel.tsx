'use client'

import { useRef, useState } from 'react'
import { Upload, Loader2, FileText, AlertCircle, Search, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'
import clsx from 'clsx'
import Markdown from 'react-markdown'

interface UploadedDoc {
  document_id: string
  metadata: { filename: string; extraction_method: string; chunk_count: number; cached: boolean }
}

export default function DocumentPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [doc, setDoc] = useState<UploadedDoc | null>(null)
  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [confidence, setConfidence] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    setDoc(null)
    setAnswer(null)
    try {
      const res = await api.uploadDocument(file) as UploadedDoc
      setDoc(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Errore upload')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const handleQuery = async () => {
    if (!doc || !question.trim() || querying) return
    setQuerying(true)
    setAnswer(null)
    setError(null)
    try {
      const res = await api.queryDocument(doc.document_id, question) as { answer: string; confidence: number }
      setAnswer(res.answer)
      setConfidence(res.confidence)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Errore query')
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <h2 className="text-base font-semibold text-gray-900">Analisi Documento</h2>

      {/* Upload area */}
      <div
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          uploading ? 'border-gray-200 bg-gray-50' : 'border-gray-300 hover:border-brand-400 hover:bg-brand-50/30'
        )}
      >
        <input ref={inputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleUpload} />
        {uploading ? (
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-2" />
        ) : (
          <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        )}
        <p className="text-sm font-medium text-gray-600">
          {uploading ? 'Elaborazione...' : 'Clicca per caricare PDF o DOCX'}
        </p>
        <p className="text-xs text-gray-400 mt-1">Max 10MB</p>
      </div>

      {/* Uploaded doc info */}
      {doc && (
        <div className="bg-green-50 border border-green-100 rounded-lg p-3 flex items-start gap-3">
          <FileText className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <div className="font-medium text-green-800">{doc.metadata.filename}</div>
            <div className="text-green-600 text-xs mt-0.5">
              {doc.metadata.chunk_count} chunk · estrazione: {doc.metadata.extraction_method}
              {doc.metadata.cached && ' · dalla cache'}
            </div>
          </div>
        </div>
      )}

      {/* Question input */}
      {doc && (
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            placeholder="Fai una domanda sul documento..."
            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            disabled={querying}
          />
          <button
            onClick={handleQuery}
            disabled={querying || !question.trim()}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-1.5',
              querying || !question.trim() ? 'bg-gray-300 cursor-not-allowed' : 'bg-brand-500 hover:bg-brand-600'
            )}
          >
            {querying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Chiedi
          </button>
        </div>
      )}

      {/* Answer */}
      {answer && (
        <div className="bg-gray-50 border border-gray-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
              <CheckCircle className="w-4 h-4 text-green-500" /> Risposta
            </div>
            {confidence !== null && (
              <span className="text-xs text-gray-400">Confidenza: {Math.round(confidence * 100)}%</span>
            )}
          </div>
          <div className="prose prose-sm max-w-none text-gray-800">
            <Markdown>{answer}</Markdown>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex gap-2">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}
    </div>
  )
}
