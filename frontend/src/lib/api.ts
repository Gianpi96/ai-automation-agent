const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  runAgent: (query: string, context?: Record<string, unknown>) =>
    fetchApi('/api/agent/run', {
      method: 'POST',
      body: JSON.stringify({ query, context }),
    }),

  listTools: () => fetchApi('/api/agent/tools'),

  uploadDocument: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE_URL}/api/documents/upload`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  },

  queryDocument: (document_id: string, question: string) =>
    fetchApi('/api/documents/query', {
      method: 'POST',
      body: JSON.stringify({ document_id, question }),
    }),

  getInbox: () => fetchApi('/api/emails/inbox'),

  processEmail: (email_id: string) =>
    fetchApi(`/api/emails/process/${email_id}`, { method: 'POST' }),

  processAllEmails: () =>
    fetchApi('/api/emails/process-all', { method: 'POST' }),

  approveDraft: (draft_id: string, approved: boolean, modifications?: string) =>
    fetchApi(`/api/emails/drafts/${draft_id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved, modifications }),
    }),

  getDrafts: () => fetchApi('/api/emails/drafts'),

  healthCheck: () => fetchApi('/health'),
}
