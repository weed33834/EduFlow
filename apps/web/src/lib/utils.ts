import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { DIFFICULTY_LABELS, MODULE_STATUS, PATH_STATUS } from './constants'

/** 合并 Tailwind 类名 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 格式化时长（分钟）为中文描述
 * - 小于 60 分钟：X分钟
 * - 大于等于 60 分钟：X小时Y分钟
 */
export function formatDuration(minutes: number): string {
  if (!minutes || minutes <= 0) return '0分钟'
  if (minutes < 60) return `${Math.round(minutes)}分钟`
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
}

/** 兼容旧名 */
export const formatTime = formatDuration

/** 将秒数格式化为中文时长描述 */
export function formatSeconds(seconds: number): string {
  return formatDuration(Math.round((seconds || 0) / 60))
}

/**
 * 根据难度获取标签颜色（Tailwind 类名）
 */
export function getDifficultyColor(difficulty: string): string {
  const map: Record<string, string> = {
    beginner: 'bg-green-100 text-green-700',
    easy: 'bg-blue-100 text-blue-700',
    medium: 'bg-amber-100 text-amber-700',
    hard: 'bg-red-100 text-red-700',
    expert: 'bg-purple-100 text-purple-700',
    intermediate: 'bg-amber-100 text-amber-700',
    advanced: 'bg-purple-100 text-purple-700',
  }
  return map[difficulty] || 'bg-gray-100 text-gray-700'
}

/**
 * 根据状态（module/path）获取标签颜色
 */
export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600',
    in_progress: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    active: 'bg-brand-100 text-brand-700',
    paused: 'bg-amber-100 text-amber-700',
    draft: 'bg-gray-100 text-gray-500',
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

/**
 * 根据状态获取中文标签（兼容 module 与 path 状态）
 */
export function getStatusLabel(status: string): string {
  return (
    MODULE_STATUS[status] ||
    PATH_STATUS[status] ||
    status ||
    '未知'
  )
}

/** 根据难度获取中文标签 */
export function getDifficultyLabel(difficulty: string): string {
  return DIFFICULTY_LABELS[difficulty] || difficulty || '未知'
}

/** 获取用户头像首字母（用于占位头像） */
export function getInitials(name?: string): string {
  if (!name) return 'U'
  const trimmed = name.trim()
  if (!trimmed) return 'U'
  // 中文名取最后一个字
  if (/[\u4e00-\u9fa5]/.test(trimmed)) return trimmed.slice(-1)
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}

/** 简单邮箱校验 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

/** 将 ISO 时间字符串格式化为 yyyy-mm-dd HH:MM */
export function formatDateTime(iso?: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 将 ISO 时间字符串格式化为 yyyy-mm-dd */
export function formatDate(iso?: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** 题目 ID 归一化：确保所有题目 ID 是数字 */
export function normalizeQuestionId(id: unknown, idx: number): number {
  return typeof id === 'number' && !isNaN(id) ? id : idx + 1
}
