# AI 智能体文档

> 文档版本: v2.0 | 最后更新: 2026-08-09

---

## 概述

EduFlow 畅学内置四个核心 AI 智能体，运行在独立的 AI 服务（端口 8100）中，基于 OpenAI 大语言模型提供智能化学习体验。四个智能体各司其职，覆盖辅导、伴学、出题评估和学习规划全流程。

AI 服务基于 FastAPI 构建，使用 OpenAI SDK 调用大语言模型（默认 `gpt-4o-mini`）。系统设计了一个关键的智能降级机制：当未配置 `OPENAI_API_KEY` 时，各智能体不会报错，而是返回按类型定制的结构化降级回复，保证服务始终可用。

```
┌──────────────────────────────────────────────────────────┐
│                   AI 服务 (FastAPI, port 8100)            │
│                                                          │
│                   core/llm.py (统一 LLM 接口)              │
│                          │                               │
│         ┌────────────────┼────────────────┐              │
│         │                │                │              │
│         ▼                ▼                ▼              │
│   有 OPENAI_API_KEY   无 API Key                        │
│   调用 OpenAI API    返回智能降级回复                    │
│                                                          │
│   ┌─────────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐   │
│   │ Tutor   │ │ Buddy   │ │ Examiner   │ │ Planner  │   │
│   │ 导师    │ │ 伙伴    │ │ 出题官     │ │ 规划师   │   │
│   │ (chat)  │ │ (chat)  │ │ (tool)    │ │ (tool)   │   │
│   └─────────┘ └─────────┘ └────────────┘ └──────────┘   │
└──────────────────────────────────────────────────────────┘
```

智能体分类：

| 智能体 | 类型 | 说明 |
|--------|------|------|
| Tutor（导师） | chat | 苏格拉底式智能导师，辅导答疑与概念解释 |
| Buddy（学习伙伴） | chat | 学习伙伴式对话 |
| Examiner（出题官） | tool | 出题与答案评估 |
| Planner（规划师） | tool | 学习路径规划与调整 |

---

## 1. Tutor 导师智能体

**对应文件**：`services/ai/agents/tutor.py`

### 1.1 功能概述

Tutor 导师智能体采用苏格拉底式教学法，通过引导式提问帮助学生自主思考，而非直接给出答案。它负责辅导答疑和概念解释两个核心能力。

### 1.2 核心能力

| 能力 | 函数 | 说明 |
|------|------|------|
| 苏格拉底式对话 | `tutor_chat(message, context)` | 引导学生自主思考，逐步深入 |
| 概念解释 | `explain_concept(topic, level, context)` | 用匹配学习者水平的方式解释概念 |

### 1.3 系统提示词

导师的系统提示词定义了五条教学原则：

1. 苏格拉底式教学：引导学生自己思考，而不是直接给答案
2. 因材施教：根据学生的水平和理解程度调整解释方式
3. 循序渐进：从基础概念开始，逐步深入
4. 举一反三：用例子和类比帮助理解抽象概念
5. 鼓励式反馈：肯定学生的努力，激发学习兴趣

### 1.4 概念解释

`explain_concept` 根据学习者水平（beginner/intermediate/advanced）调整解释方式，要求使用类比和实例，条理清晰，200-400 字。支持水平映射：

- `beginner` → 初学者
- `intermediate` → 进阶
- `advanced` → 高级

### 1.5 降级行为

未配置 API Key 时：

- **对话降级**：返回苏格拉底式引导回复，包含「理解问题」「回顾已知」「拆解难点」「提出假设」四个引导步骤，不直接给答案。
- **概念解释降级**：返回结构化的学习框架，包含「概念概览」「学习路径建议」「思考引导」「建议行动」等模块，帮助学生自主构建理解。

### 1.6 对应接口

| 接口 | 路径 |
|------|------|
| AI 服务 | `POST /api/agents/chat`（agent_type="tutor"） |
| AI 服务 | `POST /api/agents/explain` |
| API 代理 | `POST /api/ai/chat`、`POST /api/ai/explain` |

---

## 2. Buddy 学习伙伴智能体

**对应文件**：`services/ai/agents/buddy.py`

### 2.1 功能概述

Buddy 学习伙伴智能体以同学的身份与学生交流，语气轻松友好。它像朋友一样陪伴学习，通过讨论和互相鼓励激发学习兴趣。

### 2.2 核心能力

| 能力 | 函数 | 说明 |
|------|------|------|
| 学习伙伴对话 | `buddy_chat(message, context)` | 以朋友口吻交流，给予鼓励和陪伴 |

