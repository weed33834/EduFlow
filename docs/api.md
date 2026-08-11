# API 文档

> 文档版本: v2.0 | 最后更新: 2026-08-09

---

## 概述

EduFlow 畅学 API 采用 RESTful 风格设计，所有端点均以 `/api` 为前缀。请求和响应体使用 JSON 格式。系统包含三个独立的后端服务：

| 服务 | Base URL | 端口 | 说明 |
|------|----------|------|------|
| API 服务 | `http://localhost:8000/api` | 8000 | 主业务 API（认证、学习、练习、进度、AI 代理） |
| AI 服务 | `http://localhost:8100/api` | 8100 | AI 智能体服务（直接调用） |
| Engine 服务 | `http://localhost:8200/api` | 8200 | 学习引擎（知识追踪、间隔重复） |

前端通过 Next.js rewrites 将 `/api/*` 代理到 API 服务（端口 8000）。

---

## 通用约定

### 认证

除注册、登录和健康检查外，所有 API 均需在请求头中携带 JWT Token：

```
Authorization: Bearer <your_jwt_token>
```

Token 通过 `POST /api/auth/register` 或 `POST /api/auth/login` 获取，默认有效期为 7 天。

### 响应格式

成功响应直接返回 JSON 数据，无统一包装层。例如：

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "alice"
}
```

### 错误响应

错误时返回对应 HTTP 状态码和 `detail` 字段：

```json
{
  "detail": "Email or username already exists"
}
```

常见状态码：

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误（如无效的 agent_type） |
| 401 | 未认证或 Token 无效 |
| 403 | 无权限访问该资源 |
| 404 | 资源不存在 |
| 422 | 数据验证失败（如标题为空） |
| 503 | AI 服务不可用 |
| 504 | AI 服务请求超时 |

---

## 1. 认证 API

路由前缀：`/api/auth`，对应文件 `services/api/routers/auth.py`

### 1.1 用户注册

```
POST /api/auth/register
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| display_name | string | 否 | 显示名称，默认取 username |

**请求示例**：

```json
{
  "email": "user@example.com",
  "username": "alice",
  "password": "SecurePass123",
  "display_name": "Alice"
}
```

**响应**（200）：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "alice",
    "display_name": "Alice",
    "avatar_url": null,
    "bio": null,
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-08-09T10:00:00+00:00"
  }
}
```

若邮箱或用户名已存在，返回 400。

### 1.2 用户登录

```
POST /api/auth/login
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |

**响应**：与注册相同，返回 `access_token` 和 `user` 信息。凭据无效时返回 401。

### 1.3 获取当前用户信息

```
GET /api/auth/me
```

**请求头**：`Authorization: Bearer <token>`

**响应**：返回当前登录用户的完整信息（`_user_dict` 格式）。

### 1.4 更新当前用户信息

```
PUT /api/auth/me
```

**请求头**：`Authorization: Bearer <token>`

**请求体**（所有字段可选）：

| 字段 | 类型 | 说明 |
|------|------|------|
| display_name | string \| null | 显示名称 |
| avatar_url | string \| null | 头像 URL |
| bio | string \| null | 个人简介 |

**响应**：返回更新后的用户信息。

---

## 2. 学习路径与模块 API

路由前缀：`/api/learning`，对应文件 `services/api/routers/learning.py`

所有端点均需 `Authorization: Bearer <token>`，且只能操作当前用户拥有的资源。

### 2.1 创建学习路径

```
POST /api/learning/paths
```

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| title | string | 是 | - | 路径标题（不能为空） |
| description | string | 否 | `""` | 描述 |
| goal | string | 否 | `""` | 学习目标 |
| estimated_duration | integer | 否 | null | 预计时长 |
| difficulty | string | 否 | `"beginner"` | 难度 |

**响应**：返回创建的路径对象（含 `id`、`user_id`、`status`、`progress` 等字段）。

### 2.2 获取学习路径列表

```
GET /api/learning/paths
```

**响应**：返回当前用户的所有学习路径数组，按创建时间倒序排列。

### 2.3 获取单个学习路径（含模块）

```
GET /api/learning/paths/{path_id}
```

**响应**：

```json
{
  "path": { "id": 1, "title": "...", "..." : "..." },
  "modules": [ { "id": 1, "title": "...", "..." : "..." } ]
}
```

返回路径及其下所有模块（按 `order` 排序）。路径不存在返回 404，无权限返回 403。

### 2.4 更新学习路径

```
PUT /api/learning/paths/{path_id}
```

