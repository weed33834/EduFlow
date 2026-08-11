"""
EduFlow AI Service - Agents 模块

导出所有智能体函数，供主程序调用。
"""
from .tutor import (
    tutor_chat,
    explain_concept,
    tutor_chat_stream,
    build_chat_messages as tutor_build_messages,
)
from .buddy import (
    buddy_chat,
    discuss_topic,
    buddy_chat_stream,
    build_chat_messages as buddy_build_messages,
)
from .examiner import generate_questions, evaluate_answer
from .planner import generate_learning_path, adjust_plan

__all__ = [
    "tutor_chat",
    "explain_concept",
    "tutor_chat_stream",
    "tutor_build_messages",
    "buddy_chat",
    "discuss_topic",
    "buddy_chat_stream",
    "buddy_build_messages",
    "generate_questions",
    "evaluate_answer",
    "generate_learning_path",
    "adjust_plan",
]

__all__ = [
    "tutor_chat",
    "explain_concept",
    "buddy_chat",
    "discuss_topic",
    "generate_questions",
    "evaluate_answer",
    "generate_learning_path",
    "adjust_plan",
]
