from datetime import datetime, date  # ВАЖНО: добавить date
from typing import Dict, Optional
from passlib.context import CryptContext

# Для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User:
    """Модель пользователя"""
    def __init__(
        self, 
        id: int, 
        username: str, 
        email: str, 
        password_hash: str, 
        birthday: date  # теперь date определен
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.birthday = birthday
        self.created_at = datetime.now()
        self.updated_at = None
    
    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(password, self.password_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)

# Временное хранилище (пока без БД)
users_db: Dict[int, User] = {}  # id -> User
users_by_username: Dict[str, int] = {}  # username.lower() -> id
users_by_email: Dict[str, int] = {}  # email.lower() -> id
user_id_counter = 1