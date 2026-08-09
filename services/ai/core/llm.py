"""
EduFlow AI Service - LLM 核心模块

提供统一的 LLM 调用接口。当配置了 OPENAI_API_KEY 时调用真实 OpenAI API；
未配置时返回智能降级回复，根据 agent 类型返回不同风格的模板回复，
确保服务在缺少 LLM 的情况下依然可用且不报错。
"""
from typing import Optional

from openai import AsyncOpenAI

from core.config import settings

# 仅在配置了 API Key 时创建客户端
client: Optional[AsyncOpenAI] = (
    AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    if settings.OPENAI_API_KEY
    else None
)


def is_llm_available() -> bool:
    """判断 LLM 服务是否可用（是否配置了 OPENAI_API_KEY）。"""
    return client is not None


def _extract_user_message(messages: list[dict]) -> str:
    """从消息列表中提取最后一条用户消息内容。"""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# ---------------------------------------------------------------------------
# 降级回复模板（按 agent 类型区分风格）
# ---------------------------------------------------------------------------

def _tutor_fallback(user_message: str) -> str:
    """导师 agent 降级回复：苏格拉底式引导，不直接给答案。"""
    snippet = f"你提到的「{user_message[:60]}」" if user_message else "你提出的问题"
    return (
        f"你好！很高兴你愿意思考 {snippet}，这是一个很好的学习契机。\n\n"
        "作为你的学习导师，我更希望引导你自己找到答案，而不是直接告诉你结论。"
        "让我们一步步来：\n\n"
        "1. 【理解问题】你能否用自己的话重新描述一下这个问题？弄清楚它到底在问什么，"
        "是找到答案的第一步。\n"
        "2. 【回顾已知】在学习这个内容之前，你已经掌握了哪些相关知识？它们之间可能存在怎样的联系？\n"
        "3. 【拆解难点】如果把这个问题拆成更小的部分，你会如何入手？哪一部分是你最不确定的？\n"
        "4. 【提出假设】不妨先大胆猜测一个可能的答案或方向，哪怕不完全正确也没关系。\n\n"
        "学习是一个主动思考的过程，自己探索得出的结论会比直接被告知答案深刻得多。"
        "你可以先尝试回答上面的问题，再告诉我你的想法，我们继续深入探讨。\n\n"
        "提示：当前为降级模式（未配置 OPENAI_API_KEY），如需获得更深入、个性化的辅导，"
        "请联系管理员配置 AI 服务。"
    )


def _buddy_fallback(user_message: str) -> str:
    """学习伙伴 agent 降级回复：鼓励性、轻松友好。"""
    snippet = f"关于「{user_message[:60]}」" if user_message else "你正在学习的内容"
    return (
        f"嘿！看到你在努力钻研 {snippet}，真的很棒，这种求知欲值得点赞！\n\n"
        "虽然我现在暂时没法和你进行深度的多轮探讨（AI 服务还没配置好），"
        "但我可以给你分享一些超实用的学习小建议：\n\n"
        "- 先把已知的信息梳理出来，写在纸上或笔记里，理清思路往往能解决一半的困惑；\n"
        "- 试着用自己的话把问题复述一遍，这能帮你发现真正卡住的地方在哪；\n"
        "- 如果一时想不通，不妨先放一放去做点别的，换个心情回来看常常会有新灵感；\n"
        "- 找一个小伙伴或者社区讨论一下，把想法说出来本身就是一种梳理。\n\n"
        "学习就是这样一个不断探索的过程，遇到难题太正常啦，关键是要保持好奇心和耐心。"
        "你现在已经迈出了主动提问这一步，这本身就很了不起！继续加油，你一定可以的！\n\n"
        "提示：当前为降级模式（未配置 OPENAI_API_KEY），配置后我们就能更深入地交流啦。"
    )


