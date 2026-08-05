from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_session
from models import Member
from errors import ResourceNotFoundError

router = APIRouter(prefix="/members", tags=["Members"])


class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Member name")
    email: EmailStr = Field(..., description="Member email")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("name cannot be blank or whitespace-only")
        return v


class MemberResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    joined_at: datetime

    class Config:
        from_attributes = True


class MemberFilters:
    def __init__(self, name: Optional[str] = None, skip: int = 0, limit: int = 10):
        self.name = name
        self.skip = max(0, skip)
        self.limit = min(limit, 100)


async def filter_members(
    filters: MemberFilters = Depends(),
    session: AsyncSession = Depends(get_session),
) -> List[Member]:
    query = select(Member)

    if filters.name:
        query = query.where(Member.name.ilike(f"%{filters.name}%"))

    query = query.offset(filters.skip).limit(filters.limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_member_or_404(member_id: UUID, session: AsyncSession = Depends(get_session)) -> Member:
    member = await session.get(Member, member_id)
    if member is None:
        raise ResourceNotFoundError("member", member_id)
    return member


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new member",
)
async def create_member(member: MemberCreate, session: AsyncSession = Depends(get_session)):
    """Register a new library member."""
    db_member = Member(**member.model_dump())
    session.add(db_member)
    await session.commit()
    await session.refresh(db_member)
    return db_member


@router.get(
    "",
    response_model=List[MemberResponse],
    summary="List members with optional name filter",
)
async def list_members(members: List[Member] = Depends(filter_members)):
    """
    Retrieve library members.

    **Query parameters:**
    - `name`: Filter by member name (substring match, case-insensitive)
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum records to return (default: 10, max: 100)
    """
    return members


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get a member by id",
    responses={404: {"description": "Member not found"}},
)
async def get_member(member: Member = Depends(get_member_or_404)):
    """Retrieve a specific member by their UUID."""
    return member
