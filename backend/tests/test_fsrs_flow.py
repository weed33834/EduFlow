"""FSRS 调度 + 待作答上下文还原的集成测试（真实 sqlite）"""
import asyncio

import pytest
from sqlalchemy import select

from app.database import init_db, async_session
from app.models import ReviewItem, Message
from app.routers.chat import (
    apply_fsrs_reschedule,
    create_review_card_once,
    load_pending_context,
)


@pytest.fixture(scope="module", autouse=True)
def _init_db():
    asyncio.run(init_db())


def test_create_review_card_once_dedupes():
    async def scenario():
        async with async_session() as db:
            await create_review_card_once(db, 9001, "什么是递归")
            await create_review_card_once(db, 9001, "什么是递归")
            await db.commit()

            result = await db.execute(
                select(ReviewItem).where(
                    ReviewItem.user_id == 9001,
                    ReviewItem.concept == "什么是递归",
                )
            )
            items = result.scalars().all()
            assert len(items) == 1
            assert items[0].card_data, "card_data 必须已序列化"
            return items[0].id

    item_id = asyncio.run(scenario())
    assert item_id is not None


def test_apply_fsrs_reschedules_due():
    async def scenario():
        async with async_session() as db:
            await create_review_card_once(db, 9002, "列表推导式")
            await db.commit()

            result = await db.execute(
                select(ReviewItem).where(
                    ReviewItem.user_id == 9002,
                    ReviewItem.concept == "列表推导式",
                )
            )
            item = result.scalar_one()
            old_due = item.due
            old_card = dict(item.card_data)

            await apply_fsrs_reschedule(
                db, 9002,
                {"item_id": item.id, "rating": 3, "correct": True, "mode": "review"},
            )
            await db.commit()
            await db.refresh(item)

            assert item.due > old_due, f"答对后到期时间应推迟: {old_due} -> {item.due}"
            assert dict(item.card_data) != old_card

    asyncio.run(scenario())


def test_fsrs_wrong_answer_updates_state():
    """答错（rating=1）后卡片状态必须被更新（进入再学习/学习步骤）"""

    async def scenario():
        async with async_session() as db:
            await create_review_card_once(db, 9003, "闭包")
            result = await db.execute(
                select(ReviewItem).where(
                    ReviewItem.user_id == 9003, ReviewItem.concept == "闭包"
                )
            )
            item = result.scalar_one()
            old_card = dict(item.card_data)

            await apply_fsrs_reschedule(
                db, 9003, {"item_id": item.id, "rating": 1, "mode": "review"}
            )
            await db.commit()
            await db.refresh(item)
            return dict(item.card_data), old_card

    card, old_card = asyncio.run(scenario())
    assert card != old_card, "答错后卡片数据应更新"
    assert "stability" in card and "state" in card


def test_load_pending_context_roundtrip():
    async def scenario():
        async with async_session() as db:
            from app.models import Session

            session = Session(user_id=9004)
            db.add(session)
            await db.flush()

            quiz_msg = Message(
                session_id=session.id,
                role="assistant",
                content="题目",
                metadata_={"quiz": {"question": "Q", "answer": 1}, "answered": False},
            )
            db.add(quiz_msg)
            await db.flush()

            pending_quiz, pending_review = await load_pending_context(db, session.id)
            assert pending_quiz["answer"] == 1
            assert pending_quiz["_message_id"] == quiz_msg.id
            assert pending_review == {}

            # 标记为已答后不再加载
            answered_md = dict(quiz_msg.metadata_)
            answered_md["answered"] = True
            quiz_msg.metadata_ = answered_md

            review_msg = Message(
                session_id=session.id,
                role="assistant",
                content="复习一下递归",
                metadata_={
                    "review_item_id": 42,
                    "review_concept": "递归",
                    "review_answered": False,
                },
            )
            db.add(review_msg)
            await db.flush()

            pending_quiz, pending_review = await load_pending_context(db, session.id)
            assert pending_quiz == {}
            assert pending_review["item_id"] == 42
            assert pending_review["concept"] == "递归"

            await db.delete(review_msg)
            await db.delete(quiz_msg)
            await db.delete(session)
            await db.commit()

    asyncio.run(scenario())
