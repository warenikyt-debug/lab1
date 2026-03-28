## 📋 ПЛАН ПОЛНОЙ РЕАЛИЗАЦИИ ТОКЕН-СИСТЕМЫ С БД

### Текущий статус:
- ✅ **MAX_ACTIVE_TOKENS = 2** (2 пары токенов максимум)
- ✅ **Access и Refresh связаны** через `refresh_to_access` словарь
- ⚠️ **Токены хранятся в памяти** (теряются при перезагрузке)

---

## ❌ ЧТО НУЖНО СДЕЛАТЬ

### 1. **Создать таблицы в БД** ✨
```sql
CREATE TABLE tokens (
    id TEXT PRIMARY KEY,              -- UUID токена
    token_value TEXT NOT NULL,        -- Сам JWT токен
    token_type TEXT,                  -- 'access' или 'refresh'
    user_id INTEGER NOT NULL,         -- FK на пользователя
    created_at DATETIME,              -- Когда создан
    expires_at DATETIME,              -- Когда истекает
    ip_address TEXT,                  -- IP адрес
    is_blacklisted BOOLEAN DEFAULT 0, -- В черном списке?
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE token_pairs (
    id INTEGER PRIMARY KEY,           -- Пара токенов
    access_token_id TEXT,             -- FK на access
    refresh_token_id TEXT,            -- FK на refresh
    user_id INTEGER NOT NULL,         -- FK на пользователя
    created_at DATETIME,              -- Когда создана пара
    FOREIGN KEY (access_token_id) REFERENCES tokens(id),
    FOREIGN KEY (refresh_token_id) REFERENCES tokens(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2. **Модели ORM** ✨
Уже созданы в:
- `/workspaces/lab1/app/models/token.py` - Token и TokenPair модели
- `/workspaces/lab1/app/repositories/token_repository.py` - Репозиторий

### 3. **TokenService: Сохранять в БД** 🔧
Нужно обновить `app/services/token_service.py`:

```python
def create_token_pair(self, user_id: int, ip_address: str = None):
    # ... текущий код ...
    
    # 🔥 ДОБАВИТЬ: Сохранить в БД
    db_session = SessionLocal()
    
    TokenRepository.create_token(
        db_session, access_token_id, access_token,
        "access", user_id, expires_at, ip_address
    )
    TokenRepository.create_token(
        db_session, refresh_token_id, refresh_token,
        "refresh", user_id, expires_at, ip_address
    )
    TokenRepository.create_token_pair(
        db_session, access_token_id, refresh_token_id, user_id
    )
    db_session.close()
```

### 4. **TokenService: Загружать при запуске** 🔄
```python
def __init__(self):
    # ... текущий код ...
    
    # 🔥 ДОБАВИТЬ: Загрузить токены из БД
    db_session = SessionLocal()
    all_tokens = db_session.query(Token).filter(
        Token.is_blacklisted == False,
        Token.expires_at > datetime.utcnow()
    ).all()
    
    for db_token in all_tokens:
        self.active_tokens[db_token.id] = {
            "token_value": db_token.token_value,
            "type": db_token.token_type,
            "user_id": db_token.user_id,
            ...
        }
    db_session.close()
```

### 5. **Ограничение 2 пар** 📊
Текущий код в `_revoke_oldest_token` уже частично это делает, но нужно:

```python
def create_token_pair(self, user_id: int, ip_address: str = None):
    # Проверка лимита активных пар
    if user_id in self.user_tokens:
        active_pairs = self._count_active_pairs(user_id)
        
        if active_pairs >= self.max_tokens:  # max_tokens = 2
            print(f"⚠️ Лимит достигнут ({active_pairs}/{self.max_tokens} пар)")
            
            # Удаляем старые пары
            while self._count_active_pairs(user_id) >= self.max_tokens:
                oldest_pair = self._get_oldest_pair(user_id)
                if oldest_pair:
                    self.revoke_token(oldest_pair[0])  # access
                    self.revoke_token(oldest_pair[1])  # refresh
```

### 6. **Logout: Отозвать обе токена пары** 🔐
Нужно обновить логику:

```python
def revoke_access_and_pair(self, access_token_id: str):
    # 1. Отзываем access
    self.revoke_token(access_token_id)
    
    # 2. Находим связанный refresh
    refresh_token_id = self.refresh_to_access.get(access_token_id)
    if refresh_token_id:
        # 3. Отзываем refresh
        self.revoke_token(refresh_token_id)
        
        # 4. Удаляем связь
        del self.refresh_to_access[access_token_id]
```

---

## ✅ ЧТО УЖЕ СДЕЛАНО

1. ✅ `MAX_ACTIVE_TOKENS = 2` в settings.py
2. ✅ Модели Token и TokenPair созданы
3. ✅ TokenRepository создан
4. ✅ User модель обновлена с relationships
5. ✅ Миграция создана

---

## 🚀ЧТО ОСТАЛОСЬ

1. Обновить TokenService для работы с БД
2. Загружать токены при запуске
3. Сохранять токены в БД при создании
4. Реализовать ограничение на 2 пары с удалением старых

---

## 📍КЛЮЧЕВОЙ КОД (Нужно добавить в token_service.py)

```python
# === ОГРАНИЧЕНИЕ НА 2 ПАРЫ ===
if active_pairs >= self.max_tokens:
    # Удалить старую пару (access + refresh)
    oldest = self._get_oldest_pair(user_id)
    self.revoke_token(oldest['access_id'])
    self.revoke_token(oldest['refresh_id'])

# === СВЯЗЬ ACCESS-REFRESH ===
self.refresh_to_access[refresh_token_id] = access_token_id
print(f"🔗 Связь создана: refresh -> access")

# === LOGOUT ОБОИХ ===
if access_token_id in self.active_tokens:
    # Находим refresh
    refresh_id = [k for k,v in self.refresh_to_access.items() if v == access_token_id]
    self.revoke_token(access_token_id)
    if refresh_id:
        self.revoke_token(refresh_id[0])
```
