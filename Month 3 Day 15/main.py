# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import BorrowCreate, BorrowRead  # Pydantic models
import crud

app = FastAPI()

@app.post("/borrows", response_model=BorrowRead, status_code=201)
async def create_borrow(payload: BorrowCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_borrow(db, payload.member_id, payload.book_id)

@app.get("/members/{member_id}/borrows", response_model=list[BorrowRead])
async def read_member_borrows(member_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.list_active_borrows_for_member(db, member_id)

@app.post("/borrows/{borrow_id}/return", response_model=BorrowRead)
async def return_book(borrow_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.return_borrow(db, borrow_id)

from sqlalchemy.exc import IntegrityError

@app.post("/members", response_model=MemberRead, status_code=201)
async def create_member(payload: MemberCreate, db: AsyncSession = Depends(get_db)):
    member = Member(name=payload.name, email=payload.email, joined_date=date.today())
    db.add(member)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A member with this email already exists")
    await db.refresh(member)
    return member