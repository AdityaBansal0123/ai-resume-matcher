# AI-Based Resume Matching & Candidate Ranking System

**Author:** Aditya Bansal  
**Assignment:** Practical Development Assignment — AI / Full Stack Developer Intern  
**Stack:** Python 3.11+, FastAPI, React.js (Tailwind CSS), Sentence Transformers (`all-MiniLM-L6-v2`), `pypdf`, `python-docx`, SQLAlchemy (PostgreSQL / SQLite)

---

## 1. Overview & Key Functionalities Implemented

This application compares multiple candidate resumes against a target Job Description (JD) using a **Hybrid Semantic Matching & Ranking Engine** and provides full candidate-level explainability.

| Module | Requirement | Implementation Details |
| :--- | :--- | :--- |
| **Module 1: Job Description Input** | Paste or upload a JD; extract requirements, skills, experience, and qualifications | `backend/services/parser.py` (`parse_job_description`) extracts normalized technical skills across 31 canonical categories, minimum required years of experience, and degree requirements. |
| **Module 2: Batch Resume Upload** | Upload 10+ resumes in one batch; support PDF and DOCX formats; extract candidate details | Multi-file upload endpoint (`POST /api/resumes/evaluate`) and pre-packaged batch loader (`POST /api/demo/load-sample-batch`) with **12 synthetic resumes** (6 `.pdf` + 6 `.docx`) in `sample_data/resumes/`. |
| **Module 3: AI Resume Matching** | Generate 0–100 score; identify matched & missing skills; evaluate experience; use semantic similarity | `backend/services/matcher.py` (`ResumeMatcherEngine`) combines exact skill matching, `all-MiniLM-L6-v2` / domain semantic skill similarity (threshold `>= 0.72`), contextual work-experience cosine similarity, and experience duration alignment. |
| **Module 4: Candidate Ranking Dashboard** | Sortable table showing Candidate, Experience, Match %, and Matched Skills | Interactive dark-slate dashboard sorting candidates by `Match %` (or Experience/Name), with filter search, format badges (`PDF`/`DOCX`), and skill pills. |
| **Module 5: Candidate-Level Analysis** | Click a candidate to inspect extracted details, overall score, matched/missing skills, experience comparison, and reasons | Slide-over detail panel displaying the 4-component score breakdown bars, exact vs. semantic skill matches (e.g., `PostgreSQL (via SQL, 91%)`), missing skills, experience comparison, and natural-language explanations. |

---

## 2. System Architecture

1. **Ingestion & Document Parsing Layer (`backend/services/parser.py`):**
   - Extracts raw text from `.pdf` files using `pypdf` and from `.docx` files using `python-docx` (including embedded table cells).
   - Uses regex and interval-merging algorithms to compute non-overlapping years of work experience (`2021 - 2026` or explicit `5 years` headers) and extract candidate contact metadata (Name, Email, Phone, Education).
2. **AI / NLP Semantic Matching Layer (`backend/services/matcher.py`):**
   - Encodes JD requirements and candidate experience using `SentenceTransformer('all-MiniLM-L6-v2')` alongside a curated technical domain equivalence graph so synonyms and adjacent technologies (such as `PostgreSQL` ~ `SQL`, `Docker` ~ `Kubernetes`, `AWS` ~ `GCP`, `FastAPI` ~ `Flask`) are recognized even when exact keywords differ.
3. **Persistence Layer (`backend/database.py`):**
   - Uses SQLAlchemy ORM compatible with **PostgreSQL** (`DATABASE_URL=postgresql://...`) and defaults to zero-configuration local **SQLite** (`sqlite:///./resume_matcher.db`) so reviewers can run the entire stack immediately without database setup friction.
4. **Frontend Presentation Layer (`frontend/`):**
   - Built with React 18, Vite, and Tailwind CSS featuring live JD parsing, drag-and-drop batch resume upload, sortable ranking table, and interactive candidate drill-down analysis.

---

## 3. Mathematical Matching Algorithm & Scoring Methodology

To ensure the 0–100 score is **accurate, deterministic, and explainable** during technical discussions, the system computes a weighted linear combination of four normalized sub-scores:

```
Overall Match Score (0 - 100) = round( 100 * (
    0.40 * S_skills +
    0.30 * S_semantic +
    0.20 * S_experience +
    0.10 * S_education
) )
```

### Component 1: Hybrid Exact + Semantic Skill Coverage (`S_skills`, Weight = 40%)
Given the set of required JD skills $R = \{r_1, r_2, \dots, r_m\}$ and candidate resume skills $C = \{c_1, c_2, \dots, c_n\}$:
- **Exact Match (`1.0` point):** If $r_i \in C$ (after alias normalization, e.g., `Postgres` -> `PostgreSQL`, `K8s` -> `Kubernetes`), $r_i$ receives full credit (`1.0`).
- **Semantic Match (`sim` points, where `0.72 <= sim < 1.0`):** If $r_i \notin C$, we compute cosine similarity between $r_i$ and every candidate skill $c_j \in C$. If the highest similarity $\max_{c_j} \cos(e_{r_i}, e_{c_j}) \ge 0.72$, the skill is marked as a **Semantic Match** (for example, JD requires `Docker` and candidate has `Kubernetes` with `0.86` similarity) and contributes `0.86` points.
- **Missing Skill (`0.0` points):** If no candidate skill reaches the `0.72` semantic threshold, $r_i$ is classified under `missing_skills`.
- **Formula:** $S_{\text{skills}} = \frac{1}{|R|} \sum_{i=1}^{|R|} \text{score}(r_i, C)$.

