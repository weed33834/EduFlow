# EduFlow 重构方案：从 LMS 平台到编程学习 Agent

> **文档版本**：v1.0  
> **日期**：2026-08-21  
> **作者**：Simona  
> **状态**：待审批  

---

## 一、现状诊断摘要

EduFlow 现在是一个"AI 驱动的学生自学平台"，实际做的是 LMS CRUD + AI API 代理的缝合体。核心问题：

| 问题 | 严重度 | 说明 |
|---|---|---|
| 产品定位模糊 | 致命 | 什么都有但什么都不精，对标 Anki/Khan/ChatGPT 全面落败 |
| Agent 是假的 | 致命 | 四个"Agent"只是 prompt 包装的 API 调用，无记忆/无工具/无自主决策 |
| 三微服务过度拆分 | 高 | Engine 只有 100 行代码却独立服务，API 网关纯代理 |
| N+1 查询 | 高 | progress 和 conversations 每条记录 2 次查询 |
| 前端 6 页面无引导 | 中 | 用户不知道该做什么，每个页面都是空状态 |
| 多媒体功能半成品 | 中 | TTS/文生图/讲解视频全是代理转发，核心闭环未验证就加 |
| 依赖版本不统一 | 低 | 三个服务用三个版本的 FastAPI/Pydantic |
| 测试覆盖不足 | 中 | AI 和 Engine 零测试，前端零测试 |

**结论**：项目作为"平台"没有前景。砍掉 80% 功能，把剩下的 20% 做深做透，转型为垂直领域的编程学习 Agent。

---

## 二、产品重定位

### 2.1 一句话定义

**EduFlow Agent — 一个会教编程、会出题、会判题、会排复习的 AI 学习伙伴。**

不是平台，不是工具箱，不是 LMS。就是一个 Agent，学生跟它对话，它在背后做所有事。

### 2.2 核心差异化

| 能力 | ChatGPT 做不到 | EduFlow Agent 做得到 |
|---|---|---|
| 代码沙箱执行 | 学生写代码→Agent 执行→读输出→给反馈 | ✅ E2B/Judge0 沙箱 |
| 自适应出题 | 根据学生掌握度和薄弱点动态出题 | ✅ FSRS + LLM |
| 间隔重复 | 主动安排复习，遗忘曲线追踪 | ✅ FSRS-4.5 |
| 长期记忆 | 记住学生画像、常犯错误、学习偏好 | ✅ Mem0 / 自建 |
| 知识库引用 | 讲解有据可依，不是凭空生成 | ✅ Qdrant RAG |

### 2.3 产品形态变化

```
现在（平台模式）：
  注册 → 空仪表盘 → 自己建路径 → 自己加模块 → 自己去做题 → 自己去复习
  
改为（Agent 模式）：
  打开 → 告诉 Agent "我想学 Python" → 
  Agent 自主规划 → Agent 教你 → Agent 出题 → 
  你写代码 → Agent 执行判题 → Agent 给反馈 → 
  Agent 安排复习 → Agent 主动推送
```

**从"学生管理学习"变成"Agent 管理学习，学生只管学"。**

### 2.4 目标用户

- **核心**：零基础到中级编程学习者（Python 为主）
- **场景**：自学、课后练习、面试准备
- **不做**：K12 少儿（需要数字人/游戏化，不是 MVP 阶段的事）

---

## 三、核心架构设计

### 3.1 架构总览

```
                    ┌─────────────────────────────────┐
                    │         Next.js 前端（单页）      │
                    │  对话界面 + 代码编辑器 + 复习卡片  │
                    └──────────────┬──────────────────┘
                                   │ SSE 流式
                    ┌──────────────▼──────────────────┐
                    │      FastAPI 后端（单服务）       │
                    │                                  │
                    │  ┌─────────────────────────────┐ │
                    │  │   LangGraph StateGraph       │ │
                    │  │   (Agent 编排核心)             │ │
                    │  └────────┬────────────────────┘ │
                    │           │                      │
                    │  ┌────────┼────────────────────┐ │
                    │  │        工具层                 │ │
                    │  │  LLM  沙箱  RAG  FSRS  记忆  │ │
                    │  └─────────────────────────────┘ │
                    │                                  │
                    │  PostgreSQL  Qdrant  Redis       │
                    └──────────────────────────────────┘
```

**从三微服务（API + AI + Engine）合并为单一服务。** 去掉代理层、去掉 Engine 独立服务、去掉 monorepo。

### 3.2 Agent 状态机（LangGraph StateGraph）

这是整个系统的核心。Agent 不是一个 prompt 包装的 API 调用，而是一个有状态、有记忆、能自主决策的状态机。

#### 状态定义

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    # 输入
    user_message: str                    # 学生当前消息
    user_id: int
    session_id: int
    
    # 中间状态
    intent: str                          # 意图标签
    student_profile: dict                # 学生画像
    recalled_knowledge: list[dict]      # 检索到的相关知识
    due_reviews: list[dict]              # 到期复习项
    action_plan: str                      # 决策的行动方案
    
    # 工具执行结果
    teach_content: str                   # 讲解内容
    quiz_question: dict                  # 出的题目
    code_result: dict                    # 代码执行结果
    review_result: dict                  # 复习结果
    
    # 输出
    response_chunks: list[str]           # 流式回复片段
    memory_updates: list[dict]           # 记忆更新
