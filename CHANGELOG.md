# 变更日志

所有重要的项目变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本管理遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.1.0] - 2026-08-09

### 新增

- 项目初始化，搭建 monorepo 架构（pnpm workspace）
- 用户认证系统：JWT 令牌认证、邮箱注册/登录、密码哈希（bcrypt）
- 学习路径管理：创建/编辑/删除学习路径、模块管理、自动进度计算
- 练习系统：创建练习会话、答题提交、成绩计算、会话回顾与删除
- 进度追踪：学习时长记录、完成百分比、薄弱点与优势点分析
- AI 导师（Tutor）：苏格拉底式教学引导、概念解释、按需辅导
- AI 伴学（Buddy）：学习伙伴式对话、话题讨论、情感支持
- AI 出题者（Examiner）：自适应出题、答案评估、即时反馈
- AI 规划师（Planner）：个性化学习路径规划、计划调整
- 学习引擎（Engine）：FSRS 知识追踪算法、间隔重复复习计算、学习时长估算
- 前端应用：首页、仪表盘、学习、练习、进度、AI导师、AI伴学、设置、登录/注册
- Docker 容器化部署：API、AI、Engine、Web 四个服务 + PostgreSQL + Redis
- 共享 UI 组件库：GlassCard、Button、ProgressBar、StatCard
- 文档：架构设计、API 文档、部署文档、开发指南、AI智能体文档

### 技术栈

- 前端：Next.js 14、TypeScript 5、Tailwind CSS 3
- 后端：FastAPI、SQLAlchemy 2.0（异步）、SQLite（开发）/ PostgreSQL（生产）
- AI 服务：FastAPI、OpenAI 兼容 API、智能降级机制
- 引擎服务：FastAPI、FSRS 知识追踪算法
- 部署：Docker、Docker Compose

---

> 更多历史版本信息请查看 [GitHub Releases](https://github.com/your-org/eduflow/releases)。
