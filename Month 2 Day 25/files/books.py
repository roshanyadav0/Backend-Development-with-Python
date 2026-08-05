from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database import get_session
from models import Book
from errors import ResourceNotFoundError

router = APIRouter(prefix="/books", tags=["Books"])


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    author: str = Field(..., min_length=1, description="Author name")
    price: float = Field(..., gt=0, description="Price in USD")
    available: bool = Field(default=True, description="Is the book available?")

    @field_validator("title", "author", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("cannot be blank or whitespace-only")
        return v


class BookUpdate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    available: bool = Field(...)

    @field_validator("title", "author", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("cannot be blank or whitespace-only")
        return v


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    price: float
    available: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BookFilters:
    def __init__(
        self,
        author: Optional[str] = None,
        available: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10,
    ):
        self.author = author
        self.available = available
        self.skip = max(0, skip)
        self.limit = min(limit, 100)


async def filter_books(
    filters: BookFilters = Depends(),
    session: AsyncSession = Depends(get_session),
) -> List[Book]:
    query = select(Book)

    if filters.author:
        query = query.where(Book.author.ilike(f"%{filters.author}%"))

    if filters.available is not None:
        query = query.where(Book.available == filters.available)

    query = query.offset(filters.skip).limit(filters.limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_book_or_404(book_id: UUID, session: AsyncSession = Depends(get_session)) -> Book:
    book = await session.get(Book, book_id)
    if book is None:
        raise ResourceNotFoundError("book", book_id)
    return book


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book",
    response_description="The newly created book with server-generated id",
)
async def create_book(book: BookCreate, session: AsyncSession = Depends(get_session)):
    """Create a new book record in the catalog. The server generates the id and timestamp."""
    db_book = Book(**book.model_dump())
    session.add(db_book)
    await session.commit()
    await session.refresh(db_book)
    return db_book


@router.get(
    "",
    response_model=List[BookResponse],
    summary="List books with optional filtering",
)
async def list_books(books: List[Book] = Depends(filter_books)):
    """
    Retrieve books from the catalog.

    **Query parameters:**
    - `author`: Filter by author name (substring match, case-insensitive)
    - `available`: Filter by availability (`true` or `false`)
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 10, max: 100)

    Returns an empty list when no results match the filters.
    """
    return books


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get a single book by id",
    responses={404: {"description": "Book not found"}},
)
async def get_book(book: Book = Depends(get_book_or_404)):
    """Retrieve a specific book by its UUID."""
    return book


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Replace a book",
    responses={404: {"description": "Book not found"}},
)
async def replace_book(
    book_id: UUID,
    updates: BookUpdate,
    session: AsyncSession = Depends(get_session),
    existing: Book = Depends(get_book_or_404),
):
    """Replace all fields of an existing book."""
    for key, value in updates.model_dump().items():
        setattr(existing, key, value)
    session.add(existing)
    await session.commit()
    await session.refresh(existing)
    return existing


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    responses={404: {"description": "Book not found"}},
)
async def delete_book(
    book_id: UUID,
    session: AsyncSession = Depends(get_session),
    existing: Book = Depends(get_book_or_404),
):
    """Delete a book from the catalog."""
    session.delete(existing)
    await session.commit()
