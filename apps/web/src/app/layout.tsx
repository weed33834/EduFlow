import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import Navbar from '@/components/layout/Navbar'

export const metadata: Metadata = {
  title: 'EduFlow 畅学 — AI驱动的学生自学平台',
  description: 'EduFlow 畅学 — 让学习自然流畅，让知识触手可及。AI驱动的学生自学平台。',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        <AuthProvider>
          <Navbar />
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
