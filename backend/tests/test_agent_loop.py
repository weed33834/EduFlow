"""agent_loop 主循环测试：工具调用序列 / 直接回答 / 轮数上限 / 流式作答"""
import asyncio
import json

import pytest

from app.agents import loop as lp


# ── fake litellm 响应结构（对齐 OpenAI 协议） ────────────────


class _Fn:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _Call:
    def __init__(self, cid, name, arguments):
        self.id = cid
        self.function = _Fn(name, arguments)


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, msg):
        self.message = msg


class _Resp:
    def __init__(self, msg):
        self.choices = [_Choice(msg)]


def _tool_call_msg(calls):
    return _Resp(_Msg(content="", tool_calls=calls))


def _final_msg(text="好的"):
    return _Resp(_Msg(content=text, tool_calls=None))


@pytest.fixture()
def llm_env(monkeypatch):
    monkeypatch.setattr(lp.settings, "LITELLM_API_KEY", "sk-test")
    deltas_seen = []
    async def fake_stream(messages, on_delta, system_prompt="",
                          temperature=0.5, max_tokens=1200):
        on_delta("最终")
        on_delta("答案")
        # 记录作答阶段的 system 与调查结果，供断言
        fake_stream.last_messages = messages
        fake_stream.last_system = system_prompt
        return "最终答案"
    fake_stream.last_messages = []
    fake_stream.last_system = ""
    monkeypatch.setattr(lp, "chat_completion_streaming", fake_stream)
    return fake_stream


def _state(**kw):
    base = {
        "user_message": "帮我看看这段代码为什么报错",
        "user_id": 7,
        "student_profile": {"current_level": "beginner", "learning_goal": ""},
        "history": [
            {"role": "user", "content": "之前的消息"},
            {"role": "assistant", "content": "之前的回复"},
            {"role": "user", "content": "帮我看看这段代码为什么报错"},
        ],
    }
    base.update(kw)
    return base


def test_tool_call_then_answer(monkeypatch, llm_env):
    """第 1 轮调用 run_code，第 2 轮停止 → 进入流式作答；工具轨迹被记录"""
    executed = []

    async def fake_execute(name, args_json, user_id=""):
        executed.append((name, json.loads(args_json)))
        return {"success": True, "stdout": "ZeroDivisionError", "stderr": ""}

    monkeypatch.setattr(lp, "execute_tool", fake_execute)

    responses = iter([
        _tool_call_msg([_Call("c1", "run_code",
                              json.dumps({"code": "1/0"}))]),
        _final_msg(),
    ])
    seen_kwargs = {}

    async def fake_acompletion(**kwargs):
        seen_kwargs.update(kwargs)
        return next(responses)

    monkeypatch.setattr(lp.litellm, "acompletion", fake_acompletion)

    state = asyncio.run(lp.agent_loop(_state(
        tool_context={"knowledge_context": [], "memory_context": []},
    )))

    assert executed == [("run_code", {"code": "1/0"})]
    assert state["teach_content"] == "最终答案"
    assert state["tool_trace"][0]["tool"] == "run_code"
    assert state["tool_trace"][0]["ok"] is True
    # 作答阶段带导师 system prompt
    assert "导师" in llm_env.last_system
    # 工具结果进入作答上下文
    user_texts = [m["content"] for m in llm_env.last_messages if m["role"] == "user"]
    assert any("run_code" in t for t in user_texts)
    # 规划期绑定了工具
    assert seen_kwargs.get("tools") is not None


def test_zero_tool_calls_direct_answer(monkeypatch, llm_env):
    """第 1 轮就不调工具 → 直接进入作答"""

    async def fake_acompletion(**kwargs):
        return _final_msg()

    monkeypatch.setattr(lp.litellm, "acompletion", fake_acompletion)

    state = asyncio.run(lp.agent_loop(_state()))
    assert state["teach_content"] == "最终答案"
    assert state["tool_trace"] == []
    assert any("未调用任何工具" in m["content"]
               for m in llm_env.last_messages if m["role"] == "user")


def test_max_rounds_forced_finish(monkeypatch, llm_env):
    """模型一直要求调工具 → 4 轮后强制收尾"""
    counter = {"n": 0}

    def endless(**kwargs):
        counter["n"] += 1
        return _tool_call_msg([
            _Call(f"c{counter['n']}", "search_knowledge",
                  json.dumps({"query": f"q{counter['n']}"})),
        ])

    async def fake_execute(name, args_json, user_id=""):
        return {"results": []}

    async def acompletion(**kwargs):
        return endless(**kwargs)

    monkeypatch.setattr(lp.litellm, "acompletion", acompletion)
    monkeypatch.setattr(lp, "execute_tool", fake_execute)

    state = asyncio.run(lp.agent_loop(_state()))
    assert counter["n"] == lp.MAX_TOOL_ROUNDS
    assert len(state["tool_trace"]) == lp.MAX_TOOL_ROUNDS
    assert state["teach_content"] == "最终答案"


def test_tool_error_recorded_not_raised(monkeypatch, llm_env):
    """工具抛错应转为 error 载荷继续循环，而不是中断 Agent"""
    async def boom(name, args_json, user_id=""):
        return {"error": "sandbox down"}

    monkeypatch.setattr(lp, "execute_tool", boom)

    responses = iter([
        _tool_call_msg([_Call("c1", "run_code", "{}")]),
        _final_msg(),
    ])

    async def fake_acompletion(**k):
        return next(responses)

    monkeypatch.setattr(lp.litellm, "acompletion", fake_acompletion)

    state = asyncio.run(lp.agent_loop(_state()))
    assert state["tool_trace"][0]["ok"] is False
    assert state["teach_content"] == "最终答案"
