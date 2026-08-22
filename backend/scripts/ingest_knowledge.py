"""知识库摄入脚本 — 把本地文档目录灌入 Qdrant RAG

用法（backend/ 目录下）:
    python scripts/ingest_knowledge.py --dir ../docs --pattern "**/*.md"

流程: 读取文件 → chunk_text 分块 → 每块 embedding 一次 → add_document_with_vector 写入。
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools.knowledge import (  # noqa: E402
    add_document_with_vector,
    chunk_text,
    get_embedding,
    is_available,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("ingest")


async def ingest_directory(directory: str, pattern: str = "**/*.md",
                           max_chars: int = 800) -> int:
    """摄入目录下的匹配文件。返回进程退出码（0 成功 / 1 不可用 / 2 部分失败）。"""
    if not await is_available():
        logger.error(
            "知识库不可用：需要 Qdrant（QDRANT_URL）与 embedding 能力（LITELLM_API_KEY）。"
        )
        return 1

    root = Path(directory)
    if not root.is_dir():
        logger.error("目录不存在: %s", directory)
        return 1

    files = sorted(p for p in root.rglob(pattern) if p.is_file())
    if not files:
        logger.error("没有匹配 %s 的文件（目录: %s）", pattern, directory)
        return 1

    docs_ok = chunks_ok = chunks_failed = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.warning("读取失败，跳过: %s", path, exc_info=True)
            continue

        source = str(path.relative_to(root))
        file_chunks = 0
        for chunk in chunk_text(text, max_chars=max_chars):
            vector = await get_embedding(chunk)
            if not vector:
                logger.warning("embedding 失败，跳过该块: %s", source)
                chunks_failed += 1
                continue
            await add_document_with_vector(
                chunk, vector, metadata={"source": source}
            )
            file_chunks += 1
        if file_chunks:
            docs_ok += 1
            chunks_ok += file_chunks
        logger.info("%s -> %d 块", source, file_chunks)

    logger.info(
        "摄入完成：文件 %d 个，块 %d 个，失败 %d 个", docs_ok, chunks_ok, chunks_failed
    )
    return 2 if chunks_failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="把文档目录灌入 EduAgent 知识库")
    parser.add_argument("--dir", required=True, help="文档根目录")
    parser.add_argument("--pattern", default="**/*.md", help="glob 模式，默认 **/*.md")
    parser.add_argument("--max-chars", type=int, default=800, help="分块上限字符数")
    args = parser.parse_args()
    sys.exit(asyncio.run(ingest_directory(args.dir, args.pattern, args.max_chars)))


if __name__ == "__main__":
    main()
