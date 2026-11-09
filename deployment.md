# Deployment Guide

## Local Development (Standard Execution)

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- MongoDB Community Server
- Git

### 1. Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# On Windows:
.venv\Scripts\activate


# Install dependencies:
pip install -r requirements.txt

# Start backend server (runs on http://localhost:8000, docs at http://localhost:8000/docs):
uvicorn app.main:app --reload --port 8000
```

### 2. Database Seeding (Sample Data)

In a separate terminal (with `.venv` activated in `backend/`):
```bash
python scripts/seed.py
```

### 3. Frontend Setup (Next.js)

In another terminal:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs at: **http://localhost:3000***

---

## Running Tests

### Backend
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm install
npx vitest run
```

---

## Live Links & Reviewer Logins

- **Frontend App**:(Local: `http://localhost:3000`)
- **Backend API Docs**:(Local: `http://localhost:8000/docs`)



## Demo Credentials

| Role | Email | Password | Client / Organization |
|---|---|---|---|
| Recruiter | `recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing |
| Senior Recruiter | `senior.recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing |
| Client (TechCorp) | `hiring@techcorp.in` | `Client@123` | TechCorp Solutions |
| Client (FinServ) | `hiring@finserv.in` | `Client@123` | FinServ India |
| Delivery Head | `head@talentbridge.in` | `DeliveryHead@123` | TalentBridge Staffing |
