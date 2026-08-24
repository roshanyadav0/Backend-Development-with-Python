pip install "sqlalchemy[asyncio]" asyncpg --break-system-packages


# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:yourpassword@localhost:5432/library"
)

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)




from sqlalchemy import select
from models import Book

async def get_fiction_books():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Book).where(Book.category == "Fiction")
        )
        return result.scalars().all()



async def create_book(title, author, isbn):
    async with AsyncSessionLocal() as session:
        book = Book(title=title, author=author, isbn=isbn)
        session.add(book)          # still sync — no I/O happens here, just tracking
        await session.commit()     # await — this is where the actual INSERT runs
        await session.refresh(book)
        return book


# database.py (continued)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session



# OLD — sync (Day 10)
def create_borrow(db, member_id: int, book_id: int) -> Borrow:
    borrow = Borrow(member_id=member_id, book_id=book_id, ...)
    db.add(borrow)
    db.commit()
    db.refresh(borrow)
    return borrow

# NEW — async
async def create_borrow(db: AsyncSession, member_id: int, book_id: int) -> Borrow:
    borrow = Borrow(member_id=member_id, book_id=book_id, ...)
    db.add(borrow)
    await db.commit()
    await db.refresh(borrow)
    return borrow



# OLD — sync
def list_active_borrows_for_member(db, member_id: int) -> list[Borrow]:
    stmt = select(Borrow).where(Borrow.member_id == member_id, Borrow.return_date.is_(None))
    return db.execute(stmt).scalars().all()

# NEW — async
async def list_active_borrows_for_member(db: AsyncSession, member_id: int) -> list[Borrow]:
    stmt = select(Borrow).where(Borrow.member_id == member_id, Borrow.return_date.is_(None))
    result = await db.execute(stmt)
    return result.scalars().all()



# OLD — sync route
@app.get("/members/{member_id}/borrows")
def read_borrows(member_id: int, db: Session = Depends(get_db)):
    return list_active_borrows_for_member(db, member_id)

# NEW — async route
@app.get("/members/{member_id}/borrows")
async def read_borrows(member_id: int, db: AsyncSession = Depends(get_db)):
    return await list_active_borrows_for_member(db, member_id)


