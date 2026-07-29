from pydantic import BaseModel, Field, Annotated

# Pydantic data model for API request/response validation.
class Library(BaseModel):
    id: Annotated[int, Field(description="Unique identifier for the book")]
    title: Annotated[str, Field(max_length=100, description="Book title")]
    author: Annotated[str, Field(max_length=100, description="Author name")]
    year: Annotated[int, Field(description="Publication year")]
    genre: Annotated[str, Field(max_length=100, description="Book genre")]
