"""外部追踪回调注册测试（不安装任何追踪 SDK）"""
import litellm

from app.tools.llm import setup_external_callbacks


def test_disabled_by_default(monkeypatch):
    monkeypatch.setattr("app.tools.llm.settings.LITELLM_SUCCESS_CALLBACK", "")
    litellm.success_callback = []
    assert setup_external_callbacks() == []
    assert litellm.success_callback == []


def test_registers_named_providers(monkeypatch):
    monkeypatch.setattr(
        "app.tools.llm.settings.LITELLM_SUCCESS_CALLBACK", "langfuse, langsmith"
    )
    litellm.success_callback = []
    registered = setup_external_callbacks()
    assert registered == ["langfuse", "langsmith"]
    assert litellm.success_callback == ["langfuse", "langsmith"]
    litellm.success_callback = []


def test_tolerates_whitespace_and_empty_items(monkeypatch):
    monkeypatch.setattr(
        "app.tools.llm.settings.LITELLM_SUCCESS_CALLBACK", "  langfuse , , "
    )
    litellm.success_callback = []
    assert setup_external_callbacks() == ["langfuse"]
    litellm.success_callback = []
