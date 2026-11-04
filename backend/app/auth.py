from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from beanie import PydanticObjectId
from app.config import settings
from app.models import User, UserRole, Submission

bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_token(user_id: str, role: str, client_id: Optional[str] = None) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "client_id": client_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = None
    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        pass
    if not user:
        user = await User.get(user_id)
        
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

def require_role(*roles: UserRole):
    async def guard(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return guard

recruiter_only = require_role(UserRole.recruiter)
client_only = require_role(UserRole.client_hiring_manager)
delivery_head_only = require_role(UserRole.delivery_head)
recruiter_or_delivery = require_role(UserRole.recruiter, UserRole.delivery_head)
any_authenticated = require_role(UserRole.recruiter, UserRole.client_hiring_manager, UserRole.delivery_head)

async def get_client_scoped_submission(submission_id: str, current_user: User) -> Submission:
    if not current_user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no associated client")
    
    submission = None
    try:
        obj_id = PydanticObjectId(submission_id)
        submission = await Submission.find_one(
            Submission.id == obj_id,
            Submission.client_id == current_user.client_id
        )
    except Exception:
        pass
    if not submission:
        submission = await Submission.find_one(
            Submission.id == submission_id,
            Submission.client_id == current_user.client_id
        )
        
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return submission
