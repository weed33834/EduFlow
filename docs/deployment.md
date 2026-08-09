# 部署文档

> 文档版本: v2.0 | 最后更新: 2026-08-09

---

## 目录

1. [部署方式概览](#1-部署方式概览)
2. [Docker Compose 部署](#2-docker-compose-部署)
3. [手动部署](#3-手动部署)
4. [端口说明](#4-端口说明)
5. [环境变量配置](#5-环境变量配置)
6. [健康检查](#6-健康检查)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 部署方式概览

EduFlow 畅学支持两种部署方式：

| 部署方式 | 适用场景 | 复杂度 | 推荐用途 |
|----------|----------|--------|----------|
| Docker Compose | 一键启动全部服务 | 低 | 本地开发、测试、生产部署 |
| 手动部署 | 灵活控制各服务 | 中 | 本地开发、调试、自定义环境 |

---

## 2. Docker Compose 部署

### 2.1 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 2 GB 可用内存

### 2.2 服务架构

Docker Compose 配置文件位于 `docker/docker-compose.yml`，包含以下六个服务：

| 服务 | 镜像/构建 | 端口 | 依赖 |
|------|-----------|------|------|
| postgres | postgres:16-alpine | 5432 | - |
| redis | redis:7-alpine | 6379 | - |
| api | 构建（services/api） | 8000 | postgres, redis |
| ai-service | 构建（services/ai） | 8100 | redis |
| engine | 构建（services/engine） | 8200 | - |
| web | 构建（apps/web） | 3000 | api |

### 2.3 一键启动

```bash
# 1. 进入 docker 目录
cd docker

# 2. （可选）配置 OPENAI_API_KEY 启用完整 AI 能力
export OPENAI_API_KEY="sk-your-api-key"

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

启动后，API 服务会在启动时自动创建数据库表（通过 `Base.metadata.create_all`），无需手动执行迁移。

### 2.4 完整 docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: eduflow
      POSTGRES_PASSWORD: eduflow
      POSTGRES_DB: eduflow
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eduflow"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ../services/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://eduflow:eduflow@postgres:5432/eduflow
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      AI_SERVICE_URL: http://ai-service:8100
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  ai-service:
    build:
      context: ../services/ai
      dockerfile: Dockerfile
    ports:
      - "8100:8100"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  engine:
    build:
      context: ../services/engine
      dockerfile: Dockerfile
    ports:
      - "8200:8200"

  web:
    build:
      context: ../apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
      NEXT_PUBLIC_AI_API_URL: http://ai-service:8100
    depends_on:
      - api

volumes:
  pgdata:
```

### 2.5 关键配置说明

- **postgres**：使用 `postgres:16-alpine` 轻量镜像，用户名/密码/数据库名均为 `eduflow`，数据持久化到 `pgdata` 卷。配置了 `pg_isready` 健康检查。
- **redis**：使用 `redis:7-alpine`，配置了 `redis-cli ping` 健康检查。
- **api**：通过 `DATABASE_URL` 连接 PostgreSQL（`postgresql+asyncpg`），通过 `AI_SERVICE_URL` 指向 AI 服务。依赖 postgres 和 redis 的健康检查通过后才启动。
- **ai-service**：依赖 redis 健康检查。`OPENAI_API_KEY` 为空时自动启用降级模式。
- **engine**：无外部依赖，独立运行。
- **web**：依赖 api 服务，通过 `NEXT_PUBLIC_API_URL` 和 `NEXT_PUBLIC_AI_API_URL` 配置后端地址。

### 2.6 常用 Docker 命令

```bash
# 启动所有服务（后台）
docker-compose up -d

# 启动并重新构建镜像
docker-compose up -d --build

# 仅启动部分服务
docker-compose up -d postgres redis api
docker-compose up -d ai-service
docker-compose up -d engine

# 查看服务状态
docker-compose ps

# 查看指定服务日志
docker-compose logs -f api
docker-compose logs -f ai-service
docker-compose logs -f web

# 重启指定服务
docker-compose restart api

# 停止所有服务
docker-compose down

# 停止并删除数据卷（清除数据库数据）
docker-compose down -v
```

### 2.7 访问服务

启动完成后，可通过以下地址访问各服务：

| 服务 | 访问地址 |
|------|----------|
| Web 前端 | http://localhost:3000 |
| API 服务 | http://localhost:8000 |
| AI 服务 | http://localhost:8100 |
| Engine 服务 | http://localhost:8200 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 3. 手动部署

适用于本地开发或需要单独调试某个服务的场景。

### 3.1 前置要求

- Python >= 3.12
- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Redis >= 7.0（可选，AI 服务和 API 服务可配置）
- PostgreSQL >= 16（生产环境，开发可用 SQLite）

### 3.2 启动 API 服务

```bash
# 1. 进入 API 服务目录
cd services/api

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置环境变量（可选，开发默认使用 SQLite）
# 创建 .env 文件或通过环境变量配置
# DATABASE_URL=sqlite+aiosqlite:///./eduflow.db
# AI_SERVICE_URL=http://localhost:8100
# SECRET_KEY=your-secret-key

# 4. 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 服务启动后会自动在当前目录创建 `eduflow.db`（SQLite）并建表。

### 3.3 启动 AI 服务

```bash
# 1. 进入 AI 服务目录
cd services/ai

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量（可选）
# OPENAI_API_KEY=sk-your-api-key  # 配置后启用完整 AI 能力
# 不配置时自动启用降级模式

# 4. 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8100
```

> 注意：AI 服务的 `API_PORT` 配置默认值为 8001，但实际部署时通过 uvicorn 的 `--port` 参数指定为 8100。`main.py` 中的 `__main__` 入口使用 `settings.API_PORT`，请确保端口一致。

### 3.4 启动 Engine 服务

```bash
# 1. 进入 Engine 服务目录
cd services/engine

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8200
```

Engine 服务无外部依赖，可直接启动。

### 3.5 启动 Web 前端

```bash
# 1. 进入项目根目录
cd /path/to/eduflow

# 2. 安装依赖（pnpm workspace 会同时安装所有包）
pnpm install

# 3. 启动前端开发服务器
cd apps/web
pnpm dev
```

前端开发服务器启动在 http://localhost:3000，通过 Next.js rewrites 自动将 `/api/*` 请求代理到 http://localhost:8000/api/*。

### 3.6 启动顺序建议

手动部署时建议按以下顺序启动：

1. Redis（如需要）
2. AI 服务（端口 8100）
3. Engine 服务（端口 8200）
4. API 服务（端口 8000）— 依赖 AI 服务
5. Web 前端（端口 3000）— 依赖 API 服务

---

## 4. 端口说明

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Web 前端 | 3000 | HTTP | Next.js 开发/生产服务器 |
| API 服务 | 8000 | HTTP | FastAPI 主业务服务 |
| AI 服务 | 8100 | HTTP | FastAPI AI 智能体服务 |
| Engine 服务 | 8200 | HTTP | FastAPI 学习引擎服务 |
| PostgreSQL | 5432 | TCP | 数据库（生产环境） |
| Redis | 6379 | TCP | 缓存 |

确保以上端口未被占用。如需修改端口，请同时更新对应服务的启动参数和配置。

---

## 5. 环境变量配置

### 5.1 API 服务环境变量

定义在 `services/api/core/config.py`，通过 pydantic-settings 加载，支持 `.env` 文件。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | `"EduFlow API"` | 应用名称 |
| `VERSION` | `"0.1.0"` | 应用版本 |
| `DEBUG` | `False` | 调试模式（开启 SQL 日志） |
| `DATABASE_URL` | `sqlite+aiosqlite:///./eduflow.db` | 数据库连接字符串 |
| `SECRET_KEY` | `"eduflow-secret-key-change-in-production"` | JWT 加密密钥（生产环境必须修改） |
| `ALGORITHM` | `"HS256"` | JWT 签名算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 天) | Token 有效期（分钟） |
| `AI_SERVICE_URL` | `"http://localhost:8100"` | AI 服务地址 |
| `PASS_SCORE_THRESHOLD` | `60` | 练习及格分数线 |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | 允许的跨域来源 |

**数据库连接字符串示例**：

- 开发（SQLite）：`sqlite+aiosqlite:///./eduflow.db`
- 生产（PostgreSQL）：`postgresql+asyncpg://eduflow:eduflow@localhost:5432/eduflow`

### 5.2 AI 服务环境变量

定义在 `services/ai/core/config.py`。

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | `"EduFlow AI Service"` | 应用名称 |
| `VERSION` | `"0.1.0"` | 应用版本 |
| `DEBUG` | `False` | 调试模式 |
| `OPENAI_API_KEY` | `None` | OpenAI API Key，未配置时启用降级 |
| `LLM_PROVIDER` | `"openai"` | LLM 提供商 |
| `LLM_MODEL` | `"gpt-4o-mini"` | 使用的模型 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度 |
| `MAX_TOKENS` | `4096` | 最大生成 token 数 |
| `REDIS_URL` | `"redis://localhost:6379/0"` | Redis 连接地址 |
| `API_PORT` | `8001` | 配置中的端口（实际启动通过 uvicorn 指定 8100） |

### 5.3 Web 前端环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API 服务地址（constants.ts 中定义） |
| `NEXT_PUBLIC_AI_API_URL` | `http://localhost:8100` | AI 服务地址（constants.ts 中定义） |

> 注意：前端实际请求通过 Next.js rewrites 代理到 `http://localhost:8000/api/*`，`NEXT_PUBLIC_API_URL` 主要用于 constants.ts 中的常量定义。在 Docker 部署中，web 容器内使用服务名 `http://api:8000`。

### 5.4 Docker Compose 环境变量

Docker 部署时可通过宿主机环境变量传入：

```bash
# 设置 OpenAI API Key（可选，不设置则 AI 服务降级运行）
export OPENAI_API_KEY="sk-your-api-key"

# 启动
docker-compose up -d
```

在 `docker-compose.yml` 中，`OPENAI_API_KEY` 通过 `${OPENAI_API_KEY:-}` 引用，未设置时为空字符串，AI 服务会自动降级。

---

## 6. 健康检查

### 6.1 健康检查端点

每个后端服务都提供健康检查端点：

| 服务 | 端点 | 端口 |
|------|------|------|
| API 服务 | `GET http://localhost:8000/api/health` | 8000 |
| AI 服务 | `GET http://localhost:8100/api/health` | 8100 |
| Engine 服务 | `GET http://localhost:8200/api/health` | 8200 |

### 6.2 健康检查响应

**API 服务**：

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "version": "0.1.0",
  "service": "EduFlow API"
}
```

**AI 服务**：

```bash
curl http://localhost:8100/api/health
```

```json
{
  "status": "ok",
  "service": "EduFlow AI Service",
  "version": "0.1.0",
  "timestamp": "2026-08-09T12:00:00+00:00",
  "llm_available": false,
  "config": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "api_port": 8001,
    "debug": false
  },
  "agents": [...],
  "endpoints": [...]
}
```

AI 服务的健康检查额外返回 `llm_available` 字段，可用于判断 AI 是否处于降级模式。

**Engine 服务**：

```bash
curl http://localhost:8200/api/health
```

```json
{
  "status": "ok",
  "service": "EduFlow Engine"
}
```

### 6.3 Docker 健康检查

Docker Compose 中为 PostgreSQL 和 Redis 配置了健康检查：

- **PostgreSQL**：`pg_isready -U eduflow`，间隔 5 秒，重试 5 次
- **Redis**：`redis-cli ping`，间隔 5 秒，重试 5 次

API 服务和 AI 服务通过 `depends_on.condition: service_healthy` 确保依赖的基础设施就绪后再启动。

### 6.4 验证部署

```bash
# 验证 API 服务
curl http://localhost:8000/api/health

# 验证 AI 服务（检查 llm_available 判断是否降级）
curl http://localhost:8100/api/health | python -m json.tool

# 验证 Engine 服务
curl http://localhost:8200/api/health

# 验证前端可访问
curl http://localhost:3000

# 验证前端 API 代理（需先注册用户获取 token）
curl http://localhost:3000/api/health
```

---

## 7. 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|----------|
| API 服务启动失败 | 端口 8000 被占用 | 检查端口占用：`lsof -i :8000`，释放或更换端口 |
| API 服务无法连接 AI 服务 | `AI_SERVICE_URL` 配置错误 | 检查 `AI_SERVICE_URL` 是否指向正确的 AI 服务地址 |
| AI 接口返回 503 | AI 服务未启动或不可达 | 确认 AI 服务（端口 8100）已启动且正常运行 |
| AI 接口返回 504 | AI 服务响应超时（>60s） | 检查 OpenAI API Key 是否有效，网络是否通畅 |
| AI 功能降级运行 | 未配置 `OPENAI_API_KEY` | 设置环境变量 `OPENAI_API_KEY`，重启 AI 服务 |
| 数据库连接失败 | `DATABASE_URL` 配置错误 | 开发环境使用 SQLite，生产环境检查 PostgreSQL 连接字符串 |
| 前端 API 请求 404 | Next.js rewrites 未生效 | 确认 API 服务（端口 8000）已启动，检查 `next.config.js` 配置 |
| 前端登录失败 | JWT `SECRET_KEY` 不一致 | 确认 API 服务的 `SECRET_KEY` 配置正确 |
| PostgreSQL 健康检查失败 | 数据库未就绪 | 等待启动完成，检查 `docker-compose logs postgres` |
| Docker 构建失败 | Dockerfile 上下文路径错误 | 确认从 `docker/` 目录执行 `docker-compose`，构建上下文为 `../services/*` |

### 日志查看

```bash
# Docker 环境
docker-compose logs -f api
docker-compose logs -f ai-service
docker-compose logs -f engine
docker-compose logs -f web

# 手动部署（uvicorn 终端输出）
# 开发模式下日志直接输出到终端
# 开启 SQL 日志：设置 DEBUG=True
```

### 数据库管理

```bash
# 连接 PostgreSQL（Docker 环境）
docker-compose exec postgres psql -U eduflow -d eduflow

# 连接 PostgreSQL（手动部署）
psql -U eduflow -d eduflow -h localhost -p 5432

# 开发环境 SQLite 文件位于 services/api/eduflow.db
# 可使用 sqlite3 命令行工具或 DB Browser for SQLite 查看
```
