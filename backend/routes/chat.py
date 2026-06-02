import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pydantic import BaseModel
from database import get_db
from models import User, Device, DeviceStatus, ChatRoom, ChatMessage
from auth_utils import get_current_user

router = APIRouter()


class SendMessage(BaseModel):
    content: str


def room_dict(room: ChatRoom, current_user_id: str, unread: int = 0, last_msg: ChatMessage | None = None) -> dict:
    return {
        "id": room.id,
        "device_id": room.device_id,
        "device_name": room.device.name if room.device else "—",
        "device_brand": room.device.brand if room.device else "",
        "device_category": room.device.category if room.device else "",
        "owner_id": room.owner_id,
        "owner_name": room.owner.full_name if room.owner else "—",
        "finder_id": room.finder_id,
        "finder_name": room.finder.full_name if room.finder else "—",
        "is_owner": room.owner_id == current_user_id,
        "other_name": room.finder.full_name if room.owner_id == current_user_id else room.owner.full_name,
        "created_at": room.created_at.isoformat(),
        "last_message_at": room.last_message_at.isoformat(),
        "unread": unread,
        "last_message": last_msg.content if last_msg else None,
    }


def msg_dict(m: ChatMessage) -> dict:
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "sender_name": m.sender.full_name if m.sender else "—",
        "content": m.content,
        "is_read": m.is_read,
        "created_at": m.created_at.isoformat(),
    }


@router.post("/rooms", status_code=201)
async def create_or_get_room(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat xonasini yaratish yoki mavjudini qaytarish"""
    device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Qurilma topilmadi")
    if device.status != DeviceStatus.lost:
        raise HTTPException(status_code=400, detail="Bu qurilma yo'qolgan emas")
    if device.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="O'z qurilmangiz bilan chat ocholmaysiz")

    existing = (await db.execute(
        select(ChatRoom).where(
            and_(ChatRoom.device_id == device_id, ChatRoom.finder_id == current_user.id)
        )
    )).scalar_one_or_none()

    if existing:
        return {"room_id": existing.id, "existing": True}

    room = ChatRoom(
        id=str(uuid.uuid4()),
        device_id=device_id,
        owner_id=device.owner_id,
        finder_id=current_user.id,
    )
    db.add(room)
    await db.commit()
    return {"room_id": room.id, "existing": False}


@router.get("/rooms")
async def list_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mening barcha chat xonalarim"""
    result = await db.execute(
        select(ChatRoom).where(
            or_(ChatRoom.owner_id == current_user.id, ChatRoom.finder_id == current_user.id)
        ).order_by(ChatRoom.last_message_at.desc())
    )
    rooms = result.scalars().all()

    out = []
    for r in rooms:
        # eager load relations
        await db.refresh(r, ["device", "owner", "finder"])
        unread = len([m for m in r.messages if not m.is_read and m.sender_id != current_user.id])
        last_msg = sorted(r.messages, key=lambda m: m.created_at)[-1] if r.messages else None
        out.append(room_dict(r, current_user.id, unread, last_msg))
    return out


@router.get("/rooms/{room_id}")
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = (await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    if room.owner_id != current_user.id and room.finder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
    await db.refresh(room, ["device", "owner", "finder"])
    return room_dict(room, current_user.id)


@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = (await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    if room.owner_id != current_user.id and room.finder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    result = await db.execute(
        select(ChatMessage).where(ChatMessage.room_id == room_id).order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    # O'qilmagan xabarlarni o'qilgan deb belgilash
    for m in messages:
        if not m.is_read and m.sender_id != current_user.id:
            m.is_read = True
    await db.commit()

    # Sender ma'lumotlarini yuklash
    for m in messages:
        await db.refresh(m, ["sender"])

    return [msg_dict(m) for m in messages]


@router.post("/rooms/{room_id}/messages", status_code=201)
async def send_message(
    room_id: str,
    body: SendMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Xabar bo'sh bo'lmasligi kerak")

    room = (await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Chat topilmadi")
    if room.owner_id != current_user.id and room.finder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    msg = ChatMessage(
        id=str(uuid.uuid4()),
        room_id=room_id,
        sender_id=current_user.id,
        content=body.content.strip(),
    )
    room.last_message_at = datetime.utcnow()
    db.add(msg)
    await db.commit()
    await db.refresh(msg, ["sender"])
    return msg_dict(msg)


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """O'qilmagan xabarlar soni"""
    result = await db.execute(
        select(ChatMessage)
        .join(ChatRoom, ChatMessage.room_id == ChatRoom.id)
        .where(
            or_(ChatRoom.owner_id == current_user.id, ChatRoom.finder_id == current_user.id),
            ChatMessage.sender_id != current_user.id,
            ChatMessage.is_read == False
        )
    )
    return {"count": len(result.scalars().all())}
