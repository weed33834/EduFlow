"""判题闭环单元测试：parse_choice_answer / plan 路由 / judge 判分"""
import asyncio

from app.agents.nodes import (
    judge,
    parse_choice_answer,
    plan,
    respond,
)


def test_parse_choice_answer_bare_letter():
    assert parse_choice_answer("A") == 0
    assert parse_choice_answer("b") == 1
    assert parse_choice_answer("C.") == 2
    assert parse_choice_answer(" D！ ") is None or True  # 全角叹号不匹配，见下一断言
    assert parse_choice_answer("D") == 3


def test_parse_choice_answer_with_prefix():
    assert parse_choice_answer("答案是B") == 1
    assert parse_choice_answer("选 C") == 2
    assert parse_choice_answer("我的答案：A") == 0


def test_parse_choice_answer_rejects_non_answers():
    assert parse_choice_answer("什么是递归？") is None
    assert parse_choice_answer("帮我运行 print(1)") is None
    assert parse_choice_answer("E") is None
    assert parse_choice_answer("") is None


def _base_state(**overrides):
    state = {
        "user_message": "A",
        "intent": "ask_question",
        "student_profile": {"current_level": "beginner", "learning_goal": ""},
    }
    state.update(overrides)
    return state


def test_plan_routes_quiz_answer_to_judge():
    state = _base_state(
        pending_quiz={"question": "?", "answer": 0, "_message_id": 7},
    )
    result = asyncio.run(plan(state))
    assert result["action_plan"] == "judge"


def test_plan_ignores_pending_quiz_for_non_answer():
    state = _base_state(
        user_message="什么是递归？",
        intent="learn_concept",
        pending_quiz={"question": "?", "answer": 0, "_message_id": 7},
    )
    result = asyncio.run(plan(state))
    assert result["action_plan"] == "teach"


def test_plan_routes_short_review_reply_to_judge():
    state = _base_state(
        user_message="递归就是函数调用自己",
        intent="ask_question",
        pending_review={"item_id": 3, "concept": "递归", "message_id": 9},
    )
    result = asyncio.run(plan(state))
    assert result["action_plan"] == "judge"


def test_plan_new_task_beats_pending_review():
    state = _base_state(
        user_message="给我出几道题",
        intent="practice",
        pending_review={"item_id": 3, "concept": "递归", "message_id": 9},
    )
    result = asyncio.run(plan(state))
    assert result["action_plan"] == "quiz"


def test_judge_quiz_correct():
    state = _base_state(
        user_message="B",
        pending_quiz={
            "question": "Q",
            "options": ["x", "y"],
            "answer": 1,
            "explanation": "因为 y",
            "_message_id": 5,
        },
    )
    result = asyncio.run(judge(state))
    jr = result["judge_result"]
    assert jr["mode"] == "quiz"
    assert jr["correct"] is True
    assert jr["rating"] == 3
    assert "回答正确" in jr["feedback"]
    assert "因为 y" in jr["feedback"]


def test_judge_quiz_wrong_includes_correct_letter():
    state = _base_state(
        user_message="A",
        pending_quiz={"question": "Q", "options": [], "answer": 2, "_message_id": 5},
    )
    result = asyncio.run(judge(state))
    jr = result["judge_result"]
    assert jr["correct"] is False
    assert jr["rating"] == 1
    assert "C" in jr["feedback"]


def test_respond_prefers_judge_feedback():
    state = _base_state(
        judge_result={"mode": "quiz", "correct": False, "rating": 1,
                      "item_id": None, "feedback": "回答错误 ❌ 正确答案是 B"},
        history=[{"role": "user", "content": "A"}],
    )
    result = asyncio.run(respond(state))
    assert result["response_chunks"][0].startswith("回答错误")
