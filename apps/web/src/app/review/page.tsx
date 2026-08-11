'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Brain, CheckCircle2, AlertCircle, Clock, RefreshCw, ArrowRight,
  GraduationCap, TrendingUp, BookOpen,
} from 'lucide-react'
import { reviewAPI, type ReviewDue, type ReviewItem } from '@/lib/api'

/** 自评按钮 -> 得分(映射到 0-100) */
const SELF_ASSESS = [
  { label: '记住了', score: 90, color: 'bg-emerald-500', desc: '清晰记得，间隔延长' },
  { label: '有点模糊', score: 60, color: 'bg-amber-500', desc: '能想起，需要再巩固' },
  { label: '忘了', score: 30, color: 'bg-red-500', desc: '记不清，尽快重学' },
]

export default function ReviewPage() {
  const [data, setData] = useState<ReviewDue | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await reviewAPI.getDue())
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const submit = async (item: ReviewItem, score: number) => {
    setSubmitting(item.id)
    try {
      await reviewAPI.submitReview(item.id, score)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : '提交失败')
    } finally {
      setSubmitting(null)
    }
  }

  const due = data?.due_items || []
  const upcoming = data?.upcoming_items || []

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-6 h-6 text-brand-600" /> 复习
        </h1>
        <p className="text-gray-500 mt-1">
          基于记忆规律(FSRS)为你排期，及时复习巩固知识。做完练习后会自动生成复习任务。
        </p>
      </div>

      {error && (
        <div className="mb-6 flex items-start gap-2 p-4 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}。请确认后端服务已启动。</span>
        </div>
      )}

      {/* 待复习概览 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Stat icon={Clock} label="今日待复习" value={String(data?.due_count ?? 0)} color="bg-brand-600" />
        <Stat icon={TrendingUp} label="即将到期" value={String(data?.upcoming_count ?? 0)} color="bg-blue-500" />
        <Stat icon={GraduationCap} label="全部知识点" value={String(data?.total ?? 0)} color="bg-teal-500" />
      </div>

      {loading ? (
        <div className="space-y-4">
          {[0, 1].map(i => <div key={i} className="glass-card p-6 animate-pulse"><div className="h-4 bg-gray-100 rounded w-1/3 mb-3" /><div className="h-3 bg-gray-100 rounded w-2/3" /></div>)}
        </div>
      ) : data && data.total === 0 ? (
        <div className="glass-card p-12 text-center empty-state">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-700 mb-2">还没有复习任务</p>
          <p className="text-gray-500 mb-6">去创建一个学习路径并完成练习，系统会为你的薄弱点自动安排复习。</p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link href="/learning" className="btn-primary">去学习 <ArrowRight className="w-4 h-4" /></Link>
            <Link href="/practice" className="btn-secondary">去练习</Link>
          </div>
        </div>
      ) : due.length === 0 ? (
        <div className="glass-card p-10 text-center empty-state">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-700 mb-1">今日复习已完成</p>
          <p className="text-gray-500">没有到期的复习任务，继续保持学习节奏。</p>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900">今日待复习 ({due.length})</h2>
          {due.map(item => (
            <div key={item.id} className="glass-card p-6">
              <div className="flex items-start justify-between flex-wrap gap-3 mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{item.topic}</h3>
                  <div className="text-sm text-gray-500 mt-1">
                    已复习 {item.review_count} 次 · 掌握度 {Math.round(item.mastery_level * 100)}%
                    {item.last_score != null ? ` · 上次得分 ${item.last_score}` : ''}
                  </div>
                </div>
                <div className="text-xs text-gray-400">记忆稳定性 {item.stability} 天</div>
              </div>
              <div className="flex gap-3">
                {SELF_ASSESS.map(a => (
                  <button
                    key={a.label}
                    disabled={submitting === item.id}
                    onClick={() => submit(item, a.score)}
                    className={`${a.color} text-white font-semibold px-4 py-2.5 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 flex-1 sm:flex-none`}
                  >
                    {submitting === item.id ? '提交中...' : a.label}
                    <span className="block text-xs font-normal opacity-80 mt-0.5">{a.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 即将到期 */}
      {!loading && upcoming.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-3">
            <BookOpen className="w-5 h-5 text-blue-500" /> 即将到期
          </h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {upcoming.map(item => (
              <div key={item.id} className="glass-card p-4 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="font-medium text-gray-800 truncate">{item.topic}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    掌握度 {Math.round(item.mastery_level * 100)}% · 已复习 {item.review_count} 次
                  </div>
                </div>
                <div className="text-xs text-gray-400 flex-shrink-0 ml-3">
                  下次 {item.due_at ? new Date(item.due_at).toLocaleDateString('zh-CN') : '—'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8 text-right">
        <button onClick={load} className="btn-secondary !py-2 !px-4 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> 刷新
        </button>
      </div>
    </main>
  )
}

function Stat({ icon: Icon, label, value, color }: { icon: typeof Clock; label: string; value: string; color: string }) {
  return (
    <div className="glass-card p-5">
      <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center mb-3`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  )
}
