# API 文档

> 文档版本: v1.0 | 最后更新: 2026-08-09

---

## 概述

EduFlow 畅学 API 采用 RESTful 风格设计，所有 API 端点均以 `/api/v1/` 为前缀。请求和响应体使用 JSON 格式。

- **Base URL**: `https://api.eduflow.example.com/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

---

## 通用约定

### 认证

所有受保护的 API 需要在请求头中携带 JWT Token：

```
Authorization: Bearer <your_jwt_token>
```

### 分页

列表接口统一使用以下分页参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | integer | 1 | 页码，从 1 开始 |
| `page_size` | integer | 20 | 每页条数，最大 100 |

分页响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

### 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误响应：

```json
{
  "code": 40001,
  "message": "参数错误",
  "details": {
    "field": "email",
    "error": "邮箱格式不正确"
  }
}
```

### 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 请求成功 |
| 40001 | 请求参数错误 |
| 40101 | 未认证或 Token 无效 |
| 40102 | Token 已过期 |
| 40301 | 权限不足 |
| 40401 | 资源不存在 |
| 40901 | 资源冲突（如重复注册） |
| 42901 | 请求过于频繁 |
| 50001 | 服务器内部错误 |

---

## 1. 用户服务

### 1.1 用户注册

```
POST /auth/register
```

**请求体**：

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "张三",
  "role": "student"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码（8-32 位，需包含字母和数字） |
| name | string | 是 | 用户昵称（2-20 字符） |
| role | string | 否 | 角色（`student`/`teacher`/`admin`，默认 `student`） |

**响应**：

```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "user_id": "u_abc123",
    "email": "user@example.com",
    "name": "张三",
    "role": "student",
    "created_at": "2026-08-09T10:00:00Z"
  }
}
```

### 1.2 用户登录

```
POST /auth/login
```

**请求体**：

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**响应**：

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
      "user_id": "u_abc123",
      "email": "user@example.com",
      "name": "张三",
      "role": "student"
    }
  }
}
```

### 1.3 刷新 Token

```
POST /auth/refresh
```

**请求体**：

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

### 1.4 获取当前用户信息

```
GET /users/me
```

