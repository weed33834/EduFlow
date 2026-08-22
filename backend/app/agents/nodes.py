"""Agent 状态机节点 — v0.3.0

状态流：understand → recall → plan → [teach | quiz | code | review | judge] → respond → reflect

新增：
- judge 节点：判题闭环（quiz 选择题判分 + review 回忆作答评估）
- LLM 节点通过 LangGraph custom stream 输出增量 token（真流式）

集成开源组件：
- LiteLLM：LLM 统一接口 + JSON mode
- E2B：代码沙箱（开源，云端 API）
- Qdrant：向量知识库 RAG（开源）
- Mem0：长期记忆（开源）
- fsrs：间隔重复（开源）
"""
import logging
import re

from langgraph.config import get_stream_writer

from app.agents.state import AgentState
from app.tools.llm import (
    chat_completion,
    chat_completion_streaming,
    classify_intent,
    generate_json,
)
from app.config import settings

logger = logging.getLogger(__name__)

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

CODE_FEEDBACK_PROMPT = """你是编程老师。学生提交了代码，代码沙箱已执行完毕。
请根据执行结果给学生反馈：指出问题、给出建议、表扬正确的地方。简洁，不超过 200 字。"""

REVIEW_JUDGE_PROMPT = """你是一个间隔重复复习的判卷老师。学生之前学过某个概念，
现在凭记忆复述。请判断学生的复述是否表明他还记得核心内容。
返回 JSON（严格遵守）：{"remembered": true 或 false, "comment": "一两句中文点评"}
- remembered=true: 复述抓住了概念的核心含义（允许表述不完整）
- remembered=false: 复述错误或完全没答到点上"""


# ── 流式输出辅助 ──────────────────────────────────────────

def _emitter():
    """返回一个把增量 token 写入 LangGraph custom stream 的回调。

    在 graph.astream(stream_mode=["custom", ...]) 上下文中调用时，
    每个增量都会实时推给 SSE；不在该上下文中时是安全的 no-op。
    """
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    if writer is None:
        def _noop(_delta: str) -> None:
            return None
        return _noop
    return writer


