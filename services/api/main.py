from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import auth, learning, progress, practice, ai

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(learning.router)
app.include_router(progress.router)
app.include_router(practice.router)
app.include_router(ai.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "service": "EduFlow API"}