### 2.3 系统提示词

学习伙伴的特点：

1. 平易近人：像朋友一样交流，语气轻松自然
2. 共同学习：用"我们一起"、"让我们来看看"等方式
3. 讨论式学习：通过提问和讨论激发思考
4. 互相鼓励：分享学习心得，给予积极反馈
5. 偶尔犯错：如果不知道，会诚实说"这个我也不太确定，我们一起查查资料"

### 2.4 降级行为

未配置 API Key 时：

- **对话降级**：返回鼓励性回复，分享实用的学习小建议（梳理已知信息、复述问题、换换心情、找人讨论等），营造陪伴感。

### 2.5 对应接口

| 接口 | 路径 |
|------|------|
| AI 服务 | `POST /api/agents/chat`（agent_type="buddy"） |

> 注意：`POST /api/agents/chat` 仅支持 `tutor` 和 `buddy` 两种 agent_type，传入其他值会返回 HTTP 400 错误，而非静默降级。

---

## 3. Examiner 出题官智能体

**对应文件**：`services/ai/agents/examiner.py`

### 3.1 功能概述

Examiner 出题官智能体负责根据学习内容生成高质量练习题，并对学生的作答进行智能评估。它支持难度自适应，能根据学生当前水平调整题目难度。

### 3.2 核心能力

| 能力 | 函数 | 说明 |
|------|------|------|
| 生成练习题 | `generate_questions(topic, difficulty, count, context)` | 生成结构化练习题 |
| 评估答案 | `evaluate_answer(question, user_answer, context)` | 对作答进行评分和反馈 |

### 3.3 系统提示词

出题原则：

1. 难度自适应：根据学生当前水平调整题目难度
2. 覆盖全面：涵盖概念理解、应用分析、综合评估等层次
3. 题型多样：选择题、填空题、简答题、编程题等
4. 即时反馈：每题提供详细解析和参考答案
5. 知识巩固：针对薄弱点重点出题

### 3.4 题目格式

所有题目统一为以下结构：

```json
{
  "id": 1,
  "question": "题目内容",
  "options": ["选项1", "选项2", "选项3", "选项4"],
  "answer": "1",
  "explanation": "详细解析",
  "difficulty": "easy",
  "topic": "Python 基础"
}
```

其中 `answer` 是正确选项的数字索引字符串（从 `"0"` 开始）。LLM 返回的题目会经过 `_normalize_questions` 规范化，确保字段完整、answer 为字符串格式。

### 3.5 答案评估

评估返回结构化结果：

```json
{
  "is_correct": true,
  "score": 85,
  "feedback": "个性化反馈，指出优点和不足",
  "hint": "引导性提示或拓展建议"
}
```

支持从 `context` 中提取正确答案（`correct_answer` 或 `answer` 字段）进行参考。

### 3.6 降级行为

未配置 API Key 时：

- **出题降级**：返回预设的通用编程题库（`_FALLBACK_QUESTION_BANK`），包含 12 道涵盖变量、数据类型、控制流、函数、数据结构、面向对象等核心知识点的题目。会根据难度筛选，数量不足时从全库补足，并标注主题关联。
- **评估降级**：基于字符串匹配进行简单判断（去除空白和大小写后比较）。答对返回 100 分，无标准答案返回 60 分，答错返回 30 分，并提供相应的引导反馈。

### 3.7 对应接口

| 接口 | 路径 |
|------|------|
| AI 服务 | `POST /api/agents/generate-questions` |
| AI 服务 | `POST /api/agents/evaluate` |
| API 代理 | `POST /api/ai/generate-questions`、`POST /api/ai/evaluate` |

---

## 4. Planner 规划师智能体

**对应文件**：`services/ai/agents/planner.py`

### 4.1 功能概述

Planner 规划师智能体根据学习目标、当前水平、可用时间和偏好，制定个性化的学习路径，并支持根据反馈动态调整计划。

### 4.2 核心能力

| 能力 | 函数 | 说明 |
|------|------|------|
| 生成学习路径 | `generate_learning_path(goal, level, duration_weeks, preferences)` | 生成结构化学习路径 |

### 4.3 系统提示词

规划原则：

1. 目标导向：根据学生的学习目标制定路径
2. 循序渐进：从基础到进阶，合理安排学习顺序
3. 时间合理：考虑学生可用时间，制定可行的计划
4. 动态调整：根据学习进度和反馈及时调整
5. 全面评估：考虑前置知识、学习风格和偏好

### 4.4 学习路径格式

学习路径统一返回以下结构：

