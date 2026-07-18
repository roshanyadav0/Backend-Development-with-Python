from fastapi import FastAPI
from pprint import pprint

app = FastAPI()

@app.get("/")
def get_root():
    return {"message": "Hello, World!"}

@app.get("/books/{book_id}")
def get_book(book_id: int):
    return {"book_id": book_id, "title": "Dune"}

