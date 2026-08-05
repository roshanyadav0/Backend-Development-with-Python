# Library API — Complete Build

This is a production-ready REST API for managing a library's book catalog and membership system, incorporating all concepts from the 25-day FastAPI curriculum.

## What's Included

✅ **Full CRUD operations** for Books and Members  
✅ **Async/await** throughout for high concurrency  
✅ **Real SQLite database** via SQLAlchemy async ORM  
✅ **Filtering & pagination** with query parameters  
✅ **Consistent error handling** with structured JSON  
✅ **OpenAPI/Swagger docs** auto-generated  
✅ **CORS** configured for frontend integration  
✅ **Request timing middleware** for performance  
✅ **Comprehensive validation** with Pydantic  
✅ **Professional project structure** ready to scale  

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload

# Visit the interactive docs
open http://localhost:8000/docs
```

## Key Concepts Implemented

- **Day 1-3**: FastAPI app structure, routing, documentation
- **Day 2**: REST principles with proper HTTP methods
- **Day 4**: Path and query parameters with filtering
- **Day 6-7**: Pydantic models with full validation
- **Day 8-9**: Request/response bodies with proper schemas
- **Day 12-13**: Dependency injection for database and filters
- **Day 14-15**: Async/await patterns throughout
- **Day 16**: Centralized error handling with consistent shapes
- **Day 18**: OpenAPI docs with tags, summaries, descriptions
- **Day 19**: Middleware for timing and logging
- **Day 20**: CORS configuration for frontend access
- **Day 21**: Project structure with APIRouter and package layout
- **Day 24-25**: Filtering, pagination, and edge case validation

## API Endpoints

### Books
- `POST /api/v1/books` — Create
- `GET /api/v1/books` — List (with filtering & pagination)
- `GET /api/v1/books/{id}` — Get one
- `PUT /api/v1/books/{id}` — Replace
- `DELETE /api/v1/books/{id}` — Delete

### Members
- `POST /api/v1/members` — Register
- `GET /api/v1/members` — List (with filtering & pagination)
- `GET /api/v1/members/{id}` — Get one

## Example Requests

```bash
# Create a book
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Dune","author":"Frank Herbert","price":12.99}'

# List available books by Herbert
curl "http://localhost:8000/api/v1/books?author=Herbert&available=true"

# Register a member
curl -X POST http://localhost:8000/api/v1/members \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

## Production Deployment

```bash
# With Gunicorn
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Or with Docker
docker build -t library-api .
docker run -p 8000:8000 library-api
```

## Next Steps

- Add JWT authentication
- Implement role-based access control (admin vs. member)
- Add loan tracking (`/api/v1/loans`)
- Use PostgreSQL instead of SQLite
- Add automated pytest test suite
- Deploy to production with CI/CD

See README.md for full documentation.