def _stream_llm(messages: list[dict], system_prompt: str, temperature: float = 0.7,
                max_tokens: int = 2000) -> str:
    """封装同步签名：内部异步执行，LLM 可用时走真流式并推送增量。

    返回协程（由调用方 await）。
    """
    async def _run() -> str:
        return await chat_completion_streaming(
            messages,
            on_delta=_emitter(),
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _run()


# ── 判题闭环辅助 ──────────────────────────────────────────

_ANSWER_LETTER_RE = re.compile(r"^\s*(?:答案(?:是|为)?|选(?:择)?|我的答案)\s*[:：]?\s*([A-Da-d])\s*[.。!！]?\s*$")
_ANSWER_LETTER_BARE_RE = re.compile(r"^\s*([A-Da-d])\s*[.。!！]?\s*$")


def keyword_intent(message: str) -> str:
    """降级意图分类：关键词匹配（无 LLM 时使用，也是评估集的基线）"""
    msg = message.lower()
    if any(k in msg for k in ["def ", "print(", "import ", "class ", "console.log",
                              "运行这段代码", "帮我运行", "跑一下"]):
        return "run_code"
    if any(k in msg for k in ["什么是", "解释", "讲解", "讲讲", "原理", "怎么理解"]):
        return "learn_concept"
    if any(k in msg for k in ["出题", "练习", "题目", "考考", "quiz", "题"]):
        return "practice"
    if any(k in msg for k in ["你好", "hi", "hello", "嘿", "hey"]):
        return "chitchat"
    return "ask_question"


def parse_choice_answer(text: str) -> int | None:
    """从学生消息中解析选择题作答（0-3），解析失败返回 None。"""
    stripped = text.strip()
    for pattern in (_ANSWER_LETTER_BARE_RE, _ANSWER_LETTER_RE):
        m = pattern.match(stripped)
        if m:
            return ord(m.group(1).upper()) - ord("A")
    return None


# ── 节点实现 ──────────────────────────────────────────────

async def understand(state: AgentState) -> AgentState:
    """理解学生意图（带最近对话上下文，消解指代）"""
    message = state["user_message"]
    prior_history = state.get("history", [])

    if settings.llm_available:
        # classify_intent 用 LiteLLM JSON mode 返回干净标签；传入历史以处理"继续/那第二点呢"
        intent = await classify_intent(message, history=prior_history)
    else:
        # 降级：关键词匹配
        intent = keyword_intent(message)

    # 把当前用户消息加入历史（由 LangGraph Checkpointer 自动持久化）
    history = state.get("history", [])
    history = list(history) + [{"role": "user", "content": message}]

    return {**state, "intent": intent, "history": history}


async def recall(state: AgentState) -> AgentState:
    """检索记忆 — Mem0 长期记忆 + Qdrant 知识库 RAG"""
    profile = state.get("student_profile") or {
        "current_level": "beginner",
        "learning_goal": "",
    }

    message = state.get("user_message", "")
    user_id = str(state.get("user_id", ""))

    # 从 Mem0 检索长期记忆
    memories = []
    try:
        from app.tools.memory import search_memory
        memories = await search_memory(user_id, message)
    except Exception:
        logger.warning("recall: Mem0 检索失败", exc_info=True)

    # 从 Qdrant 知识库检索相关文档
    knowledge = []
    try:
        from app.tools.knowledge import search_knowledge
        knowledge = await search_knowledge(message)
    except Exception:
        logger.warning("recall: 知识库检索失败", exc_info=True)

    return {
        **state,
        "student_profile": profile,
        "memory_context": memories,
        "knowledge_context": knowledge,
    }


async def plan(state: AgentState) -> AgentState:
    """决策下一步行动"""
    intent = state.get("intent", "ask_question")
    message = state.get("user_message", "")

    # 判题优先：上一轮留了待作答的选择题，且本轮消息是选项作答
    pending_quiz = state.get("pending_quiz") or {}
    if pending_quiz and parse_choice_answer(message) is not None:
        return {**state, "action_plan": "judge"}

    # 复习回忆作答：上一轮是复习提问，本轮短回复且不是明确的新任务
    pending_review = state.get("pending_review") or {}
    if (pending_review
            and len(message) <= 200
            and intent not in ("practice", "run_code", "learn_concept")):
        return {**state, "action_plan": "judge"}

    # 检查是否有到期的复习项（FSRS 间隔重复）
    review_items = state.get("review_items", [])
    if review_items and intent not in ("practice", "run_code", "chitchat"):
        action = "review"
    else:
        route = {
            "learn_concept": "teach",
            "practice": "quiz",
            "run_code": "code",
            "ask_question": "teach",  # 答疑也走 teach
            "chitchat": "respond",
        }
        action = route.get(intent, "respond")

    return {**state, "action_plan": action}


async def judge(state: AgentState) -> AgentState:
    """判题节点 — 闭合 quiz / review 的学习反馈回路

    - quiz 选择题：确定性判分（对比选项索引），无需 LLM
    - review 回忆作答：LLM 判断学生复述是否记得核心（降级用关键词匹配）
    判分映射 FSRS rating：正确 → 3（Good），错误 → 1（Again）
    """
    message = state.get("user_message", "")
    pending_quiz = state.get("pending_quiz") or {}
    pending_review = state.get("pending_review") or {}

    if pending_quiz:
        selected = parse_choice_answer(message)
        answer = pending_quiz.get("answer")
        correct = selected is not None and answer is not None and selected == int(answer)
        explanation = str(pending_quiz.get("explanation", "") or "").strip()
        if correct:
            feedback = f"回答正确 ✅（{chr(65 + selected)}）"
        else:
            letter = chr(65 + int(answer)) if isinstance(answer, int) else "?"
            feedback = f"回答错误 ❌ 正确答案是 {letter}"
        if explanation:
            feedback += f"\n\n解析：{explanation}"

        return {**state, "judge_result": {
            "mode": "quiz",
            "correct": correct,
            "rating": 3 if correct else 1,
            "item_id": pending_quiz.get("review_item_id"),
            "selected": selected,
            "answer": int(answer) if isinstance(answer, int) else None,
            "feedback": feedback,
        }}

    if pending_review:
        concept = pending_review.get("concept", "")
        item_id = pending_review.get("item_id")

        if settings.llm_available:
            prompt = (
                f"概念：{concept}\n学生的复述：{message}\n\n"
                '请返回 JSON：{"remembered": true/false, "comment": "一两句中文点评"}'
            )
            result = await generate_json(prompt, system_prompt=REVIEW_JUDGE_PROMPT)
            remembered = bool(result.get("remembered"))
            comment = str(result.get("comment", "") or "").strip()
        else:
            # 降级：复述包含概念关键词即视为记得
            remembered = bool(concept) and concept in message or len(message) >= 10
            comment = ""

        feedback = "记得很牢，继续保持 ✅" if remembered else "这个概念印象变淡了，建议再回顾一遍 ❌"
        if comment:
            feedback += f"\n\n{comment}"

        return {**state, "judge_result": {
            "mode": "review",
            "correct": remembered,
            "rating": 3 if remembered else 1,
            "item_id": item_id,
            "feedback": feedback,
        }}

    # 没有待判题内容却被路由进来 — 回退为通用回复
    return {**state, "action_plan": "respond"}


def _recent_messages(history: list[dict], exclude_last: bool = True,
                     max_entries: int = 6) -> list[dict]:
    """取最近的合法对话条目（role+content 齐全），供 LLM 消息构造使用。

    teach/respond 共用，避免两处各写一份截取循环。
    """
    entries = history[:-1] if exclude_last else history
    messages: list[dict] = []
    for h in entries[-max_entries:]:
        if h.get("role") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])})
    return messages


