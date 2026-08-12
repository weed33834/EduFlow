"""
多模态能力抽象层

用户通过 OPENAI_BASE_URL + OPENAI_API_KEY 接入任意兼容端点。
不同端点提供的模型能力不同（可能只有 chat，也可能有 tts/asr/image/video）。
本模块负责：
1. 定义能力枚举 Capability
2. 拉取 /v1/models 并按模型名启发式分类，识别端点具备哪些能力
3. 提供「产品功能 → 所需能力」映射，以及能力缺失时的降级判断与提示
"""
from __future__ import annotations

import httpx
from enum import Enum
from typing import Optional


class Capability(str, Enum):
    CHAT = "chat"          # 文本对话 / 讲解稿 / 规划 / 出题
    IMAGE = "image"        # 文生图 / 配图
    TTS = "tts"            # 语音合成（配音）
    ASR = "asr"            # 语音转写
    EMBEDDING = "embedding"  # 向量检索
    VIDEO = "video"        # 文生视频

    def __str__(self) -> str:
        return self.value


# 产品功能 → 所需能力 的映射（能力注册表）
FEATURE_REQUIREMENTS: dict[str, set[Capability]] = {
    "chat": {Capability.CHAT},
    "generate_questions": {Capability.CHAT},
    "plan": {Capability.CHAT},
    "ppt": {Capability.CHAT},
    "narration_text": {Capability.CHAT},
    "image": {Capability.IMAGE},
    "tts": {Capability.TTS},
    "asr": {Capability.ASR},
    "presentation_video": {Capability.CHAT, Capability.TTS},
    "text_to_video": {Capability.VIDEO},
}

FEATURE_LABELS: dict[str, str] = {
    "chat": "AI 对话",
    "generate_questions": "AI 出题",
    "plan": "学习规划",
    "ppt": "PPT 生成",
    "narration_text": "讲解稿生成",
    "image": "配图生成",
    "tts": "语音配音",
    "asr": "语音转写",
    "presentation_video": "AI 讲解视频",
    "text_to_video": "文生视频",
}

CAPABILITY_LABELS: dict[str, str] = {
    "chat": "文本对话(LLM)",
    "image": "文生图",
    "tts": "语音合成(TTS)",
    "asr": "语音转写(ASR)",
    "embedding": "向量检索",
    "video": "文生视频",
}

# 模型名 → 能力分类规则（按顺序匹配，命中即返回）
_CAP_KEYWORDS: list[tuple[Capability, tuple[str, ...]]] = [
    (Capability.TTS, ("-tts", "_tts", "tts-1", "audio-speech", "-speech")),
    (Capability.ASR, ("-asr", "_asr", "-transcri", "whisper")),
    (Capability.IMAGE, ("image", "dall-e", "flux", "sdxl", "stable-diffusion", "cogview", "step-image", "midjourney", "seedream")),
    (Capability.VIDEO, ("video", "sora", "kling", "runway", "pika", "veo", "step-video", "hailuo", "wan-", "cogvideo")),
    (Capability.EMBEDDING, ("embed", "bge-", "text-embedding")),
    (Capability.CHAT, ("deepseek", "gpt", "qwen", "glm", "kimi", "claude", "gemini", "minimax", "sensenova", "step-", "kat-", "mistral", "llama", "phi", "yi-", "doubao", "ernie", "hunyuan", "moonshot")),
]


def classify_model(model_id: str) -> Optional[Capability]:
    """根据模型名识别其主要能力。未知返回 None。"""
    if not model_id:
        return None
    m = model_id.lower()
    for cap, kws in _CAP_KEYWORDS:
        for kw in kws:
            if kw in m:
                return cap
    return None


async def detect_capabilities(
    base_url: str, api_key: str, timeout: float = 10.0
) -> dict:
    """拉取 /v1/models 并识别端点具备的全部能力。"""
    caps: set[Capability] = set()
    models_by_cap: dict[str, list[str]] = {}
    chat_models: list[str] = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("data", []):
                    mid = m.get("id", "")
                    cap = classify_model(mid)
                    if cap:
                        caps.add(cap)
                        models_by_cap.setdefault(cap.value, []).append(mid)
                        if cap == Capability.CHAT:
                            chat_models.append(mid)
    except Exception:
        pass

    if not caps:
        caps.add(Capability.CHAT)

    features: dict[str, bool] = {}
    missing: dict[str, list[str]] = {}
    for feat, req in FEATURE_REQUIREMENTS.items():
        lacks = [c.value for c in req if c not in caps]
        features[feat] = not lacks
        missing[feat] = lacks

    return {
        "capabilities": {c.value: (c in caps) for c in Capability},
        "models": models_by_cap,
        "chat_models": chat_models,
        "features": features,
        "missing": missing,
        "labels": CAPABILITY_LABELS,
        "feature_labels": FEATURE_LABELS,
    }


def build_availability_hint(feature: str, missing: list[str]) -> str:
    """生成面向用户的能力缺失提示。"""
    if not missing:
        return ""
    names = "、".join(CAPABILITY_LABELS.get(m, m) for m in missing)
    return (
        f"功能「{FEATURE_LABELS.get(feature, feature)}」需要模型能力：{names}，"
        f"当前接入的模型端点未提供。请在设置中接入具备该能力的模型后重试。"
    )
