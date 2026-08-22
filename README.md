# EduAgent

> AI 编程学习 Agent — 会教编程、会出题、会判题、会运行代码、会排复习的 AI 学习伙伴。

不是平台，不是工具箱，不是 LMS。就是一个 Agent。

## 项目结构

```
EduAgent/
├── backend/                  # FastAPI 后端（单服务）
│   ├── app/
│   │   ├── main.py           # 入口（生产模式安全检查 fail-fast）
│   │   ├── config.py         # 配置（LLM/E2B/Qdrant/Mem0/限流）
│   │   ├── database.py       # 数据库引擎
│   │   ├── ratelimit.py      # 进程内滑动窗口限流
│   │   ├── security.py       # JWT + bcrypt
│   │   ├── models.py         # 数据模型（User/Session/Message/ReviewItem）
│   │   ├── agents/           # LangGraph 状态机
│   │   │   ├── state.py      # AgentState 定义
│   │   │   ├── nodes.py      # 10 节点：understand→recall→plan→[teach|quiz|code|review|judge]→respond→reflect
│   │   │   └── graph.py      # StateGraph + PostgresSaver/MemorySaver Checkpointer
│   │   ├── tools/            # 工具层（全部用开源项目）
│   │   │   ├── llm.py        # LiteLLM 封装 + JSON mode + 调用追踪日志 + 真流式
│   │   │   ├── sandbox.py    # E2B 代码沙箱（2.x API）
│   │   │   ├── knowledge.py  # Qdrant RAG + 分块器
│   │   │   └── memory.py     # Mem0 长期记忆（AsyncMemory）
│   │   └── routers/          # API 路由
│   │       ├── auth.py       # 认证（注册/登录/获取用户，IP 限流）
│   │       ├── chat.py       # SSE 流式对话 + 判题闭环 + FSRS 重排（用户限流）
│   │       ├── sessions.py   # 会话管理
│   │       └── profile.py    # 学生画像（判题结果自动回写 strengths/weaknesses）
│   ├── scripts/
│   │   └── ingest_knowledge.py  # 知识库摄入 CLI
│   ├── tests/                # pytest 套件（80 用例，全离线可跑）
│   ├── requirements.txt      # 全量精确钉版
│   └── Dockerfile
├── frontend/                 # Next.js 14 前端
│   └── src/
│       ├── app/
│       │   ├── page.tsx       # 落地页
│       │   ├── login/        # 登录
│       │       ├── register/     # 注册
│       │   └── chat/         # 主界面（SSE 流式 + 判题反馈 + 代码结果）
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
git clone https://github.com/weed33834/EduAgent.git
cd EduAgent
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
understand → recall → plan → [teach | quiz | code | review | judge | agent_loop] → respond → reflect → END（LLM 可用时生成型任务走 agent_loop 自主编排工具）
```

| 节点 | 功能 |
|---|---|
| understand | 意图分类（带最近 6 轮上下文消解指代；LLM JSON mode / 关键词降级） |
| recall | Mem0 检索长期记忆 + Qdrant 检索知识库文档 |
| plan | 判题优先（待作答 quiz/review）→ 到期复习项 → 按意图路由 |
| teach | 讲解概念，带入知识库参考文档 + 学生记忆（真流式输出） |
| quiz | 出题（LiteLLM JSON mode 保证结构化输出） |
| judge | 判题闭环：quiz 选项确定性判分 / review 复述 LLM 判卷，映射 FSRS rating |
| code | E2B 沙箱执行学生代码 → LLM 根据输出给反馈（真流式输出） |
| review | FSRS 间隔重复，生成复习内容；作答后按判题结果重排卡片 due |
| respond | 组织回复，加入对话历史（Checkpointer 自动持久化） |
| reflect | Mem0 自动保存对话记忆 |

## 学习闭环

- **判题**：出题后学生回复 A-D 即触发 judge；答对 rating=3、答错 rating=1
- **间隔重复**：fsrs 包按作答质量重排每张卡片的下次到期时间；同概念只建一张卡
- **画像回写**：判题结果自动写入 StudentProfile 的 strengths/weaknesses（各留最近 20 条）

## 知识库摄入

RAG 需要先把文档灌进 Qdrant：

```bash
cd backend
python scripts/cli.py ingest --dir ../docs --pattern "**/*.md"
```

## 管理 CLI

```bash
python scripts/cli.py stats                          # 用户/会话/消息/复习卡统计
python scripts/cli.py traces --session 42            # 查看 LLM 调用链
python scripts/cli.py create-user --email a@b.c --username alice --password ****
```

## 可观测性与限流

**本地追踪（默认开启，零账号零依赖）**

每次请求生成 trace_id，所有 LLM 调用（含失败）记录 span 到 `backend/logs/traces.jsonl`：

```bash
cd backend
python scripts/cli.py traces               # 最近 20 条调用链
python scripts/cli.py traces --session 42  # 按会话过滤
```

**外部面板（可选增强）**

| 方案 | 需要云账号 | 接入方式 |
|---|---|---|
| LangSmith | ✅ 必须 | `LITELLM_SUCCESS_CALLBACK=langsmith` + 安装其 SDK |
| Langfuse Cloud | ✅ 云端版要 | `LITELLM_SUCCESS_CALLBACK=langfuse` + SDK |
| Langfuse 自托管 | ❌ 开源版 docker 起 | 同上，指向自建地址 |
| Phoenix (Arize) | ❌ 本地 pip 即起 UI | litellm otel 回调 / OTLP |

**限流**：chat 按用户（默认 20 次/分钟）、认证按 IP（默认 10 次/分钟），超限 429+Retry-After；
配 `REDIS_URL` 启用跨 worker 分布式计数，未配置回退进程内实现。

## 测试

```bash
cd backend
pip install -r requirements.txt
pytest   # 全离线可跑（外部服务均 mock/降级）
```

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
| v0.4.x | Agent 核心闭环：判题节点 + FSRS 按质重排 + 真增量流式 + PostgresSaver 持久化 + 知识库摄入 + 画像回写 + 限流 + 追踪日志 + 评估集 + 全量工程审计 | ✅ 已完成 |
| v0.5.0 | 前端框架现代化：Next 16 + React 19（依赖漏洞 48→0），移除 legacy-peer-deps；外部追踪接入点、Redis 分布式限流、深色模式与移动端适配随 v0.4.x 落地 | ✅ 已完成 |
| v0.6.0 | 对话管理大迭代：重新生成、编辑重发、会话置顶/归档/搜索；历史以 DB 为唯一事实源（移除 Checkpointer，多 worker 天然安全） | ✅ 已完成 |
| v0.7.0 | 工具自主规划：function-calling 主循环（跑代码/查知识库/查记忆/出题四工具自主编排），judge·FSRS 教学护栏保持固定 | ✅ 已完成 |

## 生产部署

```bash
cp .env.example .env   # 填入 POSTGRES_PASSWORD / JWT_SECRET / LITELLM_API_KEY
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

生产覆盖（`docker-compose.prod.yml`）：数据库/向量库/Redis 不暴露宿主机端口；
`ENV=production` 下弱 JWT 密钥或缺 LLM key 会拒绝启动；前端只绑回环交给反代。

## License

MIT
