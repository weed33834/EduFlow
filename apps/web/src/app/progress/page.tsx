'use client'
import { BarChart3, TrendingUp, Clock, Target, Brain, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function ProgressPage() {
  return (
    <div className="min-h-screen bg-[#F7F8FC]">
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">EF</span>
            </div>
            <span className="font-bold text-lg">EduFlow</span>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">仪表盘</Link>
            <Link href="/learning" className="text-gray-500 hover:text-gray-900">学习</Link>
            <Link href="/practice" className="text-gray-500 hover:text-gray-900">练习</Link>
            <Link href="/progress" className="text-brand-600 font-medium">进度</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-brand-600" /> 学习进度
        </h1>

        {/* Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: Target, label: '总体完成率', value: '42%', change: '+5%', color: 'bg-purple-500' },
            { icon: Clock, label: '总学习时长', value: '28h', change: '+3h', color: 'bg-blue-500' },
            { icon: Brain, label: '掌握知识点', value: '45', change: '+8', color: 'bg-teal-500' },
            { icon: TrendingUp, label: '本周活跃', value: '7天', change: '+2天', color: 'bg-amber-500' },
          ].map((s, i) => (
            <div key={i} className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5">
              <div className={`w-10 h-10 rounded-xl ${s.color} flex items-center justify-center mb-3`}>
                <s.icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{s.value}</div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-sm text-gray-500">{s.label}</span>
                <span className="text-xs text-green-600 font-medium">{s.change}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Course Progress */}
          <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">课程进度</h2>
            <div className="space-y-4">
              {[
                { name: 'Python 基础入门', progress: 65, color: 'from-brand-600 to-purple-500' },
                { name: '数据结构与算法', progress: 30, color: 'from-teal-400 to-cyan-500' },
                { name: 'Web 开发基础', progress: 0, color: 'from-blue-500 to-indigo-500' },
              ].map((c, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-gray-700 font-medium">{c.name}</span>
                    <span className="text-gray-500">{c.progress}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r ${c.color} rounded-full transition-all`} style={{ width: `${c.progress}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Weak Points */}
          <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-500" /> 薄弱点分析
            </h2>
            <div className="space-y-3">
              {[
                { topic: '递归算法', mastery: 25, tag: '需加强' },
                { topic: '面向对象编程', mastery: 40, tag: '需练习' },
                { topic: '文件 I/O 操作', mastery: 55, tag: '继续努力' },
                { topic: '异常处理', mastery: 70, tag: '良好' },
              ].map((w, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700">{w.topic}</span>
                      <span className="text-gray-500">{w.mastery}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${w.mastery < 40 ? 'bg-red-400' : w.mastery < 60 ? 'bg-amber-400' : 'bg-green-400'}`} style={{ width: `${w.mastery}%` }} />
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${w.mastery < 40 ? 'bg-red-100 text-red-600' : w.mastery < 60 ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'}`}>{w.tag}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}