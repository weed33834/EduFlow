'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  BookOpen,
  Brain,
  BarChart3,
  GraduationCap,
  Settings,
  LogOut,
  Menu,
  X,
  RefreshCw,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { getInitials, cn } from '@/lib/utils'

const navItems = [
  { href: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { href: '/learning', label: '学习', icon: BookOpen },
  { href: '/review', label: '复习', icon: RefreshCw },
  { href: '/practice', label: '练习', icon: Brain },
  { href: '/progress', label: '进度', icon: BarChart3 },
  { href: '/ai-tutor', label: 'AI助手', icon: GraduationCap },
]

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, loading, logout } = useAuth()
  const [open, setOpen] = useState(false)

  const handleLogout = () => {
    logout()
    setOpen(false)
    router.push('/login')
  }

  const isHome = pathname === '/'

  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-sm">EF</span>
          </div>
          <span className="font-bold text-lg text-gray-900">EduFlow</span>
        </Link>

        {/* 桌面端导航 */}
        {user && !loading ? (
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map(item => {
              const active = pathname === item.href || pathname.startsWith(item.href + '/')
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium transition-colors',
                    active
                      ? 'text-brand-600 bg-brand-50'
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        ) : (
          <nav className="hidden lg:flex items-center gap-6 text-sm">
            {isHome ? (
              <>
                <Link href="/#features" className="text-gray-500 hover:text-gray-900">核心功能</Link>
                <Link href="/#agents" className="text-gray-500 hover:text-gray-900">AI 助手</Link>
              </>
            ) : null}
          </nav>
        )}

        {/* 右侧操作区 */}
        <div className="flex items-center gap-2">
          {loading ? (
            <div className="w-9 h-9 rounded-full bg-gray-100 animate-pulse" />
          ) : user ? (
            <div className="hidden lg:flex items-center gap-2">
              <Link
                href="/settings"
                className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-full hover:bg-gray-50 transition-colors"
                title="设置"
              >
                <Avatar user={user} />
                <span className="text-sm font-medium text-gray-700 max-w-[120px] truncate">
                  {user.display_name || user.username}
                </span>
              </Link>
              <Link
                href="/settings"
                className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                title="设置"
              >
                <Settings className="w-5 h-5" />
              </Link>
              <button
                onClick={handleLogout}
                className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                title="退出登录"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div className="hidden lg:flex items-center gap-2">
              <Link href="/login" className="px-4 py-2 rounded-full text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                登录
              </Link>
              <Link href="/register" className="btn-primary !px-5 !py-2 text-sm">
                注册
              </Link>
            </div>
          )}

          {/* 移动端菜单按钮 */}
          <button
            onClick={() => setOpen(v => !v)}
            className="lg:hidden w-9 h-9 rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-100"
            aria-label="菜单"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* 移动端下拉菜单 */}
      {open && (
        <div className="lg:hidden border-t border-gray-100 bg-white">
          <div className="max-w-7xl mx-auto px-4 py-3 space-y-1">
            {user ? (
              <>
                <div className="flex items-center gap-3 px-2 py-3 mb-2 border-b border-gray-100">
                  <Avatar user={user} />
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-gray-900 truncate">
                      {user.display_name || user.username}
                    </div>
                    <div className="text-xs text-gray-400 truncate">{user.email}</div>
                  </div>
                </div>
                {navItems.map(item => {
                  const active = pathname === item.href || pathname.startsWith(item.href + '/')
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      className={cn(
                        'flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                        active ? 'text-brand-600 bg-brand-50' : 'text-gray-600 hover:bg-gray-50'
                      )}
                    >
                      <item.icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  )
                })}
                <Link
                  href="/settings"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50"
                >
                  <Settings className="w-4 h-4" />
                  设置
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50"
                >
                  <LogOut className="w-4 h-4" />
                  退出登录
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 py-2">
                <Link
                  href="/login"
                  onClick={() => setOpen(false)}
                  className="btn-secondary w-full"
                >
                  登录
                </Link>
                <Link
                  href="/register"
                  onClick={() => setOpen(false)}
                  className="btn-primary w-full"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}

function Avatar({ user }: { user: { avatar_url?: string; display_name?: string; username?: string } }) {
  if (user.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt="头像"
        className="w-8 h-8 rounded-full object-cover border border-gray-100"
      />
    )
  }
  const initials = getInitials(user.display_name || user.username)
  return (
    <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-semibold">
      {initials}
    </div>
  )
}
