from datetime import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from beanie import PydanticObjectId
from app.models import Requisition, ScorecardCriterion, Submission, Candidate, User
from app.auth import recruiter_or_delivery
from app.ai.jd_extractor import extract_scorecard_from_jd

router = APIRouter(prefix="/requisitions", tags=["requisitions"])

class CreateRequisitionRequest(BaseModel):
    title: str
    jd_text: str
    client_id: str

class UpdateScorecardRequest(BaseModel):
    scorecard: List[ScorecardCriterion]

async def _get_requisition_or_404(req_id: str) -> Requisition:
    req = None
    try:
        req = await Requisition.get(PydanticObjectId(req_id))
    except Exception:
        pass
    if not req:
        req = await Requisition.get(req_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found")
    return req

@router.get("", response_model=List[dict])
async def list_requisitions(current_user: User = Depends(recruiter_or_delivery)):
    reqs = await Requisition.find_all().sort("-created_at").to_list()
    results = []
    for r in reqs:
        count = await Submission.find(Submission.requisition_id == str(r.id)).count()
        results.append({
            "id": str(r.id),
            "title": r.title,
            "client_id": r.client_id,
            "status": r.status,
            "scorecard_count": len(r.scorecard),
            "candidates_count": count,
            "created_by": r.created_by,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        })
    return results

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_requisition(
    body: CreateRequisitionRequest,
    current_user: User = Depends(recruiter_or_delivery)
):
    scorecard = extract_scorecard_from_jd(body.jd_text)
    req = Requisition(
        title=body.title,
        client_id=body.client_id,
        jd_text=body.jd_text,
        scorecard=scorecard,
        status="open",
        created_by=str(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await req.insert()
    return {
        "id": str(req.id),
        "title": req.title,
        "client_id": req.client_id,
        "jd_text": req.jd_text,
        "scorecard": [c.model_dump() for c in req.scorecard],
        "status": req.status,
        "created_by": req.created_by,
        "created_at": req.created_at,
        "updated_at": req.updated_at,
    }

@router.get("/{id}")
async def get_requisition(id: str, current_user: User = Depends(recruiter_or_delivery)):
    req = await _get_requisition_or_404(id)
    return {
        "id": str(req.id),
        "title": req.title,
        "client_id": req.client_id,
        "jd_text": req.jd_text,
        "scorecard": [c.model_dump() for c in req.scorecard],
        "status": req.status,
        "created_by": req.created_by,
        "created_at": req.created_at,
        "updated_at": req.updated_at,
    }

@router.patch("/{id}/scorecard")
async def update_scorecard(
    id: str,
    body: UpdateScorecardRequest,
    current_user: User = Depends(recruiter_or_delivery)
):
    req = await _get_requisition_or_404(id)
    req.scorecard = body.scorecard
    req.updated_at = datetime.utcnow()
    await req.save()
    return {
        "id": str(req.id),
        "scorecard": [c.model_dump() for c in req.scorecard],
        "updated_at": req.updated_at,
    }

@router.get("/{id}/ranked")
async def get_ranked_candidates(
    id: str,
    current_user: User = Depends(recruiter_or_delivery)
):
    req = await _get_requisition_or_404(id)
    submissions = await Submission.find(
        Submission.requisition_id == str(req.id)
    ).sort("-ai_score").to_list()

    results = []
    for sub in submissions:
        cand = None
        try:
            cand = await Candidate.get(PydanticObjectId(sub.candidate_id))
        except Exception:
            pass
        if not cand:
            cand = await Candidate.get(sub.candidate_id)

        candidate_info = None
        if cand:
            candidate_info = {
                "id": str(cand.id),
                "full_name": cand.full_name,
                "email": cand.email,
                "phone": cand.phone,
                "current_role": cand.current_role,
                "experience_years": cand.experience_years,
                "skills": cand.skills,
                "notice_days": cand.notice_days,
                "file_name": cand.file_name,
            }

        results.append({
            "submission_id": str(sub.id),
            "requisition_id": sub.requisition_id,
            "candidate_id": sub.candidate_id,
            "client_id": sub.client_id,
            "ai_score": sub.ai_score,
            "pipeline_stage": sub.pipeline_stage.value,
            "client_decision": sub.client_decision.value,
            "recruiter_viewed": sub.recruiter_viewed,
            "submitted_at": sub.submitted_at,
            "criteria_scores": [cs.model_dump() for cs in sub.criteria_scores],
            "candidate": candidate_info,
        })

    return results
