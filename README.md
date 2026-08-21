# EduFlow Agent

> AI 编程学习 Agent — 会教编程、会出题、会判题、会运行代码、会排复习的 AI 学习伙伴。

不是平台，不是工具箱，不是 LMS。就是一个 Agent。

## 项目结构

```
EduFlow/
├── backend/                  # FastAPI 后端（单服务）
│   ├── app/
│   │   ├── main.py           # 入口
│   │   ├── config.py          # 配置（LLM/E2B/Qdrant/Mem0）
│   │   ├── database.py        # 数据库引擎
│   │   ├── security.py        # JWT + bcrypt
│   │   ├── models.py          # 数据模型（User/Session/Message/ReviewItem）
│   │   ├── agents/            # LangGraph 状态机
│   │   │   ├── state.py       # AgentState 定义
│   │   │   ├── nodes.py       # 9 节点：understand→recall→plan→[teach|quiz|code|review|respond]→reflect
│   │   │   └── graph.py       # StateGraph + MemorySaver Checkpointer
│   │   ├── tools/            # 工具层（全部用开源项目）
│   │   │   ├── llm.py         # LiteLLM 封装 + JSON mode
│   │   │   ├── sandbox.py     # E2B 代码沙箱
│   │   │   ├── knowledge.py   # Qdrant + LiteLLM embedding RAG
│   │   │   └── memory.py      # Mem0 长期记忆
│   │   └── routers/          # API 路由
│   │       ├── auth.py        # 认证（注册/登录/获取用户）
│   │       ├── chat.py        # SSE 流式对话（Agent 核心）
│   │       ├── sessions.py    # 会话管理
│   │       └── profile.py     # 学生画像
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # Next.js 14 前端
│   └── src/
│       ├── app/
│       │   ├── page.tsx       # 落地页
│       │   ├── login/        # 登录
│       │   ├── register/     # 注册
│       │   └── chat/         # 主界面（单页对话 + 流式 + 代码结果）
│       ├── contexts/         # AuthContext
│       ├── components/       # RouteGuard
│       └── lib/              # API 客户端 + 工具
├── docker-compose.yml         # PostgreSQL + Qdrant + 后端 + 前端
├── .env.example               # 环境变量模板
└── REBUILD-PLAN.md            # 重构方案文档
```

## 快速开始

### Docker

```bash
git clone https://github.com/weed33834/EduFlow.git
cd EduFlow
cp .env.example .env
# 编辑 .env，填入 LITELLM_API_KEY
LITELLM_API_KEY=your-key docker compose up -d --build

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
npm install --legacy-peer-deps
npm run dev
```

## 技术栈（全部开源项目，不重复造轮子）

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js 14 + Tailwind CSS | 单页对话界面，支持流式显示 |
| 后端 | FastAPI | 单服务 |
| Agent 编排 | LangGraph | 9 节点状态机 + MemorySaver Checkpointer |
| LLM 接口 | LiteLLM | 统一 100+ 模型，原生 JSON mode |
| 代码沙箱 | E2B | 开源云端沙箱，`pip install e2b` |
| 知识库 RAG | Qdrant + LiteLLM embedding | 开源向量数据库，不装 LlamaIndex（太重） |
| 长期记忆 | Mem0 | 开源记忆层，`pip install mem0ai` |
| 间隔重复 | fsrs | 开源 FSRS-6.3 算法，`pip install fsrs` |
| 数据库 | PostgreSQL 16 | SQLAlchemy 2.0 Mapped |
| 认证 | python-jose + passlib | JWT + bcrypt |

## Agent 状态机

```
understand → recall → plan → [teach | quiz | code | review | respond] → respond → reflect → END
```

| 节点 | 功能 |
|---|---|
| understand | 意图分类（learn_concept/practice/run_code/ask_question/chitchat） |
| recall | Mem0 检索长期记忆 + Qdrant 检索知识库文档 |
| plan | 检查 FSRS 到期复习项 → review；否则按意图路由 |
| teach | 讲解概念，带入知识库参考文档 + 学生记忆 |
| quiz | 出题（LiteLLM JSON mode 保证结构化输出） |
| code | E2B 沙箱执行学生代码 → LLM 根据输出给反馈 |
| review | FSRS 间隔重复，生成复习内容 |
| respond | 组织回复，加入对话历史（Checkpointer 自动持久化） |
| reflect | Mem0 自动保存对话记忆 |

## 降级机制

没有 API key 也能跑——所有外部组件都有 try/except 保护：

| 组件 | 未配置时 |
|---|---|
| LLM | 关键词匹配降级 |
| E2B | 返回"未配置"提示 |
| Qdrant | 跳过知识库检索 |
| Mem0 | 跳过记忆存储/检索 |
| FSRS | 跳过复习项创建 |

## 开发路线

| 版本 | 目标 | 状态 |
|---|---|---|
| v0.1.0 | 最小对话闭环（教概念+出题+历史保存） | ✅ 已完成 |
| v0.2.0 | 代码沙箱 + 知识库 RAG + 长期记忆 + 间隔重复 + 流式 SSE | ✅ 已完成 |
| v0.3.0 | 前端打磨（移动端 + 深色模式 + 真增量流式） | 📋 计划 |

## License

MIT
