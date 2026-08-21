"""LLM 统一接口（LiteLLM 封装 — 支持 OpenAI/Claude/Gemini 等 100+ 模型）"""
import json
from typing import AsyncIterator

import litellm

from app.config import settings


async def chat_completion(
    messages: list[dict],
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: dict | None = None,
) -> str:
    """非流式对话

    response_format: 传入 {"type": "json_object"} 启用 LiteLLM 原生 JSON mode，
    LLM 保证返回合法 JSON，无需手动 find("{") 解析。
    """
    if not settings.llm_available:
        return ""

    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    kwargs: dict = {
        "model": settings.LITELLM_MODEL,
        "messages": full_messages,
        "api_key": settings.LITELLM_API_KEY,
        "api_base": settings.LITELLM_BASE_URL,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = await litellm.acompletion(**kwargs)
    return response.choices[0].message.content


async def stream_chat(
    messages: list[dict],
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> AsyncIterator[str]:
    """流式对话，yield 增量文本"""
    if not settings.llm_available:
        return

    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    response = await litellm.acompletion(
        model=settings.LITELLM_MODEL,
        messages=full_messages,
        api_key=settings.LITELLM_API_KEY,
        api_base=settings.LITELLM_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def classify_intent(message: str) -> str:
    """意图分类，返回标签（LiteLLM JSON mode 保证输出可靠）"""
    prompt = f"""判断学生意图，返回 JSON：
{{"intent": "learn_concept" 或 "practice" 或 "ask_question" 或 "chitchat"}}

规则：
- learn_concept: 学新概念（如"什么是递归"）
- practice: 想练习（如"给我出几道题"）
- ask_question: 答疑（如"为什么这里报错"）
- chitchat: 闲聊（如"你好"）

学生消息：{message}"""

    result = await chat_completion(
        [{"role": "user", "content": prompt}],
        system_prompt="你是一个意图分类器，只输出 JSON。",
        temperature=0.1,
        max_tokens=50,
        response_format={"type": "json_object"},
    )
    if not result:
        return "ask_question"
    try:
        data = json.loads(result)
        return data.get("intent", "ask_question").strip().lower()
    except (json.JSONDecodeError, ValueError):
        return "ask_question"


async def generate_json(prompt: str, system_prompt: str = "") -> dict:
    """生成 JSON 输出（LiteLLM 原生 JSON mode，无需手动解析）"""
    result = await chat_completion(
        [{"role": "user", "content": prompt}],
        system_prompt=system_prompt,
        temperature=0.5,
        max_tokens=1000,
        response_format={"type": "json_object"},
    )
    if not result:
        return {}
    try:
        return json.loads(result)
    except (json.JSONDecodeError, ValueError):
        return {}
