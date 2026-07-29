@app.get("/books/{book_id}/sequential")
async def get_book_sequential(book_id: int):
    book = await fetch_book_info(book_id)       # waits, THEN starts the next
    reviews = await fetch_reviews(book_id)
    available = await fetch_availability(book_id)
    return {"book": book, "reviews": reviews, "available": available}

@app.get("/books/{book_id}/concurrent")
async def get_book_concurrent(book_id: int):
    book, reviews, available = await asyncio.gather(
        fetch_book_info(book_id),
        fetch_reviews(book_id),
        fetch_availability(book_id),
    )
    return {"book": book, "reviews": reviews, "available": available}

    # When not to use  async - CPU bound work 

def cpu_heavy_work() -> int:
    return sum(i * i for i in range(20_000_000))

@app.get("/cpu-async")
async def cpu_async_route():
    result = cpu_heavy_work()
    return {"result": result}

# The httpx benchmark

async def hit(client, path):
    r = await client.get(f"http://localhost:8000{path}")
    return r.status_code

async def benchmark(path, label):
    async with httpx.AsyncClient(timeout=30) as client:
        start = time.perf_counter()
        results = await asyncio.gather(*[hit(client, path) for _ in range(N)])
        elapsed = time.perf_counter() - start
    print(f"{label} -> {elapsed:.2f}s")