```

#### 状态转移图

```
                         ┌──────────────┐
                         │  understand  │  ← 学生消息 → 意图分类
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │    recall    │  ← 检索记忆 + 知识库 + FSRS
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │     plan     │  ← LLM 决策下一步做什么
                         └──┬──┬──┬──┬───┘
                            │  │  │  │
          ┌─────────────────┘  │  │  └─────────────────┐
          │            ┌───────┘  └────────┐            │
          ▼            ▼                    ▼            ▼
    ┌──────────┐ ┌──────────┐      ┌──────────┐  ┌──────────┐
    │  teach   │ │   quiz   │      │   code   │  │  review  │
    │ 讲解概念  │ │ 出题测试  │      │ 代码练习  │  │ 间隔重复  │
    └────┬─────┘ └────┬─────┘      └────┬─────┘  └────┬─────┘
         │            │                 │              │
         └────────────┴────────────────┴──────────────┘
                                │
                         ┌──────▼───────┐
                         │   reflect    │  ← 提取记忆 + 更新画像 + FSRS
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │   respond    │  ← 组织流式回复
                         └──────────────┘
```

#### 各状态详解

**1. `understand` — 理解意图**

```python
async def understand(state: AgentState) -> AgentState:
    """用 LLM 对学生消息做意图分类。
    
    输出 intent 标签：
    - learn_concept: 学新概念（"什么是递归"）
    - practice: 想练习（"给我出几道题"）
    - write_code: 想写代码（"我想写个函数试试"）
    - review: 到了复习时间（由 FSRS 触发）
    - ask_question: 答疑（"为什么这里报错"）
    - chitchat: 闲聊（"你好"）
    """
    prompt = f"""判断学生意图，只返回标签：
    learn_concept / practice / write_code / review / ask_question / chitchat
    
    学生消息：{state['user_message']}
    学生当前水平：{state['student_profile'].get('current_level', 'beginner')}
    """
    intent = await llm.classify(prompt)
    return {**state, "intent": intent}
```

**2. `recall` — 检索记忆和知识**

```python
async def recall(state: AgentState) -> AgentState:
    """三路并行检索：
    1. 向量检索知识库（Qdrant）— 找相关知识点
    2. 记忆检索（student_profile + memory_facts）— 找学生画像
    3. FSRS 查询 — 找到期复习项
    """
    # 并行执行
    knowledge, profile, reviews = await asyncio.gather(
        qdrant.search(state['user_message'], top_k=4),
        get_student_profile(state['user_id']),
        get_due_reviews(state['user_id']),
    )
    return {
        **state,
        "recalled_knowledge": knowledge,
        "student_profile": profile,
        "due_reviews": reviews,
    }
```

**3. `plan` — 决策**

```python
async def plan(state: AgentState) -> AgentState:
    """LLM 基于 intent + recall 结果，决定下一步行动。
    
    决策规则（LLM 辅助，但有硬编码兜底）：
    - learn_concept → teach
    - practice → quiz
    - write_code → code
    - review → review（如果有 due_items）否则 quiz
    - ask_question → teach（针对性讲解）
    - chitchat → respond（直接回复）
    """
    # 如果意图明确且不需要 LLM 决策，直接路由
    route_map = {
        "learn_concept": "teach",
        "practice": "quiz",
        "write_code": "code",
        "ask_question": "teach",
        "chitchat": "respond",
    }
    if state['intent'] in route_map:
        return {**state, "action_plan": route_map[state['intent']]}
    
    # review 意图需要判断是否有到期项
    if state['intent'] == 'review':
        if state.get('due_reviews'):
            return {**state, "action_plan": "review"}
        return {**state, "action_plan": "quiz"}
    
    return {**state, "action_plan": "teach"}
```

**4. `teach` — 讲解**

```python
async def teach(state: AgentState) -> AgentState:
    """生成概念讲解，带知识库引用和代码示例。
    
    工具：
    - LLM 生成讲解（注入 recalled_knowledge 作为上下文）
    - 可选：沙箱执行代码示例验证正确性
    """
    knowledge_ctx = format_knowledge(state['recalled_knowledge'])
    prompt = f"""讲解以下概念，要求：
    1. 适合 {state['student_profile']['current_level']} 水平的学生
    2. 用代码示例说明
    3. 引用知识库内容（如果有）
    4. 简洁，不超过 300 字
    
    概念：{state['user_message']}
    
    相关知识库：
    {knowledge_ctx}
    """
    content = await llm.generate(prompt, stream=True)
    return {**state, "teach_content": content}
```

**5. `quiz` — 出题**

```python
async def quiz(state: AgentState) -> AgentState:
    """根据学生水平和薄弱点出题。
    
    工具：
    - LLM 生成题目（注入 weaknesses 作为重点）
    - 题目格式：{question, options, answer_index, explanation, difficulty}
    """
    weaknesses = state['student_profile'].get('weaknesses', [])
    prompt = f"""出 1 道选择题，要求：
    1. 难度匹配 {state['student_profile']['current_level']} 水平
    2. 重点考察薄弱点：{weaknesses or '综合能力'}
    3. 4 个选项，answer 是正确选项的索引（0-3）
    4. 附带详细解析
    
    返回 JSON：{{question, options, answer, explanation, difficulty}}
    """
    question = await llm.generate_json(prompt)
    return {**state, "quiz_question": question}
