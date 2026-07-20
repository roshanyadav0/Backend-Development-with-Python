"""
Day 6: Pydantic models
BaseModel, field types, validators

from pydantic import BaseModel
Define Book and Member schemas
Field types: str, int, float, datetime, UUID
Optional fields with None defaults
Test: send bad data, watch Pydantic reject it with 422

"""


from datetime import date
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, field_validator

class Book(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    author: str
    year: int
    price: float
    published: Optional[date] = None

    @field_validator("year")
    @classmethod
    def year_must_be_reasonable(cls, v):
        if v < 1450 or v > date.today().year:
            raise ValueError("year must be between 1450 and the current year")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("price must be greater than 0")
        return v

class Member(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None