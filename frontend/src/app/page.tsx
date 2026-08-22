'use client'

import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import {
  Sparkles, Code, Brain, ArrowRight, TerminalSquare,
  CalendarClock, DatabaseZap,
} from 'lucide-react'

function GithubMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden>
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.15c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.75 2.69 1.25 3.35.95.1-.74.4-1.25.72-1.54-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 5.74 0c2.19-1.49 3.15-1.18 3.15-1.18.62 1.59.23 2.76.11 3.05.73.81 1.18 1.83 1.18 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.04.77 2.1v3.11c0 .3.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
    </svg>
  )
}

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-aurora bg-grid">
      {/* 导航 */}
      <header className="sticky top-0 z-40 backdrop-blur-xl border-b" style={{ borderColor: 'var(--border)' }}>
        <nav className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
              <Brain className="w-5 h-5 text-white" />
            </span>
            <span className="font-bold text-lg tracking-tight text-gray-900">
              Edu<span className="text-brand-600">Agent</span>
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com/weed33834/EduAgent"
              target="_blank"
              rel="noreferrer"
              className="p-2.5 rounded-xl text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-800"
              aria-label="GitHub"
            >
              <GithubMark className="w-5 h-5" />
            </a>
            {user ? (
              <Link href="/chat" className="btn-primary !py-2 text-sm">
                进入对话 <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link href="/login" className="btn-secondary !py-2 text-sm hidden sm:inline-flex">
                  登录
                </Link>
                <Link href="/register" className="btn-primary !py-2 text-sm">
                  免费开始
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative max-w-6xl mx-auto px-4 pt-20 pb-16 md:pt-28 md:pb-24 text-center">
        <p className="animate-fade-in inline-flex items-center gap-2 text-xs font-semibold text-brand-700 bg-brand-50 border border-brand-200/70 px-3 py-1.5 rounded-full mb-7 dark:bg-brand-600/10 dark:text-brand-300 dark:border-brand-500/30">
          <Sparkles className="w-3.5 h-3.5" />
          开源 AI 编程学习 Agent · v0.5
        </p>

        <h1 className="animate-fade-in animate-delay-1 text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6 text-gray-900">
          会教学的
          <span className="bg-gradient-to-r from-brand-600 via-indigo-500 to-brand-500 bg-clip-text text-transparent">
            {' '}AI 学习伙伴
          </span>
        </h1>

        <p className="animate-fade-in animate-delay-2 text-lg md:text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed mb-10 dark:text-gray-400">
          不是平台，不是工具箱。它教你概念、给你出题、<b className="font-semibold text-gray-700 dark:text-gray-200">真的会判题</b>、
          把你写错的代码跑起来讲给你听，还按记忆曲线安排复习。
        </p>

        <div className="animate-fade-in animate-delay-3 flex flex-wrap gap-3 justify-center mb-20">
          {user ? (
            <Link href="/chat" className="btn-primary !px-8 !py-3.5 text-base">
              继续学习 <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link href="/register" className="btn-primary !px-8 !py-3.5 text-base">
                免费开始 <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/login" className="btn-secondary !px-8 !py-3.5 text-base">
                我有账号
              </Link>
            </>
          )}
        </div>

        {/* 产品预览：对话窗口 mockup */}
        <div className="animate-fade-in animate-delay-3 relative max-w-3xl mx-auto animate-float-slow">
          <div className="absolute -inset-x-8 -top-8 bottom-0 bg-gradient-to-b from-brand-500/15 to-transparent rounded-3xl blur-2xl" aria-hidden />
          <div className="glass-card !rounded-2xl overflow-hidden text-left shadow-xl">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <span className="w-3 h-3 rounded-full bg-red-400" />
              <span className="w-3 h-3 rounded-full bg-amber-400" />
              <span className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-3 text-xs text-gray-400">EduAgent — 对话</span>
            </div>
            <div className="p-5 space-y-4 text-sm">
              <div className="flex justify-end">
                <p className="bg-gradient-to-br from-brand-600 to-indigo-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-md max-w-[80%]">
                  什么是递归？写个例子给我看看
                </p>
              </div>
              <div className="flex items-start gap-2.5">
                <span className="icon-tile w-8 h-8 bg-gradient-to-br from-brand-600 to-indigo-600 rounded-lg">
                  <Brain className="w-4 h-4 text-white" />
                </span>
                <div className="glass-card !rounded-2xl !rounded-tl-md px-4 py-3 space-y-2.5 max-w-[85%]">
                  <p className="leading-relaxed">递归就是函数调用自己。关键是<b>终止条件</b>——没有它就会栈溢出：</p>
                  <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-xs font-mono overflow-x-auto"><code>{`def fact(n):
    if n <= 1:   # 终止条件
        return 1
    return n * fact(n - 1)`}</code></pre>
                  <p className="text-gray-500 dark:text-gray-400">想验证一下理解？我出道题考考你 🎯</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 特性 */}
      <section className="max-w-6xl mx-auto px-4 py-16 md:py-24">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-900 mb-4">
            跟直接问 ChatGPT，差在哪？
          </h2>
          <p className="text-gray-500 max-w-xl mx-auto dark:text-gray-400">
            四件普通聊天机器人做不到的事
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <Feature
            icon={TerminalSquare}
            title="真·代码执行"
            desc="你的代码在隔离沙箱里真实运行，报错原样讲给你听，而不是猜"
          />
          <Feature
            icon={Sparkles}
            title="出题并判题"
            desc="按水平生成选择题，答完立刻判分讲解——闭环，不是只出不管"
          />
          <Feature
            icon={CalendarClock}
            title="记住该复习的"
            desc="FSRS 记忆曲线主动安排复习，快忘的时候它会出现"
          />
          <Feature
            icon={DatabaseZap}
            title="越用越懂你"
            desc="长期记忆 + 学生画像，薄弱点被持续追踪"
          />
        </div>
      </section>

      {/* 底部 CTA */}
      {!user && (
        <section className="max-w-4xl mx-auto px-4 pb-24">
          <div className="glass-card p-10 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-indigo-500/10" aria-hidden />
            <h2 className="relative text-2xl md:text-3xl font-bold tracking-tight text-gray-900 mb-3">
              准备好开始了吗？
            </h2>
            <p className="relative text-gray-500 mb-8 dark:text-gray-400">
              注册即用，所有组件开源自托管
            </p>
            <Link href="/register" className="relative btn-primary !px-8 !py-3 text-base inline-flex">
              免费开始 <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="border-t py-8 px-4" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-gray-400">
          <p>EduAgent · MIT License</p>
          <p className="flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5" />
            FastAPI · LangGraph · Next.js · Qdrant · E2B · FSRS
          </p>
        </div>
      </footer>
    </div>
  )
}

function Feature({
  icon: Icon,
  title,
  desc,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  desc: string
}) {
  return (
    <div className="glass-card p-6 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg group">
      <span className="icon-tile bg-gradient-to-br from-brand-50 to-indigo-50 text-brand-600 group-hover:from-brand-600 group-hover:to-indigo-600 group-hover:text-white transition-colors mb-4 dark:from-brand-600/15 dark:to-indigo-600/15">
        <Icon className="w-5 h-5" />
      </span>
      <h3 className="font-semibold text-gray-900 mb-1.5">{title}</h3>
      <p className="text-sm leading-relaxed text-gray-500 dark:text-gray-400">{desc}</p>
    </div>
  )
}
