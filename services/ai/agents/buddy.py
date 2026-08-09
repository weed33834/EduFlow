"""
AI Buddy Agent - 协同练习对话
Acts as a study partner for collaborative learning and discussion
"""
from core.llm import chat_completion

BUDDY_SYSTEM_PROMPT = """你是一位AI学习伙伴，像同学一样和学生一起学习和讨论。
你的特点：
1. 平易近人：像朋友一样交流，语气轻松自然
2. 共同学习：用"我们一起"、"让我们来看看"等方式
3. 讨论式学习：通过提问和讨论激发思考
4. 互相鼓励：分享学习心得，给予积极反馈
5. 偶尔犯错：如果不知道，会诚实说"这个我也不太确定，我们一起查查资料"

请用中文交流，语气亲切友好。"""

async def buddy_chat(message: str, context: dict = None) -> str:
    context_str = ""
    if context:
        context_str = f"\n当前学习内容：{context.get('topic', '')}"
        if context.get('progress'):
            context_str += f"\n学习进度：{context['progress']}"
    
    messages = [
        {"role": "user", "content": f"{context_str}\n\n{message}"}
    ]
    return await chat_completion(messages, BUDDY_SYSTEM_PROMPT)

async def discuss_topic(topic: str) -> str:
    prompt = f"我们一起来讨论一下{topic}吧！你对这个主题有什么了解？"
    messages = [{"role": "user", "content": prompt}]
    return await chat_completion(messages, BUDDY_SYSTEM_PROMPT)