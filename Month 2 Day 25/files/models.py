from sqlalchemy import Column, String, Float, Boolean, DateTime
from datetime import datetime
from database import Base
import uuid


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Member(Base):
    __tablename__ = "members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
