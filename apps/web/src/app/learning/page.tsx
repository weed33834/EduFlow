'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  BookOpen, Plus, ChevronDown, ChevronRight, Trash2, Sparkles, Clock,
  CheckCircle, FileText, Loader2, AlertCircle, Target, RefreshCw, X, Wand2,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  learningAPI, aiAPI,
  type LearningPath, type Module,
} from '@/lib/api'
import { DIFFICULTY_OPTIONS } from '@/lib/constants'
import {
  formatDuration, getDifficultyColor, getDifficultyLabel, getStatusColor, getStatusLabel, cn,
} from '@/lib/utils'

export default function LearningPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  const [paths, setPaths] = useState<LearningPath[]>([])
  const [modulesByPath, setModulesByPath] = useState<Record<number, Module[]>>({})
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState('')

  // 创建路径表单
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [pathForm, setPathForm] = useState({ title: '', description: '', goal: '', difficulty: 'beginner' })

  // 添加模块
  const [addingToPath, setAddingToPath] = useState<number | null>(null)
  const [moduleForm, setModuleForm] = useState({ title: '', description: '' })
  const [moduleBusy, setModuleBusy] = useState(false)

  // AI 规划
  const [planningPathId, setPlanningPathId] = useState<number | null>(null)

  // 提示消息
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 3200)
  }

  const loadPaths = useCallback(async () => {
    setFetching(true)
    setError('')
    try {
      const data = await learningAPI.getPaths()
      setPaths(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载学习路径失败')
      setPaths([])
    } finally {
      setFetching(false)
    }
  }, [])

  useEffect(() => {
    if (user) loadPaths()
  }, [user, loadPaths])

  const loadModules = useCallback(async (pathId: number) => {
    if (modulesByPath[pathId]) return
    try {
      const data = await learningAPI.getPath(pathId)
      setModulesByPath(prev => ({ ...prev, [pathId]: data.modules || [] }))
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '加载模块失败')
      setModulesByPath(prev => ({ ...prev, [pathId]: [] }))
    }
  }, [modulesByPath])

  const toggleExpand = (pathId: number) => {
    setExpandedId(prev => (prev === pathId ? null : pathId))
    loadModules(pathId)
  }

  const computeProgress = (pathId: number) => {
    const modules = modulesByPath[pathId]
    if (!modules || modules.length === 0) {
      const p = paths.find(x => x.id === pathId)
      return Math.round(p?.progress || 0)
    }
    const total = modules.length
    const sum = modules.reduce((acc, m) => acc + (m.progress || (m.status === 'completed' ? 100 : 0)), 0)
    return Math.round(sum / total)
  }

  /* ---------------- 创建路径 ---------------- */
  const handleCreatePath = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pathForm.title.trim()) {
      showToast('error', '请输入路径标题')
      return
    }
    setCreating(true)
    try {
      const created = await learningAPI.createPath({
        title: pathForm.title.trim(),
        description: pathForm.description.trim(),
        goal: pathForm.goal.trim(),
        difficulty: pathForm.difficulty,
      })
      setPaths(prev => [created, ...prev])
      setPathForm({ title: '', description: '', goal: '', difficulty: 'beginner' })
      setShowCreate(false)
      showToast('success', '学习路径已创建')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '创建失败')
    } finally {
      setCreating(false)
    }
  }

  /* ---------------- 删除路径 ---------------- */
  const handleDeletePath = async (pathId: number) => {
    if (!confirm('确定删除该学习路径及其所有模块？')) return
    try {
      await learningAPI.deletePath(pathId)
      setPaths(prev => prev.filter(p => p.id !== pathId))
      setModulesByPath(prev => {
        const next = { ...prev }
        delete next[pathId]
        return next
      })
      if (expandedId === pathId) setExpandedId(null)
      showToast('success', '已删除')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '删除失败')
    }
  }

  /* ---------------- 添加模块 ---------------- */
  const handleAddModule = async (pathId: number) => {
    if (!moduleForm.title.trim()) {
      showToast('error', '请输入模块标题')
      return
    }
    setModuleBusy(true)
    try {
      const existing = modulesByPath[pathId] || []
      const created = await learningAPI.createModule({
        path_id: pathId,
        title: moduleForm.title.trim(),
        description: moduleForm.description.trim(),
        order: existing.length,
      })
      setModulesByPath(prev => ({ ...prev, [pathId]: [...(prev[pathId] || []), created] }))
      setModuleForm({ title: '', description: '' })
      setAddingToPath(null)
      showToast('success', '模块已添加')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '添加失败')
    } finally {
      setModuleBusy(false)
    }
  }

  /* ---------------- 标记模块完成 ---------------- */
  const handleToggleComplete = async (pathId: number, mod: Module) => {
    const nextStatus = mod.status === 'completed' ? 'in_progress' : 'completed'
    const nextProgress = nextStatus === 'completed' ? 100 : mod.status === 'completed' ? 50 : mod.progress
    // 乐观更新
    setModulesByPath(prev => ({
      ...prev,
      [pathId]: (prev[pathId] || []).map(m =>
        m.id === mod.id ? { ...m, status: nextStatus, progress: nextProgress } : m
      ),
    }))
    try {
      await learningAPI.updateModule(mod.id, { status: nextStatus, progress: nextProgress })
      showToast('success', nextStatus === 'completed' ? '已标记完成' : '已恢复进行中')
    } catch (err) {
      // 回滚
      setModulesByPath(prev => ({
        ...prev,
        [pathId]: (prev[pathId] || []).map(m => (m.id === mod.id ? mod : m)),
      }))
      showToast('error', err instanceof Error ? err.message : '更新失败')
    }
  }

  /* ---------------- 删除模块 ---------------- */
  const handleDeleteModule = async (pathId: number, mod: Module) => {
    if (!confirm(`确定删除模块「${mod.title}」？`)) return
    // 乐观删除
    setModulesByPath(prev => ({
      ...prev,
      [pathId]: (prev[pathId] || []).filter(m => m.id !== mod.id),
    }))
    try {
      await learningAPI.deleteModule(mod.id)
      showToast('success', '模块已删除')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '删除失败')
      loadModules(pathId) // 重新加载
    }
  }

  /* ---------------- AI 规划模块 ---------------- */
  const handleAIPlan = async (path: LearningPath) => {
    setPlanningPathId(path.id)
    try {
      let planned: Array<{ title: string; description?: string; estimated_minutes?: number }> = []
      try {
        const res = await aiAPI.plan(path.goal || path.title, path.difficulty || 'beginner', 5)
        if (Array.isArray(res.modules) && res.modules.length > 0) {
          planned = res.modules
        }
      } catch {
        // 后端未提供规划接口时，使用本地兜底规划
        planned = localPlan(path.goal || path.title)
      }

      const created: Module[] = []
      const base = modulesByPath[path.id] || []
      for (let i = 0; i < planned.length; i++) {
        const m = planned[i]
        try {
          const c = await learningAPI.createModule({
            path_id: path.id,
            title: m.title,
            description: m.description,
            order: base.length + i,
          })
          created.push(c)
        } catch {
          /* 跳过失败项 */
        }
      }
      if (created.length > 0) {
        setModulesByPath(prev => ({ ...prev, [path.id]: [...(prev[path.id] || []), ...created] }))
        showToast('success', `AI 已规划并添加 ${created.length} 个模块`)
      } else {
        showToast('error', 'AI 规划失败，请手动添加模块')
      }
    } finally {
      setPlanningPathId(null)
    }
  }

  if (loading) return <FullScreenLoader />
  if (!user) return null

  return (
    <main className="max-w-5xl mx-auto px-4 py-8 pb-24">
      {/* 头部 */}
      <div className="mb-8 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-brand-600" /> 学习空间
          </h1>
          <p className="text-gray-500 mt-1 text-sm">创建学习路径，管理模块，让 AI 帮你规划</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadPaths} className="btn-secondary !py-2 !px-4 text-sm">
            <RefreshCw className={`w-4 h-4 ${fetching ? 'animate-spin' : ''}`} /> 刷新
          </button>
          <button onClick={() => setShowCreate(v => !v)} className="btn-primary !py-2 !px-4 text-sm">
            <Plus className="w-4 h-4" /> 创建学习路径
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={cn(
            'fixed top-20 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-full shadow-lg text-sm font-medium flex items-center gap-2',
            toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          )}
        >
          {toast.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* 创建路径表单 */}
      {showCreate && (
        <div className="glass-card p-6 mb-6 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-brand-600" /> 新建学习路径
            </h2>
            <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleCreatePath} className="grid md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="label">路径标题 *</label>
              <input
                className="input-field"
                placeholder="例如：Python 数据分析入门"
                value={pathForm.title}
                onChange={e => setPathForm(s => ({ ...s, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">学习目标</label>
              <input
                className="input-field"
                placeholder="例如：掌握 Pandas 与数据可视化"
                value={pathForm.goal}
                onChange={e => setPathForm(s => ({ ...s, goal: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">难度</label>
              <select
                className="input-field"
                value={pathForm.difficulty}
                onChange={e => setPathForm(s => ({ ...s, difficulty: e.target.value }))}
              >
                {DIFFICULTY_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="label">描述</label>
              <textarea
                className="input-field min-h-[80px] resize-y"
                placeholder="简要描述这条学习路径..."
                value={pathForm.description}
                onChange={e => setPathForm(s => ({ ...s, description: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2 flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary !py-2">
                取消
              </button>
              <button type="submit" disabled={creating} className="btn-primary !py-2">
                {creating ? <><Loader2 className="w-4 h-4 animate-spin" /> 创建中</> : '创建路径'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 路径列表 */}
      {fetching ? (
        <SkeletonList />
      ) : error ? (
        <div className="glass-card p-8 empty-state">
          <AlertCircle className="w-10 h-10 text-amber-400 mb-3" />
          <p className="text-gray-600 mb-2">加载失败：{error}</p>
          <p className="text-sm text-gray-400 mb-4">请确认后端服务已启动，然后刷新重试</p>
          <button onClick={loadPaths} className="btn-primary">重新加载</button>
        </div>
      ) : paths.length === 0 ? (
        <div className="glass-card p-12 empty-state">
          <Target className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-1">还没有学习路径</h3>
          <p className="text-sm text-gray-400 mb-5">创建你的第一条学习路径，开启自学之旅</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> 创建学习路径
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {paths.map(path => {
            const expanded = expandedId === path.id
            const progress = computeProgress(path.id)
            const modules = modulesByPath[path.id]
            return (
              <div key={path.id} className="glass-card overflow-hidden">
                {/* 路径卡片头部 */}
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <button onClick={() => toggleExpand(path.id)} className="flex items-start gap-3 min-w-0 text-left flex-1">
                      <div className="mt-0.5 text-gray-400">
                        {expanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-semibold text-gray-900 hover:text-brand-600 transition-colors">
                          {path.title}
                        </h3>
                        <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                          {path.description || path.goal || '暂无描述'}
                        </p>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <span className={cn('text-xs px-2 py-0.5 rounded-full', getDifficultyColor(path.difficulty))}>
                            {getDifficultyLabel(path.difficulty)}
                          </span>
                          <span className={cn('text-xs px-2 py-0.5 rounded-full', getStatusColor(path.status || 'active'))}>
                            {getStatusLabel(path.status || 'active')}
                          </span>
                          {modules && (
                            <span className="text-xs text-gray-400 flex items-center gap-1">
                              <FileText className="w-3 h-3" /> {modules.length} 个模块
                            </span>
                          )}
                          {path.estimated_duration ? (
                            <span className="text-xs text-gray-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" /> {formatDuration(path.estimated_duration)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </button>
                    <button
                      onClick={() => handleDeletePath(path.id)}
                      className="text-gray-300 hover:text-red-500 transition-colors p-1.5 rounded-lg hover:bg-red-50 flex-shrink-0"
                      title="删除路径"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 progress-track">
                      <div
                        className="h-full bg-brand-500 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-600 w-10 text-right">{progress}%</span>
                  </div>
                </div>

                {/* 展开模块列表 */}
                {expanded && (
                  <div className="border-t border-gray-100 bg-gray-50/50 p-5 animate-fade-in">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-sm font-bold text-gray-700 flex items-center gap-1.5">
                        <FileText className="w-4 h-4" /> 模块列表
                      </h4>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAIPlan(path)}
                          disabled={planningPathId === path.id}
                          className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-brand-50 text-brand-600 hover:bg-brand-100 transition-colors disabled:opacity-60"
                        >
                          {planningPathId === path.id ? (
                            <><Loader2 className="w-3.5 h-3.5 animate-spin" /> AI 规划中</>
                          ) : (
                            <><Wand2 className="w-3.5 h-3.5" /> AI 规划模块</>
                          )}
                        </button>
                        <button
                          onClick={() => setAddingToPath(addingToPath === path.id ? null : path.id)}
                          className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors"
                        >
                          <Plus className="w-3.5 h-3.5" /> 添加模块
                        </button>
                      </div>
                    </div>

                    {/* 添加模块表单 */}
                    {addingToPath === path.id && (
                      <form
                        onSubmit={e => { e.preventDefault(); handleAddModule(path.id) }}
                        className="glass-card p-4 mb-4 space-y-3 animate-fade-in"
                      >
                        <div>
                          <label className="label">模块标题 *</label>
                          <input
                            className="input-field"
                            placeholder="例如：变量与数据类型"
                            value={moduleForm.title}
                            onChange={e => setModuleForm(s => ({ ...s, title: e.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="label">描述</label>
                          <input
                            className="input-field"
                            placeholder="简要描述该模块内容"
                            value={moduleForm.description}
                            onChange={e => setModuleForm(s => ({ ...s, description: e.target.value }))}
                          />
                        </div>
                        <div className="flex justify-end gap-2">
                          <button type="button" onClick={() => setAddingToPath(null)} className="btn-secondary !py-1.5 text-sm">
                            取消
                          </button>
                          <button type="submit" disabled={moduleBusy} className="btn-primary !py-1.5 text-sm">
                            {moduleBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : '添加'}
                          </button>
                        </div>
                      </form>
                    )}

                    {/* 模块项 */}
                    {!modules ? (
                      <div className="flex items-center justify-center py-6 text-gray-400 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin mr-2" /> 加载模块...
                      </div>
                    ) : modules.length === 0 ? (
                      <div className="empty-state py-8">
                        <FileText className="w-8 h-8 text-gray-300 mb-2" />
                        <p className="text-sm text-gray-400 mb-3">还没有模块，手动添加或让 AI 规划</p>
                        <button onClick={() => handleAIPlan(path)} className="btn-secondary !py-1.5 text-sm">
                          <Sparkles className="w-3.5 h-3.5" /> 让 AI 规划
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {modules.map((mod, idx) => {
                          const done = mod.status === 'completed'
                          return (
                            <div
                              key={mod.id}
                              className={cn(
                                'flex items-center justify-between p-3 rounded-xl border transition-colors',
                                done ? 'bg-green-50/60 border-green-100' : 'bg-white border-gray-100 hover:border-brand-200'
                              )}
                            >
                              <div className="flex items-center gap-3 min-w-0 flex-1">
                                <button
                                  onClick={() => handleToggleComplete(path.id, mod)}
                                  className={cn(
                                    'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                                    done
                                      ? 'border-green-500 bg-green-500 text-white'
                                      : 'border-gray-300 hover:border-brand-500'
                                  )}
                                  title={done ? '标记为未完成' : '标记完成'}
                                >
                                  {done && <CheckCircle className="w-3.5 h-3.5" />}
                                </button>
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-gray-400">#{idx + 1}</span>
                                    <span className={cn('text-sm font-medium truncate', done ? 'text-gray-400 line-through' : 'text-gray-900')}>
                                      {mod.title}
                                    </span>
                                  </div>
                                  {mod.description && (
                                    <p className="text-xs text-gray-400 truncate mt-0.5">{mod.description}</p>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className={cn('text-xs px-2 py-0.5 rounded-full', getStatusColor(mod.status))}>
                                  {getStatusLabel(mod.status)}
                                </span>
                                {mod.estimated_minutes ? (
                                  <span className="text-xs text-gray-400 hidden sm:flex items-center gap-1">
                                    <Clock className="w-3 h-3" /> {formatDuration(mod.estimated_minutes)}
                                  </span>
                                ) : null}
                                <button
                                  onClick={() => handleDeleteModule(path.id, mod)}
                                  className="text-gray-300 hover:text-red-500 transition-colors p-1"
                                  title="删除模块"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {/* 去练习入口 */}
                    {modules && modules.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <Link
                          href="/practice"
                          className="inline-flex items-center gap-1.5 text-sm text-brand-600 font-medium hover:underline"
                        >
                          <Sparkles className="w-4 h-4" /> 去练习这些模块
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </main>
  )
}

/** 本地兜底规划（后端 AI 规划接口不可用时使用） */
function localPlan(goal: string): Array<{ title: string; description?: string; estimated_minutes?: number }> {
  const g = goal || '学习主题'
  return [
    { title: `入门：${g}基础概念`, description: `了解 ${g} 的核心概念与背景知识`, estimated_minutes: 60 },
    { title: `核心：${g}原理与机制`, description: `深入 ${g} 的核心原理与工作机制`, estimated_minutes: 90 },
    { title: `实践：${g}动手练习`, description: `通过动手实践巩固 ${g} 知识`, estimated_minutes: 120 },
    { title: `进阶：${g}高级应用`, description: `探索 ${g} 的进阶用法与最佳实践`, estimated_minutes: 90 },
    { title: `复习：${g}总结与测验`, description: `回顾要点并通过测验检验掌握程度`, estimated_minutes: 45 },
  ]
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
          <div className="h-5 bg-gray-100 rounded w-2/5 mb-3" />
          <div className="h-3 bg-gray-100 rounded w-3/4 mb-4" />
          <div className="h-2 bg-gray-100 rounded-full" />
        </div>
      ))}
    </div>
  )
}
