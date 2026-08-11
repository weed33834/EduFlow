'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

/** 公开页面：无需登录即可访问 */
const PUBLIC_PATHS = ['/', '/login', '/register']

/**
 * 路由守卫：统一处理「用户点进某个页面时」的登录校验与跳转。
 * - 公开页面直接渲染
 * - 受保护页面：未登录 -> 跳转 /login；已登录 -> 正常渲染
 * 通过 layout 包裹，覆盖所有应用页，避免每个页面各自重复判断。
 */
export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, loading } = useAuth()

  const isPublic = PUBLIC_PATHS.includes(pathname)

  useEffect(() => {
    if (loading) return
    if (!isPublic && !user) {
      router.replace(`/login?redirect=${encodeURIComponent(pathname)}`)
    }
    // 已登录用户访问 /login /register 时，送回仪表盘
    if (isPublic && user && (pathname === '/login' || pathname === '/register')) {
      router.replace('/dashboard')
    }
  }, [loading, isPublic, user, pathname, router])

  // 未登录访问受保护页：显示加载占位，避免闪现空白
  if (loading || (!isPublic && !user)) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-400">
          <span className="w-5 h-5 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
          <span className="text-sm">加载中...</span>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
