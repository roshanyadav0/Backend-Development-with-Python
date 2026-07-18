import requests

# Idempotency — the property that decides your retry logic

# Safe to retry automatically — same result every time
requests.put("https://httpbin.org/put", json={"id": 42, "title": "Dune"})

# NOT safe to retry blindly — could create duplicates
requests.post("https://httpbin.org/post", json={"title": "Dune"})


# JSON as the payload format

response = requests.post(
    "https://httpbin.org/post",
    json={"title": "Dune", "author": "Frank Herbert", "year": 1965},
)
# requests automatically sets Content-Type: application/json when you use json=
print(response.request.headers["Content-Type"])   # application/json
print(response.json())                              # parse JSON straight into a dict


"""
Exercise: design the Library API on paper
Before writing a single line of code, sketch the URIs for a library system that manages books, authors, and members who can borrow books. Work through:

What are the resources (nouns)? — probably books, authors, members, loans.
What's the full CRUD set for each? (list, create, get one, update, delete)
How do relationships nest? A book's author — is it /books/42/author or just a field in the book's JSON? Loans probably belong to a member: /members/7/loans.
What actions don't fit CRUD? "Borrow a book" and "return a book" aren't create/update in the usual sense — decide whether that's POST /loans (creating a loan resource) or an action endpoint like POST /books/42/checkout. Both are defensible; REST purists prefer modeling the loan as its own resource.
What goes in the path vs. the query string? (/books/42 vs /books?genre=scifi&available=true)

"""