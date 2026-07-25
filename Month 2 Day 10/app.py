from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status

app =  FastAPI()

books_db: dict[UUID, dict] = {}

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str
    year: int
    price: float = Field(..., gt=0)

class BookUpdate(BaseModel):
    # PUT = full replacement, so every field is still required
    title: str = Field(..., min_length=1)
    author: str
    year: int
    price: float = Field(..., gt=0)

class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    year: int
    price: float
    created_at: datetime

def get_book_or_404(book_id: UUID) -> dict:
    book = books_db.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return book

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    new_id = uuid4()
    record = {**book.model_dump(), "id": new_id, "created_at": datetime.now()}
    books_db[new_id] = record
    return record

@app.get("/books", response_model=List[BookResponse])
def list_books():
    return list(books_db.values())

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: UUID):
    return get_book_or_404(book_id)

@app.put("/books/{book_id}", response_model=BookResponse)
def replace_book(book_id: UUID, book: BookUpdate):
    existing = get_book_or_404(book_id)
    updated = {**book.model_dump(), "id": book_id, "created_at": existing["created_at"]}
    books_db[book_id] = updated
    return updated

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: UUID):
    get_book_or_404(book_id)
    del books_db[book_id]
    return None