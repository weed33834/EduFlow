"""
模型端点运行时配置

允许用户在前端配置模型端点（api_key / base_url / 各模型名），
配置持久化到本地 JSON 文件，运行时覆盖环境变量默认值。

安全：api_key 存于服务端文件；对外接口只返回掩码，不回传明文。
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

# 配置文件路径（可用环境变量覆盖）
_CONFIG_PATH = os.environ.get(
    "MODEL_CONFIG_PATH",
    str(Path(__file__).resolve().parent.parent / "model_config.json"),
)

_lock = threading.Lock()
_cache: dict | None = None


def _defaults() -> dict:
    from core.config import settings

    return {
        "api_key": settings.OPENAI_API_KEY or "",
        "base_url": settings.OPENAI_BASE_URL or "",
        "llm_model": settings.LLM_MODEL,
        "tts_model": settings.TTS_MODEL or "",
        "asr_model": settings.ASR_MODEL or "",
        "image_model": settings.IMAGE_MODEL or "",
        "video_model": settings.VIDEO_MODEL or "",
        "tts_voice": settings.TTS_VOICE,
    }


def get_config(force_reload: bool = False) -> dict:
    """读取当前生效的模型配置（默认 + 文件覆盖）。"""
    global _cache
    with _lock:
        if _cache is None or force_reload:
            cfg = _defaults()
            if os.path.exists(_CONFIG_PATH):
                try:
                    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for k, v in data.items():
                        if v is not None and str(v) != "":
                            cfg[k] = v
                except Exception:
                    pass
            _cache = cfg
        return dict(_cache)


def save_config(patch: dict) -> dict:
    """合并保存配置（只更新传入的字段）。"""
    global _cache
    with _lock:
        cfg = get_config(force_reload=True)
        for k, v in patch.items():
            if v is not None:
                cfg[k] = v
        Path(_CONFIG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        _cache = cfg
        return dict(cfg)


def masked_config() -> dict:
    """对外返回：api_key 脱敏，其它字段明文。"""
    cfg = get_config()
    out = dict(cfg)
    ak = cfg.get("api_key", "")
    if len(ak) > 8:
        out["api_key"] = ak[:4] + "****" + ak[-4:]
    else:
        out["api_key"] = "****" if ak else ""
    out["has_api_key"] = bool(ak)
    return out
