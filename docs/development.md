# 开发指南

> 文档版本: v2.0 | 最后更新: 2026-08-09

本指南面向 EduFlow 项目的开发者，介绍本地开发环境搭建、项目结构、数据库配置、代码规范以及前端 API 代理等核心开发流程。

---

## 目录

1. [环境要求](#1-环境要求)
2. [项目结构说明](#2-项目结构说明)
3. [本地开发步骤](#3-本地开发步骤)
4. [数据库说明](#4-数据库说明)
5. [前端 API 代理配置](#5-前端-api-代理配置)
6. [代码规范](#6-代码规范)
7. [环境变量配置](#7-环境变量配置)
8. [调试技巧](#8-调试技巧)
9. [常见问题](#9-常见问题)

---

## 1. 环境要求

EduFlow 采用 pnpm monorepo 架构，前端使用 Node.js / TypeScript，后端三个服务均使用 Python / FastAPI。

### 1.1 必备软件

| 软件 | 最低版本 | 推荐版本 | 用途 |
|------|----------|----------|------|
| Node.js | 18.0.0 | 20.0.0+ | 前端开发环境（Next.js 14） |
| pnpm | 8.0.0 | 9.0.0+ | Monorepo 包管理器 |
| Python | 3.12.0 | 3.12+ | 后端服务（API / AI / Engine） |
| pip | 23.0 | 24.0+ | Python 依赖安装 |
| Git | 2.30 | 2.40+ | 版本控制 |

### 1.2 可选软件（生产 / Docker 部署）

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker | 24.0+ | 容器化部署 |
| Docker Compose | 2.20+ | 多容器编排 |
| PostgreSQL | 16+ | 生产环境数据库 |
| Redis | 7.0+ | 缓存（AI 服务使用） |

### 1.3 验证安装

```bash
# 检查 Node.js 版本（需 >= 18）
node --version

# 检查 pnpm 版本（需 >= 8）
pnpm --version

# 检查 Python 版本（需 >= 3.12）
python --version

# 检查 pip
pip --version
```

### 1.4 Python 虚拟环境

后端每个服务（api、ai、engine）各自拥有独立的 `requirements.txt`，建议为每个服务创建独立的虚拟环境以避免依赖冲突。

---

## 2. 项目结构说明

EduFlow 是一个 pnpm workspace monorepo，包含前端应用、共享包和三个后端微服务。

```
eduflow/
├── apps/
│   └── web/                        # Next.js 14 前端应用（@eduflow/web）
│       ├── src/
│       │   ├── app/                # Next.js App Router 页面
│       │   │   ├── layout.tsx      # 根布局
│       │   │   ├── page.tsx        # 首页
│       │   │   ├── login/          # 登录页
│       │   │   ├── register/       # 注册页
│       │   │   ├── dashboard/      # 仪表盘
│       │   │   ├── learning/       # 学习路径管理
│       │   │   ├── practice/       # 练习模块
│       │   │   ├── progress/       # 进度追踪
│       │   │   ├── ai-tutor/       # AI 导师对话
│       │   │   ├── ai-buddy/       # AI 伴学对话
│       │   │   └── settings/       # 用户设置
│       │   ├── components/         # 组件
│       │   │   └── layout/         # 布局组件（如 Navbar）
│       │   ├── contexts/           # React Context（如 AuthContext）
│       │   └── lib/                # 工具库
│       │       ├── api.ts          # 前端 API 客户端
│       │       ├── constants.ts    # 常量定义
│       │       └── utils.ts        # 通用工具函数
│       ├── next.config.js          # Next.js 配置（含 rewrites 代理）
│       ├── tailwind.config.js       # Tailwind CSS 配置
│       ├── tsconfig.json           # TypeScript 配置
│       └── package.json            # 前端依赖
│
├── packages/
│   ├── shared/                     # 共享包（@eduflow/shared）
│   │   ├── types/                  # 共享 TypeScript 类型定义
│   │   ├── utils/                  # 共享常量与工具
│   │   └── index.ts
│   └── ui/                         # UI 组件库（@eduflow/ui）
│       ├── components/              # Button, GlassCard, ProgressBar, StatCard
│       └── index.ts
│
├── services/
│   ├── api/                        # API 主服务（FastAPI, port 8000）
│   │   ├── main.py                 # 应用入口，注册路由 + 自动建表
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings 配置
│   │   │   ├── database.py         # SQLAlchemy 异步引擎
│   │   │   ├── security.py         # JWT 生成/校验 + bcrypt 密码哈希
│   │   │   └── deps.py             # 依赖注入（get_current_user）
│   │   ├── models/                 # SQLAlchemy 数据模型
│   │   │   ├── user.py             # User
│   │   │   └── learning.py         # LearningPath, Module, PracticeSession, Progress
│   │   ├── routers/                # API 路由
│   │   │   ├── auth.py             # 认证路由
│   │   │   ├── learning.py         # 学习路径/模块路由
│   │   │   ├── practice.py         # 练习会话路由
│   │   │   ├── progress.py         # 进度路由
│   │   │   └── ai.py               # AI 服务代理路由
│   │   ├── requirements.txt        # Python 依赖
│   │   └── Dockerfile              # 容器构建文件
│   │
│   ├── ai/                         # AI 智能体服务（FastAPI, port 8100）
│   │   ├── main.py                 # 应用入口，7 个 agent 端点
│   │   ├── core/
│   │   │   ├── config.py           # AI 服务配置（OpenAI / LLM）
│   │   │   └── llm.py              # LLM 调用 + 降级机制
│   │   ├── agents/                 # 四个 AI 智能体
│   │   │   ├── tutor.py            # 导师（苏格拉底式引导）
│   │   │   ├── buddy.py            # 学习伙伴（协同对话）
│   │   │   ├── examiner.py         # 出题官（自适应出题 + 评估）
│   │   │   └── planner.py          # 规划师（学习路径 + 调整）
│   │   ├── prompts/                # 系统提示词模板
│   │   ├── tools/                  # 智能体工具（知识检索）
│   │   ├── requirements.txt        # Python 依赖（openai, langchain, langgraph）
│   │   └── Dockerfile
│   │
│   └── engine/                     # 学习引擎服务（FastAPI, port 8200）
│       ├── main.py                 # FSRS 知识追踪 + 间隔重复 + 时长估算
│       ├── requirements.txt        # Python 依赖（numpy, scipy）
│       └── Dockerfile
│
├── docker/
│   └── docker-compose.yml          # Docker Compose 编排配置
│
├── docs/                           # 项目文档
│   ├── architecture.md             # 系统架构设计
│   ├── api.md                      # API 端点文档
│   ├── ai-agents.md                # AI 智能体文档
│   ├── deployment.md               # 部署指南
│   └── development.md              # 本开发指南
│
├── package.json                    # 根 package.json（monorepo scripts）
├── pnpm-workspace.yaml             # pnpm workspace 配置
├── pnpm-lock.yaml                  # 锁定文件
├── README.md                       # 项目说明
├── CONTRIBUTING.md                 # 贡献指南
├── CHANGELOG.md                    # 变更日志
└── LICENSE                         # MIT 许可证
```

### 2.1 pnpm workspace 配置

根目录的 `pnpm-workspace.yaml` 定义了 monorepo 的工作空间：

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'services/*'
```

这意味着 `apps/`、`packages/`、`services/` 下的所有子目录都会被识别为 workspace 成员。前端通过包名 `@eduflow/ui` 和 `@eduflow/shared` 引用共享包。

### 2.2 服务端口一览

| 服务 | 端口 | 框架 | 说明 |
|------|------|------|------|
| Web | 3000 | Next.js 14 | 前端应用 |
| API | 8000 | FastAPI | 后端主服务（认证、学习、练习、进度） |
| AI | 8100 | FastAPI | AI 智能体服务 |
| Engine | 8200 | FastAPI | 学习引擎（FSRS 知识追踪） |
| PostgreSQL | 5432 | — | 生产数据库 |
| Redis | 6379 | — | 缓存 |

---

## 3. 本地开发步骤

### 3.1 克隆仓库

```bash
git clone https://github.com/your-org/eduflow.git
cd eduflow
```

### 3.2 安装前端依赖

在项目根目录执行：

```bash
pnpm install
```

该命令会根据 `pnpm-workspace.yaml` 安装 `apps/web`、`packages/shared`、`packages/ui` 下所有包的依赖。

根 `package.json` 提供了便捷脚本：

```bash
# 并行启动所有前端 workspace 成员的 dev 服务
pnpm dev

# 构建所有包
pnpm build

# 代码检查
pnpm lint

# 清理构建产物
pnpm clean
```

### 3.3 启动后端服务

后端三个服务需要分别安装 Python 依赖并启动。建议在各自目录下创建虚拟环境。

#### 3.3.1 启动 API 服务（端口 8000）

```bash
cd services/api

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（带热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问 API 文档：http://localhost:8000/docs（FastAPI 自动生成的 Swagger UI）

健康检查：http://localhost:8000/api/health

#### 3.3.2 启动 AI 服务（端口 8100）

```bash
cd services/ai

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8100
```

> 注意：AI 服务默认配置的 `API_PORT` 为 8001，但为与 API 服务的 `AI_SERVICE_URL`（默认 `http://localhost:8100`）保持一致，本地开发时请使用 `--port 8100`。

健康检查：http://localhost:8100/api/health

#### 3.3.3 启动 Engine 服务（端口 8200）

```bash
cd services/engine

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8200
```

健康检查：http://localhost:8200/api/health

### 3.4 启动前端（端口 3000）

```bash
cd apps/web
pnpm dev
```

前端默认运行在 http://localhost:3000。

### 3.5 完整启动顺序

为保证服务间调用正常，建议按以下顺序启动：

1. **API 服务**（端口 8000）— 核心后端，前端和 AI 代理都依赖它
2. **AI 服务**（端口 8100）— API 服务通过 httpx 调用 AI 服务
3. **Engine 服务**（端口 8200）— 独立运行，可按需启动
4. **前端**（端口 3000）— 最后启动，通过 rewrites 代理请求到 API

### 3.6 配置 OPENAI_API_KEY（可选）

AI 服务在未配置 `OPENAI_API_KEY` 时会自动启用降级模式，返回结构化的预设回复，不会报错。如需启用完整 AI 能力：

```bash
# 在 services/ai/ 目录下创建 .env 文件
cd services/ai
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

或通过环境变量启动：

```bash
OPENAI_API_KEY=sk-your-api-key-here uvicorn main:app --reload --port 8100
```

---

## 4. 数据库说明

### 4.1 开发环境：SQLite

开发环境默认使用 SQLite，无需额外安装数据库服务。

- **配置项**：`DATABASE_URL = sqlite+aiosqlite:///./eduflow.db`
- **驱动**：aiosqlite（异步 SQLite 驱动）
- **自动建表**：API 服务启动时通过 `lifespan` 钩子自动执行 `Base.metadata.create_all`，无需手动执行迁移
- **文件位置**：`services/api/eduflow.db`（首次启动后自动生成）

```python
# services/api/main.py 中的自动建表逻辑
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)
```

### 4.2 生产环境：PostgreSQL

生产环境使用 PostgreSQL，通过 Docker Compose 部署。

- **配置项**：`DATABASE_URL = postgresql+asyncpg://eduflow:eduflow@postgres:5432/eduflow`
- **驱动**：asyncpg（异步 PostgreSQL 驱动）
- **Docker 镜像**：`postgres:16-alpine`

切换到 PostgreSQL 只需修改环境变量：

```bash
# 在 services/api/.env 中设置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/eduflow
```

### 4.3 数据模型

数据模型定义在 `services/api/models/` 目录下，使用 SQLAlchemy 2.0 声明式语法：

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `users` | 用户信息（邮箱、用户名、密码哈希、头像、简介等） |
| `LearningPath` | `learning_paths` | 学习路径（标题、目标、难度、进度、状态） |
| `Module` | `modules` | 学习模块（关联路径，含内容 JSON、预计时长） |
| `PracticeSession` | `practice_sessions` | 练习会话（题目 JSON、答案 JSON、分数、状态） |
| `Progress` | `progress` | 学习进度（学习时长、完成率、薄弱点、强项） |

模型间通过外键关联，并设置了 `ondelete="CASCADE"` 级联删除。SQLite 环境下通过 `PRAGMA foreign_keys=ON` 确保外键约束生效。

### 4.4 数据库迁移

项目依赖中包含 Alembic（`alembic==1.13.0`），可用于管理数据库迁移。开发环境下由于自动建表，通常无需手动迁移。生产环境可按需配置 Alembic 迁移脚本。

---

## 5. 前端 API 代理配置

### 5.1 Next.js rewrites 代理

前端通过 Next.js 的 `rewrites` 功能将 `/api/*` 请求代理到后端 API 服务，避免开发环境的跨域问题。

配置文件位于 `apps/web/next.config.js`：

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@eduflow/ui', '@eduflow/shared'],
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }
    ]
  }
}

module.exports = nextConfig
```

### 5.2 代理工作原理

- 前端代码中所有 API 请求路径以 `/api` 开头（如 `/api/auth/login`）
- Next.js dev server 拦截这些请求，通过 rewrites 转发到 `http://localhost:8000/api/auth/login`
- 后端 API 服务的路由也统一以 `/api` 为前缀（如 `@app.post("/api/auth/login")`）
- 因此前端无需关心后端实际地址，只需请求相对路径 `/api/*`

### 5.3 前端 API 客户端

前端 API 客户端位于 `apps/web/src/lib/api.ts`，核心特性：

- **统一请求方法**：`request<T>()` 函数自动附加 `Authorization: Bearer <token>` 头
- **Token 存储**：JWT token 和用户信息存储在 `localStorage`
- **错误处理**：封装 `ApiError` 类，统一处理 HTTP 错误
- **模块化 API**：按功能划分 `authAPI`、`learningAPI`、`practiceAPI`、`progressAPI`、`aiAPI`

```typescript
// 所有请求通过相对路径 /api/* 发出，由 Next.js rewrites 代理
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(`/api${path}`, { ...options, headers })
  // ... 错误处理与响应解析
}
```

### 5.4 直接访问 AI 服务

部分场景下前端可直接访问 AI 服务（如需要绕过 API 代理时），通过环境变量配置：

```bash
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8100
```

常量定义在 `apps/web/src/lib/constants.ts` 中：

```typescript
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const AI_API_BASE = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8100'
```

---

## 6. 代码规范

### 6.1 Python 代码规范

后端三个服务（api、ai、engine）遵循以下规范：

#### 格式化与检查工具

| 工具 | 用途 | 配置 |
|------|------|------|
| Black | 代码格式化 | `--line-length=88` |
| Ruff | Lint 检查 | 遵循 PEP 8 |
| isort | 导入排序 | — |

```bash
# 在各服务目录下执行
cd services/api

# 格式化
black . --line-length=88

# Lint 检查（自动修复）
ruff check . --fix

# 导入排序
isort .
```

#### 代码风格要点

- 使用类型注解（Type Hints），FastAPI / Pydantic 依赖类型推断
- 异步优先：数据库操作使用 `async/await`，配合 SQLAlchemy 2.0 异步引擎
- 配置管理使用 `pydantic-settings` 的 `BaseSettings`，支持环境变量与 `.env` 文件
- 路由函数使用 `async def`，依赖注入通过 `Depends()` 实现

#### Python 版本

所有后端服务的 Dockerfile 基于 `python:3.12-slim`，要求 Python 3.12+。

### 6.2 TypeScript / 前端代码规范

#### 格式化与检查工具

| 工具 | 用途 |
|------|------|
| ESLint | 代码质量检查（`next lint`） |
| TypeScript | 静态类型检查 |
| Tailwind CSS | 原子化 CSS 样式 |

```bash
cd apps/web

# ESLint 检查
pnpm lint

# TypeScript 类型检查
pnpm exec tsc --noEmit

# 构建检查（会同时执行类型检查）
pnpm build
```

#### 代码风格要点

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- API 调用统一通过 `src/lib/api.ts` 中的模块化 API 对象
- 共享类型定义在 `packages/shared/types/` 中，通过 `@eduflow/shared` 引用
- UI 组件优先使用 `@eduflow/ui` 中的基础组件

### 6.3 Git 提交规范

项目使用 Conventional Commits 规范：

```bash
# 功能新增
git commit -m "feat(api): 添加学习路径删除接口"

# Bug 修复
git commit -m "fix(web): 修复登录页 token 解析错误"

# 文档更新
git commit -m "docs: 更新开发指南中的数据库说明"

# 重构
git commit -m "refactor(ai): 重构 LLM 降级回复逻辑"

# 样式调整
git commit -m "style(web): 调整导航栏间距"
```

提交前缀参考：`feat` / `fix` / `docs` / `refactor` / `style` / `test` / `chore` / `perf`。

---

## 7. 环境变量配置

### 7.1 API 服务（services/api）

配置文件：`services/api/core/config.py`，支持 `.env` 文件。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | `EduFlow API` | 应用名称 |
| `VERSION` | `0.1.0` | 版本号 |
| `DEBUG` | `False` | 调试模式（开启 SQL 日志） |
| `DATABASE_URL` | `sqlite+aiosqlite:///./eduflow.db` | 数据库连接串 |
| `SECRET_KEY` | `eduflow-secret-key-change-in-production` | JWT 签名密钥 |
| `ALGORITHM` | `HS256` | JWT 加密算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080`（7 天） | Token 有效期（分钟） |
| `AI_SERVICE_URL` | `http://localhost:8100` | AI 服务地址 |
| `PASS_SCORE_THRESHOLD` | `60` | 练习及格分 |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | 跨域来源 |

### 7.2 AI 服务（services/ai）

配置文件：`services/ai/core/config.py`，支持 `.env` 文件。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | `EduFlow AI Service` | 应用名称 |
| `VERSION` | `0.1.0` | 版本号 |
| `DEBUG` | `False` | 调试模式 |
| `OPENAI_API_KEY` | `None` | OpenAI API 密钥（为空时启用降级模式） |
| `LLM_PROVIDER` | `openai` | LLM 提供方 |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名称 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度 |
| `MAX_TOKENS` | `4096` | 单次响应最大 token |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `API_PORT` | `8001` | 服务端口（本地建议用 `--port 8100` 覆盖） |

### 7.3 Engine 服务（services/engine）

Engine 服务无额外环境变量配置，默认监听 8200 端口。

### 7.4 前端（apps/web）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API 服务地址 |
| `NEXT_PUBLIC_AI_API_URL` | `http://localhost:8100` | AI 服务地址 |

前端环境变量需以 `NEXT_PUBLIC_` 前缀开头才能在浏览器端访问。可在 `apps/web/.env.local` 中配置。

---

## 8. 调试技巧

### 8.1 后端调试

#### 查看数据库 SQL 日志

在 `services/api/.env` 中设置：

```bash
DEBUG=True
```

这会启用 SQLAlchemy 的 SQL echo，在终端打印所有 SQL 查询。

#### 使用断点调试

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 Python 3.7+ 内置
breakpoint()
```

#### FastAPI 自动文档

每个后端服务启动后都提供交互式 API 文档：

- API 服务 Swagger UI：http://localhost:8000/docs
- API 服务 ReDoc：http://localhost:8000/redoc
- AI 服务 Swagger UI：http://localhost:8100/docs
- Engine 服务 Swagger UI：http://localhost:8200/docs

### 8.2 前端调试

#### 查看代理请求

前端通过 Next.js rewrites 代理的请求会在终端 dev server 日志中显示转发记录。

#### React Developer Tools

推荐安装浏览器扩展 React Developer Tools，用于检查组件状态和 props。

#### 网络请求

前端 API 客户端在请求失败时会抛出 `ApiError`，包含 `status` 和 `detail` 字段，方便定位问题：

```typescript
try {
  await authAPI.login(email, password)
} catch (err) {
  if (err instanceof ApiError) {
    console.error(`HTTP ${err.status}:`, err.detail)
  }
}
```

### 8.3 数据库调试（SQLite）

```bash
# 使用 sqlite3 命令行工具查看数据
cd services/api
sqlite3 eduflow.db

# 查看所有表
.tables

# 查看用户表结构
.schema users

# 查询数据
SELECT id, email, username FROM users;
```

### 8.4 健康检查端点

所有服务均提供健康检查接口，可用于验证服务是否正常运行：

```bash
curl http://localhost:8000/api/health    # API 服务
curl http://localhost:8100/api/health    # AI 服务（含 LLM 状态）
curl http://localhost:8200/api/health    # Engine 服务
```

AI 服务的健康检查会返回 `llm_available` 字段，指示是否配置了 OpenAI API Key：

```json
{
  "status": "ok",
  "service": "EduFlow AI Service",
  "version": "0.1.0",
  "llm_available": false,
  "agents": [...]
}
```

---

## 9. 常见问题

### 9.1 前端请求返回 404

**原因**：Next.js rewrites 代理未生效，或后端 API 服务未启动。

**解决**：
1. 确认 API 服务已在 8000 端口启动：`curl http://localhost:8000/api/health`
2. 确认 `next.config.js` 中 rewrites 配置正确
3. 确认前端请求路径以 `/api` 开头

### 9.2 AI 服务调用失败

**原因**：AI 服务未启动，或端口不匹配。

**解决**：
1. 确认 AI 服务在 8100 端口启动：`curl http://localhost:8100/api/health`
2. 确认 API 服务的 `AI_SERVICE_URL` 指向 `http://localhost:8100`
3. AI 服务未配置 `OPENAI_API_KEY` 不会报错，会返回降级回复

### 9.3 数据库表未创建

**原因**：API 服务通过 `lifespan` 钩子自动建表，如果服务未完整启动则表不会创建。

**解决**：
1. 确认 API 服务已成功启动（终端无报错）
2. 查看 `services/api/` 目录下是否生成了 `eduflow.db` 文件
3. 设置 `DEBUG=True` 查看 SQL 日志，确认建表语句执行

### 9.4 Python 依赖安装失败

**原因**：Python 版本过低或缺少编译工具。

**解决**：
1. 确认 Python 版本 >= 3.12：`python --version`
2. 升级 pip：`pip install --upgrade pip`
3. 对于 `numpy` / `scipy` 安装失败（Engine 服务），确保系统已安装编译工具

### 9.5 pnpm install 报错

**原因**：Node.js 版本过低。

**解决**：
1. 确认 Node.js >= 18：`node --version`
2. 根目录 `package.json` 中 `engines.node` 要求 `>=18.0.0`
3. 如使用 nvm：`nvm use 20`

### 9.6 跨域错误（CORS）

**原因**：API 服务默认允许所有来源（`allow_origins=["*"]`），但配置了 `allow_credentials=True`。

**解决**：开发环境通常无此问题。如遇跨域，检查 `services/api/core/config.py` 中的 `CORS_ORIGINS` 配置，并确保前端通过 rewrites 代理而非直接跨域请求。

---

> 如遇其他问题，请查阅 [CONTRIBUTING.md](../CONTRIBUTING.md) 或在项目仓库提交 Issue。
