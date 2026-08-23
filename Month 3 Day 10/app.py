from database import SessionLocal
from models import Member
from datetime import date

db = SessionLocal()

new_member = Member(name="Asha Rao", email="asha@mail.com", joined_date=date.today())
db.add(new_member)          # Transient -> Pending. Not in the DB yet.
db.commit()                 # Pending -> Persistent. INSERT actually runs.

print(new_member.member_id) # populated only after commit — Postgres assigned it
db.close()


from sqlalchemy import select
from models import Book, Borrow

# WHERE
stmt = select(Book).where(Book.category == "Fiction")
books = db.execute(stmt).scalars().all()

# JOIN + WHERE, translating a Day 4 query directly
stmt = (
    select(Member.name, Book.title, Borrow.borrow_date)
    .join(Borrow, Borrow.member_id == Member.member_id)
    .join(Book, Book.book_id == Borrow.book_id)
    .where(Borrow.return_date.is_(None))
)
results = db.execute(stmt).all()

# GROUP BY + COUNT, translating a Day 3 query directly
from sqlalchemy import func
stmt = (
    select(Book.category, func.count(Book.book_id))
    .group_by(Book.category)
)
counts = db.execute(stmt).all()


member = db.get(Member, 3)
if member:
    db.delete(member)   # Persistent -> Deleted (pending)
    db.commit()          # DELETE actually runs

    book = db.get(Book, 5)
book.total_copies = 10          # just a normal Python attribute assignment
db.commit()                      # SQLAlchemy generates UPDATE books SET total_copies = 10 WHERE book_id = 5

# OLD — in-memory store, gone on every restart
books_db = {}
members_db = {}
borrows_db = {}

def get_book(book_id):
    return books_db.get(book_id)

def add_borrow(member_id, book_id):
    borrow_id = len(borrows_db) + 1
    borrows_db[borrow_id] = {"member_id": member_id, "book_id": book_id, ...}
    return borrow_id



# NEW — real persistence, survives restarts
from database import SessionLocal
from models import Book, Member, Borrow
from sqlalchemy import select
from datetime import date

def get_book(db, book_id: int) -> Book | None:
    return db.get(Book, book_id)

def create_borrow(db, member_id: int, book_id: int) -> Borrow:
    borrow = Borrow(
        member_id=member_id,
        book_id=book_id,
        borrow_date=date.today(),
        due_date=date.today().replace(day=date.today().day + 14),
    )
    db.add(borrow)
    db.commit()
    db.refresh(borrow)   # reload borrow_id and any DB-side defaults
    return borrow

def list_active_borrows_for_member(db, member_id: int) -> list[Borrow]:
    stmt = select(Borrow).where(
        Borrow.member_id == member_id,
        Borrow.return_date.is_(None)
    )
    return db.execute(stmt).scalars().all()