#!/usr/bin/env python3
"""
Generates 2 sample Job Descriptions and 12 synthetic candidate resumes
(6 PDFs and 6 DOCX files) inside sample_data/, then runs the actual
backend parser and hybrid semantic matcher to verify end-to-end accuracy.
"""

import io
import json
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt

BASE_DIR = Path("/working_dir/c_fcc58f61fc5bbc60/artifacts/file_generation/ttl=63d/intermediate/ai-resume-matcher")
SAMPLE_DIR = BASE_DIR / "sample_data"
RESUMES_DIR = SAMPLE_DIR / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)


def write_simple_text_pdf(output_path: Path, lines: list[str]) -> None:
    """
    Creates a clean, valid single-page PDF file containing the exact lines of text
    readable by pypdf / pdfplumber without requiring external binary tools.
    """
    def escape_pdf_text(s: str) -> str:
        s_ascii = s.encode("ascii", errors="replace").decode("ascii")
        return s_ascii.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream_lines = ["BT", "/F1 10 Tf", "50 790 Td", "13 TL"]
    for idx, line in enumerate(lines):
        escaped = escape_pdf_text(line)
        if idx == 0:
            stream_lines.append(f"({escaped}) Tj")
        else:
            stream_lines.append(f"T* ({escaped}) Tj")
    stream_lines.append("ET")
    stream_data = "\n".join(stream_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream_data)).encode("ascii") + b" >>\nstream\n" + stream_data + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    output_path.write_bytes(bytes(out))


def write_docx_resume(output_path: Path, lines: list[str]) -> None:
    doc = Document()
    for idx, line in enumerate(lines):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = "Calibri"
        run.font.size = Pt(14 if idx == 0 else 10.5)
        if idx == 0 or line.endswith(":"):
            run.bold = True
    doc.save(str(output_path))


# 1. Write 2 Sample Job Descriptions
JD_JAVA_BACKEND = """Job Title: Senior Java & Microservices Backend Engineer
Location: Bengaluru / Hybrid (Synthetic Evaluation Dataset)
Experience Required: 4+ years of professional experience
Required Qualification: B.Tech / B.E. / M.Tech / MCA in Computer Science or Engineering

Role Overview:
We are looking for a Backend Engineer with strong hands-on expertise in Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, and Docker to architect and scale high-throughput distributed backend services.

Key Requirements & Technical Skills:
- 4 to 6 years of backend software engineering experience building enterprise services.
- Proficiency in Java, Spring Boot, and REST APIs for distributed backend systems.
- Strong database design and query optimization skills using SQL and PostgreSQL.
- Hands-on experience with Microservices architecture, containerization using Docker, and cloud deployment on AWS.
- Educational qualification: B.Tech / B.E. or M.Tech in Computer Science or equivalent STEM field.
"""

JD_AI_FULLSTACK = """Job Title: AI & Full Stack Developer (FastAPI + React + NLP)
Location: Remote / Hybrid (Synthetic Evaluation Dataset)
Experience Required: 2+ years of professional experience
Required Qualification: B.Tech / B.E. in Computer Science, Computational Mathematics, or related discipline

Role Overview:
We are seeking an AI / Full Stack Developer to build intelligent document processing and semantic matching applications using Python, FastAPI, React.js, Sentence Transformers, spaCy, PostgreSQL, and Docker.

Key Requirements & Technical Skills:
- 2+ years of experience developing full-stack AI applications and REST APIs.
- Backend proficiency in Python and FastAPI with PostgreSQL or MongoDB databases.
- Applied NLP experience with Sentence Transformers, spaCy, and Machine Learning for semantic similarity and ranking.
- Frontend experience building responsive dashboards in React.js and Tailwind CSS.
- Experience containerizing services with Docker and deploying on AWS or GCP.
"""

(SAMPLE_DIR / "sample_jd_java_backend.txt").write_text(JD_JAVA_BACKEND.strip(), encoding="utf-8")
(SAMPLE_DIR / "sample_jd_ai_fullstack.txt").write_text(JD_AI_FULLSTACK.strip(), encoding="utf-8")

