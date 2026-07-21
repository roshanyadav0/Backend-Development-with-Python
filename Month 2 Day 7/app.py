class Author(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    country: Optional[str] = None

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, alias="book_title")
    author: Author
    year: int = Field(..., gt=1450, le=date.today().year)
    price: float = Field(..., gt=0, description="Price in USD, must be positive")
    stock: int = Field(default=0, ge=0)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()

class BookResponse(BaseModel):
    id: UUID
    title: str
    author: Author
    year: int
    price: float
    stock: int
    created_at: datetime