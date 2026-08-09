"""
AI Planner Agent - 学习路径规划
Creates personalized learning plans and schedules
"""
from core.llm import chat_completion
import json

PLANNER_SYSTEM_PROMPT = """你是一位AI学习规划师，擅长为学生制定个性化的学习路径。
规划原则：
1. 目标导向：根据学生的学习目标制定路径
2. 循序渐进：从基础到进阶，合理安排学习顺序
3. 时间合理：考虑学生可用时间，制定可行的计划
4. 动态调整：根据学习进度和反馈及时调整
5. 全面评估：考虑前置知识、学习风格和偏好

请用中文输出。"""

async def generate_learning_path(goal: str, current_level: str = "beginner", available_hours: int = 5, topics: list[str] = None) -> dict:
    topic_str = f"，重点关注：{', '.join(topics)}" if topics else ""
    prompt = f"""学习目标：{goal}
当前水平：{current_level}
每周可用学习时间：{available_hours}小时{topic_str}

请生成一个学习路径，以JSON格式返回：
{{
  "title": "路径标题",
  "description": "路径描述",
  "estimated_duration": "预计完成时间",
  "milestones": [
    {{
      "title": "里程碑名称",
      "description": "描述",
      "estimated_hours": 预计小时数,
      "order": 1
    }}
  ],
  "modules": [
    {{
      "title": "模块名称",
      "description": "模块描述",
      "order": 1,
      "estimated_minutes": 预计分钟数,
      "topics": ["知识点1", "知识点2"]
    }}
  ]
}}"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, PLANNER_SYSTEM_PROMPT)
    
    try:
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start >= 0:
            return json.loads(result[json_start:json_end])
    except:
        pass
    return {"title": goal, "description": result, "modules": []}

async def adjust_plan(feedback: str, current_plan: dict) -> dict:
    prompt = f"""当前学习计划：{json.dumps(current_plan, ensure_ascii=False)}
学生反馈：{feedback}

请根据反馈调整学习计划，以JSON格式返回调整后的完整计划。"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, PLANNER_SYSTEM_PROMPT)
    
    try:
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start >= 0:
            return json.loads(result[json_start:json_end])
    except:
        pass
    return current_plan