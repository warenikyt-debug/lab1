# 🔐 ПОЛНОЕ ОБЪЯСНЕНИЕ ТОКЕНОВ В КОДЕ

---

## 📋 ШАГИ 1-3: ГДЕ И ИЗ ЧЕГО ГЕНЕРИРУЕТСЯ ТОКЕН

### ШАГ 1️⃣: ПОЛЬЗОВАТЕЛЬ ЛОГИНИТСЯ
```
📱 POST /api/auth/login
   ↓ (LoginRequest с username + password)
   ↓
🎯 auth_controller.login() - ВХОД В КОНТРОЛЛЕР
```

📍 **Файл:** `app/controllers/auth_controller.py:21`
```python
async def login(request: Request, login_data: LoginRequest):
    dto = login_data.to_dto()
    result = auth_service.login(
        username=dto.username,
        password=dto.password,
        ip_address=request.client.host
    )
```

---

### ШАГ 2️⃣: ПРОВЕРКА ПАРОЛЯ В СЕРВИСЕ
```
🎯 auth_service.login() - ВХОД В СЕРВИС
   ↓ 
   ├─ 1️⃣ Ищем пользователя в БД
   ├─ 2️⃣ Проверяем пароль (verify_password)
   ├─ 3️⃣ Если ВЕРНО → ГЕНЕРИРУЕМ ТОКЕНЫ ✅
   └─ 4️⃣ Если НЕВЕРНО → Возвращаем None ❌
```

📍 **Файл:** `app/services/auth_service.py:87-129`
```python
def login(self, username: str, password: str, ip_address: str = None):
    user_data = find_user_by_username(username)      # Ищем в БД
    if not user_data:
        return None                                   # Пользователь не найден
    
    # Проверяем пароль (сравниваем с хешем в БД)
    if not temp_user.verify_password(password):
        return None                                   # Пароль неверный
    
    # ✅ ЗДЕСЬ ГЕНЕРИРУЮТСЯ ТОКЕНЫ!
    tokens = self.token_service.create_token_pair(user_data['id'], ip_address)
```

---

### ШАГ 3️⃣: ГЕНЕРАЦИЯ ТОКЕНОВ
```
🔑 token_service.create_token_pair() - ГЛАВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ
   ↓
   ├─ Проверяем лимит активных токенов (макс 5)
   ├─ Генерируем 2 УНИКАЛЬНЫХ ID:
   │  ├─ access_token_id (например: "a1b2c3d4-...")
   │  └─ refresh_token_id (например: "x9y8z7w6-...")
   │
   ├─ Создаём 2 JWT ТОКЕНА с использованием этих ID
   │  ├─ ACCESS токен (живёт 60 минут)
   │  └─ REFRESH токен (живёт 7 дней)
   │
   └─ Сохраняем информацию о токенах во внутренних хранилищах
```

�� **Файл:** `app/services/token_service.py:72-139`

---

## 🔍 ШАГИ 4-5: ИЗ ЧЕГО СОСТОИТ ТОКЕН

### ШАГ 4️⃣: СТРУКТУРА JWT ТОКЕНА

JWT токен состоит из **3 частей**, разделённых точками:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjoxLCJ0eXBlIjoiYWNjZXNzIn0.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
  ↓                 ↓                     ↓
HEADER          PAYLOAD             SIGNATURE
(заголовок)     (данные)           (подпись)
```

### 📌 HEADER (Заголовок)
```json
{
  "alg": "HS256",     // Алгоритм подписи (HMAC SHA-256)
  "typ": "JWT"        // Тип токена
}
```
📍 **Где:** Автоматически создаётся библиотекой `jwt.encode()`

---

### 📌 PAYLOAD (Данные - самое важное!)
```json
{
  "user_id": 1,                                    // ID пользователя
  "type": "access",                                // Тип токена (access или refresh)
  "token_id": "a1b2c3d4-1234-5678-90ab-cdef12345",// Уникальный ID
  "exp": 1711270855.123,                           // Время истечения (timestamp)
  "iat": 1711267255.123                            // Время создания (timestamp)
}
```

📍 **Файл:** `app/services/token_service.py:58-70`
```python
def _create_jwt_token(self, user_id: int, token_type: str, 
                      ttl_minutes: int, token_id: str) -> str:
    expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    # ✅ СОЗДАЁМ PAYLOAD
    payload = {
        "user_id": user_id,              # Кто это
        "type": token_type,              # Тип (access/refresh)
        "token_id": token_id,            # Уникальный ID
        "exp": expires.timestamp(),      # Когда истечёт
        "iat": datetime.utcnow().timestamp()  # Когда создан
    }
    
    # 🔐 Подписываем секретным ключом
    return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
