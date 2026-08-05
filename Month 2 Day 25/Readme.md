# Library API — Production-Ready REST API

A professional, fully-featured REST API for managing a library's book catalog and member system, built with **FastAPI**, **SQLAlchemy**, and **Pydantic**.

## Features

✅ **Full CRUD operations** for Books and Members  
✅ **Async/await** throughout for high concurrency  
✅ **Real SQLite database** via SQLAlchemy ORM  
✅ **Advanced filtering & pagination** with query parameters  
✅ **Consistent error handling** with structured JSON responses  
✅ **OpenAPI/Swagger documentation** auto-generated  
✅ **CORS configured** for cross-origin frontend requests  
✅ **Request timing middleware** for performance monitoring  
✅ **Comprehensive validation** with Pydantic  
✅ **Professional package structure** ready to scale  

## Quick Start

### Installation

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic[email] python-multipart
```

### Running

```bash
# Development with auto-reload
uvicorn main:app --reload

# Production (without reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will start at `http://localhost:8000`

- **Interactive Swagger docs**: http://localhost:8000/docs
- **ReDoc (read-only)**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## Project Structure

```
library_api_complete/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration (DB URL, CORS, environment)
├── database.py          # SQLAlchemy engine, session factory
├── models.py            # ORM models (Book, Member)
├── errors.py            # Error handlers & custom exceptions
├── middleware.py        # HTTP middleware (timing, logging)
├── routers/
│   ├── books.py         # /api/v1/books — full CRUD + filtering
│   └── members.py       # /api/v1/members — create/list/get + filtering
└── library.db           # SQLite database (created automatically)
```

## API Endpoints

### Books

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/books` | Create a new book |
| `GET` | `/api/v1/books` | List all books (with filters) |
| `GET` | `/api/v1/books/{id}` | Get a specific book |
| `PUT` | `/api/v1/books/{id}` | Replace a book |
| `DELETE` | `/api/v1/books/{id}` | Delete a book |

**Query parameters on `GET /api/v1/books`:**
```
?author=Frank          # Filter by author (substring, case-insensitive)
?available=true        # Filter by availability (true/false)
?skip=20&limit=10      # Pagination (skip 20, return 10)
```

### Members

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/members` | Register a new member |
| `GET` | `/api/v1/members` | List all members (with filters) |
| `GET` | `/api/v1/members/{id}` | Get a specific member |

**Query parameters on `GET /api/v1/members`:**
```
?name=Alice            # Filter by name (substring, case-insensitive)
?skip=0&limit=10       # Pagination
```

## Example Requests

### Create a Book

```bash
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dune",
    "author": "Frank Herbert",
    "price": 12.99,
    "available": true
  }'
```

### List Available Books by Author

```bash
curl "http://localhost:8000/api/v1/books?author=Herbert&available=true"
```

### Register a Member

```bash
curl -X POST http://localhost:8000/api/v1/members \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com"
  }'
```

### Get a Member

```bash
curl http://localhost:8000/api/v1/members/550e8400-e29b-41d4-a716-446655440000
```

## Validation Rules

### Books
- `title`: Required, non-blank string (min 1 char, stripped)
- `author`: Required, non-blank string (min 1 char, stripped)
- `price`: Required, must be > 0
- `available`: Optional boolean (defaults to `true`)

### Members
- `name`: Required, non-blank string (min 1 char, stripped)
- `email`: Required, valid email address

## Error Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "book 550e8400-e29b-41d4-a716-446655440000 not found"
  }
}
```

| Status | Code | Meaning |
|--------|------|---------|
| **422** | `VALIDATION_ERROR` | Invalid request (bad type, missing field, failed validator) |
| **404** | `{RESOURCE}_NOT_FOUND` | Resource doesn't exist |
| **500** | `INTERNAL_ERROR` | Unexpected server error |

## Configuration

Edit `config.py` or set environment variables:

```bash
# Database URL (any SQLAlchemy async URL)
DATABASE_URL=sqlite+aiosqlite:///./library.db

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENV=development
```

## Database

The API uses **SQLite** with **async support** via `aiosqlite`. The database is automatically created on first run.

To inspect the database directly:

```bash
sqlite3 library.db
sqlite> SELECT * FROM books;
```

To migrate to PostgreSQL for production, change `DATABASE_URL`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/library
```

## Performance Considerations

- **Pagination limit is capped at 100** to prevent bulk exports and server overload
- **Filtering is done in SQL**, not in memory, so it scales with large datasets
- **Async/await throughout** allows thousands of concurrent requests per process
- **Request timing middleware** tracks every endpoint's latency in the `X-Process-Time` header

## Testing the API

### With cURL

```bash
# Test the health endpoint
curl http://localhost:8000/

# Create a book and capture its id
BOOK_ID=$(curl -s -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","author":"Tester","price":5.0}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Verify it was created
curl http://localhost:8000/api/v1/books/$BOOK_ID

# Update it
curl -X PUT http://localhost:8000/api/v1/books/$BOOK_ID \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated","author":"Tester","price":6.0,"available":false}'

# Delete it
curl -X DELETE http://localhost:8000/api/v1/books/$BOOK_ID
```

### With Swagger UI

Open http://localhost:8000/docs in your browser. Every endpoint can be tested interactively with a "Try it out" button.

## Production Deployment

### Using Gunicorn (ASGI)

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Using Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment for Production

```bash
ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db/library
CORS_ORIGINS=https://yourdomain.com
```

## Next Steps

- **Authentication**: Add JWT token validation in a dependency
- **Authorization**: Restrict delete/update operations to admin roles
- **Loans tracking**: Add `/api/v1/loans` to track who borrowed which books
- **Search indexing**: Use PostgreSQL full-text search for better performance
- **Automated tests**: Add pytest with async fixtures
- **Rate limiting**: Add middleware to prevent abuse
- **Caching**: Use Redis to cache frequently accessed books

## Common Issues

**Database is locked**: SQLite is not ideal for high concurrency. Switch to PostgreSQL for production.

**404 on book {id}**: Make sure the UUID is valid and the book exists. Check the 404 error response.

**CORS errors in browser**: Ensure `http://localhost:3000` (or your frontend origin) is in `CORS_ORIGINS`.

**Validation error on POST**: Check that required fields are present and valid. Whitespace-only strings are rejected.

## License

MIT