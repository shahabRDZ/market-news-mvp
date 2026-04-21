from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_access_token, current_user, hash_password, verify_password
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    plan: str


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterPayload, db: Session = Depends(get_db)) -> AuthResponse:
    if len(body.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    existing = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    u = User(email=body.email.lower(), password_hash=hash_password(body.password), plan="free")
    db.add(u)
    db.commit()
    db.refresh(u)
    return AuthResponse(token=create_access_token(u.id), user={"id": u.id, "email": u.email, "plan": u.plan})


@router.post("/login", response_model=AuthResponse)
def login(body: LoginPayload, db: Session = Depends(get_db)) -> AuthResponse:
    u = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if u is None or not verify_password(body.password, u.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not u.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return AuthResponse(token=create_access_token(u.id), user={"id": u.id, "email": u.email, "plan": u.plan})


@router.get("/me", response_model=UserResponse)
def me(u: User = Depends(current_user)) -> UserResponse:
    return UserResponse(id=u.id, email=u.email, plan=u.plan)
