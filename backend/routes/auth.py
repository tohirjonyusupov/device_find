import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from database import get_db
from models import User, Subscription, SubscriptionPlan, SubscriptionStatus
from auth_utils import hash_password, verify_password, create_token, get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def user_response(user: User, token: str | None = None):
    data = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
        "plan": user.subscription.plan if user.subscription else "free",
    }
    if token:
        data["token"] = token
    return data


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    sub = Subscription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        plan=SubscriptionPlan.free,
        status=SubscriptionStatus.active,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(user)
    await db.refresh(sub)
    user.subscription = sub

    token = create_token(user.id)
    return user_response(user, token)


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # load subscription
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    user.subscription = sub_result.scalar_one_or_none()

    token = create_token(user.id)
    return user_response(user, token)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    current_user.subscription = sub_result.scalar_one_or_none()
    return user_response(current_user)


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name: current_user.full_name = body.full_name
    if body.phone is not None: current_user.phone = body.phone
    await db.commit()
    await db.refresh(current_user)
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    current_user.subscription = sub_result.scalar_one_or_none()
    return user_response(current_user)


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"success": True, "message": "Password changed successfully"}
