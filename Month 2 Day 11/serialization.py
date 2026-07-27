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

print(patient)
print("Name:", patient.name)
print("City:", patient.address.city)



# Serialization and Deserialization
# Serialization: Converting a Python object to a JSON string
temp_json = patient.model_dump_json(include={"name", "age", "address"})  # Include only specific fields in serialization
print("Serialized JSON:", temp_json)

temp_dict = patient.model_dump(exclude={"address"})  # Exclude the address field from serialization
print("Serialized Dictionary:", temp_dict)

# exclude_unset=True: Exclude fields that are not set (i.e., have a value of None) from serialization

# Deserialization: Converting a JSON string back to a Python object
new_patient = Patient.model_validate_json(temp_json)
print("Deserialized Patient:", new_patient)