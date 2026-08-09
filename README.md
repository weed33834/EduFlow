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

## 快速开始

```bash
# 方式一：Docker 一键启动
cd docker && docker-compose up -d

# 方式二：手动启动
# 1. 安装依赖
pnpm install

# 2. 启动 API 服务
cd services/api && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 3. 启动 AI 服务
cd services/ai && pip install -r requirements.txt && uvicorn main:app --reload --port 8100

# 4. 启动前端
cd apps/web && pnpm dev
```

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