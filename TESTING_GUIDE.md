# 🧪 РУКОВОДСТВО ПО ТЕСТИРОВАНИЮ RBAC СИСТЕМЫ

## 📍 СПОСОБ 1: ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС (САМЫЙ ПРОСТОЙ!)

### Шаг 1: Запустить сервер
```bash
cd /workspaces/lab1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Шаг 2: Открыть документацию
Открыть в браузере: **http://localhost:8000/docs**

Видишь красивый интерфейс Swagger? Отлично! 

### Шаг 3: Авторизоваться
1. Найти эндпоинт **POST /api/auth/login**
2. Кликнуть **"Try it out"**
3. Ввести:
```json
{
  "username": "Admin123",
  "password": "Admin@123"
}
```
4. Кликнуть **"Execute"**
5. **СКОПИРОВАТЬ** весь текст из поля `access_token` (без кавычек)

### Шаг 4: Авторизовать все запросы
1. Нажать кнопку **"Authorize"** (вверху справа)
2. Вставить в формат: `Bearer СКОПИРОВАННЫЙ_ТОКЕН`
3. Кликнуть "Authorize"

### Шаг 5: Тестировать эндпоинты
Теперь можешь тестировать любой эндпоинт:
- **GET /api/ref/policy/role** - видишь роли
- **GET /api/ref/user** - видишь пользователей
- **POST /api/ref/policy/role** - создать новую роль
- Всё работает с одной кнопкой "Execute"!

---

## 💻 СПОСОБ 2: ЧЕРЕЗ COMMAND LINE (CURL)

### Получить токен
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}'
```

Скопировать значение `access_token` из ответа.

### Использовать токен в запросах
Сохрани токен в переменную (удобнее):
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

Теперь в каждом запросе используй:
```bash
-H "Authorization: Bearer $TOKEN"
```

### Примеры запросов

**1️⃣ Получить список ролей:**
```bash
curl http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN"
```

**2️⃣ Получить список разрешений:**
```bash
curl http://localhost:8000/api/ref/policy/permission \
  -H "Authorization: Bearer $TOKEN"
```

**3️⃣ Получить список пользователей:**
```bash
curl http://localhost:8000/api/ref/user \
  -H "Authorization: Bearer $TOKEN"
```

**4️⃣ Создать новую роль:**
```bash
curl -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Moderator",
    "slug": "moderator",
    "description": "Content moderator"
  }'
```

**5️⃣ Создать новое разрешение:**
```bash
curl -X POST http://localhost:8000/api/ref/policy/permission \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ban User",
    "slug": "ban-user",
    "description": "Ability to ban users"
  }'
```

**6️⃣ Обновить роль:**
```bash
curl -X PUT http://localhost:8000/api/ref/policy/role/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Super Admin",
    "slug": "admin",
    "description": "Super administrator"
  }'
```

**7️⃣ Мягко удалить роль:**
```bash
curl -X DELETE http://localhost:8000/api/ref/policy/role/5/soft \
  -H "Authorization: Bearer $TOKEN"
```

**8️⃣ Восстановить роль:**
```bash
curl -X POST http://localhost:8000/api/ref/policy/role/5/restore \
  -H "Authorization: Bearer $TOKEN"
```

**9️⃣ Жестко удалить роль:**
```bash
curl -X DELETE http://localhost:8000/api/ref/policy/role/5 \
  -H "Authorization: Bearer $TOKEN"
```

**🔟 Получить роли пользователя:**
```bash
curl http://localhost:8000/api/ref/user/1/role \
  -H "Authorization: Bearer $TOKEN"
```

**1️⃣1️⃣ Присвоить роль пользователю:**
```bash
curl -X POST http://localhost:8000/api/ref/user/1/role/2 \
  -H "Authorization: Bearer $TOKEN"
```

**1️⃣2️⃣ Удалить роль у пользователя:**
```bash
curl -X DELETE http://localhost:8000/api/ref/user/1/role/2 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔓 УЧЕТНЫЕ ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ

### АДМИН (полный доступ)
```
Username: Admin123
Email:    admin@test.com
Password: Admin@123
Роли:     Admin, User
```

### ОГРАНИЧЕННЫЙ ПОЛЬЗОВАТЕЛЬ
```
Username: LimitedUser
Email:    limited@test.com
Password: LimitedPass123!@#
Роли:     (не назначены)
```

---

## 🧪 ТЕСТИРОВАНИЕ СЦЕНАРИЕВ

### Сценарий 1: Проверка ошибки 403 (доступ запрещен)

**Авторизоваться как LimitedUser:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"LimitedUser","password":"LimitedPass123!@#"}'
```