```json
{
  "title": "路径标题",
  "description": "路径整体描述",
  "estimated_duration": "12 周",
  "milestones": [
    { "title": "里程碑名称", "description": "...", "estimated_hours": 24, "order": 1 }
  ],
  "modules": [
    { "title": "模块名称", "description": "...", "order": 1, "estimated_minutes": 240, "topics": ["知识点1"] }
  ]
}
```

LLM 返回结果经过 `_normalize_plan` 规范化，确保字段完整。

### 4.5 计划调整


### 4.6 降级行为

未配置 API Key 时：

- **路径规划降级**：返回结构化的通用学习路径模板，包含三个里程碑（夯实基础、深入实践、综合应用与拓展）和四个模块（导论与基础概念、核心知识体系、实战练习与项目、进阶提升与拓展），并根据 `duration_weeks` 和 `level` 动态调整时长和标签。
- **计划调整降级**：基于反馈关键词做规则化调整。检测到"太慢/加快"时缩减时长约 25%，检测到"太难/吃力"时延长时长约 30%，检测到"太简单/挑战"时建议跳过基础模块，并追加调整说明。

### 4.7 对应接口

| 接口 | 路径 |
|------|------|
| AI 服务 | `POST /api/agents/plan` |
| API 代理 | `POST /api/ai/plan` |

---

## 5. 降级机制

### 5.1 设计理念

AI 服务的核心设计原则是**永远可用**。无论是否配置了 `OPENAI_API_KEY`，所有接口都会正常响应，区别在于返回内容的质量和个性化程度。

### 5.2 实现原理

降级机制在 `services/ai/core/llm.py` 中实现：

```
请求到达 → chat_completion()
              │
              ├──▶ 有 client (配置了 API Key)
              │      → 组装 system prompt + messages
              │      → 调用 OpenAI API
              │      → 返回 LLM 生成内容
              │
              └──▶ 无 client (未配置 API Key)
                     → _build_fallback_reply(messages, agent_type)
                     → 根据 agent_type 选择对应降级模板
                     → 返回结构化降级回复
```

### 5.3 降级回复生成器

`llm.py` 中定义了四个按 agent 类型区分的降级回复生成器：

| 生成器 | agent_type | 风格 |
|--------|------------|------|
| `_tutor_fallback` | tutor | 苏格拉底式引导，不直接给答案 |
| `_buddy_fallback` | buddy | 鼓励性、轻松友好 |
| `_examiner_fallback` | examiner | 通用练习建议（结构化题目由 examiner 模块自行处理） |
| `_planner_fallback` | planner | 结构化通用路径（由 planner 模块自行处理） |
| `_default_fallback` | 其他 | 默认提示降级模式 |

每个智能体模块（tutor/examiner/planner）还有自己专属的降级处理，会生成更贴合具体场景的结构化内容。

### 5.4 降级标识

所有降级回复均包含「降级模式」「未配置 OPENAI_API_KEY」等提示文本，方便用户和管理员识别当前状态。同时，健康检查端点 `GET /api/health` 返回 `llm_available` 字段明确指示 LLM 是否可用。

### 5.5 错误处理策略

- **无效 agent_type**：`POST /api/agents/chat` 对不支持的 `agent_type` 返回 HTTP 400 错误，而非静默降级。仅 `tutor` 和 `buddy` 是有效的聊天 agent。
- **LLM 返回解析失败**：Examiner 和 Planner 在 LLM 返回的 JSON 解析失败时，会回退到各自的降级处理，不会抛出错误。
- **API 服务代理错误**：API 服务的 AI 路由在 AI 服务不可用时返回 503，超时（60 秒）返回 504。

---

## 6. 智能体协作场景

### 6.1 学习闭环

四个智能体协同工作，形成完整的学习闭环：

```
1. Planner 规划路径    →  生成个性化学习路径与模块
2. Tutor 辅导学习      →  学习过程中随时提问、解释概念
4. Examiner 出题评估    →  生成练习题、评估答案
5. Planner 调整计划    →  根据反馈动态调整学习路径
```

### 6.2 典型使用流程

1. 用户通过 Planner 生成学习路径（`POST /api/ai/plan`）
2. 用户在学习中遇到问题，向 Tutor 提问（`POST /api/ai/chat`，agent_type="tutor"）
3. 用户想讨论某个话题，与 Buddy 交流（`POST /api/ai/chat`，agent_type="buddy"）
4. 用户通过 Examiner 生成练习题（`POST /api/ai/generate-questions`）
5. 用户提交答案，Examiner 评估（`POST /api/ai/evaluate`）

---

## 7. LLM 核心模块

