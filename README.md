# Staffing Firm AI Resume Screening Tool & Client Shortlist Portal

A purpose-built applicant screening and client collaboration portal engineered for **Company A, Noida** (120 staff, 70 recruiters, processing 300 requisitions/month across IT services and banking back-office clients).

This system replaces manual 3-minute-per-CV reading with instant, evidence-backed candidate matching, cuts screening turnaround time from 5 days to under 48 hours, and provides clients with a clean, privacy-first portal to review shortlists and schedule interviews.

---

## Live Links & Reviewer Logins

- **Frontend App**: `https://staffing-resume-portal.vercel.app` (Local: `http://localhost:3000`)
- **Backend API Docs**: `https://staffing-resume-api.onrender.com/docs` (Local: `http://localhost:8000/docs`)

### Demo Accounts for Evaluators

| Role | Email | Password | Organization | What to Test |
|---|---|---|---|---|
| **Recruiter** | `recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing | Upload resumes, edit JD scorecards, review AI evidence quotes, drag candidates across Kanban stages. |
| **Senior Recruiter** | `senior.recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing | Full agency sourcing and candidate management. |
| **Client 1 (IT Services)** | `hiring@techcorp.in` | `Client@123` | **TechCorp Solutions** | Review shortlists for Senior Java Developer (includes **Ritika Bansal `CND-91022`** and **Pooja Nair `CND-91088`**). Contact details are masked until interview proposal. |
| **Client 2 (Banking)** | `hiring@finserv.in` | `Client@123` | **FinServ India** | Review shortlists for KYC Analyst (includes **Arjun Rawat `CND-91047`**). Strictly isolated from TechCorp submissions. |
| **Delivery Head** | `head@talentbridge.in` | `DeliveryHead@123` | TalentBridge Staffing | Agency-wide metrics at `/delivery`, recruiter activity stats, and AI vs. Recruiter rank alignment audits. |

---

## Core Capabilities

1. **Deterministic JD Intake**: Extracts must-have skills, experience bounds, notice period, and CTC budget into an editable, weighted scorecard in <50ms without brittle LLM API dependencies.
2. **Bulk Resume Ingestion & OCR**: Ingests PDF and DOCX files in batches with automatic fallback to Tesseract OCR for scanned documents.
3. **Fingerprint Deduplication**: Hashes normalized candidate identifiers with SHA-256 to prevent duplicate profiles while allowing submissions across multiple requisitions.
4. **Verbatim Evidence Quotes**: Every criterion match is justified by quoting the exact sentence from the candidate's CV.
5. **Algorithmic Fairness (Blind Scoring)**: Names, emails, phones, gender indicators, age, and photos are stripped before AI evaluation. Missing a mandatory criterion caps the score at 60/100 rather than disqualifying the candidate outright.
6. **Multi-Tenant Client Portal**: Clients can view shortlisted profiles on mobile or desktop, review evidence, reject with structured reasons, or propose an interview slot (which unmasks phone and email).
7. **DPDP Act 2023 Compliance**: Built-in consent records (`purpose: "hiring"`), right to erasure endpoint (`DELETE /candidates/{id}`), and an immutable audit log tracking every candidate profile view.

---

## Quick Start (Local Runbook)

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- MongoDB running locally on port 27017

### 1. Start Backend (Terminal 1)
```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*API runs at `http://localhost:8000` (interactive documentation at `http://localhost:8000/docs`).*

### 2. Seed Database with Sample Data (Terminal 2)
```bash
cd backend
# With .venv activated:
python scripts/seed.py
```
*Seeds the 2 corporate clients, 5 demo accounts, 3 requisitions, and 25 candidate profiles (including Ritika Bansal, Arjun Rawat, and Pooja Nair).*

### 3. Start Frontend (Terminal 3)
```bash
cd frontend
npm install
npm run dev
```
*Web portal runs at: **http://localhost:3000***

---

## Running Automated Tests

### Backend Unit & Integration Tests (12 test suites)
```bash
cd backend
python -m pytest tests/ -v
```
Verifies:
- Password hashing and authentication tokens
- Deterministic JD scorecard extraction
- CV parsing and blind-text sanitization
- Criterion scoring with verbatim quotes
- Missing required criteria 60% score cap (no auto-rejection)
- SHA-256 fingerprint deduplication
- Client submission access isolation (404 boundary)
- DPDP candidate deletion & audit logging
- Requisition deletion (`DELETE /requisitions/{id}`) with cascade submission clean-up

### Frontend Component Tests
```bash
cd frontend
npm test
```

---

## Architecture & Technology Stack

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS (Crimson & Slate enterprise theme), React Query, Lucide Icons.
- **Backend**: FastAPI (Python 3.11 ASGI), Pydantic v2, Beanie ODM (asynchronous MongoDB object mapping), Motor, python-jose (JWT), passlib (bcrypt).
- **Document Processing**: `pdfplumber`, `python-docx`, `pytesseract` OCR, `pdf2image`.
- **Database**: MongoDB 7.0 (locally) / MongoDB Atlas M0 (cloud).

---

## Submission Deliverables

- `Technical-Design-Document.docx` — Complete design specification in Word format.
- `Technical-Design-Document.md` — Full technical architecture, data model, and engineering decisions.
- `deployment.md` — Step-by-step local runbook, production deployment guide, and environment variable references.
- `submission.zip` — Packaged deliverables archive (<60 KB).
