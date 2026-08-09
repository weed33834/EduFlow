from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
import httpx
import json

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ChatRequest(BaseModel):
    message: str
    context: dict = {}
    agent_type: str = "tutor"

class GenerateQuestionsRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5
    context: str = ""

@router.post("/chat")
async def ai_chat(req: ChatRequest):
    # Route to AI agent service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://ai-service:8100/api/agents/chat",
                json=req.model_dump(),
                timeout=60.0
            )
            return resp.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI service unavailable")

@router.post("/generate-questions")
async def generate_questions(req: GenerateQuestionsRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://ai-service:8100/api/agents/generate-questions",
                json=req.model_dump(),
                timeout=60.0
            )
            return resp.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI service unavailable")