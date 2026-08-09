"""
EduFlow Engine - Learning Path Engine & Knowledge Tracing
Handles learning path generation, spaced repetition, and knowledge tracing
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import math
import json

app = FastAPI(title="EduFlow Engine", version="0.1.0")

class KnowledgeState(BaseModel):
    user_id: int
    topic: str
    mastery_level: float = 0.0
    review_count: int = 0
    last_review_score: Optional[float] = None
    time_since_last_review_hours: float = 0.0

class ReviewRequest(BaseModel):
    knowledge_state: KnowledgeState
    desired_retention: float = 0.9

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "EduFlow Engine"}

@app.post("/api/engine/next-review")
async def calculate_next_review(req: ReviewRequest):
    """Calculate optimal next review time using FSRS-inspired algorithm"""
    ks = req.knowledge_state
    stability = max(1.0, ks.review_count * 0.5 + ks.mastery_level * 2)
    difficulty = 1.0 - ks.mastery_level
    
    if ks.last_review_score is not None:
        score_factor = ks.last_review_score / 100.0
        stability *= (1.0 + score_factor * 0.5)
    
    next_interval_hours = stability * 24 * (1.0 - difficulty * 0.3)
    retention = math.exp(-ks.time_since_last_review_hours / (stability * 24))
    
    return {
        "next_review_hours": round(next_interval_hours, 1),
        "predicted_retention": round(retention, 3),
        "stability": round(stability, 2),
        "difficulty": round(difficulty, 2),
        "recommended": "review_now" if retention < req.desired_retention else "skip"
    }

@app.post("/api/engine/knowledge-tracing")
async def trace_knowledge(states: list[KnowledgeState]):
    """Analyze knowledge state across topics and identify weak points"""
    results = []
    weak_points = []
    
    for s in states:
        mastery = s.mastery_level
        results.append({
            "topic": s.topic,
            "mastery": round(mastery * 100, 1),
            "status": "mastered" if mastery >= 0.8 else "learning" if mastery >= 0.4 else "weak",
            "reviews_done": s.review_count,
        })
        if mastery < 0.6:
            weak_points.append(s.topic)
    
    return {
        "topics": results,
        "weak_points": weak_points[:5],
        "overall_mastery": round(sum(s.mastery_level for s in states) / max(len(states), 1) * 100, 1),
        "total_topics": len(states),
    }

@app.post("/api/engine/estimate-duration")
async def estimate_duration(topic: str, difficulty: str = "medium", depth: str = "standard"):
    """Estimate learning time for a topic"""
    base = {"beginner": 30, "easy": 45, "medium": 60, "hard": 90, "expert": 120}
    depth_mult = {"overview": 0.5, "standard": 1.0, "deep": 2.0}
    minutes = base.get(difficulty, 60) * depth_mult.get(depth, 1.0)
    return {"topic": topic, "estimated_minutes": int(minutes), "difficulty": difficulty, "depth": depth}