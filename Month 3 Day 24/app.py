# database_mongo.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client: AsyncIOMotorClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017/")
    yield
    mongo_client.close()



# main.py
from fastapi import FastAPI
from database_mongo import lifespan

app = FastAPI(lifespan=lifespan)




# database_mongo.py (continued)
def get_mongo_db():
    return mongo_client["library_docs"]



from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

@app.get("/logs")
async def read_logs(mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    borrow_log = mongo_db["borrow_log"]
    ...


from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

@app.post("/borrows", response_model=BorrowRead, status_code=201)
async def create_borrow(
    payload: BorrowCreate,
    db: AsyncSession = Depends(get_db),           # Postgres session (Day 14)
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),  # Mongo db (today)
):
    borrow = await crud.create_borrow(db, payload.member_id, payload.book_id)

    member = await db.get(Member, payload.member_id)
    book = await db.get(Book, payload.book_id)

    await mongo_db["borrow_log"].insert_one({
        "event": "borrow",
        "timestamp": datetime.utcnow(),
        "member": {"member_id": member.member_id, "name": member.name, "email": member.email},
        "book": {"book_id": book.book_id, "title": book.title, "author": book.author, "category": book.category},
        "due_date": borrow.due_date,
        "returned": False,
        "return_timestamp": None,
    })

    return borrow


from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

@app.post("/borrows", response_model=BorrowRead, status_code=201)
async def create_borrow(
    payload: BorrowCreate,
    db: AsyncSession = Depends(get_db),           # Postgres session (Day 14)
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),  # Mongo db (today)
):
    borrow = await crud.create_borrow(db, payload.member_id, payload.book_id)

    member = await db.get(Member, payload.member_id)
    book = await db.get(Book, payload.book_id)

    await mongo_db["borrow_log"].insert_one({
        "event": "borrow",
        "timestamp": datetime.utcnow(),
        "member": {"member_id": member.member_id, "name": member.name, "email": member.email},
        "book": {"book_id": book.book_id, "title": book.title, "author": book.author, "category": book.category},
        "due_date": borrow.due_date,
        "returned": False,
        "return_timestamp": None,
    })

    return borrow


@app.post("/borrows/{borrow_id}/return", response_model=BorrowRead)
async def return_book(
    borrow_id: int,
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    borrow = await crud.return_borrow(db, borrow_id)   # updates Postgres, raises 404/409 as needed

    await mongo_db["borrow_log"].update_one(
        {"member.member_id": borrow.member_id, "book.book_id": borrow.book_id, "returned": False},
        {"$set": {"returned": True, "return_timestamp": datetime.utcnow()}}
    )

    return borrow


from bson import ObjectId

@app.get("/logs")
async def read_logs(
    member_id: int | None = None,
    limit: int = 20,
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    query = {}
    if member_id is not None:
        query["member.member_id"] = member_id

    cursor = mongo_db["borrow_log"].find(query).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(length=limit)

    for doc in docs:
        doc["_id"] = str(doc["_id"])   # see below — this line is not optional

    return docs


from pydantic import BaseModel, Field, field_validator

class LogEntry(BaseModel):
    id: str = Field(alias="_id")
    event: str
    timestamp: datetime
    returned: bool

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v):
        return str(v)

    model_config = {"populate_by_name": True}


    uvicorn main:app --reload


    curl -X POST http://localhost:8000/borrows \
  -H "Content-Type: application/json" \
  -d '{"member_id": 1, "book_id": 3}'

curl http://localhost:8000/logs


-- psql
SELECT * FROM borrows ORDER BY borrow_id DESC LIMIT 1;


// mongosh
db.borrow_log.find().sort({timestamp: -1}).limit(1)