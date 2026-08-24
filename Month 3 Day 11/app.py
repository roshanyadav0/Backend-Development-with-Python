from datetime import date
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base



class Member(Base):
    __tablename__ = 'members'

    member_id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(100), nullable = False)
    email: Mapped[str] = mapped_column(String(100), nullable = False, unique = True)
    joined_date: Mapped[date] = mapped_column(nullable = False)

    borrows : Mapped[List['Borrow']] = relationship(back_populates = 'member')


    def __repr__(self) -> str:
        return f'Member {self.member_id} {self.name}'

class Book(Base):
    __tablename__ = 'books'

    book_id: Mapped[int] = mapped_column(primary_key = True)
    title: Mapped[str] = mapped_column(String(200), nullable = False)
    author: Mapped[str] = mapped_column(String(200), nullable = False)
    isbn: Mapped[str] = mapped_column(String(13), nullable = False, unique = True)
    publication_date: Mapped[date] = mapped_column(nullable = False)
    categories: Mapped[Optional[str]] = mapped_column(String(100), nullable = True)
    total_copies: Mapped[int] = mapped_column(nullable = False)

    borrows : Mapped[List['Borrow']] = relationship(back_populates = 'book')

    def __repr__(self) -> str:
        return f'Book {self.book_id} {self.title!r}'


class Borrow(Base):
    __tablename__ = 'borrows'

    borrow_id: Mapped[int] = mapped_column(primary_key = True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.member_id'), nullable = False)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.book_id'), nullable = False)
    borrow_date: Mapped[date] = mapped_column(nullable = False)
    due_date: Mapped[date] = mapped_column(nullable = False)
    return_date: Mapped[Optional[date]] = mapped_column(nullable = True)

    member : Mapped['Member'] = relationship(back_populates = 'borrows')
    book : Mapped['Book'] = relationship(back_populates = 'borrows')

    def __repr__(self) -> str:
        return f"<Borrow {self.borrow_id} member={self.member_id} book={self.book_id}>"