### Component 2: Contextual Experience & Project Similarity (`S_semantic`, Weight = 30%)
Keyword matching alone fails when two candidates list the same skill tag but one has built production distributed systems while the other only took an introductory course. We isolate the **Work Experience & Projects** text block from the resume and compute its normalized cosine similarity against the **Role Responsibilities** text of the JD, blended (`0.65 * cos_sim + 0.35 * S_skills`) to keep the contextual score grounded.

### Component 3: Experience Duration Alignment (`S_experience`, Weight = 20%)
Compares the candidate's merged non-overlapping years of experience ($Y_{\text{cand}}$) against the minimum years required by the JD ($Y_{\text{req}}$):
- If $Y_{\text{req}} = 0$ or $Y_{\text{cand}} \ge Y_{\text{req}}$, then $S_{\text{experience}} = 1.0$.
- If $Y_{\text{cand}} < Y_{\text{req}}$, the score scales proportionally: $S_{\text{experience}} = \frac{Y_{\text{cand}}}{Y_{\text{req}}}$.

### Component 4: Qualification & Education Fit (`S_education`, Weight = 10%)
Evaluates whether the candidate holds a matching STEM degree (`B.Tech`, `B.E.`, `M.Tech`, `MCA`, `B.Sc`): `1.0` if verified, `0.5` otherwise.

---

## 4. Benchmark Output on the Included 12 Synthetic Resumes

When evaluated against `sample_data/sample_jd_java_backend.txt` (*Senior Java & Microservices Backend Engineer — 4+ years, Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, Docker, AWS*), the engine produces the following ranked leaderboard:

| Rank | Candidate | Format | Experience | Match % | Exact Skills | Semantic Skills | Missing Skills |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **Aarav Mehta** | PDF | 5 yrs | **96%** | Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, Docker, AWS | None | None |
| **#2** | **Priya Nair** | DOCX | 4.5 yrs | **93%** | Java, Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, Docker | AWS (~Kubernetes, 80%) | None |
| **#3** | **Rohan Kulkarni** | PDF | 4 yrs | **92%** | Java, Spring Boot, SQL, REST APIs, Hibernate, Kafka, Kubernetes, GCP | PostgreSQL (~SQL, 91%), Docker (~Kubernetes, 86%), AWS (~GCP, 87%) | None |
| **#4** | **Sneha Iyer** | DOCX | 3.5 yrs | **90%** | Java, Spring Boot, SQL, PostgreSQL, REST APIs, Docker | Microservices (~Spring Boot, 80%), AWS (~Docker, 76%) | None |
| **#5** | **Karthik Subramanian** | PDF | 4 yrs | **89%** | Java, SQL, PostgreSQL, REST APIs, AWS | Spring Boot (~Java, 78%), Microservices (~REST APIs, 84%), Docker (~AWS, 76%) | None |
| **#6** | **Vikram Deshmukh** | PDF | 5 yrs | **88%** | SQL, PostgreSQL, Microservices, REST APIs, Docker, AWS | Spring Boot (~FastAPI, 74%) | Java |
| **#7** | **Neha Kapoor** | DOCX | 3.5 yrs | **80%** | REST APIs, Docker, AWS | Spring Boot (~REST APIs, 76%), SQL (~MongoDB, 73%), PostgreSQL (~MongoDB, 75%), Microservices (~REST APIs, 84%) | Java |
| **#8** | **Ananya Chatterjee** | DOCX | 3 yrs | **75%** | Java, Spring Boot, SQL, REST APIs | PostgreSQL (~SQL, 91%), Microservices (~REST APIs, 84%) | Docker, AWS |
| **#9** | **Meera Krishnan** | DOCX | 2.5 yrs | **73%** | SQL, PostgreSQL, REST APIs, Docker, AWS | Spring Boot (~FastAPI, 74%), Microservices (~REST APIs, 84%) | Java |
| **#10** | **Siddharth Verma** | PDF | 2 yrs | **65%** | Java, Spring Boot, SQL | PostgreSQL (~SQL, 91%), Microservices (~Spring Boot, 80%), REST APIs (~Spring Boot, 78%) | Docker, AWS |
| **#11** | **Arjun Malhotra** | PDF | 4 yrs | **52%** | SQL, PostgreSQL | None | Java, Spring Boot, Microservices, REST APIs, Docker, AWS |
| **#12** | **Divya Banerjee** | DOCX | 1.5 yrs | **22%** | None | Java (~TypeScript, 72%) | Spring Boot, SQL, PostgreSQL, Microservices, REST APIs, Docker, AWS |

---

## 5. Quick Start & Local Setup Instructions

### Option A: Local Python + Node Setup (Recommended for Rapid Review)

**1. Start the FastAPI Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
The API and interactive Swagger documentation will be live at `http://localhost:8000/docs`.

**2. Start the React Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. Click **"Load 12 Synthetic Resumes (Sample Batch)"** to test the pre-packaged 12 PDF/DOCX resumes immediately, or upload any `.pdf` / `.docx` files from `sample_data/resumes/`.

### Option B: Docker Compose (PostgreSQL + Backend + Frontend)
```bash
docker-compose up --build
```

### Re-generating the Synthetic Resume Dataset
To regenerate all 12 `.pdf` and `.docx` resumes in `sample_data/resumes/`:
```bash
python3 scripts/generate_sample_resumes.py
```
