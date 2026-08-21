"""长期记忆 — Mem0 集成（开源）

pip install mem0ai — 一行装好
GitHub: https://github.com/mem0ai/mem0
自动提取/存储/检索用户记忆，不需要自己写记忆管理
"""
import os
from typing import Optional

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

_memory: Optional["Memory"] = None


def get_memory() -> Optional["Memory"]:
    """获取 Mem0 实例（延迟初始化）"""
    global _memory
    if not MEM0_AVAILABLE:
        return None
    if _memory is None:
        api_key = os.getenv("MEM0_API_KEY")
        try:
            if api_key:
                # 云端模式
                _memory = Memory.from_config({"api_key": api_key})
            else:
                # 本地模式（需要 Qdrant）
                _memory = Memory()
        except Exception:
            _memory = None
    return _memory


async def add_memory(user_id: str, content: str, metadata: dict = None):
    """添加记忆 — Mem0 自动提取关键信息"""
    m = get_memory()
    if m:
        try:
            m.add(content, user_id=user_id, metadata=metadata or {})
        except Exception:
            pass


async def search_memory(user_id: str, query: str, top_k: int = 3) -> list[dict]:
    """搜索记忆 — Mem0 自动语义检索"""
    m = get_memory()
    if not m:
        return []
    try:
        results = m.search(query, user_id=user_id, limit=top_k)
        return [
            {"text": r.get("memory", ""), "score": r.get("score", 0)}
            for r in results
        ]
    except Exception:
        return []


async def get_user_memories(user_id: str) -> list[dict]:
    """获取用户的所有记忆"""
    m = get_memory()
    if not m:
        return []
    try:
        results = m.get_all(user_id=user_id)
        return [{"text": r.get("memory", "")} for r in results]
    except Exception:
        return []


async def is_available() -> bool:
    """检查 Mem0 是否可用"""
    return get_memory() is not None
