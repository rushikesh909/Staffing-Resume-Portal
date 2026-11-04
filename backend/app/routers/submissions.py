from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from beanie import PydanticObjectId
from app.models import Submission, Candidate, Requisition, PipelineStage, ClientDecision, User, UserRole
from app.auth import get_current_user, recruiter_only, client_only, get_client_scoped_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])
client_router = APIRouter(prefix="/client", tags=["client"])

class UpdateStageRequest(BaseModel):
    stage: PipelineStage

class ClientDecisionRequest(BaseModel):
    decision: ClientDecision
    rejection_reason: Optional[str] = None
    interview_slot: Optional[datetime] = None

async def _get_submission_or_404(submission_id: str) -> Submission:
    sub = None
    try:
        sub = await Submission.get(PydanticObjectId(submission_id))
    except Exception:
        pass
    if not sub:
        sub = await Submission.get(submission_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return sub

async def _format_submission_with_candidate(sub: Submission, is_client: bool = False):
    cand = None
    try:
        cand = await Candidate.get(PydanticObjectId(sub.candidate_id))
    except Exception:
        pass
    if not cand:
        cand = await Candidate.get(sub.candidate_id)

    cand_dict = None
    if cand:
        mask_contacts = is_client and sub.pipeline_stage not in [
            PipelineStage.interview, PipelineStage.offer, PipelineStage.joined
        ]
        cand_dict = {
            "id": str(cand.id),
            "full_name": cand.full_name,
            "email": None if mask_contacts else cand.email,
            "phone": None if mask_contacts else cand.phone,
            "current_role": cand.current_role,
            "experience_years": cand.experience_years,
            "skills": cand.skills,
            "notice_days": cand.notice_days,
            "file_name": cand.file_name,
        }

    return {
        "id": str(sub.id),
        "requisition_id": sub.requisition_id,
        "candidate_id": sub.candidate_id,
        "client_id": sub.client_id,
        "ai_score": sub.ai_score,
        "criteria_scores": [cs.model_dump() for cs in sub.criteria_scores],
        "pipeline_stage": sub.pipeline_stage.value,
        "client_decision": sub.client_decision.value,
        "rejection_reason": sub.rejection_reason,
        "interview_slot": sub.interview_slot,
        "recruiter_viewed": sub.recruiter_viewed,
        "recruiter_viewed_at": sub.recruiter_viewed_at,
        "submitted_at": sub.submitted_at,
        "updated_at": sub.updated_at,
        "candidate": cand_dict,
    }

# ==================== RECRUITER SUBMISSION ENDPOINTS ====================

@router.get("/{id}")
async def get_submission(
    id: str,
    current_user: User = Depends(get_current_user)
):
    sub = await _get_submission_or_404(id)
    if current_user.role == UserRole.client_hiring_manager:
        if sub.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        return await _format_submission_with_candidate(sub, is_client=True)

    return await _format_submission_with_candidate(sub, is_client=False)

@router.patch("/{id}/stage")
async def update_pipeline_stage(
    id: str,
    body: UpdateStageRequest,
    current_user: User = Depends(recruiter_only)
):
    sub = await _get_submission_or_404(id)
    sub.pipeline_stage = body.stage
    sub.updated_at = datetime.utcnow()
    await sub.save()
    return {
        "id": str(sub.id),
        "pipeline_stage": sub.pipeline_stage.value,
        "updated_at": sub.updated_at,
    }

@router.post("/{id}/submit-to-client")
async def submit_to_client(
    id: str,
    current_user: User = Depends(recruiter_only)
):
    sub = await _get_submission_or_404(id)
    if not sub.recruiter_viewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruiter must review candidate profile before submitting to client"
        )
    sub.pipeline_stage = PipelineStage.client_reviewed
    sub.updated_at = datetime.utcnow()
    await sub.save()
    return {
        "id": str(sub.id),
        "pipeline_stage": sub.pipeline_stage.value,
        "status": "submitted_to_client",
        "updated_at": sub.updated_at,
    }

# ==================== CLIENT SCOPED ENDPOINTS ====================

@client_router.get("/requisitions")
async def list_client_requisitions(current_user: User = Depends(client_only)):
    if not current_user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No client associated with user")
    
    reqs = await Requisition.find(
        Requisition.client_id == current_user.client_id
    ).sort("-created_at").to_list()

    return [
        {
            "id": str(r.id),
            "title": r.title,
            "client_id": r.client_id,
            "status": r.status,
            "scorecard": [c.model_dump() for c in r.scorecard],
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in reqs
    ]

@client_router.get("/requisitions/{req_id}/submissions")
async def list_client_submissions(
    req_id: str,
    current_user: User = Depends(client_only)
):
    if not current_user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No client associated with user")

    # Verify requisition belongs to this client
    req = None
    try:
        req = await Requisition.get(PydanticObjectId(req_id))
    except Exception:
        pass
    if not req:
        req = await Requisition.get(req_id)
    if not req or req.client_id != current_user.client_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found")

    submissions = await Submission.find(
        Submission.requisition_id == str(req.id),
        Submission.client_id == current_user.client_id
    ).sort("-ai_score").to_list()

    return [
        await _format_submission_with_candidate(s, is_client=True)
        for s in submissions
    ]

@client_router.patch("/submissions/{id}/decision")
async def client_decision(
    id: str,
    body: ClientDecisionRequest,
    current_user: User = Depends(client_only)
):
    # Enforces client_id match via get_client_scoped_submission
    sub = await get_client_scoped_submission(id, current_user)

    sub.client_decision = body.decision
    if body.decision == ClientDecision.rejected:
        sub.rejection_reason = body.rejection_reason
    elif body.decision == ClientDecision.interview_proposed:
        sub.interview_slot = body.interview_slot
        sub.pipeline_stage = PipelineStage.interview
    elif body.decision == ClientDecision.shortlisted:
        sub.pipeline_stage = PipelineStage.shortlisted

    sub.updated_at = datetime.utcnow()
    await sub.save()

    return {
        "id": str(sub.id),
        "client_decision": sub.client_decision.value,
        "pipeline_stage": sub.pipeline_stage.value,
        "rejection_reason": sub.rejection_reason,
        "interview_slot": sub.interview_slot,
        "updated_at": sub.updated_at,
    }