**请求体**（所有字段可选）：

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string \| null | 路径标题 |
| description | string \| null | 描述 |
| goal | string \| null | 学习目标 |
| estimated_duration | integer \| null | 预计时长 |
| difficulty | string \| null | 难度 |
| status | string \| null | 状态 |

**响应**：返回更新后的路径对象。

### 2.5 删除学习路径

```
DELETE /api/learning/paths/{path_id}
```

级联删除该路径下的所有模块、练习会话和进度记录。

**响应**：`{ "detail": "Path deleted" }`

### 2.6 创建模块

```
POST /api/learning/modules
```

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path_id | integer | 是 | - | 所属路径 ID |
| title | string | 是 | - | 模块标题（不能为空） |
| description | string | 否 | `""` | 描述 |
| order | integer | 否 | `0` | 排序序号 |
| content | array | 否 | `[]` | 模块内容 |
| estimated_minutes | integer | 否 | null | 预计学习分钟数 |

创建模块后会自动重算所属路径的进度。

### 2.7 获取单个模块

```
GET /api/learning/modules/{module_id}
```

**响应**：返回模块对象。通过所属路径验证用户权限。

### 2.8 更新模块

```
PUT /api/learning/modules/{module_id}
```

**请求体**（所有字段可选）：

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string \| null | 模块标题 |
| description | string \| null | 描述 |
| order | integer \| null | 排序序号 |
| content | array \| null | 模块内容 |
| status | string \| null | 状态（not_started/in_progress/completed） |
| estimated_minutes | integer \| null | 预计学习分钟数 |

更新 `status` 时会自动调整模块 `progress`：completed→100、in_progress→50、not_started→0，并重算路径进度。

### 2.9 删除模块

```
DELETE /api/learning/modules/{module_id}
```

级联删除关联的练习会话和进度记录，并重算路径进度。

**响应**：`{ "detail": "Module deleted" }`

---

## 3. 练习 API

路由前缀：`/api/practice`，对应文件 `services/api/routers/practice.py`

所有端点均需 `Authorization: Bearer <token>`。

### 3.1 创建练习会话

```
POST /api/practice/sessions
```

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| module_id | integer | 否 | null | 关联模块 ID（提供时验证归属） |
| session_type | string | 否 | `"quiz"` | 会话类型 |
| topic | string | 否 | null | 练习主题 |
| questions | array | 否 | `[]` | 题目列表 |

**响应**：返回创建的会话对象（状态为 `in_progress`，分数为 0）。

### 3.2 获取练习会话列表

```
GET /api/practice/sessions
```

**响应**：返回当前用户的所有练习会话，按开始时间倒序。

### 3.3 获取单个练习会话

```
GET /api/practice/sessions/{session_id}
```

**响应**：返回会话对象（含 `questions`、`answers`、`score` 等）。会话不存在返回 404，无权限返回 403。

### 3.4 删除练习会话

```
DELETE /api/practice/sessions/{session_id}
```

**响应**：`{ "detail": "Session deleted" }`

### 3.5 提交答案

```
POST /api/practice/submit
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | integer | 是 | 会话 ID |
| question_id | integer | 是 | 题目 ID |
| answer | string | 是 | 用户答案 |
| is_correct | boolean | 是 | 是否正确 |

每次提交将答案追加到会话的 `answers` 列表，并实时更新会话 `score`（正确数/总数 * 100）。

**响应**：

```json
{
  "score": 75.0,
  "total": 4,
  "correct": 3
}
```

### 3.6 完成练习会话

```
PUT /api/practice/sessions/{session_id}/complete
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| weak_points | string[] | `[]` | 薄弱知识点 |
| strong_points | string[] | `[]` | 掌握知识点 |

完成会话时：计算最终得分、设置状态为 `completed`、记录完成时间。根据是否达到及格线（`PASS_SCORE_THRESHOLD = 60`）更新关联模块状态。若关联模块，还会创建或更新 `Progress` 记录（合并测验成绩与知识点），并重算路径进度。

**响应**：

```json
{
  "session": { "id": 1, "status": "completed", "score": 80.0, "..." : "..." },
  "passed": true,
  "pass_threshold": 60,
  "score": 80.0
}
```

---

## 4. 进度 API

路由前缀：`/api/progress`，对应文件 `services/api/routers/progress.py`

所有端点均需 `Authorization: Bearer <token>`。

### 4.1 获取我的学习进度

```
GET /api/progress/me
```

**响应**：返回当前用户所有模块的进度详情，包含模块标题。

