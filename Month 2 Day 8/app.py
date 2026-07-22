class BookCreate(BaseModel):
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

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    new_book = BookResponse(
        id=uuid4(), title=book.title, author=book.author,
        year=book.year, price=book.price, created_at=datetime.now(),
    )
    books_db[new_book.id] = new_book.model_dump()
    return new_book