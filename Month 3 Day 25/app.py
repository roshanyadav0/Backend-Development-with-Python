# database.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient

# --- Postgres ---
DATABASE_URL = os.environ["DATABASE_URL"]
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- MongoDB ---
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
mongo_client: AsyncIOMotorClient | None = None

def get_mongo_db():
    return mongo_client["library_docs"]

# --- One combined lifespan for both ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    yield
    mongo_client.close()
    await engine.dispose()



# main.py
from fastapi import FastAPI
from database import lifespan

app = FastAPI(lifespan=lifespan)


# .env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/library
MONGO_URL=mongodb://localhost:27017/


# main.py (continued)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import crud
import schemas

@app.post("/borrows", response_model=schemas.BorrowRead, status_code=201)
async def create_borrow(
    payload: schemas.BorrowCreate,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    borrow = await crud.create_borrow(db, payload.member_id, payload.book_id)
    member = await db.get(crud.Member, payload.member_id)
    book = await db.get(crud.Book, payload.book_id)

    await mongo_db["borrow_log"].insert_one({
        "event": "borrow",
        "timestamp": datetime.utcnow(),
        "member": {"member_id": member.member_id, "name": member.name},
        "book": {"book_id": book.book_id, "title": book.title, "category": book.category},
        "due_date": borrow.due_date,
        "returned": False,
        "return_timestamp": None,
    })

    return borrow



uvicorn main:app --reload



curl -X POST http://localhost:8000/borrows \
  -H "Content-Type: application/json" \
  -d '{"member_id": 1, "book_id": 3}'



-- psql
SELECT * FROM borrows ORDER BY borrow_id DESC LIMIT 1;



// mongosh
db.borrow_log.find().sort({timestamp: -1}).limit(1)

@app.post("/borrows", response_model=schemas.BorrowRead, status_code=201)
async def create_borrow(
    payload: schemas.BorrowCreate,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    borrow = await crud.create_borrow(db, payload.member_id, payload.book_id)
    member = await db.get(crud.Member, payload.member_id)
    book = await db.get(crud.Book, payload.book_id)

    try:
        await mongo_db["borrow_log"].insert_one({
            "event": "borrow",
            "timestamp": datetime.utcnow(),
            "member": {"member_id": member.member_id, "name": member.name},
            "book": {"book_id": book.book_id, "title": book.title, "category": book.category},
            "due_date": borrow.due_date,
            "returned": False,
            "return_timestamp": None,
        })
    except Exception:
        pass   # log this properly in real code — don't let a Mongo outage fail the borrow

    return borrow