# schemas.py
from pydantic import BaseModel
from datetime import date

class BorrowCreate(BaseModel):
    member_id: int
    book_id: int

class BorrowRead(BaseModel):
    borrow_id: int
    member_id: int
    book_id: int
    borrow_date: date
    due_date: date
    return_date: date | None
    model_config = {"from_attributes": True}   # lets Pydantic read ORM objects directly
    