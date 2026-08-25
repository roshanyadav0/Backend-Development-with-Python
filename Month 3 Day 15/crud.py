# crud.py
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models import Book, Borrow
from datetime import date, timedelta

async def create_borrow(db: AsyncSession, member_id: int, book_id: int) -> Borrow:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    active_count_stmt = select(func.count()).select_from(Borrow).where(
        Borrow.book_id == book_id, Borrow.return_date.is_(None)
    )
    active_count = (await db.execute(active_count_stmt)).scalar()
    if active_count >= book.total_copies:
        raise HTTPException(status_code=409, detail="No copies available")

    borrow = Borrow(
        member_id=member_id,
        book_id=book_id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=14),
    )
    db.add(borrow)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid member or book reference")
    await db.refresh(borrow)
    return borrow


from sqlalchemy import select

stmt = select(Book).where(Book.book_id == book_id).with_for_update()
book = (await db.execute(stmt)).scalar_one()