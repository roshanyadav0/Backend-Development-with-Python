from typing import Optional
from fastapi import FastAPI

app = FastAPI()

books = [
    {"id": 1, "title": "Dune", "author": "Frank Herbert", "category": "fiction"},
    {"id": 2, "title": "Foundation", "author": "Isaac Asimov", "category": "fiction"},
    {"id": 3, "title": "Clean Code", "author": "Robert Martin", "category": "programming"},
    {"id": 4, "title": "Deep Work", "author": "Cal Newport", "category": "productivity"},
]

@app.get("/books")
def list_books(aurthor: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = 10):
    result = books
    if aurthor:
        result = [book for book in result if book["author"].lower() == aurthor.lower()]
    if category:
        result = [book for book in result if book["category"].lower() == category.lower()]
    return result[:limit]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return book
    return {"error": "Book not found"}

