import io
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from pypdf import PdfReader
from docx import Document

SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Java": ["java", "core java", "java 8", "java 11", "java 17", "j2ee", "jakarta ee"],
    "Spring Boot": ["spring boot", "springboot", "spring framework", "spring mvc", "spring cloud", "spring security"],
    "Python": ["python", "python3", "python 3"],
    "FastAPI": ["fastapi", "fast api"],
    "Flask": ["flask"],
    "Django": ["django", "django rest framework", "drf"],
    "SQL": ["sql", "mysql", "sqlite", "tsql", "pl/sql", "ansi sql"],
    "PostgreSQL": ["postgresql", "postgres", "pgvector", "psql"],
    "MongoDB": ["mongodb", "mongo", "nosql", "mongoose", "atlas"],
    "Redis": ["redis", "redis cache", "redis streams"],
    "React.js": ["react", "react.js", "reactjs", "react 18", "next.js", "nextjs"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js", "es6", "ecmascript"],
    "Node.js": ["node.js", "nodejs", "express.js", "express"],
    "Docker": ["docker", "dockerfile", "docker-compose", "containerization"],
    "Kubernetes": ["kubernetes", "k8s", "helm", "eks", "gke"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "ecs", "fargate", "lambda", "rds"],
    "GCP": ["gcp", "google cloud", "google cloud platform", "bigquery", "cloud run"],
    "Microservices": ["microservices", "microservice architecture", "distributed systems", "service mesh"],
    "REST APIs": ["rest api", "restful api", "rest apis", "restful services", "openapi", "swagger"],
    "GraphQL": ["graphql", "apollo"],
    "Kafka": ["kafka", "apache kafka", "event-driven", "rabbitmq"],
    "Sentence Transformers": ["sentence transformers", "sentence-transformers", "huggingface", "bert", "all-minilm-l6-v2", "embeddings"],
    "spaCy": ["spacy", "named entity recognition", "ner"],
    "NLP": ["nlp", "natural language processing", "text mining", "semantic search", "rag", "langchain", "langgraph"],
    "Machine Learning": ["machine learning", "ml", "scikit-learn", "sklearn", "xgboost", "lightgbm"],
    "Deep Learning": ["deep learning", "pytorch", "tensorflow", "neural networks"],
    "Git": ["git", "github", "gitlab", "version control"],
    "CI/CD": ["ci/cd", "jenkins", "github actions", "gitlab ci", "devops"],
    "Tailwind CSS": ["tailwind", "tailwind css", "tailwindcss"],
    "Hibernate": ["hibernate", "jpa", "spring data jpa", "orm"],
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,5}")
EXP_YEARS_REGEX = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|relevant\s+|total\s+|industry\s+|hands-on\s+)?experience",
    re.IGNORECASE,
)
EXP_RANGE_REGEX = re.compile(r"(\d+)\s*[-–to]+\s*(\d+)\s*(?:years?|yrs?)", re.IGNORECASE)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        pages.append(txt)
    return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)
    return "\n".join(paragraphs).strip()


def extract_skills_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    detected: List[str] = []
    for canonical, aliases in SKILL_TAXONOMY.items():
        for alias in aliases:
            pattern = r"(?:^|[\s,;/()\[\]\-•])" + re.escape(alias) + r"(?:$|[\s,;/()\[\].\-•])"
            if re.search(pattern, text_lower):
                detected.append(canonical)
                break
    return detected


def extract_experience_years(text: str, is_jd: bool = False) -> float:
    explicit_header = re.search(
        r"(?:total\s+experience|experience|work\s+experience)\s*[:\-]\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )
    if explicit_header:
        return float(explicit_header.group(1))

    if is_jd:
        range_match = EXP_RANGE_REGEX.search(text)
        if range_match:
            return float(range_match.group(1))

    exp_matches = EXP_YEARS_REGEX.findall(text)
    if exp_matches:
        vals = [float(x) for x in exp_matches if float(x) <= 35]
        if vals:
            return max(vals) if not is_jd else min(vals)

    year_ranges = re.findall(r"(20\d{2})\s*[-–—to]+\s*(20\d{2}|present|current|now)", text, re.IGNORECASE)
    intervals: List[Tuple[int, int]] = []
    for start_str, end_str in year_ranges:
        start_yr = int(start_str)
        end_yr = 2026 if end_str.lower() in ("present", "current", "now") else int(end_str)
        if 2000 <= start_yr <= end_yr <= 2027 and (end_yr - start_yr) <= 20:
            intervals.append((start_yr, end_yr))

    if intervals:
        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]
        for curr in intervals[1:]:
            prev_start, prev_end = merged[-1]
            if curr[0] <= prev_end:
                merged[-1] = (prev_start, max(prev_end, curr[1]))
            else:
                merged.append(curr)
        total_span = sum(end - start for start, end in merged)
        if total_span > 0:
            return float(total_span)

    return 0.0


