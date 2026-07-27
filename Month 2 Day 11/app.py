def get_book_or_404(book_id: UUID) -> dict:
    book = books_db.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return book

# ... five routes using it: POST 201, GET list, GET one, PUT, DELETE 204