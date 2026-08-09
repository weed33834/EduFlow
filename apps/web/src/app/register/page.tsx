'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Mail, Lock, User, ArrowRight, AlertCircle, Rocket, Eye, EyeOff, Check } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { isValidEmail } from '@/lib/utils'

export default function RegisterPage() {
  const router = useRouter()
  const { user, loading, register } = useAuth()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{ username?: string; email?: string; password?: string }>({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  useEffect(() => {
    if (!loading && user) router.replace('/dashboard')
  }, [loading, user, router])

  const validate = () => {
    const e: { username?: string; email?: string; password?: string } = {}
    if (!username.trim()) e.username = '请输入用户名'
    else if (username.trim().length < 2) e.username = '用户名至少 2 个字符'
    if (!email.trim()) e.email = '请输入邮箱'
    else if (!isValidEmail(email)) e.email = '邮箱格式不正确'
    if (!password) e.password = '请输入密码'
    else if (password.length < 6) e.password = '密码至少 6 位'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (ev: FormEvent) => {
    ev.preventDefault()
    setServerError('')
    if (!validate()) return
    setSubmitting(true)
    try {
      await register({
        email: email.trim(),
        username: username.trim(),
        password,
        display_name: username.trim(),
      })
      router.replace('/dashboard')
    } catch (err) {
      setServerError(err instanceof Error ? err.message : '注册失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  const passwordChecks = [
    { label: '至少 6 位', ok: password.length >= 6 },
    { label: '包含字母', ok: /[a-zA-Z]/.test(password) },
    { label: '包含数字', ok: /\d/.test(password) },
  ]

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-400 to-brand-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Rocket className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">创建账号</h1>
          <p className="text-gray-500 mt-1 text-sm">免费注册，开启 AI 驱动的自学之旅</p>
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
              <label className="label" htmlFor="username">用户名</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="username"
                  type="text"
                  className={`input-field pl-10 ${errors.username ? 'border-red-400 focus:ring-red-200 focus:border-red-400' : ''}`}
                  placeholder="你的昵称"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
              {errors.username && <p className="mt-1 text-xs text-red-500">{errors.username}</p>}
            </div>

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
                  placeholder="至少 6 位密码"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="new-password"
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
              {!errors.password && password.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {passwordChecks.map(c => (
                    <span
                      key={c.label}
                      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${
                        c.ok ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {c.ok ? <Check className="w-3 h-3" /> : null}
                      {c.label}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? '注册中...' : <>免费注册 <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            已有账号？{' '}
            <Link href="/login" className="text-brand-600 font-medium hover:underline">
              去登录
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          注册即表示同意 EduFlow 的服务条款与隐私政策
        </p>
      </div>
    </div>
  )
}
