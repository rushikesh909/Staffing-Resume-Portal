import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth as auth_router
from app.config import settings

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Staffing Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
