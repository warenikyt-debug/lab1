from pydantic import BaseModel
from datetime import datetime, date  
from typing import List, Optional
from .user_dto import UserDTO

class LoginDTO(BaseModel):
    username: str
    password: str
    class Config:
        frozen = True

class RegisterDTO(BaseModel):
    username: str
    email: str
    password: str
    birthday: date 
    class Config:
        frozen = True

class AuthSuccessDTO(BaseModel):
    access_token: str
    refresh_token: str
    user: UserDTO
    class Config:
        frozen = True

class TokenInfoDTO(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    class Config:
        frozen = True

class TokenListDTO(BaseModel):
    tokens: List[TokenInfoDTO]
    class Config:
        frozen = True