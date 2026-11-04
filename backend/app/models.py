from enum import Enum
from datetime import datetime
from typing import Optional, List, Any
from beanie import Document, Indexed
from pydantic import BaseModel, Field, EmailStr
import pymongo

class UserRole(str, Enum):
    recruiter = "recruiter"
    client_hiring_manager = "client_hiring_manager"
    delivery_head = "delivery_head"

class PipelineStage(str, Enum):
    sourced = "sourced"
    screened = "screened"
    shortlisted = "shortlisted"
    client_reviewed = "client_reviewed"
    interview = "interview"
    offer = "offer"
    joined = "joined"

class ClientDecision(str, Enum):
    pending = "pending"
    shortlisted = "shortlisted"
    rejected = "rejected"
    interview_proposed = "interview_proposed"

# Embedded models (not Documents)
class ScorecardCriterion(BaseModel):
    name: str
    type: str  # "skill", "experience", "ctc", "notice", "other"
    weight: float = 1.0
    required: bool = False

class CriterionEvidence(BaseModel):
    criterion_name: str
    score: float  # 0.0–1.0
    evidence_quotes: List[str]  # actual quoted lines from CV
    matched: bool

class ConsentRecord(BaseModel):
    given: bool = False
    timestamp: Optional[datetime] = None
    purpose: str = "hiring"

# Beanie Documents
class User(Document):
    email: Indexed(str, unique=True)
    hashed_password: str
    full_name: str
    role: UserRole
    client_id: Optional[str] = None  # only for client_hiring_manager
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

class Client(Document):
    name: str
    contact_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "clients"

class Requisition(Document):
    title: str
    client_id: str
    jd_text: str
    scorecard: List[ScorecardCriterion] = []
    status: str = "open"  # open, closed, on_hold
    created_by: str  # user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "requisitions"

class Candidate(Document):
    # Stored for display - NOT fed to scoring
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    experience_years: Optional[float] = None
    skills: List[str] = []
    notice_days: Optional[int] = None
    # Scoring uses this (protected attributes stripped)
    raw_text: str  # full extracted CV text
    blind_text: str  # raw_text with name/gender/age/marital stripped for scoring
    parse_error: Optional[str] = None
    fingerprint: Indexed(str, unique=True)  # sha256(normalized email+phone or name+role)
    consent: ConsentRecord = Field(default_factory=ConsentRecord)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_name: str = ""

    class Settings:
        name = "candidates"

class Submission(Document):
    requisition_id: str
    candidate_id: str
    client_id: str
    ai_score: float = 0.0  # 0.0–100.0
    criteria_scores: List[CriterionEvidence] = []
    pipeline_stage: PipelineStage = PipelineStage.sourced
    client_decision: ClientDecision = ClientDecision.pending
    rejection_reason: Optional[str] = None
    interview_slot: Optional[datetime] = None
    recruiter_viewed: bool = False
    recruiter_viewed_at: Optional[datetime] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "submissions"
        indexes = [
            pymongo.IndexModel(
                [("requisition_id", pymongo.ASCENDING), ("ai_score", pymongo.DESCENDING)],
                name="req_score_idx"
            ),
            pymongo.IndexModel([("client_id", pymongo.ASCENDING)], name="client_idx"),
            pymongo.IndexModel(
                [("requisition_id", pymongo.ASCENDING), ("candidate_id", pymongo.ASCENDING)],
                unique=True, name="req_candidate_unique"
            ),
        ]

class AuditLog(Document):
    candidate_id: str
    viewer_user_id: str
    viewer_role: str
    requisition_id: Optional[str] = None
    action: str = "viewed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "audit_logs"
