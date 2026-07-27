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

    @computed_field()
    @property
    def bmi(self) -> Optional[float]:
        if self.weight and self.age:
            # Assuming height is a constant for simplicity, in real scenarios, height should be a field
            height_meters = 1.75  # Example height in meters
            return self.weight / (height_meters ** 2)
        return None


    