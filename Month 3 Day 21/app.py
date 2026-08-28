from bson.son import SON

pipeline = [
    {"$match": {"returned": False}}
]
results = list(borrow_log.aggregate(pipeline))


pipeline = [
    {"$group": {
        "_id": "$book.book_id",
        "borrow_count": {"$sum": 1}
    }}
]
results = list(borrow_log.aggregate(pipeline))
# [{"_id": 3, "borrow_count": 12}, {"_id": 7, "borrow_count": 4}, ...]


pipeline = [
    {"$group": {"_id": "$book.book_id", "borrow_count": {"$sum": 1}}},
    {"$sort": {"borrow_count": -1}},
    {"$limit": 5}
]


pipeline = [
    {"$group": {
        "_id": "$book.book_id",
        "title": {"$first": "$book.title"},
        "borrow_count": {"$sum": 1}
    }},
    {"$sort": {"borrow_count": -1}}
]

for doc in borrow_log.aggregate(pipeline):
    print(doc["title"], doc["borrow_count"])


pipeline = [
    {"$group": {
        "_id": "$member.member_id",
        "name": {"$first": "$member.name"},
        "borrow_count": {"$sum": 1}
    }},
    {"$sort": {"borrow_count": -1}}
]

for doc in borrow_log.aggregate(pipeline):
    print(doc["name"], doc["borrow_count"])


    pipeline = [
    {"$group": {
        "_id": "$book.book_id",
        "title": {"$first": "$book.title"},
        "borrow_count": {"$sum": 1}
    }},
    {"$match": {"borrow_count": {"$gt": 2}}},   # this is $match acting as HAVING
    {"$sort": {"borrow_count": -1}}
]


