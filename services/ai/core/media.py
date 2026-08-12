"""
媒体能力接入层（TTS / ASR / 文生图 / 文生视频）

通过 httpx 调用 OpenAI 兼容端点的媒体接口：
- TTS:   POST {base}/audio/speech          → 音频字节
- ASR:   POST {base}/audio/transcriptions   → 转写文本
- 文生图: POST {base}/images/generations    → 图片 url/b64
- 文生视频: POST {base}/videos/generations  → 视频 url（异步任务，尽力而为）

所有函数返回 (ok, result)；失败时 ok=False 并带错误信息，由上层降级。
"""
from __future__ import annotations

import base64

import httpx


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


async def tts(
    base_url: str,
    api_key: str,
    model: str,
    text: str,
    voice: str = "default",
    response_format: str = "mp3",
    timeout: float = 60.0,
) -> tuple[bool, bytes | str]:
    """文本转语音。成功返回 (True, 音频字节)。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/audio/speech",
                headers=_headers(api_key),
                json={"model": model, "input": text, "voice": voice, "response_format": response_format},
            )
            if resp.status_code == 200:
                return True, resp.content
            return False, f"TTS 失败: {resp.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"TTS 请求异常: {str(e)[:200]}"


async def asr(
    base_url: str,
    api_key: str,
    model: str,
    audio_bytes: bytes,
    filename: str = "audio.mp3",
    timeout: float = 60.0,
) -> tuple[bool, str]:
    """语音转写。成功返回 (True, 文本)。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/audio/transcriptions",
                headers=_headers(api_key),
                data={"model": model},
                files={"file": (filename, audio_bytes, "application/octet-stream")},
            )
            if resp.status_code == 200:
                return True, resp.json().get("text", "")
            return False, f"ASR 失败: {resp.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"ASR 请求异常: {str(e)[:200]}"


async def image(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str = "1024x1024",
    timeout: float = 90.0,
) -> tuple[bool, bytes | str]:
    """文生图。成功返回 (True, 图片字节)。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/images/generations",
                headers=_headers(api_key),
                json={"model": model, "prompt": prompt, "size": size, "n": 1},
            )
            if resp.status_code != 200:
                return False, f"文生图失败: {resp.text[:200]}"
            data = resp.json()
            item = (data.get("data") or [{}])[0]
            if item.get("b64_json"):
                return True, base64.b64decode(item["b64_json"])
            if item.get("url"):
                img = await client.get(item["url"])
                if img.status_code == 200:
                    return True, img.content
            return False, "文生图返回无有效图片"
    except Exception as e:  # noqa: BLE001
        return False, f"文生图请求异常: {str(e)[:200]}"


async def video(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: float = 30.0,
) -> tuple[bool, dict]:
    """文生视频（异步任务）。成功返回 (True, 任务信息)。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/videos/generations",
                headers=_headers(api_key),
                json={"model": model, "prompt": prompt},
            )
            if resp.status_code == 200:
                return True, resp.json()
            return False, {"error": f"文生视频失败: {resp.text[:200]}"}
    except Exception as e:  # noqa: BLE001
        return False, {"error": f"文生视频请求异常: {str(e)[:200]}"}
