import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel
from database import get_db
from models import User, Device, Subscription, SubscriptionPlan, SubscriptionStatus, PaymentRequest, PaymentStatus
from auth_utils import get_current_user

router = APIRouter()

TELEGRAM_USERNAME = "@abdumuratov_m"
PRICE_UZS = 49900
PRICE_USD = 4.99
PRO_DURATION_DAYS = 30


class PaymentRequestCreate(BaseModel):
    note: str | None = None


class ReviewPayment(BaseModel):
    status: str
    admin_note: str | None = None


def _pr_dict(r: PaymentRequest, user: User | None = None) -> dict:
    d = {
        "id": r.id,
        "user_id": r.user_id,
        "amount": r.amount,
        "currency": r.currency,
        "status": r.status,
        "note": r.note,
        "admin_note": r.admin_note,
        "created_at": r.created_at.isoformat(),
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
    }
    if user:
        d["user_name"] = user.full_name
        d["user_email"] = user.email
        d["user_phone"] = user.phone
    return d


async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/info")
async def payment_info(current_user: User = Depends(get_current_user)):
    return {
        "telegram": TELEGRAM_USERNAME,
        "price_uzs": PRICE_UZS,
        "price_usd": PRICE_USD,
        "duration_days": PRO_DURATION_DAYS,
        "instructions": [
            f"1. Telegram da {TELEGRAM_USERNAME} ga xabar yuboring",
            "2. To'lov miqdori va usulini so'rang",
            "3. To'lovni amalga oshiring",
            "4. To'lov chekini (screenshot) yuboring",
            "5. Quyidagi 'To'lov qildim' tugmasini bosing va izoh qoldiring",
            "6. Admin tasdiqlagandan so'ng PRO rejim avtomatik faollashadi"
        ]
    }


@router.post("/request", status_code=201)
async def create_payment_request(
    body: PaymentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(PaymentRequest).where(
            PaymentRequest.user_id == current_user.id,
            PaymentRequest.status == PaymentStatus.pending
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Kutilayotgan so'rovingiz allaqachon bor. Admin ko'rib chiqishini kuting.")

    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = sub_result.scalar_one_or_none()
    if sub and sub.plan == SubscriptionPlan.pro and sub.status == SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="Siz allaqachon PRO rejimdasiz.")

    pr = PaymentRequest(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=PRICE_UZS,
        currency="UZS",
        note=body.note,
    )
    db.add(pr)
    await db.commit()
    await db.refresh(pr)
    return {
        "id": pr.id,
        "status": pr.status,
        "message": f"So'rovingiz qabul qilindi! Admin {TELEGRAM_USERNAME} tez orada ko'rib chiqadi.",
        "telegram": TELEGRAM_USERNAME,
        "created_at": pr.created_at.isoformat(),
    }


@router.get("/request/my")
async def my_payment_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentRequest)
        .where(PaymentRequest.user_id == current_user.id)
        .order_by(PaymentRequest.created_at.desc())
    )
    return [_pr_dict(r) for r in result.scalars().all()]


# ── ADMIN ──────────────────────────────────────────────────────────────────

@router.get("/admin/stats")
async def admin_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    pro_users   = (await db.execute(select(func.count()).select_from(Subscription).where(Subscription.plan == SubscriptionPlan.pro))).scalar()
    total_devices = (await db.execute(select(func.count()).select_from(Device))).scalar()
    pending  = (await db.execute(select(func.count()).select_from(PaymentRequest).where(PaymentRequest.status == PaymentStatus.pending))).scalar()
    approved = (await db.execute(select(func.count()).select_from(PaymentRequest).where(PaymentRequest.status == PaymentStatus.approved))).scalar()
    return {
        "total_users": total_users,
        "pro_users": pro_users,
        "free_users": total_users - pro_users,
        "total_devices": total_devices,
        "pending_payments": pending,
        "approved_payments": approved,
        "estimated_revenue_uzs": approved * PRICE_UZS,
    }


@router.get("/admin/requests")
async def admin_list_requests(
    status: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = select(PaymentRequest).order_by(PaymentRequest.created_at.desc())
    if status:
        q = q.where(PaymentRequest.status == status)
    result = await db.execute(q)
    requests = result.scalars().all()

    enriched = []
    for r in requests:
        u = (await db.execute(select(User).where(User.id == r.user_id))).scalar_one_or_none()
        enriched.append(_pr_dict(r, u))
    return enriched


@router.get("/admin/users")
async def admin_list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    out = []
    for u in users:
        sub = (await db.execute(select(Subscription).where(Subscription.user_id == u.id))).scalar_one_or_none()
        dev_count = (await db.execute(select(func.count()).select_from(Device).where(Device.owner_id == u.id))).scalar()
        out.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "plan": sub.plan if sub else "free",
            "sub_status": sub.status if sub else "none",
            "end_date": sub.end_date.isoformat() if sub and sub.end_date else None,
            "device_count": dev_count,
            "created_at": u.created_at.isoformat(),
        })
    return out


@router.post("/admin/requests/{request_id}/review")
async def admin_review(
    request_id: str,
    body: ReviewPayment,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pr = (await db.execute(select(PaymentRequest).where(PaymentRequest.id == request_id))).scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if pr.status != PaymentStatus.pending:
        raise HTTPException(status_code=400, detail="Bu so'rov allaqachon ko'rib chiqilgan")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status: 'approved' yoki 'rejected' bo'lishi kerak")

    pr.status = body.status
    pr.admin_note = body.admin_note
    pr.reviewed_at = datetime.utcnow()

    if body.status == "approved":
        sub = (await db.execute(select(Subscription).where(Subscription.user_id == pr.user_id))).scalar_one_or_none()
        if sub:
            sub.plan = SubscriptionPlan.pro
            sub.status = SubscriptionStatus.active
            sub.start_date = datetime.utcnow()
            sub.end_date = datetime.utcnow() + timedelta(days=PRO_DURATION_DAYS)

    await db.commit()
    return {"success": True, "status": pr.status}


@router.post("/admin/users/{user_id}/set-plan")
async def admin_set_plan(
    user_id: str,
    plan: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin qo'lda PRO/FREE berishi"""
    if plan not in ("pro", "free"):
        raise HTTPException(status_code=400, detail="Plan: 'pro' yoki 'free'")
    sub = (await db.execute(select(Subscription).where(Subscription.user_id == user_id))).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="User topilmadi")
    sub.plan = plan
    sub.status = SubscriptionStatus.active if plan == "pro" else SubscriptionStatus.cancelled
    if plan == "pro":
        sub.start_date = datetime.utcnow()
        sub.end_date = datetime.utcnow() + timedelta(days=PRO_DURATION_DAYS)
    await db.commit()
    return {"success": True}