```

**6. `code` — 代码练习**

```python
async def code(state: AgentState) -> AgentState:
    """学生写代码 → 沙箱执行 → Agent 读输出 → 给反馈。
    
    工具：
    - E2B 沙箱执行学生代码
    - LLM 分析执行结果并给反馈
    """
    # 从学生消息中提取代码
    code = extract_code(state['user_message'])
    if not code:
        # Agent 先出一道编程题
        prompt = "出一道适合当前水平的 Python 编程题，返回题目描述"
        challenge = await llm.generate(prompt)
        return {**state, "code_result": {"challenge": challenge, "awaiting_code": True}}
    
    # 执行代码
    result = await sandbox.run(code, language="python", timeout=10)
    
    # LLM 分析结果
    analysis = await llm.generate(f"""
    学生代码执行结果：
    stdout: {result.stdout}
    stderr: {result.stderr}
    exit_code: {result.exit_code}
    
    请给出反馈：是否正确？有什么问题？如何改进？
    """)
    
    return {**state, "code_result": {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "feedback": analysis,
    }}
```

**7. `review` — 间隔重复**

```python
async def review(state: AgentState) -> AgentState:
    """FSRS 间隔重复复习。
    
    工具：
    - FSRS 取到期知识点
    - LLM 生成复习题
    - 学生作答后更新 FSRS 参数
    """
    due = state.get('due_reviews', [])
    if not due:
        return {**state, "review_result": {"no_due": True}}
    
    item = due[0]  # 最紧急的
    prompt = f"""针对知识点「{item['topic']}」出一道复习题。
    掌握度：{item['mastery_level']}
    已复习次数：{item['review_count']}
    
    返回 JSON：{{question, options, answer, explanation}}
    """
    question = await llm.generate_json(prompt)
    return {**state, "review_result": {
        "topic": item['topic'],
        "question": question,
        "knowledge_item_id": item['id'],
    }}
```

**8. `reflect` — 反思与记忆更新**

```python
async def reflect(state: AgentState) -> AgentState:
    """从本次交互中提取记忆事实，更新学生画像。
    
    工具：
    - LLM 提取记忆事实（"学生混淆了 list 和 tuple"）
    - 更新 student_profile（weaknesses/strengths）
    - 如果有 quiz/code 结果，更新 FSRS 参数
    """
    # 提取记忆事实
    facts = await llm.generate_json(f"""
    从以下交互中提取学生的记忆事实：
    学生消息：{state['user_message']}
    Agent 回复：{state.get('teach_content', '')}
    测验结果：{state.get('quiz_question', {})}
    代码结果：{state.get('code_result', {})}
    
    返回 JSON 数组：[{{fact, category}}]
    category: weakness/strength/preference/progress
    """)
    
    # 持久化记忆
    for f in facts:
        await save_memory_fact(state['user_id'], f)
    
    # 更新 FSRS（如果有测验结果）
    if state.get('quiz_question') and state.get('quiz_question', {}).get('student_answer'):
        await update_fsrs(
            state['quiz_question']['knowledge_item_id'],
            state['quiz_question']['is_correct']
        )
    
    return {**state, "memory_updates": facts}
```

**9. `respond` — 组织回复**

```python
async def respond(state: AgentState) -> AgentState:
    """把各工具的结果组织成流式回复。
    
    优先级：
    1. 如果有 teach_content → 直接流式输出讲解
    2. 如果有 quiz_question → 输出题目卡片
    3. 如果有 code_result → 输出执行结果 + 反馈
    4. 如果有 review_result → 输出复习题
    5. 如果都没有 → LLM 生成通用回复
    """
    chunks = []
    if state.get('teach_content'):
        chunks.append(state['teach_content'])
    elif state.get('quiz_question'):
        chunks.append(format_quiz(state['quiz_question']))
    elif state.get('code_result'):
        chunks.append(format_code_result(state['code_result']))
    elif state.get('review_result'):
        chunks.append(format_review(state['review_result']))
    else:
        # 通用回复
        reply = await llm.generate(state['user_message'], stream=True)
        chunks.append(reply)
    
    return {**state, "response_chunks": chunks}
```

#### StateGraph 构建

```python
from langgraph.graph import StateGraph, END

def build_agent_graph():
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("understand", understand)
    graph.add_node("recall", recall)
    graph.add_node("plan", plan)
    graph.add_node("teach", teach)
    graph.add_node("quiz", quiz)
    graph.add_node("code", code)
    graph.add_node("review", review)
    graph.add_node("reflect", reflect)
    graph.add_node("respond", respond)
    
    # 固定边
    graph.set_entry_point("understand")
    graph.add_edge("understand", "recall")
    graph.add_edge("recall", "plan")
    
    # 条件路由（plan → teach/quiz/code/review/respond）
    graph.add_conditional_edges("plan", lambda s: s["action_plan"], {
        "teach": "teach",
        "quiz": "quiz",
        "code": "code",
        "review": "review",
        "respond": "respond",
    })
    
    # 所有工具节点 → reflect → respond → END
    for node in ["teach", "quiz", "code", "review"]:
        graph.add_edge(node, "reflect")
    graph.add_edge("reflect", "respond")
    graph.add_edge("respond", END)
    
    return graph.compile()
