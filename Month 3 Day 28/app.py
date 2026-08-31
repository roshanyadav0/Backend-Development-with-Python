This is the demo day — treat it literally: walk through the API as if a senior engineer is watching over your shoulder, asking "show me it actually works," not "tell me it works."That's the whole 28-day arc in one picture. Now walk through it, out loud, exactly as you'd narrate it to someone deciding whether to trust this code.

## Walk through every endpoint as if demoing to a senior engineer

The discipline that matters here: **narrate what you expect before you run it, then show the actual result** — not just "it works," but "here's why it should work, here's the command, here's the output, here's how I know it's correct." A senior engineer isn't impressed by a green checkmark; they're checking whether you understand *why* it's green.

```bash
uvicorn main:app --reload
```

**Books and members (Day 9–17, straightforward CRUD):**

```bash
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Clean Code", "author": "Robert Martin", "isbn": "978-1", "total_copies": 3}'
```

Say out loud what you expect: `201`, a `book_id` assigned by Postgres, and confirm it in `psql` independently — never trust only the API's own response, per the discipline every single prior day insisted on.

**The borrow flow (Day 15/25, the actual interesting part):**

```bash
curl -X POST http://localhost:8000/borrows \
  -H "Content-Type: application/json" \
  -d '{"member_id": 1, "book_id": 1}'
```

Narrate the full chain as it happens: FastAPI validates the payload via Pydantic → the CRUD function checks availability inside one transaction (Day 7, Day 15) → Postgres commits the borrow → the same request writes a matching document to `borrow_log` (Day 24/25) → both are independently confirmable:

```sql
SELECT * FROM borrows ORDER BY borrow_id DESC LIMIT 1;
```
```javascript
db.borrow_log.find().sort({timestamp: -1}).limit(1)
```

**The edge cases (Day 16/27, this is what separates "works" from "actually correct"):**

Don't just say these are handled — trigger each one live and show the exact status code:

```bash
# Borrow the last copy twice
curl -X POST http://localhost:8000/borrows -d '{"member_id": 2, "book_id": 1}'
# expect: 409, "No copies available"

# Return something already returned
curl -X POST http://localhost:8000/borrows/1/return
curl -X POST http://localhost:8000/borrows/1/return
# second call: 409, "already returned"

# Duplicate ISBN
curl -X POST http://localhost:8000/books -d '{"title": "X", "author": "Y", "isbn": "978-1", "total_copies": 1}'
# expect: 409, not a raw 500
```

If any of these produces an unhandled `500` right now, that's real, valuable signal to fix today — not something to explain away in the demo.

## PostgreSQL: CRUD works, migrations are clean, transactions correct

Run through this checklist against the actual running system, not from memory:

```bash
alembic current
alembic heads
```

These two should match exactly — your database is caught up to the latest migration, no drift.

```bash
alembic history
```

Read it top to bottom: one clean chain, no branching heads (Day 16), every `down_revision` pointing at a real prior migration, nothing orphaned from earlier experimentation.

**Transactions**, re-verified one more time, live: cause the deliberate failure from Day 7's practice section — attempt a borrow with a `member_id` that doesn't exist, and confirm via `psql` that `available_copies` (or your active-borrow count) is completely unaffected. This is the single check most worth doing live in a demo, because it's the one that actually proves atomicity rather than just asserting it.

## MongoDB: borrow logs write and query correctly

```javascript
db.borrow_log.find({returned: false}).sort({timestamp: -1}).limit(5)
db.borrow_log.aggregate([
  {"$group": {"_id": "$book.book_id", "title": {"$first": "$book.title"}, "count": {"$sum": 1}}},
  {"$sort": {"count": -1}}
])
```

Confirm the aggregation from Day 21 still produces sane numbers against real accumulated demo data, and that the `_id` serialization fix from Day 24 is actually in place — hit `GET /logs` and confirm the JSON response doesn't crash or leak a raw `ObjectId`.

## Tests pass — both DB paths covered

```bash
pytest -v
```

The bar here isn't "tests exist," it's "tests exist for both databases, including the failure paths, not just the happy path." A reasonable coverage checklist to hold yourself to:

- Postgres CRUD: create/read/update/delete for each model
- Postgres constraint violations: duplicate email/ISBN → `409`, not `500`
- Postgres transaction integrity: a deliberately failed borrow leaves no partial state (Day 7's test, automated)
- Mongo inserts: a borrow event actually lands with the correct embedded shape
- Mongo queries: the 30-day activity query (Day 20) and the aggregation pipelines (Day 21) return correct results against known seeded data
- The dual-write path (Day 25): Postgres succeeds even when Mongo is deliberately made unavailable in the test

That last one is worth having as an actual automated test, not just something you checked by hand once on Day 25 — mock or point `MONGO_URL` at an unreachable address in one specific test, and assert the borrow endpoint still returns `201`. If you don't have this test, that's the one gap most worth closing today, since it's protecting the single most important architectural decision from the last two weeks.

## README updated with setup instructions for both DBs

```markdown
# Library API

A dual-database Library API: PostgreSQL for transactional data (books, members, borrows), MongoDB for activity logging (borrow_log).

## Prerequisites
- Python 3.11+
- PostgreSQL running locally
- MongoDB running locally

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Create a `.env` file:
   DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/library
   MONGO_URL=mongodb://localhost:27017/

3. Create the Postgres database:
   createdb library

4. Apply migrations:
   alembic upgrade head

5. Run the app:
   uvicorn main:app --reload

## Run tests
   pytest -v

## API docs
   http://localhost:8000/docs

## Architecture
- `books`, `members`, `borrows` live in PostgreSQL — the source of truth, with full ACID guarantees.
- `borrow_log` lives in MongoDB — an append-only activity history, denormalized for fast querying without joins.
- The two are not transactionally linked: a MongoDB outage does not fail a borrow request. See `create_borrow()` for the deliberate error handling around this.
```

That last "Architecture" section is worth including explicitly rather than assuming it's obvious — it's the one piece of context that turns "why are there two databases here" from a confusing surprise into a documented, deliberate decision, for anyone who clones this repo without having lived through the 28 days that led to it.

**Do one final clean-clone test**, same discipline as Day 16, now covering both databases:

```bash
git clone <your-repo> /tmp/final-check
cd /tmp/final-check
pip install -r requirements.txt --break-system-packages
# create .env, createdb, alembic upgrade head, start Postgres AND Mongo, uvicorn
pytest -v
```

If this succeeds end to end on a genuinely fresh clone with fresh, empty databases, that's the real finish line — not "the code exists," but "a stranger, following only what's written down, gets a working, tested, dual-database system running from nothing."

---

Twenty-eight days ago this started with "what is a relational database and why does it exist." It ends here: a real, tested, version-controlled system spanning two databases, each holding the kind of data it's actually suited for, with transactions, migrations, async I/O, error handling, and a documented architectural decision behind every major choice — not because a tutorial said so, but because you can trace the reasoning back to a specific day and a specific trade-off you worked through yourself.

Where would you like to take this next — deployment (Docker Compose, a hosted environment), authentication and authorization, or something entirely different?