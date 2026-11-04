from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import enum

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    recruiter = "recruiter"
    client_hiring_manager = "client_hiring_manager"

class PipelineStage(str, enum.Enum):
    sourced = "sourced"
    screened = "screened"
    submitted_to_client = "submitted_to_client"
    client_reviewed = "client_reviewed"
    interview_scheduled = "interview_scheduled"
    offer_made = "offer_made"
    joined = "joined"

class ClientDecision(str, enum.Enum):
    shortlisted = "shortlisted"
    rejected = "rejected"
    interview_proposed = "interview_proposed"

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact_email = Column(String(200), unique=True, nullable=False)
    users = relationship("User", back_populates="client")
    requisitions = relationship("Requisition", back_populates="client")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    client = relationship("Client", back_populates="users")

class Requisition(Base):
    __tablename__ = "requisitions"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    jd_text = Column(Text, nullable=False)
    scorecard = Column(JSON, nullable=True)   # extracted + editable
    status = Column(String(50), default="active")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    client = relationship("Client", back_populates="requisitions")
    requisition_candidates = relationship("RequisitionCandidate", back_populates="requisition")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    current_role = Column(String(200), nullable=True)
    experience_years = Column(Float, nullable=True)
    notice_days = Column(Integer, nullable=True)
    skills = Column(JSON, nullable=True)         # list of strings
    cv_path = Column(String(500), nullable=True)
    cv_text = Column(Text, nullable=True)        # parsed plaintext
    parsed_data = Column(JSON, nullable=True)    # structured fields
    fingerprint = Column(String(200), nullable=True, index=True)  # dedup key
    consent_given = Column(Boolean, default=False)
    consent_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    requisition_candidates = relationship("RequisitionCandidate", back_populates="candidate")

class RequisitionCandidate(Base):
    __tablename__ = "requisition_candidates"
    id = Column(Integer, primary_key=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    ai_score = Column(Float, nullable=True)
    score_evidence = Column(JSON, nullable=True)  # {criterion: {score, evidence_lines}}
    pipeline_stage = Column(SAEnum(PipelineStage), default=PipelineStage.sourced)
    submitted_to_client = Column(Boolean, default=False)
    viewed_by_recruiter = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    requisition = relationship("Requisition", back_populates="requisition_candidates")
    candidate = relationship("Candidate", back_populates="requisition_candidates")
    client_submissions = relationship("ClientSubmission", back_populates="requisition_candidate")

class ClientSubmission(Base):
    __tablename__ = "client_submissions"
    id = Column(Integer, primary_key=True)
    requisition_candidate_id = Column(Integer, ForeignKey("requisition_candidates.id"), nullable=False)
    client_decision = Column(SAEnum(ClientDecision), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    proposed_slot = Column(String(200), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    requisition_candidate = relationship("RequisitionCandidate", back_populates="client_submissions")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
