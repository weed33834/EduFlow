'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  BookOpen, Brain, Clock, Target, TrendingUp, Award, BarChart3,
  GraduationCap, ChevronRight, Sparkles, Zap, AlertCircle, RefreshCw, ArrowRight, RefreshCcw,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { learningAPI, progressAPI, reviewAPI, type LearningPath, type ProgressOverview, type ReviewDue } from '@/lib/api'
import { formatDuration, getDifficultyColor, getDifficultyLabel } from '@/lib/utils'

export default function DashboardPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  const [paths, setPaths] = useState<LearningPath[]>([])
  const [progress, setProgress] = useState<ProgressOverview | null>(null)
  const [review, setReview] = useState<ReviewDue | null>(null)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  const loadData = async () => {
    if (!user) return
    setFetching(true)
    setError('')
    try {
      const [pathsData, progressData, reviewData] = await Promise.allSettled([
        learningAPI.getPaths(),
        progressAPI.getMyProgress(),
        reviewAPI.getDue(),
      ])
      if (pathsData.status === 'fulfilled') setPaths(pathsData.value || [])
      else setPaths([])
      if (progressData.status === 'fulfilled') setProgress(progressData.value)
      else setProgress(null)
      if (reviewData.status === 'fulfilled') setReview(reviewData.value)
      else setReview(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setFetching(false)
    }
  }

  useEffect(() => {
    if (user) loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  if (loading || (!user && !error)) {
    return <FullScreenLoader />
  }
  if (!user) return null

  const inProgressCount = paths.filter(p => (p.status || 'active') === 'active').length
  const completedCount = paths.filter(p => p.status === 'completed').length
  const totalLearningMinutes =
    progress?.details?.reduce((sum, d) => sum + (d.learning_time || 0), 0) || 0
  const avgScore =
    progress && progress.details && progress.details.length > 0
      ? Math.round(progress.overall_completion)
      : 0

  const stats = [
    { icon: BookOpen, label: '学习中', value: String(inProgressCount), color: 'bg-brand-600' },
    { icon: Brain, label: '已掌握', value: String(completedCount), color: 'bg-teal-500' },
    { icon: Clock, label: '学习时长', value: formatDuration(totalLearningMinutes), color: 'bg-blue-500' },
    { icon: Zap, label: '平均完成度', value: `${avgScore}%`, color: 'bg-amber-500' },
  ]

  const suggestions = buildSuggestions(paths, progress)

  const quickEntries = [
    { icon: BookOpen, label: '学习空间', desc: '管理学习路径与模块', href: '/learning', color: 'from-purple-500 to-indigo-500' },
    { icon: Brain, label: '开始练习', desc: 'AI 出题，即时反馈', href: '/practice', color: 'from-teal-400 to-cyan-500' },
    { icon: BarChart3, label: '学习进度', desc: '查看进度与薄弱点', href: '/progress', color: 'from-blue-500 to-indigo-500' },
    { icon: GraduationCap, label: 'AI 导师', desc: '随时提问，按需辅导', href: '/ai-tutor', color: 'from-brand-600 to-purple-700' },
  ]

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* 欢迎区 */}
      <div className="mb-8 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            欢迎回来，{user.display_name || user.username} 👋
          </h1>
          <p className="text-gray-500 mt-1">
            继续你的学习之旅{paths.length > 0 ? `，当前有 ${paths.length} 个学习路径` : ''}
          </p>
        </div>
        <button onClick={loadData} className="btn-secondary !py-2 !px-4 text-sm">
          <RefreshCw className={`w-4 h-4 ${fetching ? 'animate-spin' : ''}`} /> 刷新
        </button>
      </div>

      {error && (
        <div className="mb-6 flex items-start gap-2 p-4 rounded-xl bg-amber-50 border border-amber-100 text-sm text-amber-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>部分数据加载失败：{error}。请确认后端服务已启动。</span>
        </div>
      )}

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {stats.map((s, i) => (
          <div key={i} className="glass-card p-5">
            <div className={`w-10 h-10 rounded-xl ${s.color} flex items-center justify-center mb-3`}>
              <s.icon className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{s.value}</div>
            <div className="text-sm text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* 学习路径列表 */}
        <div className="md:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-brand-600" /> 学习路径
            </h2>
            <Link href="/learning" className="text-sm text-brand-600 font-medium hover:underline flex items-center gap-1">
              全部 <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {fetching ? (
            <SkeletonList />
          ) : paths.length === 0 ? (
            <div className="glass-card p-10 empty-state">
              <Target className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-gray-500 mb-4">还没有学习路径</p>
              <Link href="/learning" className="btn-primary">
                创建第一个学习路径 <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            paths.slice(0, 4).map(p => {
              const prog = Math.round(p.progress || 0)
              return (
                <Link
                  key={p.id}
                  href="/learning"
                  className="glass-card p-5 hover:-translate-y-0.5 transition-all duration-300 group block"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors truncate">
                        {p.title}
                      </h3>
                      <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">
                        {p.description || p.goal || '暂无描述'}
                      </p>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ml-3 ${getDifficultyColor(p.difficulty)}`}
                    >
                      {getDifficultyLabel(p.difficulty)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 progress-track">
                      <div
                        className="h-full bg-gradient-to-r from-brand-600 to-purple-500 rounded-full transition-all duration-500"
                        style={{ width: `${prog}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-600 w-10 text-right">{prog}%</span>
                  </div>
                </Link>
              )
            })
          )}
        </div>

        {/* 右侧：复习 + 建议 + 快捷入口 */}
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-3">
              <RefreshCcw className="w-5 h-5 text-brand-600" /> 待复习
            </h2>
            <Link href="/review" className="glass-card p-5 flex items-center justify-between hover:-translate-y-0.5 transition-all duration-300 group block">
              <div>
                <div className="text-3xl font-bold text-gray-900">
                  {review ? review.due_count : 0}
                </div>
                <div className="text-sm text-gray-500 mt-1">个知识点今日待复习</div>
              </div>
              <div className="flex items-center gap-1 text-sm text-brand-600 font-medium">
                {review && review.due_count > 0 ? '去复习' : '查看'}
                <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
            {review && review.due_count > 0 && (
              <p className="text-xs text-amber-600 mt-2 px-1">
                根据记忆曲线，建议尽快完成今天的复习任务，巩固薄弱点。
              </p>
            )}
          </div>

          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-teal-500" /> 学习建议
            </h2>
            <div className="glass-card p-5 space-y-4">
              {suggestions.length === 0 ? (
                <p className="text-sm text-gray-400">暂无建议，开始学习后将为你生成个性化建议</p>
              ) : (
                suggestions.map((s, i) => (
                  <div key={i} className="flex gap-3">
                    <s.icon className={`w-5 h-5 ${s.color} flex-shrink-0 mt-0.5`} />
                    <p className="text-sm text-gray-600 leading-relaxed">{s.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-brand-600" /> 快捷入口
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {quickEntries.map((q, i) => (
                <Link
                  key={i}
                  href={q.href}
                  className="glass-card p-4 hover:-translate-y-0.5 transition-all duration-300 group"
                >
                  <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${q.color} flex items-center justify-center mb-2 group-hover:scale-110 transition-transform`}>
                    <q.icon className="w-5 h-5 text-white" />
                  </div>
                  <div className="text-sm font-semibold text-gray-900">{q.label}</div>
                  <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{q.desc}</div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

function buildSuggestions(paths: LearningPath[], progress: ProgressOverview | null) {
  const out: Array<{ icon: typeof Brain; text: string; color: string }> = []
  if (paths.length === 0) {
    out.push({ icon: Target, text: '还没有学习路径，去创建一个并让 AI 帮你规划模块吧！', color: 'text-brand-600' })
  } else {
    const active = paths.find(p => (p.status || 'active') === 'active')
    if (active) {
      out.push({ icon: Brain, text: `继续推进「${active.title}」，保持每日学习节奏`, color: 'text-teal-500' })
    }
    const nearDone = paths.find(p => (p.progress || 0) >= 80 && p.status !== 'completed')
    if (nearDone) {
      out.push({ icon: Award, text: `「${nearDone.title}」即将完成，加油冲刺！`, color: 'text-amber-500' })
    }
  }
  if (progress && progress.weak_points && progress.weak_points.length > 0) {
    out.push({
      icon: AlertCircle,
      text: `检测到薄弱点：${progress.weak_points.slice(0, 3).join('、')}，建议针对性复习`,
      color: 'text-red-500',
    })
  }
  if (out.length < 2) {
    out.push({ icon: TrendingUp, text: '坚持每日学习，AI 会持续为你优化学习路径', color: 'text-blue-500' })
  }
  return out.slice(0, 3)
}

function FullScreenLoader() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="w-8 h-8 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
        <span className="text-sm">加载中...</span>
      </div>
    </div>
  )
}

function SkeletonList() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map(i => (
        <div key={i} className="glass-card p-5 animate-pulse">
          <div className="h-4 bg-gray-100 rounded w-1/3 mb-3" />
          <div className="h-3 bg-gray-100 rounded w-2/3 mb-4" />
          <div className="h-2 bg-gray-100 rounded-full" />
        </div>
      ))}
    </div>
  )
}