def _examiner_fallback(user_message: str) -> str:
    """出题官 agent 的文本降级回复（结构化题目由 examiner 模块自行处理）。"""
    return (
        "当前处于降级模式（未配置 OPENAI_API_KEY），无法动态生成个性化题目。\n\n"
        "不过别担心，我已经为你准备了一套通用编程练习题库，涵盖了变量、数据类型、"
        "控制流、函数、数据结构等核心知识点，你可以先练起来！\n\n"
        "建议你：\n"
        "1. 按顺序作答，先易后难，建立信心；\n"
        "2. 每道题做完后仔细阅读解析，理解背后的原理；\n"
        "3. 把错题记录下来，过几天再复习一遍，巩固记忆。\n\n"
        "配置 AI 服务后，我就能根据你的水平和薄弱点量身定制更精准的题目了。"
    )


def _planner_fallback(user_message: str) -> str:
    """规划师 agent 的文本降级回复（结构化路径由 planner 模块自行处理）。"""
    return (
        "当前处于降级模式（未配置 OPENAI_API_KEY），无法生成完全个性化的学习路径。\n\n"
        "不过我已经为你准备了一份结构化的通用学习路径模板，覆盖从入门到进阶的完整流程，"
        "你可以以此为起点，根据自己的实际情况灵活调整节奏。\n\n"
        "规划建议：\n"
        "1. 先明确学习目标和当前水平，找到适合自己的起点；\n"
        "2. 把大目标拆解为可衡量的小里程碑，每完成一个就给自己一点奖励；\n"
        "3. 合理分配每周的学习时间，保持规律比偶尔冲刺更有效；\n"
        "4. 定期回顾和调整计划，学习路径不是一成不变的。\n\n"
        "配置 AI 服务后，我可以结合你的具体目标、水平和偏好，生成更精准的个性化学习路径。"
    )


def _default_fallback(user_message: str) -> str:
    """默认降级回复。"""
    snippet = f"你提到的「{user_message[:60]}」" if user_message else "你的问题"
    return (
        f"感谢你提出 {snippet}。\n\n"
        "当前 AI 服务处于降级模式（未配置 OPENAI_API_KEY），暂时无法进行深度的智能分析。"
        "请联系管理员配置 OPENAI_API_KEY 以启用完整的 AI 能力。\n\n"
        "在降级模式下，服务仍可正常响应请求并返回预设的结构化内容，不会影响基本使用。"
    )


_FALLBACK_BUILDERS = {
    "tutor": _tutor_fallback,
    "buddy": _buddy_fallback,
    "examiner": _examiner_fallback,
    "planner": _planner_fallback,
}


def _build_fallback_reply(messages: list[dict], agent_type: str = "tutor") -> str:
    """根据 agent 类型构建降级回复。"""
    user_message = _extract_user_message(messages)
    builder = _FALLBACK_BUILDERS.get(agent_type, _default_fallback)
    return builder(user_message)


# ---------------------------------------------------------------------------
# 核心接口
# ---------------------------------------------------------------------------

async def chat_completion(
    messages: list[dict],
    system_prompt: str = "",
    agent_type: str = "tutor",
    temperature: Optional[float] = None,
) -> str:
    """调用 LLM 完成对话。

    Args:
        messages: 对话消息列表，格式为 [{"role": "user", "content": "..."}]。
        system_prompt: 系统提示词，用于设定 agent 角色。
        agent_type: agent 类型，用于在未配置 API Key 时生成对应风格的降级回复。
            支持 "tutor" / "buddy" / "examiner" / "planner"。
        temperature: 采样温度，为 None 时使用全局配置。

    Returns:
        LLM 生成的文本回复；未配置 API Key 时返回智能降级回复。
    """
    # 未配置 API Key：返回智能降级回复，不报错
    if not client:
        return _build_fallback_reply(messages, agent_type)

    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    resp = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
    )
    return resp.choices[0].message.content


async def stream_chat(
    messages: list[dict],
    system_prompt: str = "",
    agent_type: str = "tutor",
):
    """流式调用 LLM。

    未配置 API Key 时以降级回复作为单次产出。
    """
    if not client:
        yield _build_fallback_reply(messages, agent_type)
        return

    full_messages: list[dict] = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