# 2. Define 12 Synthetic Candidates (6 PDFs + 6 DOCX)
CANDIDATES = [
    {
        "filename": "01_Aarav_Mehta_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Aarav Mehta",
            "Email: aarav.mehta.synth@example.com | Phone: +91-9810011001",
            "Total Experience: 5 years",
            "Education:",
            "B.Tech in Computer Science and Engineering, VIT Vellore (2017 - 2021)",
            "Technical Skills:",
            "Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, Docker, AWS, Hibernate, Kafka, Git",
            "Work Experience:",
            "Senior Backend Engineer | FinCore Systems (2023 - 2026)",
            "- Architected high-throughput payment Microservices using Java 17, Spring Boot, and REST APIs handling 15,000 req/sec.",
            "- Optimized complex transactional queries in PostgreSQL and SQL, reducing p99 latency by 38%.",
            "- Containerized 14 backend services with Docker and deployed on AWS ECS clusters.",
            "Software Engineer | CloudPulse Tech (2021 - 2023)",
            "- Built distributed order processing services in Java, Spring Boot, Hibernate, and SQL.",
        ],
    },
    {
        "filename": "02_Priya_Nair_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Priya Nair",
            "Email: priya.nair.synth@example.com | Phone: +91-9810011002",
            "Total Experience: 4.5 years",
            "Education:",
            "M.Tech in Software Engineering, IIIT Bangalore (2019 - 2021)",
            "Technical Skills:",
            "Java, Spring Boot, SQL, PostgreSQL, REST APIs, Microservices, Docker, Kubernetes, Git",
            "Work Experience:",
            "Backend Software Engineer | PayScale India (2021 - 2026)",
            "- Designed scalable ledger Microservices using Java, Spring Boot, and REST APIs.",
            "- Managed multi-terabyte relational schemas on PostgreSQL and wrote optimized SQL stored procedures.",
            "- Packaged backend applications using Docker and orchestrated deployments on Kubernetes.",
        ],
    },
    {
        "filename": "03_Rohan_Kulkarni_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Rohan Kulkarni",
            "Email: rohan.kulkarni.synth@example.com | Phone: +91-9810011003",
            "Total Experience: 4 years",
            "Education:",
            "B.E. in Information Technology, PICT Pune (2018 - 2022)",
            "Technical Skills:",
            "Java, Spring Boot, SQL, REST APIs, Hibernate, Kafka, Kubernetes, GCP, Git",
            "Work Experience:",
            "Software Development Engineer II | Nexus Commerce (2022 - 2026)",
            "- Note: Demonstrates semantic skill matching (has SQL & Hibernate instead of explicit PostgreSQL; Kubernetes & GCP instead of Docker & AWS; Kafka distributed services).",
            "- Engineered event-driven backend services using Java, Spring Boot, REST APIs, and Apache Kafka.",
            "- Built relational data access layers with SQL and Hibernate ORM, deploying workloads on Kubernetes and GCP.",
        ],
    },
    {
        "filename": "04_Sneha_Iyer_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Sneha Iyer",
            "Email: sneha.iyer.synth@example.com | Phone: +91-9810011004",
            "Total Experience: 3.5 years",
            "Education:",
            "B.Tech in Computer Science, SRM Institute of Science and Technology (2019 - 2023)",
            "Technical Skills:",
            "Java, Spring Boot, PostgreSQL, SQL, REST APIs, Docker, React.js, Git",
            "Work Experience:",
            "Full Stack Java Developer | Stratagem Labs (2022 - 2026)",
            "- Developed enterprise REST APIs with Java and Spring Boot backed by PostgreSQL and SQL databases.",
            "- Containerized backend APIs with Docker and integrated frontend modules in React.js.",
        ],
    },
    {
        "filename": "05_Vikram_Deshmukh_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Vikram Deshmukh",
            "Email: vikram.deshmukh.synth@example.com | Phone: +91-9810011005",
            "Total Experience: 5 years",
            "Education:",
            "B.Tech in Computer Engineering, COEP Pune (2017 - 2021)",
            "Technical Skills:",
            "Python, FastAPI, PostgreSQL, SQL, Microservices, REST APIs, Docker, AWS, Redis, Kubernetes",
            "Work Experience:",
            "Senior Backend Architect | QuantFlow AI (2021 - 2026)",
            "- Cross-stack semantic test case: 5 years experience in Python & FastAPI Microservices with PostgreSQL, SQL, REST APIs, Docker, and AWS.",
            "- Designed high-concurrency distributed Microservices and REST APIs deployed via Docker on AWS.",
        ],
    },
    {
        "filename": "06_Ananya_Chatterjee_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Ananya Chatterjee",
            "Email: ananya.chatterjee.synth@example.com | Phone: +91-9810011006",
            "Total Experience: 3 years",
            "Education:",
            "B.Tech in Computer Science, Jadavpur University (2020 - 2023)",
            "Technical Skills:",
            "Java, Spring Boot, SQL, REST APIs, Hibernate, Git",
            "Work Experience:",
            "Backend Developer | VeriSoft Solutions (2023 - 2026)",
            "- Built core banking REST APIs in Java and Spring Boot with SQL and Hibernate persistence.",
            "- Collaborated on API schema design and unit testing for enterprise banking modules.",
        ],
    },
    {
        "filename": "07_Karthik_Subramanian_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Karthik Subramanian",
            "Email: karthik.subramanian.synth@example.com | Phone: +91-9810011007",
            "Total Experience: 4 years",
            "Education:",
            "MCA (Master of Computer Applications), NIT Trichy (2019 - 2022)",
            "Technical Skills:",
            "Java, SQL, PostgreSQL, REST APIs, AWS, CI/CD, Git",
            "Work Experience:",
            "Systems Engineer | InfoGrid Services (2022 - 2026)",
            "- Maintained legacy Java backend services and REST APIs connected to PostgreSQL and SQL databases on AWS.",
            "- Automated build pipelines using Jenkins CI/CD and Git.",
        ],
    },
    {
        "filename": "08_Meera_Krishnan_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Meera Krishnan",
            "Email: meera.krishnan.synth@example.com | Phone: +91-9810011008",
            "Total Experience: 2.5 years",
            "Education:",
            "B.Tech in Computational Mathematics, NIT Agartala (2020 - 2024)",
            "Technical Skills:",
            "Python, FastAPI, React.js, Tailwind CSS, Sentence Transformers, spaCy, NLP, Machine Learning, PostgreSQL, SQL, Docker, AWS, REST APIs",
            "Work Experience:",
            "AI & Full Stack Engineer | LexiRank AI (2024 - 2026)",
            "- Built semantic resume parsing and ranking pipelines using Python, FastAPI, Sentence Transformers (all-MiniLM-L6-v2), and spaCy.",
            "- Engineered interactive recruiter dashboards in React.js and Tailwind CSS backed by PostgreSQL and Docker on AWS.",
        ],
    },
    {
        "filename": "09_Siddharth_Verma_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Siddharth Verma",
            "Email: siddharth.verma.synth@example.com | Phone: +91-9810011009",
            "Total Experience: 2 years",
            "Education:",
            "B.Tech in Information Technology, DTU Delhi (2020 - 2024)",
            "Technical Skills:",
            "Java, Spring Boot, MySQL, SQL, Git",
            "Work Experience:",
            "Junior Java Associate | CodeCraft India (2024 - 2026)",
            "- Assisted in developing internal CRUD modules using Java, Spring Boot, and SQL.",
            "- Wrote unit tests and fixed bug tickets for internal reporting portals.",
        ],
    },
    {
        "filename": "10_Neha_kapoor_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Neha Kapoor",
            "Email: neha.kapoor.synth@example.com | Phone: +91-9810011010",
            "Total Experience: 3.5 years",
            "Education:",
            "B.Tech in Electronics and Communication, Thapar Institute (2019 - 2023)",
            "Technical Skills:",
            "Node.js, TypeScript, JavaScript, React.js, MongoDB, REST APIs, Docker, AWS",
            "Work Experience:",
            "MERN Stack Developer | PixelWave Digital (2022 - 2026)",
            "- Developed e-commerce storefronts and REST APIs using Node.js, TypeScript, React.js, and MongoDB.",
            "- Deployed containerized web applications using Docker on AWS EC2.",
        ],
    },
    {
        "filename": "11_Arjun_Malhotra_Resume.pdf",
        "format": "pdf",
        "lines": [
            "Candidate Name: Arjun Malhotra",
            "Email: arjun.malhotra.synth@example.com | Phone: +91-9810011011",
            "Total Experience: 4 years",
            "Education:",
            "B.Sc in Statistics and Data Science, Fergusson College (2018 - 2021)",
            "Technical Skills:",
            "Python, SQL, PostgreSQL, Machine Learning, Deep Learning, NLP",
            "Work Experience:",
            "Data Analyst & ML Associate | InsightMetrics (2022 - 2026)",
            "- Built customer churn prediction models in Python and wrote analytical SQL queries on PostgreSQL data warehouses.",
        ],
    },
    {
        "filename": "12_Divya_banerjee_Resume.docx",
        "format": "docx",
        "lines": [
            "Candidate Name: Divya Banerjee",
            "Email: divya.banerjee.synth@example.com | Phone: +91-9810011012",
            "Total Experience: 1.5 years",
            "Education:",
            "BCA, Christ University Bengaluru (2021 - 2024)",
            "Technical Skills:",
            "React.js, JavaScript, TypeScript, Tailwind CSS, Git",
            "Work Experience:",
            "Frontend UI Developer | StudioNova (2024 - 2026)",
            "- Built responsive marketing pages and design systems using React.js, TypeScript, and Tailwind CSS.",
        ],
    },
]

