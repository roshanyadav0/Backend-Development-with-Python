from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

BookDict = Dict[str, Any]
BooksDB = Dict[UUID, BookDict]

class BookResponse(BaseModel):
    id: UUID
    title: str
    stock: int

class BookNotFoundError(HTTPException):
    def __init__(self, book_id: UUID):
        super().__init__(status_code=404, detail=f"Book {book_id} not found")

class InsufficientStockError(HTTPException):
    def __init__(self, book_id: UUID):
        super().__init__(status_code=400, detail=f"Insufficient stock for book {book_id}")

example_book_id = uuid4()
books_db: BooksDB = {
    example_book_id: {
        "id": example_book_id,
        "title": "Example Book",
        "stock": 5,
    }
}

async def get_db() -> BooksDB:
    return books_db   # every route below asks for THIS, never the global directly

async def get_book_or_404(book_id: UUID, db: BooksDB = Depends(get_db)) -> BookDict:
    book = db.get(book_id)
    if book is None:
        raise BookNotFoundError(book_id)
    return book

@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book: BookDict = Depends(get_book_or_404)):
    return book

@app.post("/books/{book_id}/checkout", response_model=BookResponse)
async def checkout_book(book_id: UUID, db: BooksDB = Depends(get_db), book: BookDict = Depends(get_book_or_404)):
    if book["stock"] <= 0:
        raise InsufficientStockError(book_id)
    book["stock"] -= 1
    return book