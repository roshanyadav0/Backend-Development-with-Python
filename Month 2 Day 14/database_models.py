from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.declarative import DeclarativeBase

# Base class for SQLAlchemy ORM models.
Base = DeclarativeBase()

class Library(Base):
    """SQLAlchemy ORM model representing a book in the library."""

    __tablename__ = "library"

    id = Column(Integer, primary_key=True) 
    title = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    genre = Column(String(100), nullable=False)