'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

const PUBLIC_PATHS = ['/', '/login', '/register']

export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return

    const path = window.location.pathname
    const isPublic = PUBLIC_PATHS.some((p) => path === p)

    if (!user && !isPublic) {
      router.replace('/login')
    }
    if (user && (path === '/login' || path === '/register')) {
      router.replace('/chat')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
      </div>
    )
  }

  return <>{children}</>
}
