"""
AI Buddy Agent - 学习伙伴

以学习伙伴的身份与学生进行协同练习和讨论，语气轻松友好。
未配置 API Key 时返回鼓励性降级回复，营造陪伴感。
"""
from typing import Optional

from core.llm import chat_completion, stream_chat
from core.rag import build_knowledge_context

BUDDY_SYSTEM_PROMPT = """你是一位 AI 学习伙伴，像同学一样和学生一起学习和讨论。
你的特点：
1. 平易近人：像朋友一样交流，语气轻松自然
2. 共同学习：用"我们一起"、"让我们来看看"等方式
3. 讨论式学习：通过提问和讨论激发思考
4. 互相鼓励：分享学习心得，给予积极反馈
5. 偶尔犯错：如果不知道，会诚实说"这个我也不太确定，我们一起查查资料"

请用中文交流，语气亲切友好。"""


async def build_chat_messages(
    message: str, context: Optional[dict] = None, history: Optional[list] = None
) -> list[dict]:
    """组装学习伙伴对话消息(含 RAG)，供普通对话与流式对话共用。"""
    context_str = ""
    if context:
        context_str = f"\n当前学习内容：{context.get('topic', '')}"
        if context.get("progress"):
            context_str += f"\n学习进度：{context['progress']}"

    rag_ctx = await build_knowledge_context(message)

    messages: list[dict] = []
    for h in history or []:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])})
    messages.append({"role": "user", "content": f"{context_str}\n{rag_ctx}\n\n{message}"})
    return messages


async def buddy_chat(message: str, context: Optional[dict] = None, history: Optional[list] = None) -> str:
    """学习伙伴式对话。

    以朋友的口吻与学生交流，给予鼓励和陪伴。
    未配置 API Key 时返回鼓励性降级回复。

    Args:
        message: 学生的消息内容。
        context: 学习上下文，可包含 topic、progress 等信息。
        history: 多轮会话历史，[{"role": "user"|"assistant", "content": "..."}]。

    Returns:
        学习伙伴的回复文本。
    """
    messages = await build_chat_messages(message, context, history)
    return await chat_completion(messages, BUDDY_SYSTEM_PROMPT, agent_type="buddy")


async def buddy_chat_stream(
    message: str, context: Optional[dict] = None, history: Optional[list] = None
):
    """流式学习伙伴对话。"""
    messages = await build_chat_messages(message, context, history)
    async for chunk in stream_chat(messages, BUDDY_SYSTEM_PROMPT, agent_type="buddy"):
        yield chunk
