# Blank-string validators — the actual gap they close
def _reject_blank(v: str, field_name: str) -> str:
    stripped = v.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be blank")
    return stripped

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    ...
    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        return _reject_blank(v, "title")