```

### 3.3 工具定义

Agent 可调用的工具，用 LangGraph 的 tool calling 或手动注入：

| 工具名 | 用途 | 实现 | 降级方案 |
|---|---|---|---|
| `llm_generate` | 生成文本 | LiteLLM 统一接口 | 返回模板文本 |
| `llm_classify` | 意图分类 | LiteLLM + JSON 输出 | 关键词匹配 |
| `llm_generate_json` | 生成结构化 JSON | LiteLLM + response_format | 正则提取 JSON |
| `sandbox_run` | 执行学生代码 | E2B API | 返回"沙箱不可用"提示 |
| `qdrant_search` | 检索知识库 | Qdrant API | 返回空列表 |
| `get_student_profile` | 读取学生画像 | PostgreSQL 查询 | 返回默认画像 |
| `get_due_reviews` | 查到期复习项 | PostgreSQL + FSRS 查询 | 返回空列表 |
| `save_memory_fact` | 存记忆事实 | PostgreSQL INSERT | 忽略错误 |
| `update_fsrs` | 更新 FSRS 参数 | FSRS-4.5 算法 | 跳过更新 |

---

## 四、数据模型

### 4.1 表结构设计

```sql
-- 用户（保留 EduFlow 的 user 表，改用 SQLAlchemy 2.0 Mapped 风格）
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    bio         TEXT,
    avatar_url  VARCHAR(500),
    password_hash VARCHAR(255) NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 学生画像（Agent 自动维护，学生不直接编辑）
