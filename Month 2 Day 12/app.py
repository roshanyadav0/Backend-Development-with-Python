# A dependency is just a function

def get_db() -> dict:
    print("get_db() called")
    return books_db


# Injecting it into a route

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: UUID, db: dict = Depends(get_db)):
    book = db.get(book_id)
    ...


# A second dependency, to show it's general-purpose

def pagination_params(skip: int = 0, limit: int = 10) -> dict:
    return {"skip": skip, "limit": limit}

@app.get("/books", response_model=List[BookResponse])
def list_books(db: dict = Depends(get_db), pagination: dict = Depends(pagination_params)):
    items = list(db.values())
    return items[pagination["skip"]: pagination["skip"] + pagination["limit"]]


def get_fake_db():
return fake_db          # a totally separate, empty dict

app.dependency_overrides[get_db] = get_fake_db

client.post("/books", json={...})   # hits the FAKE db
client.get("/books")                # → 1 book, the fake db, untouched real data