'use client'

import { useEffect, useState } from 'react'
import { BarChart3, Clock, CheckCircle2, Activity } from 'lucide-react'
import { api } from '@/lib/api'

interface StatsData {
  processedToday: number
  timeSavedMinutes: number
  successRate: number
  activeAgents: number
}

function StatCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
  color: string
}) {
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

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
      <div className="w-10 h-10 rounded-lg bg-gray-100 mb-3" />
      <div className="h-7 w-16 bg-gray-100 rounded mb-2" />
      <div className="h-4 w-28 bg-gray-100 rounded" />
    </div>
  )
}

export default function Stats() {
  const [stats, setStats] = useState<StatsData | null>(null)

  const load = async () => {
    try {
      const data = await api.getStats() as StatsData
      setStats(data)
    } catch {
      // backend non raggiungibile — mostra zeri
      setStats({ processedToday: 0, timeSavedMinutes: 0, successRate: 0, activeAgents: 0 })
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 10000) // aggiorna ogni 10s
    return () => clearInterval(interval)
  }, [])

  if (!stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  const timeSaved = stats.timeSavedMinutes >= 60
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
        value={stats.processedToday === 0 ? '0m' : timeSaved}
        sub="~3 min per elaborazione"
        color="bg-purple-50"
      />
      <StatCard
        icon={<CheckCircle2 className="w-5 h-5 text-green-600" />}
        label="Tasso di successo"
        value={stats.processedToday === 0 ? '—' : `${Math.round(stats.successRate * 100)}%`}
        sub="ultime 24 ore"
        color="bg-green-50"
      />
      <StatCard
        icon={<Activity className="w-5 h-5 text-amber-600" />}
        label="Agenti usati oggi"
        value={stats.activeAgents.toString()}
        sub="su 3 disponibili"
        color="bg-amber-50"
      />
    </div>
  )
}
