# 版本规范

## 规则（Semver 0.x 约定）

| 位 | 含义 | 判定标准 |
|---|---|---|
| `0.X.0` | **大迭代** | 新增核心能力面或架构变化，多个能力必须一起发布才成立 |
| `0.x.Y` | **小迭代** | bug 修复、单点小功能、测试与文档、配置调整——不改变产品能力边界 |

- 当前主线：`0.4.x`（Agent 核心闭环线）。
- 下一个大迭代预留：`0.5.0`（候选：前端打磨、LangSmith/Langfuse 外部追踪、Redis 分布式限流）。
- patch 号允许超过 9（如 v0.4.10）。

## 全量提交归类审计

| Tag | 提交 | 类型 | 归类理由 |
|---|---|---|---|
| v0.3.1 | fix(auth): created_at 类型修复注册/登录 500 | 小 | bug 修复 |
| v0.3.2 | fix(deps): bcrypt==4.0.1 钉版 | 小 | 依赖修复 |
| **v0.4.0** | **feat(agent): 判题闭环+FSRS 重排+真流式+PostgresSaver+JWT fail-fast** | **大** | judge 节点是新核心能力面，与流式/持久化一体发布才成立；唯一中间位跳变 |
| v0.4.1 | fix(memory): mem0ai 2.x API 迁移 | 小 | 让既有功能恢复工作，无新能力 |
| v0.4.2 | fix(knowledge): qdrant query_points 迁移 | 小 | 同上 |
| v0.4.3 | fix(sandbox): e2b 2.x API 迁移 | 小 | 同上 |
| v0.4.4 | feat(knowledge): 摄入 CLI + 分块器 | 小 | 单点工具能力，不触碰核心交互 |
| v0.4.5 | feat(profile): 判题回写画像 | 小 | 在已有判题结果上补一路写库 |
| v0.4.6 | feat(ratelimit): 进程内限流 | 小 | 独立防御层，单文件+依赖注入 |
| v0.4.7 | feat(agent): 多轮意图分类 | 小 | 既有节点的 prompt 增强 |
| v0.4.8 | feat(observability): LLM 追踪日志 | 小 | 日志埋点，零行为变化 |
| v0.4.9 | test(evals): 意图评估集 | 小 | 测试资产 |
| v0.4.10 | docs: README 对齐 | 小 | 文档 |

## 未来大迭代候选（升 0.5.0 / 0.6.0 的门槛）

- 前端打磨成体系落地（移动端+深色模式+判题 UI 重构）
- 外部可观测平台接入（LangSmith/Langfuse）
- Redis 分布式限流 / 多 worker 会话一致性
- 多 Agent 协作或工具自主规划（当前是固定状态机）
