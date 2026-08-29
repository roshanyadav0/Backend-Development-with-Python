pip install motor --break-system-packages


from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017/")
db = client["library_docs"]
borrow_log = db["borrow_log"]


async def log_borrow(member: dict, book: dict, due_date):
    result = await borrow_log.insert_one({
        "event": "borrow",
        "timestamp": datetime.utcnow(),
        "member": member,
        "book": book,
        "due_date": due_date,
        "returned": False,
        "return_timestamp": None,
    })
    return result.inserted_id


    async def return_book(borrow_id):
    await borrow_log.update_one(
        {"_id": borrow_id},
        {"$set": {"returned": True, "return_timestamp": datetime.utcnow()}}
    )



async def get_active_borrows(member_id: int):
    cursor = borrow_log.find({
        "member.member_id": member_id,
        "returned": False
    })
    results = await cursor.to_list(length=100)
    return results



async def recent_borrows_for_member(member_id: int, days: int = 30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    cursor = borrow_log.find({
        "member.member_id": member_id,
        "timestamp": {"$gte": cutoff}
    }).sort("timestamp", -1).limit(10)

    return await cursor.to_list(length=10)



async def print_all_active_borrows():
    async for doc in borrow_log.find({"returned": False}):
        print(doc["book"]["title"], doc["member"]["name"])


async def borrows_per_book():
    pipeline = [
        {"$group": {
            "_id": "$book.book_id",
            "title": {"$first": "$book.title"},
            "borrow_count": {"$sum": 1}
        }},
        {"$sort": {"borrow_count": -1}}
    ]
    return await borrow_log.aggregate(pipeline).to_list(length=None)




