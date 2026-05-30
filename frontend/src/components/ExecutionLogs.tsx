'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, Loader2, ChevronDown, ChevronUp, Wrench } from 'lucide-react'
import { api } from '@/lib/api'
import type { ExecutionLog } from '@/types'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { it } from 'date-fns/locale'

const STATUS_CONFIG = {
  completed: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50', label: 'Completato' },
  failed:    { icon: XCircle,     color: 'text-red-500',   bg: 'bg-red-50',   label: 'Errore'     },
  running:   { icon: Loader2,     color: 'text-brand-500', bg: 'bg-brand-50', label: 'In esecuzione' },
  timeout:   { icon: Clock,       color: 'text-amber-500', bg: 'bg-amber-50', label: 'Timeout'    },
} as const

function LogRow({ log }: { log: ExecutionLog }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[log.status] ?? STATUS_CONFIG.completed
  const Icon = cfg.icon

  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors text-left"
      >
        <div className={clsx('p-1.5 rounded-lg', cfg.bg)}>
          <Icon className={clsx('w-4 h-4', cfg.color, log.status === 'running' && 'animate-spin')} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 text-sm">{log.agentName}</span>
            <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', cfg.bg, cfg.color)}>
              {cfg.label}
            </span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {formatDistanceToNow(new Date(log.startedAt), { addSuffix: true, locale: it })}
            {log.status !== 'running' && log.duration > 0 && (
              <span className="ml-2">· {(log.duration / 1000).toFixed(1)}s</span>
            )}
            <span className="ml-2">· {log.iterations} iter.</span>
          </div>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
          : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100 pt-3 bg-gray-50/50">
          {log.toolsUsed.length > 0 && (
            <div className="mb-3">
              <div className="text-xs font-medium text-gray-500 mb-1.5 flex items-center gap-1">
                <Wrench className="w-3 h-3" /> Tool utilizzati
              </div>
              <div className="flex flex-wrap gap-1.5">
                {log.toolsUsed.map((tool) => (
                  <span key={tool} className="text-xs bg-white border border-gray-200 px-2 py-0.5 rounded-full text-gray-600">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}
          {log.error && (
            <div className="bg-red-50 border border-red-100 rounded-lg p-3">
              <div className="text-xs font-medium text-red-600 mb-1">Errore</div>
              <div className="text-xs text-red-700 font-mono">{log.error}</div>
            </div>
          )}
          {log.toolsUsed.length === 0 && !log.error && (
            <p className="text-xs text-gray-400">Nessun dettaglio aggiuntivo.</p>
          )}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-12">
      <Clock className="w-10 h-10 text-gray-200 mx-auto mb-3" />
      <p className="text-gray-500 font-medium text-sm">Nessuna esecuzione ancora</p>
      <p className="text-gray-400 text-xs mt-1">
        Usa un agente qui sopra per vedere i log apparire in tempo reale
      </p>
    </div>
  )
}

export default function ExecutionLogs() {
  const [logs, setLogs] = useState<ExecutionLog[]>([])

  const load = async () => {
    try {
      const data = await api.getLogs() as ExecutionLog[]
      setLogs(data)
    } catch {
      // backend non raggiungibile
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-2">
      {logs.length === 0 ? <EmptyState /> : logs.map((log) => <LogRow key={log.id} log={log} />)}
    </div>
  )
}
