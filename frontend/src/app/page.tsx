'use client'

import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { Sparkles, Code, Brain, ArrowRight } from 'lucide-react'

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative bg-gradient-to-b from-brand-50 to-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-20 md:py-28 text-center">
          <p className="inline-flex items-center gap-2 text-xs font-semibold text-brand-600 bg-brand-50 border border-brand-100 px-3 py-1.5 rounded-lg mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-500" /> AI 编程学习 Agent
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight mb-5">
            Edu<span className="text-brand-600">Agent</span>
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed mb-8">
            不是平台，不是工具箱。就是一个 Agent——
            会教编程、会出题、会判题、会排复习的 AI 学习伙伴。
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            {user ? (
              <Link href="/chat" className="btn-primary !px-7 !py-3 text-base">
                开始对话 <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link href="/register" className="btn-primary !px-7 !py-3 text-base">
                  免费开始 <ArrowRight className="w-4 h-4" />
                </Link>
                <Link href="/login" className="btn-secondary !px-7 !py-3 text-base">
                  登录
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* 特性 */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
              跟 ChatGPT 不一样的编程学习
            </h2>
            <p className="text-gray-500 max-w-xl mx-auto">
              代码沙箱执行、自适应出题、间隔重复复习、长期记忆
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Feature
              icon={Code}
              title="代码沙箱"
              desc="学生写代码 → Agent 执行 → 读输出 → 给反馈"
            />
            <Feature
              icon={Brain}
              title="自适应出题"
              desc="根据掌握度和薄弱点动态出题，不是随机题库"
            />
            <Feature
              icon={Sparkles}
              title="间隔重复"
              desc="FSRS 记忆曲线追踪，主动安排复习不遗漏"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 text-center text-sm text-gray-400 border-t border-gray-100">
        <p>EduAgent · MIT License</p>
      </footer>
    </div>
  )
}

function Feature({ icon: Icon, title, desc }: { icon: typeof Code; title: string; desc: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm hover:border-gray-300 transition-colors">
      <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
        <Icon className="w-5 h-5" />
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
    </div>
  )
}
