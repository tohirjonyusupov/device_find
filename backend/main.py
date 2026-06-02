import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base, AsyncSessionLocal
from routes import auth, devices, subscription, payment, chat


async def _seed_admin():
    """Birinchi ishga tushishda admin avtomatik yaratiladi"""
    from sqlalchemy import select
    from models import User, Subscription, UserRole, SubscriptionPlan, SubscriptionStatus
    from auth_utils import hash_password

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "admin@deviceguard.com"))
        if existing.scalar_one_or_none():
            return  # Allaqachon bor

        admin = User(
            id=str(uuid.uuid4()),
            full_name="Admin",
            email="admin@deviceguard.com",
            password_hash=hash_password("Admin1234!"),
            role=UserRole.admin,
        )
        db.add(admin)
        await db.flush()
        db.add(Subscription(
            id=str(uuid.uuid4()),
            user_id=admin.id,
            plan=SubscriptionPlan.pro,
            status=SubscriptionStatus.active,
        ))
        await db.commit()
        print("✅ Admin yaratildi: admin@deviceguard.com / Admin1234!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_admin()
    yield


app = FastAPI(title="Device-Guard API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(devices.router,      prefix="/devices",      tags=["Devices"])
app.include_router(subscription.router, prefix="/subscription", tags=["Subscription"])
app.include_router(payment.router,      prefix="/payment",      tags=["Payment"])
app.include_router(chat.router,         prefix="/chat",         tags=["Chat"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "Device-Guard API v2.0"}
