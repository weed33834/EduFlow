"""
AI Buddy Agent - 学习伙伴

以学习伙伴的身份与学生进行协同练习和讨论，语气轻松友好。
未配置 API Key 时返回鼓励性降级回复，营造陪伴感。
"""
from typing import Optional

from core.llm import chat_completion

BUDDY_SYSTEM_PROMPT = """你是一位 AI 学习伙伴，像同学一样和学生一起学习和讨论。
你的特点：
1. 平易近人：像朋友一样交流，语气轻松自然
2. 共同学习：用"我们一起"、"让我们来看看"等方式
3. 讨论式学习：通过提问和讨论激发思考
4. 互相鼓励：分享学习心得，给予积极反馈
5. 偶尔犯错：如果不知道，会诚实说"这个我也不太确定，我们一起查查资料"

请用中文交流，语气亲切友好。"""


async def buddy_chat(message: str, context: Optional[dict] = None) -> str:
    """学习伙伴式对话。

    以朋友的口吻与学生交流，给予鼓励和陪伴。
    未配置 API Key 时返回鼓励性降级回复。

    Args:
        message: 学生的消息内容。
        context: 学习上下文，可包含 topic、progress 等信息。

    Returns:
        学习伙伴的回复文本。
    """
    context_str = ""
    if context:
        context_str = f"\n当前学习内容：{context.get('topic', '')}"
        if context.get("progress"):
            context_str += f"\n学习进度：{context['progress']}"

    messages = [
        {"role": "user", "content": f"{context_str}\n\n{message}"}
    ]
    return await chat_completion(messages, BUDDY_SYSTEM_PROMPT, agent_type="buddy")


async def discuss_topic(topic: str) -> str:
    """话题讨论。

    围绕指定话题发起讨论，激发学生的思考和表达。
    未配置 API Key 时返回结构化的讨论引导降级回复。

    Args:
        topic: 要讨论的话题。

    Returns:
        讨论引导文本。
    """
    prompt = f"我们一起来讨论一下「{topic}」吧！你对这个主题有什么了解或看法？"
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, BUDDY_SYSTEM_PROMPT, agent_type="buddy")

    # 降级时补充话题讨论专属的结构化引导
    if "降级模式" in result:
        result = _discuss_fallback(topic)
    return result


def _discuss_fallback(topic: str) -> str:
    """话题讨论降级回复：提供多角度思考框架，鼓励学生展开讨论。"""
    return (
        f"嘿！「{topic}」这个话题真的很有意思，值得好好聊一聊！\n\n"
        "虽然我现在暂时没法和你进行深度的多轮讨论（AI 服务还没配置好），"
        "但我可以分享一些思考角度，帮你开启对这个话题的探索：\n\n"
        "【可以从这几个方面切入】\n"
        f"1. 历史背景：「{topic}」是怎么发展起来的？它最初是为了解决什么问题而出现的？\n"
        f"2. 核心观点：关于「{topic}」，主要有哪些不同的立场和看法？各自的理由是什么？\n"
        f"3. 现实意义：「{topic}」对我们的学习、工作或生活有什么实际影响？\n"
        f"4. 争议焦点：在「{topic}」领域，有哪些尚未达成共识的问题？你怎么看？\n"
        f"5. 未来发展：「{topic}」未来可能会朝什么方向演进？有什么值得期待的进展？\n\n"
        "【一起来想想】\n"
        f"- 如果让你向一个完全不了解「{topic}」的人介绍它，你会怎么说？\n"
        f"- 「{topic}」里最让你感到好奇或困惑的部分是什么？\n"
        f"- 你有没有在现实生活中遇到过和「{topic}」相关的例子？\n\n"
        "你可以先挑一个最感兴趣的角度，自己思考一下，把想法记下来。"
        "等你准备好深入交流的时候，我们再一起讨论！保持这份好奇心，你很棒！\n\n"
        "提示：当前为降级模式（未配置 OPENAI_API_KEY），配置后我们可以进行更丰富的互动式讨论。"
    )
