'use client'
import { useState } from 'react'
import { BookOpen, Brain, Target, BarChart3, Clock, ChevronRight, Award, TrendingUp, Zap, Calendar } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#F7F8FC]">
      {/* Top Nav */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">EF</span>
            </div>
            <span className="font-bold text-lg">EduFlow</span>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/dashboard" className="text-brand-600 font-medium">仪表盘</Link>
            <Link href="/learning" className="text-gray-500 hover:text-gray-900">学习</Link>
            <Link href="/practice" className="text-gray-500 hover:text-gray-900">练习</Link>
            <Link href="/progress" className="text-gray-500 hover:text-gray-900">进度</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">欢迎回来，同学 👋</h1>
          <p className="text-gray-500 mt-1">继续你的学习之旅，今天有 3 个待完成模块</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: BookOpen, label: '学习中', value: '3', color: 'bg-purple-500' },
            { icon: Brain, label: '已掌握', value: '12', color: 'bg-teal-500' },
            { icon: Clock, label: '学习时长', value: '28h', color: 'bg-blue-500' },
            { icon: Zap, label: '连续学习', value: '7天', color: 'bg-amber-500' },
          ].map((s, i) => (
            <div key={i} className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5 hover:shadow-md transition-shadow">
              <div className={`w-10 h-10 rounded-xl ${s.color} flex items-center justify-center mb-3`}>
                <s.icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{s.value}</div>
              <div className="text-sm text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Learning Path */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-brand-600" /> 学习路径
            </h2>
            {[
              { title: 'Python 基础入门', progress: 65, desc: '变量、数据类型、控制流', eta: '2天' },
              { title: '数据结构与算法', progress: 30, desc: '数组、链表、栈与队列', eta: '5天' },
              { title: 'Web 开发基础', progress: 0, desc: 'HTML、CSS、JavaScript', eta: '7天' },
            ].map((p, i) => (
              <div key={i} className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5 hover:shadow-md transition-all group">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors">{p.title}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">{p.desc}</p>
                  </div>
                  <span className="text-xs text-gray-400 flex items-center gap-1"><Clock className="w-3 h-3" />{p.eta}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-brand-600 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${p.progress}%` }} />
                  </div>
                  <span className="text-sm font-medium text-gray-600">{p.progress}%</span>
                </div>
              </div>
            ))}
          </div>

          {/* Right Sidebar */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-teal-500" /> 学习建议
            </h2>
            <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5 space-y-4">
              {[
                { icon: Brain, text: '你的 Python 基础掌握不错，可以开始学习数据结构了', color: 'text-teal-500' },
                { icon: Award, text: '已经连续学习 7 天，继续保持！', color: 'text-amber-500' },
                { icon: BarChart3, text: '上周学习时长增长 20%，进步明显', color: 'text-blue-500' },
              ].map((a, i) => (
                <div key={i} className="flex gap-3">
                  <a.icon className={`w-5 h-5 ${a.color} flex-shrink-0 mt-0.5`} />
                  <p className="text-sm text-gray-600 leading-relaxed">{a.text}</p>
                </div>
              ))}
            </div>

            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mt-6">
              <Calendar className="w-5 h-5 text-brand-600" /> 今日计划
            </h2>
            <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-5">
              <div className="space-y-3">
                {[
                  { time: '09:00', task: '数据结构 - 数组与链表', done: true },
                  { time: '10:30', task: '练习：数组操作', done: false },
                  { time: '14:00', task: '复习：Python 函数', done: false },
                ].map((t, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${t.done ? 'border-teal-500 bg-teal-500' : 'border-gray-300'}`}>
                      {t.done && <div className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                    <span className="text-xs text-gray-400 w-12">{t.time}</span>
                    <span className={`text-sm ${t.done ? 'text-gray-400 line-through' : 'text-gray-700'}`}>{t.task}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}