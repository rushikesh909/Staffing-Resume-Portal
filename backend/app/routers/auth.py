from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.models import User
from app.auth import verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    client_id: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    user = await User.find_one(User.email == body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    token = create_token(str(user.id), user.role.value, user.client_id)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            client_id=user.client_id,
        )
    )

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        client_id=current_user.client_id,
    )
