'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Brain, CheckCircle, XCircle, ArrowRight, Loader2,
  AlertCircle, Trash2, History, Play, Sparkles, FileText, Award, RotateCcw, X,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  aiAPI, practiceAPI, learningAPI,
  type Question, type Module as LearningModule,
} from '@/lib/api'
import { DIFFICULTY_OPTIONS } from '@/lib/constants'
import { normalizeQuestionId, cn, formatDateTime } from '@/lib/utils'

/* ---------------- 本地历史记录（保证回顾可用） ---------------- */
interface NormalizedQuestion {
  id: number
  question: string
  options: string[]
  answerIndex: number
  explanation: string
  difficulty?: string
}

interface LocalSession {
  id: number
  topic: string
  moduleId?: number
  moduleTitle?: string
  difficulty: string
  questions: NormalizedQuestion[]
  answers: Array<{ questionId: number; selected: number; correct: boolean }>
  score: number
  total: number
  correct: number
  completedAt: string
}

const HISTORY_KEY = 'eduflow_practice_history'

function loadHistory(): LocalSession[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? (JSON.parse(raw) as LocalSession[]) : []
  } catch {
    return []
  }
}

function saveHistory(list: LocalSession[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 50)))
}

/** 本地兜底题库：AI 出题超时/失败时立即返回，保证练习永不卡死 */
const FALLBACK_BANK: Array<{ q: string; o: string[]; a: number; e: string; d: string }> = [
  { q: '下列哪个不是 Python 的数据类型？', o: ['整数 int', '浮点 float', '字符 char', '字符串 str'], a: 2, e: 'Python 没有独立的 char 类型，字符用长度为 1 的字符串表示。', d: 'easy' },
  { q: '执行 `print(2 ** 3)` 的输出是？', o: ['6', '8', '9', '23'], a: 1, e: '** 是幂运算符，2 的 3 次方等于 8。', d: 'easy' },
  { q: '下列哪种数据结构是无序且不重复的？', o: ['列表', '元组', '字典', '集合'], a: 3, e: '集合 set 存储唯一元素且无序，常用于去重。', d: 'medium' },
  { q: '关于函数参数，下列哪项正确？', o: ['默认参数必须放在非默认参数之后', '函数必须有 return', '参数只能是位置参数', '不能有多个参数'], a: 0, e: '默认参数必须位于所有非默认参数之后，否则语法错误。', d: 'medium' },
  { q: '`s = "hello"`，`s[1]` 的值是？', o: ['h', 'e', 'l', 'o'], a: 1, e: '字符串索引从 0 开始，s[1] 是第 2 个字符 e。', d: 'easy' },
]

function localQuestions(topic: string, count: number): NormalizedQuestion[] {
  const picked = FALLBACK_BANK.slice(0, Math.max(count, 1))
  return picked.map((it, idx) => ({
    id: idx + 1,
    question: `【${topic || '练习'}】${it.q}`,
    options: it.o,
    answerIndex: it.a,
    explanation: it.e,
    difficulty: it.d,
  }))
}

/** 带超时的 AI 出题：超时抛错，交由调用方用本地题库兜底 */
async function generateQuestionsWithTimeout(topic: string, difficulty: string, count: number, timeoutMs = 15000) {
  return Promise.race([
    aiAPI.generateQuestions(topic, difficulty, count, ''),
    new Promise<never>((_, rej) => setTimeout(() => rej(new Error('AI 出题超时，已切换为本地题库')), timeoutMs)),
  ])
}

/* ---------------- 题目归一化 ---------------- */
function normalizeQuestions(raw: Question[]): NormalizedQuestion[] {
  return (raw || []).map((q, idx) => {
    const id = normalizeQuestionId(q.id, idx)
    const options = Array.isArray(q.options) ? q.options.map(String) : []
    let answerIndex = Number(q.answer)
    if (isNaN(answerIndex)) answerIndex = 0
    if (answerIndex < 0 || answerIndex >= options.length) answerIndex = Math.max(0, Math.min(answerIndex, options.length - 1))
    return {
      id,
      question: q.question || '(无题干)',
      options,
      answerIndex,
      explanation: q.explanation || '',
      difficulty: q.difficulty,
    }
  }).filter(q => q.options.length > 0)
}

