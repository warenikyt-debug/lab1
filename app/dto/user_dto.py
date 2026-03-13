from pydantic import BaseModel, EmailStr
from datetime import date, datetime  # оба импорта

class UserDTO(BaseModel):
    id: int
    username: str
    email: EmailStr
    birthday: date
    created_at: datetime
    
    class Config:
        frozen = True