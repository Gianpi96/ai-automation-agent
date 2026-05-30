export interface AgentInfo {
  id: string
  name: string
  description: string
  status: 'active' | 'inactive'
  lastRun?: string
  runsToday: number
  avgDuration: number
  successRate: number
}

export interface ExecutionLog {
  id: string
  agentId: string
  agentName: string
  status: 'completed' | 'failed' | 'running' | 'timeout'
  startedAt: string
  duration: number
  iterations: number
  toolsUsed: string[]
  error?: string
}

export interface Stats {
  processedToday: number
  timeSavedMinutes: number
  successRate: number
  activeAgents: number
}

export interface Notification {
  id: string
  type: string
  message: string
  timestamp: string
  read: boolean
}

export interface AgentResult {
  answer: string
  tools_used: string[]
  iterations: number
  confidence: number
  status: string
  total_duration_ms: number
}
