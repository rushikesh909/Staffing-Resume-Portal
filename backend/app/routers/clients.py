from typing import List
from fastapi import APIRouter, Depends
from app.models import Client, User
from app.auth import recruiter_or_delivery

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("", response_model=List[dict])
async def list_clients(current_user: User = Depends(recruiter_or_delivery)):
    clients = await Client.find_all().sort("name").to_list()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "contact_email": c.contact_email,
        }
        for c in clients
    ]
