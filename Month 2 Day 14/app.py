# FastAPI application with SQLAlchemy database integration
# This file defines the API routes, database initialization, and serialization helpers.
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from config import session, engine
import database_models

# Sample book data used to populate the database if it is empty.
sample_books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "year": 1925, "genre": "Fiction"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee", "year": 1960, "genre": "Fiction"},
    {"id": 3, "title": "1984", "author": "George Orwell", "year": 1949, "genre": "Dystopian"},
    {"id": 4, "title": "Pride and Prejudice", "author": "Jane Austen", "year": 1813, "genre": "Romance"},
    {"id": 5, "title": "Moby-Dick", "author": "Herman Melville", "year": 1851, "genre": "Adventure"},
    {"id": 6, "title": "The Hobbit", "author": "J.R.R. Tolkien", "year": 1937, "genre": "Fantasy"},
    {"id": 7, "title": "War and Peace", "author": "Leo Tolstoy", "year": 1869, "genre": "Historical"},
    {"id": 8, "title": "The Catcher in the Rye", "author": "J.D. Salinger", "year": 1951, "genre": "Fiction"},
    {"id": 9, "title": "The Alchemist", "author": "Paulo Coelho", "year": 1988, "genre": "Philosophy"},
    {"id": 10, "title": "Jane Eyre", "author": "Charlotte Brontë", "year": 1847, "genre": "Gothic"}
]


def get_db():
    """Yield a new SQLAlchemy session for each request."""
    db = session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create the database tables and populate sample data if needed."""
    with session() as db:
        if db.query(database_models.Library).count() == 0:
            for book_data in sample_books:
                db.add(database_models.Library(**book_data))
            db.commit()


def serialize_book(book: database_models.Library) -> dict:
    """Convert a SQLAlchemy model object into a JSON-serializable dict."""
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "genre": book.genre,
    }

#  Auth 
def get_current_user(x_token: str = Header(...), db: dict = Depends(get_db)) -> dict:
    print("get_current_user() called")
    if x_token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid or missing X-Token header")
    return {"username": "demo_user"}

# Create all database tables and initialize with sample data.
database_models.Base.metadata.create_all(bind=engine)
init_db()

# Create the FastAPI app instance.
app = FastAPI()


@app.get('/')
def read_root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the Library API"}


@app.get('/library')
def read_library(db: Session = Depends(get_db)):
    """Return all books from the library as a serialized list."""
    books = db.query(database_models.Library).all()
    return {
        'message': 'Fetched successfully',
        'context': [serialize_book(book) for book in books]
    }


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db : Session = Depends(get_db)
    ):
    print(f"handling request as user: {current_user['username']}")