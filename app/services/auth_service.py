from datetime import date
from typing import Optional, Dict
from app.models.user import User, users_db, users_by_username, users_by_email, user_id_counter
from app.dto.user_dto import UserDTO
from app.dto.auth_dto import RegisterDTO
from app.services.token_service import TokenService

class AuthService:
    """
    Сервис аутентификации
    """
    def __init__(self):
        self.token_service = TokenService()
    
    def register(self, data: RegisterDTO) -> UserDTO:
        """
        Регистрация нового пользователя
        """
        global user_id_counter
        
        # Проверка уникальности username (без учета регистра)
        if data.username.lower() in users_by_username:
            raise ValueError("Пользователь с таким именем уже существует")
        
        # Проверка уникальности email (без учета регистра)
        if data.email.lower() in users_by_email:
            raise ValueError("Пользователь с таким email уже существует")
        
        # Создание пользователя
        user = User(
            id=user_id_counter,
            username=data.username,
            email=data.email,
            password_hash=User.hash_password(data.password),
            birthday=data.birthday
        )
        
        # Сохранение
        users_db[user_id_counter] = user
        users_by_username[data.username.lower()] = user_id_counter
        users_by_email[data.email.lower()] = user_id_counter
        
        user_id_counter += 1
        
        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            birthday=user.birthday,
            created_at=user.created_at
        )
    
    def login(self, username: str, password: str, ip_address: str = None) -> Optional[Dict]:
        """
        Авторизация пользователя
        """
        # Поиск пользователя
        username_lower = username.lower()
        if username_lower not in users_by_username:
            return None
        
        user_id = users_by_username[username_lower]
        user = users_db[user_id]
        
        # Проверка пароля
        if not user.verify_password(password):
            return None
        
        # Создание токенов
        tokens = self.token_service.create_token_pair(user_id, ip_address)
        
        return {
            **tokens,
            "user": UserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                birthday=user.birthday,
                created_at=user.created_at
            )
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return users_db.get(user_id)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Смена пароля
        """
        user = users_db.get(user_id)
        if not user:
            return False
        
        # Проверка текущего пароля
        if not user.verify_password(current_password):
            return False
        
        # Смена пароля
        user.password_hash = User.hash_password(new_password)
        user.updated_at = date.today()
        
        return True