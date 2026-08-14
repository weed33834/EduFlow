# 架构设计文档

> 文档版本: v2.0 | 最后更新: 2026-08-09

---

## 1. 系统架构概述

EduFlow 畅学是一个 AI 驱动的学生自主学习平台，采用 **Monorepo + 多服务** 架构。整个仓库基于 pnpm workspace 管理，包含四个独立服务：Web 前端、API 主服务、AI 智能体服务和 Engine 引擎服务。各服务之间通过 RESTful API 进行通信，前端请求经 Next.js rewrites 代理转发至后端。

```
┌──────────────────────────────────────────────────────────────┐
│                     Web 前端 (Next.js)                        │
│                      端口 3000                                │
│   浏览器 ──▶ Next.js ──(rewrites)──▶ /api/* → API 服务         │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP
┌──────────────────────────────▼───────────────────────────────┐
│                   API 主服务 (FastAPI)                        │
│                      端口 8000                                │
│  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────┐  │
│  │  auth  │ │ learning │ │ practice │ │progress │ │  ai  │  │
│  └────────┘ └──────────┘ └──────────┘ └─────────┘ └──┬───┘  │
│  认证鉴权 · 业务逻辑 · 数据持久化 · AI 请求代理          │      │
└──────────────┬──────────────────────────┬──────────────┼──────┘
               │                           │              │
               ▼                           ▼              ▼
        ┌───────────┐             ┌───────────┐    ┌───────────┐
        │ 数据库     │             │  Redis    │    │ AI 服务   │
        │SQLite/PG   │             │  缓存     │    │ port 8100 │
        └───────────┘             └───────────┘    └─────┬─────┘
                                                          │
                                                   ┌──────▼─────┐
                                                   │ Engine 服务 │
                                                   │ port 8200  │
                                                   │ FSRS 引擎  │
                                                   └────────────┘
```

---

## 2. Monorepo 结构

