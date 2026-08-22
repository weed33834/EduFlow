"""工具注册表测试：schema 完整性 / 分发 / 错误自愈 / user_id 注入"""
import asyncio
import json
from unittest.mock import patch

import pytest

from app.agents import tools_registry as reg


def test_schemas_wellformed():
    assert {t["function"]["name"] for t in reg.TOOLS} == set(reg.AVAILABLE_TOOLS)
    for t in reg.TOOLS:
        fn = t["function"]
        assert t["type"] == "function"
        assert fn["description"], f"{fn['name']} 缺描述"
        assert fn["parameters"]["type"] == "object"
        assert isinstance(fn["parameters"].get("required"), list)


def test_dispatch_unknown_tool_returns_error():
    out = asyncio.run(reg.execute_tool("nope", "{}"))
    assert "error" in out and "未知工具" in out["error"]


def test_dispatch_invalid_json_returns_error():
    out = asyncio.run(reg.execute_tool("run_code", "{not json"))
    assert "error" in out and "JSON" in out["error"]


def test_dispatch_non_object_json_returns_error():
    out = asyncio.run(reg.execute_tool("run_code", "[1,2]"))
    assert "error" in out


def test_run_code_dispatch(monkeypatch):
    captured = {}

    async def fake_execute(code):
        captured["code"] = code
        return {"success": True, "stdout": "1\n", "stderr": "", "exit_code": 0}

    monkeypatch.setattr("app.tools.sandbox.execute_code", fake_execute)
    out = asyncio.run(reg.execute_tool(
        "run_code", json.dumps({"code": "print(1)"}),
    ))
    assert out["success"] is True and captured["code"] == "print(1)"


def test_search_memory_injects_user_id(monkeypatch):
    captured = {}

    class _FakeMemoryMod:
        pass

    async def fake_search(user_id, query):
        captured.update(user_id=user_id, query=query)
        return []

    from app.tools import memory as memory_mod
    monkeypatch.setattr(memory_mod, "search_memory", fake_search)

    # 模型试图传别人的 user_id 也应被覆盖
    out = asyncio.run(reg.execute_tool(
        "search_memory",
        json.dumps({"query": "递归", "user_id": "999"}),
        user_id=42,
    ))
    assert out == {"results": []}
    assert captured == {"user_id": "42", "query": "递归"}


def test_search_knowledge_dispatch(monkeypatch):
    async def fake_search(query, top_k=3):
        return [{"text": f"关于{query}", "score": 0.9}]

    from app.tools import knowledge as knowledge_mod
    monkeypatch.setattr(knowledge_mod, "search_knowledge", fake_search)

    out = asyncio.run(reg.execute_tool(
        "search_knowledge", json.dumps({"query": "闭包"}),
    ))
    assert out["results"][0]["text"] == "关于闭包"


def test_create_quiz_degraded_fallback(monkeypatch):
    """无 LLM key 时 create_quiz 走离线兜底题"""
    monkeypatch.setattr("app.agents.nodes.settings.LITELLM_API_KEY", "")
    out = asyncio.run(reg.execute_tool(
        "create_quiz", json.dumps({"topic": "递归", "level": "beginner"}),
    ))
    assert out["question"]
    assert len(out["options"]) == 4
    assert out["answer"] in (0, 1, 2, 3)


def test_tool_exception_becomes_error_payload(monkeypatch):
    async def boom(args):
        raise RuntimeError("sandbox exploded")

    monkeypatch.setitem(reg.DISPATCH, "run_code", boom)
    out = asyncio.run(reg.execute_tool("run_code", "{}"))
    assert "sandbox exploded" in out.get("error", "")
