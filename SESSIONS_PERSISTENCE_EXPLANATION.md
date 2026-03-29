# Реализация Активных Сессий и Персистентности Токенов

## 1. АРХИТЕКТУРА

### Компонент 1: Максимум 1 активная сессия на пользователя

**Как работает:**
1. При логине проверяется количество активных сеансов (пар токенов)
2. Если лимит достигнут, старая сессия автоматически удаляется
3. Новая сессия создается и становится единственной активной

**Где это реализовано:**
- `TokenService._get_user_active_sessions()` - подсчитывает активные сеансы
- `TokenService._revoke_oldest_session()` - удаляет самый старый сеанс
- `TokenService.create_token_pair()` - проверяет лимит при создании

```
Логин #1 (Device A)  → 1 активная сеанс
Логин #2 (Device B)  → Device A автоматически выходит, 1 активная сеанс
```

### Компонент 2: Остаться залогиненым после перезагрузки сервера

**Как работает:**
1. При создании пары токенов они сохраняются в SQLite БД
2. При перезагрузке сервера токены загружаются из БД в памяти
3. Токены становятся активными и доступными для использования

**Где это реализовано:**
- `TokenService._load_tokens_from_db()` - загружает токены при инициализации
- `TokenService._save_tokens_to_db()` - сохраняет при создании токенов
- `TokenService._blacklist_token_in_db()` - отмечает как удаленные при logout

---

## 2. ПОДРОБНОЕ ОБЪЯСНЕНИЕ

### A. Максимум активных сеансов (MAX_ACTIVE_TOKENS = 1)

#### Структуры данных в TokenService:

```python
# Основные структуры
self.active_tokens: Dict[str, dict]      # {token_id -> {type, user_id, created_at, ...}}
self.refresh_to_access: Dict[str, str]   # {refresh_id -> access_id}  (пара!)
self.user_tokens: Dict[int, List[str]]   # {user_id -> [token_ids]}
self.blacklisted_tokens: set             # {revoked_token_ids}
```

#### Счет активных сеансов:

```python
def _get_user_active_sessions(self, user_id: int) -> List[Dict]:
    """Возвращает список активных сеансов (пар токенов)"""
    sessions = []
    
    # Для каждого токена пользователя:
    for token_id in self.user_tokens[user_id]:
        # Если это активный refresh токен (не в черном списке)
        if token_id in self.active_tokens and token_id not in self.blacklisted_tokens:
            token_info = self.active_tokens[token_id]
            if token_info["type"] == "refresh":  # Refresh = это сеанс!
                # Находим парный access токен
                access_token_id = self.refresh_to_access[token_id]
                sessions.append({
                    "refresh_token_id": token_id,
                    "access_token_id": access_token_id,
                    "created_at": token_info["created_at"]
                })
    
    return sessions  # Список всех сеансов
```

**Почему считаем именно refresh токены?**
- Каждый сеанс = пара (access + refresh)
- Refresh токен = маркер сеанса
- Один refresh токен → одна сеанс

#### Удаление старой сеанса:

```python
def _revoke_oldest_session(self, user_id: int):
    """Удаляет самый старый сеанс"""
    sessions = self._get_user_active_sessions(user_id)
    
    # Находим самый старый по created_at
    oldest = min(sessions, key=lambda s: s["created_at"])
    
    # Отзываем ОБЕИХ токена из пары
    self.revoke_token_pair(oldest["access_token_id"])
    # revoke_token_pair() отзывает и access и refresh сразу!
```

#### При логине:

```python
def create_token_pair(self, user_id, ip_address=None):
    # Подсчитываем активные сеансы
    active_sessions = self._get_user_active_sessions(user_id)
    
    # Если количество >= лимита
    if len(active_sessions) >= self.max_tokens:  # max_tokens = 1
        # Удаляем самый старый
        self._revoke_oldest_session(user_id)
    
    # Создаем новую пару
    access_token = self._create_jwt_token(...)
    refresh_token = self._create_jwt_token(...)
    
    # ... сохраняем в БД
    self._save_tokens_to_db(...)
```

---

### B. Персистентность токенов (остаться залогиненым после перезагрузки)

#### При СОЗДАНИИ токенов:

```python
def _save_tokens_to_db(self, user_id, access_id, refresh_id, created_at, ip):
    """Сохраняет токены в SQLite"""
    
    # Создаем записи в таблице Token
    Token(
        id=access_id,              # UUID
        token_value=access_id,     # Для быстрого поиска
        token_type="access",
        user_id=user_id,
        created_at=created_at,
        expires_at=created_at + 60min,
        is_blacklisted=False       # Не удален
    )
    
    Token(
        id=refresh_id,
        token_type="refresh",
        ...
        expires_at=created_at + 7 days,
        is_blacklisted=False
    )
    
    # Создаем запись в таблице TokenPair (связь!)
    TokenPair(
        access_token_id=access_id,
        refresh_token_id=refresh_id,
        user_id=user_id,
        created_at=created_at
    )
```

#### При ПЕРЕЗАГРУЗКЕ сервера:

