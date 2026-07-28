import json

from fastapi import FastAPI, HTTPException 
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Any, Optional
from pydantic import BaseModel, Field, computed_field

app = FastAPI()


class Patient(BaseModel):
    id: Annotated[str, Field(...,description="The unique identifier for the patient")]
    name: Annotated[str, Field(...,description="The name of the patient")]
    city: Annotated[str, Field(...,description="The city where the patient resides")]
    age: Annotated[int, Field(...,description='The age of the patient', gt=0, lt=120, examples=[25, 30, 45])]
    gender: Annotated[Literal['Male','Female'], Field(...,description='The gender of the patient', examples=['Male', 'Female'])]
    height: Annotated[float, Field(...,description='The height of the patient in meters', gt=0, examples=[1.705, 1.802])]
    weight: Annotated[float, Field(...,description='The weight of the patient in kilograms', gt=0, examples=[70.5, 80.2])]

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

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None, description="The name of the patient")]
    city: Annotated[Optional[str], Field(default=None, description="The city where the patient resides")]
    age: Annotated[Optional[int], Field(default=None, description='The age of the patient', gt=0, lt=120, examples=[25, 30, 45])]
    gender: Annotated[Optional[Literal['Male', 'Female']], Field(default=None, description='The gender of the patient', examples=['Male', 'Female'])]
    height: Annotated[Optional[float], Field(default=None, description='The height of the patient in meters', gt=0, examples=[1.705, 1.802])]
    weight: Annotated[Optional[float], Field(default=None, description='The weight of the patient in kilograms', gt=0, examples=[70.5, 80.2])]



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




@app.put('/patients/{patient_id}')
def update_patient(patient_id : str, patient_update : PatientUpdate): 
    data = load_data()

    existing_patient = next((p for p in data if p['id'] == patient_id), None)
    if existing_patient is None:
        raise HTTPException(status_code=404, detail='Patient not found')

    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    if 'id' in updated_patient_info and updated_patient_info['id'] != patient_id:
        raise HTTPException(status_code=400, detail='Cannot change patient ID')

    for key, value in updated_patient_info.items():
        if key == 'id':
            continue
        existing_patient[key] = value

    existing_patient_obj = Patient(**existing_patient)
    patient_index = data.index(existing_patient)
    data[patient_index] = existing_patient_obj.model_dump()

    save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient updated successfully", "patient": existing_patient_obj.model_dump()}) 




@app.delete('/patients/{patient_id}')
def delete_patient(patient_id: str):
    """Delete a patient by ID."""
    data = load_data()
    existing_patient = next((p for p in data if p['id'] == patient_id), None)
    if existing_patient is None:
        raise HTTPException(status_code=404, detail='Patient not found')

    data.remove(existing_patient)
    save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully", "patient": existing_patient})