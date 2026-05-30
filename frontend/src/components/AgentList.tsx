'use client'

import { useEffect, useState } from 'react'
import { Activity, Power, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import clsx from 'clsx'

interface AgentInfo {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  runsToday: number
  avgDuration: number
  successRate: number
}

const DESCRIPTIONS: Record<string, string> = {
  'react-agent':    'Risponde a domande usando tool (ricerca web, lettura file, notifiche)',
  'document-agent': 'Analizza PDF e DOCX, risponde a domande sul contenuto',
  'email-agent':    'Classifica email e genera bozze di risposta (mai inviate automaticamente)',
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-gray-100 flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-32 bg-gray-100 rounded" />
          <div className="h-3 w-48 bg-gray-100 rounded" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-100">
        {[0,1,2].map(i => <div key={i} className="h-10 bg-gray-100 rounded" />)}
      </div>
    </div>
  )
}

interface ToggleDialogProps {
  agent: AgentInfo
  onConfirm: () => void
  onCancel: () => void
}

function ToggleDialog({ agent, onConfirm, onCancel }: ToggleDialogProps) {
  const action = agent.status === 'active' ? 'disattivare' : 'attivare'
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Conferma azione</h3>
        <p className="text-gray-600 mb-6">
          Vuoi {action} l&apos;agente <strong>{agent.name}</strong>?
          {agent.status === 'active' && (
            <span className="block mt-2 text-amber-600 text-sm">
              L&apos;agente non elaborerà nuove richieste finché non viene riattivato.
            </span>
          )}
        </p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors">
            Annulla
          </button>
          <button
            onClick={onConfirm}
            className={clsx('px-4 py-2 rounded-lg text-white font-medium transition-colors',
              agent.status === 'active' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
            )}
          >
            {agent.status === 'active' ? 'Disattiva' : 'Attiva'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AgentList() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [pendingToggle, setPendingToggle] = useState<AgentInfo | null>(null)
  const [toggling, setToggling] = useState<string | null>(null)

  // Local toggle state (backend non ha ancora endpoint on/off)
  const [statusMap, setStatusMap] = useState<Record<string, 'active' | 'inactive'>>({})

  const load = async () => {
    try {
      const data = await api.getAgentsStats() as Array<{
        id: string; name: string; runsToday: number; avgDuration: number; successRate: number
      }>
      setAgents(data.map(a => ({
        ...a,
        description: DESCRIPTIONS[a.id] || '',
        status: statusMap[a.id] ?? 'active',
      })))
    } catch {
      // backend offline
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 10000)
    return () => clearInterval(interval)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusMap])

  const handleConfirmToggle = async () => {
    if (!pendingToggle) return
    const id = pendingToggle.id
    const newStatus = pendingToggle.status === 'active' ? 'inactive' : 'active'
    setStatusMap(prev => ({ ...prev, [id]: newStatus }))
    setPendingToggle(null)
    setToggling(id)
    await new Promise(r => setTimeout(r, 600))
    setToggling(null)
  }

  if (loading) {
    return <div className="space-y-4">{[0,1,2].map(i => <SkeletonCard key={i} />)}</div>
  }

  return (
    <div>
      {pendingToggle && (
        <ToggleDialog
          agent={pendingToggle}
          onConfirm={handleConfirmToggle}
          onCancel={() => setPendingToggle(null)}
        />
      )}

      <div className="space-y-4">
        {agents.map((agent) => {
          const status = statusMap[agent.id] ?? 'active'
          const isActive = status === 'active'

          return (
            <div key={agent.id} className={clsx('bg-white rounded-xl border p-5 transition-all',
              isActive ? 'border-gray-200' : 'border-gray-100 opacity-70'
            )}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                    isActive ? 'bg-brand-50' : 'bg-gray-100'
                  )}>
                    <Activity className={clsx('w-5 h-5', isActive ? 'text-brand-500' : 'text-gray-400')} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium',
                        isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      )}>
                        {isActive ? 'Attivo' : 'Inattivo'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-0.5">{agent.description}</p>
                  </div>
                </div>

                <button
                  onClick={() => setPendingToggle({ ...agent, status })}
                  disabled={toggling === agent.id}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex-shrink-0',
                    toggling === agent.id && 'opacity-50 cursor-wait',
                    isActive ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100'
                  )}
                >
                  <Power className="w-3.5 h-3.5" />
                  {toggling === agent.id ? 'Attendere...' : isActive ? 'Disattiva' : 'Attiva'}
                </button>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-4 pt-4 border-t border-gray-100">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{agent.runsToday}</div>
                  <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
                    <Activity className="w-3 h-3" /> Oggi
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">
                    {agent.avgDuration > 0 ? `${(agent.avgDuration / 1000).toFixed(1)}s` : '—'}
                  </div>
                  <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
                    <Clock className="w-3 h-3" /> Durata media
                  </div>
                </div>
                <div className="text-center">
                  <div className={clsx('text-lg font-bold',
                    agent.runsToday === 0 ? 'text-gray-400' :
                    agent.successRate >= 0.9 ? 'text-green-600' : 'text-amber-500'
                  )}>
                    {agent.runsToday === 0 ? '—' : `${Math.round(agent.successRate * 100)}%`}
                  </div>
                  <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
                    <TrendingUp className="w-3 h-3" /> Successo
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {!loading && agents.length === 0 && (
          <div className="text-center py-16">
            <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">Backend non raggiungibile</p>
          </div>
        )}
      </div>
    </div>
  )
}
