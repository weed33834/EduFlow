"""多轮意图上下文构造 + 降级分类器的测试"""
from app.agents.nodes import keyword_intent, understand
from app.tools.llm import format_history_for_prompt


def test_format_history_empty():
    assert format_history_for_prompt(None) == ""
    assert format_history_for_prompt([]) == ""


def test_format_history_skips_invalid_entries():
    history = [
        {"role": "user", "content": "什么是递归"},
        {"role": "", "content": "坏数据"},
        {"role": "assistant"},
        {"role": "assistant", "content": "递归是自调用"},
    ]
    out = format_history_for_prompt(history)
    assert "学生：什么是递归" in out
    assert "助手：递归是自调用" in out
    assert "坏数据" not in out


def test_format_history_truncates_to_max_turns():
    history = [{"role": "user", "content": f"消息{i}"} for i in range(10)]
    out = format_history_for_prompt(history, max_turns=3)
    assert "消息9" in out
    assert "消息7" in out
    assert "消息6" not in out


def test_format_history_long_content_clamped():
    history = [{"role": "user", "content": "长" * 500}]
    out = format_history_for_prompt(history)
    assert len(out) < 200  # 120 字上限 + 前缀


def test_keyword_intents():
    assert keyword_intent("帮我运行 print(1)") == "run_code"
    assert keyword_intent("什么是闭包？") == "learn_concept"
    assert keyword_intent("给我出几道题") == "practice"
    assert keyword_intent("你好呀") == "chitchat"
    assert keyword_intent("为什么这里会报错") == "ask_question"


def test_understand_uses_prior_history_for_context():
    """understand 应把当前消息之前的历史传给分类（降级路径下验证历史不被污染）"""
    state = {
        "user_message": "继续",
        "history": [
            {"role": "user", "content": "讲讲递归"},
            {"role": "assistant", "content": "递归是……"},
        ],
    }
    result = asyncio_run_understand(state)
    # 当前消息已追加进返回的历史，且原历史保持在前
    assert result["history"][0]["content"] == "讲讲递归"
    assert result["history"][-1] == {"role": "user", "content": "继续"}


def asyncio_run_understand(state):
    import asyncio
    return asyncio.run(understand(state))
