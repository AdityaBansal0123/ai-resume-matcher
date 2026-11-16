import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_matcher.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobDescriptionModel(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    min_experience_years = Column(Float, default=0.0)
    required_education = Column(String(255), default="Bachelor's in CS/Engineering or equivalent")
    responsibilities_text = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evaluations = relationship("CandidateEvaluationModel", back_populates="job_description", cascade="all, delete-orphan")


class CandidateEvaluationModel(Base):
    __tablename__ = "candidate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    phone = Column(String(100), default="")
    filename = Column(String(255), nullable=False)
    file_format = Column(String(20), nullable=False)
    total_experience_years = Column(Float, default=0.0)
    education_summary = Column(String(255), default="")
    extracted_skills = Column(JSON, default=list)
    raw_text = Column(Text, default="")
    experience_summary = Column(Text, default="")

    # Matching & Scoring outputs (Modules 3, 4, 5)
    overall_score = Column(Float, nullable=False)
    skill_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)

    matched_skills = Column(JSON, default=list)
    exact_matched_skills = Column(JSON, default=list)
    semantic_matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    experience_status = Column(String(100), default="Met")
    reasons = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job_description = relationship("JobDescriptionModel", back_populates="evaluations")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
