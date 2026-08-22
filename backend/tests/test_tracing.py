"""本地 JSONL 追踪器测试：span 写入 / 上下文关联 / 失败不影响主流程"""
import asyncio
import json
from pathlib import Path

import pytest

import app.tools.tracing as tr
from app.tools import llm


@pytest.fixture()
def trace_env(tmp_path, monkeypatch):
    monkeypatch.setattr(tr.settings, "TRACE_ENABLED", True)
    monkeypatch.setattr(tr.settings, "TRACE_DIR", str(tmp_path))
    # 重置上下文，避免用例间串扰
    tr.trace_id_var.set("")
    tr.session_id_var.set(0)
    return tmp_path


def _read(tmp: Path):
    f = tmp / "traces.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_disabled_writes_nothing(trace_env, monkeypatch):
    monkeypatch.setattr(tr.settings, "TRACE_ENABLED", False)
    tr.record_span("llm.call")
    assert _read(trace_env) == []


def test_span_written_with_context(trace_env):
    tr.trace_id_var.set("abc123")
    tr.session_id_var.set(42)
    tr.record_span(
        "llm.call", model="gpt-x", dur_ms=123.4,
        out_chars=88, stream=True, ok=True,
    )
    spans = _read(trace_env)
    assert len(spans) == 1
    s = spans[0]
    assert s["trace_id"] == "abc123"
    assert s["session_id"] == 42
    assert s["model"] == "gpt-x"
    assert s["dur_ms"] == 123.4
    assert s["out_chars"] == 88
    assert s["stream"] is True


def test_error_span_includes_message(trace_env):
    tr.record_span("llm.call", stream=False, ok=False, error="boom" * 200)
    s = _read(trace_env)[0]
    assert s["ok"] is False
    assert len(s["error"]) <= 300


def test_llm_failure_records_span(caplog, monkeypatch, trace_env):
    """LLM 报错时追踪 span 也要落盘（ok=false）"""
    async def boom(**kwargs):
        raise RuntimeError("api down")

    monkeypatch.setattr(llm.settings, "LITELLM_API_KEY", "sk-test")
    monkeypatch.setattr(llm.litellm, "acompletion", boom)
    tr.trace_id_var.set("t-error")

    with pytest.raises(RuntimeError):
        asyncio.run(llm.chat_completion([{"role": "user", "content": "hi"}]))

    spans = _read(trace_env)
    assert spans and spans[-1]["ok"] is False and spans[-1]["error"] == "api down"


def test_write_failure_does_not_raise(trace_env, monkeypatch):
    """磁盘不可写时 record_span 必须静默降级"""
    class BrokenDir:
        def mkdir(self, *a, **k):
            raise OSError("disk full")

        def __truediv__(self, name):
            raise OSError("disk full")

    monkeypatch.setattr(tr, "_trace_file", lambda: Path("Z:/nope/x.jsonl"))
    tr.record_span("llm.call")  # 不应抛异常
