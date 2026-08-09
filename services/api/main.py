from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import engine, Base
from routers import auth, learning, progress, practice, ai
# Import models so they are registered with Base.metadata before table creation
import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(learning.router)
app.include_router(progress.router)
app.include_router(practice.router)
app.include_router(ai.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "service": "EduFlow API",
    }