**请求头**: `Authorization: Bearer <token>`

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "u_abc123",
    "email": "user@example.com",
    "name": "张三",
    "avatar_url": "https://cdn.eduflow.example.com/avatars/u_abc123.png",
    "role": "student",
    "bio": "热爱学习的学生",
    "created_at": "2026-08-09T10:00:00Z",
    "stats": {
      "courses_in_progress": 3,
      "courses_completed": 5,
      "total_learning_hours": 120,
      "total_assignments": 45
    }
  }
}
```

### 1.5 更新用户信息

```
PUT /users/me
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "name": "张三丰",
  "bio": "终身学习者",
  "avatar_url": "https://cdn.eduflow.example.com/avatars/new_avatar.png"
}
```

### 1.6 获取用户列表（管理员）

```
GET /users?page=1&page_size=20&role=student&keyword=张三
```

**请求头**: `Authorization: Bearer <token>` (需 admin 角色)

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | string | 否 | 按角色筛选 |
| keyword | string | 否 | 按姓名/邮箱搜索 |
| status | string | 否 | 按状态筛选 (`active`/`disabled`) |

---

## 2. 课程服务

### 2.1 创建课程

```
POST /courses
```

**请求头**: `Authorization: Bearer <token>` (需 teacher 或 admin 角色)

**请求体**：

```json
{
  "title": "Python 入门到精通",
  "description": "从零开始学习 Python 编程语言，涵盖基础语法、数据结构、面向对象编程等核心内容。",
  "category": "programming",
  "tags": ["python", "编程入门", "后端开发"],
  "cover_url": "https://cdn.eduflow.example.com/covers/python_course.png",
  "difficulty": "beginner",
  "price": 199.00,
  "is_published": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 课程标题（2-100 字符） |
| description | string | 是 | 课程描述（10-2000 字符） |
| category | string | 是 | 课程分类 |
| tags | string[] | 否 | 标签列表 |
| cover_url | string | 否 | 封面图片 URL |
| difficulty | string | 是 | 难度 (`beginner`/`intermediate`/`advanced`) |
| price | number | 是 | 价格（元），免费课程设为 0 |
| is_published | boolean | 否 | 是否立即发布 |

### 2.2 获取课程列表

```
GET /courses?page=1&page_size=20&category=programming&difficulty=beginner&keyword=Python
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 否 | 分类筛选 |
| difficulty | string | 否 | 难度筛选 |
| keyword | string | 否 | 搜索关键词 |
| sort_by | string | 否 | 排序方式 (`popular`/`newest`/`rating`) |
| is_free | boolean | 否 | 仅显示免费课程 |

### 2.3 获取课程详情

```
GET /courses/{course_id}
```

### 2.4 更新课程

```
PUT /courses/{course_id}
```

**请求头**: `Authorization: Bearer <token>` (需课程创建者或 admin)

### 2.5 删除课程

```
DELETE /courses/{course_id}
```

**请求头**: `Authorization: Bearer <token>` (需课程创建者或 admin)

### 2.6 课程章节管理

```
# 获取课程章节列表
GET /courses/{course_id}/chapters

# 创建章节
POST /courses/{course_id}/chapters
{
  "title": "第一章：Python 基础",
  "description": "学习 Python 的基本语法和数据类型",
  "sort_order": 1
}

# 更新章节
PUT /courses/{course_id}/chapters/{chapter_id}

# 删除章节
DELETE /courses/{course_id}/chapters/{chapter_id}
```

### 2.7 课时管理

```
# 创建课时
POST /courses/{course_id}/chapters/{chapter_id}/lessons
{
  "title": "1.1 变量和数据类型",
  "type": "video",
  "content": {
    "video_url": "https://cdn.eduflow.example.com/videos/lesson_1_1.mp4",
    "duration": 1800,
    "resources": []
  },
  "sort_order": 1
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 课时类型 (`video`/`document`/`quiz`/`live`) |
| content.video_url | string | 视频地址（视频类型） |
| content.duration | integer | 时长（秒） |
| content.resources | array | 附加资源列表 |

---

## 3. 学习服务

### 3.1 报名课程

```
POST /enrollments
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "course_id": "c_xyz789"
}
```

### 3.2 获取学习进度

```
GET /learning/progress/{course_id}
```

**请求头**: `Authorization: Bearer <token>`

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "course_id": "c_xyz789",
    "course_title": "Python 入门到精通",
    "overall_progress": 35.5,
    "total_lessons": 40,
    "completed_lessons": 14,
    "total_duration": 72000,
    "studied_duration": 25200,
    "last_study_at": "2026-08-09T14:30:00Z",
    "chapters": [
      {
        "chapter_id": "ch_001",
        "title": "第一章：Python 基础",
        "progress": 80,
        "lessons": [
          {
            "lesson_id": "l_001",
            "title": "1.1 变量和数据类型",
            "completed": true,
            "duration": 1800,
            "studied_duration": 1800
          }
        ]
      }
    ]
  }
}
```

### 3.3 更新学习进度

```
POST /learning/progress
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "course_id": "c_xyz789",
  "lesson_id": "l_001",
  "progress": 100,
  "watched_duration": 1800
}
```

### 3.4 获取学习路径

```
GET /learning/path
```

**请求头**: `Authorization: Bearer <token>`

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| goal | string | 否 | 学习目标描述 |
| skill_level | string | 否 | 当前水平 (`beginner`/`intermediate`/`advanced`) |

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "goal": "掌握 Python 全栈开发",
    "estimated_duration": "6 个月",
    "path": [
      {
        "course_id": "c_001",
        "title": "Python 入门到精通",
        "order": 1,
        "estimated_hours": 40,
        "prerequisites": []
      },
      {
        "course_id": "c_002",
        "title": "Web 开发基础",
        "order": 2,
        "estimated_hours": 60,
        "prerequisites": ["c_001"]
      }
    ]
  }
}
```

---

## 4. 评估服务

### 4.1 创建测验

```
POST /assessments/quizzes
```

**请求头**: `Authorization: Bearer <token>` (需 teacher 或 admin)

### 4.2 提交测验答案

```
POST /assessments/quizzes/{quiz_id}/submit
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "answers": [
    {
      "question_id": "q_001",
      "answer": "A"
    },
    {
      "question_id": "q_002",
      "answer": "Python 是一种解释型、面向对象的高级编程语言。"
    }
  ]
}
```

### 4.3 获取测验结果

```
GET /assessments/quizzes/{quiz_id}/results
```

**请求头**: `Authorization: Bearer <token>`

### 4.4 获取作业列表

```
GET /assessments/assignments?course_id={course_id}
```

**请求头**: `Authorization: Bearer <token>`

### 4.5 提交作业

```
POST /assessments/assignments/{assignment_id}/submit
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "content": {
    "text": "这是我的作业答案...",
    "code": "def hello():\n    print('Hello, World!')\n",
    "files": [
      {
        "filename": "main.py",
        "url": "https://cdn.eduflow.example.com/submissions/main.py"
      }
    ]
  }
}
```

---

## 5. AI 智能体服务

### 5.1 智能问答

