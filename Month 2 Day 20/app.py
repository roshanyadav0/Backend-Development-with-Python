# CORSMiddleware, piece by piece

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Dev vs. prod settings
# prod
allow_origins=["https://library.example.com"],
allow_credentials=True,


# dev
allow_origins=["http://localhost:3000", "http://localhost:5173"],  # common dev server ports
allow_credentials=True,