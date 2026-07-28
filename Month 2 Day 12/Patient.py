import json

from fastapi import FastAPI, HTTPException 
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Any
from pydantic import BaseModel, Field, computed_field

app = FastAPI()


class Patient(BaseModel):
    id : Annotated[str,Field(..., description="The unique identifier for the patient", examples=["PAT001"])]
    name: Annotated[str, Field(..., description="The name of the patient")]
    city: Annotated[str, Field(..., description="The city where the patient resides")]
    age: Annotated[int, Field(..., description='The age of the patient', gt=0, lt=120, examples=[25, 30, 45])]
    gender: Annotated[Literal['Male','Female','Other'], Field(..., description='The gender of the patient', examples=['Male', 'Female'])]
    height: Annotated[float, Field(..., description='The height of the patient in meters', gt=0, examples=[1.705, 1.802])]
    weight: Annotated[float, Field(..., description='The weight of the patient in kilograms', gt=0, examples=[70.5, 80.2])]

    @computed_field(description="The Body Mass Index (BMI) of the patient", examples=[24.2, 27.5])
    @property
    def bmi(self) -> float:
        """Calculate the Body Mass Index (BMI) of the patient."""
        return self.weight / (self.height ** 2)

    @computed_field(description="The health status of the patient based on BMI", examples=["Normal weight", "Overweight"])
    @property
    def verdict(self) -> str:
        """Determine the health status of the patient based on BMI."""
        bmi_value = self.bmi
        if bmi_value < 18.5:
            return "Underweight"
        elif 18.5 <= bmi_value < 24.9:
            return "Normal weight"
        elif 25 <= bmi_value < 29.9:
            return "Overweight"
        else:
            return "Obesity"


def load_data() -> list[dict[str, Any]]:
    """Load patient data from a JSON file."""
    with open('patients.json', 'r') as f:
        data = json.load(f)
        return data

def save_data(data: list[dict[str, Any]]) -> None:
    """Save patient data to a JSON file."""
    with open('patients.json', 'w') as f:
        json.dump(data, f)


@app.get('/patients')
def get_patients() -> list[Patient]:
    """Get the list of all patients."""
    data = load_data()
    return [Patient(**patient) for patient in data]

@app.post('/patients')
def create_patient(patient: Patient):
    """Create a new patient and save it to the JSON file."""
    data = load_data()
    if patient.id in [p['id'] for p in data]:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    data.append(patient.model_dump())
    save_data(data)
    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient": patient.model_dump()})