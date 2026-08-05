from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import CORS_ORIGINS, ENV
from database import init_db
from errors import register_error_handlers
from middleware import TimingMiddleware
from routers import books, members


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the database
    await init_db()
    print("✓ Database initialized")
    yield
    # Shutdown: cleanup if needed (not much to do with SQLite)
    print("✓ Shutting down")


app = FastAPI(
    title="Library API",
    description="A professional REST API for managing a library's book catalog and membership system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware (remember: last registered = first executed)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Error handlers
register_error_handlers(app)

# Routers
app.include_router(books.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")


@app.get("/", tags=["Meta"], summary="Service health check")
async def root():
    """API health and metadata endpoint."""
    return {
        "service": "Library API",
        "version": "1.0.0",
        "environment": ENV,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