for cand in CANDIDATES:
    out_file = RESUMES_DIR / cand["filename"]
    if cand["format"] == "pdf":
        write_simple_text_pdf(out_file, cand["lines"])
    else:
        write_docx_resume(out_file, cand["lines"])

# Also save the generator script inside the repo's scripts/ folder so reviewers can inspect or re-run it
(BASE_DIR / "scripts" / "generate_sample_resumes.py").write_text(
    Path(__file__).read_text(encoding="utf-8"), encoding="utf-8"
)

# 3. Verify parsing and scoring on all 12 generated files using the actual backend services
sys.path.insert(0, str(BASE_DIR / "backend"))
from services.parser import parse_job_description, parse_resume_file
from services.matcher import ResumeMatcherEngine

engine = ResumeMatcherEngine()

jd1 = parse_job_description(JD_JAVA_BACKEND, title_hint="Senior Java & Microservices Backend Engineer")
jd2 = parse_job_description(JD_AI_FULLSTACK, title_hint="AI & Full Stack Developer (FastAPI + React + NLP)")

rankings_jd1 = []
rankings_jd2 = []

for file_path in sorted(RESUMES_DIR.glob("*.*")):
    raw_bytes = file_path.read_bytes()
    parsed_res = parse_resume_file(file_path.name, raw_bytes)
    eval1 = engine.evaluate_candidate(jd1, parsed_res)
    eval2 = engine.evaluate_candidate(jd2, parsed_res)

    rankings_jd1.append({**parsed_res, **eval1})
    rankings_jd2.append({**parsed_res, **eval2})

