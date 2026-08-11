/** @type {import('next').NextConfig} */
// API 上游地址：本地开发默认 localhost:8000，Docker 容器内通过 API_UPSTREAM
// 覆盖为 http://api:8000。rewrites 在服务端运行时求值，因此该变量运行时可读。
const apiUpstream = process.env.API_UPSTREAM || 'http://localhost:8000'

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@eduflow/ui', '@eduflow/shared'],
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${apiUpstream}/api/:path*` }
    ]
  }
}

module.exports = nextConfig