export default function PracticePage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  // 视图：home | quiz | result
  const [view, setView] = useState<'home' | 'quiz' | 'result'>('home')
  const [reviewing, setReviewing] = useState<LocalSession | null>(null)

  // 模块选择
  const [modules, setModules] = useState<Array<{ module: LearningModule; pathTitle: string }>>([])
  const [loadingModules, setLoadingModules] = useState(true)

  // 设置表单
  const [selectedModuleId, setSelectedModuleId] = useState<number | ''>('')
  const [customTopic, setCustomTopic] = useState('')
  const [difficulty, setDifficulty] = useState('medium')
  const [count, setCount] = useState(5)
  const [generating, setGenerating] = useState(false)

  // 当前测验
  const [questions, setQuestions] = useState<NormalizedQuestion[]>([])
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [answers, setAnswers] = useState<Array<{ questionId: number; selected: number; correct: boolean }>>([])
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [currentTopic, setCurrentTopic] = useState('')

  // 历史
  const [history, setHistory] = useState<LocalSession[]>([])

  // 提示
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  useEffect(() => {
    setHistory(loadHistory())
  }, [])

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3200)
  }

  /* ---------------- 加载模块列表 ---------------- */
  const loadModules = useCallback(async () => {
    setLoadingModules(true)
    try {
      const paths = await learningAPI.getPaths()
      const safePaths = Array.isArray(paths) ? paths : []
      const results = await Promise.allSettled(
        safePaths.map(p => learningAPI.getPath(p.id))
      )
      const flat: Array<{ module: LearningModule; pathTitle: string }> = []
      results.forEach((r, i) => {
        if (r.status === 'fulfilled' && Array.isArray(r.value?.modules)) {
          r.value.modules.forEach(m => flat.push({ module: m, pathTitle: safePaths[i].title }))
        }
      })
      setModules(flat)
    } catch {
      setModules([])
    } finally {
      setLoadingModules(false)
    }
  }, [])

  useEffect(() => {
    if (user) loadModules()
  }, [user, loadModules])

  /* ---------------- 开始测验 ---------------- */
  const handleStart = async () => {
    let topic = customTopic.trim()
    let moduleId: number | undefined
    let moduleTitle: string | undefined

    if (selectedModuleId !== '') {
      const found = modules.find(m => m.module.id === Number(selectedModuleId))
      if (found) {
        moduleId = found.module.id
        moduleTitle = found.module.title
        topic = topic || found.module.title
      }
    }

    if (!topic) {
      showToast('error', '请选择模块或输入练习主题')
      return
    }

    setGenerating(true)
    setSessionId(null)
    let qs: NormalizedQuestion[] = []
    let usedFallback = false
    try {
      try {
        const res = await generateQuestionsWithTimeout(topic, difficulty, count)
        qs = normalizeQuestions(res.questions || [])
      } catch {
        // AI 超时或失败 -> 本地题库兜底，练习依然可用、不卡死
        usedFallback = true
        qs = localQuestions(topic, count)
      }
      if (qs.length === 0) {
        qs = localQuestions(topic, count)
        usedFallback = true
      }
      if (usedFallback) {
        showToast('success', 'AI 出题较慢，已使用本地题库')
      }
      setQuestions(qs)
      setCurrentTopic(topic)
      setCurrent(0)
      setSelected(null)
      setShowFeedback(false)
      setAnswers([])

      // 后台创建会话（best effort）
      if (moduleId) {
        practiceAPI.createSession(moduleId, 'quiz')
          .then(s => setSessionId(s?.id ?? null))
          .catch(() => {})
      }

      setView('quiz')
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : '生成题目失败')
    } finally {
      setGenerating(false)
    }
  }

  /* ---------------- 选择答案 ---------------- */
  const handleSelect = (idx: number) => {
    if (showFeedback) return
    setSelected(idx)
    setShowFeedback(true)
    const q = questions[current]
    const correct = idx === q.answerIndex
    const record = { questionId: q.id, selected: idx, correct }
    setAnswers(prev => [...prev, record])

    // 后台提交（best effort）
    if (sessionId) {
      practiceAPI.submitAnswer({
        session_id: sessionId,
        question_id: q.id,
        answer: String(idx),
        is_correct: correct,
      }).catch(() => {})
    }
  }

  const handleNext = () => {
    if (current < questions.length - 1) {
      setCurrent(prev => prev + 1)
      setSelected(null)
      setShowFeedback(false)
    } else {
      finishQuiz()
    }
  }

  /* ---------------- 完成测验 ---------------- */
  const finishQuiz = () => {
    const correct = answers.filter(a => a.correct).length
    const total = questions.length
    const score = total > 0 ? Math.round((correct / total) * 100) : 0

    const session: LocalSession = {
      id: sessionId ?? Date.now(),
      topic: currentTopic,
      moduleId: selectedModuleId !== '' ? Number(selectedModuleId) : undefined,
      moduleTitle: modules.find(m => m.module.id === Number(selectedModuleId))?.module.title,
      difficulty,
      questions,
      answers,
      score,
      total,
      correct,
      completedAt: new Date().toISOString(),
    }

    // 写入本地历史
    const next = [session, ...history.filter(h => h.id !== session.id)]
    setHistory(next)
    saveHistory(next)

    // 后台完成会话（best effort）
    if (sessionId) {
      practiceAPI.completeSession(sessionId).catch(() => {})
    }

    setView('result')
  }

  /* ---------------- 重置 ---------------- */
  const resetQuiz = () => {
    setView('home')
    setQuestions([])
    setCurrent(0)
    setSelected(null)
    setShowFeedback(false)
    setAnswers([])
    setSessionId(null)
    setCurrentTopic('')
  }

  /* ---------------- 删除历史 ---------------- */
  const handleDeleteHistory = (id: number) => {
    if (!confirm('确定删除该练习记录？')) return
    const next = history.filter(h => h.id !== id)
    setHistory(next)
    saveHistory(next)
    practiceAPI.deleteSession(id).catch(() => {})
    if (reviewing?.id === id) setReviewing(null)
    showToast('success', '已删除')
  }

  if (loading) return <FullScreenLoader />
  if (!user) return null

  /* ===================== 测验视图 ===================== */
  if (view === 'quiz' && questions.length > 0) {
    const q = questions[current]
    return (
      <main className="max-w-3xl mx-auto px-4 py-8 pb-24">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="w-5 h-5 text-brand-600" /> 自适应练习 · {currentTopic}
          </h1>
          <span className="text-sm text-gray-500">第 {current + 1}/{questions.length} 题</span>
        </div>

        <div className="glass-card p-6 md:p-8">
          <div className="progress-track mb-6">
            <div
              className="h-full bg-brand-500 rounded-full transition-all"
              style={{ width: `${((current + (showFeedback ? 1 : 0)) / questions.length) * 100}%` }}
            />
          </div>

          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-medium text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">选择题</span>
            {q.difficulty && (
              <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">{q.difficulty}</span>
            )}
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-6 whitespace-pre-wrap">{q.question}</h2>

          <div className="space-y-3">
            {q.options.map((opt, idx) => {
              let cls = 'bg-gray-50 hover:bg-gray-100 border-gray-200'
              let icon: React.ReactNode = null
              if (showFeedback && idx === q.answerIndex) {
                cls = 'bg-green-50 border-green-500'
                icon = <CheckCircle className="w-5 h-5 text-green-500" />
              } else if (showFeedback && idx === selected && idx !== q.answerIndex) {
                cls = 'bg-red-50 border-red-500'
                icon = <XCircle className="w-5 h-5 text-red-500" />
              } else if (idx === selected) {
                cls = 'bg-brand-50 border-brand-500'
              }
              return (
                <button
                  key={idx}
                  onClick={() => handleSelect(idx)}
                  disabled={showFeedback}
                  className={cn(
                    'w-full flex items-center justify-between p-4 rounded-xl border transition-all text-left disabled:cursor-default',
                    cls
                  )}
                >
                  <span className="text-sm font-medium text-gray-900">
                    <span className="text-gray-400 mr-2">{String.fromCharCode(65 + idx)}.</span>
                    {opt}
                  </span>
                  {icon}
                </button>
              )
            })}
          </div>

          {showFeedback && q.explanation && (
            <div className="mt-6 p-4 bg-brand-50 rounded-xl border border-brand-100">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">解析：</span>
                {q.explanation}
              </p>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            {showFeedback && (
              <button onClick={handleNext} className="btn-primary">
                {current < questions.length - 1 ? <>下一题 <ArrowRight className="w-4 h-4" /></> : <>查看结果 <Award className="w-4 h-4" /></>}
              </button>
            )}
          </div>
        </div>
      </main>
    )
  }

  /* ===================== 结果视图 ===================== */
  if (view === 'result') {
    const correct = answers.filter(a => a.correct).length
    const total = questions.length
    const score = total > 0 ? Math.round((correct / total) * 100) : 0
    return (
      <main className="max-w-3xl mx-auto px-4 py-8 pb-24">
        <div className="glass-card p-8 md:p-10 text-center mb-6">
          <div className={cn(
            'w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4',
            score >= 80 ? 'bg-green-100' : score >= 60 ? 'bg-amber-100' : 'bg-red-100'
          )}>
            <Brain className={cn('w-10 h-10', score >= 80 ? 'text-green-600' : score >= 60 ? 'text-amber-600' : 'text-red-600')} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">练习完成！</h2>
          <p className="text-5xl font-black text-brand-600 mb-2">{score}<span className="text-2xl">分</span></p>
          <p className="text-gray-500 mb-1">
            答对 <span className="font-semibold text-green-600">{correct}</span> / {total} 题
            {currentTopic && <> · 主题：{currentTopic}</>}
          </p>

          <div className="mt-6 flex gap-3 justify-center flex-wrap">
            <button onClick={resetQuiz} className="btn-primary">
              <RotateCcw className="w-4 h-4" /> 再练一次
            </button>
            <button
              onClick={() => {
                const session = history[0]
                if (session) setReviewing(session)
              }}
              className="btn-secondary"
            >
              <FileText className="w-4 h-4" /> 查看解析
            </button>
            <Link href="/dashboard" className="btn-secondary">返回仪表盘</Link>
          </div>
        </div>

        {/* 结果中的逐题回顾 */}
        <ResultReview questions={questions} answers={answers} />
      </main>
    )
  }

  /* ===================== 首页（设置 + 历史） ===================== */
  return (
    <main className="max-w-4xl mx-auto px-4 py-8 pb-24">
      {/* Toast */}
      {toast && (
        <div className={cn(
          'fixed top-20 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-full shadow-lg text-sm font-medium flex items-center gap-2',
          toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
        )}>
          {toast.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-6 h-6 text-brand-600" /> 练习中心
        </h1>
        <p className="text-gray-500 mt-1 text-sm">选择模块或自定义主题，让 AI 为你出题</p>
      </div>

      {/* 设置卡片 */}
      <div className="glass-card p-6 mb-8">
        <h2 className="font-bold text-gray-900 flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-brand-600" /> 新建练习
        </h2>

        <div className="space-y-4">
          <div>
            <label className="label">选择模块 {loadingModules && <span className="text-xs text-gray-400">（加载中...）</span>}</label>
            <select
              className="input-field"
              value={selectedModuleId}
              onChange={e => setSelectedModuleId(e.target.value === '' ? '' : Number(e.target.value))}
              disabled={loadingModules}
            >
              <option value="">— 不关联模块，使用自定义主题 —</option>
              {modules.map(({ module: m, pathTitle }) => (
                <option key={m.id} value={m.id}>
                  {pathTitle} / {m.title}
                </option>
              ))}
            </select>
            {modules.length === 0 && !loadingModules && (
              <p className="mt-1 text-xs text-gray-400">
                还没有模块，<Link href="/learning" className="text-brand-600 hover:underline">去创建学习路径与模块</Link>
              </p>
            )}
          </div>

          <div>
            <label className="label">练习主题（不选模块时必填）</label>
            <input
              className="input-field"
              placeholder="例如：Python 列表与字典"
              value={customTopic}
              onChange={e => setCustomTopic(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">难度</label>
              <select className="input-field" value={difficulty} onChange={e => setDifficulty(e.target.value)}>
                {DIFFICULTY_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">题目数量</label>
              <select className="input-field" value={count} onChange={e => setCount(Number(e.target.value))}>
                {[3, 5, 8, 10].map(n => (
                  <option key={n} value={n}>{n} 题</option>
                ))}
              </select>
            </div>
          </div>

          <button onClick={handleStart} disabled={generating} className="btn-primary w-full">
            {generating ? <><Loader2 className="w-4 h-4 animate-spin" /> AI 出题中...</> : <><Brain className="w-4 h-4" /> 开始练习</>}
          </button>
        </div>
      </div>

      {/* 历史记录 */}
      <div>
        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-gray-500" /> 练习历史
          {history.length > 0 && <span className="text-sm text-gray-400 font-normal">({history.length})</span>}
        </h2>

        {history.length === 0 ? (
          <div className="glass-card p-10 empty-state">
            <History className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-gray-500 mb-1">还没有练习记录</p>
            <p className="text-sm text-gray-400">完成一次练习后，记录会出现在这里</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map(s => (
              <div key={s.id} className="glass-card p-4 flex items-center justify-between gap-3">
                <button onClick={() => setReviewing(s)} className="flex items-center gap-3 min-w-0 flex-1 text-left">
                  <div className={cn(
                    'w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0',
                    s.score >= 80 ? 'bg-green-100 text-green-600' : s.score >= 60 ? 'bg-amber-100 text-amber-600' : 'bg-red-100 text-red-600'
                  )}>
                    <span className="text-sm font-bold">{s.score}</span>
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900 truncate">{s.topic}</div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {s.correct}/{s.total} 正确 · {formatDateTime(s.completedAt)}
                    </div>
                  </div>
                </button>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => setReviewing(s)}
                    className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                    title="回顾"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteHistory(s.id)}
                    className="w-9 h-9 rounded-full flex items-center justify-center text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="删除"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 回顾弹层 */}
      {reviewing && (
        <ReviewModal session={reviewing} onClose={() => setReviewing(null)} />
      )}
    </main>
  )
}

/* ---------------- 结果回顾 ---------------- */
function ResultReview({ questions, answers }: { questions: NormalizedQuestion[]; answers: Array<{ questionId: number; selected: number; correct: boolean }> }) {
  return (
    <div className="space-y-4">
      <h3 className="font-bold text-gray-900 flex items-center gap-2">
        <FileText className="w-5 h-5 text-brand-600" /> 题目解析
      </h3>
      {questions.map((q, i) => {
        const ans = answers.find(a => a.questionId === q.id)
        const selectedIdx = ans?.selected
        const correct = ans?.correct
        return (
          <div key={q.id} className="glass-card p-5">
            <div className="flex items-start gap-2 mb-3">
              {correct ? <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />}
              <h4 className="text-sm font-semibold text-gray-900">
                <span className="text-gray-400 mr-1">{i + 1}.</span>{q.question}
              </h4>
            </div>
            <div className="space-y-1.5 ml-7">
              {q.options.map((opt, idx) => {
                let cls = 'text-gray-600'
                if (idx === q.answerIndex) cls = 'text-green-600 font-medium'
                else if (idx === selectedIdx && idx !== q.answerIndex) cls = 'text-red-500 line-through'
                return (
                  <div key={idx} className={cn('text-sm flex items-center gap-2', cls)}>
                    <span className="text-xs text-gray-400">{String.fromCharCode(65 + idx)}.</span>
                    {opt}
                    {idx === q.answerIndex && <CheckCircle className="w-3.5 h-3.5" />}
                  </div>
                )
              })}
            </div>
            {q.explanation && (
              <div className="mt-3 ml-7 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                <span className="font-semibold">解析：</span>{q.explanation}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ---------------- 回顾弹层 ---------------- */
function ReviewModal({ session, onClose }: { session: LocalSession; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div className="min-w-0">
            <h3 className="font-bold text-gray-900 truncate">回顾：{session.topic}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {session.correct}/{session.total} 正确 · 得分 {session.score} · {formatDateTime(session.completedAt)}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-5 overflow-y-auto">
          <ResultReview questions={session.questions} answers={session.answers} />
        </div>
      </div>
    </div>
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
