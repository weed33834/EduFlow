"""
AI Planner Agent - 学习路径规划

根据学习目标、当前水平、可用时间和偏好，制定个性化的学习路径。
返回格式统一为 {title, description, estimated_duration, milestones, modules}。
未配置 API Key 时返回结构化的通用学习路径。
"""
import json
from typing import Optional, Union

from core.llm import chat_completion, is_llm_available

PLANNER_SYSTEM_PROMPT = """你是一位 AI 学习规划师，擅长为学生制定个性化的学习路径。
规划原则：
1. 目标导向：根据学生的学习目标制定路径
2. 循序渐进：从基础到进阶，合理安排学习顺序
3. 时间合理：考虑学生可用时间，制定可行的计划
4. 动态调整：根据学习进度和反馈及时调整
5. 全面评估：考虑前置知识、学习风格和偏好

请用中文输出。所有返回必须是合法的 JSON 对象。"""


async def generate_learning_path(
    goal: str,
    level: str = "beginner",
    duration_weeks: int = 12,
    preferences: Union[list, dict, str, None] = None,
) -> dict:
    """生成学习路径。

    根据学习目标、水平、时长和偏好生成结构化学习路径。
    未配置 API Key 时返回结构化的通用学习路径。

    Args:
        goal: 学习目标描述。
        level: 当前水平，beginner / intermediate / advanced。
        duration_weeks: 计划学习的总周数。
        preferences: 学习偏好，可为列表、字典或字符串。

    Returns:
        学习路径字典，格式为：
        {title, description, estimated_duration, milestones, modules}
    """
    # 降级：返回结构化通用学习路径
    if not is_llm_available():
        return _fallback_learning_path(goal, level, duration_weeks, preferences)

    pref_str = _format_preferences(preferences)
    prompt = f"""学习目标：{goal}
当前水平：{level}
计划学习周期：{duration_weeks} 周
学习偏好：{pref_str or '无'}

请生成一个个性化的学习路径，以 JSON 格式返回，严格遵循以下结构：
{{
  "title": "路径标题",
  "description": "路径整体描述",
  "estimated_duration": "预计完成时间（如 12 周 / 3 个月）",
  "milestones": [
    {{
      "title": "里程碑名称",
      "description": "里程碑描述",
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
    result = await chat_completion(messages, PLANNER_SYSTEM_PROMPT, agent_type="planner")

    plan = _parse_json(result)
    if isinstance(plan, dict) and plan:
        return _normalize_plan(plan, goal, level, duration_weeks)

    # 解析失败，回退到通用路径
    return _fallback_learning_path(goal, level, duration_weeks, preferences)


async def adjust_plan(feedback: str, current_plan: dict) -> dict:
    """调整学习计划。

    根据学生反馈调整现有学习计划。
    未配置 API Key 时基于反馈做规则化的简单调整。

    Args:
        feedback: 学生的反馈内容。
        current_plan: 当前的学习计划。

    Returns:
        调整后的学习计划字典。
    """
    # 降级：基于反馈做规则化调整
    if not is_llm_available():
        return _fallback_adjust_plan(feedback, current_plan)

    prompt = f"""当前学习计划：{json.dumps(current_plan, ensure_ascii=False)}
学生反馈：{feedback}