项目使用 pnpm workspace 管理多个包，工作区配置在 `pnpm-workspace.yaml` 中：

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'services/*'
```

```
eduflow/
├── apps/
│   └── web/                       # Next.js 前端应用
│       ├── src/
│       │   ├── app/                # Next.js App Router 页面
│       │   ├── components/         # React 组件
│       │   ├── contexts/           # React Context（认证等）
│       │   └── lib/                # API 客户端、常量、工具
│       ├── next.config.js          # rewrites 代理配置
│       └── package.json
├── packages/
│   ├── shared/                    # 共享类型与工具
│   └── ui/                        # 共享 UI 组件库
├── services/
│   ├── api/                       # API 主服务 (FastAPI)
│   ├── ai/                        # AI 智能体服务 (FastAPI)
│   └── engine/                    # 引擎服务 (FastAPI)
├── docker/
│   └── docker-compose.yml         # Docker 编排配置
├── docs/                          # 项目文档
├── package.json                   # 根 monorepo 配置
└── pnpm-workspace.yaml
```

根目录 `package.json` 提供统一的脚本入口：

```json
{
  "scripts": {
    "dev": "pnpm --parallel -r run dev",
    "build": "pnpm -r run build",
    "lint": "pnpm -r run lint"
  }
}
```

---

## 3. 四个服务

### 3.1 Web 前端服务（端口 3000）

| 属性 | 说明 |
|------|------|
| 技术栈 | Next.js + TypeScript + Tailwind CSS |
| 端口 | 3000 |
| 入口 | `apps/web/src/app/layout.tsx` |
| API 客户端 | `apps/web/src/lib/api.ts` |

前端通过 Next.js 的 `rewrites` 功能将所有 `/api/*` 请求代理到 API 服务：

```javascript
// apps/web/next.config.js
async rewrites() {
  return [
    { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }
  ]
}
```

前端 API 客户端自动从 `localStorage` 读取 JWT Token 并附加到 `Authorization: Bearer <token>` 请求头中。Token 和用户信息分别存储在 `eduflow_token` 和 `eduflow_user` 两个键中。

页面路由包括：登录、注册、仪表盘、学习路径、练习、进度、AI 导师、AI 伴学、设置。

### 3.2 API 主服务（端口 8000）

| 属性 | 说明 |
|------|------|
| 技术栈 | FastAPI + SQLAlchemy (async) + Pydantic |
| 端口 | 8000 |
| 入口 | `services/api/main.py` |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |

API 服务是系统的核心，负责认证鉴权、业务逻辑处理和数据持久化。应用启动时通过 `lifespan` 上下文自动创建数据库表。它注册了五个路由模块：

- `auth` — 用户注册、登录、个人信息管理
- `learning` — 学习路径与模块的 CRUD
- `practice` — 练习会话管理与答案提交
- `progress` — 学习进度追踪与统计
- `ai` — AI 请求代理（转发至 AI 服务）

此外提供 `GET /api/health` 健康检查端点。

### 3.3 AI 智能体服务（端口 8100）

| 属性 | 说明 |
|------|------|
| 技术栈 | FastAPI + OpenAI SDK |
| 端口 | 8100 |
| 入口 | `services/ai/main.py` |

AI 服务提供四个智能体的能力（详见 [AI 智能体文档](ai-agents.md)）：

- **Tutor（导师）** — 苏格拉底式教学引导、概念解释
- **Buddy（学习伙伴）** — 学习伙伴式对话
- **Examiner（出题官）** — 自适应出题、答案评估
- **Planner（规划师）** — 学习路径规划

该服务具备智能降级机制：当未配置 `OPENAI_API_KEY` 时，各接口返回按 agent 类型定制的降级回复，保证服务始终可用。

### 3.4 Engine 引擎服务（端口 8200）

| 属性 | 说明 |
|------|------|
| 技术栈 | FastAPI + Python 标准库 |
| 端口 | 8200 |
| 入口 | `services/engine/main.py` |

Engine 服务提供学习科学相关的算法能力：

- **FSRS 间隔重复** — 基于知识掌握度、复习次数、上次得分等计算下次复习时间
- **知识追踪** — 分析各主题掌握度，识别薄弱知识点
- **时长估算** — 根据主题难度和学习深度估算学习时长

---

## 4. 数据存储

### 4.1 数据库

采用双数据库策略：

| 环境 | 数据库 | 连接字符串示例 |
|------|--------|---------------|
| 开发 | SQLite (aiosqlite) | `sqlite+aiosqlite:///./eduflow.db` |
| 生产 | PostgreSQL (asyncpg) | `postgresql+asyncpg://eduflow:eduflow@host:5432/eduflow` |

通过 `DATABASE_URL` 环境变量切换。开发环境默认使用 SQLite，文件为项目根目录下的 `eduflow.db`，并启用 SQLite 外键约束（`PRAGMA foreign_keys=ON`）。数据库表在应用启动时通过 `Base.metadata.create_all` 自动创建，无需手动迁移。

### 4.2 缓存

使用 Redis 作为缓存层，默认连接 `redis://localhost:6379/0`。在 Docker 部署中由 `redis:7-alpine` 提供。

---

## 5. 认证流程

系统采用 JWT（JSON Web Token）进行无状态认证。

```
1. 注册 / 登录
   用户提交凭据 → API 服务验证 → 生成 JWT → 返回 {access_token, user}

2. 请求受保护资源
   前端从 localStorage 读取 token → 附加 Authorization: Bearer <token>
   → API 服务 get_current_user 依赖解码 JWT → 校验用户 → 返回数据

3. Token 失效
   JWT 过期或无效 → 返回 401 Unauthorized
```

认证实现细节：

- **密码哈希**：使用 bcrypt 加密存储（`core/security.py`）
- **Token 生成**：使用 python-jose 库，算法为 HS256
- **Token 载荷**：`{"sub": user_id, "email": email, "exp": 过期时间}`
- **有效期**：默认 7 天（`ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7`）
- **校验依赖**：`get_current_user` 通过 `HTTPBearer` 提取 Token，解码后查询数据库验证用户存在且 `is_active`

---

## 6. 数据流

### 6.1 总体数据流

```
浏览器
  │
  ▼
Next.js 前端 (port 3000)
  │  fetch /api/* (rewrites 代理)
  ▼
API 服务 (port 8000)
  │
  ├──▶ 数据库 (SQLite / PostgreSQL)     ← 认证、学习、练习、进度数据
  ├──▶ Redis (缓存)
  ├──▶ AI 服务 (port 8100)              ← AI 代理转发
  └──▶ Engine 服务 (port 8200)          ← 知识追踪、间隔重复
```

### 6.2 学习闭环数据流

```
用户登录 → 创建学习路径 → 添加模块 → 开始练习会话
                                        │
                                        ▼
                                   提交答案 (POST /api/practice/submit)
                                        │
                                        ▼
                                   完成会话 (PUT /api/practice/sessions/{id}/complete)
                                        │
                          ┌─────────────┴─────────────┐
                          ▼                           ▼
                    更新模块状态                  创建/更新进度记录
                    (completed/in_progress)       (quiz_scores, weak/strong_points)
                          │
                          ▼
                    重算路径进度
                    (_recalculate_path_progress)
```

### 6.3 AI 请求代理流

前端 AI 请求经 API 服务代理转发至 AI 服务，API 服务负责附加用户身份信息：

```
前端 → POST /api/ai/chat (带 JWT)
         │
         ▼
API 服务 ai 路由 (get_current_user 鉴权)
         │  注入 user_id 到 payload
         ▼
AI 服务 POST /api/agents/chat (HTTP 转发，超时 60s)
         │
         ├──▶ 有 OPENAI_API_KEY → 调用 OpenAI API → 返回结果
         └──▶ 无 API Key → 返回智能降级回复
```

AI 路由还负责前后端字段映射，例如 `ExplainRequest` 通过 alias 将前端的 `detail_level` 映射为 AI 服务期望的 `level`，`PlanRequest` 将 `difficulty` 和 `context` 映射为 `preferences`。

---

## 7. 数据模型

系统包含五个核心数据模型，定义在 `services/api/models/` 中：

### 7.1 User（用户）

表名：`users`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 用户 ID |
| email | String(255) | 邮箱，唯一 |
| username | String(100) | 用户名，唯一 |
| hashed_password | String(255) | bcrypt 哈希密码 |
| display_name | String(100) | 显示名称 |
| avatar_url | String(500) | 头像 URL |
| bio | Text | 个人简介 |
| is_active | Boolean | 是否激活 |
| is_verified | Boolean | 是否已验证 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 7.2 LearningPath（学习路径）

表名：`learning_paths`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 路径 ID |
| user_id | Integer (FK→users) | 所属用户 |
| title | String(200) | 路径标题 |
| description | Text | 描述 |
| goal | Text | 学习目标 |
| estimated_duration | Integer | 预计时长 |
| difficulty | String(20) | 难度（beginner/intermediate/advanced） |
| status | String(20) | 状态（not_started/in_progress/completed） |
| progress | Float | 完成进度（0-100） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 7.3 Module（模块）

表名：`modules`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 模块 ID |
| path_id | Integer (FK→learning_paths) | 所属路径 |
| title | String(200) | 模块标题 |
| description | Text | 描述 |
| order | Integer | 排序序号 |
| content | JSON | 模块内容（数组） |
| status | String(20) | 状态（not_started/in_progress/completed） |
| progress | Float | 完成进度 |
| estimated_minutes | Integer | 预计学习分钟数 |
| created_at | DateTime | 创建时间 |

### 7.4 PracticeSession（练习会话）

表名：`practice_sessions`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 会话 ID |
| user_id | Integer (FK→users) | 所属用户 |
| module_id | Integer (FK→modules) | 关联模块（可选） |
| session_type | String(50) | 会话类型（quiz 等） |
| topic | String(255) | 练习主题 |
| questions | JSON | 题目列表 |
| answers | JSON | 作答记录列表 |
| score | Float | 得分（0-100） |
| status | String(20) | 状态（in_progress/completed） |
| started_at | DateTime | 开始时间 |
| completed_at | DateTime | 完成时间 |

### 7.5 Progress（学习进度）

表名：`progress`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 进度 ID |
| user_id | Integer (FK→users) | 所属用户 |
| module_id | Integer (FK→modules) | 关联模块 |
| learning_time_minutes | Integer | 学习时长（分钟） |
| completion_percentage | Float | 完成百分比 |
| quiz_scores | JSON | 测验成绩记录列表 |
| weak_points | JSON | 薄弱知识点列表 |
| strong_points | JSON | 掌握知识点列表 |
| updated_at | DateTime | 更新时间 |

### 7.6 模型关系

```
User (1) ──── (N) LearningPath (1) ──── (N) Module (1) ──── (N) PracticeSession
  │                                       │
  │                                       └──── (1) ──── (N) Progress
  └──────────── (N) Progress
  └──────────── (N) PracticeSession
```

所有外键均配置了 `ON DELETE CASCADE`，删除路径时会级联删除其下的模块、练习会话和进度记录。模块状态变更后会触发路径进度的自动重算（`_recalculate_path_progress`）。

---

## 8. 技术栈总结

| 层级 | 技术 |
|------|------|
| 前端 | Next.js、TypeScript、Tailwind CSS |
| API 服务 | FastAPI、SQLAlchemy (async)、Pydantic、python-jose、bcrypt、httpx |
| AI 服务 | FastAPI、OpenAI SDK、Pydantic |
| Engine 服务 | FastAPI、Pydantic、Python 标准库 (math) |
| 数据库 | SQLite (aiosqlite) / PostgreSQL (asyncpg) |
| 缓存 | Redis |
| 包管理 | pnpm workspace (前端) / pip (Python 服务) |
| 容器化 | Docker、Docker Compose |

---

## 9. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 仓库结构 | pnpm Monorepo | 统一管理前后端及共享包，简化依赖与协作 |
| 服务拆分 | API + AI + Engine 三后端服务 | AI 计算与业务逻辑解耦，可独立扩展和降级 |
| 前端代理 | Next.js rewrites | 前端无感知地转发 API 请求，避免 CORS 问题 |
| 开发数据库 | SQLite | 零配置开箱即用，便于本地开发 |
| AI 降级 | 无 API Key 时返回智能 fallback | 保证服务始终可用，不因缺少配置而崩溃 |
| 认证 | JWT 无状态 | 简单高效，适合多服务架构 |
| 表创建 | 启动时自动 create_all | 开发友好，无需手动迁移 |
