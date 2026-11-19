from pydantic import BaseModel
from typing import Optional


class StudentCreate(BaseModel):
    name: str
    qualification: str
    age: Optional[int] = None
    target_exam: Optional[str] = None
    preparation_level: str
    study_hours: float
    interested_field: Optional[str] = None
    subject_preferences: Optional[str] = None
    learning_preferences: Optional[str] = None


class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True