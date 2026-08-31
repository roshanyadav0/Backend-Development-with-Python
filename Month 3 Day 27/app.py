from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

async def safe_commit(db: AsyncSession, conflict_message: str = "Conflicts with existing data"):
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=conflict_message)


async def create_member(db: AsyncSession, payload: MemberCreate) -> Member:
    member = Member(name=payload.name, email=payload.email, joined_date=date.today())
    db.add(member)
    await safe_commit(db, "A member with this email already exists")
    await db.refresh(member)
    return member


from pymongo.errors import DuplicateKeyError

async def log_event_safely(mongo_db, event: dict):
    try:
        await mongo_db["borrow_log"].insert_one(event)
    except DuplicateKeyError:
        # someone already logged this exact event — treat as success, not failure
        pass


from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # base connections kept open and ready
    max_overflow=5,      # extra temporary connections allowed under load
    pool_timeout=30,     # seconds to wait for a connection before raising
    pool_recycle=1800,   # recycle connections older than this (seconds) — avoids stale connections
)



from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    MONGO_URL,
    maxPoolSize=100,   # default is 100
    minPoolSize=0,     # default is 0 — connections open lazily, on demand
)


client = AsyncIOMotorClient(MONGO_URL, maxPoolSize=100, waitQueueTimeoutMS=5000)


import asyncio
from sqlalchemy.exc import OperationalError, DBAPIError

async def with_retry(coro_fn, *args, max_attempts=3, base_delay=0.5, **kwargs):
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except (OperationalError, DBAPIError) as e:
            if attempt == max_attempts:
                raise
            wait = base_delay * (2 ** (attempt - 1))   # exponential backoff: 0.5s, 1s, 2s
            await asyncio.sleep(wait)



async def create_borrow_with_retry(db: AsyncSession, member_id: int, book_id: int):
    return await with_retry(crud.create_borrow, db, member_id, book_id)



