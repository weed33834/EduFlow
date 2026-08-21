"""Agent 状态定义"""
from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    # 输入
    user_message: str
    user_id: int
    session_id: int
    history: list[dict]  # 对话历史

    # 中间状态
    intent: str
    student_profile: dict
    action_plan: str

    # 工具执行结果
    teach_content: str
    quiz_question: dict
    review_items: list[dict]  # 到期的复习项（FSRS）
    review_content: str  # 复习内容
    response_chunks: list[str]
