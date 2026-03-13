from datetime import datetime, timedelta
from typing import Dict, Optional, List
import jwt
import uuid
import hashlib
from app.config.settings import settings
from app.dto.auth_dto import TokenInfoDTO

class TokenService:
    """
    Сервис для работы с токенами
    Требование: самостоятельная реализация (не использовать готовые библиотеки целиком)
    """
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES
        self.max_tokens = settings.MAX_ACTIVE_TOKENS
        
        # Хранилище активных токенов (в реальном проекте - Redis/БД)
        self.active_tokens: Dict[str, dict] = {}  # token_id -> информация
        self.refresh_to_access: Dict[str, str] = {}  # refresh_token_id -> access_token_id
        self.user_tokens: Dict[int, List[str]] = {}  # user_id -> [token_ids]
        self.used_refresh_tokens: set = set()  # использованные refresh токены
    
    def _generate_token_id(self) -> str:
        """Генерация уникального ID токена"""
        return str(uuid.uuid4())
    
    def _create_jwt_token(self, user_id: int, token_type: str, ttl_minutes: int, token_id: str) -> str:
        """Создание JWT токена"""
        expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "token_id": token_id,
            "exp": expires.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_token_pair(self, user_id: int, ip_address: str = None) -> Dict[str, str]:
        """
        Создание пары токенов (доступа и обновления)
        С учетом лимита активных токенов
        """
        # Проверка лимита активных токенов
        if user_id in self.user_tokens:
            active_count = len([
                tid for tid in self.user_tokens[user_id] 
                if tid in self.active_tokens
            ])
            if active_count >= self.max_tokens:
                self._revoke_oldest_token(user_id)
        
        # Генерация ID токенов
        access_token_id = self._generate_token_id()
        refresh_token_id = self._generate_token_id()
        
        # Создание токенов
        access_token = self._create_jwt_token(user_id, "access", self.access_ttl, access_token_id)
        refresh_token = self._create_jwt_token(user_id, "refresh", self.refresh_ttl, refresh_token_id)
        
        # Сохранение информации о токенах (не сами токены!)
        now = datetime.utcnow()
        self.active_tokens[access_token_id] = {
            "user_id": user_id,
            "type": "access",
            "created_at": now,
            "expires_at": now + timedelta(minutes=self.access_ttl),
            "ip_address": ip_address
        }
        
        self.active_tokens[refresh_token_id] = {
            "user_id": user_id,
            "type": "refresh",
            "created_at": now,
            "expires_at": now + timedelta(minutes=self.refresh_ttl),
            "ip_address": ip_address
        }
        
        # Связывание токенов
        self.refresh_to_access[refresh_token_id] = access_token_id
        
        # Добавление в список пользователя
        if user_id not in self.user_tokens:
            self.user_tokens[user_id] = []
        self.user_tokens[user_id].extend([access_token_id, refresh_token_id])
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    def verify_token(self, token: str, expected_type: str = None) -> Optional[Dict]:
        """
        Проверка токена
        Возвращает payload если токен действителен
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            
            # Проверка типа токена
            if expected_type and payload.get("type") != expected_type:
                return None
            
            # Проверка, активен ли токен
            if token_id not in self.active_tokens:
                return None
            
            # Проверка срока действия
            exp = datetime.fromtimestamp(payload.get("exp"))
            if exp < datetime.utcnow():
                self.revoke_token(token_id)
                return None
            
            # Для refresh токенов проверяем, не использован ли он
            if expected_type == "refresh" and token_id in self.used_refresh_tokens:
                # Отзываем все токены пользователя (мера безопасности)
                user_id = payload.get("user_id")
                self.revoke_all_user_tokens(user_id)
                return None
            
            return payload
            
        except jwt.PyJWTError:
            return None
    
    def revoke_token(self, token_id: str):
        """Отзыв конкретного токена"""
        if token_id in self.active_tokens:
            user_id = self.active_tokens[token_id]["user_id"]
            del self.active_tokens[token_id]
            
            # Удаление из списка пользователя
            if user_id in self.user_tokens and token_id in self.user_tokens[user_id]:
                self.user_tokens[user_id].remove(token_id)
        
        # Удаление связей
        if token_id in self.refresh_to_access:
            del self.refresh_to_access[token_id]
    
    def revoke_all_user_tokens(self, user_id: int, exclude_token_id: str = None):
        """Отзыв всех токенов пользователя"""
        if user_id not in self.user_tokens:
            return
        
        tokens_to_revoke = self.user_tokens[user_id].copy()
        for token_id in tokens_to_revoke:
            if exclude_token_id and token_id == exclude_token_id:
                continue
            self.revoke_token(token_id)
    
    def _revoke_oldest_token(self, user_id: int):
        """Отзыв самого старого токена пользователя"""
        if user_id not in self.user_tokens:
            return
        
        oldest_token = None
        oldest_time = None
        
        for token_id in self.user_tokens[user_id]:
            if token_id in self.active_tokens:
                token_info = self.active_tokens[token_id]
                if token_info["type"] == "access":
                    if oldest_time is None or token_info["created_at"] < oldest_time:
                        oldest_time = token_info["created_at"]
                        oldest_token = token_id
        
        if oldest_token:
            self.revoke_token(oldest_token)
    
    def get_user_active_tokens(self, user_id: int) -> List[TokenInfoDTO]:
        """Получение списка активных токенов пользователя"""
        tokens = []
        if user_id in self.user_tokens:
            for token_id in self.user_tokens[user_id]:
                if token_id in self.active_tokens:
                    info = self.active_tokens[token_id]
                    tokens.append(TokenInfoDTO(
                        id=token_id,
                        created_at=info["created_at"],
                        expires_at=info["expires_at"],
                        ip_address=info.get("ip_address")
                    ))
        return tokens
    
    def refresh_tokens(self, refresh_token: str, ip_address: str = None) -> Optional[Dict[str, str]]:
        """
        Обновление пары токенов
        Требование: refresh токен одноразовый
        """
        # Проверка refresh токена
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        refresh_token_id = payload.get("token_id")
        user_id = payload.get("user_id")
        
        # Помечаем refresh токен как использованный
        self.used_refresh_tokens.add(refresh_token_id)
        
        # Отзываем старую пару
        self.revoke_token(refresh_token_id)
        if refresh_token_id in self.refresh_to_access:
            access_token_id = self.refresh_to_access[refresh_token_id]
            self.revoke_token(access_token_id)
        
        # Создаем новую пару
        return self.create_token_pair(user_id, ip_address)