**Попытаться создать роль (не будет разрешения):**
```bash
TOKEN_LIMITED="eyJhbGciOiJIUzI1NiIs..." # Токен LimitedUser

curl -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN_LIMITED" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","slug":"test"}'
```

**Ожидаемый ответ (403):**
```json
{
  "error": "Access denied. Required permission: create-role"
}
```

✅ **Это правильно!**

---

### Сценарий 2: Создание и удаление роли

**1. Создать роль:**
```bash
curl -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tester","slug":"tester","description":"QA tester"}'
```
→ Получишь ID новой роли (например, **6**)

**2. Мягко удалить:**
```bash
curl -X DELETE http://localhost:8000/api/ref/policy/role/6/soft \
  -H "Authorization: Bearer $TOKEN"
```

**3. Восстановить:**
```bash
curl -X POST http://localhost:8000/api/ref/policy/role/6/restore \
  -H "Authorization: Bearer $TOKEN"
```

**4. Жестко удалить:**
```bash
curl -X DELETE http://localhost:8000/api/ref/policy/role/6 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Сценарий 3: Присвоение ролей пользователю

**1. Получить пользователей:**
```bash
curl http://localhost:8000/api/ref/user \
  -H "Authorization: Bearer $TOKEN"
```

**2. Получить роли пользователя ID=2:**
```bash
curl http://localhost:8000/api/ref/user/2/role \
  -H "Authorization: Bearer $TOKEN"
```

**3. Присвоить роль User (ID=2) пользователю (ID=2):**
```bash
curl -X POST http://localhost:8000/api/ref/user/2/role/2 \
  -H "Authorization: Bearer $TOKEN"
```

**4. Проверить роли снова:**
```bash
curl http://localhost:8000/api/ref/user/2/role \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 ВСЕ ЭНДПОИНТЫ

### Роли
```
GET    /api/ref/policy/role              - Список ролей
GET    /api/ref/policy/role/{id}         - Получить роль
POST   /api/ref/policy/role              - Создать роль
PUT    /api/ref/policy/role/{id}         - Обновить роль
DELETE /api/ref/policy/role/{id}         - Жёсткое удаление
DELETE /api/ref/policy/role/{id}/soft    - Мягкое удаление
POST   /api/ref/policy/role/{id}/restore - Восстановить роль
```

### Разрешения
```
GET    /api/ref/policy/permission              - Список разрешений
GET    /api/ref/policy/permission/{id}         - Получить разрешение
POST   /api/ref/policy/permission              - Создать разрешение
PUT    /api/ref/policy/permission/{id}         - Обновить разрешение
DELETE /api/ref/policy/permission/{id}         - Жёсткое удаление
DELETE /api/ref/policy/permission/{id}/soft    - Мягкое удаление
POST   /api/ref/policy/permission/{id}/restore - Восстановить разрешение
```

### Пользователи
```
GET    /api/ref/user                        - Список пользователей
GET    /api/ref/user/{user_id}/role         - Роли пользователя
POST   /api/ref/user/{user_id}/role/{id}    - Присвоить роль
DELETE /api/ref/user/{user_id}/role/{id}    - Удалить роль (hard)
DELETE /api/ref/user/{user_id}/role/{id}/soft - Мягкое удаление
POST   /api/ref/user/{user_id}/role/{id}/restore - Восстановить роль
```

---

## 💡 ПОЛЕЗНЫЕ СОВЕТЫ

### Сохранить токен в переменную
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo $TOKEN
```

### Красивый вывод JSON
Добавить в конец команды: `| python3 -m json.tool`

```bash
curl http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Сохранить ответ в файл
```bash
curl http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" > roles.json
```

---

## 🔍 КОДЫ ОШИБОК

| Код | Значение | Решение |
|-----|----------|--------|
| 200 | OK | Всё работает |
| 201 | Created | Ресурс успешно создан |
| 204 | No Content | Успешно удалено |
| 400 | Bad Request | Ошибка в данных (проверь JSON) |
| 401 | Unauthorized | Токен неверный или истёк |
| 403 | Forbidden | Нет разрешения на операцию |
| 404 | Not Found | Ресурс не найден (неверный ID) |
| 500 | Server Error | Ошибка сервера |

---

## 🎯 QUICK START

Для быстрого старта скопируй и выполни в терминале:

```bash
# Получить токен админа
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Теперь можешь использовать $TOKEN

# Пример 1: Получить роли
curl http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Пример 2: Создать роль
curl -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","slug":"test","description":"Test role"}'
```

---

**✅ Теперь ты готов тестировать систему!**
