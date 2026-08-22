"""EduAgent 统一 CLI

用法（backend/ 目录下）:
    python scripts/cli.py ingest --dir ../docs        # 知识库摄入
    python scripts/cli.py traces --session 42         # 查看 LLM 追踪
    python scripts/cli.py stats                       # 数据统计
    python scripts/cli.py create-user --email a@b.c --username alice --password ****
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402


# ── 子命令实现 ────────────────────────────────────────────


async def cmd_ingest(args) -> int:
    from scripts.ingest_knowledge import ingest_directory
    return await ingest_directory(args.dir, args.pattern, args.max_chars)


def _print_traces(args) -> None:
    from scripts.view_traces import print_recent
    count = print_recent(args.session, args.n, args.dir)
    if count == 0:
        print("（没有匹配的追踪记录）")


async def cmd_stats(args) -> dict:
    from sqlalchemy import select, func as sa_func
    from app.database import async_session, init_db
    from app.models import User, Session, Message, ReviewItem
    from datetime import datetime

    await init_db()
    async with async_session() as db:
        async def count(model):
            r = await db.execute(select(sa_func.count()).select_from(model))
            return r.scalar() or 0

        stats = {
            "users": await count(User),
            "sessions": await count(Session),
            "messages": await count(Message),
            "review_items": await count(ReviewItem),
        }
        due = await db.execute(
            select(sa_func.count()).select_from(ReviewItem)
            .where(ReviewItem.due <= datetime.now())
        )
        stats["review_due_now"] = due.scalar() or 0

    if getattr(args, "csv", False):
        lines = ["metric,value"] + [f"{k},{v}" for k, v in stats.items()]
        print("\n".join(lines))
    else:
        print("EduAgent 数据统计")
        for k, v in stats.items():
            print(f"  {k:>16}: {v}")
    return stats


async def cmd_create_user(args) -> int:
    from sqlalchemy import select
    from app.database import async_session, init_db
    from app.models import User, StudentProfile
    from app.security import hash_password

    await init_db()
    email = args.email.lower()
    async with async_session() as db:
        for field, value in (("email", email), ("username", args.username)):
            exists = await db.execute(
                select(User).where(getattr(User, field) == value).limit(1)
            )
            if exists.scalar_one_or_none():
                print(f"错误：{field} 已存在 → {value}")
                return 1

        user = User(
            email=email,
            username=args.username,
            display_name=args.display_name or args.username,
            password_hash=hash_password(args.password),
        )
        db.add(user)
        await db.flush()
        db.add(StudentProfile(user_id=user.id))
        await db.commit()
        print(f"用户已创建: {args.username} (id={user.id})")
        return 0


# ── 入口 ─────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eduagent",
        description="EduAgent 管理 CLI（摄入 / 追踪 / 统计 / 用户）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="把文档目录灌入知识库")
    p_ingest.add_argument("--dir", required=True)
    p_ingest.add_argument("--pattern", default="**/*.md")
    p_ingest.add_argument("--max-chars", type=int, default=800)

    p_traces = sub.add_parser("traces", help="查看本地 LLM 追踪")
    p_traces.add_argument("--session", type=int, default=None)
    p_traces.add_argument("-n", type=int, default=20)
    p_traces.add_argument("--dir", default=settings.TRACE_DIR)

    p_stats = sub.add_parser("stats", help="数据库统计")
    p_stats.add_argument("--csv", action="store_true", help="以 CSV 格式输出")

    p_user = sub.add_parser("create-user", help="创建用户（含默认画像）")
    p_user.add_argument("--email", required=True)
    p_user.add_argument("--username", required=True)
    p_user.add_argument("--password", required=True)
    p_user.add_argument("--display-name", default=None)

    args = parser.parse_args()

    handlers = {
        "ingest": lambda: sys.exit(asyncio.run(cmd_ingest(args))),
        "traces": lambda: _print_traces(args),
        "stats": lambda: asyncio.run(cmd_stats(args)),
        "create-user": lambda: sys.exit(asyncio.run(cmd_create_user(args))),
    }
    handlers[args.command]()


if __name__ == "__main__":
    main()
