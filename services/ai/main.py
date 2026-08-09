from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from core.config import settings
from agents import tutor_chat, explain_concept, generate_questions, evaluate_answer, buddy_chat, generate_learning_path

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    agent_type: str = "tutor"
    context: dict = {}

class ExplainRequest(BaseModel):
    topic: str
    level: str = "beginner"

class GenerateQuestionsRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5
    context: str = ""

class EvaluateRequest(BaseModel):
    question: str
    correct_answer: str
    student_answer: str

class PlanRequest(BaseModel):
    goal: str
    current_level: str = "beginner"
    available_hours: int = 5
    topics: list[str] = None

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "EduFlow AI Service"}

@app.post("/api/agents/chat")
async def agent_chat(req: ChatRequest):
    if req.agent_type == "tutor":
        result = await tutor_chat(req.message, req.context)
    elif req.agent_type == "buddy":
        result = await buddy_chat(req.message, req.context)
    else:
        result = await tutor_chat(req.message, req.context)
    return {"response": result, "agent_type": req.agent_type}

@app.post("/api/agents/explain")
async def agent_explain(req: ExplainRequest):
    result = await explain_concept(req.topic, req.level)
    return {"response": result, "topic": req.topic}

@app.post("/api/agents/generate-questions")
async def agent_generate_questions(req: GenerateQuestionsRequest):
    questions = await generate_questions(req.topic, req.difficulty, req.count, req.context)
    return {"questions": questions, "count": len(questions)}

@app.post("/api/agents/evaluate")
async def agent_evaluate(req: EvaluateRequest):
    result = await evaluate_answer(req.question, req.correct_answer, req.student_answer)
    return result

@app.post("/api/agents/plan")
async def agent_plan(req: PlanRequest):
    plan = await generate_learning_path(req.goal, req.current_level, req.available_hours, req.topics)
    return plan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.API_PORT)