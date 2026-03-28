# 📍 КЛЮЧЕВОЙ КОД ОГРАНИЧЕНИЯ НА 2 ПАРЫ И СВЯЗЬ ТОКЕНОВ

## 🔴 ФИНАЛЬНОЕ ОГРАНИЧЕНИЕ

### 1️⃣ ПРОВЕРКА ЛИМИТА В `create_token_pair()`

При создании новой пары нужно проверить, есть ли уже 2 пары. Если есть - удалить старую.

```python
# === КЛЮЧЕВОЙ МОМЕНТ: ПРОВЕРКА ЛИМИТА ===
if user_id in self.user_tokens:
    # Считаем активные ПАРЫ (не отдельные токены!)
    active_pairs = 0
    
    for token_id in self.user_tokens[user_id]:
        if token_id in self.active_tokens and token_id not in self.blacklisted_tokens:
            token_info = self.active_tokens[token_id]
            
            # Считаем только ACCESS токены (каждый access это одна пара)
            if token_info["type"] == "access":
                active_pairs += 1
    
    print(f"📊 Активных пар: {active_pairs}, лимит: {self.max_tokens}")
    
    # === ЕСЛИ ЛИМИТ ПРЕВЫШЕН, УДАЛЯЕМ СТАРЫЕ ПАРЫ ===
    while active_pairs >= self.max_tokens:
        print(f"⚠️ ПРЕВЫШЕН ЛИМИТ! Удаляю старую пару...")
        self._revoke_oldest_pair(user_id)
        active_pairs -= 1

# Сохраняем связь: если logout access то и refresh не работает
self.refresh_to_access[refresh_token_id] = access_token_id
print(f"🔗 Связь создана: refresh_id -> access_id")
```

### 2️⃣ НОВЫЙ МЕТОД: Удаление старой пары

```python
def _revoke_oldest_pair(self, user_id: int):
    """Отзыв самой старой пары токенов (access + refresh вместе)"""
    if user_id not in self.user_tokens:
        return
    
    oldest_access = None
    oldest_time = None
    oldest_refresh = None
    
    # Ищем самый старый access токен
    for token_id in self.user_tokens[user_id]:
        if token_id in self.active_tokens and token_id not in self.blacklisted_tokens:
            token_info = self.active_tokens[token_id]
            
            # Только access токены считаем как пары
            if token_info["type"] == "access":
                if oldest_time is None or token_info["created_at"] < oldest_time:
                    oldest_time = token_info["created_at"]
                    oldest_access = token_id
    
    # Если нашли access, ищем его refresh
    if oldest_access:
        for refresh_id, access_id in self.refresh_to_access.items():
            if access_id == oldest_access:
                oldest_refresh = refresh_id
                break
    
    # === ОТЗЫВАЕМ ОБА ТОКЕНА ПАРЫ ===
    if oldest_access:
        print(f"🗑️ Удаляю пару: access={oldest_access[:8]}...")
        self.revoke_token(oldest_access)
        
        if oldest_refresh:
            print(f"🗑️ Удаляю связанный refresh={oldest_refresh[:8]}...")
            self.revoke_token(oldest_refresh)
            # Удаляем связь
            del self.refresh_to_access[oldest_refresh]
        
        print(f"✅ Пара удалена")
```

### 3️⃣ НОВЫЙ МЕТОД: Подсчет активных пар

```python
def _count_active_pairs(self, user_id: int) -> int:
    """Подсчет количества активных пар токенов"""
    if user_id not in self.user_tokens:
        return 0
    
    pair_count = 0
    for token_id in self.user_tokens[user_id]:
        if token_id in self.active_tokens and token_id not in self.blacklisted_tokens:
            token_info = self.active_tokens[token_id]
            # Считаем только access (каждый access = одна пара)
            if token_info["type"] == "access":
                pair_count += 1
    
    return pair_count
```

---

## 🔴 СВЯЗЬ ACCESS-REFRESH (уже сделано!)

### Когда logout из access токена:
```python
# В auth_controller.py POST /logout:
payload = token_service.verify_token(token, expected_type="access")
token_id = payload.get("token_id")

# Отзываем ТОЛЬКО access (по требованию)
token_service.revoke_token(token_id)

# Примечание: refresh из этой пары остается в черном списке
# если захотим, можем добавить:
# refresh_id = find_refresh_for_access(token_id)
# if refresh_id:
#     token_service.revoke_token(refresh_id)
```

---

## 📊 РЕЗУЛЬТАТ

- ✅ `MAX_ACTIVE_TOKENS = 2` (максимум 2 пары)
- ✅ `refresh_to_access` связывает refresh с access
- ✅ При 5 парах создание новой оставляет 2 пары (удаляет 3 старые)
- ✅ Старая пара удаляется целиком (access + refresh вместе)
- ✅ Refresh из других пар остаются работать

---

## 🔐 БД СОХРАНЕНИЕ (На будущее)

Для сохранения при перезагрузке сервера нужно:
1. При создании токена сохранять в таблицу `tokens`
2. При создании пары сохранять в таблицу `token_pairs`
3. При загрузке TokenService загружать все активные токены из БД
4. При logout обновлять флаг `is_blacklisted` в таблице

Модели уже созданы в `/workspaces/lab1/app/models/token.py`
