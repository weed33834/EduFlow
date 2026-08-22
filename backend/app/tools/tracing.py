"""本地 JSONL 追踪器 — 零依赖、零账号的可观测性基线

每次 Agent 请求生成 trace_id；每个 LLM 调用追加一条 span 到 logs/traces.jsonl：
    {"ts","trace_id","session_id","event","model","dur_ms","out_chars","stream","ok"}

用 scripts/view_traces.py 按会话/轮次聚合查看。
外部面板（Langfuse/LangSmith/Phoenix）为可选增强，见 README「可观测性」。
"""
import json
import logging
import threading
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# 请求级上下文：chat 路由设置，llm 层读取（跨 await/task 自动传播）
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
session_id_var: ContextVar[int] = ContextVar("session_id", default=0)

_lock = threading.Lock()


def new_trace_id() -> str:
    import uuid
    return uuid.uuid4().hex[:16]


def _trace_file() -> Path:
    directory = Path(settings.TRACE_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "traces.jsonl"


def record_span(
    event: str,
    *,
    model: str | None = None,
    dur_ms: float | None = None,
    out_chars: int | None = None,
    stream: bool | None = None,
    ok: bool = True,
    error: str | None = None,
) -> None:
    """追加一条 span；追踪失败绝不影响主流程"""
    if not settings.TRACE_ENABLED:
        return
    span = {
        "ts": datetime.now().isoformat(timespec="milliseconds"),
        "trace_id": trace_id_var.get() or "detached",
        "session_id": session_id_var.get() or None,
        "event": event,
    }
    if model is not None:
        span["model"] = model
    if dur_ms is not None:
        span["dur_ms"] = round(dur_ms, 1)
    if out_chars is not None:
        span["out_chars"] = out_chars
    if stream is not None:
        span["stream"] = stream
    if not ok:
        span["ok"] = False
    if error:
        span["error"] = error[:300]

    try:
        line = json.dumps(span, ensure_ascii=False)
        with _lock:
            with open(_trace_file(), "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        logger.debug("追踪写入失败（忽略）", exc_info=True)