```

---

### 🔐 SIGNATURE (Подпись)
```
HMAC(HS256, 
     header + payload,
     SECRET_KEY
)
```

**Где хранится SECRET_KEY:**
📍 **Файл:** `app/config/settings.py`
```python
SECRET_KEY: str = "your-secret-key-here-change-in-production"
ALGORITHM: str = "HS256"
```

**Зачем подпись?**
- Гарантирует, что токен **не был изменён**
- Если хакер попробует изменить `user_id` с 1 на 2, подпись не совпадёт
- Подпись можно проверить только если знаешь SECRET_KEY

---

## 🏪 ШАГИ 6-7: ГДЕ ХРАНЯТСЯ ИНФОРМАЦИЯ О ТОКЕНАХ

### ШАГ 6️⃣: ХРАНИЛИЩА НА СЕРВЕРЕ

После создания токенов, сервис сохраняет информацию в **памяти** (в Python объектах):

📍 **Файл:** `app/services/token_service.py:42-48`
```python
# Хранилище 1: Все активные токены
self.active_tokens: Dict[str, dict] = {}
# Пример: {
#   "a1b2c3d4-...": {
#       "user_id": 1,
#       "type": "access",
#       "created_at": 2024-03-28 10:00:00,
#       "expires_at": 2024-03-28 11:00:00,
#       "ip_address": "192.168.1.1"
#   }
# }

# Хранилище 2: Связь refresh → access токена
self.refresh_to_access: Dict[str, str] = {}
# Пример: {
#   "x9y8z7w6-...": "a1b2c3d4-..."
# }

# Хранилище 3: Токены пользователя
self.user_tokens: Dict[int, List[str]] = {}
# Пример: {
#   1: ["a1b2c3d4-...", "x9y8z7w6-..."]
# }

# Хранилище 4: ЧЕРНЫЙ СПИСОК (отозванные токены)
self.blacklisted_tokens: set = set()
# Пример: {"old-token-id-...", "another-old-id-..."}
```

**Почему это важно:**
- Когда пользователь выходит (logout) → токен **добавляется в черный список**
- Когда обновляются токены (refresh) → старые **отзываются**
- Если у пользователя > 5 токенов → самый старый **автоматически отзывается**

---

## ✅ ШАГИ 8-10: КАК ПРОВЕРЯЕТСЯ ТОКЕН

### ШАГ 8️⃣: ПОЛЬЗОВАТЕЛЬ ДЕЛАЕТ ЗАПРОС С ТОКЕНОМ

```
📱 GET /api/auth/me
   ↓ (с заголовком)
   ↓ Authorization: Bearer eyJhbGc...
   ↓
🎯 auth_controller.get_me() - ВХОД В КОНТРОЛЛЕР
```

📍 **Файл:** `app/controllers/auth_controller.py:51-78`
```python
async def get_me(request: Request):
    # Извлекаем токен из заголовка
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "")
    
    # ✅ ПРОВЕРЯЕМ ТОКЕН
    payload = token_service.verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    # Извлекаем user_id из токена
    user_id = payload.get("user_id")
    
    # Получаем данные пользователя
    user_data = auth_service.get_user_by_id(user_id)
    return UserDTO(...)
```

---

### ШАГ 9️⃣: ПРОЦЕСС ПРОВЕРКИ ТОКЕНА

```
🔍 token_service.verify_token(token, "access")
   ↓
   ├─ 1️⃣ Декодируем JWT
   │      (проверяем подпись используя SECRET_KEY)
   │
   ├─ 2️⃣ Извлекаем PAYLOAD
   │      (user_id, type, token_id, exp, iat)
   │
   ├─ 3️⃣ Проверяем черный список ⚠️
   │      Если token_id в blacklisted_tokens → ВЕРНУТЬ None (токен отозван)
   │
   ├─ 4️⃣ Проверяем тип токена
   │      Ожидали "access"? А получили "refresh"? → ВЕРНУТЬ None
   │
   ├─ 5️⃣ Проверяем срок действия (exp)
   │      Текущее время > exp? → ВЕРНУТЬ None (истёк)
   │      Если refresh использован ранее? → ВЕРНУТЬ None
   │
   └─ ✅ Если все проверки прошли → ВЕРНУТЬ payload
