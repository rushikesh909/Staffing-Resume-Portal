# Deployment Guide

## Local Development (Docker Compose)

### Prerequisites
- Docker Desktop 4.x+
- Docker Compose v2+
- Git

### Steps

1. Clone the repository:
   ```bash
   git clone <GITHUB_REPO_URL>
   cd staffing-resume-portal
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY to a random 32-byte hex string:
   # openssl rand -hex 32
   ```

3. Start services:
   ```bash
   docker compose up --build
   ```
   This starts MongoDB 7, the FastAPI backend (port 8000), and Next.js frontend (port 3000).

4. Run the seed script (in a new terminal):
   ```bash
   docker compose exec backend python scripts/seed.py
   ```

5. Open the app: http://localhost:3000

---

## Local (without Docker)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Ensure MongoDB is running locally on port 27017
cp ../.env.example ../.env  # edit as needed
uvicorn app.main:app --reload --port 8000
```

### Seed
```bash
cd backend
python scripts/seed.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

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

## Production Deployment

### Architecture
- **Backend (FastAPI)**: Deployed to [Render.com](https://render.com) free tier (Web Service, Python)
- **Database (MongoDB)**: MongoDB Atlas free tier (M0 cluster)
- **Frontend (Next.js)**: Deployed to [Vercel](https://vercel.com) (free tier)

### Environment Variables Required

#### Backend (Render / any server)
| Variable | Description |
|---|---|
| `MONGODB_URL` | MongoDB connection string (Atlas: `mongodb+srv://...`) |
| `MONGODB_DB` | Database name (`staffing_db`) |
| `SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) |
| `ALGORITHM` | JWT algorithm (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (`480`) |
| `UPLOAD_DIR` | Directory for uploaded CV files (`./uploads`) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins (e.g. `https://your-frontend.vercel.app`) |

#### Frontend (Vercel)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Full URL of the deployed backend API (e.g. `https://your-backend.onrender.com`) |

### Render Deployment Steps
1. Connect GitHub repo to Render.
2. Create a new Web Service, root directory: `backend/`.
3. Runtime: **Python 3**.
4. Build command: `pip install -r requirements.txt`.
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Set environment variables in the Render dashboard as listed above.
7. After first deploy, run seed: Use Render's Shell feature to run `python scripts/seed.py`.

### Vercel Deployment Steps
1. Import GitHub repo to Vercel.
2. Set root directory to `frontend/`.
3. Set `NEXT_PUBLIC_API_URL` environment variable to your Render backend URL.
4. Deploy.

---

## Demo Credentials

| Role | Email | Password | Client / Organization |
|---|---|---|---|
| Recruiter | `recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing |
| Senior Recruiter | `senior.recruiter@talentbridge.in` | `Recruiter@123` | TalentBridge Staffing |
| Client (TechCorp) | `hiring@techcorp.in` | `Client@123` | TechCorp Solutions |
| Client (FinServ) | `hiring@finserv.in` | `Client@123` | FinServ India |
| Delivery Head | `head@talentbridge.in` | `DeliveryHead@123` | TalentBridge Staffing |