```json
{
  "user_id": 1,
  "module_count": 3,
  "details": [
    {
      "id": 1,
      "module_id": 5,
      "module_title": "Python 基础",
      "learning_time_minutes": 120,
      "completion_percentage": 100.0,
      "quiz_scores": [{ "session_id": 1, "score": 85.0, "passed": true }],
      "weak_points": ["递归"],
      "strong_points": ["循环"],
      "updated_at": "2026-08-09T14:00:00+00:00"
    }
  ]
}
```

### 4.2 更新学习进度

```
POST /api/progress/update
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| module_id | integer | 是 | 模块 ID（验证归属） |
| learning_time_minutes | integer | 否 | 学习时长（分钟） |
| completion_percentage | float | 否 | 完成百分比 |
| quiz_scores | array | 否 | 测验成绩列表 |
| weak_points | string[] | 否 | 薄弱知识点 |
| strong_points | string[] | 否 | 掌握知识点 |

若进度记录不存在则创建，存在则更新对应字段。

**响应**：返回更新后的进度记录。

### 4.3 获取进度概览

```
GET /api/progress/overview
```

**响应**：返回当前用户的学习进度全局概览：

```json
{
  "user_id": 1,
  "module_count": 3,
  "total_learning_time_minutes": 240,
  "overall_completion": 66.7,
  "weak_points": ["递归", "异步"],
  "strong_points": ["循环", "函数"],
  "module_details": [
    {
      "module_id": 5,
      "module_title": "Python 基础",
      "path_title": "Python 学习路径",
      "module_status": "completed",
      "module_progress": 100.0,
      "learning_time_minutes": 120,
      "completion_percentage": 100.0,
      "quiz_scores": [],
      "weak_points": [],
      "strong_points": [],
      "updated_at": "2026-08-09T14:00:00+00:00"
    }
  ]
}
```

---

## 5. AI 代理 API（API 服务）

路由前缀：`/api/ai`，对应文件 `services/api/routers/ai.py`

这些端点在 API 服务中作为代理，鉴权后将请求转发至 AI 服务（端口 8100）。所有端点均需 `Authorization: Bearer <token>`。转发超时为 60 秒，AI 服务不可用时返回 503，超时返回 504。

### 5.1 AI 对话

```
POST /api/ai/chat
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| message | string | - | 用户消息 |
| context | object | `{}` | 上下文信息 |
| agent_type | string | `"tutor"` | 智能体类型（tutor / buddy） |

转发至 AI 服务 `POST /api/agents/chat`，并附加 `user_id`。

### 5.2 生成练习题

```
POST /api/ai/generate-questions
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| topic | string | - | 出题主题 |
| difficulty | string | `"medium"` | 难度 |
| count | integer | `5` | 题目数量 |
| context | string \| object \| null | null | 附加上下文 |

转发至 AI 服务 `POST /api/agents/generate-questions`。

### 5.3 概念解释

```
POST /api/ai/explain
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| concept | string | - | 概念名称 |
| context | object \| null | null | 附加上下文 |
| detail_level | string | `"beginner"` | 学习者水平（通过 alias 映射为 AI 服务的 `level`） |

转发至 AI 服务 `POST /api/agents/explain`。

### 5.4 评估答案

```
POST /api/ai/evaluate
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| question | string | - | 题目内容 |
| user_answer | string | - | 学生答案 |
| correct_answer | string | `""` | 正确答案（合并进 context 转发） |
| context | string \| object \| null | null | 附加上下文 |

转发至 AI 服务 `POST /api/agents/evaluate`，`correct_answer` 会合并进 `context` 后转发。

### 5.5 学习路径规划

```
POST /api/ai/plan
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| goal | string | - | 学习目标 |
| level | string | `"beginner"` | 当前水平 |
| duration_weeks | integer | `12` | 计划周期（周） |
| difficulty | string | `"medium"` | 难度（映射到 preferences） |
| context | object \| null | null | 附加上下文（映射到 preferences） |

转发至 AI 服务 `POST /api/agents/plan`，`difficulty` 和 `context` 会映射为 `preferences`。

---

## 5.6 复习(间隔重复) API

对应文件 `services/api/routers/review.py`。练习完成后会自动为主题模块与薄弱点生成复习项，
按 FSRS 启发式(调用 Engine)计算下次复习时间；引擎不可用时降级为内置排期。

### 5.6.1 待复习列表

`GET /api/review/due`（需登录）

返回 `{ due_count, upcoming_count, total, due_items, upcoming_items }`，每项含 `topic / mastery_level / review_count / stability / due_at / status(due|upcoming)`。

### 5.6.2 全部复习项

`GET /api/review/`（需登录）

返回 `{ items: [...] }`。

### 5.6.3 完成一次复习

`POST /api/review/{review_id}/review`（需登录）

```json
{ "score": 80 }   // 0-100 自评得分
```

