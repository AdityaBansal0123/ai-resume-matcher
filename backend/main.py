import os
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import init_db, get_db, JobDescriptionModel, CandidateEvaluationModel
from services.parser import parse_job_description, parse_resume_file
from services.matcher import ResumeMatcherEngine

matcher_engine: Optional[ResumeMatcherEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global matcher_engine
    init_db()
    matcher_engine = ResumeMatcherEngine(
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
        threshold=float(os.getenv("SEMANTIC_SKILL_THRESHOLD", "0.72")),
    )
    yield


app = FastAPI(
    title="AI-Based Resume Matching & Candidate Ranking API",
    description="Compares multiple candidate resumes (PDF/DOCX) against a Job Description using hybrid semantic similarity and explainable scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JDCreateRequest(BaseModel):
    title: Optional[str] = ""
    raw_text: str


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_path = Path(__file__).resolve().parent.parent / "frontend" / "dashboard.html"
    if dashboard_path.exists():
        return dashboard_path.read_text(encoding="utf-8")
    return "<h3>Dashboard file not found. Place dashboard.html in frontend/</h3>"


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "model": os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
        "semantic_threshold": float(os.getenv("SEMANTIC_SKILL_THRESHOLD", "0.72")),
    }


@app.post("/api/jd")
def create_job_description(payload: JDCreateRequest, db: Session = Depends(get_db)):
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Job Description text cannot be empty.")

    parsed = parse_job_description(payload.raw_text, title_hint=payload.title or "")
    jd_record = JobDescriptionModel(
        title=parsed["title"],
        raw_text=parsed["raw_text"],
        required_skills=parsed["skills"],
        min_experience_years=parsed["min_experience_years"],
        required_education=parsed["required_education"],
        responsibilities_text=parsed["responsibilities_text"],
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    return {
        "jd_id": jd_record.id,
        "title": jd_record.title,
        "required_skills": jd_record.required_skills,
        "min_experience_years": jd_record.min_experience_years,
        "required_education": jd_record.required_education,
        "raw_text": jd_record.raw_text,
    }


@app.post("/api/resumes/evaluate")
async def upload_and_evaluate_resumes(
    jd_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    jd_record = db.query(JobDescriptionModel).filter(JobDescriptionModel.id == jd_id).first()
    if not jd_record:
        raise HTTPException(status_code=404, detail=f"Job Description ID {jd_id} not found.")

    jd_data = {
        "title": jd_record.title,
        "raw_text": jd_record.raw_text,
        "skills": jd_record.required_skills,
        "min_experience_years": jd_record.min_experience_years,
        "required_education": jd_record.required_education,
        "responsibilities_text": jd_record.responsibilities_text,
    }

    db.query(CandidateEvaluationModel).filter(CandidateEvaluationModel.jd_id == jd_id).delete()
    db.commit()

    results = []
    for upload in files:
        content = await upload.read()
        parsed_res = parse_resume_file(upload.filename or "resume.pdf", content)
        eval_res = matcher_engine.evaluate_candidate(jd_data, parsed_res)

        cand_model = CandidateEvaluationModel(
            jd_id=jd_record.id,
            candidate_name=parsed_res["candidate_name"],
            email=parsed_res["email"],
            phone=parsed_res["phone"],
            filename=parsed_res["filename"],
            file_format=parsed_res["file_format"],
            total_experience_years=parsed_res["total_experience_years"],
            education_summary=parsed_res["education_summary"],
            extracted_skills=parsed_res["skills"],
            raw_text=parsed_res["raw_text"],
            experience_summary=parsed_res["experience_text"],
            overall_score=eval_res["overall_score"],
            skill_score=eval_res["breakdown"]["skill_score"],
            semantic_score=eval_res["breakdown"]["semantic_score"],
            experience_score=eval_res["breakdown"]["experience_score"],
            education_score=eval_res["breakdown"]["education_score"],
            matched_skills=eval_res["matched_skills"],
            exact_matched_skills=eval_res["exact_matched_skills"],
            semantic_matched_skills=eval_res["semantic_matched_skills"],
            missing_skills=eval_res["missing_skills"],
            experience_status=eval_res["experience_status"],
            reasons=eval_res["reasons"],
        )
        db.add(cand_model)
        db.commit()
        db.refresh(cand_model)
        results.append(cand_model)

    results.sort(key=lambda x: x.overall_score, reverse=True)

    return {
        "jd": jd_data,
        "total_candidates": len(results),
        "rankings": [
            {
                "id": r.id,
                "rank": idx + 1,
                "candidate_name": r.candidate_name,
                "email": r.email,
                "phone": r.phone,
                "filename": r.filename,
                "file_format": r.file_format,
                "experience_years": r.total_experience_years,
                "education_summary": r.education_summary,
                "extracted_skills": r.extracted_skills,
                "overall_score": r.overall_score,
                "breakdown": {
                    "skill_score": r.skill_score,
                    "semantic_score": r.semantic_score,
                    "experience_score": r.experience_score,
                    "education_score": r.education_score,
                },
                "matched_skills": r.matched_skills,
                "exact_matched_skills": r.exact_matched_skills,
                "semantic_matched_skills": r.semantic_matched_skills,
                "missing_skills": r.missing_skills,
                "experience_status": r.experience_status,
                "reasons": r.reasons,
                "experience_summary": r.experience_summary,
            }
            for idx, r in enumerate(results)
        ],
    }


@app.post("/api/demo/load-sample-batch")
def load_sample_batch(db: Session = Depends(get_db)):
    sample_dir = Path(__file__).resolve().parent.parent / "sample_data"
    jd_path = sample_dir / "sample_jd_java_backend.txt"
    resumes_dir = sample_dir / "resumes"

    if not jd_path.exists():
        raise HTTPException(status_code=404, detail="Sample JD file not found.")

    jd_text = jd_path.read_text(encoding="utf-8")
    parsed_jd = parse_job_description(jd_text, title_hint="Senior Java & Microservices Backend Engineer")

    jd_record = JobDescriptionModel(
        title=parsed_jd["title"],
        raw_text=parsed_jd["raw_text"],
        required_skills=parsed_jd["skills"],
        min_experience_years=parsed_jd["min_experience_years"],
        required_education=parsed_jd["required_education"],
        responsibilities_text=parsed_jd["responsibilities_text"],
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    results = []
    for file_path in sorted(resumes_dir.glob("*.*")):
        if file_path.suffix.lower() not in (".pdf", ".docx"):
            continue
        file_bytes = file_path.read_bytes()
        parsed_res = parse_resume_file(file_path.name, file_bytes)
        eval_res = matcher_engine.evaluate_candidate(parsed_jd, parsed_res)

        cand_model = CandidateEvaluationModel(
            jd_id=jd_record.id,
            candidate_name=parsed_res["candidate_name"],
            email=parsed_res["email"],
            phone=parsed_res["phone"],
            filename=parsed_res["filename"],
            file_format=parsed_res["file_format"],
            total_experience_years=parsed_res["total_experience_years"],
            education_summary=parsed_res["education_summary"],
            extracted_skills=parsed_res["skills"],
            raw_text=parsed_res["raw_text"],
            experience_summary=parsed_res["experience_text"],
            overall_score=eval_res["overall_score"],
            skill_score=eval_res["breakdown"]["skill_score"],
            semantic_score=eval_res["breakdown"]["semantic_score"],
            experience_score=eval_res["breakdown"]["experience_score"],
            education_score=eval_res["breakdown"]["education_score"],
            matched_skills=eval_res["matched_skills"],
            exact_matched_skills=eval_res["exact_matched_skills"],
            semantic_matched_skills=eval_res["semantic_matched_skills"],
            missing_skills=eval_res["missing_skills"],
            experience_status=eval_res["experience_status"],
            reasons=eval_res["reasons"],
        )
        db.add(cand_model)
        db.commit()
        db.refresh(cand_model)
        results.append(cand_model)

    results.sort(key=lambda x: x.overall_score, reverse=True)
    return {
        "jd": parsed_jd,
        "jd_id": jd_record.id,
        "total_candidates": len(results),
        "rankings": [
            {
                "id": r.id,
                "rank": idx + 1,
                "candidate_name": r.candidate_name,
                "email": r.email,
                "phone": r.phone,
                "filename": r.filename,
                "file_format": r.file_format,
                "experience_years": r.total_experience_years,
                "education_summary": r.education_summary,
                "extracted_skills": r.extracted_skills,
                "overall_score": r.overall_score,
                "breakdown": {
                    "skill_score": r.skill_score,
                    "semantic_score": r.semantic_score,
                    "experience_score": r.experience_score,
                    "education_score": r.education_score,
                },
                "matched_skills": r.matched_skills,
                "exact_matched_skills": r.exact_matched_skills,
                "semantic_matched_skills": r.semantic_matched_skills,
                "missing_skills": r.missing_skills,
                "experience_status": r.experience_status,
                "reasons": r.reasons,
                "experience_summary": r.experience_summary,
            }
            for idx, r in enumerate(results)
        ],
    }