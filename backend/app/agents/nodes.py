"""Agent 状态机节点 — v0.1.0 最小闭环

状态流：understand → recall → plan → [teach | quiz] → respond → reflect
"""
from app.agents.state import AgentState
from app.tools.llm import chat_completion, classify_intent, generate_json
from app.config import settings

# ── 系统提示词 ──────────────────────────────────────────────

TEACH_PROMPT = """你是一个编程教学 Agent，擅长用简洁清晰的方式讲解编程概念。
要求：
1. 适合学生当前水平的讲解
2. 用代码示例说明
3. 简洁，不超过 300 字
4. 用中文回答"""

QUIZ_PROMPT = """你是一个编程出题专家，擅长根据学生水平生成高质量选择题。
出题要求：
1. 难度匹配学生水平
2. 4 个选项，answer 是正确选项的索引（0-3）
3. 附带详细解析
4. 必须返回 JSON 格式

返回格式（严格遵守）：
{"question": "题目内容", "options": ["选项A", "选项B", "选项C", "选项D"], "answer": 0, "explanation": "详细解析", "difficulty": "easy"}"""

GENERAL_PROMPT = """你是一个友好的编程学习助手。用中文简洁回答学生的问题。
如果学生是在回答之前出的题，判断对错并给出解析。"""


# ── 节点实现 ──────────────────────────────────────────────

async def understand(state: AgentState) -> AgentState:
    """理解学生意图"""
    message = state["user_message"]

    if settings.llm_available:
        # classify_intent 用 LiteLLM JSON mode 返回干净标签，无需手动规范化
        intent = await classify_intent(message)
    else:
        # 降级：关键词匹配
        msg = message.lower()
        if any(k in msg for k in ["什么是", "解释", "讲解", "原理", "怎么理解"]):
            intent = "learn_concept"
        elif any(k in msg for k in ["出题", "练习", "题目", "考考", "quiz", "题"]):
            intent = "practice"
        elif any(k in msg for k in ["你好", "hi", "hello", "嘿", "hey"]):
            intent = "chitchat"
        else:
            intent = "ask_question"

    return {**state, "intent": intent}


async def recall(state: AgentState) -> AgentState:
    """检索记忆（v0.1.0 空操作 — v0.4.0 接 Qdrant，v0.5.0 接 Mem0）"""
    profile = state.get("student_profile") or {
        "current_level": "beginner",
        "learning_goal": "",
    }
    return {**state, "student_profile": profile}


async def plan(state: AgentState) -> AgentState:
    """决策下一步行动"""
    intent = state.get("intent", "ask_question")

    route = {
        "learn_concept": "teach",
        "practice": "quiz",
        "ask_question": "teach",  # 答疑也走 teach
        "chitchat": "respond",
    }

    action = route.get(intent, "respond")
    return {**state, "action_plan": action}


async def teach(state: AgentState) -> AgentState:
    """讲解概念"""
    message = state["user_message"]
    profile = state.get("student_profile", {})
    level = profile.get("current_level", "beginner")
    history = state.get("history", [])

    # 构造带历史的消息
    messages: list[dict] = []
    for h in history[-6:]:  # 最近 3 轮
        if h.get("role") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])})
    messages.append({"role": "user", "content": f"学生问题：{message}\n学生水平：{level}"})

    if settings.llm_available:
        content = await chat_completion(messages, system_prompt=TEACH_PROMPT)
    else:
        content = _teach_fallback(message)

    return {**state, "teach_content": content}


async def quiz(state: AgentState) -> AgentState:
    """出题"""
    message = state["user_message"]
    profile = state.get("student_profile", {})
    level = profile.get("current_level", "beginner")

    if settings.llm_available:
        prompt = f"请围绕以下主题出 1 道选择题。学生水平：{level}\n主题/要求：{message}"
        question = await generate_json(prompt, system_prompt=QUIZ_PROMPT)
        if not question or "question" not in question:
            question = _quiz_fallback(message)
    else:
        question = _quiz_fallback(message)

    return {**state, "quiz_question": question}


async def respond(state: AgentState) -> AgentState:
    """组织回复"""
    # 1. 如果有讲解内容
    if state.get("teach_content"):
        return {**state, "response_chunks": [state["teach_content"]]}

    # 2. 如果有题目
    if state.get("quiz_question"):
        formatted = _format_quiz(state["quiz_question"])
        return {**state, "response_chunks": [formatted]}

    # 3. 通用回复
    message = state["user_message"]
    history = state.get("history", [])
    messages: list[dict] = []
    for h in history[-6:]:
        if h.get("role") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])})
    messages.append({"role": "user", "content": message})

    if settings.llm_available:
        reply = await chat_completion(messages, system_prompt=GENERAL_PROMPT)
    else:
        reply = _general_fallback(message)

    return {**state, "response_chunks": [reply]}


async def reflect(state: AgentState) -> AgentState:
    """反思与记忆更新（v0.1.0 只标记，不做实际更新 — v0.5.0 接记忆层）"""
    return state


# ── 降级模板 ──────────────────────────────────────────────

def _teach_fallback(message: str) -> str:
    return (
        f"关于「{message}」，我目前处于降级模式（未配置 LLM），无法生成详细讲解。\n\n"
        "建议你：\n"
        "1. 在设置中配置 LLM API Key 以获得完整体验\n"
        "2. 或者搜索相关教程文档进行学习\n"
        "3. 如果你有具体问题，可以直接描述，我会尽力回答"
    )


def _quiz_fallback(topic: str) -> dict:
    return {
        "question": f"关于「{topic}」，下列说法正确的是？",
        "options": [
            "这个知识点很重要，需要认真学习",
            "这个知识点不太常用，可以跳过",
            "这个知识点只适用于特定场景",
            "以上都不对",
        ],
        "answer": 0,
        "explanation": "当前处于降级模式，无法生成高质量题目。请配置 LLM API Key 后重试。",
        "difficulty": "easy",
    }


def _general_fallback(message: str) -> str:
    return (
        f"你好！我收到了你的消息：「{message}」\n\n"
        "目前处于降级模式（未配置 LLM），我的功能有限。"
        "请在设置中配置 LLM API Key 以获得完整的 AI 学习体验。"
    )


def _format_quiz(q: dict) -> str:
    """格式化题目为文本"""
    lines = [q.get("question", "")]
    for i, opt in enumerate(q.get("options", [])):
        lines.append(f"  {chr(65 + i)}. {opt}")
    lines.append("")
    lines.append("(请回复 A/B/C/D 作答)")
    return "\n".join(lines)
