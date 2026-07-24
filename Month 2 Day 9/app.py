class BookCreate(BaseModel):
    title: str
    author: str
    price: float = Field(..., gt=0)
    cost_price: float = Field(..., gt=0)   # what WE paid — internal only

class BookResponse(BaseModel):
    # deliberately does NOT include cost_price
    id: UUID
    title: str
    author: str
    price: float
    created_at: datetime

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    record = {"id": uuid4(), "title": book.title, "author": book.author,
              "price": book.price, "cost_price": book.cost_price, "created_at": datetime.now()}
    books_db[record["id"]] = record
    return record   # the FULL record, cost_price included, goes in here

return JSONResponse(
    status_code=200,
    headers={"X-Generated-By": "library-api"},
    content={"receipt_for": book["title"], "amount_due": book["price"]},
)