```python
def _load_tokens_from_db(self):
    """Загружается при инициализации TokenService"""
    
    db = SessionLocal()
    
    # 1. Загружаем все активные токены из БД
    tokens = db.query(Token).filter(
        Token.is_blacklisted == False  # Только не удаленные
    ).all()
    
    for token in tokens:
        # Пропускаем истекшие
        if token.expires_at < now:
            continue
        
        # Восстанавливаем в памяти
        self.active_tokens[token.id] = {
            "user_id": token.user_id,
            "type": token.token_type,
            "created_at": token.created_at,
            "expires_at": token.expires_at,
            ...
        }
        
        self.user_tokens[user_id].append(token.id)
    
    # 2. Восстанавливаем связи пар
    pairs = db.query(TokenPair).all()
    for pair in pairs:
        # Если оба токена все еще активны
        if pair.access_id in active_tokens and pair.refresh_id in active_tokens:
            self.refresh_to_access[pair.refresh_id] = pair.access_id
```

#### При УДАЛЕНИИ токенов (logout):

```python
def _blacklist_token_in_db(self, token_id):
    """Отмечает токен как удаленный в БД"""
    
    token = db.query(Token).filter(Token.id == token_id).first()
    if token:
        token.is_blacklisted = True  # Отметили
        token.blacklisted_at = now
        db.commit()
```

---

## 3. МОДЕЛИ БД

### Token таблица:
```
id (UUID)
token_value (UUID)        # Для быстрого поиска
token_type ('access' / 'refresh')
user_id (FK)
created_at
expires_at
ip_address
is_blacklisted (bool)     # Ключ для персистентности!
blacklisted_at
```

### TokenPair таблица:
```
id (auto)
access_token_id (FK)      # Ключ для связи
refresh_token_id (FK)     # Ключ для связи
user_id (FK)
created_at
```

---

## 4. ПОТОК ДАННЫХ

### Сценарий: Пользователь залогинился, сервер упал, сервер запустился

```
1. ЛОГИН (Device A)
   └─ POST /login
      └─ create_token_pair(user_id=1)
         ├─ Подсчет: 0 активных сеансов < 1 (лимит)
         ├─ Создание: access_id = UUID1, refresh_id = UUID2
         ├─ Память:
         │  ├─ active_tokens[UUID1] = {type: access, user_id: 1, ...}
         │  ├─ active_tokens[UUID2] = {type: refresh, user_id: 1, ...}
         │  ├─ refresh_to_access[UUID2] = UUID1
         │  └─ user_tokens[1] = [UUID1, UUID2]
         └─ БД:
            ├─ INSERT Token(id=UUID1, type='access', is_blacklisted=0)
            ├─ INSERT Token(id=UUID2, type='refresh', is_blacklisted=0)
            └─ INSERT TokenPair(access_id=UUID1, refresh_id=UUID2)

2. ИСПОЛЬЗОВАНИЕ
   └─ GET /me + Authorization: Bearer JWT(UUID1)
      └─ verify_token() проверяет: UUID1 NOT IN blacklisted_tokens ✅

3. СЕРВЕР ПАДАЕТ

4. СЕРВЕР ЗАПУСКАЕТСЯ
   └─ TokenService.__init__()
      └─ _load_tokens_from_db()
         ├─ SELECT * FROM Token WHERE is_blacklisted=0
         │  └─ Находит: UUID1, UUID2
         ├─ Восстанавливает в памяти:
         │  ├─ active_tokens[UUID1] = {type: access, ...}
         │  ├─ active_tokens[UUID2] = {type: refresh, ...}
         │  └─ user_tokens[1] = [UUID1, UUID2]
         ├─ SELECT * FROM TokenPair
         │  └─ Восстанавливает: refresh_to_access[UUID2] = UUID1
         └─ Консоль: "✅ Loaded 2 active tokens from DB"

5. ИСПОЛЬЗОВАНИЕ (ПОСЛЕ ПЕРЕЗАГРУЗКИ)
   └─ GET /me + Authorization: Bearer JWT(UUID1)
      └─ verify_token() проверяет: UUID1 NOT IN blacklisted_tokens ✅
         └─ РАБОТАЕТ! 🎉
```

---

## 5. КОНФИГУРАЦИЯ

```
.env файл:
MAX_ACTIVE_TOKENS=1        # Максимум 1 активный сеанс на пользователя
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080  # 7 дней
```

---

## 6. ИТОГОВАЯ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────────────┐
│                      TokenService                           │
│                      (Singleton)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  В ПАМЯТИ:                                                 │
│  ├─ active_tokens[token_id] = {info}                      │
│  ├─ refresh_to_access[refresh_id] = access_id (пара!)     │
│  ├─ user_tokens[user_id] = [token_ids]                    │
│  └─ blacklisted_tokens = {deleted_ids}                    │
│                                                             │
│  ↓↑ ЗАГРУЖАЕТ/СОХРАНЯЕТ ↓↑                                 │
│                                                             │
│  В БД (SQLite):                                            │
│  ├─ Token таблица (id, type, user_id, is_blacklisted)    │
│  └─ TokenPair таблица (access_id, refresh_id)  ← СВЯЗЬ   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. ПРИМЕР ЛОГОВ

```
🔑 Создание токенов для user 1
📊 Активных сеансов: 0, лимит: 1
✅ Токены созданы:
   - Access: a1b2c3d4... (живет 60 мин)
   - Refresh: e5f6g7h8... (живет 10080 мин)

🔑 Создание токенов для user 1 (2-й логин)
📊 Активных сеансов: 1, лимит: 1
⚠️ Превышен лимит сеансов (1), отзываем самый старый
📉 Отзыв старого сеанса:
   Access: a1b2c3d4...
   Refresh: e5f6g7h8...
🔴 REVOKE_TOKEN_PAIR для: a1b2c3d4...
✅ Токен отозван и добавлен в черный список

✅ Загружено 2 активных токенов из БД
✅ Загружено 1 пар токенов из БД
```
