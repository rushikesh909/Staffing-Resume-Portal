from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId
from app.models import Submission, Requisition, PipelineStage, User, UserRole
from app.auth import get_current_user

router = APIRouter(prefix="/requisitions", tags=["pipeline"])

@router.get("/{id}/pipeline")
async def get_requisition_pipeline(
    id: str,
    current_user: User = Depends(get_current_user)
):
    req = None
    try:
        req = await Requisition.get(PydanticObjectId(id))
    except Exception:
        pass
    if not req:
        req = await Requisition.get(id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found")

    # If client user, ensure requisition belongs to client
    if current_user.role == UserRole.client_hiring_manager:
        if req.client_id != current_user.client_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisition not found")

    # Initialize count for all stages
    stage_counts: Dict[str, int] = {stage.value: 0 for stage in PipelineStage}

    submissions = await Submission.find(
        Submission.requisition_id == str(req.id)
    ).to_list()

    for sub in submissions:
        stage_val = sub.pipeline_stage.value if hasattr(sub.pipeline_stage, "value") else str(sub.pipeline_stage)
        if stage_val in stage_counts:
            stage_counts[stage_val] += 1
        else:
            stage_counts[stage_val] = 1

    return {
        "requisition_id": str(req.id),
        "total_submissions": len(submissions),
        "stages": stage_counts,
    }
