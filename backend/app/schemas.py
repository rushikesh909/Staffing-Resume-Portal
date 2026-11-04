from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import UserRole, PipelineStage, ClientDecision

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    client_id: Optional[int] = None

class ScorecardCriteria(BaseModel):
    skills: List[str] = []
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    notice_days_max: Optional[int] = None
    ctc_max: Optional[float] = None
    location: Optional[str] = None

class RequisitionCreate(BaseModel):
    title: str
    client_id: int
    jd_text: str

class RequisitionOut(BaseModel):
    id: int
    title: str
    client_id: int
    jd_text: str
    scorecard: Optional[Dict] = None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class ScorecardUpdate(BaseModel):
    scorecard: Dict[str, Any]

class CandidateOut(BaseModel):
    id: int
    name: str
    current_role: Optional[str]
    experience_years: Optional[float]
    notice_days: Optional[int]
    skills: Optional[List[str]]
    ai_score: Optional[float]
    score_evidence: Optional[Dict]
    pipeline_stage: Optional[str]
    submitted_to_client: bool
    viewed_by_recruiter: bool
    model_config = {"from_attributes": True}

class CandidatePortalOut(BaseModel):
    id: int
    current_role: Optional[str]
    experience_years: Optional[float]
    notice_days: Optional[int]
    skills: Optional[List[str]]
    ai_score: Optional[float]
    score_evidence: Optional[Dict]
    pipeline_stage: Optional[str]
    client_decision: Optional[str]
    rejection_reason: Optional[str]
    model_config = {"from_attributes": True}

class ClientDecisionRequest(BaseModel):
    decision: ClientDecision
    rejection_reason: Optional[str] = None
    proposed_slot: Optional[str] = None

class PipelineStageUpdate(BaseModel):
    stage: PipelineStage