```

📍 **Файл:** `app/services/token_service.py:141-187`
```python
def verify_token(self, token: str, expected_type: str = None) -> Optional[Dict]:
    try:
        # 1️⃣ Декодируем JWT (проверяем подпись)
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        token_id = payload.get("token_id")
        token_type = payload.get("type")
        
        print(f"🔍 Проверка токена: {token_id[:8]}...")
        
        # 2️⃣ ЧЕРНЫЙ СПИСОК - главная проверка!
        if token_id in self.blacklisted_tokens:
            print(f"❌ ТОКЕН В ЧЕРНОМ СПИСКЕ!")
            return None
        
        # 3️⃣ Проверяем тип
        if expected_type and token_type != expected_type:
            print(f"❌ Неверный тип токена")
            return None
        
        # 4️⃣ Проверяем срок действия
        exp = datetime.fromtimestamp(payload.get("exp"))
        if exp < datetime.utcnow():
            print(f"❌ Токен истек")
            return None
        
        # 5️⃣ Проверяем используемость refresh токена
        if token_type == "refresh" and token_id in self.used_refresh_tokens:
            print(f"❌ Refresh токен уже использован")
            self.revoke_all_user_tokens(user_id)  # УГРОЗА БЕЗОПАСНОСТИ!
            return None
        
        print(f"✅ Токен действителен")
        return payload
        
    except jwt.PyJWTError as e:
        print(f"❌ Ошибка JWT: {e}")
        return None
```

---

### ШАГ 1️⃣0️⃣: ЧТО ДЕЛАЕМ С PAYLOAD

Если `verify_token()` вернул payload, мы можем использовать данные:

```python
# Извлекаем информацию из payload
user_id = payload.get("user_id")        # Кто делает запрос
token_type = payload.get("type")        # Какой токен
token_id = payload.get("token_id")      # Уникальный ID

# Используем эти данные:
user_data = auth_service.get_user_by_id(user_id)  # Получаем пользователя
return UserDTO(id=user_data['id'], ...)  # Возвращаем данные
```

---

## 🚪 ОСОБЕННОСТЬ: LOGOUT (ВЫХОД)

### Когда пользователь нажимает "Выход"

```
📱 POST /api/auth/logout
   ↓ (с токеном в заголовке)
   ↓
🎯 auth_controller.logout()
   ↓
🔐 token_service.revoke_token(token_id)
   ↓
➕ blacklisted_tokens.add(token_id)  ← ДОБАВЛЯЕМ В ЧЕРНЫЙ СПИСОК
   ↓
❌ Теперь этот токен больше никогда не будет работать!
```

📍 **Файл:** `app/services/token_service.py:189-216`
```python
def revoke_token(self, token_id: str):
    # 🔥 ГЛАВНОЕ: Добавляем в черный список
    self.blacklisted_tokens.add(token_id)
    print(f"✅ Токен добавлен в черный список")
    
    # Удаляем из других хранилищ
    del self.active_tokens[token_id]
    self.user_tokens[user_id].remove(token_id)
```

---

## 📊 ИТОГОВАЯ ТАБЛИЦА

| Что | Где | Как | Когда |
|-----|-----|-----|-------|
| **Генерация** | `token_service.create_token_pair()` | `jwt.encode(payload, SECRET_KEY)` | После успешного логина |
| **Хранение** | `self.active_tokens` (память) | Python dict | В процессе жизни токена |
| **Проверка** | `token_service.verify_token()` | Декодирование JWT + проверка черного списка | Перед использованием |
| **Отзыв** | `token_service.revoke_token()` | Добавление в `blacklisted_tokens` | При logout или по лимиту |
| **Обновление** | `token_service.refresh_tokens()` | Все старые в черный список + новые созданы | Когда access истекает |

---

## 🎯 ВЫВОД

**Простая схема:**
```
1️⃣ Логин → создаём 2 токена (access + refresh)
2️⃣ Каждый запрос → проверяем access токен (не в ч.списке + не истёк)
3️⃣ Logout → добавляем токены в ч.список (больше не работают)
4️⃣ Refresh → создаём новые токены, старые в ч.список
```

**Ключевые моменты:**
- 🔑 **Токены живут в памяти, не в БД**
- 🔐 **Подпись невозможно подделать без SECRET_KEY**
- 🔴 **Черный список = главный способ отключить токен**
- ♻️ **Access короткоживущий (60 мин), refresh долгоживущий (7 дней)**
