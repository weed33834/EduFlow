# EduFlow Agent

> AI 编程学习 Agent — 会教编程、会出题、会判题、会排复习的 AI 学习伙伴。

不是平台，不是工具箱，不是 LMS。就是一个 Agent。

## 项目结构

```
EduFlow/
├── backend/              # FastAPI 后端（单服务）
│   ├── app/
│   │   ├── main.py       # 入口
│   │   ├── config.py     # 配置
│   │   ├── database.py   # 数据库
│   │   ├── security.py   # JWT + bcrypt
│   │   ├── models.py     # 数据模型（SQLAlchemy 2.0 Mapped）
│   │   ├── agents/       # LangGraph 状态机
│   │   │   ├── state.py  # AgentState 定义
│   │   │   ├── nodes.py  # 6 节点：understand→recall→plan→teach/quiz→respond→reflect
│   │   │   └── graph.py  # StateGraph 构建
│   │   ├── tools/        # 工具层
│   │   │   └── llm.py    # LiteLLM 封装
│   │   └── routers/     # API 路由
│   │       ├── auth.py   # 认证
│   │       ├── chat.py   # SSE 流式对话
│   │       ├── sessions.py # 会话管理
│   │       └── profile.py # 学生画像
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # Next.js 14 前端
│   └── src/
│       ├── app/
│       │   ├── page.tsx  # 落地页
│       │   ├── login/    # 登录
│       │   ├── register/ # 注册
│       │   └── chat/     # 主界面（单页对话）
│       ├── contexts/     # AuthContext
│       ├── components/   # RouteGuard
│       └── lib/          # API 客户端 + 工具
│
├── docker-compose.yml     # PostgreSQL + Redis + 后端 + 前端
└── REBUILD-PLAN.md       # 重构方案文档
```

## 快速开始

### Docker

```bash
# 克隆
git clone https://github.com/weed33834/EduFlow.git
cd EduFlow

# 启动
LITELLM_API_KEY=your-key docker compose up -d

# 访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000/api/health
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
pnpm install
pnpm dev
```

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js 14 | 单页对话界面 |
| 后端 | FastAPI | 单服务（合并旧三微服务） |
| Agent | LangGraph | 6 节点状态机 |
| LLM | LiteLLM | 统一接口，支持 100+ 模型 |
| 数据库 | PostgreSQL 16 | SQLAlchemy 2.0 Mapped |
| 缓存 | Redis 7 | 预留 |

## 开发路线

| 版本 | 目标 | 状态 |
|---|---|---|
| v0.1.0 | 最小对话闭环（教概念+出题+历史保存） | ✅ 已完成 |
| v0.2.0 | 代码沙箱（E2B 执行+反馈） | 📋 计划 |
| v0.3.0 | FSRS 间隔重复 | 📋 计划 |
| v0.4.0 | 知识库 RAG（Qdrant） | 📋 计划 |
| v0.5.0 | 长期记忆 | 📋 计划 |
| v0.6.0 | 前端打磨 | 📋 计划 |

## License

MIT