async def teach(state: AgentState) -> AgentState:
    """讲解概念"""
    message = state["user_message"]
    profile = state.get("student_profile", {})
    level = profile.get("current_level", "beginner")
    history = state.get("history", [])

    # 构造带历史的消息（排除当前消息，由 understand 节点加入）
    messages: list[dict] = _recent_messages(history, exclude_last=True, max_entries=6)

    # 加入知识库上下文（如果有）
    knowledge = state.get("knowledge_context", [])
    context_parts = []
    if knowledge:
        context_parts.append("参考资料：\n" + "\n".join(k.get("text", "")[:200] for k in knowledge[:2]))

    # 加入记忆上下文（如果有）
    memories = state.get("memory_context", [])
    if memories:
        context_parts.append("学生记忆：\n" + "\n".join(m.get("text", "")[:100] for m in memories[:3]))

    user_content = f"学生问题：{message}\n学生水平：{level}"
    if context_parts:
        user_content += "\n\n" + "\n\n".join(context_parts)
    messages.append({"role": "user", "content": user_content})

    if settings.llm_available:
        content = await _stream_llm(messages, TEACH_PROMPT)
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


async def code(state: AgentState) -> AgentState:
    """代码执行节点 — 用 E2B 开源沙箱执行学生代码"""
    from app.tools.sandbox import execute_code

    message = state["user_message"]

    # 在 E2B 沙箱中执行代码
    result = await execute_code(message)

    # 让 LLM 根据执行结果给反馈
    if settings.llm_available:
        feedback_prompt = (
            f"学生代码执行成功。\n代码：\n{message}\n\n输出：\n{result['stdout']}\n\n请简要评价代码和输出。"
            if result["success"]
            else f"学生代码执行失败。\n代码：\n{message}\n\n错误：\n{result['stderr']}\n\n请指出问题并给出修复建议。"
        )

        content = await _stream_llm(
            [{"role": "user", "content": feedback_prompt}],
            CODE_FEEDBACK_PROMPT,
            temperature=0.3,
            max_tokens=500,
        )
    else:
        # 降级：直接返回执行结果
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        if result["success"]:
            content = f"代码执行成功 ✅\n\n输出：\n{stdout}"
        else:
            content = f"代码执行失败 ❌\n\n错误：\n{stderr}"

    return {**state, "code_result": result, "teach_content": content}


async def review(state: AgentState) -> AgentState:
    """复习节点 — 基于开源 fsrs 包的间隔重复，生成复习内容"""
    review_items = state.get("review_items", [])

    if not review_items:
        return {**state, "review_content": ""}

    # 取第一个到期项
    item = review_items[0]
    concept = item.get("concept", "")

    if settings.llm_available:
        prompt = f"学生之前学过「{concept}」，现在需要复习。请用 1-2 句话简要回顾这个概念，然后出一道简单的判断题检验学生是否还记得。"
        content = await _stream_llm(
            [{"role": "user", "content": prompt}],
            system_prompt="你是一个编程复习助手。简洁回顾概念并出题。",
            temperature=0.5,
            max_tokens=500,
        )
    else:
        content = f"复习：{concept}\n\n请简要描述你对「{concept}」的理解。"

    return {**state, "review_content": content, "review_item_id": item.get("id")}


async def respond(state: AgentState) -> AgentState:
    """组织回复"""
    reply_text = ""

    # 0. 判题结果（judge 节点产出）— 最高优先
    judge_result = state.get("judge_result") or {}
    if judge_result.get("feedback"):
        reply_text = judge_result["feedback"]
    # 1. 如果有复习内容（FSRS 间隔重复）
    elif state.get("review_content"):
        reply_text = state["review_content"]
    # 2. 如果有讲解内容
    elif state.get("teach_content"):
        reply_text = state["teach_content"]
    # 3. 如果有题目
    elif state.get("quiz_question"):
        reply_text = _format_quiz(state["quiz_question"])
    # 4. 通用回复
    else:
        message = state["user_message"]
        history = state.get("history", [])
        messages: list[dict] = _recent_messages(history, exclude_last=True, max_entries=6)
        messages.append({"role": "user", "content": message})

        if settings.llm_available:
            reply_text = await _stream_llm(messages, GENERAL_PROMPT)
        else:
            reply_text = _general_fallback(message)

    # 把助手回复加入历史（由 LangGraph Checkpointer 自动持久化）
    history = state.get("history", [])
    history = list(history) + [{"role": "assistant", "content": reply_text}]

    return {**state, "response_chunks": [reply_text], "history": history}


async def reflect(state: AgentState) -> AgentState:
    """反思 — 用 Mem0 保存对话记忆，FSRS 卡片由 chat.py 路由层管理"""
    user_id = str(state.get("user_id", ""))
    message = state.get("user_message", "")
    reply = ""
    if state.get("response_chunks"):
        reply = state["response_chunks"][0]

    # 保存对话到 Mem0（自动提取关键信息）
    if user_id and message and reply:
        try:
            from app.tools.memory import add_memory
            await add_memory(user_id, f"学生问：{message}\n助手答：{reply}")
        except Exception:
            logger.warning("reflect: Mem0 写入失败", exc_info=True)

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
