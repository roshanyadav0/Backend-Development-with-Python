pip install pymongo --break-system-packages



from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["library_docs"]          # or client.library_docs
books = db["books"]                   # or db.books


from datetime import datetime

result = books.insert_one({
    "title": "Clean Code",
    "author": "Robert Martin",
    "isbn": "978-1",
    "category": "Programming",
    "total_copies": 3,
})

print(result.inserted_id)   # ObjectId('...') — MongoDB generated this automatically


result = books.insert_many([
    {"title": "The Pragmatic Programmer", "author": "Andy Hunt", "isbn": "978-2"},
    {"title": "Refactoring", "author": "Martin Fowler", "isbn": "978-3"},
])

print(result.inserted_ids)   # list of ObjectIds, one per document

# All documents — equivalent to SELECT * FROM books
all_books = books.find()
for book in all_books:
    print(book)

# find_one — like Day 10's db.get(), but by any field, not just PK
book = books.find_one({"isbn": "978-1"})

# Filter — equivalent to WHERE category = 'Programming'
programming_books = books.find({"category": "Programming"})

# Comparison operators — equivalent to WHERE total_copies > 2
plenty_copies = books.find({"total_copies": {"$gt": 2}})

# Multiple conditions (implicit AND) — WHERE category = 'Programming' AND total_copies > 2
result = books.find({"category": "Programming", "total_copies": {"$gt": 2}})

# $in — equivalent to Day 3's WHERE category IN (...)
result = books.find({"category": {"$in": ["Fiction", "Sci-Fi"]}})

# $or — equivalent to WHERE title LIKE '%Guide%' OR category = 'Reference'
result = books.find({
    "$or": [
        {"title": {"$regex": "Guide"}},
        {"category": "Reference"}
    ]
})


# Equivalent to Day 10's "fetch, mutate, commit" pattern — but expressed as one call
books.update_one(
    {"isbn": "978-1"},                          # filter — which document
    {"$set": {"total_copies": 10}}              # update operator — what changes
)

# update_many — applies to every matching document, not just the first
books.update_many(
    {"category": "Programming"},
    {"$set": {"on_sale": True}}
)

# $inc — atomic increment, useful for counters (like decrementing available copies)
books.update_one(
    {"isbn": "978-1"},
    {"$inc": {"total_copies": -1}}
)

# delete_one / delete_many
books.delete_one({"isbn": "978-3"})
books.delete_many({"category": "Discontinued"})


# WRONG — this REPLACES the entire document with just {"total_copies": 10},
# silently deleting title, author, isbn, and every other field
books.update_one({"isbn": "978-1"}, {"total_copies": 10})

# RIGHT — $set only touches the specified field, leaves everything else alone
books.update_one({"isbn": "978-1"}, {"$set": {"total_copies": 10}})


from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient("mongodb://localhost:27017/")
db = client["library_docs"]
borrow_log = db["borrow_log"]

log_entry = {
    "event": "borrow",
    "timestamp": datetime.utcnow(),
    "member": {
        "member_id": 7,
        "name": "Asha Rao",
        "email": "asha@mail.com",
    },
    "book": {
        "book_id": 3,
        "title": "Clean Code",
        "author": "Robert Martin",
        "isbn": "978-1",
    },
    "due_date": datetime.utcnow() + timedelta(days=14),
    "returned": False,
}

result = borrow_log.insert_one(log_entry)
print(f"Logged borrow event: {result.inserted_id}")

# Later — mark it returned, without needing member/book IDs again
borrow_log.update_one(
    {"_id": result.inserted_id},
    {"$set": {"returned": True, "return_timestamp": datetime.utcnow()}}
)

# Query: every currently-active (unreturned) borrow event
active = list(borrow_log.find({"returned": False}))

# Query: every event for a specific member, most recent first
history = list(borrow_log.find({"member.member_id": 7}).sort("timestamp", -1))