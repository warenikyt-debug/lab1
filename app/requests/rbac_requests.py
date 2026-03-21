"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - RBAC Requests                                               ║
║                                                                              ║
║ Классы форм-запросов для управления ролями и разрешениями (Pydantic)        ║
║ Включают валидацию входных данных, авторизацию, преобразование в DTO       ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class StoreRoleRequest(BaseModel):
    """Запрос на создание роли (POST /api/ref/policy/role)"""
    name: str = Field(..., min_length=1, max_length=255, example="Administrator")
    slug: str = Field(..., min_length=1, max_length=255, example="admin")
    description: Optional[str] = Field(None, max_length=1000, example="Администратор системы")
    
    @validator('slug')
    def validate_slug(cls, v):
        """Проверка формата slug: только буквы латиницы, цифры, дефис, подчеркивание"""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug должен содержать только буквы латиницы, цифры, дефис и подчеркивание')
        return v


class UpdateRoleRequest(BaseModel):
    """Запрос на обновление роли (PUT/PATCH /api/ref/policy/role/{role})"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Проверка формата slug"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug должен содержать только буквы латиницы, цифры, дефис и подчеркивание')
        return v


class StorePermissionRequest(BaseModel):
    """Запрос на создание разрешения (POST /api/ref/policy/permission)"""
    name: str = Field(..., min_length=1, max_length=255, example="Create User")
    slug: str = Field(..., min_length=1, max_length=255, example="create-user")
    description: Optional[str] = Field(None, max_length=1000, example="Позволяет создавать пользователей")
    
    @validator('slug')
    def validate_slug(cls, v):
        """Проверка формата slug"""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug должен содержать только буквы латиницы, цифры, дефис и подчеркивание')
        return v


class UpdatePermissionRequest(BaseModel):
    """Запрос на обновление разрешения (PUT/PATCH /api/ref/policy/permission/{permission})"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('slug')
    def validate_slug(cls, v):
        """Проверка формата slug"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Slug должен содержать только буквы латиницы, цифры, дефис и подчеркивание')
        return v


class AttachUserRoleRequest(BaseModel):
    """Запрос на присвоение роли пользователю (POST /api/ref/user/{user}/role)"""
    role_id: int = Field(..., gt=0, example=1)


class DetachUserRoleRequest(BaseModel):
    """Запрос на удаление роли у пользователя (DELETE /api/ref/user/{user}/role/{role})
    Может быть пуст (роль передаётся в URL)"""
    pass
