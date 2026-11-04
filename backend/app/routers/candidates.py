import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel
from beanie import PydanticObjectId
from app.config import settings
from app.models import Candidate, Requisition, Submission, AuditLog, ConsentRecord, PipelineStage, ClientDecision, User
from app.auth import recruiter_only
from app.ai.cv_parser import extract_text_from_pdf, extract_text_from_docx, extract_profile_and_blind_text
from app.ai.scorer import score_candidate

router = APIRouter(prefix="/candidates", tags=["candidates"])

MAX_FILES = 50
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload")
async def bulk_upload_cvs(
    requisition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(recruiter_only)
):
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded maximum file upload limit of {MAX_FILES}"
        )

    # Validate requisition
    req = None
    try:
        req = await Requisition.get(PydanticObjectId(requisition_id))
    except Exception:
        pass
    if not req:
        req = await Requisition.get(requisition_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found")

    results = []

    for file in files:
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ["pdf", "docx"]:
            results.append({
                "filename": filename,
                "status": "error",
                "error": f"Unsupported file type .{ext}. Only PDF and DOCX are accepted."
            })
            continue

        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": f"File exceeds maximum size of 10MB"
                })
                continue

            # Extract raw text
            if ext == "pdf":
                raw_text = extract_text_from_pdf(content)
            else:
                raw_text = extract_text_from_docx(content)

            if not raw_text or len(raw_text.strip()) < 10:
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": "Failed to extract text from document"
                })
                continue

            profile, blind_text, parse_err = extract_profile_and_blind_text(raw_text, filename)
            if parse_err:
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": parse_err
                })
                continue

            # Deduplication by fingerprint
            existing_candidate = await Candidate.find_one(
                Candidate.fingerprint == profile["fingerprint"]
            )

            if existing_candidate:
                # Check if submission already exists for this req
                existing_sub = await Submission.find_one(
                    Submission.requisition_id == str(req.id),
                    Submission.candidate_id == str(existing_candidate.id)
                )
                if existing_sub:
                    results.append({
                        "filename": filename,
                        "status": "duplicate",
                        "candidate_id": str(existing_candidate.id),
                        "submission_id": str(existing_sub.id),
                        "candidate_name": existing_candidate.full_name,
                        "message": "Candidate already submitted for this requisition"
                    })
                else:
                    # Score existing candidate for this new requisition
                    evidences, score = score_candidate(existing_candidate, req.scorecard)
                    new_sub = Submission(
                        requisition_id=str(req.id),
                        candidate_id=str(existing_candidate.id),
                        client_id=req.client_id,
                        ai_score=score,
                        criteria_scores=evidences,
                        pipeline_stage=PipelineStage.sourced,
                        client_decision=ClientDecision.pending,
                        submitted_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    await new_sub.insert()
                    results.append({
                        "filename": filename,
                        "status": "duplicate",
                        "candidate_id": str(existing_candidate.id),
                        "submission_id": str(new_sub.id),
                        "candidate_name": existing_candidate.full_name,
                        "ai_score": score,
                        "message": "Existing candidate linked to new requisition"
                    })
                continue

            # Save file to disk
            safe_filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
            save_path = os.path.join(settings.upload_dir, safe_filename)
            try:
                with open(save_path, "wb") as f:
                    f.write(content)
            except Exception:
                pass

            # Create Candidate
            candidate = Candidate(
                full_name=profile["full_name"],
                email=profile.get("email"),
                phone=profile.get("phone"),
                current_role=profile.get("current_role"),
                experience_years=profile.get("experience_years"),
                skills=profile.get("skills", []),
                notice_days=profile.get("notice_days"),
                raw_text=raw_text,
                blind_text=blind_text,
                fingerprint=profile["fingerprint"],
                consent=ConsentRecord(given=True, timestamp=datetime.utcnow(), purpose="hiring"),
                file_name=filename,
                created_at=datetime.utcnow(),
            )
            await candidate.insert()

            # Score candidate against requisition scorecard
            evidences, score = score_candidate(candidate, req.scorecard)

            # Create Submission
            submission = Submission(
                requisition_id=str(req.id),
                candidate_id=str(candidate.id),
                client_id=req.client_id,
                ai_score=score,
                criteria_scores=evidences,
                pipeline_stage=PipelineStage.sourced,
                client_decision=ClientDecision.pending,
                submitted_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await submission.insert()

            results.append({
                "filename": filename,
                "status": "success",
                "candidate_id": str(candidate.id),
                "submission_id": str(submission.id),
                "ai_score": score,
                "candidate_name": candidate.full_name
            })

        except Exception as e:
            results.append({
                "filename": filename,
                "status": "error",
                "error": str(e)
            })

    return {
        "results": results,
        "total": len(files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "duplicate": sum(1 for r in results if r["status"] == "duplicate"),
        "error": sum(1 for r in results if r["status"] == "error"),
    }

@router.get("/{id}")
async def get_candidate_profile(
    id: str,
    requisition_id: Optional[str] = Query(None),
    current_user: User = Depends(recruiter_only)
):
    candidate = None
    try:
        candidate = await Candidate.get(PydanticObjectId(id))
    except Exception:
        pass
    if not candidate:
        candidate = await Candidate.get(id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    # Record Audit Log
    audit = AuditLog(
        candidate_id=str(candidate.id),
        viewer_user_id=str(current_user.id),
        viewer_role=current_user.role.value,
        requisition_id=requisition_id,
        action="viewed",
        timestamp=datetime.utcnow()
    )
    await audit.insert()

    # Mark submission recruiter_viewed if requisition_id is passed
    if requisition_id:
        submission = await Submission.find_one(
            Submission.requisition_id == requisition_id,
            Submission.candidate_id == str(candidate.id)
        )
        if submission:
            submission.recruiter_viewed = True
            submission.recruiter_viewed_at = datetime.utcnow()
            await submission.save()

    return {
        "id": str(candidate.id),
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "current_role": candidate.current_role,
        "experience_years": candidate.experience_years,
        "skills": candidate.skills,
        "notice_days": candidate.notice_days,
        "fingerprint": candidate.fingerprint,
        "consent": candidate.consent.model_dump(),
        "file_name": candidate.file_name,
        "created_at": candidate.created_at,
        "raw_text": candidate.raw_text,
    }

class UpdateConsentRequest(BaseModel):
    given: bool
    purpose: Optional[str] = "hiring"

@router.get("/{id}/consent")
async def get_candidate_consent(
    id: str,
    current_user: User = Depends(recruiter_only)
):
    candidate = None
    try:
        candidate = await Candidate.get(PydanticObjectId(id))
    except Exception:
        pass
    if not candidate:
        candidate = await Candidate.get(id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return {
        "candidate_id": str(candidate.id),
        "consent": candidate.consent.model_dump(),
    }

@router.patch("/{id}/consent")
async def update_candidate_consent(
    id: str,
    body: UpdateConsentRequest,
    current_user: User = Depends(recruiter_only)
):
    candidate = None
    try:
        candidate = await Candidate.get(PydanticObjectId(id))
    except Exception:
        pass
    if not candidate:
        candidate = await Candidate.get(id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    candidate.consent.given = body.given
    candidate.consent.timestamp = datetime.utcnow()
    if body.purpose:
        candidate.consent.purpose = body.purpose
    await candidate.save()

    audit = AuditLog(
        candidate_id=str(candidate.id),
        viewer_user_id=str(current_user.id),
        viewer_role=current_user.role.value,
        action="consent_updated",
        timestamp=datetime.utcnow()
    )
    await audit.insert()

    return {
        "candidate_id": str(candidate.id),
        "consent": candidate.consent.model_dump(),
    }

@router.get("/{id}/audit-logs")
async def get_candidate_audit_logs(
    id: str,
    current_user: User = Depends(recruiter_only)
):
    candidate = None
    try:
        candidate = await Candidate.get(PydanticObjectId(id))
    except Exception:
        pass
    if not candidate:
        candidate = await Candidate.get(id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    logs = await AuditLog.find(
        AuditLog.candidate_id == str(candidate.id)
    ).sort("-timestamp").to_list()

    return [
        {
            "id": str(log.id),
            "candidate_id": log.candidate_id,
            "viewer_user_id": log.viewer_user_id,
            "viewer_role": log.viewer_role,
            "requisition_id": log.requisition_id,
            "action": log.action,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]

@router.delete("/{id}")
async def delete_candidate(
    id: str,
    current_user: User = Depends(recruiter_only)
):
    candidate = None
    try:
        candidate = await Candidate.get(PydanticObjectId(id))
    except Exception:
        pass
    if not candidate:
        candidate = await Candidate.get(id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    cand_id_str = str(candidate.id)
    await Submission.find(Submission.candidate_id == cand_id_str).delete()
    await AuditLog.find(AuditLog.candidate_id == cand_id_str).delete()
    await candidate.delete()
    return {"message": "Candidate and associated data deleted successfully"}