rankings_jd1.sort(key=lambda x: x["overall_score"], reverse=True)
rankings_jd2.sort(key=lambda x: x["overall_score"], reverse=True)

print(f"Generated {len(rankings_jd1)} resume files in {RESUMES_DIR}")
print("\n--- Rankings for JD 1: Senior Java & Microservices Backend Engineer ---")
for i, r in enumerate(rankings_jd1, 1):
    print(f"{i:2d}. {r['candidate_name']:24s} | {r['file_format']:4s} | {r['total_experience_years']:3g} yrs | Match: {r['overall_score']:3d}% | Exact: {len(r['exact_matched_skills'])}, Sem: {len(r['semantic_matched_skills'])}, Missing: {len(r['missing_skills'])}")

print("\n--- Rankings for JD 2: AI & Full Stack Developer (FastAPI + React + NLP) ---")
for i, r in enumerate(rankings_jd2, 1):
    print(f"{i:2d}. {r['candidate_name']:24s} | {r['file_format']:4s} | {r['total_experience_years']:3g} yrs | Match: {r['overall_score']:3d}% | Exact: {len(r['exact_matched_skills'])}, Sem: {len(r['semantic_matched_skills'])}, Missing: {len(r['missing_skills'])}")

# Save precomputed evaluation snapshots for the interactive web app & documentation
snapshot = {
    "jd_java_backend": jd1,
    "jd_ai_fullstack": jd2,
    "rankings_java_backend": rankings_jd1,
    "rankings_ai_fullstack": rankings_jd2,
}
(BASE_DIR / "sample_data" / "evaluation_snapshot.json").write_text(
    json.dumps(snapshot, indent=2), encoding="utf-8"
)
