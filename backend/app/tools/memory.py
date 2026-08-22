"""长期记忆 — Mem0 集成（开源）

pip install mem0ai — 一行装好
GitHub: https://github.com/mem0ai/mem0
自动提取/存储/检索用户记忆，不需要自己写记忆管理。

适配 mem0ai==2.0.18：
- 使用 AsyncMemory（避免同步网络调用阻塞事件循环）
- search/get_all 的实体过滤统一走 filters={"user_id": ...}
"""
import logging
import os
from typing import Optional

try:
    from mem0 import AsyncMemory
    MEM0_AVAILABLE = True
except ImportError:
    AsyncMemory = None
    MEM0_AVAILABLE = False

logger = logging.getLogger(__name__)

_memory: Optional["AsyncMemory"] = None


def get_memory() -> Optional["AsyncMemory"]:
    """获取 Mem0 异步实例（延迟初始化）"""
    global _memory
    if not MEM0_AVAILABLE:
        return None
    if _memory is None:
        api_key = os.getenv("MEM0_API_KEY")
        try:
            if api_key:
                # 云端模式
                _memory = AsyncMemory.from_config({"api_key": api_key})
            else:
                # 本地模式（需要向量库与 embedding 配置）
                _memory = AsyncMemory()
        except Exception:
            logger.warning("Mem0 初始化失败，长期记忆不可用", exc_info=True)
            _memory = None
    return _memory


async def add_memory(user_id: str, content: str, metadata: dict = None):
    """添加记忆 — Mem0 自动提取关键信息"""
    m = get_memory()
    if not m:
        return
    try:
        await m.add(content, user_id=user_id, metadata=metadata or {})
    except Exception:
        logger.warning("Mem0 写入失败 user=%s", user_id, exc_info=True)


async def search_memory(user_id: str, query: str, top_k: int = 3) -> list[dict]:
    """搜索记忆 — Mem0 语义检索，按 user_id 过滤"""
    m = get_memory()
    if not m:
        return []
    try:
        results = await m.search(
            query, top_k=top_k, filters={"user_id": user_id}
        )
        if isinstance(results, dict):
            results = results.get("results", [])
        return [
            {"text": r.get("memory", ""), "score": r.get("score", 0)}
            for r in results
            if isinstance(r, dict)
        ]
    except Exception:
        logger.warning("Mem0 检索失败 user=%s", user_id, exc_info=True)
        return []


async def get_user_memories(user_id: str) -> list[dict]:
    """获取用户的所有记忆"""
    m = get_memory()
    if not m:
        return []
    try:
        results = await m.get_all(filters={"user_id": user_id})
        if isinstance(results, dict):
            results = results.get("results", [])
        return [
            {"text": r.get("memory", "")}
            for r in results
            if isinstance(r, dict)
        ]
    except Exception:
        logger.warning("Mem0 全量读取失败 user=%s", user_id, exc_info=True)
        return []


async def is_available() -> bool:
    """检查 Mem0 是否可用"""
    return get_memory() is not None
