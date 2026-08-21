import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import RouteGuard from '@/components/RouteGuard'

export const metadata: Metadata = {
  title: 'EduFlow Agent — AI 编程学习伙伴',
  description: '一个会教编程、会出题、会判题的 AI 学习 Agent',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        <AuthProvider>
          <RouteGuard>{children}</RouteGuard>
        </AuthProvider>
      </body>
    </html>
  )
}
