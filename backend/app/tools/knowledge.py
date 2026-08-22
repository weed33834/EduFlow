"""知识库 RAG — Qdrant 向量数据库 + LiteLLM Embedding

不安装 llama-index（太重），直接用 qdrant-client + litellm.aembedding
pip install qdrant-client — 轻量
GitHub: https://github.com/qdrant/qdrant
"""
import logging
import os
from typing import Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

import litellm

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION = "eduagent"
_client: Optional["QdrantClient"] = None


def get_client() -> Optional["QdrantClient"]:
    """获取 Qdrant 客户端（延迟初始化）"""
    global _client
    if not QDRANT_AVAILABLE:
        return None
    if _client is None:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        try:
            _client = QdrantClient(url=url)
            # 确保集合存在
            if not _client.collection_exists(COLLECTION):
                _client.create_collection(
                    collection_name=COLLECTION,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
        except Exception:
            logger.warning("Qdrant 连接/建集合失败 url=%s", url, exc_info=True)
            _client = None
    return _client


async def get_embedding(text: str) -> list[float]:
    """用 LiteLLM 获取文本嵌入（支持 OpenAI/Cohere 等）"""
    if not settings.llm_available:
        return []
    try:
        resp = await litellm.aembedding(
            model="text-embedding-3-small",
            input=text[:2000],
            api_key=settings.LITELLM_API_KEY,
            api_base=settings.LITELLM_BASE_URL,
        )
        return resp.data[0]["embedding"]
    except Exception:
        return []


async def search_knowledge(query: str, top_k: int = 3) -> list[dict]:
    """搜索知识库，返回相关文档"""
    client = get_client()
    if not client or not settings.llm_available:
        return []

    query_vec = await get_embedding(query)
    if not query_vec:
        return []

    try:
        response = client.query_points(
            collection_name=COLLECTION,
            query=query_vec,
            limit=top_k,
        )
        return [
            {"text": p.payload.get("text", ""), "score": p.score, "metadata": p.payload}
            for p in response.points
        ]
    except Exception:
        logger.warning("知识库检索失败", exc_info=True)
        return []


async def add_document(text: str, metadata: dict = None):
    """添加文档到知识库（内部完成 embedding）"""
    vec = await get_embedding(text)
    if not vec:
        return
    await add_document_with_vector(text, vec, metadata)


async def add_document_with_vector(text: str, vector: list[float], metadata: dict = None):
    """用现成向量写入知识库（摄入管线避免重复 embedding）"""
    import uuid

    client = get_client()
    if not client:
        return
    try:
        client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": text, **(metadata or {})},
            )],
        )
    except Exception:
        logger.warning("知识库写入失败", exc_info=True)


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """按段落聚合分块：段落尽量完整，超长段落硬切。

    返回空输入 → []；每块长度 ≤ max_chars（硬切保证）。
    """
    if not text or not text.strip():
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # 超长段落先硬切成 max_chars 以内的片
        pieces = [paragraph[i:i + max_chars] for i in range(0, len(paragraph), max_chars)]
        for piece in pieces:
            piece_len = len(piece)
            if current and current_len + piece_len + 2 > max_chars:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            current.append(piece)
            current_len += piece_len + (2 if len(current) > 1 else 0)

    if current:
        chunks.append("\n\n".join(current))
    return chunks


async def is_available() -> bool:
    """检查知识库是否可用"""
    return get_client() is not None and settings.llm_available