def extract_education(text: str) -> Tuple[str, bool]:
    degree_patterns = [
        (r"M\.?\s*Tech|Master of Technology|M\.?\s*S\.?|M\.?\s*Sc|MCA|Master of Computer Applications", "Master's Degree in Computer Science / Engineering"),
        (r"B\.?\s*Tech|Bachelor of Technology|B\.?\s*E\.?|Bachelor of Engineering|B\.?\s*S\.?|BCA", "Bachelor's Degree in Engineering / Computer Science"),
        (r"B\.?\s*Sc|Bachelor of Science|Diploma", "Bachelor of Science / Technical Diploma"),
    ]
    for pattern, label in degree_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            for line in text.splitlines():
                if re.search(pattern, line, re.IGNORECASE) and len(line.strip()) < 120:
                    return line.strip(), True
            return label, True
    return "Degree not explicitly listed", False


def parse_job_description(raw_text: str, title_hint: str = "") -> Dict[str, Any]:
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    title = title_hint.strip() if title_hint.strip() else (lines[0][:100] if lines else "Software / AI Engineer Role")
    for ln in lines[:5]:
        m = re.match(r"^(?:job\s+title|role|position)\s*[:\-]\s*(.+)$", ln, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            break

    skills = extract_skills_from_text(raw_text)
    min_exp = extract_experience_years(raw_text, is_jd=True)
    edu_summary, _ = extract_education(raw_text)

    return {
        "title": title,
        "raw_text": raw_text,
        "skills": skills,
        "min_experience_years": min_exp,
        "required_education": edu_summary if edu_summary != "Degree not explicitly listed" else "B.Tech / B.E. / MCA in Computer Science or equivalent",
        "responsibilities_text": raw_text,
    }


def parse_resume_file(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    candidate_name = Path(filename).stem.replace("_", " ").replace("-", " ").title()
    for ln in lines[:6]:
        name_match = re.match(r"^(?:candidate\s+name|name)\s*[:\-]\s*(.+)$", ln, re.IGNORECASE)
        if name_match:
            candidate_name = name_match.group(1).strip()
            break
        if (
            not EMAIL_REGEX.search(ln)
            and not any(k in ln.lower() for k in ("resume", "curriculum", "summary", "email", "phone", "http", "linkedin"))
            and 2 <= len(ln.split()) <= 4
            and len(ln) <= 45
        ):
            candidate_name = ln.strip()
            break

    email_match = EMAIL_REGEX.search(raw_text)
    email = email_match.group(0) if email_match else "not_provided@example.com"

    phone_match = PHONE_REGEX.search(raw_text)
    phone = phone_match.group(0).strip() if phone_match else "+91-9000000000"

    skills = extract_skills_from_text(raw_text)
    exp_years = extract_experience_years(raw_text, is_jd=False)
    edu_summary, degree_matched = extract_education(raw_text)

    exp_lines = []
    capture = False
    for ln in lines:
        if re.match(r"^(?:work\s+experience|professional\s+experience|experience|projects)\b", ln, re.IGNORECASE):
            capture = True
            continue
        if capture and re.match(r"^(?:education|certifications|achievements|references)\b", ln, re.IGNORECASE):
            break
        if capture:
            exp_lines.append(ln)

    experience_text = "\n".join(exp_lines) if exp_lines else raw_text

    return {
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
        "filename": filename,
        "file_format": ext.upper(),
        "total_experience_years": exp_years,
        "education_summary": edu_summary,
        "degree_matched": degree_matched,
        "skills": skills,
        "raw_text": raw_text,
        "experience_text": experience_text,
    }
