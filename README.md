# EduFlow 畅学

> AI 驱动的学生自学平台 — 让学习自然流畅，让知识触手可及。

EduFlow（畅学）是一个基于大模型构建的 AI 驱动学生自学平台。区别于传统的教学管理系统（LMS）或 AI 助教工具，EduFlow 将**学生**置于学习的中心，AI 智能体作为辅助角色，按需提供辅导、练习、出题和进度追踪。

## 核心特性

### 🎯 学生为中心
- **学习仪表盘（Dashboard）** — 全局视图，学习目标、进度、推荐一目了然
- **学习路径引擎（Path Engine）** — AI 自动生成个性化学习路径，动态调整
- **模块学习区（Module Workspace）** — 沉浸式学习空间，支持各类学习材料
- **练习系统（Practice System）** — 自适应出题，即时反馈，巩固知识
- **进度追踪（Progress Tracker）** — 可视化学习进度，薄弱点智能诊断

### 🤖 AI 智能体辅助
- **AI 导师（Tutor）** — 按需辅导答疑，不会的时候随时提问
- **AI 伴学（Buddy）** — 协同练习对话，像同学一样讨论问题
- **AI 出题者（Examiner）** — 自适应出题，根据掌握程度调整难度

### 🏗️ 基础设施
- 支持 17+ LLM 提供商（OpenAI、Anthropic、DeepSeek 等）
- Guardrails 安全护栏，确保内容安全合规
- RAG / 知识图谱增强检索
- 知识追踪（Knowledge Tracing）算法

## 技术栈

- **前端**: Next.js + React + TypeScript
- **后端**: FastAPI + Python
- **AI 框架**: LangGraph / LangChain
- **数据库**: PostgreSQL + Redis
- **基础设施**: Docker / Kubernetes

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/weed33834/EduFlow.git
cd EduFlow

# 安装依赖
pnpm install

# 启动开发环境
pnpm dev
```

## 项目结构

```
EduFlow/
├── apps/                    # 前端应用
│   ├── web/                 # Web 主应用
│   └── mobile/              # 移动端（规划中）
├── services/                # 后端服务
│   ├── api/                 # API 服务
│   ├── ai/                  # AI 智能体服务
│   └── engine/              # 学习路径引擎
├── packages/                # 共享包
│   ├── shared/              # 类型定义和工具
│   └── ui/                  # UI 组件库
├── docs/                    # 文档
└── docker/                  # Docker 配置
```

## 路线图

### 第一阶段：核心学习闭环
- [ ] 学习仪表盘（Dashboard）
- [ ] 学习路径引擎（Path Engine）
- [ ] 模块学习区（Module Workspace）
- [ ] 基础练习系统
- [ ] 进度追踪

### 第二阶段：AI 智能体增强
- [ ] AI 导师对话系统
- [ ] AI 伴学协同练习
- [ ] 自适应出题系统
- [ ] 知识追踪算法

### 第三阶段：生态完善
- [ ] 学习社区与协作
- [ ] 评估与诊断系统
- [ ] 激励与游戏化
- [ ] 内容市场

## 许可

MIT License