/** API 地址 */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/** localStorage 键名 */
export const STORAGE_KEYS = {
  TOKEN: 'eduagent_token',
  USER: 'eduagent_user',
} as const
