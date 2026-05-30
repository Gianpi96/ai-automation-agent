'use client'

import { useState } from 'react'
import { Activity, Power, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import type { AgentInfo } from '@/types'
import clsx from 'clsx'

const INITIAL_AGENTS: AgentInfo[] = [
  {
    id: 'react-agent',
    name: 'Agente ReAct',
    description: 'Risponde a domande usando tool (ricerca web, lettura file, notifiche)',
    status: 'active',
    runsToday: 12,
    avgDuration: 4200,
    successRate: 0.92,
  },
  {
    id: 'document-agent',
    name: 'Agente Documenti',
    description: 'Analizza PDF e DOCX, risponde a domande sul contenuto',
    status: 'active',
    runsToday: 8,
    avgDuration: 6800,
    successRate: 0.95,
  },
  {
    id: 'email-agent',
    name: 'Agente Email',
    description: 'Classifica email e genera bozze di risposta (mai inviate automaticamente)',
    status: 'active',
    runsToday: 24,
    avgDuration: 3100,
    successRate: 0.88,
  },
]

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
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Conferma azione
        </h3>
        <p className="text-gray-600 mb-6">
          Vuoi {action} l&apos;agente <strong>{agent.name}</strong>?
          {agent.status === 'active' && (
            <span className="block mt-2 text-amber-600 text-sm">
              L&apos;agente non elaborerà nuove richieste finché non viene riattivato.
            </span>
          )}
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Annulla
          </button>
          <button
            onClick={onConfirm}
            className={clsx(
              'px-4 py-2 rounded-lg text-white font-medium transition-colors',
              agent.status === 'active'
                ? 'bg-red-500 hover:bg-red-600'
                : 'bg-green-500 hover:bg-green-600'
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
  const [agents, setAgents] = useState<AgentInfo[]>(INITIAL_AGENTS)
  const [pendingToggle, setPendingToggle] = useState<AgentInfo | null>(null)
  const [loading, setLoading] = useState<string | null>(null)

  const handleToggleClick = (agent: AgentInfo) => {
    setPendingToggle(agent)
  }

  const handleConfirmToggle = async () => {
    if (!pendingToggle) return
    const agentId = pendingToggle.id

    // Optimistic update
    setAgents((prev) =>
      prev.map((a) =>
        a.id === agentId
          ? { ...a, status: a.status === 'active' ? 'inactive' : 'active' }
          : a
      )
    )
    setPendingToggle(null)
    setLoading(agentId)

    // Simulate API call (replace with real API in production)
    await new Promise((r) => setTimeout(r, 800))
    setLoading(null)
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
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={clsx(
              'bg-white rounded-xl border p-5 transition-all',
              agent.status === 'active' ? 'border-gray-200' : 'border-gray-100 opacity-70'
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div
                  className={clsx(
                    'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                    agent.status === 'active' ? 'bg-brand-50' : 'bg-gray-100'
                  )}
                >
                  <Activity
                    className={clsx(
                      'w-5 h-5',
                      agent.status === 'active' ? 'text-brand-500' : 'text-gray-400'
                    )}
                  />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                    <span
                      className={clsx(
                        'text-xs px-2 py-0.5 rounded-full font-medium',
                        agent.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      )}
                    >
                      {agent.status === 'active' ? 'Attivo' : 'Inattivo'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{agent.description}</p>
                </div>
              </div>

              <button
                onClick={() => handleToggleClick(agent)}
                disabled={loading === agent.id}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  loading === agent.id && 'opacity-50 cursor-wait',
                  agent.status === 'active'
                    ? 'bg-red-50 text-red-600 hover:bg-red-100'
                    : 'bg-green-50 text-green-600 hover:bg-green-100'
                )}
              >
                <Power className="w-3.5 h-3.5" />
                {loading === agent.id
                  ? 'Attendere...'
                  : agent.status === 'active'
                  ? 'Disattiva'
                  : 'Attiva'}
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
                  {(agent.avgDuration / 1000).toFixed(1)}s
                </div>
                <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
                  <Clock className="w-3 h-3" /> Durata media
                </div>
              </div>
              <div className="text-center">
                <div
                  className={clsx(
                    'text-lg font-bold',
                    agent.successRate >= 0.9 ? 'text-green-600' : 'text-amber-500'
                  )}
                >
                  {Math.round(agent.successRate * 100)}%
                </div>
                <div className="text-xs text-gray-500 flex items-center justify-center gap-1">
                  <TrendingUp className="w-3 h-3" /> Successo
                </div>
              </div>
            </div>
          </div>
        ))}

        {agents.length === 0 && (
          <div className="text-center py-16">
            <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">Nessun agente configurato</p>
            <p className="text-gray-400 text-sm mt-1">
              Aggiungi un agente per iniziare ad automatizzare i tuoi processi
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
