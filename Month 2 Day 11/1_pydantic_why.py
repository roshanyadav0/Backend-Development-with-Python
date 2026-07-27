# type validation 

def validate_type(value: int) -> int:
    if not isinstance(value, int):
        raise ValueError(f"Expected an integer, got {type(value).__name__}")
    return value

"""
Here is a simple example of type validation in Python. The function `validate_type` takes a value as input and checks if it is an instance of the `int` type. If the value is not an integer, it raises a `ValueError` with a message indicating the expected type and the actual type received. If the value is valid, it returns the value. This kind of validation is useful for ensuring that functions receive the correct types of arguments, which can help prevent bugs and improve code reliability.
we use if else to validate the type of the input value. If the input is not of the expected type, we raise an exception to signal that there is an error. This approach allows us to catch type-related issues early in the execution of our program, making it easier to debug and maintain.

"""

# data validation

def validate_data(data: dict) -> dict:
    required_keys = ['name', 'age', 'email']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    return data

"""
Here is an example of data validation in Python. The function `validate_data` takes a dictionary as input and checks if it contains all the required keys: 'name', 'age', and 'email'. If any of these keys
are missing, it raises a `ValueError` with a message indicating which key is missing. If the dictionary contains all the required keys, it returns the dictionary. This kind of validation is useful for ensuring that data structures meet certain criteria before they are processed further, which can help prevent errors and improve the robustness of the code.

"""


# Pydantic 
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Annotated

class Patient(BaseModel):
    name: Annotated[str, Field(max_length=50, title= 'name of the patient', description= 'Give the name of the patient less than 50 char', examples=['David', 'Nina'])]  # Field with max length validation
    age: int
    weight: Annotated[float, Field(gt=0, description='Weight must be greater than 0', strict=True)]  # Field with greater than validation
    married: Optional[bool] = None  # Optional field, can be None and default is None
    allergies: Optional[List[str]] = None  # Optional list of strings, can be None and default is None
    contact: Dict[str, str]

def incert_patient(patient: Patient):
    print(patient.name)
    print(patient.age)

patient1 = Patient(
    name="John Doe",
    age=30,
    weight=70.5,
    married=True,
    allergies=["Peanuts", "Shellfish"],
    contact={"email": "john.doe@example.com"},
)
incert_patient(patient1)

