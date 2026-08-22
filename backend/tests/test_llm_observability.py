"""LLM 调用可观测性日志测试（mock litellm，不联网）"""
import asyncio
import logging

from app.tools import llm


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Delta:
    def __init__(self, content):
        self.content = content


class _StreamChoice:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Chunk:
    def __init__(self, content):
        self.choices = [_StreamChoice(content)]


async def _fake_acompletion(**kwargs):
    return _Resp("你好")


def _fake_stream_response(chunks):
    class _Stream:
        def __init__(self, items):
            self._items = iter(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self._items)
            except StopIteration:
                raise StopAsyncIteration

    async def _call(**kwargs):
        return _Stream(chunks)
    return _call


def test_chat_completion_logs_call(caplog, monkeypatch):
    monkeypatch.setattr(llm.settings, "LITELLM_API_KEY", "sk-test")
    monkeypatch.setattr(llm.litellm, "acompletion", _fake_acompletion)

    with caplog.at_level(logging.INFO, logger="app.tools.llm"):
        out = asyncio.run(llm.chat_completion([{"role": "user", "content": "hi"}]))

    assert out == "你好"
    records = [r for r in caplog.records if "llm.call" in r.getMessage()]
    assert records, "应产生 llm.call 日志"
    msg = records[-1].getMessage()
    assert "stream=false" in msg
    assert "out_chars=2" in msg
    assert "dur_ms=" in msg


def test_streaming_logs_call(caplog, monkeypatch):
    monkeypatch.setattr(llm.settings, "LITELLM_API_KEY", "sk-test")
    monkeypatch.setattr(
        llm.litellm, "acompletion",
        _fake_stream_response([_Chunk("你"), _Chunk("好")]),
    )

    deltas: list[str] = []
    with caplog.at_level(logging.INFO, logger="app.tools.llm"):
        out = asyncio.run(llm.chat_completion_streaming(
            [{"role": "user", "content": "hi"}], on_delta=deltas.append,
        ))

    assert out == "你好"
    assert deltas == ["你", "好"]
    records = [r for r in caplog.records if "llm.call" in r.getMessage()]
    assert records and "stream=true" in records[-1].getMessage()
    assert "out_chars=2" in records[-1].getMessage()


def test_failure_logs_warning_and_reraises(caplog, monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(llm.settings, "LITELLM_API_KEY", "sk-test")
    monkeypatch.setattr(llm.litellm, "acompletion", boom)

    with caplog.at_level(logging.WARNING, logger="app.tools.llm"):
        try:
            asyncio.run(llm.chat_completion([{"role": "user", "content": "hi"}]))
            raised = False
        except RuntimeError:
            raised = True

    assert raised, "异常应向上传播（行为不变）"
    warnings = [r for r in caplog.records if "llm.call failed" in r.getMessage()]
    assert warnings and warnings[0].exc_info, "失败日志应带堆栈"


def test_unavailable_short_circuits_without_log(caplog, monkeypatch):
    monkeypatch.setattr(llm.settings, "LITELLM_API_KEY", "")
    with caplog.at_level(logging.INFO, logger="app.tools.llm"):
        out = asyncio.run(llm.chat_completion([{"role": "user", "content": "hi"}]))
    assert out == ""
    assert not [r for r in caplog.records if "llm.call" in r.getMessage()]
