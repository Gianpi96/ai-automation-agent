import type { Metadata } from 'next'
import './globals.css'
import BackendBanner from '@/components/BackendBanner'

export const metadata: Metadata = {
  title: 'AI Automation Agent',
  description: 'Dashboard per agenti AI automatizzati',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body>
        <BackendBanner />
        {children}
      </body>
    </html>
  )
}