按得分更新掌握度与复习次数，重新调用 Engine 排期下一次复习时间。

---

## 5.7 Engine 网关(经 API)

对应文件 `services/api/routers/engine.py`。将学习引擎能力带鉴权地暴露给前端：

| 端点 | 说明 |
|------|------|
| `POST /api/engine/next-review` | 计算单个知识点下次复习时间，返回 `due_at` |
| `POST /api/engine/knowledge-tracing` | 批量知识追踪，识别薄弱点 |
| `POST /api/engine/estimate-duration` | 估算学习时长 |

引擎服务不可用时返回 `503`，调用方应优雅降级。

---

## 6. AI 服务 API（端口 8100）

对应文件 `services/ai/main.py`。AI 服务直接暴露智能体接口，可被 API 服务代理调用，也可直接访问。

### 6.1 健康检查

```
GET /api/health
```

**响应**：

```json
{
  "status": "ok",
  "service": "EduFlow AI Service",
  "version": "0.1.0",
  "timestamp": "2026-08-09T12:00:00+00:00",
  "llm_available": true,
  "config": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "api_port": 8001,
    "debug": false
  },
  "agents": [
    { "name": "tutor", "type": "chat", "description": "苏格拉底式智能导师" },
    { "name": "buddy", "type": "chat", "description": "学习伙伴式对话" },
    { "name": "examiner", "type": "tool", "description": "出题与答案评估" },
    { "name": "planner", "type": "tool", "description": "学习路径规划与调整" }
  ],
  "endpoints": [
    "POST /api/agents/chat",
    "POST /api/agents/explain",
    "POST /api/agents/discuss",
    "POST /api/agents/generate-questions",
    "POST /api/agents/evaluate",
    "POST /api/agents/plan",
    "POST /api/agents/adjust-plan"
  ]
}
```

### 6.2 智能体对话

```
POST /api/agents/chat
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| message | string | - | 用户消息 |
| agent_type | string | `"tutor"` | 智能体类型（tutor / buddy），无效值返回 400 |
| context | object | `{}` | 上下文信息 |
| history | array | `[]` | 多轮会话历史 `[{role, content}]` |

> 说明：tutor / buddy 已接入本地知识库检索(RAG)，会先检索相关知识再生成回答，无 LLM 时也能给出有依据的降级回复。

**响应**：

```json
{
  "response": "让我们一步步来思考...",
  "agent_type": "tutor",
  "llm_available": true
}
```

### 6.2.1 流式对话

```
POST /api/agents/chat/stream
```

与 `/api/agents/chat` 请求体相同，返回 SSE(`text/event-stream`) 增量内容，`data: ` 事件，结束标记 `data: [done]`。前端经 API 网关 `POST /api/ai/chat/stream` 使用。
```

### 6.3 概念解释

```
POST /api/agents/explain
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| concept | string | - | 概念名称 |
| context | object \| null | null | 附加上下文 |
| level | string | `"beginner"` | 学习者水平 |

**响应**：`{ "response": "...", "concept": "...", "level": "...", "llm_available": true }`

### 6.4 话题讨论

```
POST /api/agents/discuss
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| topic | string | - | 讨论话题 |
| context | object \| null | null | 附加上下文 |

**响应**：`{ "response": "...", "topic": "...", "llm_available": true }`

### 6.5 生成练习题

```
POST /api/agents/generate-questions
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| topic | string | - | 出题主题 |
| difficulty | string | `"medium"` | 难度 |
| count | integer | `5` | 题目数量 |
| context | string \| object \| null | `""` | 附加上下文 |

**响应**：

```json
{
  "questions": [
    {
      "id": 1,
      "question": "下列哪个选项是 Python 中合法的变量名？",
      "options": ["2variable", "_username", "class", "my-var"],
      "answer": "1",
      "explanation": "...",
      "difficulty": "easy",
      "topic": "Python 基础"
    }
  ],
  "count": 5,
  "topic": "Python 基础",
  "difficulty": "medium",
  "llm_available": true
}
```

### 6.6 评估答案

```
POST /api/agents/evaluate
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| question | string | - | 题目内容 |
| user_answer | string | - | 学生答案 |
| context | string \| object \| null | null | 上下文（可含 correct_answer） |

**响应**：

```json
{
  "is_correct": true,
  "score": 100,
  "feedback": "回答正确！",
  "hint": "可以尝试用自己的语言复述这个知识点。",
  "llm_available": true
}
```

### 6.7 学习路径规划

