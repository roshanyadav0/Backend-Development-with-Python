from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_validator
from typing import Optional, List, Dict, Annotated

class Patient(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=120)
    weight: float = Field(..., gt=0)
    email: Optional[EmailStr] = None
    married: Optional[bool] = None
    medical_history: Optional[List[str]] = None
    additional_info: Optional[Dict[str, str]] = None

    @field_validator('email')
    @classmethod
    def email_validator(cls, value):
        valid_domains = ['hdfc.com', 'icici.com', 'sbi.com']
        # @abc.com
        domain_name = value.split('@')[-1]
        if domain_name not in valid_domains:
            raise ValueError(f"Email domain must be one of {valid_domains}")
        return value

    @field_validator('name')
    @classmethod
    def name_validator(cls, value):
        return value.upper()  # Convert name to uppercase

