# Filtering logic lives entirely in a dependency
class BookFilters:
    def __init__(self, author: Optional[str] = None, available: Optional[bool] = None, skip: int = 0, limit: int = 10):
        self.author = author
        self.available = available
        self.skip = skip
        self.limit = limit

async def filter_books(filters: BookFilters = Depends(), db: dict = Depends(get_db)) -> List[dict]:
    items = list(db.values())
    if filters.author:
        items = [b for b in items if filters.author.lower() in b["author"].lower()]
    if filters.available is not None:
        items = [b for b in items if b["available"] == filters.available]
    return items[filters.skip: filters.skip + filters.limit]

@router.get("", response_model=List[BookResponse])
async def list_books(books: List[dict] = Depends(filter_books)):
    return books