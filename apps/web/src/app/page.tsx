'use client'

import Link from 'next/link'
import { BookOpen, Brain, Target, Rocket, ArrowRight, Sparkles, Users, BarChart3, GraduationCap } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-4rem)]">
      {/* Hero Section */}
      <section
        className="relative flex items-center justify-center overflow-hidden pt-12 pb-20"
        style={{ background: 'linear-gradient(135deg, #1A1A2E 0%, #2D1B69 40%, #4B3FE3 70%, #27D2BF 100%)' }}
      >
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 20% 20%, rgba(75,63,227,0.4) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 80% 80%, rgba(39,210,191,0.3) 0%, transparent 60%)',
          }}
        />
        <div className="relative z-10 text-center px-4 max-w-4xl mx-auto animate-fade-in">
          <div className="inline-block bg-white/10 backdrop-blur-md border border-white/20 text-white/90 text-sm font-semibold px-5 py-2 rounded-full mb-6">
            🚀 AI驱动 · 学生主导 · 自学平台
          </div>
          <h1 className="text-5xl md:text-7xl font-black text-white tracking-tight leading-tight mb-4">
            EduFlow <span className="bg-gradient-to-r from-[#27D2BF] to-[#4B3FE3] bg-clip-text text-transparent">畅学</span>
          </h1>
          <p className="text-xl md:text-2xl text-white/70 font-light mb-4 tracking-wider">让学习自然流畅，让知识触手可及</p>
          <p className="text-base text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
            AI 驱动的学生自学平台，将学生置于学习的中心。AI 智能体作为辅助角色，按需提供辅导、练习、出题和进度追踪。
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 bg-white text-brand-600 font-semibold px-8 py-3.5 rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
            >
              开始学习 <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md text-white border border-white/20 font-semibold px-8 py-3.5 rounded-full hover:bg-white/20 transition-all"
            >
              免费注册
            </Link>
          </div>
        </div>
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/30 text-xs flex flex-col items-center gap-2 animate-bounce">
          <span>向下滚动</span>
          <div className="w-4 h-4 border-r-2 border-b-2 border-white/30 rotate-45" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block text-xs font-bold tracking-widest text-brand-600 bg-brand-100 px-3 py-1 rounded-full mb-4">
              核心功能
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">六大功能模块，覆盖完整学习闭环</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">从学习规划到评估诊断，从内容获取到社交协作，全方位支持学生自主学习</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Target, title: '学习管理', desc: '学习目标设定、智能路径规划、间隔重复复习、自动排期', color: 'from-purple-500 to-indigo-500' },
              { icon: Brain, title: '评估与诊断', desc: '入学能力评估、薄弱点分析、学习周报/月报自动生成', color: 'from-teal-400 to-cyan-500' },
              { icon: BookOpen, title: '内容与资源', desc: '内容市场、资源推荐系统、笔记与标注、知识图谱', color: 'from-blue-500 to-indigo-500' },
              { icon: Users, title: '社交与协作', desc: '学习社区、学习伙伴匹配、小组项目协作、知识问答', color: 'from-pink-500 to-rose-500' },
              { icon: Sparkles, title: '激励与游戏化', desc: '成就系统、学习积分与排行榜、学习挑战赛徽章', color: 'from-amber-400 to-orange-500' },
              { icon: BarChart3, title: '工具与体验', desc: '专注模式(番茄钟)、学习日历、浏览器插件、多语言', color: 'from-emerald-400 to-green-500' },
            ].map((f, i) => (
              <div key={i} className="glass-card p-6 hover:-translate-y-1 transition-all duration-300 group">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <f.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Agents Section */}
      <section id="agents" className="py-24 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="inline-block text-xs font-bold tracking-widest text-brand-600 bg-brand-100 px-3 py-1 rounded-full mb-4">
              AI 智能体
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">三位 AI 学习助手</h2>
            <p className="text-gray-500 max-w-2xl mx-auto">AI 导师、AI 伴学、AI 出题者，按需辅助，从不打扰</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: GraduationCap, title: 'AI 导师 Tutor', desc: '按需辅导答疑，苏格拉底式教学引导，不会的时候随时提问', color: 'from-brand-600 to-purple-700', href: '/ai-tutor' },
              { icon: Users, title: 'AI 伴学 Buddy', desc: '像同学一样协同练习对话，一起讨论问题，互相鼓励', color: 'from-teal-400 to-teal-600', href: '/ai-buddy' },
              { icon: Brain, title: 'AI 出题者 Examiner', desc: '自适应出题，根据掌握程度调整难度，即时反馈解析', color: 'from-blue-500 to-blue-700', href: '/practice' },
            ].map((a, i) => (
              <Link key={i} href={a.href} className="glass-card p-8 text-center hover:-translate-y-1 transition-all duration-300 block">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${a.color} flex items-center justify-center mx-auto mb-5`}>
                  <a.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{a.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{a.desc}</p>
                <span className="inline-flex items-center gap-1 text-sm text-brand-600 font-medium mt-4">
                  立即体验 <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card p-10 md:p-14 text-center" style={{ background: 'linear-gradient(135deg, rgba(75,63,227,0.06), rgba(39,210,191,0.06))' }}>
            <Rocket className="w-10 h-10 text-brand-600 mx-auto mb-4" />
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">现在开始你的学习之旅</h2>
            <p className="text-gray-500 mb-8 max-w-xl mx-auto">免费注册，立即拥有 AI 学习助手、个性化学习路径与进度追踪</p>
            <div className="flex gap-3 justify-center flex-wrap">
              <Link href="/register" className="btn-primary">
                免费注册 <ArrowRight className="w-4 h-4" />
              </Link>
              <Link href="/login" className="btn-secondary">
                已有账号，登录
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 text-center text-sm text-gray-400 border-t border-gray-100">
        <p>EduFlow 畅学 — AI-driven student self-learning platform</p>
        <p className="mt-1">MIT License · Open Source</p>
      </footer>
    </div>
  )
}
