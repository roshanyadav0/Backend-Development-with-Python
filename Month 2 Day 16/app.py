# HTTPException — the standard tool for "this doesn't exist / this isn't allowed"

@app.get("/books/{book_id}")
def get_book(book_id: UUID):
    book = books_db.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return book

# HTTPException for 404 vs a custom exception for business logic

@app.post("/books/{book_id}/checkout")
def checkout_book(book_id: UUID):
    book = books_db.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    if book["stock"] <= 0:
        raise InsufficientStockError(book_id)   # not HTTPException
    ...


# @app.exception_handler — funneling everything into one shape

def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}

@app.exception_handler(InsufficientStockError)
async def handle_insufficient_stock(request: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=400, content=error_body("INSUFFICIENT_STOCK", f"Book {exc.book_id} has no stock available"))

@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=error_body(f"HTTP_{exc.status_code}", str(exc.detail)))

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", "One or more fields failed validation"))

@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "Something went wrong on our end"))