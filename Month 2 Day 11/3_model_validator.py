from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict

class Patient(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=120)
    weight: float = Field(..., gt=0)
    email: Optional[str] = None
    married: Optional[bool] = None
    medical_history: Optional[List[str]] = None
    emergency_contact: Optional[Dict[str, str]] = None

    @model_validator(mode='after')
    def validate_emergency_contact(cls, model):
        if model.emergency_contact:
            if 'name' not in model.emergency_contact or 'phone' not in model.emergency_contact:
                raise ValueError("Emergency contact must include both 'name' and 'phone'")
        return model
        