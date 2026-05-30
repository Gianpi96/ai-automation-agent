import { getToken, clearToken } from './auth'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Sessione scaduta')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  login: async (username: string, password: string) => {
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Credenziali non valide' }))
      throw new Error(err.detail)
    }
    return res.json() as Promise<{ access_token: string }>
  },

  runAgent: (query: string, context?: Record<string, unknown>) =>
    fetchApi('/api/agent/run', { method: 'POST', body: JSON.stringify({ query, context }) }),

  listTools: () => fetchApi('/api/agent/tools'),
  getStats: () => fetchApi('/api/agent/stats'),
  getLogs: () => fetchApi('/api/agent/logs'),
  getAgentsStats: () => fetchApi('/api/agent/agents/stats'),

  uploadDocument: async (file: File) => {
    const token = getToken()
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE_URL}/api/documents/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  queryDocument: (document_id: string, question: string) =>
    fetchApi('/api/documents/query', { method: 'POST', body: JSON.stringify({ document_id, question }) }),

  getInbox: () => fetchApi('/api/emails/inbox'),
  processEmail: (email_id: string) => fetchApi(`/api/emails/process/${email_id}`, { method: 'POST' }),
  processAllEmails: () => fetchApi('/api/emails/process-all', { method: 'POST' }),
  approveDraft: (draft_id: string, approved: boolean, modifications?: string) =>
    fetchApi(`/api/emails/drafts/${draft_id}/approve`, { method: 'POST', body: JSON.stringify({ approved, modifications }) }),
  getDrafts: () => fetchApi('/api/emails/drafts'),

  getImapInbox: (limit = 10) => fetchApi(`/api/emails/imap/inbox?limit=${limit}`),
  processImapEmails: (limit = 10) => fetchApi(`/api/emails/imap/process-all?limit=${limit}`, { method: 'POST' }),

  healthCheck: () => fetch(`${BASE_URL}/health`).then(r => r.json()),
}
