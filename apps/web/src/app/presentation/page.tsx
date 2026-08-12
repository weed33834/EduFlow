'use client'

import { useState } from 'react'
import {
  PlayCircle, Sparkles, AlertTriangle, CheckCircle2, Loader2, FileText, Volume2, Wand2,
} from 'lucide-react'
import { aiAPI, type PresentationResult } from '@/lib/api'
import { cn } from '@/lib/utils'

const LEVELS = [
  { value: 'beginner', label: '入门' },
  { value: 'intermediate', label: '进阶' },
  { value: 'advanced', label: '高级' },
]

export default function PresentationPage() {
  const [topic, setTopic] = useState('')
  const [level, setLevel] = useState('beginner')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<PresentationResult | null>(null)
  const [error, setError] = useState('')
  const [activeSlide, setActiveSlide] = useState(0)

  const generate = async () => {
    const t = topic.trim()
    if (!t) { setError('请输入讲解主题'); return }
    setError('')
    setGenerating(true)
    setResult(null)
    setActiveSlide(0)
    try {
      const res = await aiAPI.presentation(t, level)
      setResult(res)
      if (!res.ok) setError(res.error || '生成失败')
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败')
    } finally {
      setGenerating(false)
    }
  }

  const slides = result?.slides || []
  const videoSrc = result?.video ? `data:video/mp4;base64,${result.video}` : null

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Wand2 className="w-6 h-6 text-brand-600" /> AI 讲解视频
        </h1>
        <p className="text-gray-500 mt-1">
          输入主题，AI 自动生成幻灯片 + 讲解稿，并（模型支持时）配上语音合成讲解视频。
        </p>
      </div>

      {/* 输入区 */}
      <div className="glass-card p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-3">
          <input
            className="input-field flex-1"
            placeholder="输入讲解主题，例如：递归算法 / Python 数据分析 / CSS 布局"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && generate()}
            disabled={generating}
          />
          <select className="input-field md:w-36" value={level} onChange={e => setLevel(e.target.value)} disabled={generating}>
            {LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
          <button onClick={generate} disabled={generating || !topic.trim()} className="btn-primary md:w-40 flex-shrink-0">
            {generating ? <><Loader2 className="w-4 h-4 animate-spin" /> 生成中</> : <><Sparkles className="w-4 h-4" /> 生成讲解</>}
          </button>
        </div>
        {error && (
          <div className="mt-3 flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-100 text-sm text-red-600">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /><span>{error}</span>
          </div>
        )}
      </div>

      {/* 能力降级提示 */}
      {result?.hint && (
        <div className="mb-6 flex items-start gap-2 p-4 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium mb-0.5">当前模型能力受限</p>
            <p>{result.hint} 当前已生成无声幻灯片版，可在设置中接入具备语音合成(TTS)能力的模型后自动配音。</p>
          </div>
        </div>
      )}
      {result?.warnings && result.warnings.length > 0 && (
        <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-gray-50 border border-gray-200 text-xs text-gray-600">
          <FileText className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>{result.warnings.map((w, i) => <div key={i}>· {w}</div>)}</div>
        </div>
      )}

      {/* 结果区 */}
      {generating && (
        <div className="glass-card p-16 text-center">
          <Loader2 className="w-10 h-10 text-brand-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-500">AI 正在撰写讲稿、生成幻灯片并合成视频，请稍候...</p>
        </div>
      )}

      {result?.ok && (
        <div className="space-y-6">
          {/* 视频播放 */}
          {videoSrc && (
            <div className="glass-card overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-2">
                <PlayCircle className="w-5 h-5 text-brand-600" />
                <span className="font-semibold text-gray-800">{result.title}</span>
                <span className="text-xs text-gray-400 ml-auto">{slides.length} 页幻灯片</span>
              </div>
              <video src={videoSrc} controls className="w-full aspect-video bg-black" />
            </div>
          )}

          <div className="grid lg:grid-cols-2 gap-6">
            {/* 幻灯片 */}
            <div className="glass-card p-5">
              <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-600" /> 幻灯片
              </h2>
              <div className="space-y-2">
                {slides.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveSlide(i)}
                    className={cn(
                      'w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors',
                      activeSlide === i ? 'border-brand-300 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                    )}
                  >
                    <span className="font-medium">{i + 1}. {s.title}</span>
                    <span className="block text-xs text-gray-400 mt-0.5 truncate">
                      {(s.bullets || []).slice(0, 2).join(' · ')}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* 讲稿 */}
            <div className="glass-card p-5">
              <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-brand-600" /> 讲解稿
              </h2>
              {result.narration_text ? (
                <div className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed max-h-72 overflow-y-auto">
                  {result.narration_text}
                </div>
              ) : (
                <p className="text-sm text-gray-400">本页暂无讲解稿</p>
              )}
            </div>
          </div>

          {!videoSrc && (
            <div className="flex items-start gap-2 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-sm text-emerald-700">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>讲解内容已生成（幻灯片 + 讲解稿）。当前端点无法合成视频，可在设置接入支持视频合成的模型。</span>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
