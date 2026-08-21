"""知识库 RAG — Qdrant 向量数据库 + LiteLLM Embedding

不安装 llama-index（太重），直接用 qdrant-client + litellm.aembedding
pip install qdrant-client — 轻量
GitHub: https://github.com/qdrant/qdrant
"""
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
        results = client.search(
            collection_name=COLLECTION,
            query_vector=query_vec,
            limit=top_k,
        )
        return [
            {"text": r.payload.get("text", ""), "score": r.score, "metadata": r.payload}
            for r in results
        ]
    except Exception:
        return []


async def add_document(text: str, metadata: dict = None):
    """添加文档到知识库"""
    client = get_client()
    if not client or not settings.llm_available:
        return

    vec = await get_embedding(text)
    if not vec:
        return

    try:
        import uuid
        client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={"text": text, **(metadata or {})},
            )],
        )
    except Exception:
        pass


async def is_available() -> bool:
    """检查知识库是否可用"""
    return get_client() is not None and settings.llm_available