```
POST /agents/qa/ask
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "course_id": "c_xyz789",
  "question": "Python 中的列表推导式是如何工作的？",
  "context": {
    "current_lesson": "l_005",
    "history": [
      {"role": "user", "content": "什么是 Python 列表？"},
      {"role": "assistant", "content": "列表是 Python 中一种有序、可变的数据集合..."}
    ]
  }
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "列表推导式（List Comprehension）是 Python 中一种简洁的创建列表的方式...",
    "references": [
      {
        "title": "Python 列表推导式",
        "source": "course:chapter_1",
        "relevance": 0.95
      }
    ],
    "related_questions": [
      "字典推导式如何使用？",
      "列表推导式和 map() 函数的区别？"
    ],
    "conversation_id": "conv_abc123"
  }
}
```

### 5.2 继续对话

```
POST /agents/qa/ask
```

**请求体**：

```json
{
  "conversation_id": "conv_abc123",
  "question": "能给我举几个实际的例子吗？"
}
```

### 5.3 获取学习路径规划

```
POST /agents/learning-path/plan
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "goal": "成为一名 Python 全栈工程师",
  "current_level": "beginner",
  "available_hours_per_week": 10,
  "preferred_style": "video",
  "deadline": "2027-02-01"
}
```

### 5.4 提交 AI 批改作业

```
POST /agents/assignment/grade
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "assignment_id": "a_001",
  "student_answer": "def hello():\n    print('Hello, World!')",
  "rubric": {
    "criteria": ["代码正确性", "代码风格", "注释完整性"],
    "max_score": 100
  }
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_score": 85,
    "breakdown": [
      {"criterion": "代码正确性", "score": 40, "max_score": 40, "comment": "代码逻辑正确，功能完整"},
      {"criterion": "代码风格", "score": 30, "max_score": 35, "comment": "建议使用更多类型注解"},
      {"criterion": "注释完整性", "score": 15, "max_score": 25, "comment": "缺少函数文档字符串"}
    ],
    "detailed_feedback": "整体完成度较高...",
    "suggestions": [
      "建议为函数添加 docstring",
      "建议使用类型注解增强代码可读性"
    ],
    "weak_knowledge_points": ["函数文档规范", "类型注解"]
  }
}
```

### 5.5 获取学习分析报告

```
POST /agents/analytics/report
```

**请求头**: `Authorization: Bearer <token>`

**请求体**：

```json
{
  "report_type": "personal",
  "time_range": {
    "start": "2026-07-01",
    "end": "2026-08-09"
  }
}
```

**响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "summary": {
      "total_learning_hours": 45,
      "courses_completed": 2,
      "courses_in_progress": 3,
      "avg_daily_hours": 1.5
    },
    "knowledge_map": {
      "mastered": ["Python 基础语法", "数据结构"],
      "learning": ["面向对象编程", "文件操作"],
      "weak": ["异步编程", "网络编程"]
    },
    "trends": {
      "weekly_hours": [10, 8, 12, 5, 10],
      "completion_rate": [80, 75, 90, 60, 85]
    },
    "recommendations": [
      "建议每天保持 1-2 小时的学习时间",
      "薄弱知识点「异步编程」建议复习"
    ]
  }
}
```

---

## 6. 通知服务

### 6.1 获取通知列表

```
GET /notifications?page=1&page_size=20&type=system&unread_only=true
```

**请求头**: `Authorization: Bearer <token>`

### 6.2 标记通知已读

```
PUT /notifications/{notification_id}/read
```

### 6.3 标记全部已读

```
PUT /notifications/read-all
```

---

## 7. 搜索服务

### 7.1 全局搜索

```
GET /search?q=Python&type=course&page=1&page_size=20
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| type | string | 否 | 搜索类型 (`course`/`lesson`/`user`/`all`) |
| sort | string | 否 | 排序方式 (`relevance`/`rating`/`date`) |

---

## 8. 健康检查

### 8.1 服务健康状态

```
GET /health
```

**响应**：

```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2026-08-09T12:00:00Z",
  "services": {
    "database": "ok",
    "redis": "ok",
    "rabbitmq": "ok",
    "milvus": "ok",
    "llm": "ok"
  }
}
```

---

## API 速率限制

| 接口分类 | 限制 | 说明 |
|----------|------|------|
| 通用 API | 100 次/分钟 | 按用户 ID 限制 |
| AI 智能体 API | 20 次/分钟 | 按用户 ID 限制 |
| 认证 API | 5 次/分钟 | 按 IP 限制 |
| 搜索 API | 30 次/分钟 | 按用户 ID 限制 |

超出限制时返回 `429 Too Many Requests`。

---

> 完整 API 文档请参考 OpenAPI 规范文件：`docs/api-spec/openapi.yaml`。