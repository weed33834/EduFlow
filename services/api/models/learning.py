from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal = Column(Text)
    estimated_duration = Column(Integer)
    difficulty = Column(String(20), default="beginner")
    status = Column(String(20), default="not_started")
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    content = Column(JSON, default=list)
    status = Column(String(20), default="not_started")
    progress = Column(Float, default=0.0)
    estimated_minutes = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    session_type = Column(String(50), default="quiz")
    topic = Column(String(255))
    questions = Column(JSON, default=list)
    answers = Column(JSON, default=list)
    score = Column(Float)
    status = Column(String(20), default="in_progress")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    learning_time_minutes = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    quiz_scores = Column(JSON, default=list)
    weak_points = Column(JSON, default=list)
    strong_points = Column(JSON, default=list)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReviewItem(Base):
    """间隔重复复习项：按知识点/主题追踪掌握度与下次复习时间(FSRS 启发式)。

    由练习完成后自动创建/更新，供「复习」页面按 due_at 排期展示。
    """

    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    topic = Column(String(255), nullable=False)
    mastery_level = Column(Float, default=0.0)          # 0-1
    review_count = Column(Integer, default=0)
    last_score = Column(Float)                           # 最近一次复习得分 0-100
    stability = Column(Float, default=1.0)               # 记忆稳定性(天)
    difficulty = Column(Float, default=0.5)              # 0-1
    due_at = Column(DateTime(timezone=True), nullable=False)  # 下次复习时间
    last_reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