请根据反馈调整学习计划，以 JSON 格式返回调整后的完整计划。
返回结构必须与原计划一致：{{
  "title": "...",
  "description": "...",
  "estimated_duration": "...",
  "milestones": [...],
  "modules": [...]
}}"""
    messages = [{"role": "user", "content": prompt}]
    result = await chat_completion(messages, PLANNER_SYSTEM_PROMPT, agent_type="planner")

    adjusted = _parse_json(result)
    if isinstance(adjusted, dict) and adjusted:
        return _normalize_plan(adjusted, current_plan.get("title", ""), "", 0)

    # 解析失败，回退到规则化调整
    return _fallback_adjust_plan(feedback, current_plan)


# ---------------------------------------------------------------------------
# 降级：结构化通用学习路径
# ---------------------------------------------------------------------------

def _fallback_learning_path(
    goal: str,
    level: str,
    duration_weeks: int,
    preferences: Union[list, dict, str, None],
) -> dict:
    """构建降级学习路径：返回结构化的通用学习路径。"""
    pref_str = _format_preferences(preferences)
    level_label = {
        "beginner": "入门",
        "intermediate": "进阶",
        "advanced": "高级",
    }.get(level, level)

    total_weeks = max(duration_weeks, 1) if duration_weeks else 12

    return {
        "title": f"「{goal}」{level_label}学习路径",
        "description": (
            f"这是一份围绕「{goal}」制定的结构化通用学习路径，"
            f"适合{level_label}阶段的学习者，预计 {total_weeks} 周完成。"
            "由于当前处于降级模式（未配置 OPENAI_API_KEY），路径基于通用学习规律生成，"
            "建议你根据自身实际情况灵活调整节奏和重点。"
            + (f"\n已纳入你的学习偏好：{pref_str}。" if pref_str else "")
        ),
        "estimated_duration": f"{total_weeks} 周",
        "milestones": [
            {
                "title": "里程碑一：夯实基础",
                "description": f"掌握「{goal}」所需的基础概念和核心知识，建立整体认知框架。",
                "estimated_hours": total_weeks * 2,
                "order": 1,
            },
            {
                "title": "里程碑二：深入实践",
                "description": f"通过实际练习加深对「{goal}」的理解，能够独立完成中等难度的任务。",
                "estimated_hours": total_weeks * 3,
                "order": 2,
            },
            {
                "title": "里程碑三：综合应用与拓展",
                "description": f"将「{goal}」融会贯通，完成综合性项目，并向相关领域拓展。",
                "estimated_hours": total_weeks * 2,
                "order": 3,
            },
        ],
        "modules": [
            {
                "title": "模块 1：导论与基础概念",
                "description": (
                    f"了解「{goal}」的整体概貌、发展脉络和核心术语，建立初步认知。"
                    "建议阅读入门资料、观看导论视频，并动手完成第一个小练习。"
                ),
                "order": 1,
                "estimated_minutes": 240,
                "topics": [
                    f"{goal} 的基本概念与术语",
                    "学习「{goal}」的前置知识",
                    "环境搭建与工具准备",
                    "第一个 Hello World 练习",
                ],
            },
            {
                "title": "模块 2：核心知识体系",
                "description": (
                    f"系统学习「{goal}」的核心知识点，理解各部分之间的联系与原理。"
                    "建议边学边做笔记，遇到不懂的概念及时回顾。"
                ),
                "order": 2,
                "estimated_minutes": 480,
                "topics": [
                    f"{goal} 的核心原理",
                    "关键特性与工作机制",
                    "常见模式与最佳实践",
                    "阶段性自测练习",
                ],
            },
            {
                "title": "模块 3：实战练习与项目",
                "description": (
                    f"通过实战项目将「{goal}」的理论知识转化为实际能力。"
                    "建议从模仿开始，逐步过渡到独立完成。"
                ),
                "order": 3,
                "estimated_minutes": 600,
                "topics": [
                    "小型实战项目（入门级）",
                    "中型综合项目（进阶级）",
                    "代码审查与优化",
                    "常见问题排查与调试",
                ],
            },
            {
                "title": "模块 4：进阶提升与拓展",
                "description": (
                    f"在掌握「{goal}」的基础上，探索进阶主题和相关领域，"
                    "形成更完整的知识体系，培养举一反三的能力。"
                ),
                "order": 4,
                "estimated_minutes": 360,
                "topics": [
                    f"{goal} 的高阶主题",
                    "性能优化与工程化实践",
                    "相关领域知识拓展",
                    "学习成果总结与复盘",
                ],
            },
        ],
    }


def _fallback_adjust_plan(feedback: str, current_plan: dict) -> dict:
    """降级计划调整：基于反馈做规则化的简单调整。"""
    if not isinstance(current_plan, dict) or not current_plan:
        # 若没有原计划，直接生成一份新的通用路径
        return _fallback_learning_path(feedback or "自主学习", "beginner", 12, None)

    # 深拷贝原计划，避免修改入参
    import copy
    adjusted = copy.deepcopy(current_plan)

    feedback_lower = (feedback or "").lower()
    note = (
        "\n\n[降级模式调整说明] 当前未配置 OPENAI_API_KEY，已根据你的反馈"
        "「" + (feedback or "") + "」做规则化调整。"
    )

    # 根据反馈关键词做简单调整
    if any(kw in feedback_lower for kw in ["太慢", "进度慢", "加快", "提速", "太长"]):
        # 加快节奏：缩减时长
        for m in adjusted.get("modules", []):
            if "estimated_minutes" in m and isinstance(m["estimated_minutes"], int):
                m["estimated_minutes"] = max(int(m["estimated_minutes"] * 0.75), 30)
        note += "检测到希望加快进度，已将各模块预计时长缩减约 25%。"
    elif any(kw in feedback_lower for kw in ["太难", "吃力", "跟不上", "太难了"]):
        # 降低难度：增加时长、补充基础
        for m in adjusted.get("modules", []):
            if "estimated_minutes" in m and isinstance(m["estimated_minutes"], int):
                m["estimated_minutes"] = int(m["estimated_minutes"] * 1.3)
        note += "检测到学习吃力，已延长各模块学习时长约 30%，建议放慢节奏、多做基础练习。"
    elif any(kw in feedback_lower for kw in ["太简单", "太容易", "加快难度", "挑战"]):
        note += "检测到希望提升难度，建议跳过已掌握的基础模块，重点攻克进阶和实战部分。"
    elif any(kw in feedback_lower for kw in ["更多练习", "加题", "练习题", "实战"]):
        note += "检测到希望增加练习，建议在每个模块后补充对应的练习题和小项目。"
    else:
        note += "由于无法进行语义分析，仅原样保留计划并附上你的反馈，建议配置 AI 服务后获得更精准的调整。"

    # 追加调整说明到描述
    desc = adjusted.get("description", "")
    adjusted["description"] = (desc + note).strip()
    adjusted["adjustment_feedback"] = feedback or ""
    return adjusted


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _format_preferences(preferences: Union[list, dict, str, None]) -> str:
    """将偏好格式化为可读字符串。"""
    if not preferences:
        return ""
    if isinstance(preferences, str):
        return preferences
    if isinstance(preferences, (list, tuple)):
        return "、".join(str(p) for p in preferences)
    if isinstance(preferences, dict):
        return "、".join(f"{k}:{v}" for k, v in preferences.items())
    return str(preferences)


def _parse_json(text: str):
    """从 LLM 返回的文本中提取 JSON 对象。"""
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _normalize_plan(plan: dict, goal: str, level: str, duration_weeks: int) -> dict:
    """规范化学习路径结构，确保字段完整。"""
    total_weeks = max(duration_weeks, 1) if duration_weeks else 12
    return {
        "title": plan.get("title") or f"「{goal}」学习路径",
        "description": plan.get("description", ""),
        "estimated_duration": plan.get("estimated_duration") or f"{total_weeks} 周",
        "milestones": plan.get("milestones", []) or [],
        "modules": plan.get("modules", []) or [],
    }
