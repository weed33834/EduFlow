'use client'
import { BookOpen, ChevronRight, Play, Clock, CheckCircle, Lock, FileText } from 'lucide-react'
import Link from 'next/link'

export default function LearningPage() {
  const modules = [
    { title: 'Python 基础入门', progress: 65, lessons: [
      { name: '变量与数据类型', duration: '25min', done: true },
      { name: '字符串操作', duration: '20min', done: true },
      { name: '列表与元组', duration: '30min', done: false },
      { name: '条件判断', duration: '25min', done: false },
      { name: '循环语句', duration: '35min', done: false },
    ]},
    { title: '数据结构与算法', progress: 30, lessons: [
      { name: '数组基础', duration: '20min', done: true },
      { name: '链表操作', duration: '30min', done: false },
      { name: '栈与队列', duration: '25min', done: false },
    ]},
  ]

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
            <Link href="/learning" className="text-brand-600 font-medium">学习</Link>
            <Link href="/practice" className="text-gray-500 hover:text-gray-900">练习</Link>
            <Link href="/progress" className="text-gray-500 hover:text-gray-900">进度</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-brand-600" /> 学习空间
        </h1>
        
        {modules.map((mod, i) => (
          <div key={i} className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-6 mb-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">{mod.title}</h2>
              <span className="text-sm text-gray-500">{mod.progress}% 完成</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full mb-6 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-brand-600 to-purple-500 rounded-full" style={{ width: `${mod.progress}%` }} />
            </div>
            <div className="space-y-2">
              {mod.lessons.map((l, j) => (
                <div key={j} className={`flex items-center justify-between p-3 rounded-xl transition-colors ${l.done ? 'bg-green-50' : 'hover:bg-gray-50'}`}>
                  <div className="flex items-center gap-3">
                    {l.done ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <FileText className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <span className={`text-sm font-medium ${l.done ? 'text-gray-500 line-through' : 'text-gray-900'}`}>{l.name}</span>
                      <span className="text-xs text-gray-400 ml-2 flex items-center gap-1"><Clock className="w-3 h-3" />{l.duration}</span>
                    </div>
                  </div>
                  {!l.done && (
                    <button className="flex items-center gap-1 text-sm text-brand-600 font-medium hover:text-brand-700">
                      开始 <Play className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </main>
    </div>
  )
}