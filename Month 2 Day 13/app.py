def get_db() -> dict:
    print("get_db() called")
    return books_db

def get_current_user(x_token: str = Header(...), db: dict = Depends(get_db)) -> dict:
    print("get_current_user() called")
    if x_token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid or missing X-Token header")
    return {"username": "demo_user"}

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: dict = Depends(get_db),
):
    print(f"handling request as user: {current_user['username']}")
    ...

# Class-based dependency: CommonParams

class CommonParams:
def __init__(self, skip: int = 0, limit: int = 10):
    self.skip = skip
    self.limit = limit

@app.get("/books", response_model=List[BookResponse])
def list_books(commons: CommonParams = Depends(), db: dict = Depends(get_db)):
    items = list(db.values())
    return items[commons.skip : commons.skip + commons.limit]