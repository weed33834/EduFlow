"""判题结果回写学生画像的测试（真实 sqlite + API 全链路）"""
import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models import StudentProfile
from app.routers.chat import update_profile_on_judge
from tests.conftest import find_complete, parse_sse_events


def test_update_profile_on_judge_direct(client):
    """直接调用：对/错分别进 strengths/weaknesses，重复概念不重复追加"""
    import uuid as _uuid
    suffix = _uuid.uuid4().hex[:8]
    reg = client.post("/api/auth/register", json={
        "email": f"prof-{suffix}@example.com",
        "username": f"prof{suffix}",
        "password": "password123",
    })
    assert reg.status_code == 200
    user_id = reg.json()["user"]["id"]

    async def run():
        async with async_session() as db:
            await update_profile_on_judge(db, user_id, False, "递归")
            await update_profile_on_judge(db, user_id, False, "递归")
            await update_profile_on_judge(db, user_id, True, "闭包")
            await db.commit()
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user_id)
            )
            profile = result.scalar_one()
            return list(profile.weaknesses or []), list(profile.strengths or [])

    weaknesses, strengths = asyncio.run(run())
    assert weaknesses.count("递归") == 1, "重复判错不应重复追加"
    assert strengths == ["闭包"]


def test_wrong_quiz_answer_writes_weakness(client, auth_headers):
    """API 链路：出题→答错→weaknesses 出现该概念"""
    body = {"message": "考考我闭包"}
    resp = client.post("/api/chat", json=body, headers=auth_headers)
    assert resp.status_code == 200
    complete = find_complete(parse_sse_events(resp.text))
    session_id = complete["session_id"]

    resp2 = client.post(
        "/api/chat",
        json={"message": "B", "session_id": session_id},
        headers=auth_headers,
    )
    complete2 = find_complete(parse_sse_events(resp2.text))
    assert complete2.get("judged", {}).get("correct") is False

    user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]

    async def read_profile():
        async with async_session() as db:
            result = await db.execute(
                select(StudentProfile).where(StudentProfile.user_id == user_id)
            )
            profile = result.scalar_one()
            return list(profile.weaknesses or [])

    weaknesses = asyncio.run(read_profile())
    assert any("闭包" in w for w in weaknesses), f"weaknesses 应包含概念: {weaknesses}"
