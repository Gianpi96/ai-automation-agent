'use client'

type MessageHandler = (data: Record<string, unknown>) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private handlers: Set<MessageHandler> = new Set()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private url: string
  private connected = false

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.connected = true
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handlers.forEach((h) => h(data))
      } catch (e) {
        console.error('[WS] Parse error', e)
      }
    }

    this.ws.onclose = () => {
      this.connected = false
      this.reconnectTimer = setTimeout(() => this.connect(), 3000)
    }

    // onerror fires before onclose; just let onclose handle the reconnect.
    // Log only if it was previously connected (unexpected drop), not on first connect attempt.
    this.ws.onerror = () => {
      if (this.connected) {
        console.warn('[WS] Connection lost, will retry in 3s...')
      }
      this.ws?.close()
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  subscribe(handler: MessageHandler) {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

const WS_URL =
  typeof window !== 'undefined'
    ? `ws://${window.location.hostname}:8000/ws`
    : 'ws://localhost:8000/ws'

export const wsManager = new WebSocketManager(WS_URL)
