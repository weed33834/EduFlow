'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/dashboard', label: '仪表盘' },
  { href: '/learning', label: '学习' },
  { href: '/practice', label: '练习' },
  { href: '/progress', label: '进度' },
]

export default function Navbar() {
  const path = usePathname()
  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center">
            <span className="text-white font-bold text-sm">EF</span>
          </div>
          <span className="font-bold text-lg">EduFlow</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          {navItems.map(item => (
            <Link key={item.href} href={item.href} className={path === item.href ? 'text-brand-600 font-medium' : 'text-gray-500 hover:text-gray-900'}>
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}