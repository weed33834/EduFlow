"""
AI 讲解视频 Agent（Presenter）

输入课程主题 → 输出「讲解视频」：
1. 用 chat LLM 生成结构化幻灯片 + 逐页讲解稿
2. 用 PIL 把每页幻灯片渲染为精美 PNG
3. 用 TTS 为每页生成配音（可用时）
4. 用 ffmpeg 把「幻灯片 + 配音」合成讲解视频

能力降级：
- 无 TTS → 仍合成无声幻灯片视频，并提供完整讲解稿，提示接入 TTS 模型可配音
- 无 chat LLM → 返回错误
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import tempfile
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from core.config import settings
from core.llm import chat_completion, is_llm_available
from core.capabilities import detect_capabilities, build_availability_hint, Capability
from core import media


PRESENTER_SYSTEM_PROMPT = """你是资深课程制作人。请为给定的学习主题制作一份结构化的讲解演示稿。
输出必须是合法 JSON，结构如下：
{
  "title": "演示标题",
  "subtitle": "副标题",
  "slides": [
    {
      "title": "页面标题",
      "bullets": ["要点1", "要点2", "要点3"],
      "narration": "本页讲解口播文案（自然、口语化，60-100字）"
    }
  ]
}
要求：5-7 页，先总览、再逐层深入、最后总结。讲解文案要通顺易懂。用中文。"""


# ---------------------------------------------------------------------------
# 1. 生成讲稿 + 幻灯片结构
# ---------------------------------------------------------------------------

async def generate_presentation(topic: str, level: str = "beginner") -> dict:
    if not is_llm_available():
        return {"ok": False, "error": "未配置 LLM 模型，无法生成讲解内容。"}
    prompt = (
        f"主题：{topic}\n受众水平：{level}\n\n"
        "请生成一份 5-7 页的讲解演示稿（JSON）。"
    )
    result = await chat_completion(
        [{"role": "user", "content": prompt}], PRESENTER_SYSTEM_PROMPT, agent_type="planner"
    )
    data = _parse_json(result)
    if not isinstance(data, dict) or not data.get("slides"):
        # LLM 失败 -> 使用内置模板兜底，保证功能可用
        fb = _fallback_presentation(topic, level)
        fb["warnings"] = ["AI 生成讲解稿失败，已使用内置模板。" ]
        return fb
    return {"ok": True, "title": data.get("title", topic), "subtitle": data.get("subtitle", ""),
            "slides": data.get("slides", [])}


def _fallback_presentation(topic: str, level: str = "beginner") -> dict:
    """LLM 不可用时的内置模板讲解稿，保证讲解视频管线始终可用。"""
    slides = [
        {"title": f"{topic} · 课程总览", "bullets": [f"认识 {topic} 的核心概念", "明确学习目标与路径", "建立整体知识框架"],
         "narration": f"大家好，今天我们一起学习{topic}。首先我们来了解它的整体框架和核心概念。"},
        {"title": "基础概念", "bullets": [f"{topic} 的基本定义与原理", "核心术语与关键思想", "为什么要学习它"],
         "narration": f"接下来我们进入基础部分，掌握{topic}的基本定义和核心思想。"},
        {"title": "核心知识点", "bullets": ["由浅入深拆解重点", "结合实例理解原理", "常见的应用场景"],
         "narration": f"这一部分我们深入讲解{topic}的核心知识点，并用实例帮助理解。"},
        {"title": "实战应用", "bullets": ["动手实践关键步骤", "解决典型问题", "巩固所学知识"],
         "narration": f"理论之后是实践。我们通过动手练习来巩固{topic}的知识。"},
        {"title": "总结回顾", "bullets": ["回顾重点与难点", "梳理知识脉络", "下一步学习建议"],
         "narration": f"最后我们做一次总结，回顾{topic}的要点，并给出进一步学习的建议。"},
    ]
    return {"ok": True, "title": f"{topic} · AI 讲解", "subtitle": f"适合{level}水平学习者",
            "slides": slides}


def _parse_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# 2. 渲染幻灯片为 PNG（PIL）
# ---------------------------------------------------------------------------

_SLIDE_W, _SLIDE_H = 1280, 720
_BG = (24, 30, 54)          # 深蓝背景
_ACCENT = (99, 102, 241)    # indigo
_TITLE = (255, 255, 255)
_BODY = (226, 232, 240)


def _load_font(size: int):
    for name in ("NotoSansCJK-Regular.ttc", "wqy-microhei.ttc", "PingFang.ttc", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _render_slide(title: str, bullets: list[str], page: str, index: int, total: int) -> Image.Image:
    img = Image.new("RGB", (_SLIDE_W, _SLIDE_H), _BG)
    d = ImageDraw.Draw(img)
    # 顶部渐变条
    for i in range(8):
        d.rectangle([0, i * 8, _SLIDE_W, i * 8 + 8], fill=(i * 12 + 24, i * 12 + 30, i * 14 + 54))
    # 左侧强调条
    d.rectangle([0, 0, 12, _SLIDE_H], fill=_ACCENT)
    # 页码角标
    d.text((_SLIDE_W - 150, _SLIDE_H - 60), f"{index + 1} / {total}", font=_load_font(28), fill=(148, 163, 184))
    # 标题
    tfont = _load_font(52)
    d.text((80, 90), title, font=tfont, fill=_TITLE)
    d.rectangle([80, 150, 260, 156], fill=_ACCENT)
    # 要点
    bfont = _load_font(36)
    y = 210
    for b in bullets:
        wrapped = _wrap_text(b, 30)
        for line in wrapped:
            d.text((80, y), f"• {line}", font=bfont, fill=_BODY)
            y += 52
        y += 16
        if y > _SLIDE_H - 60:
            break
    return img


def _wrap_text(text: str, max_chars: int) -> list[str]:
    lines = []
    cur = ""
    for ch in text:
        if len(cur) >= max_chars:
            lines.append(cur)
            cur = ""
        cur += ch
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# 3. ffmpeg 工具
# ---------------------------------------------------------------------------

def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"


def _audio_duration(audio_path: str) -> float:
    try:
        r = subprocess.run(
            [_ffmpeg(), "-i", audio_path, "-f", "null", "-"],
            capture_output=True, text=True, timeout=60,
        )
        m = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", r.stderr)
        if m:
            h, mi, s = m.groups()
            return int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        pass
    return 6.0


# ---------------------------------------------------------------------------
# 4. 合成讲解视频
# ---------------------------------------------------------------------------

async def compose_presentation_video(topic: str, level: str = "beginner") -> dict:
    """完整管线：生成讲稿 → 渲染幻灯片 → 配音 → 合成视频。

    Returns:
        {
          "ok": bool, "title", "slides":[...],
          "video": "base64 视频" 或 "text_only": true,
          "narration_text": 全文讲解稿,
          "hint": 能力降级提示(可选), "warnings": [...]
        }
    """
    gen = await generate_presentation(topic, level)
    if not gen.get("ok"):
        return gen
    title = gen["title"]
    slides = gen["slides"]
    warnings: list[str] = list(gen.get("warnings") or [])

    # 探测能力（决定是否配音）
    caps = await detect_capabilities(settings.OPENAI_BASE_URL or "", settings.OPENAI_API_KEY or "")
    tts_models = caps["models"].get("tts", [])
    tts_ok = bool(tts_models) and bool(settings.OPENAI_BASE_URL)
    if tts_ok and settings.TTS_MODEL:
        tts_model = settings.TTS_MODEL
    elif tts_models:
        tts_model = tts_models[0]
    else:
        tts_model = None

    tmp = tempfile.mkdtemp(prefix="eduflow_pres_")
    segment_paths: list[str] = []
    narration_lines: list[str] = []

    try:
        # 逐页：渲染幻灯片 + 生成配音
        for i, slide in enumerate(slides):
            img = _render_slide(slide.get("title", f"第{i+1}页"), slide.get("bullets", []),
                                slide.get("narration", ""), i, len(slides))
            img_path = os.path.join(tmp, f"slide_{i:03d}.png")
            img.save(img_path)
            narration = slide.get("narration", "")
            narration_lines.append(f"【{slide.get('title','')}】{narration}")

            audio_path = None
            if tts_ok and tts_model and narration:
                ok, aud = await media.tts(
                    settings.OPENAI_BASE_URL, settings.OPENAI_API_KEY,
                    tts_model, narration, voice=settings.TTS_VOICE,
                )
                if ok and isinstance(aud, bytes) and aud:
                    audio_path = os.path.join(tmp, f"audio_{i:03d}.mp3")
                    with open(audio_path, "wb") as f:
                        f.write(aud)
                else:
                    warnings.append(f"第{i+1}页配音失败：{aud if isinstance(aud,str) else '未知'}")

            seg = os.path.join(tmp, f"seg_{i:03d}.mp4")
            _make_segment(img_path, audio_path, seg)
            if os.path.exists(seg):
                segment_paths.append(seg)

        if not segment_paths:
            return {"ok": False, "error": "幻灯片合成失败"}

        # 合成最终视频
        out_path = os.path.join(tmp, "final.mp4")
        ok_concat = _concat_segments(segment_paths, out_path)
        narration_text = "\n\n".join(narration_lines)

        if not ok_concat or not os.path.exists(out_path):
            # 无法合成视频 -> 降级为纯图片 + 讲稿
            return {
                "ok": True, "title": title, "slides": slides,
                "text_only": True, "narration_text": narration_text,
                "warnings": warnings + ["视频合成失败，已返回图片版与讲解稿。"],
            }

        with open(out_path, "rb") as f:
            video_b64 = __import__("base64").b64encode(f.read()).decode()

        result = {
            "ok": True, "title": title, "slides": slides,
            "video": video_b64, "narration_text": narration_text,
            "warnings": warnings,
        }
        if not tts_ok:
            result["hint"] = build_availability_hint("presentation_video", ["tts"])
            result["warnings"] = warnings + ["当前端点无 TTS 能力，视频为无声幻灯片版；接入语音合成模型后可自动配音。"]
        return result
    finally:
        pass  # tmp 清理交给系统


def _make_segment(img_path: str, audio_path: Optional[str], out: str) -> None:
    """单页：图片+音频 → mp4 片段。无音频则固定时长。"""
    try:
        if audio_path and os.path.exists(audio_path):
            dur = max(_audio_duration(audio_path), 2.0)
            subprocess.run(
                [_ffmpeg(), "-y", "-loop", "1", "-i", img_path, "-i", audio_path,
                 "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", "-c:a", "aac",
                 "-shortest", out],
                capture_output=True, timeout=120,
            )
        else:
            subprocess.run(
                [_ffmpeg(), "-y", "-loop", "1", "-i", img_path,
                 "-c:v", "libx264", "-t", "6", "-pix_fmt", "yuv420p", out],
                capture_output=True, timeout=120,
            )
    except Exception:
        pass


def _concat_segments(segments: list[str], out: str) -> bool:
    try:
        tmp = os.path.join(os.path.dirname(out), "list.txt")
        with open(tmp, "w") as f:
            for s in segments:
                f.write(f"file '{s}'\n")
        r = subprocess.run(
            [_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", tmp, "-c", "copy", out],
            capture_output=True, timeout=180,
        )
        return r.returncode == 0 and os.path.exists(out)
    except Exception:
        return False
