"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - RBAC Requests                                               ║
║                                                                              ║
║ Классы форм-запросов для управления ролями и разрешениями (Pydantic)        ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class StoreRoleRequest(BaseModel):
    """Запрос на создание роли"""
    name: str = Field(..., min_length=1, max_length=255, example="Administrator")
    slug: str = Field(..., min_length=1, max_length=255, example="admin")
    description: Optional[str] = Field(None, max_length=1000, example="System administrator")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug must contain only letters, numbers, dash and underscore')
        return v


class UpdateRoleRequest(BaseModel):
    """Запрос на обновление роли"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('slug')
    def validate_slug(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug must contain only letters, numbers, dash and underscore')
        return v


class StorePermissionRequest(BaseModel):
    """Запрос на создание разрешения"""
    name: str = Field(..., min_length=1, max_length=255, example="Create User")
    slug: str = Field(..., min_length=1, max_length=255, example="create-user")
    description: Optional[str] = Field(None, max_length=1000, example="Allows user creation")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug must contain only letters, numbers, dash and underscore')
        return v


class UpdatePermissionRequest(BaseModel):
    """Запрос на обновление разрешения"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('slug')
    def validate_slug(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug must contain only letters, numbers, dash and underscore')
        return v


class AttachUserRoleRequest(BaseModel):
    """Запрос на присвоение роли пользователю"""
    role_id: int = Field(..., gt=0, example=1)


class DetachUserRoleRequest(BaseModel):
    """Запрос на удаление роли у пользователя"""
    pass
