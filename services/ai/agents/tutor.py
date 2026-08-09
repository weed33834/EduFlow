"""
AI Tutor Agent - 按需辅导答疑
Helps students understand concepts, answers questions, provides explanations
"""
from core.llm import chat_completion

TUTOR_SYSTEM_PROMPT = """你是一位经验丰富的AI导师，擅长帮助学生理解和掌握知识。
你的教学原则：
1. 苏格拉底式教学：引导学生自己思考，而不是直接给答案
2. 因材施教：根据学生的水平和理解程度调整解释方式
3. 循序渐进：从基础概念开始，逐步深入
4. 举一反三：用例子和类比帮助理解抽象概念
5. 鼓励式反馈：肯定学生的努力，激发学习兴趣

请用中文回答，语言亲切自然。"""

async def tutor_chat(message: str, context: dict = None) -> str:
    context_str = ""
    if context:
        context_str = f"\n当前学习上下文：{context.get('topic', '')} - {context.get('module', '')}"
        if context.get('learning_history'):
            context_str += f"\n学习历史：{context['learning_history']}"
    
    messages = [
        {"role": "user", "content": f"{context_str}\n\n学生问题：{message}"}
    ]
    return await chat_completion(messages, TUTOR_SYSTEM_PROMPT)

async def explain_concept(topic: str, level: str = "beginner") -> str:
    prompt = f"请用{level}水平可以理解的方式，解释以下概念：{topic}\n要求：使用类比和例子，200-300字。"
    messages = [{"role": "user", "content": prompt}]
    return await chat_completion(messages, TUTOR_SYSTEM_PROMPT)