CREATE TABLE student_profiles (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    current_level   VARCHAR(20) DEFAULT 'beginner',  -- beginner/intermediate/advanced
    learning_goal   TEXT,                              -- "我想学 Python 编程"
    preferred_style VARCHAR(50) DEFAULT 'text',       -- text/visual/practice
    strengths       JSONB DEFAULT '[]'::jsonb,        -- ["list操作", "基本语法"]
    weaknesses      JSONB DEFAULT '[]'::jsonb,        -- ["递归", "面向对象"]
    total_study_minutes INTEGER DEFAULT 0,
    streak_days     INTEGER DEFAULT 0,
    last_active_at  TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 学习会话（一次对话 = 一个会话）
CREATE TABLE sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    started_at      TIMESTAMP DEFAULT NOW(),
    ended_at        TIMESTAMP,
    summary         TEXT,                              -- Agent 自动生成的会话总结
    topics_covered  JSONB DEFAULT '[]'::jsonb,        -- 本次会话涉及的知识点
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 消息
CREATE TABLE messages (
    id          SERIAL PRIMARY KEY,
    session_id  INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL,                -- user / assistant
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}'::jsonb,           -- {agent_state, tools_used, ...}
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_messages_session ON messages(session_id);

-- 知识点（FSRS 追踪）
CREATE TABLE knowledge_items (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    topic           VARCHAR(200) NOT NULL,           -- "Python 列表可变性"
    stability       REAL DEFAULT 0,                  -- FSRS stability
    difficulty      REAL DEFAULT 0.3,                 -- FSRS difficulty
    last_reviewed_at TIMESTAMP,
    next_review_at  TIMESTAMP,
    review_count    INTEGER DEFAULT 0,
    mastery_level   REAL DEFAULT 0,                   -- 0.0 ~ 1.0
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_knowledge_user ON knowledge_items(user_id);
CREATE INDEX idx_knowledge_due ON knowledge_items(user_id, next_review_at);

-- 代码提交
CREATE TABLE code_submissions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id      INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    challenge       TEXT,                              -- Agent 给的编程题
    code            TEXT NOT NULL,                     -- 学生写的代码
    language        VARCHAR(20) DEFAULT 'python',
    stdout          TEXT,
    stderr          TEXT,
    exit_code       INTEGER,
    agent_feedback  TEXT,                              -- Agent 的反馈
    is_correct      BOOLEAN,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_code_user ON code_submissions(user_id);

-- 测验结果
CREATE TABLE quiz_results (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id          INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    question            TEXT NOT NULL,
    options             JSONB NOT NULL,
    answer_index        INTEGER NOT NULL,
    student_answer      INTEGER,
    is_correct          BOOLEAN,
    explanation         TEXT,
    difficulty          VARCHAR(20),
    knowledge_item_id   INTEGER REFERENCES knowledge_items(id) ON DELETE SET NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_quiz_user ON quiz_results(user_id);

-- 长期记忆事实（Mem0 风格）
CREATE TABLE memory_facts (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    fact        TEXT NOT NULL,                         -- "学生经常混淆 list 和 tuple 的可变性"
    category    VARCHAR(50) NOT NULL,                  -- weakness/strength/preference/progress
    confidence  REAL DEFAULT 1.0,
    created_at   TIMESTAMP DEFAULT NOW(),
    updated_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_memory_user ON memory_facts(user_id);
CREATE INDEX idx_memory_category ON memory_facts(user_id, category);
```

### 4.2 与 EduFlow 旧模型对比

| 旧表 | 新表 | 变化 |
|---|---|---|
| users | users | 保留，加 Mapped 改造 |
| learning_paths | **删除** | Agent 自己规划，不需要 CRUD |
| modules | **删除** | 同上 |
| practice_sessions | sessions + quiz_results | 拆分：会话归会话，题目归题目 |
| progress_records | student_profiles + memory_facts | 从"进度记录"变成"学生画像" |
| review_items | knowledge_items | 保留 FSRS 思路，字段更完整 |
| conversations | sessions | 重命名，加 summary |
| conversation_messages | messages | 重命名，加 metadata |

---

## 五、API 设计

### 5.1 核心接口

```
# 对话（SSE 流式）
POST /api/chat
  请求体：{ message: string, session_id?: int }
  响应：SSE 流
    data: {"type": "thinking", "content": "正在思考..."}
    data: {"type": "teach", "content": "递归是指..."}
    data: {"type": "quiz", "content": {"question": "...", "options": [...], "answer": 0}}
    data: {"type": "code", "content": {"stdout": "...", "stderr": "...", "feedback": "..."}}
    data: {"type": "review", "content": {"topic": "...", "question": {...}}}
    data: {"type": "done"}

# 测验答题
POST /api/quiz/answer
  请求体：{ session_id: int, question: string, answer: int }
  响应：{ is_correct: bool, explanation: string, knowledge_item_id: int }

# 代码执行
POST /api/code/run
  请求体：{ code: string, language: string, session_id?: int }
  响应：{ stdout: string, stderr: string, exit_code: int, feedback: string }

# 会话管理
GET  /api/sessions                          → { sessions: [...] }
GET  /api/sessions/:id                      → { session, messages: [...] }
DELETE /api/sessions/:id                    → { ok: bool }

# 学生画像
GET  /api/profile                           → { profile, stats }

# 复习
GET  /api/review/due                        → { due_count, items: [...] }

# 认证（保留 EduFlow 原有接口）
POST /api/auth/register                     → { access_token, user }
POST /api/auth/login                        → { access_token, user }
GET  /api/auth/me                           → { user }
PUT  /api/auth/me                           → { user }

# 健康检查
GET  /api/health                            → { status: "ok" }
```

### 5.2 与 EduFlow 旧 API 对比

| 旧接口 | 新接口 | 变化 |
|---|---|---|
| POST /api/ai/chat/stream | POST /api/chat | 从"代理转发"变成"Agent 状态机" |
| POST /api/ai/generate-questions | 内嵌到 /api/chat | 不单独暴露，Agent 自己出题 |
| POST /api/ai/explain | 内嵌到 /api/chat | 同上 |
| POST /api/ai/evaluate | POST /api/quiz/answer | 答题接口独立 |
| POST /api/ai/plan | 内嵌到 /api/chat | Agent 自己规划 |
| GET /api/learning/paths | **删除** | 不需要 |
| POST /api/learning/paths | **删除** | 不需要 |
| GET /api/practice/sessions | GET /api/sessions | 重命名 |
| POST /api/practice/submit | POST /api/quiz/answer | 重构 |
| GET /api/progress/overview | GET /api/profile | 从"进度"变成"画像" |
| GET /api/review/due | GET /api/review/due | 保留 |
| GET /api/conversations | GET /api/sessions | 重命名 |

---

## 六、前端设计

### 6.1 页面结构

**只有两个页面**（外加认证页）：

```
/               → 落地页（介绍 + 登录/注册入口）
/login          → 登录
/register       → 注册
/chat           → 主界面（Agent 对话 + 代码编辑器 + 复习卡片）
```

### 6.2 主界面布局

```
┌──────────────────────────────────────────────────────┐
│  EduFlow Agent                  [设置] [退出]       │
├────────────┬─────────────────────────────────────────┤
│            │                                          │
│  会话列表   │  对话区域                                 │
│            │                                          │
│  > 新对话   │  ┌─────────────────────────────────┐    │
│            │  │ Agent: 你好！你想学什么？         │    │
│  历史1     │  └─────────────────────────────────┘    │
│  历史2     │  ┌─────────────────────────────────┐    │
│  历史3     │  │ You: 我想学 Python 递归          │    │
│            │  └─────────────────────────────────┘    │
│  复习提醒   │  ┌─────────────────────────────────┐    │
│  3项待复习  │  │ Agent: 好的！递归是指...         │    │
│  [去复习]  │  │ [代码块] def factorial(n): ...  │    │
│            │  │ [选择题] 下列哪个是递归的...     │    │
│            │  └─────────────────────────────────┘    │
│            │                                          │
│            │  ┌─────────────────────────────────┐    │
│            │  │ [输入框] 说点什么...    [发送]   │    │
│            │  │ [代码模式切换]                  │    │
│            │  └─────────────────────────────────┘    │
└────────────┴──────────────────────────────────────────┘
```

### 6.3 对话中嵌入的组件

| 组件 | 触发条件 | 交互 |
|---|---|---|
| 代码块 | Agent teach/code | 高亮 + 运行按钮 |
| 选择题卡片 | Agent quiz/review | 4 选项 + 提交 + 解析 |
| 代码编辑器 | Agent code | Monaco Editor + 运行按钮 |
| 复习提醒 | 侧边栏 | 到期数量 + 点击开始 |
| 反馈卡片 | reflect 之后 | 掌握度变化 + 鼓励 |

### 6.4 技术选型

- **框架**：Next.js 14（App Router）
- **数据获取**：SWR（缓存 + 乐观更新）
- **代码编辑器**：Monaco Editor（@monaco-editor/react）
- **Markdown 渲染**：react-markdown + rehype-highlight
- **样式**：Tailwind CSS（保留现有配置）
- **图标**：lucide-react（保留）

---

## 七、技术选型

### 7.1 后端

| 组件 | 选型 | 版本 | 理由 |
|---|---|---|---|
| Web 框架 | FastAPI | 0.115+ | 保留，统一版本 |
| Agent 编排 | LangGraph | 0.2+ | 真正用 StateGraph，不只是引入 |
| LLM 统一接口 | LiteLLM | 1.40+ | 一个接口切换所有模型 |
| ORM | SQLAlchemy 2.0 | 2.0+ | 用 Mapped 风格，不用旧式 Column |
| 数据库 | PostgreSQL | 16 | 带 pgvector 扩展 |
| 迁移 | Alembic | 1.13+ | 保留 |
| 代码沙箱 | E2B | latest | MVP 用云端，免部署 |
| 向量数据库 | Qdrant | 1.12+ | 开源，Rust 写，性能强 |
| 记忆层 | 自建（memory_facts 表） | — | MVP 阶段自建足够，不用 Mem0 |
| 缓存/队列 | Redis | 7+ | 限流 + 异步任务 |
| 认证 | python-jose + bcrypt | 保留 | 保留 EduFlow 原有方案 |

### 7.2 前端

| 组件 | 选型 | 理由 |
|---|---|---|
| 框架 | Next.js 14 | 保留 |
| 数据获取 | SWR | 替代手动 useEffect |
| 代码编辑器 | Monaco Editor | 编程学习必备 |
| Markdown | react-markdown + rehype-highlight | Agent 回复含代码 |
| 样式 | Tailwind CSS | 保留 |
| 图标 | lucide-react | 保留 |

### 7.3 不选什么

| 不选 | 理由 |
|---|---|
| Mem0 | MVP 阶段自建 memory_facts 表足够 |
| Celery | MVP 不需要异步任务队列，复习提醒用定时查询 |
| Whisper/FunASR | 不做语音输入 |
| 数字人 | 编程学习场景 ROI 低 |
| TTS | 不做语音输出 |
| docker-compose 多服务 | 单服务用单 Dockerfile |

---

## 八、从 EduFlow 迁移策略

### 8.1 保留（直接搬过来）

| 文件 | 保留内容 | 需要改造 |
|---|---|---|
| `services/api/core/security.py` | bcrypt + JWT | 缩短 token 有效期到 1 天，加 refresh token |
| `services/api/core/config.py` | Settings 基础结构 | 加新配置项（E2B/Qdrant/LiteLLM） |
| `services/api/core/deps.py` | get_current_user 依赖 | 保留 |
| `services/api/models/user.py` | User 模型 | 改用 Mapped 风格 |
| `services/api/routers/auth.py` | 认证路由 | 保留，加 refresh token |
| `apps/web/src/contexts/AuthContext.tsx` | 认证上下文 | 保留 |
| `apps/web/src/components/layout/RouteGuard.tsx` | 路由守卫 | 保留 |
| `apps/web/tailwind.config.js` | Tailwind 配置 | 保留 |
| `apps/web/src/lib/utils.ts` | 工具函数 | 保留 |

### 8.2 砍掉（直接删除）

```
services/engine/                    ← 整个目录，合并到后端
services/ai/agents/                ← 重写为 LangGraph
services/ai/core/capabilities.py   ← 不需要多模态探测
services/ai/core/media.py          ← 不需要 TTS/文生图
services/ai/core/model_config.py  ← 改用 LiteLLM
services/ai/agents/presenter.py   ← 不需要讲解视频
services/api/routers/learning.py  ← 不需要学习路径 CRUD
services/api/routers/practice.py  ← 重写
services/api/routers/progress.py  ← 不需要
services/api/routers/engine.py    ← 不需要
services/api/routers/ai.py        ← 重写
services/api/models/learning.py   ← 删除
services/api/models/conversation.py ← 重写
packages/                          ← 整个目录，不用 monorepo
apps/web/src/app/dashboard/       ← 砍
apps/web/src/app/learning/        ← 砍
apps/web/src/app/practice/        ← 砍
apps/web/src/app/review/          ← 砍
apps/web/src/app/progress/        ← 砍
apps/web/src/app/settings/        ← 简化为 /chat 内弹窗
apps/web/src/app/ai-tutor/        ← 重写为 /chat
apps/web/src/app/ai-buddy/        ← 砍
apps/web/src/app/ai/              ← 砍
apps/web/src/app/presentation/   ← 砍
docker/docker-compose.yml         ← 重写为单服务
```

### 8.3 重写

| 模块 | 旧实现 | 新实现 |
|---|---|---|
| Agent 核心 | prompt 包装的 API 调用 | LangGraph StateGraph 状态机 |
| LLM 接入 | 直连 OpenAI SDK | LiteLLM 统一接口 |
| 数据模型 | CRUD 表（learning_paths, modules...） | Agent 原生表（sessions, knowledge_items, memory_facts...） |
| API | REST CRUD（10+ 路由） | 对话接口 + 少量辅助接口（6 个路由） |
| 前端 | 6 个页面 | 1 个对话页 |
| FSRS | 10 行启发式 | FSRS-4.5 完整实现 |
| 代码沙箱 | 无 | E2B 集成 |
| 知识库 | 空壳 rag.py | Qdrant + LlamaIndex |

---

## 九、MVP 开发计划

### v0.1.0 — 最小对话闭环（第 1-2 周）

**目标**：学生能跟 Agent 对话，Agent 能教概念和出选择题。

**交付物**：
- [ ] 单后端服务（FastAPI，合并三服务）
- [ ] LangGraph StateGraph（understand → recall → plan → teach/quiz → respond）
- [ ] LiteLLM 接入（支持 OpenAI 兼容端点）
- [ ] 基础数据模型（users, sessions, messages, student_profiles）
- [ ] SSE 流式对话接口（POST /api/chat）
- [ ] 认证接口（保留 EduFlow 的 register/login/me）
- [ ] 前端单页对话界面（/chat）
- [ ] 基础学生画像（current_level, learning_goal）
- [ ] 对话历史持久化

**验收标准**：
1. 学生注册 → 登录 → 进入对话页
2. 学生说"我想学 Python 递归" → Agent 回复讲解
3. 学生说"给我出道题" → Agent 出选择题
4. 学生答题 → Agent 判断对错 + 给解析
5. 对话历史保存，刷新后不丢失
6. 无 API Key 时降级为模板回复

**技术约束**：
- 暂不接 E2B/Qdrant/FSRS
- recall 节点返回空（不检索知识库）
- reflect 节点只保存对话历史
- 前端不用 Monaco，普通输入框

---

### v0.2.0 — 代码沙箱（第 3 周）

**目标**：学生能写代码，Agent 能执行并给反馈。

**交付物**：
- [ ] E2B SDK 集成
- [ ] Agent 状态机新增 `code` 节点
- [ ] POST /api/code/run 接口
- [ ] code_submissions 表
- [ ] 前端 Monaco Editor 集成
- [ ] 对话中代码块高亮 + 运行按钮
- [ ] Agent 能从学生消息中提取代码

**验收标准**：
1. 学生说"我想写代码试试" → Agent 出编程题
2. 学生在代码编辑器写代码 → 点击运行
3. Agent 执行代码 → 返回 stdout/stderr
4. Agent 分析输出 → 给反馈
5. 代码提交记录持久化

---

### v0.3.0 — 间隔重复（第 4 周）

**目标**：Agent 能追踪知识点掌握度，主动安排复习。

**交付物**：
- [ ] FSRS-4.5 完整实现（stability/difficulty/retrievability）
- [ ] knowledge_items 表
- [ ] quiz_results 表关联 knowledge_items
- [ ] Agent 状态机新增 `review` 节点
- [ ] GET /api/review/due 接口
- [ ] 前端侧边栏复习提醒组件
- [ ] reflect 节点更新 FSRS 参数
- [ ] Agent 主动提示"你有 3 个知识点需要复习"

**验收标准**：
1. 学生做选择题 → 自动创建 knowledge_item
2. 学生答对 → FSRS 延长下次复习间隔
3. 学生答错 → FSRS 缩短间隔
4. 到期复习项出现在侧边栏
5. 学生点击"去复习" → Agent 出复习题
6. 复习后掌握度更新

---

### v0.4.0 — 知识库 RAG（第 5 周）

**目标**：Agent 讲解时引用知识库，不是凭空生成。

**交付物**：
- [ ] Qdrant 部署 + Python SDK
- [ ] 知识库灌入脚本（教材/文档 → 分块 → embedding → Qdrant）
- [ ] recall 节点接入 Qdrant 检索
- [ ] teach 节点注入知识库上下文
- [ ] Agent 回复中标注引用来源
- [ ] 基础 Python 教材库（至少 50 个知识点）

**验收标准**：
1. 学生问"什么是列表推导式" → Agent 回复引用知识库
2. 回复中包含"📚 来源：Python 基础教程 > 列表推导式"
3. 知识库未命中时 → Agent 用 LLM 知识回复（标注"AI 生成"）
4. 检索延迟 < 200ms

---

### v0.5.0 — 长期记忆（第 6 周）

**目标**：Agent 记住学生画像，个性化教学。

**交付物**：
- [ ] memory_facts 表
- [ ] reflect 节点用 LLM 提取记忆事实
- [ ] student_profiles 自动更新（strengths/weaknesses）
- [ ] recall 节点注入学生画像和记忆事实
- [ ] Agent 出题时优先考察 weaknesses
- [ ] Agent 讲解时根据 preferred_style 调整风格
- [ ] GET /api/profile 接口
- [ ] 前端"我的学习画像"面板

**验收标准**：
1. 学生多次答错递归题 → Agent 记住"递归是薄弱点"
2. 下次学生来 → Agent 主动说"上次递归有点困难，要不要再练练？"
3. Agent 出题时优先出递归题
4. 学生画像页显示 strengths/weaknesses
5. 记忆事实可删除（学生说"我已经掌握了"）

---

### v0.6.0 — 前端打磨（第 7 周）

**目标**：生产级别的对话体验。

**交付物**：
- [ ] 流式输出优化（打字机效果 + 代码块实时高亮）
- [ ] 移动端适配（响应式布局）
- [ ] 对话搜索（搜索历史消息）
- [ ] 会话重命名 + 删除
- [ ] 代码编辑器语法补全
- [ ] 选择题动画反馈
- [ ] 深色模式
- [ ] 加载状态骨架屏
- [ ] Error Boundary + 统一错误处理

**验收标准**：
1. 移动端对话体验流畅
2. 流式输出无闪烁
3. 代码块可复制
4. 选中题答对/答错有动画
5. 深色模式切换正常
6. 网络断开有友好提示

---

## 十、项目结构

```
eduflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py             # Settings
│   │   ├── database.py           # AsyncEngine + Session
│   │   ├── deps.py               # 依赖注入
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── knowledge.py
│   │   │   ├── code.py
│   │   │   ├── quiz.py
│   │   │   └── memory.py
│   │   ├── agents/
│   │   │   ├── graph.py          # LangGraph StateGraph 构建
│   │   │   ├── nodes/
│   │   │   │   ├── understand.py
│   │   │   │   ├── recall.py
│   │   │   │   ├── plan.py
│   │   │   │   ├── teach.py
│   │   │   │   ├── quiz.py
│   │   │   │   ├── code.py
│   │   │   │   ├── review.py
│   │   │   │   ├── reflect.py
│   │   │   │   └── respond.py
│   │   │   └── state.py          # AgentState 定义
│   │   ├── tools/
│   │   │   ├── llm.py            # LiteLLM 封装
│   │   │   ├── sandbox.py        # E2B 封装
│   │   │   ├── retriever.py      # Qdrant 封装
│   │   │   └── fsrs.py           # FSRS-4.5 实现
│   │   ├── routers/
│   │   │   ├── auth.py           # 认证（保留）
│   │   │   ├── chat.py           # 对话（SSE）
│   │   │   ├── sessions.py      # 会话管理
│   │   │   ├── profile.py       # 学生画像
│   │   │   └── review.py        # 复习
│   │   └── security.py           # bcrypt + JWT
│   ├── alembic/
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_chat.py
│   │   ├── test_fsrs.py
│   │   └── test_sandbox.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx          # 落地页
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── chat/
│   │   │       └── page.tsx     # 主界面
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── CodeBlock.tsx
│   │   │   ├── QuizCard.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── ReviewReminder.tsx
│   │   │   └── ProfilePanel.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts        # SSE 流式对话
│   │   │   └── useSWR.ts
│   │   └── lib/
│   │       ├── api.ts
│   │       └── utils.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml            # 单服务 + PostgreSQL + Qdrant + Redis
└── README.md
```

---

## 十一、Docker 部署

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: eduflow
      POSTGRES_PASSWORD: eduflow
      POSTGRES_DB: eduflow
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eduflow"]
      interval: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6379:6333"]   # 注：Qdrant 默认 6333
    volumes: [qdrant_data:/qdrant/storage]

  redis:
    image: redis:7-alpine
    ports: ["6389:6379"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://eduflow:eduflow@postgres:5432/eduflow
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      E2B_API_KEY: ${E2B_API_KEY:-}
      LITELLM_API_KEY: ${LITELLM_API_KEY:-}
      LITELLM_BASE_URL: ${LITELLM_BASE_URL:-}
      LITELLM_MODEL: ${LITELLM_MODEL:-gpt-4o-mini}
      JWT_SECRET: ${JWT_SECRET:-change-me}
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
      qdrant: { condition: service_started }

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [backend]

volumes:
  pgdata:
  qdrant_data:
```

---

## 十二、验收总表

| 版本 | 核心验收 | 预计周期 |
|---|---|---|
| v0.1.0 | 对话 → 教概念 → 出选择题 → 判题 → 历史保存 | 2 周 |
| v0.2.0 | 写代码 → 沙箱执行 → Agent 反馈 | 1 周 |
| v0.3.0 | FSRS 排期 → 主动复习 → 掌握度更新 | 1 周 |
| v0.4.0 | 知识库检索 → 引用来源 → 有据可依 | 1 周 |
| v0.5.0 | 记忆提取 → 画像更新 → 个性化出题 | 1 周 |
| v0.6.0 | 移动端 → 深色模式 → 流式优化 | 1 周 |

**总计：7 周，从 LMS 平台转型为编程学习 Agent。**

---

## 十三、风险与对策

| 风险 | 概率 | 影响 | 对策 |
|---|---|---|---|
| E2B 免费额度不够 | 中 | 高 | 准备 Judge0 自部署方案作为备选 |
| LLM API 成本 | 高 | 高 | LiteLLM 支持切换便宜模型；降级模式兜底 |
| LangGraph 学习曲线 | 中 | 中 | v0.1.0 先用简化版状态机（3 个节点），逐步增加 |
| Qdrant 部署复杂度 | 低 | 低 | Docker 一行启动，不复杂 |
| FSRS 实现难度 | 中 | 中 | 用开源 fsrs 库（Python 版），不自己写 |
| 前端 Monaco 体积大 | 低 | 低 | 动态导入，不影响首屏 |

---

> **下一步**：审批通过后，从 v0.1.0 开始执行。先合并三服务为单后端，搭建 LangGraph 状态机骨架，跑通最小对话闭环。
