"""数据库引擎与会话"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI 依赖：获取数据库会话"""
    async with async_session() as session:
        yield session


async def init_db():
    """初始化数据库表（开发环境用 create_all；并为既有表补齐新增列的轻量迁移）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _add_missing_columns(conn)


# create_all 只建缺失的表、不会给已有表加列——这里手工补（单机/开发场景；
# 多实例生产建议 Alembic）
_PENDING_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "sessions": [
        ("pinned", "BOOLEAN DEFAULT 0"),
        ("archived", "BOOLEAN DEFAULT 0"),
    ],
}


async def _add_missing_columns(conn) -> None:
    from sqlalchemy import inspect as sa_inspect, text

    def _migrate(sync_conn):
        insp = sa_inspect(sync_conn)
        for table, columns in _PENDING_COLUMNS.items():
            if table not in insp.get_table_names():
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in columns:
                if name not in existing:
                    sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

    await conn.run_sync(_migrate)
