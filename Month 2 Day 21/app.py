# The actual layout
library_api/
├── database.py
├── main.py
└── routers/
    ├── __init__.py
    ├── books.py
    └── members.py

# APIRouter — a mini-FastAPI for one resource

# routers/books.py
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db

router = APIRouter(prefix="/books", tags=["Books"])

@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate, db: dict = Depends(get_db)):
    ...

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, db: dict = Depends(get_db)):
    ...


# Wiring it together in main.py
from fastapi import FastAPI
from routers import books, members

app = FastAPI(title="Library API")
app.include_router(books.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")