from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, Device, Subscription, SubscriptionPlan
from auth_utils import get_current_user

router = APIRouter()
FREE_LIMIT = 3
PRO_LIMIT  = 10


@router.get("")
async def get_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = (await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))).scalar_one_or_none()
    count = (await db.execute(select(func.count()).where(Device.owner_id == current_user.id))).scalar()
    plan = sub.plan if sub else SubscriptionPlan.free
    is_admin = current_user.role == "admin"
    limit = None if is_admin else (PRO_LIMIT if plan == SubscriptionPlan.pro else FREE_LIMIT)

    return {
        "plan": plan,
        "status": sub.status if sub else "active",
        "start_date": sub.start_date.isoformat() if sub else None,
        "end_date": sub.end_date.isoformat() if sub and sub.end_date else None,
        "device_count": count,
        "device_limit": limit,
        "free_limit": FREE_LIMIT,
        "pro_limit": PRO_LIMIT,
        "can_add": limit is None or count < limit,
        "is_admin": is_admin,
    }