**对应文件**：`services/ai/core/llm.py`

### 7.1 配置

LLM 相关配置在 `services/ai/core/config.py` 中定义：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | None | OpenAI API Key，未配置时启用降级 |
| `LLM_PROVIDER` | `"openai"` | LLM 提供商 |
| `LLM_MODEL` | `"gpt-4o-mini"` | 模型名称 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度 |
| `MAX_TOKENS` | `4096` | 最大生成 token 数 |

### 7.2 核心接口

`llm.py` 提供两个核心异步函数：

| 函数 | 说明 |
|------|------|
| `chat_completion(messages, system_prompt, agent_type, temperature)` | 非流式对话补全，返回完整文本 |
| `stream_chat(messages, system_prompt, agent_type)` | 流式对话补全，逐字产出 |
| `is_llm_available()` | 判断 LLM 是否可用（是否配置了 API Key） |

`chat_completion` 是所有智能体调用的统一入口。它会自动将 system_prompt 作为首条 system 消息插入，并在无 API Key 时返回降级回复。

### 7.3 工具模块

AI 服务还包含一个工具模块 `services/ai/tools/knowledge_search.py`，用于知识检索。提示词模板存放在 `services/ai/prompts/` 目录下（如 `tutor_zh.txt`、`examiner_zh.txt`）。

---

## 8. Engine 引擎服务

**对应文件**：`services/engine/main.py`

Engine 服务独立于 AI 服务运行（端口 8200），提供基于学习科学理论的算法能力，不依赖 LLM。

### 8.1 FSRS 间隔重复算法

基于 FSRS（Free Spaced Repetition Scheduler）启发的间隔重复算法，计算最优复习时间：

```
输入：知识状态 (掌握度、复习次数、上次得分、距上次复习时长)
  │
  ├──▶ 计算稳定性 (stability)
  │     = max(1.0, 复习次数 * 0.5 + 掌握度 * 2)
  │     若有上次得分，按得分因子增强稳定性
  │
  ├──▶ 计算难度 (difficulty) = 1.0 - 掌握度
  │
  ├──▶ 计算下次复习间隔
  │     = 稳定性 * 24 * (1.0 - 难度 * 0.3) 小时
  │
  └──▶ 计算预测保留率
        = exp(-距上次复习时长 / (稳定性 * 24))
```

输出：下次复习小时数、预测保留率、稳定性、难度、推荐动作（review_now / skip）。

### 8.2 知识追踪

分析多个主题的知识状态，按掌握度分级：

| 掌握度 | 状态 |
|--------|------|
| >= 0.8 | mastered（已掌握） |
| >= 0.4 | learning（学习中） |
| < 0.4 | weak（薄弱） |

掌握度低于 0.6 的主题被标记为薄弱点（最多返回 5 个），并提供整体掌握度均值。

### 8.3 学习时长估算

根据难度和深度估算学习时长：

| 难度 | 基础时长（分钟） |
|------|-----------------|
| beginner | 30 |
| easy | 45 |
| medium | 60 |
| hard | 90 |
| expert | 120 |

| 深度 | 系数 |
|------|------|
| overview | 0.5 |
| standard | 1.0 |
| deep | 2.0 |

最终时长 = 基础时长 * 深度系数。

### 8.4 Engine 接口

| 接口 | 路径 | 说明 |
|------|------|------|
| 健康检查 | `GET /api/health` | 服务状态 |
| 下次复习 | `POST /api/engine/next-review` | FSRS 间隔重复计算 |
| 知识追踪 | `POST /api/engine/knowledge-tracing` | 多主题掌握度分析 |
| 时长估算 | `POST /api/engine/estimate-duration` | 学习时长估算 |

---

## 9. 技术实现总结

| 组件 | 技术选型 |
|------|----------|
| AI 服务框架 | FastAPI |
| LLM SDK | OpenAI Python SDK (AsyncOpenAI) |
| LLM 模型 | gpt-4o-mini（可配置） |
| 配置管理 | pydantic-settings |
| Engine 算法 | Python 标准库 (math) |
| 降级机制 | 内置 fallback 模板与预设题库 |

### 扩展性设计

- **模型无关性**：通过 `LLM_MODEL` 配置可切换不同的 OpenAI 模型。
- **降级容错**：所有智能体在无 API Key 时返回结构化降级内容，LLM 解析失败时回退到降级处理。
- **独立部署**：AI 服务与 Engine 服务独立部署，可分别扩展。
- **预设题库**：Examiner 内置 12 道通用编程题库，降级时仍可提供有价值的练习内容。
