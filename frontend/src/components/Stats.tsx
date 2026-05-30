'use client'

import { BarChart3, Clock, CheckCircle2, Activity } from 'lucide-react'
import type { Stats } from '@/types'

const MOCK_STATS: Stats = {
  processedToday: 44,
  timeSavedMinutes: 132,
  successRate: 0.91,
  activeAgents: 3,
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
  color: string
}

function StatCard({ icon, label, value, sub, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm font-medium text-gray-700 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

export default function Stats({ stats = MOCK_STATS }: { stats?: Stats }) {
  const timeSaved =
    stats.timeSavedMinutes >= 60
      ? `${Math.floor(stats.timeSavedMinutes / 60)}h ${stats.timeSavedMinutes % 60}m`
      : `${stats.timeSavedMinutes}m`

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        icon={<BarChart3 className="w-5 h-5 text-brand-600" />}
        label="Elaborazioni oggi"
        value={stats.processedToday.toString()}
        sub="richieste processate"
        color="bg-brand-50"
      />
      <StatCard
        icon={<Clock className="w-5 h-5 text-purple-600" />}
        label="Tempo risparmiato"
        value={timeSaved}
        sub="stima basata su durata media"
        color="bg-purple-50"
      />
      <StatCard
        icon={<CheckCircle2 className="w-5 h-5 text-green-600" />}
        label="Tasso di successo"
        value={`${Math.round(stats.successRate * 100)}%`}
        sub="ultime 24 ore"
        color="bg-green-50"
      />
      <StatCard
        icon={<Activity className="w-5 h-5 text-amber-600" />}
        label="Agenti attivi"
        value={stats.activeAgents.toString()}
        sub="su 3 configurati"
        color="bg-amber-50"
      />
    </div>
  )
}
