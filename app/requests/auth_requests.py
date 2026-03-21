"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🔵 LAB2: AUTHENTICATION & JWT - Auth Requests                               ║
║                                                                              ║
║ Классы форм-запросов для аутентификации (Pydantic)                          ║
║ Включают валидацию и преобразование в DTO                                   ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import date
import re
from ..dto.auth_dto import LoginDTO, RegisterDTO

class LoginRequest(BaseModel):
    username: str = Field(..., example="TestUser1")
    password: str = Field(..., example="Test123!@#")
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match("^[A-Z][a-zA-Z0-9]*$", v):
            raise ValueError('Должно начинаться с заглавной буквы и содержать только латиницу и цифры')
        if len(v) < 7:
            raise ValueError('Минимум 7 символов')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        errors = []
        if len(v) < 8: 
            errors.append('8+ символов')
        if not any(c.isdigit() for c in v): 
            errors.append('цифру')
        if not any(not c.isalnum() for c in v): 
            errors.append('спецсимвол')
        if not any(c.isupper() for c in v): 
            errors.append('заглавную букву')
        if not any(c.islower() for c in v): 
            errors.append('строчную букву')
        if errors:
            raise ValueError(f'Пароль должен содержать: {", ".join(errors)}')
        return v
    
    def to_dto(self) -> LoginDTO:
        return LoginDTO(username=self.username, password=self.password)

class RegisterRequest(BaseModel):
    username: str = Field(..., 
        min_length=7,
        example="TestUser1",
        description="Имя пользователя: с заглавной буквы, только латиница и цифры, мин 7 символов"
    )
    email: EmailStr = Field(..., 
        example="user@example.com",
        description="Email: должен быть уникальным"
    )
    password: str = Field(..., 
        example="Test123!@#",
        description="Пароль: мин 8 символов, заглавная, цифра, спецсимвол"
    )
    c_password: str = Field(..., 
        example="Test123!@#",
        description="Подтверждение пароля"
    )
    birthday: date = Field(..., 
        example="2000-01-01",
        description="Дата рождения: возраст >= 14 лет"
    )
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match("^[A-Z][a-zA-Z0-9]*$", v):
            raise ValueError('Должно начинаться с заглавной буквы и содержать только латиницу и цифры')
        if len(v) < 7:
            raise ValueError('Минимум 7 символов')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        errors = []
        if len(v) < 8: 
            errors.append('8+ символов')
        if not any(c.isdigit() for c in v): 
            errors.append('цифру')
        if not any(not c.isalnum() for c in v): 
            errors.append('спецсимвол')
        if not any(c.isupper() for c in v): 
            errors.append('заглавную букву')
        if not any(c.islower() for c in v): 
            errors.append('строчную букву')
        if errors:
            raise ValueError(f'Пароль должен содержать: {", ".join(errors)}')
        return v
    
    @validator('c_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v
    
    @validator('birthday')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14:
            raise ValueError('Возраст должен быть не менее 14 лет')
        return v
    
    def to_dto(self) -> RegisterDTO:
        return RegisterDTO(
            username=self.username,
            email=self.email,
            password=self.password,
            birthday=self.birthday
        )

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., example="OldPass123!@#")
    new_password: str = Field(..., example="NewPass123!@#")
    confirm_password: str = Field(..., example="NewPass123!@#")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        errors = []
        if len(v) < 8: 
            errors.append('8+ символов')
        if not any(c.isdigit() for c in v): 
            errors.append('цифру')
        if not any(not c.isalnum() for c in v): 
            errors.append('спецсимвол')
        if not any(c.isupper() for c in v): 
            errors.append('заглавную букву')
        if not any(c.islower() for c in v): 
            errors.append('строчную букву')
        if errors:
            raise ValueError(f'Новый пароль должен содержать: {", ".join(errors)}')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Пароли не совпадают')
        return v