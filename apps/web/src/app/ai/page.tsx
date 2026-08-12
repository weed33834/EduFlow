'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  GraduationCap, Users, Sparkles, Wand2, ArrowRight, Loader2, CheckCircle, AlertTriangle,
} from 'lucide-react'
import { aiAPI, type CapabilitiesInfo } from '@/lib/api'

export default function AiHubPage() {
  const [caps, setCaps] = useState<CapabilitiesInfo | null>(null)

  useEffect(() => {
    aiAPI.capabilities().then(setCaps).catch(() => setCaps(null))
  }, [])

  const entries = [
    { href: '/ai-tutor', icon: GraduationCap, title: 'AI 导师', desc: '苏格拉底式辅导，按需答疑', color: 'bg-brand-600' },
    { href: '/ai-buddy', icon: Users, title: 'AI 伴学', desc: '像同学一样讨论练习', color: 'bg-teal-600' },
    { href: '/ai-tools', icon: Sparkles, title: 'AI 工具箱', desc: '概念解释 · 知识库 · 配音 · 文生图', color: 'bg-indigo-600' },
    { href: '/presentation', icon: Wand2, title: '讲解视频', desc: '自动生成 PPT + 配音讲解', color: 'bg-violet-600' },
  ]

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-600" /> AI 助手
        </h1>
        <p className="text-gray-500 mt-1">一站式使用 EduFlow 的全部 AI 能力。</p>
      </div>

      {/* 能力状态 */}
      <div className="glass-card p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700">当前模型能力</span>
          {!caps ? (
            <span className="text-xs text-gray-400 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> 探测中...</span>
          ) : !caps.configured ? (
            <span className="text-xs text-amber-600 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> 未配置模型端点</span>
          ) : (
            <span className="flex flex-wrap gap-1.5">
              {Object.entries(caps.capabilities || {}).filter(([, v]) => v).map(([k]) => (
                <span key={k} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs">
                  <CheckCircle className="w-3 h-3" /> {caps.labels?.[k] || k}
                </span>
              ))}
              <Link href="/settings" className="text-xs text-brand-600 hover:underline self-center">管理模型</Link>
            </span>
          )}
        </div>
      </div>

      {/* 入口卡片 */}
      <div className="grid sm:grid-cols-2 gap-4">
        {entries.map((e, i) => (
          <Link key={i} href={e.href} className="glass-card p-6 flex items-center gap-4 hover:shadow-md hover:border-gray-300 transition-all group">
            <div className={`w-12 h-12 rounded-xl ${e.color} flex items-center justify-center flex-shrink-0`}>
              <e.icon className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="font-semibold text-gray-800">{e.title}</h2>
              <p className="text-sm text-gray-500 mt-0.5">{e.desc}</p>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-brand-500 transition-colors flex-shrink-0" />
          </Link>
        ))}
      </div>
    </main>
  )
}
