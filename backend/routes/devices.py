import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User, Device, DeviceCategory, DeviceStatus, Subscription, SubscriptionPlan
from backend.auth_utils import get_current_user

router = APIRouter()
FREE_LIMIT = 3
PRO_LIMIT  = 10


class DeviceCreate(BaseModel):
    name: str
    brand: str
    model: str
    category: DeviceCategory
    serial_number: str
    imei: str | None = None
    color: str | None = None
    description: str | None = None
    purchase_date: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    model: str | None = None
    category: DeviceCategory | None = None
    color: str | None = None
    description: str | None = None
    last_location: str | None = None
    reward: int | None = None
    purchase_date: str | None = None


class StatusUpdate(BaseModel):
    status: DeviceStatus
    last_location: str | None = None
    reward: int | None = None


def device_to_dict(d: Device) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "brand": d.brand,
        "model": d.model,
        "category": d.category,
        "serial_number": d.serial_number,
        "imei": d.imei,
        "status": d.status,
        "color": d.color,
        "description": d.description,
        "purchase_date": d.purchase_date,
        "last_location": d.last_location,
        "reward": d.reward,
        "date_added": d.date_added.isoformat(),
        "date_lost": d.date_lost.isoformat() if d.date_lost else None,
        "date_found": d.date_found.isoformat() if d.date_found else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


async def get_user_plan(user_id: str, db: AsyncSession) -> str:
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    sub = result.scalar_one_or_none()
    return sub.plan if sub else SubscriptionPlan.free


@router.get("")
async def list_devices(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.owner_id == current_user.id).order_by(Device.date_added.desc()))
    return [device_to_dict(d) for d in result.scalars().all()]


@router.get("/public/lost")
async def public_lost_devices(db: AsyncSession = Depends(get_db)):
    """Barcha yo'qolgan qurilmalar — login siz ko'rish mumkin"""
    result = await db.execute(
        select(Device, User)
        .join(User, Device.owner_id == User.id)
        .where(Device.status == DeviceStatus.lost)
        .order_by(Device.date_lost.desc())
    )
    rows = result.all()
    return [{
        "id": d.id,
        "name": d.name,
        "brand": d.brand,
        "model": d.model,
        "category": d.category,
        "serial_number": d.serial_number[:4] + "****" + d.serial_number[-2:] if len(d.serial_number) > 6 else "****",
        "color": d.color,
        "description": d.description,
        "last_location": d.last_location,
        "reward": d.reward,
        "date_lost": d.date_lost.isoformat() if d.date_lost else None,
        "owner_id": u.id,
        "owner_name": u.full_name,
    } for d, u in rows]


@router.get("/public/search")
async def public_search(q: str, db: AsyncSession = Depends(get_db)):
    """Login siz qurilma qidirish (serial yoki IMEI)"""
    if len(q) < 4:
        raise HTTPException(status_code=400, detail="Kamida 4 ta belgi kiriting")
    result = await db.execute(
        select(Device).where(
            (Device.serial_number.ilike(f"%{q}%")) | (Device.imei.ilike(f"%{q}%"))
        ).limit(5)
    )
    devices = result.scalars().all()
    return [{
        "name": d.name, "brand": d.brand, "model": d.model,
        "category": d.category, "status": d.status,
        "serial_number": d.serial_number[:6] + "****",
        "reward": d.reward if d.status == "lost" else None,
        "last_location": d.last_location if d.status == "lost" else None,
    } for d in devices]


@router.post("", status_code=201)
async def create_device(
    body: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin":
        plan = await get_user_plan(current_user.id, db)
        limit = PRO_LIMIT if plan == SubscriptionPlan.pro else FREE_LIMIT
        count_result = await db.execute(select(func.count()).where(Device.owner_id == current_user.id))
        count = count_result.scalar()
        if count >= limit:
            raise HTTPException(
                status_code=403,
                detail={"error": "LIMIT_REACHED", "message": "Device limit reached", "count": count, "limit": limit, "plan": plan}
            )

    existing = await db.execute(select(Device).where(Device.serial_number == body.serial_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Serial number already registered")

    device = Device(
        id=str(uuid.uuid4()), owner_id=current_user.id,
        name=body.name, brand=body.brand, model=body.model,
        category=body.category, serial_number=body.serial_number,
        imei=body.imei, color=body.color, description=body.description,
        purchase_date=body.purchase_date,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device_to_dict(device)


@router.put("/{device_id}")
async def update_device(
    device_id: str, body: DeviceUpdate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == current_user.id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    device.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(device)
    return device_to_dict(device)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == current_user.id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()


@router.get("/{device_id}")
async def get_device(
    device_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == current_user.id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_to_dict(device)


@router.patch("/{device_id}/status")
async def update_status(
    device_id: str, body: StatusUpdate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Device).where(Device.id == device_id, Device.owner_id == current_user.id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.status = body.status
    device.updated_at = datetime.utcnow()
    if body.status == DeviceStatus.lost:
        device.date_lost = datetime.utcnow()
        if body.last_location: device.last_location = body.last_location
        if body.reward is not None: device.reward = body.reward
    elif body.status == DeviceStatus.found:
        device.date_found = datetime.utcnow()
    elif body.status == DeviceStatus.active:
        device.date_lost = None
        device.date_found = None
    await db.commit()
    await db.refresh(device)
    return device_to_dict(device)
