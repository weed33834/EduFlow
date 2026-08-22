"""LLM 统一接口（LiteLLM 封装 — 支持 OpenAI/Claude/Gemini 等 100+ 模型）"""
import json
from typing import AsyncIterator, Callable

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


async def chat_completion_streaming(
    messages: list[dict],
    on_delta: Callable[[str], None],
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """真流式对话：每收到一个增量就调用 on_delta（推给 LangGraph custom writer），
    最终返回完整文本。未配置 LLM 时返回空串。"""
    if not settings.llm_available:
        return ""

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
    parts: list[str] = []
    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            parts.append(delta)
            try:
                on_delta(delta)
            except Exception:
                pass
    return "".join(parts)


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


def format_history_for_prompt(history: list[dict] | None, max_turns: int = 6) -> str:
    """把最近几轮对话压成纯文本上下文块（多轮意图分类用）。

    纯函数：空历史返回空串；只保留有 role+content 的条目。
    """
    if not history:
        return ""
    lines: list[str] = []
    for h in history[-max_turns:]:
        role = h.get("role")
        content = h.get("content")
        if not role or not content:
            continue
        who = "学生" if role == "user" else "助手"
        text = str(content).replace("\n", " ")[:120]
        lines.append(f"{who}：{text}")
    return "\n".join(lines)


async def classify_intent(message: str, history: list[dict] | None = None) -> str:
    """意图分类，返回标签（LiteLLM JSON mode 保证输出可靠）

    history: 当前消息之前的最近几轮对话，用于消解指代
    （如上一轮在讲递归时，"为什么不会栈溢出"应归入 ask_question 而非 chitchat）。
    """
    context_block = format_history_for_prompt(history)
    context_section = f"\n\n最近对话（供参考，可能存在指代）：\n{context_block}\n" if context_block else ""

    prompt = f"""判断学生最新一条消息的意图，返回 JSON：
{{"intent": "learn_concept" 或 "practice" 或 "run_code" 或 "ask_question" 或 "chitchat"}}

规则：
- learn_concept: 学新概念（如"什么是递归"）
- practice: 想练习（如"给我出几道题"）
- run_code: 想运行代码（消息包含代码块，如 def/print/import，或说"运行这段代码"）
- ask_question: 答疑或对上文追问（如"为什么这里报错""继续""那第二点呢"）
- chitchat: 闲聊（如"你好"）
结合最近对话判断指代与省略。{context_section}
学生最新消息：{message}"""

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
