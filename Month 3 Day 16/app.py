# Insert a book, then try inserting another with the same isbn


# Borrow the last copy, then attempt a second concurrent borrow of the same book

# POST /borrows/99999/return where 99999 doesn't exist



# Call /borrows/{id}/return twice in a row

# POST /borrows with member_id=99999

# POST /members with {"name": "Test", "email": ""}

# POST /books with {"total_copies": -1}

# DELETE /members/1 where member 1 currently has an unreturned book

# Fire two POST /borrows requests for the same last-copy book at nearly the same instant

# POST /borrows with {"member_id": "not-a-number"}

-- confirm these exist (from Day 6, Day 13)
\d books    -- expect: idx on author, unique on isbn
\d members  -- expect: unique on email
\d borrows  -- expect: idx on member_id, idx on book_id

CREATE INDEX idx_borrows_book_id ON borrows(book_id);

alembic history

# .gitignore
__pycache__/
*.pyc
.env
venv/
*.db

# .env (never committed)
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/library


# database.py — reads from .env via python-dotenv, never hardcodes credentials
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]  # raises clearly if missing, rather than silently using a wrong default


# Library API

## Setup
1. `pip install -r requirements.txt`
2. Create a `.env` file with `DATABASE_URL=postgresql+asyncpg://...`
3. `alembic upgrade head`
4. `uvicorn main:app --reload`

## Run tests
pytest

pip freeze > requirements.txt   # pin what you actually used
git init
git add .
git commit -m "Library API: PostgreSQL + SQLAlchemy async + Alembic + FastAPI"
git remote add origin https://github.com/yourusername/library-api.git
git push -u origin main

git clone https://github.com/yourusername/library-api.git /tmp/library-test
cd /tmp/library-test
pip install -r requirements.txt --break-system-packages
# create .env, run alembic upgrade head, start the app