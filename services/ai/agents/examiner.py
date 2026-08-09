"""
AI Examiner Agent - 自适应出题与评估
Generates questions, evaluates answers, tracks knowledge mastery
"""
from core.llm import chat_completion
import json

EXAMINER_SYSTEM_PROMPT = """你是一位AI出题专家，擅长根据学习内容生成高质量的练习题。
出题原则：
1. 难度自适应：根据学生当前水平调整题目难度
2. 覆盖全面：涵盖概念理解、应用分析、综合评估等层次
3. 题型多样：选择题、填空题、简答题、编程题等
4. 即时反馈：每题提供详细解析和参考答案
5. 知识巩固：针对薄弱点重点出题

请用中文出题。"""

async def generate_questions(topic: str, difficulty: str = "medium", count: int = 5, context: str = "") -> list[dict]:
    prompt = f"""请为以下主题生成{count}道{difficulty}难度的练习题：
主题：{topic}
{context}

请以JSON格式返回，格式为：
[
  {{
    "type": "choice" | "fill" | "short_answer",
    "question": "题目内容",
    "options": ["A. 选项1", "B. 选项2", ...] (仅选择题需要),
    "answer": "正确答案",
    "explanation": "详细解析"
  }}
]"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, EXAMINER_SYSTEM_PROMPT)
    
    try:
        # Extract JSON from response
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
        if json_start >= 0:
            return json.loads(result[json_start:json_end])
    except:
        pass
    return [{"type": "short_answer", "question": topic, "answer": "", "explanation": result}]

async def evaluate_answer(question: str, correct_answer: str, student_answer: str) -> dict:
    prompt = f"""题目：{question}
正确答案：{correct_answer}
学生答案：{student_answer}

请评估学生的回答，返回JSON格式：
{{
  "is_correct": true/false,
  "score": 0-100,
  "feedback": "个性化反馈",
  "hint": "如果错了，给出提示"
}}"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, EXAMINER_SYSTEM_PROMPT)
    
    try:
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start >= 0:
            return json.loads(result[json_start:json_end])
    except:
        pass
    return {"is_correct": False, "score": 0, "feedback": result, "hint": ""}