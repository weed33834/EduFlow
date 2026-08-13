'use client'

import Link from 'next/link'
import { BookOpen, Brain, Target, ArrowRight, GraduationCap, Users, BarChart3, RefreshCw } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-4rem)]">
      {/* Hero */}
      <section className="relative bg-white border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 py-20 md:py-28 text-center">
          <p className="inline-flex items-center gap-2 text-xs font-semibold text-brand-600 bg-brand-50 border border-brand-100 px-3 py-1.5 rounded-lg mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-500" /> 自学辅助平台
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight mb-5">
            EduFlow <span className="text-brand-600">畅学</span>
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
            以学生为中心的自学平台：管理学习路径、完成练习、按记忆规律复习，AI 在需要时提供辅导。
          </p>
          <div className="flex gap-3 justify-center flex-wrap mt-8">
            <Link href="/dashboard" className="btn-primary !px-7 !py-3 text-base">
              开始使用 <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/register" className="btn-secondary !px-7 !py-3 text-base">
              免费注册
            </Link>
          </div>
        </div>
      </section>

      {/* 核心功能 */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">围绕完整学习闭环设计</h2>
            <p className="text-gray-500 max-w-xl mx-auto">从规划、学习、练习到复习与复盘，每一环都衔接顺畅</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Feature icon={Target} title="学习路径" desc="创建学习目标与模块，系统自动计算进度" />
            <Feature icon={BookOpen} title="练习与判题" desc="创建练习会话，服务端自动判题并记录成绩" />
            <Feature icon={RefreshCw} title="间隔复习" desc="练习后自动安排复习，按记忆规律排期" />
            <Feature icon={BarChart3} title="进度与薄弱点" desc="学习时长、完成度与薄弱点分析" />
            <Feature icon={GraduationCap} title="AI 导师" desc="苏格拉底式答疑，基于知识库提供有据回答" />
            <Feature icon={Users} title="AI 伴学" desc="像同学一样讨论，多轮对话、云端记忆" />
          </div>
        </div>
      </section>

      {/* 怎么开始 */}
      <section className="py-16 px-4 bg-white border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <span className="inline-flex items-center gap-2 text-xs font-semibold text-brand-600 bg-brand-50 border border-brand-100 px-3 py-1.5 rounded-lg mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500" /> 三步开始
            </span>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900">三分钟就能开始学习</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <Step n={1} title="注册账号" desc="免费注册，登录后进入个人学习空间。" />
            <Step n={2} title="创建课程" desc="输入学习目标，AI 自动规划模块与进度。" />
            <Step n={3} title="练习·复习·AI辅导" desc="做题、按记忆规律复习，随时向 AI 求助。" />
          </div>
          <div className="text-center mt-8">
            <Link href="/register" className="btn-primary !px-7 !py-3">
              立即开始 <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto bg-white border border-gray-200 rounded-2xl p-10 md:p-12 text-center shadow-sm">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">现在开始</h2>
          <p className="text-gray-500 mb-7 max-w-md mx-auto">免费注册，即可使用学习路径、练习与复习的全套流程。</p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link href="/register" className="btn-primary">免费注册</Link>
            <Link href="/login" className="btn-secondary">已有账号，登录</Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 text-center text-sm text-gray-400 border-t border-gray-100">
        <p>EduFlow 畅学 · Apache-2.0 开源</p>
      </footer>
    </div>
  )
}

function Feature({ icon: Icon, title, desc }: { icon: typeof Target; title: string; desc: string }) {
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

function Step({ n, title, desc }: { n: number; title: string; desc: string }) {
  return (
    <div className="bg-gray-50 border border-gray-100 rounded-2xl p-6">
      <div className="w-9 h-9 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold mb-3">{n}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
    </div>
  )
}
