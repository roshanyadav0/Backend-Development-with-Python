app = FastAPI(
    title="Library API",
    description="A small REST API for managing a library's book catalog and checkouts.",
    version="1.0.0",
    contact={"name": "Library API Support", "email": "support@example.com"},
)


# This block confirmed live in info:

# {"title": "Library API", "description": "...", "contact": {...}, "version": "1.0.0"}

# tags= — grouping routes into sections
@app.post("/books", ..., tags=["Books"])
@app.get("/books", ..., tags=["Books"])
@app.get("/books/{book_id}", ..., tags=["Books"])
@app.post("/books/{book_id}/checkout", ..., tags=["Checkout"])

# summary= and response_description=
@app.post(
    "/books",
    summary="Add a new book to the catalog",
    response_description="The newly created book, including its generated id",
)

# Docstrings become the description — automatically
async def create_book(book: BookCreate, db: dict = Depends(get_db)):
    """
    Create a new book record.

    - Requires a **title**, **author**, and **price** greater than zero.
    - **stock** defaults to 0 if not provided.
    - The server generates the book's **id** and **created_at** timestamp.
    """


# responses={} — documenting non-2xx outcomes
@app.get(
    "/books/{book_id}",
    responses={404: {"description": "Book not found"}},
)