"""安全配置测试：生产模式弱密钥 fail-fast"""
import pytest

from app.config import settings
from app.main import assert_production_security


def test_dev_mode_allows_weak_secret(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "dev")
    monkeypatch.setattr(settings, "JWT_SECRET", "change-me-in-production")
    assert_production_security()  # 不应抛异常


def test_production_rejects_weak_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    for weak in ("change-me", "change-me-in-production", ""):
        monkeypatch.setattr(settings, "JWT_SECRET", weak)
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            assert_production_security()


def test_production_rejects_missing_llm_key(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "a-strong-secret-value")
    monkeypatch.setattr(settings, "LITELLM_API_KEY", "")
    with pytest.raises(RuntimeError, match="LITELLM_API_KEY"):
        assert_production_security()


def test_production_passes_with_strong_config(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "a-strong-secret-value")
    monkeypatch.setattr(settings, "LITELLM_API_KEY", "sk-test")
    assert_production_security()
