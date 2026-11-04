from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models import User, Client, Requisition, Candidate, Submission, AuditLog

async def init_db(database_url: str | None = None, database_name: str | None = None):
    url = database_url or settings.mongodb_url
    db_name = database_name or settings.mongodb_db
    client = AsyncIOMotorClient(url)
    await init_beanie(
        database=client[db_name],
        document_models=[User, Client, Requisition, Candidate, Submission, AuditLog]
    )
    return client
