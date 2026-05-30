import AgentList from '@/components/AgentList'
import ExecutionLogs from '@/components/ExecutionLogs'
import Stats from '@/components/Stats'
import NotificationPanel from '@/components/NotificationPanel'
import AgentRunner from '@/components/AgentRunner'
import { Bot } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-gray-900">AI Automation Agent</span>
              <span className="hidden sm:inline text-gray-400 text-sm ml-2">Dashboard</span>
            </div>
          </div>
          <NotificationPanel />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Statistiche */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Panoramica di oggi
          </h2>
          <Stats />
        </section>

        {/* Esegui agente */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Esegui un agente
          </h2>
          <AgentRunner />
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Lista agenti */}
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
              Agenti configurati
            </h2>
            <AgentList />
          </section>

          {/* Log esecuzioni */}
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
              Log esecuzioni recenti
            </h2>
            <ExecutionLogs />
          </section>
        </div>
      </main>

      <footer className="mt-16 border-t border-gray-100 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-400">
          AI Automation Agent · Groq llama-3.3-70b-versatile · FastAPI + Next.js 14
        </div>
      </footer>
    </div>
  )
}
