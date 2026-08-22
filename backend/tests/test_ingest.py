"""知识库摄入路径测试：分块器 + 向量直写 + 摄入脚本端到端（全 mock）"""
import asyncio
import importlib.util
from pathlib import Path

import pytest

import app.tools.knowledge as k
from app.tools.knowledge import add_document_with_vector, chunk_text

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ingest_knowledge.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("ingest_knowledge", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── chunk_text ────────────────────────────────────────────


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_text_short_single_chunk():
    out = chunk_text("递归是函数调用自身。")
    assert out == ["递归是函数调用自身。"]


def test_chunk_text_merges_paragraphs_within_limit():
    paras = [f"段落{i}。" + "x" * 30 for i in range(5)]
    text = "\n\n".join(paras)
    out = chunk_text(text, max_chars=100)
    assert len(out) >= 2
    for c in out:
        assert len(c) <= 100, f"块超限: {len(c)}"
    # 内容不丢
    assert "".join(out).replace("\n\n", "") == "".join(paras)


def test_chunk_text_hard_splits_oversized_paragraph():
    big = "y" * 250
    out = chunk_text(big, max_chars=100)
    assert all(len(c) <= 100 for c in out)
    assert "".join(out) == big


# ── add_document_with_vector ──────────────────────────────


def test_add_document_with_vector_upserts_payload():
    captured = {}

    class FakeClient:
        def upsert(self, collection_name, points):
            captured["collection"] = collection_name
            captured["points"] = points

    old = k._client
    k._client = FakeClient()
    try:
        asyncio.run(add_document_with_vector(
            "内容", [0.1] * 4, metadata={"source": "a.md"}
        ))
    finally:
        k._client = old

    assert captured["collection"] == k.COLLECTION
    point = captured["points"][0]
    assert point.payload["text"] == "内容"
    assert point.payload["source"] == "a.md"
    assert point.vector == [0.1] * 4


# ── 摄入脚本端到端 ─────────────────────────────────────────


def test_ingest_directory_end_to_end(tmp_path, monkeypatch):
    mod = _load_script()
    (tmp_path / "a.md").write_text("# 递归\n\n递归是自调用。" + "x" * 50, encoding="utf-8")
    (tmp_path / "b.md").write_text("闭包捕获自由变量。", encoding="utf-8")

    upserts = []

    class FakeClient:
        def upsert(self, collection_name, points):
            upserts.extend(points)

    async def fake_embed(text):
        return [0.2] * 8

    monkeypatch.setattr(k, "_client", FakeClient())
    monkeypatch.setattr(k.settings, "LITELLM_API_KEY", "sk-test")
    monkeypatch.setattr(mod, "get_embedding", fake_embed)
    monkeypatch.setattr(mod, "is_available", lambda: asyncio.sleep(0, result=True))
    monkeypatch.setattr(mod, "add_document_with_vector",
                        _make_recorder(upserts))

    code = asyncio.run(mod.ingest_directory(str(tmp_path)))
    assert code == 0
    assert len(upserts) == 2
    sources = sorted(p.payload["source"] for p in upserts)
    assert sources == ["a.md", "b.md"]
    texts = {p.payload["text"] for p in upserts}
    assert any("递归是自调用" in t for t in texts)


def _make_recorder(upserts):
    async def record(text, vector, metadata=None):
        from qdrant_client.models import PointStruct
        import uuid as _uuid
        upserts.append(PointStruct(
            id=str(_uuid.uuid4()), vector=vector,
            payload={"text": text, **(metadata or {})},
        ))
    return record


def test_ingest_unavailable_returns_1(tmp_path, monkeypatch):
    mod = _load_script()
    async def not_available():
        return False

    monkeypatch.setattr(mod, "is_available", not_available)
    assert asyncio.run(mod.ingest_directory(str(tmp_path))) == 1


@pytest.mark.parametrize("missing", [True])
def test_ingest_missing_dir_returns_1(monkeypatch, missing):
    mod = _load_script()
    monkeypatch.setattr(
        mod, "is_available", lambda: asyncio.sleep(0, result=True)
    )
    assert asyncio.run(mod.ingest_directory("Z:/definitely/not/here")) == 1
