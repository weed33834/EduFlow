'use client'

import { useState } from 'react'
import {
  Search, BookOpen, Volume2, Image as ImageIcon, Loader2, Sparkles, AlertTriangle, CheckCircle2,
} from 'lucide-react'
import { aiAPI } from '@/lib/api'

export default function AiToolsPage() {
  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-600" /> AI 工具箱
        </h1>
        <p className="text-gray-500 mt-1">概念解释 · 知识库检索 · 配音试听 · 文生图，一站式使用全部 AI 能力。</p>
      </div>
      <div className="grid md:grid-cols-2 gap-6">
        <ExplainTool />
        <KnowledgeTool />
        <TtsTool />
        <ImageTool />
      </div>
    </main>
  )
}

/* ---------------- 概念解释 ---------------- */
function ExplainTool() {
  const [concept, setConcept] = useState('')
  const [level, setLevel] = useState('beginner')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const run = async () => {
    if (!concept.trim()) return
    setLoading(true); setErr(''); setResult('')
    try {
      const r = await aiAPI.explain(concept, level)
      setResult(r.response || '（无回复）')
    } catch (e) { setErr(e instanceof Error ? e.message : '失败') }
    finally { setLoading(false) }
  }

  return (
    <Card icon={<BookOpen className="w-5 h-5" />} title="概念解释" desc="输入概念，AI 按你的水平通俗讲解">
      <input className="input-field mb-2" placeholder="例如：递归、哈希表、闭包" value={concept} onChange={e => setConcept(e.target.value)} disabled={loading} />
      <div className="flex gap-2 mb-3">
        <select className="input-field flex-1" value={level} onChange={e => setLevel(e.target.value)}>
          <option value="beginner">入门</option><option value="intermediate">进阶</option><option value="advanced">高级</option>
        </select>
        <button className="btn-primary flex-shrink-0" onClick={run} disabled={loading || !concept.trim()}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '解释'}
        </button>
      </div>
      {err && <p className="text-xs text-red-600 mb-1">{err}</p>}
      {result && <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg p-3 max-h-56 overflow-y-auto">{result}</div>}
    </Card>
  )
}

/* ---------------- 知识库检索 ---------------- */
function KnowledgeTool() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const run = async () => {
    if (!query.trim()) return
    setLoading(true); setErr(''); setResult('')
    try {
      const r = await aiAPI.knowledge(query, '', true)
      setResult((r.knowledge || '无匹配结果') + (r.prerequisites ? '\n\n' + r.prerequisites : ''))
    } catch (e) { setErr(e instanceof Error ? e.message : '失败') }
    finally { setLoading(false) }
  }

  return (
    <Card icon={<Search className="w-5 h-5" />} title="知识库检索" desc="搜索内置知识点与前置知识">
      <div className="flex gap-2 mb-3">
        <input className="input-field flex-1" placeholder="例如：动态规划、HTTP、装饰器" value={query} onChange={e => setQuery(e.target.value)} disabled={loading} onKeyDown={e => e.key === 'Enter' && run()} />
        <button className="btn-primary flex-shrink-0" onClick={run} disabled={loading || !query.trim()}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '搜索'}
        </button>
      </div>
      {err && <p className="text-xs text-red-600 mb-1">{err}</p>}
      {result && <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg p-3 max-h-56 overflow-y-auto">{result}</div>}
    </Card>
  )
}

/* ---------------- TTS 配音试听 ---------------- */
function TtsTool() {
  const [text, setText] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const run = async () => {
    if (!text.trim()) return
    setLoading(true); setErr(''); setAudioUrl('')
    try {
      const r = await aiAPI.tts(text)
      if (r.ok && r.audio) setAudioUrl(`data:audio/mp3;base64,${r.audio}`)
      else setErr(r.error || '配音失败')
    } catch (e) { setErr(e instanceof Error ? e.message : '失败') }
    finally { setLoading(false) }
  }

  return (
    <Card icon={<Volume2 className="w-5 h-5" />} title="配音试听 (TTS)" desc="文本转语音，生成讲解配音">
      <textarea className="input-field mb-2 resize-none" rows={2} placeholder="输入要朗读的文本..." value={text} onChange={e => setText(e.target.value)} disabled={loading} />
      <div className="flex items-center gap-3">
        <button className="btn-primary" onClick={run} disabled={loading || !text.trim()}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '生成语音'}
        </button>
        {audioUrl && <audio src={audioUrl} controls className="h-9" />}
      </div>
      {err && <p className="text-xs text-amber-600 mt-2">{err}</p>}
    </Card>
  )
}

/* ---------------- 文生图 ---------------- */
function ImageTool() {
  const [prompt, setPrompt] = useState('')
  const [imgUrl, setImgUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const run = async () => {
    if (!prompt.trim()) return
    setLoading(true); setErr(''); setImgUrl('')
    try {
      const r = await aiAPI.image(prompt)
      if (r.ok && r.image) setImgUrl(`data:image/png;base64,${r.image}`)
      else setErr(r.error || '生成失败')
    } catch (e) { setErr(e instanceof Error ? e.message : '失败') }
    finally { setLoading(false) }
  }

  return (
    <Card icon={<ImageIcon className="w-5 h-5" />} title="文生图" desc="根据描述生成课程配图">
      <input className="input-field mb-2" placeholder="例如：卡通风格的 Python 编程插画" value={prompt} onChange={e => setPrompt(e.target.value)} disabled={loading} onKeyDown={e => e.key === 'Enter' && run()} />
      <button className="btn-primary mb-2" onClick={run} disabled={loading || !prompt.trim()}>
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '生成图片'}
      </button>
      {err && <p className="text-xs text-amber-600 mb-1">{err}</p>}
      {imgUrl && <img src={imgUrl} alt="生成图" className="rounded-lg border border-gray-200 w-full" />}
    </Card>
  )
}

function Card({ icon, title, desc, children }: { icon: React.ReactNode; title: string; desc: string; children: React.ReactNode }) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-2 mb-1">
        <span className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">{icon}</span>
        <h2 className="font-semibold text-gray-800">{title}</h2>
      </div>
      <p className="text-xs text-gray-400 mb-4">{desc}</p>
      {children}
    </div>
  )
}
