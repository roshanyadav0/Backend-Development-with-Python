from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
borrow_log = client["library_docs"]["borrow_log"]

# $eq — usually implicit, these two are identical
borrow_log.find({"returned": False})
borrow_log.find({"returned": {"$eq": False}})

# $gt / $gte / $lt / $lte — comparisons
borrow_log.find({"due_date": {"$lt": datetime.utcnow()}})   # overdue

# $ne — not equal
borrow_log.find({"member.member_id": {"$ne": 7}})

# $in — matches any value in a list (Day 3's WHERE ... IN)
borrow_log.find({"book.category": {"$in": ["Fiction", "Sci-Fi"]}})

# $and — usually implicit when you list multiple fields, but explicit when needed
borrow_log.find({
    "$and": [
        {"returned": False},
        {"due_date": {"$lt": datetime.utcnow()}}
    ]
})

# $or — no implicit form, must be explicit
borrow_log.find({
    "$or": [
        {"member.member_id": 7},
        {"member.member_id": 12}
    ]
})


# Include only these fields (plus _id, which comes back by default)
borrow_log.find(
    {"returned": False},
    {"member.name": 1, "book.title": 1, "due_date": 1}
)

# Exclude _id explicitly if you don't want it
borrow_log.find(
    {"returned": False},
    {"_id": 0, "member.name": 1, "book.title": 1}
)

# Exclude specific fields, keep everything else
borrow_log.find(
    {"returned": False},
    {"member.email": 0}
)

# Most recent borrows first — equivalent to ORDER BY timestamp DESC
borrow_log.find({"member.member_id": 7}).sort("timestamp", -1)

# Multiple sort keys — equivalent to ORDER BY category ASC, title ASC
borrow_log.find().sort([("book.category", 1), ("book.title", 1)])

# LIMIT 5 — the 5 most recent borrows
borrow_log.find().sort("timestamp", -1).limit(5)

# Pagination — SQL's OFFSET equivalent
borrow_log.find().sort("timestamp", -1).skip(20).limit(10)   # page 3, 10 per page


# Simple nested field match
borrow_log.find({"member.member_id": 7})

# Nested field with a comparison operator
borrow_log.find({"book.total_copies": {"$gt": 2}})

# Combining a top-level field and a nested field
borrow_log.find({"returned": False, "member.member_id": 7})

from datetime import datetime, timedelta

thirty_days_ago = datetime.utcnow() - timedelta(days=30)

results = list(borrow_log.find({
    "member.member_id": 7,
    "timestamp": {"$gte": thirty_days_ago}
}).sort("timestamp", -1))

for r in results:
    print(r["timestamp"], r["book"]["title"], "returned" if r["returned"] else "active")

results = list(borrow_log.find(
    {
        "member.member_id": 7,
        "timestamp": {"$gte": thirty_days_ago}
    },
    {"_id": 0, "book.title": 1, "timestamp": 1, "due_date": 1, "returned": 1}
).sort("timestamp", -1))

SELECT b.title, br.borrow_date, br.due_date, br.return_date
FROM borrows br
JOIN books b ON br.book_id = b.book_id
WHERE br.member_id = 7 AND br.borrow_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY br.borrow_date DESC;

