"""
AI Tutor Agent - 智能辅导答疑

按需辅导答疑，帮助学生理解概念、回答问题、提供解释。
采用苏格拉底式教学法，引导学生自主思考。
未配置 API Key 时返回引导式降级回复，不直接给出答案。
"""
from typing import Optional

from core.llm import chat_completion, stream_chat
from core.rag import build_knowledge_context, build_prerequisite_context

TUTOR_SYSTEM_PROMPT = """你是一位经验丰富的 AI 导师，擅长帮助学生理解和掌握知识。
你的教学原则：
1. 苏格拉底式教学：引导学生自己思考，而不是直接给答案
2. 因材施教：根据学生的水平和理解程度调整解释方式
3. 循序渐进：从基础概念开始，逐步深入
4. 举一反三：用例子和类比帮助理解抽象概念
5. 鼓励式反馈：肯定学生的努力，激发学习兴趣

请用中文回答，语言亲切自然。"""

# 概念解释的难度描述映射
_LEVEL_DESC = {
    "beginner": "初学者",
    "intermediate": "进阶",
    "advanced": "高级",
}


async def build_chat_messages(
    message: str, context: Optional[dict] = None, history: Optional[list] = None
) -> list[dict]:
    """组装导师对话消息(含 RAG 检索增强)，供普通对话与流式对话共用。"""
    context_str = ""
    if context:
        context_str = f"\n当前学习上下文：{context.get('topic', '')} - {context.get('module', '')}"
        if context.get("learning_history"):
            context_str += f"\n学习历史：{context['learning_history']}"

    rag_ctx = await build_knowledge_context(message)

    messages: list[dict] = []
    for h in history or []:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])})
    messages.append({"role": "user", "content": f"{context_str}\n{rag_ctx}\n\n学生问题：{message}"})
    return messages


async def tutor_chat(message: str, context: Optional[dict] = None, history: Optional[list] = None) -> str:
    """苏格拉底式教学对话。

    引导学生自主思考，而非直接给出答案。
    未配置 API Key 时返回引导式降级回复。

    Args:
        message: 学生的提问内容。
        context: 学习上下文，可包含 topic、module、learning_history 等信息。
        history: 多轮会话历史，[{"role": "user"|"assistant", "content": "..."}]。

    Returns:
        导师的回复文本。
    """
    messages = await build_chat_messages(message, context, history)
    return await chat_completion(messages, TUTOR_SYSTEM_PROMPT, agent_type="tutor")


async def tutor_chat_stream(
    message: str, context: Optional[dict] = None, history: Optional[list] = None
):
    """流式苏格拉底式对话。"""
    messages = await build_chat_messages(message, context, history)
    async for chunk in stream_chat(messages, TUTOR_SYSTEM_PROMPT, agent_type="tutor"):
        yield chunk


async def explain_concept(
    topic: str,
    level: str = "beginner",
    context: Optional[dict] = None,
) -> str:
    """概念解释。

    用与学习者水平匹配的方式解释指定概念，使用类比和实例。
    未配置 API Key 时返回结构化的引导式降级回复。

    Args:
        topic: 要解释的概念名称。
        level: 学习者水平，beginner / intermediate / advanced。
        context: 可选的附加上下文信息。

    Returns:
        概念解释文本。
    """
    level_desc = _LEVEL_DESC.get(level, level)
    context_hint = ""
    if context:
        context_hint = f"\n附加背景信息：{context}"

    # RAG：检索概念相关资料 + 前置知识
    rag_ctx = await build_knowledge_context(topic)
    prereq_ctx = await build_prerequisite_context(topic)

    prompt = (
        f"请用「{level_desc}」水平可以理解的方式，解释以下概念：{topic}\n"
        f"要求：使用类比和实例，条理清晰，200-400 字。{context_hint}\n"
        f"{rag_ctx}\n{prereq_ctx}"
    )
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, TUTOR_SYSTEM_PROMPT, agent_type="tutor")

    # 降级回复会被 chat_completion 自动返回，这里无需额外处理。
    # 为保证降级时也能体现「概念解释」的结构化引导，补充检测：
    if "降级模式" in result:
        result = _concept_fallback(topic, level_desc)
    return result


def _concept_fallback(topic: str, level_desc: str) -> str:
    """概念解释降级回复：结构化引导，帮助学习者自主构建理解。"""
    return (
        f"关于「{topic}」这个概念，我来帮你梳理一下学习思路。\n\n"
        "由于当前处于降级模式（未配置 OPENAI_API_KEY），我先提供一个结构化的学习框架，"
        f"帮助你以「{level_desc}」的视角逐步建立理解：\n\n"
        "【概念概览】\n"
        f"「{topic}」是一个值得深入理解的知识点。建议你从以下几个维度切入：\n\n"
        "【学习路径建议】\n"
        f"1. 基础定义：先弄清楚「{topic}」的核心定义——它究竟是什么？解决了什么问题？\n"
        f"2. 关键特征：理解「{topic}」的主要特点和属性，它有哪些独特之处？\n"
        f"3. 实际应用：通过具体例子看「{topic}」在实践中是如何被使用的。\n"
        f"4. 关联知识：「{topic}」和你已经学过的哪些内容有联系？它们之间有何异同？\n"
        f"5. 动手实践：尝试自己运用「{topic}」解决一个小问题，加深印象。\n\n"
        "【思考引导】\n"
        f"- 这个概念为什么会被提出？它背后的动机是什么？\n"
        f"- 它和哪些你已经熟悉的内容相似？能否找到一个类比？\n"
        f"- 在什么场景下会用到它？不用它会有什么不便？\n\n"
        "【建议行动】\n"
        f"你可以先尝试用自己的话写一段对「{topic}」的理解，然后对照资料查漏补缺。"
        "主动组织语言的过程，本身就是深化理解的有效方式。\n\n"
        "提示：配置 AI 服务后，我可以为你提供更详细、更个性化的概念讲解。"
    )
