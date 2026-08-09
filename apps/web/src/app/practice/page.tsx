'use client'
import { useState } from 'react'
import { Brain, RefreshCw, CheckCircle, XCircle, ArrowRight } from 'lucide-react'
import Link from 'next/link'

const sampleQuestions = [
  { id: 1, type: 'choice', question: 'Python 中，以下哪个是可变数据类型？', options: ['元组 (tuple)', '字符串 (str)', '列表 (list)', '整数 (int)'], answer: 2, explanation: '列表 (list) 是可变的，可以增删改元素。元组、字符串和整数都是不可变的。' },
  { id: 2, type: 'choice', question: '以下哪个关键字用于定义函数？', options: ['function', 'def', 'define', 'func'], answer: 1, explanation: 'Python 使用 def 关键字来定义函数。' },
  { id: 3, type: 'choice', question: '列表推导式 [x**2 for x in range(5)] 的结果是？', options: ['[0, 1, 4, 9, 16]', '[1, 4, 9, 16, 25]', '[0, 2, 4, 6, 8]', '[0, 1, 2, 3, 4]'], answer: 0, explanation: 'range(5) 生成 0-4，每个数的平方分别为 0, 1, 4, 9, 16。' },
]

export default function PracticePage() {
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [score, setScore] = useState(0)
  const [finished, setFinished] = useState(false)

  const q = sampleQuestions[current]

  const handleSelect = (idx: number) => {
    if (showResult) return
    setSelected(idx)
    setShowResult(true)
    if (idx === q.answer) setScore(prev => prev + 1)
  }

  const handleNext = () => {
    if (current < sampleQuestions.length - 1) {
      setCurrent(prev => prev + 1)
      setSelected(null)
      setShowResult(false)
    } else {
      setFinished(true)
    }
  }

  const handleRestart = () => {
    setCurrent(0)
    setSelected(null)
    setShowResult(false)
    setScore(0)
    setFinished(false)
  }

  if (finished) {
    return (
      <div className="min-h-screen bg-[#F7F8FC] flex items-center justify-center">
        <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-10 text-center max-w-md">
          <Brain className="w-16 h-16 text-brand-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">练习完成！</h2>
          <p className="text-5xl font-black text-brand-600 mb-2">{score}/{sampleQuestions.length}</p>
          <p className="text-gray-500 mb-6">正确率 {Math.round(score / sampleQuestions.length * 100)}%</p>
          <div className="flex gap-3 justify-center">
            <button onClick={handleRestart} className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-full font-medium hover:bg-brand-700 transition-all">
              <RefreshCw className="w-4 h-4" /> 重新练习
            </button>
            <Link href="/dashboard" className="flex items-center gap-2 bg-white text-brand-600 px-6 py-2.5 rounded-full font-medium border border-brand-200 hover:bg-brand-50 transition-all">
              返回仪表盘
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F7F8FC]">
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">EF</span>
            </div>
            <span className="font-bold text-lg">EduFlow</span>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/dashboard" className="text-gray-500 hover:text-gray-900">仪表盘</Link>
            <Link href="/learning" className="text-gray-500 hover:text-gray-900">学习</Link>
            <Link href="/practice" className="text-brand-600 font-medium">练习</Link>
            <Link href="/progress" className="text-gray-500 hover:text-gray-900">进度</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2"><Brain className="w-5 h-5 text-brand-600" /> 自适应练习</h1>
          <span className="text-sm text-gray-500">第 {current + 1}/{sampleQuestions.length} 题</span>
        </div>

        <div className="bg-white/80 backdrop-blur-xl border border-gray-100 rounded-2xl p-8">
          <div className="h-1.5 bg-gray-100 rounded-full mb-8 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-brand-600 to-purple-500 rounded-full transition-all" style={{ width: `${(current + 1) / sampleQuestions.length * 100}%` }} />
          </div>

          <div className="mb-2">
            <span className="text-xs font-medium text-brand-600 bg-brand-100 px-2 py-0.5 rounded-full">选择题</span>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-6">{q.question}</h2>

          <div className="space-y-3">
            {q.options.map((opt, idx) => {
              let bg = 'bg-gray-50 hover:bg-gray-100 border-gray-200'
              let icon = null
              if (showResult && idx === q.answer) { bg = 'bg-green-50 border-green-500'; icon = <CheckCircle className="w-5 h-5 text-green-500" /> }
              else if (showResult && idx === selected && idx !== q.answer) { bg = 'bg-red-50 border-red-500'; icon = <XCircle className="w-5 h-5 text-red-500" /> }
              else if (idx === selected) { bg = 'bg-brand-50 border-brand-500' }
              return (
                <button key={idx} onClick={() => handleSelect(idx)} className={`w-full flex items-center justify-between p-4 rounded-xl border ${bg} transition-all text-left`}>
                  <span className="text-sm font-medium text-gray-900">{opt}</span>
                  {icon}
                </button>
              )
            })}
          </div>

          {showResult && (
            <div className="mt-6 p-4 bg-brand-50 rounded-xl border border-brand-100">
              <p className="text-sm text-gray-700"><span className="font-semibold">解析：</span>{q.explanation}</p>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            {showResult && (
              <button onClick={handleNext} className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-full font-medium hover:bg-brand-700 transition-all">
                {current < sampleQuestions.length - 1 ? '下一题' : '查看结果'} <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}