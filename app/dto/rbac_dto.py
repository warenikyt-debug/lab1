from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RoleDTO(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoleCollectionDTO(BaseModel):
    items: List[RoleDTO]
    total: int
    count: int


class PermissionDTO(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PermissionCollectionDTO(BaseModel):
    items: List[PermissionDTO]
    total: int
    count: int


class UserDTO(BaseModel):
    id: int
    username: str
    email: str
    birthday: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleDTO(BaseModel):
    id: int
    user_id: int
    role_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RolePermissionDTO(BaseModel):
    id: int
    role_id: int
    permission_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

