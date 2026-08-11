import Link from 'next/link'
import { Home, Search, BookOpen, GraduationCap } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        {/* 404 大字 */}
        <div className="relative mb-8 inline-block">
          <h1
            className="text-[120px] md:text-[160px] font-black leading-none bg-gradient-to-br from-brand-600 via-purple-600 to-teal-500 bg-clip-text text-transparent"
            style={{ letterSpacing: '-0.05em' }}
          >
            404
          </h1>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-brand-100/40 blur-3xl animate-pulse" />
          </div>
        </div>

        {/* 图标 */}
        <div className="w-16 h-16 rounded-2xl bg-brand-600 flex items-center justify-center mx-auto mb-6 shadow-lg">
          <Search className="w-8 h-8 text-white" />
        </div>

        {/* 文案 */}
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          页面走丢了
        </h2>
        <p className="text-gray-500 mb-8 leading-relaxed">
          你访问的页面不存在或已被移动。别担心，让我们一起回到学习正轨。
        </p>

        {/* 按钮 */}
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link
            href="/"
            className="btn-primary"
          >
            <Home className="w-4 h-4" /> 返回首页
          </Link>
          <Link
            href="/dashboard"
            className="btn-secondary"
          >
            <BookOpen className="w-4 h-4" /> 前往仪表盘
          </Link>
        </div>

        {/* 辅助链接 */}
        <div className="mt-10 pt-8 border-t border-gray-100">
          <p className="text-sm text-gray-400 mb-4">或者试试这些</p>
          <div className="flex items-center justify-center gap-6 text-sm">
            <Link
              href="/learning"
              className="text-gray-500 hover:text-brand-600 transition-colors flex items-center gap-1.5"
            >
              <BookOpen className="w-4 h-4" /> 学习
            </Link>
            <Link
              href="/practice"
              className="text-gray-500 hover:text-brand-600 transition-colors flex items-center gap-1.5"
            >
              <Search className="w-4 h-4" /> 练习
            </Link>
            <Link
              href="/ai-tutor"
              className="text-gray-500 hover:text-brand-600 transition-colors flex items-center gap-1.5"
            >
              <GraduationCap className="w-4 h-4" /> AI 导师
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
