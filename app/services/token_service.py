"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🔵 LAB2: AUTHENTICATION & JWT - Token Service                               ║
║                                                                              ║
║ Сервис для создания, проверки, и управления JWT токенами                   ║
║ Реализован как Singleton с собственной логикой (не готовые библиотеки)      ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
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
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES
        self.max_tokens = settings.MAX_ACTIVE_TOKENS
        
        # Хранилище активных токенов
        self.active_tokens: Dict[str, dict] = {}  # token_id -> информация
        self.refresh_to_access: Dict[str, str] = {}  # refresh_token_id -> access_token_id
        self.user_tokens: Dict[int, List[str]] = {}  # user_id -> [token_ids]
        self.used_refresh_tokens: set = set()  # использованные refresh токены
        
        # 🔥 ЧЕРНЫЙ СПИСОК - для отозванных токенов
        self.blacklisted_tokens: set = set()  # token_id которые больше не работают
        
        print("🔧 TokenService инициализирован (синглтон)")
        print(f"📊 Лимит токенов на пользователя: {self.max_tokens}")
        print(f"📊 Черный список: {len(self.blacklisted_tokens)} токенов")
        
        # Загружаем сохраненные токены из БД при старте
        self._load_tokens_from_db()
    
    def _load_tokens_from_db(self):
        """Загрузить активные токены из БД при старте сервера"""
        try:
            from app.config.database import SessionLocal
            from app.models.token import Token, TokenPair
            
            db = SessionLocal()
            try:
                # Загружаем все активные (не черные, не использованные) токены
                tokens = db.query(Token).filter(
                    Token.is_blacklisted == False
                ).all()
                
                now = datetime.utcnow()
                loaded_count = 0
                
                for token in tokens:
                    # Пропускаем истекшие токены
                    if token.expires_at < now:
                        continue
                    
                    self.active_tokens[token.id] = {
                        "user_id": token.user_id,
                        "type": token.token_type,
                        "created_at": token.created_at,
                        "expires_at": token.expires_at,
                        "ip_address": token.ip_address
                    }
                    
                    if token.user_id not in self.user_tokens:
                        self.user_tokens[token.user_id] = []
                    self.user_tokens[token.user_id].append(token.id)
                    
                    loaded_count += 1
                
                # Загружаем связи пар (refresh_token_id -> access_token_id)
                pairs = db.query(TokenPair).all()
                for pair in pairs:
                    # Проверяем что оба токена еще активны
                    if pair.access_token_id in self.active_tokens and pair.refresh_token_id in self.active_tokens:
                        self.refresh_to_access[pair.refresh_token_id] = pair.access_token_id
                
                print(f"✅ Загружено {loaded_count} активных токенов из БД")
                print(f"✅ Загружено {len(self.refresh_to_access)} пар токенов из БД")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке токенов из БД: {e}")
            print(f"⚠️ Продолжаю с пустым списком токенов")
    
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
        print(f"\n🔑 Создание токенов для user {user_id}")
        
        # Проверка лимита активных токенов
        if user_id in self.user_tokens:
            active_tokens = []
            for tid in self.user_tokens[user_id]:
                if tid in self.active_tokens and tid not in self.blacklisted_tokens:
                    token_info = self.active_tokens[tid]
                    if token_info["type"] == "access":
                        active_tokens.append(tid)
            
            active_count = len(active_tokens)
            print(f"📊 Активных access токенов: {active_count}, лимит: {self.max_tokens}")
            
            # Если превышен лимит, отзываем самый старый
            if active_count >= self.max_tokens:
                print(f"⚠️ Превышен лимит токенов ({self.max_tokens}), отзываем самый старый")
                self._revoke_oldest_token(user_id)
        
        # Генерация ID токенов
        access_token_id = self._generate_token_id()
        refresh_token_id = self._generate_token_id()
        
        # Создание токенов
        access_token = self._create_jwt_token(user_id, "access", self.access_ttl, access_token_id)
        refresh_token = self._create_jwt_token(user_id, "refresh", self.refresh_ttl, refresh_token_id)
        
        # Сохранение информации о токенах
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
        
        # Сохранение токенов в БД для persisency при перезагрузке сервера
        self._save_tokens_to_db(user_id, access_token_id, refresh_token_id, now, ip_address)
        
        print(f"✅ Токены созданы:")
        print(f"   - Access: {access_token_id[:8]}... (живет {self.access_ttl} мин)")
        print(f"   - Refresh: {refresh_token_id[:8]}... (живет {self.refresh_ttl} мин)")
        print(f"📊 Всего активных токенов: {len(self.active_tokens)}")
        print(f"📊 Черный список: {len(self.blacklisted_tokens)}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    def _save_tokens_to_db(self, user_id: int, access_token_id: str, refresh_token_id: str, 
                           created_at: datetime, ip_address: str = None):
        """Сохранить пару токенов в БД"""
        try:
            from app.config.database import SessionLocal
            from app.models.token import Token, TokenPair
            
            db = SessionLocal()
            try:
                # Проверяем что токены еще не в БД
                existing = db.query(Token).filter(Token.id == access_token_id).first()
                if existing:
                    return
                
                # Создаем записи токенов в БД
                access_expires = created_at + timedelta(minutes=self.access_ttl)
                refresh_expires = created_at + timedelta(minutes=self.refresh_ttl)
                
                access_token_db = Token(
                    id=access_token_id,
                    token_value=access_token_id,  # Храним ID как значение для быстрого поиска
                    token_type="access",
                    user_id=user_id,
                    created_at=created_at,
                    expires_at=access_expires,
                    ip_address=ip_address,
                    is_blacklisted=False
                )
                
                refresh_token_db = Token(
                    id=refresh_token_id,
                    token_value=refresh_token_id,
                    token_type="refresh",
                    user_id=user_id,
                    created_at=created_at,
                    expires_at=refresh_expires,
                    ip_address=ip_address,
                    is_blacklisted=False
                )
                
                db.add(access_token_db)
                db.add(refresh_token_db)
                db.flush()
                
                # Создаем связь пары
                token_pair = TokenPair(
                    access_token_id=access_token_id,
                    refresh_token_id=refresh_token_id,
                    user_id=user_id,
                    created_at=created_at
                )
                
                db.add(token_pair)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении токенов в БД: {e}")
    
    def verify_token(self, token: str, expected_type: str = None) -> Optional[Dict]:
        """
        Проверка токена
        Возвращает payload если токен действителен
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            token_type = payload.get("type")
            
            print(f"\n🔍 Проверка токена: {token_id[:8]}..., тип: {token_type}")
            
            # 🔥 ПРОВЕРКА ЧЕРНОГО СПИСКА - самый главный момент!
            if token_id in self.blacklisted_tokens:
                print(f"❌ ТОКЕН В ЧЕРНОМ СПИСКЕ! {token_id[:8]}...")
                return None
            
            # Проверка типа токена
            if expected_type and token_type != expected_type:
                print(f"❌ Неверный тип токена: ожидался {expected_type}, получен {token_type}")
                return None
            
            # Проверка, активен ли токен (для обратной совместимости)
            if token_id not in self.active_tokens and token_id not in self.blacklisted_tokens:
                print(f"❌ Токен {token_id[:8]}... не найден в active_tokens")
                return None
            
            # Проверка срока действия
            exp = datetime.fromtimestamp(payload.get("exp"))
            if exp < datetime.utcnow():
                print(f"❌ Токен истек: {exp}")
                self.revoke_token(token_id)
                return None
            
            # Для refresh токенов проверяем, не использован ли он
            if token_type == "refresh" and token_id in self.used_refresh_tokens:
                print(f"❌ Refresh токен уже использован, отзываем все токены пользователя")
                user_id = payload.get("user_id")
                self.revoke_all_user_tokens(user_id)
                return None
            
            print(f"✅ Токен действителен")
            return payload
            
        except jwt.PyJWTError as e:
            print(f"❌ Ошибка JWT: {e}")
            return None
    
    def revoke_token(self, token_id: str):
        """Отзыв конкретного токена - добавляем в черный список"""
        print(f"\n🔴🔴🔴 REVOKE_TOKEN ДЛЯ: {token_id[:8]}...")
        
        # 🔥 ДОБАВЛЯЕМ В ЧЕРНЫЙ СПИСОК
        self.blacklisted_tokens.add(token_id)
        print(f"✅ Токен {token_id[:8]}... добавлен в черный список")
        
        # Также удаляем из active_tokens если есть
        if token_id in self.active_tokens:
            user_id = self.active_tokens[token_id]["user_id"]
            token_type = self.active_tokens[token_id]["type"]
            
            del self.active_tokens[token_id]
            print(f"✅ Токен удален из active_tokens")
            
            # Удаление из списка пользователя
            if user_id in self.user_tokens and token_id in self.user_tokens[user_id]:
                self.user_tokens[user_id].remove(token_id)
                print(f"✅ Токен удален из user_tokens[{user_id}]")
            
            # Если это refresh токен, удаляем связь
            if token_id in self.refresh_to_access:
                del self.refresh_to_access[token_id]
                print(f"✅ Удалена связь refresh_to_access")
        
        # Обновляем статус в БД
        self._blacklist_token_in_db(token_id)
        
        print(f"📊 Черный список теперь: {len(self.blacklisted_tokens)} токенов")
        print(f"📊 Активных токенов: {len(self.active_tokens)}")
    
    def _blacklist_token_in_db(self, token_id: str):
        """Добавить токен в черный список в БД"""
        try:
            from app.config.database import SessionLocal
            from app.models.token import Token
            
            db = SessionLocal()
            try:
                token = db.query(Token).filter(Token.id == token_id).first()
                if token:
                    token.is_blacklisted = True
                    token.blacklisted_at = datetime.utcnow()
                    db.commit()
                    print(f"✅ Токен {token_id[:8]}... отмечен в БД как черный")
            finally:
                db.close()
        except Exception as e:
            print(f"⚠️ Ошибка при обновлении токена в БД: {e}")
    
    def revoke_token_pair(self, token_id: str):
        """
        Отзыв пары токенов (access + refresh) одновременно
        Используется при logout - удаляет оба токена из пары
        """
        print(f"\n🔴🔴🔴 REVOKE_TOKEN_PAIR ДЛЯ: {token_id[:8]}...")
        
        paired_token_id = None
        
        # Если это refresh токен, найти его access токен
        if token_id in self.refresh_to_access:
            paired_token_id = self.refresh_to_access[token_id]
            print(f"✅ Это refresh токен, найден парный access: {paired_token_id[:8]}...")
        else:
            # Если это access токен, найти его refresh токен
            for refresh_id, access_id in self.refresh_to_access.items():
                if access_id == token_id:
                    paired_token_id = refresh_id
                    print(f"✅ Это access токен, найден парный refresh: {paired_token_id[:8]}...")
                    break
        
        # Отзываем оба токена
        self.revoke_token(token_id)
        if paired_token_id:
            self.revoke_token(paired_token_id)
        
        print(f"✅ Пара токенов отозвана")
    
    def revoke_all_user_tokens(self, user_id: int, exclude_token_id: str = None):
        """Отзыв всех токенов пользователя"""
        print(f"\n🔴 Отзыв всех токенов для user {user_id}")
        print(f"🚫 Исключая: {exclude_token_id[:8] if exclude_token_id else 'нет'}")
        
        if user_id not in self.user_tokens:
            print(f"📊 У пользователя {user_id} нет токенов")
            return
        
        tokens_to_revoke = self.user_tokens[user_id].copy()
        revoked_count = 0
        
        for token_id in tokens_to_revoke:
            if exclude_token_id and token_id == exclude_token_id:
                print(f"⏭️ Пропускаем текущий токен: {token_id[:8]}...")
                continue
            self.revoke_token(token_id)
            revoked_count += 1
        
        print(f"✅ Отозвано токенов: {revoked_count}")
        print(f"📊 Черный список: {len(self.blacklisted_tokens)}")
    
    def _revoke_oldest_token(self, user_id: int):
        """Отзыв самого старого токена пользователя (только access токены)"""
        if user_id not in self.user_tokens:
            return
        
        oldest_token = None
        oldest_time = None
        
        # Ищем самый старый access токен
        for token_id in self.user_tokens[user_id]:
            if token_id in self.active_tokens and token_id not in self.blacklisted_tokens:
                token_info = self.active_tokens[token_id]
                if token_info["type"] == "access":
                    if oldest_time is None or token_info["created_at"] < oldest_time:
                        oldest_time = token_info["created_at"]
                        oldest_token = token_id
        
        if oldest_token:
            print(f"📉 Отзыв самого старого access токена: {oldest_token[:8]}...")
            self.revoke_token(oldest_token)
            
            # Также отзываем связанный refresh токен, если есть
            for refresh_id, access_id in self.refresh_to_access.items():
                if access_id == oldest_token:
                    print(f"📉 Отзыв связанного refresh токена: {refresh_id[:8]}...")
                    self.revoke_token(refresh_id)
                    break
    
    def get_user_active_tokens(self, user_id: int) -> List[TokenInfoDTO]:
        """Получение списка активных токенов пользователя (исключая черный список и использованные refresh токены)"""
        tokens = []
        # Проходим по ВСЕМ активным токенам и фильтруем по user_id
        for token_id, info in self.active_tokens.items():
            # Пропускаем если токен в черном списке
            if token_id in self.blacklisted_tokens:
                continue
            
            # Пропускаем если это использованный refresh токен (одноразовый)
            if info["type"] == "refresh" and token_id in self.used_refresh_tokens:
                continue
            
            # Добавляем только токены текущего пользователя
            if info["user_id"] == user_id:
                tokens.append(TokenInfoDTO(
                    token_value=token_id,
                    token_type=info["type"],
                    created_at=info["created_at"],
                    expires_at=info["expires_at"],
                    ip_address=info.get("ip_address")
                ))
        return tokens
    
    def refresh_tokens(self, refresh_token: str, ip_address: str = None) -> Optional[Dict[str, str]]:
        """
        Обновление пары токенов
        Поведение:
        - Проверяет refresh токен (валиден, не в черном списке, не использован)
        - Отзывает ВСЕ старые токены (все access + refresh)
        - Создает новую пару (новые access + refresh)
        - Refresh токен одноразовый
        """
        print(f"\n🔄 Обновление токенов по refresh токену")
        
        # Проверка refresh токена
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            print("❌ Refresh токен недействителен")
            return None
        
        refresh_token_id = payload.get("token_id")
        user_id = payload.get("user_id")
        
        print(f"✅ Refresh токен действителен для user {user_id}")
        print(f"🆔 Refresh ID: {refresh_token_id[:8]}...")
        print(f"📊 ПЕРЕД REVOKE: user_tokens[{user_id}] = {len(self.user_tokens.get(user_id, []))} токенов")
        
        # Помечаем этот refresh токен как использованный (одноразовый)
        self.used_refresh_tokens.add(refresh_token_id)
        print(f"📝 Refresh токен помечен как одноразово использованный")
        
        # Отзываем ВСЕ старые токены пользователя
        if user_id in self.user_tokens:
            tokens_to_revoke = list(self.user_tokens[user_id])
            for token_id in tokens_to_revoke:
                self.revoke_token(token_id)
            print(f"✅ Все старые токены отозваны ({len(tokens_to_revoke)} шт)")
        
        print(f"📊 ПОСЛЕ REVOKE: user_tokens[{user_id}] = {len(self.user_tokens.get(user_id, []))} токенов")
        print(f"📊 Черный список: {len(self.blacklisted_tokens)} токенов")
        
        # ЯВНО очищаем список
        if user_id in self.user_tokens:
            self.user_tokens[user_id] = []
        
        # Создаем новую пару
        print(f"🆕 Создаем новую пару токенов")
        result = self.create_token_pair(user_id, ip_address)
        print(f"📊 ПОСЛЕ CREATE: user_tokens[{user_id}] = {len(self.user_tokens.get(user_id, []))} токенов")
        return result

# Создаем ЕДИНСТВЕННЫЙ экземпляр для всего приложения
token_service = TokenService()