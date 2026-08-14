'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  BarChart3, Clock, Target, Brain, TrendingUp, AlertCircle, Award,
  CheckCircle, RefreshCw, Flame, Zap,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  progressAPI,
  type Module, type ProgressOverview,
} from '@/lib/api'
import { formatDuration, getStatusColor, getStatusLabel, cn } from '@/lib/utils'

interface ModuleRow {
  module: Module
  pathTitle: string
  completion: number
  learningTime: number
}

export default function ProgressPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  const [rows, setRows] = useState<ModuleRow[]>([])
  const [overview, setOverview] = useState<ProgressOverview | null>(null)
  const [avgQuiz, setAvgQuiz] = useState<number | null>(null)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  const loadData = useCallback(async () => {
    if (!user) return
    setFetching(true)
    setError('')
    try {
      // 服务端聚合：进度总览(含模块明细/总时长/薄弱点/测验分)
      const ov = await progressAPI.getOverview()
      setOverview(ov)

      const moduleDetails = ov?.module_details || []
      // 平均测验分：取各模块最近一次测验得分
      const scores: number[] = []
      moduleDetails.forEach(md => {
        const last = (md.quiz_scores || []).slice(-1)[0]
        if (last && typeof last.score === 'number') scores.push(last.score)
      })
      setAvgQuiz(scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null)

      const moduleRows: ModuleRow[] = moduleDetails.map(md => ({
        module: {
          id: md.module_id,
          path_id: 0,
          title: md.module_title || `模块 ${md.module_id}`,
          order: 0,
          status: md.module_status || 'not_started',
          progress: md.module_progress ?? md.completion_percentage ?? 0,
        },
        pathTitle: md.path_title || '',
        completion: md.completion_percentage ?? md.module_progress ?? 0,
        learningTime: md.learning_time_minutes ?? 0,
      }))
      moduleRows.sort((a, b) => a.completion - b.completion)
      setRows(moduleRows)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载进度数据失败')
    } finally {
      setFetching(false)
    }
  }, [user])

  useEffect(() => {
    if (user) loadData()
  }, [user, loadData])

  if (loading) return <FullScreenLoader />
  if (!user) return null

  const totalLearning = rows.reduce((sum, r) => sum + r.learningTime, 0)
  const avgCompletion = overview?.overall_completion ?? (rows.length > 0 ? Math.round(rows.reduce((s, r) => s + r.completion, 0) / rows.length) : 0)
  const completedCount = rows.filter(r => r.completion >= 100 || r.module.status === 'completed').length

  const stats = [
    { icon: Clock, label: '总学习时长', value: formatDuration(totalLearning), color: 'bg-blue-500' },
    { icon: TrendingUp, label: '平均完成度', value: `${avgCompletion}%`, color: 'bg-brand-600' },
    { icon: CheckCircle, label: '已完成模块', value: String(completedCount), color: 'bg-teal-500' },
    { icon: Brain, label: '平均测验分', value: avgQuiz !== null ? `${avgQuiz}` : '-', color: 'bg-amber-500' },
  ]

  const weakPoints = overview?.weak_points && overview.weak_points.length > 0
    ? overview.weak_points
    : rows.filter(r => r.completion < 60).slice(0, 5).map(r => r.module.title)

  const strongPoints = overview?.strong_points && overview.strong_points.length > 0
    ? overview.strong_points
    : rows.filter(r => r.completion >= 80).slice(-5).reverse().map(r => r.module.title)

  return (
    <main className="max-w-5xl mx-auto px-4 py-8 pb-24">
      {/* 头部 */}
      <div className="mb-8 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-brand-600" /> 学习进度
          </h1>
          <p className="text-gray-500 mt-1 text-sm">追踪学习时长、完成度与薄弱点</p>
        </div>
        <button onClick={loadData} className="btn-secondary !py-2 !px-4 text-sm">
          <RefreshCw className={cn('w-4 h-4', fetching && 'animate-spin')} /> 刷新
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
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-3', s.color)}>
              <s.icon className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{s.value}</div>
            <div className="text-sm text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* 课程进度列表 */}
        <div className="md:col-span-2">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-brand-600" /> 课程进度
          </h2>

          {fetching ? (
            <SkeletonList />
          ) : rows.length === 0 ? (
            <div className="glass-card p-10 empty-state">
              <Target className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-gray-500 mb-2">还没有学习模块</p>
              <Link href="/learning" className="btn-primary !py-2 text-sm">去学习</Link>
            </div>
          ) : (
            <div className="glass-card divide-y divide-gray-50">
              {rows.map((r, i) => (
                <div key={r.module.id ?? i} className="p-4 flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">{r.module.title}</span>
                      <span className={cn('text-xs px-2 py-0.5 rounded-full flex-shrink-0', getStatusColor(r.module.status || (r.completion >= 100 ? 'completed' : 'in_progress')))}>
                        {getStatusLabel(r.module.status || (r.completion >= 100 ? 'completed' : 'in_progress'))}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 truncate mb-2">{r.pathTitle}</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 progress-track">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all',
                            r.completion >= 80 ? 'bg-teal-500'
                              : r.completion >= 40 ? 'bg-brand-500'
                              : 'bg-amber-500'
                          )}
                          style={{ width: `${Math.max(2, r.completion)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-9 text-right">{Math.round(r.completion)}%</span>
                    </div>
                  </div>
                  {r.learningTime > 0 && (
                    <span className="text-xs text-gray-400 flex items-center gap-1 flex-shrink-0 hidden sm:flex">
                      <Clock className="w-3 h-3" /> {formatDuration(r.learningTime)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 右侧：薄弱点 + 强项 */}
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-amber-500" /> 薄弱点分析
            </h2>
            <div className="glass-card p-5">
              {weakPoints.length === 0 ? (
                <p className="text-sm text-gray-400">暂未发现薄弱点，继续保持！</p>
              ) : (
                <div className="space-y-3">
                  {weakPoints.map((w, i) => {
                    const row = rows.find(r => r.module.title === w)
                    const mastery = row ? row.completion : Math.max(10, 50 - i * 10)
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-700 truncate">{w}</span>
                            <span className="text-gray-400">{Math.round(mastery)}%</span>
                          </div>
                          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                'h-full rounded-full',
                                mastery < 40 ? 'bg-red-400' : mastery < 60 ? 'bg-amber-400' : 'bg-green-400'
                              )}
                              style={{ width: `${mastery}%` }}
                            />
                          </div>
                        </div>
                        <span className={cn(
                          'text-xs px-2 py-0.5 rounded-full flex-shrink-0',
                          mastery < 40 ? 'bg-red-100 text-red-600' : mastery < 60 ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'
                        )}>
                          {mastery < 40 ? '需加强' : mastery < 60 ? '需练习' : '继续努力'}
                        </span>
                      </div>
                    )
                  })}
                  <Link href="/practice" className="flex items-center justify-center gap-1.5 mt-2 text-xs text-brand-600 font-medium hover:underline">
                    <Zap className="w-3.5 h-3.5" /> 针对薄弱点练习
                  </Link>
                </div>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
              <Award className="w-5 h-5 text-teal-500" /> 我的强项
            </h2>
            <div className="glass-card p-5">
              {strongPoints.length === 0 ? (
                <p className="text-sm text-gray-400">完成更多模块后，你的强项会展示在这里</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {strongPoints.map((s, i) => (
                    <span key={i} className="inline-flex items-center gap-1 text-sm bg-teal-50 text-teal-700 px-3 py-1 rounded-full">
                      <Flame className="w-3.5 h-3.5" /> {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
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
    <div className="glass-card divide-y divide-gray-50">
      {[0, 1, 2, 3].map(i => (
        <div key={i} className="p-4 animate-pulse">
          <div className="h-4 bg-gray-100 rounded w-1/3 mb-2" />
          <div className="h-3 bg-gray-100 rounded w-1/4 mb-3" />
          <div className="h-2 bg-gray-100 rounded-full" />
        </div>
      ))}
    </div>
  )
}
