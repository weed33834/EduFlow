# EduFlow 畅学

> AI 驱动的学生自学平台 — 让学习自然流畅，让知识触手可及。

EduFlow（畅学）是一个基于大模型构建的 AI 驱动学生自学平台。区别于传统的教学管理系统（LMS）或 AI 助教工具，EduFlow 将**学生**置于学习的中心，AI 智能体作为辅助角色，按需提供辅导、练习、出题和进度追踪。

## 项目结构

```
EduFlow/
├── apps/web/           # Next.js 前端应用
├── services/
│   ├── api/            # FastAPI 后端服务
│   ├── ai/             # AI 智能体服务
│   └── engine/         # 学习引擎（知识追踪 + 间隔重复）
├── packages/
│   ├── shared/         # 共享类型定义和工具
│   └── ui/             # UI 组件库
├── docker/             # Docker 配置
└── docs/               # 文档
```

## 技术栈

### 前端（apps/web）

- **框架**：Next.js 14（React 18）
- **语言**：TypeScript 5
- **样式方案**：Tailwind CSS 3
- **图标库**：lucide-react
- **工具库**：clsx、tailwind-merge

### 后端（services/api）

- **Web 框架**：FastAPI
- **ORM**：SQLAlchemy 2.0（异步）
- **数据库**：SQLite（开发环境，aiosqlite 驱动）/ PostgreSQL（生产环境）
- **数据库迁移**：Alembic
- **认证**：JWT（python-jose）+ 密码哈希（bcrypt）
- **HTTP 客户端**：httpx

### AI 服务（services/ai）

- **Web 框架**：FastAPI
- **大模型接入**：OpenAI 兼容 API（openai SDK）
- **智能体编排**：LangChain + LangGraph
- **降级机制**：在 LLM 不可用时返回兜底响应，保证服务可用

### 学习引擎（services/engine）

- **Web 框架**：FastAPI
- **核心算法**：FSRS 知识追踪算法（间隔重复复习计算、学习时长估算）
- **数值计算**：numpy、scipy

## 快速开始

### 服务端口一览

| 服务 | 端口 | 说明 |
|------|------|------|
| API | 8000 | 后端服务（认证、学习路径、练习、进度） |
| AI | 8100 | AI 智能体服务 |
| Engine | 8200 | 学习引擎（FSRS 知识追踪） |
| Web | 3000 | 前端应用 |

### 方式一：Docker 一键启动

```bash
cd docker && docker-compose up -d
```

该方式会启动 API、AI、Engine、Web 四个服务，以及 PostgreSQL 和 Redis。

### 方式二：手动启动

```bash
# 1. 安装依赖
pnpm install

# 2. 启动 API 服务（端口 8000）
cd services/api && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 3. 启动 AI 服务（端口 8100）
cd services/ai && pip install -r requirements.txt && uvicorn main:app --reload --port 8100

# 4. 启动 Engine 服务（端口 8200）
cd services/engine && pip install -r requirements.txt && uvicorn main:app --reload --port 8200

# 5. 启动前端（端口 3000）
cd apps/web && pnpm dev
```

## 环境变量配置

各服务支持通过环境变量或项目根目录的 `.env` 文件进行配置。以下为关键配置项。

### API 服务（services/api）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./eduflow.db` | 数据库连接串（生产建议使用 PostgreSQL） |
| `SECRET_KEY` | `eduflow-secret-key-change-in-production` | JWT 签名密钥，生产环境必须修改 |
| `ALGORITHM` | `HS256` | JWT 加密算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080`（7 天） | 访问令牌有效期（分钟） |
| `AI_SERVICE_URL` | `http://localhost:8100` | AI 服务地址 |
| `PASS_SCORE_THRESHOLD` | `60` | 练习及格分数阈值 |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | 允许跨域的来源 |
| `OPENAI_API_KEY` | — | OpenAI API 密钥（容器部署时透传） |

### AI 服务（services/ai）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | — | OpenAI API 密钥 |
| `LLM_PROVIDER` | `openai` | LLM 提供方 |
| `LLM_MODEL` | `gpt-4o-mini` | 使用的模型名称 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度 |
| `MAX_TOKENS` | `4096` | 单次响应最大 token 数 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |

### Engine 服务（services/engine）

Engine 服务默认监听 `8200` 端口，无额外必填环境变量。

### 前端（apps/web）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API 服务地址 |
| `NEXT_PUBLIC_AI_API_URL` | `http://localhost:8100` | AI 服务地址 |

> 提示：Docker 部署时，上述变量已通过 `docker/docker-compose.yml` 预配置，容器间使用服务名互相访问。

## 核心功能

- **学习管理** — 学习目标设定、智能路径规划、间隔重复复习
- **评估与诊断** — 入学能力评估、薄弱点分析、学习周报
- **内容与资源** — 内容市场、资源推荐、笔记系统
- **社交与协作** — 学习社区、伙伴匹配、小组协作
- **激励与游戏化** — 成就系统、积分排行榜、挑战赛
- **工具与体验** — 番茄钟、学习日历、浏览器插件

## AI 智能体

- **AI 导师 Tutor** — 按需辅导答疑，苏格拉底式教学
- **AI 伴学 Buddy** — 协同练习对话，像同学一样讨论
- **AI 出题者 Examiner** — 自适应出题，即时反馈解析
- **AI 规划师 Planner** — 个性化学习路径规划

## 文档

更详细的文档请参阅 `docs/` 目录：

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 系统架构、分层设计、数据流 |
| [部署文档](docs/deployment.md) | Docker 部署、手动部署、环境变量 |
| [API 文档](docs/api.md) | 各服务 API 端点说明 |
| [开发指南](docs/development.md) | 本地开发、代码规范、测试 |
| [AI 智能体](docs/ai-agents.md) | 四个智能体的功能和工作流程 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目贡献 |
| [变更日志](CHANGELOG.md) | 版本发布历史 |

## 许可

MIT License
