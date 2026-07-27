from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict

class Address(BaseModel):
    street: str = Field(..., max_length=100)
    city: str = Field(..., max_length=50)
    state: str = Field(..., max_length=50)
    zip_code: str = Field(..., regex=r'^\d{5}(-\d{4})?$')  # US ZIP code format

class Patient(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=120)
    gender: Optional[str] = Field(None, regex='^(male|female|other)$')
    address: Address


# Example usage of the Patient class
if __name__ == "__main__":
    patient = Patient(
        name="Jane Doe",
        age=32,
        gender="female",
        address=Address(
            street="456 Elm Street",
            city="Springfield",
            state="IL",
            zip_code="62704",
        ),
    )

    print(patient)
    print("Name:", patient.name)
    print("City:", patient.address.city)

