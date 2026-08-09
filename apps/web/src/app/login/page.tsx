'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Mail, Lock, ArrowRight, AlertCircle, GraduationCap, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { isValidEmail } from '@/lib/utils'

export default function LoginPage() {
  const router = useRouter()
  const { user, loading, login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  // 已登录则跳转
  useEffect(() => {
    if (!loading && user) router.replace('/dashboard')
  }, [loading, user, router])

  const validate = () => {
    const e: { email?: string; password?: string } = {}
    if (!email.trim()) e.email = '请输入邮箱'
    else if (!isValidEmail(email)) e.email = '邮箱格式不正确'
    if (!password) e.password = '请输入密码'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (ev: FormEvent) => {
    ev.preventDefault()
    setServerError('')
    if (!validate()) return
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      router.replace('/dashboard')
    } catch (err) {
      setServerError(err instanceof Error ? err.message : '登录失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-purple-700 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <GraduationCap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">欢迎回来</h1>
          <p className="text-gray-500 mt-1 text-sm">登录 EduFlow，继续你的学习之旅</p>
        </div>

        <div className="glass-card p-8">
          {serverError && (
            <div className="mb-5 flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-100 text-sm text-red-600">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label className="label" htmlFor="email">邮箱</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="email"
                  type="email"
                  className={`input-field pl-10 ${errors.email ? 'border-red-400 focus:ring-red-200 focus:border-red-400' : ''}`}
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email}</p>}
            </div>

            <div>
              <label className="label" htmlFor="password">密码</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className={`input-field pl-10 pr-10 ${errors.password ? 'border-red-400 focus:ring-red-200 focus:border-red-400' : ''}`}
                  placeholder="请输入密码"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password}</p>}
            </div>

            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? '登录中...' : <>登录 <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            还没有账号？{' '}
            <Link href="/register" className="text-brand-600 font-medium hover:underline">
              立即注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
