"""查看本地追踪文件：按 trace 聚合打印 LLM 调用链

用法（backend/ 目录下）:
    python scripts/view_traces.py                 # 最近 20 条 trace
    python scripts/view_traces.py --session 42    # 只看某会话
    python scripts/view_traces.py -n 5            # 最近 5 条
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402


def load_spans(trace_dir: str, session_id: int | None):
    path = Path(trace_dir) / "traces.jsonl"
    if not path.exists():
        print(f"暂无追踪数据: {path}")
        return []
    spans = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                span = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id is not None and span.get("session_id") != session_id:
                continue
            spans.append(span)
    return spans


def print_recent(session_id: int | None = None, n: int = 20,
                 trace_dir: str | None = None) -> int:
    """按 trace 聚合打印最近 n 条调用链，返回打印的 trace 数"""
    spans = load_spans(trace_dir or settings.TRACE_DIR, session_id)
    by_trace: dict[str, list[dict]] = defaultdict(list)
    for s in spans:
        by_trace[s.get("trace_id", "detached")].append(s)

    traces = list(by_trace.items())[-n:]
    for trace_id, items in reversed(traces):  # 最新在前
        session = items[0].get("session_id") or "-"
        total_ms = sum(i.get("dur_ms") or 0 for i in items)
        calls = len(items)
        failed = sum(1 for i in items if i.get("ok") is False)
        print(f"\ntrace {trace_id} · 会话 {session} · {calls} 次 LLM 调用"
              f" · 合计 {total_ms:.0f}ms" + (f" · {failed} 失败" if failed else ""))
        for i in items:
            flag = "✗" if i.get("ok") is False else "·"
            stream = "流式" if i.get("stream") else "整段"
            line = (f"   {flag} [{i['ts'][11:23]}] {i['event']} "
                    f"{i.get('model', '-')} {stream} "
                    f"{i.get('dur_ms', 0):.0f}ms out={i.get('out_chars', '-')}字")
            if i.get("error"):
                line += f"\n     错误: {i['error']}"
            print(line)
    return len(traces)


def main() -> None:
    parser = argparse.ArgumentParser(description="查看 EduAgent 本地 LLM 追踪")
    parser.add_argument("--session", type=int, default=None)
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--dir", default=settings.TRACE_DIR)
    args = parser.parse_args()
    print_recent(args.session, args.n, args.dir)

if __name__ == "__main__":
    main()

