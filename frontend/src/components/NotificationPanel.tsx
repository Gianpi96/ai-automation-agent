'use client'

import { useEffect, useRef, useState } from 'react'
import { Bell, X, Wifi, WifiOff } from 'lucide-react'
import { wsManager } from '@/lib/websocket'
import type { Notification } from '@/types'
import clsx from 'clsx'

export default function NotificationPanel() {
  const [connected, setConnected] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unread, setUnread] = useState(0)
  const [open, setOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    wsManager.connect()

    const unsub = wsManager.subscribe((data) => {
      if (data.type === 'connected') {
        setConnected(true)
        return
      }
      if (data.type === 'heartbeat' || data.type === 'pong') {
        setConnected(true)
        return
      }

      const notif: Notification = {
        id: `n_${Date.now()}`,
        type: String(data.type),
        message: data.payload
          ? JSON.stringify(data.payload).slice(0, 120)
          : String(data.message || data.type),
        timestamp: String(data.timestamp || new Date().toISOString()),
        read: false,
      }
      setNotifications((prev) => [notif, ...prev].slice(0, 50))
      setUnread((n) => n + 1)
    })

    // Detect network going offline
    const handleOffline = () => setConnected(false)
    const handleOnline = () => { setConnected(false); wsManager.connect() }
    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)

    // Poll connected state every 4s to reflect reconnects/disconnects
    const poll = setInterval(() => {
      setConnected(wsManager.isConnected())
    }, 4000)

    return () => {
      unsub()
      clearInterval(poll)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [])

  // Close panel on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnread(0)
  }

  const dismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => { setOpen(!open); if (!open) markAllRead() }}
        className="relative flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
      >
        {connected ? (
          <Wifi className="w-4 h-4 text-green-500" />
        ) : (
          <WifiOff className="w-4 h-4 text-gray-400" />
        )}
        <Bell className="w-4 h-4 text-gray-600" />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-80 bg-white border border-gray-200 rounded-xl shadow-xl z-40 overflow-hidden">
          <div className="flex items-center justify-between p-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-gray-600" />
              <span className="font-semibold text-gray-900 text-sm">Notifiche</span>
              <span
                className={clsx(
                  'text-xs px-2 py-0.5 rounded-full',
                  connected ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'
                )}
              >
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>
            {notifications.length > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-brand-500 hover:text-brand-700"
              >
                Segna tutte lette
              </button>
            )}
          </div>

          <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 ? (
              <div className="py-10 text-center">
                <Bell className="w-8 h-8 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">Nessuna notifica</p>
                <p className="text-xs text-gray-300 mt-1">
                  Le attività degli agenti appariranno qui in tempo reale
                </p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={clsx(
                    'flex items-start gap-3 px-4 py-3',
                    !n.read && 'bg-brand-50/40'
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-gray-700 capitalize">{n.type}</div>
                    <div className="text-xs text-gray-500 mt-0.5 break-words">{n.message}</div>
                    <div className="text-xs text-gray-300 mt-1">
                      {new Date(n.timestamp).toLocaleTimeString('it-IT')}
                    </div>
                  </div>
                  <button
                    onClick={() => dismiss(n.id)}
                    className="text-gray-300 hover:text-gray-500 flex-shrink-0"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
