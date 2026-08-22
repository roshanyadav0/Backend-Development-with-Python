# database.py
import os
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:yourpassword@localhost:5432/library"
)

engine = create_engine(DATABASE_URL, echo=True)


# database.py (continued)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()