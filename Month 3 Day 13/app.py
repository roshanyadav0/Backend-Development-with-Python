class Book(Base):
    __tablename__ = "books"

    book_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    total_copies: Mapped[int] = mapped_column(default=1, nullable=False)
    cover_url: Mapped[Optional[str]] = mapped_column(String(300))   # new


alembic revision --autogenerate -m "add cover_url to books"


def upgrade():
    op.add_column('books', sa.Column('cover_url', sa.String(length=300), nullable=True))

def downgrade():
    op.drop_column('books', 'cover_url')


alembic upgrade head


\d books


alembic downgrade -1


-- from the migration you're reversing:
def downgrade():
    op.drop_column('books', 'cover_url')



\d books
-- cover_url is gone
SELECT * FROM alembic_version;
-- version_num now shows the PREVIOUS revision id


alembic upgrade head


alembic revision -m "add borrows table"


from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"   # points at "add cover_url" — keep whatever Alembic filled in


def upgrade():
    op.create_table(
        "borrows",
        sa.Column("borrow_id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("borrow_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["members.member_id"]),
        sa.ForeignKeyConstraint(["book_id"], ["books.book_id"]),
    )
    op.create_index("idx_borrows_member_id", "borrows", ["member_id"])


def downgrade():
    op.drop_index("idx_borrows_member_id", table_name="borrows")
    op.drop_table("borrows")



alembic upgrade head


\d borrows
-- confirm columns, FK constraints, and the index all show up