```
POST /api/agents/plan
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| goal | string | - | 学习目标 |
| level | string | `"beginner"` | 当前水平 |
| duration_weeks | integer | `12` | 计划周期（周） |
| preferences | list \| object \| string \| null | null | 学习偏好 |

**响应**：

```json
{
  "plan": {
    "title": "「Python 全栈」入门学习路径",
    "description": "...",
    "estimated_duration": "12 周",
    "milestones": [{ "title": "...", "estimated_hours": 24, "order": 1 }],
    "modules": [{ "title": "...", "estimated_minutes": 240, "topics": [] }]
  },
  "goal": "掌握 Python 全栈开发",
  "level": "beginner",
  "llm_available": true
}
```

### 6.8 调整学习计划

```
POST /api/agents/adjust-plan
```

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| feedback | string | - | 学生反馈内容 |
| current_plan | object | `{}` | 当前学习计划 |

**响应**：`{ "plan": { ... }, "feedback": "...", "llm_available": true }`

---

## 7. Engine 服务 API（端口 8200）

对应文件 `services/engine/main.py`。提供学习科学算法能力。

### 7.1 健康检查

```
GET /api/health
```

**响应**：`{ "status": "ok", "service": "EduFlow Engine" }`

### 7.2 计算下次复习时间

```
POST /api/engine/next-review
```

使用 FSRS 启发的间隔重复算法，基于知识掌握度、复习次数和上次得分计算最优复习间隔。

**请求体**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| knowledge_state | object | - | 知识状态 |
| desired_retention | float | `0.9` | 期望保留率 |

`knowledge_state` 对象：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| user_id | integer | - | 用户 ID |
| topic | string | - | 主题 |
| mastery_level | float | `0.0` | 掌握度（0-1） |
| review_count | integer | `0` | 复习次数 |
| last_review_score | float \| null | null | 上次得分 |
| time_since_last_review_hours | float | `0.0` | 距上次复习小时数 |

**响应**：

```json
{
  "next_review_hours": 48.5,
  "predicted_retention": 0.85,
  "stability": 3.5,
  "difficulty": 0.4,
  "recommended": "review_now"
}
```

`recommended` 为 `"review_now"`（保留率低于期望值）或 `"skip"`。

### 7.3 知识追踪

```
POST /api/engine/knowledge-tracing
```

分析多个主题的知识状态，识别薄弱点。

**请求体**：`KnowledgeState` 对象数组（同 7.2 的 `knowledge_state`）。

**响应**：

```json
{
  "topics": [
    { "topic": "递归", "mastery": 30.0, "status": "weak", "reviews_done": 2 },
    { "topic": "循环", "mastery": 85.0, "status": "mastered", "reviews_done": 5 }
  ],
  "weak_points": ["递归"],
  "overall_mastery": 57.5,
  "total_topics": 2
}
```

状态判定：`mastered`（≥80%）、`learning`（≥40%）、`weak`（<40%）。掌握度低于 0.6 的主题会被标记为薄弱点（最多返回 5 个）。

### 7.4 估算学习时长

```
POST /api/engine/estimate-duration
```

**请求参数**（query/form）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| topic | string | - | 主题 |
| difficulty | string | `"medium"` | 难度（beginner/easy/medium/hard/expert） |
| depth | string | `"standard"` | 深度（overview/standard/deep） |

基础时长按难度：beginner=30、easy=45、medium=60、hard=90、expert=120（分钟），再乘以深度系数：overview=0.5、standard=1.0、deep=2.0。

**响应**：

```json
{
  "topic": "递归",
  "estimated_minutes": 120,
  "difficulty": "hard",
  "depth": "deep"
}
```

---

## 8. 健康检查端点汇总

| 服务 | 端点 | 端口 |
|------|------|------|
| API 服务 | `GET http://localhost:8000/api/health` | 8000 |
| AI 服务 | `GET http://localhost:8100/api/health` | 8100 |
| Engine 服务 | `GET http://localhost:8200/api/health` | 8200 |

API 服务健康检查响应：

```json
{
  "status": "ok",
  "version": "0.1.0",
  "service": "EduFlow API"
}
```

---

## 9. 前端 API 客户端

前端通过 `apps/web/src/lib/api.ts` 调用上述接口，主要导出以下 API 模块：

| 模块 | 说明 |
|------|------|
| `authAPI` | 登录、注册、获取/更新用户信息 |
| `learningAPI` | 学习路径与模块的 CRUD |
| `practiceAPI` | 练习会话管理、提交答案、完成会话 |
| `progressAPI` | 获取进度、更新进度、概览 |
| `aiAPI` | AI 对话、出题、解释、评估、规划 |

所有请求经统一 `request()` 方法处理，自动附加 JWT Token、解析错误响应并抛出 `ApiError`。
