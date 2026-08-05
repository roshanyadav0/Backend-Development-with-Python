import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./library.db")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
ENV = os.getenv("ENV", "development")
