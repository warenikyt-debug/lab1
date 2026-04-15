СИСТЕМА АУТЕНТИФИКАЦИИ

ОПИСАНИЕ
========

Приложение на FastAPI с регистрацией, входом, логаутом и управлением токенами.
Черно-белый дизайн, простой интерфейс в квадратах.
Полностью задокументирован процесс работы.

УСТАНОВКА
=========

pip install -r requirements.txt

ЗАПУСК
======

СИСТЕМА АУТЕНТИФИКАЦИИ
  

АДРЕСА
======

Регистрация: http://localhost:8000/register
Вход: http://localhost:8000/login
Профиль: http://localhost:8000/profile
API документация: http://localhost:8000/docs
Информация о приложении: http://localhost:8000/info
Проверка здоровья: http://localhost:8000/health

API ENDPOINTS
=============

POST /api/auth/register
- Регистрация нового пользователя
- Body: { username, email, password, c_password, birthday }
- Returns: { id, username, email, birthday, created_at }

POST /api/auth/login
- Вход и получение токенов
- Body: { username, password }
- Returns: { access_token, refresh_token, user }

GET /api/auth/me
- Получение информации о текущем пользователе
- Header: Authorization: Bearer <access_token>
- Returns: { id, username, email, birthday, created_at }

POST /api/auth/refresh
- Обновление пары токенов
- Body: { refresh_token }
- Returns: { access_token, refresh_token }

POST /api/auth/logout
- Выход из системы (отозыв токена)
- Header: Authorization: Bearer <access_token>
- Returns: { message }

ФАЙЛОВАЯ СТРУКТУРА
===================

app/
  config/
    database.py ........... SQLAlchemy конфигурация
    settings.py ........... Настройки приложения
  controllers/
    auth_controller.py .... API endpoints
  dto/
    auth_dto.py ........... DTO для аутентификации
    user_dto.py ........... DTO пользователя
  models/
    user.py ............... SQLAlchemy модель User
  requests/
    auth_requests.py ...... Валидация входных данных
  services/
    auth_service.py ....... Бизнес логика регистрации/входа
    token_service.py ...... Работа с JWT токенами
  main.py ................. Главное приложение с документацией

templates/
  register.html .......... Форма регистрации
  login.html ............. Форма входа
  profile.html ........... Профиль пользователя

data/
  app.db ................. SQLite база данных

ПРОЦЕСС РАБОТЫ
===============

1. РЕГИСТРАЦИЯ
   - Пользователь вводит данные в /register
   - Форма отправляет POST /api/auth/register
   - Данные валидируются (app/requests/auth_requests.py)
   - Пароль хешируется (SHA256 + bcrypt)
   - Пользователь сохраняется в app.db
   - Возвращается UserDTO без пароля

2. ЛОГИН
   - Пользователь вводит username и пароль в /login
   - Форма отправляет POST /api/auth/login
   - Пользователь ищется в БД по username
   - Пароль проверяется (bcrypt verify)
   - Генерируются токены (app/services/token_service.py)
   - ACCESS_TOKEN живет 60 минут
   - REFRESH_TOKEN живет 7 дней
   - Токены сохраняются в localStorage на клиенте

3. ИСПОЛЬЗОВАНИЕ ТОКЕНА
   - При доступе к /profile отправляется GET /api/auth/me
   - В Header передается Authorization: Bearer <access_token>
   - Токен проверяется (подпись, срок действия, черный список)
   - Из token_id извлекается user_id
   - Пользователь ищется в БД
   - Возвращается информация о пользователе

4. ЛОГАУТ
   - На /profile нажимается кнопка "ВЫХОД"
   - Отправляется POST /api/auth/logout с токеном
   - Токен добавляется в черный список
   - Клиент удаляет токены из localStorage
   - Перенаправление на /login

ТРЕБОВАНИЯ К ПАРОЛЮ
===================

- Минимум 8 символов
- Хотя бы одна заглавная буква
- Хотя бы одна цифра
- Хотя бы один спецсимвол (!@#$%^&*)

ТРЕБОВАНИЯ К USERNAME
=====================

- Минимум 7 символов
- Начинается с заглавной буквы
- Только латиница и цифры (A-Z, a-z, 0-9)

ТРЕБОВАНИЯ К ДАТЕ РОЖДЕНИЯ
===========================

- Возраст должен быть не менее 14 лет

БЕЗОПАСНОСТЬ
============

ХЕШИРОВАНИЕ ПАРОЛЕЙ:
- SHA256(password) -> bcrypt с солью
- Никогда не возвращается password_hash в ответе

JWT ТОКЕНЫ:
- Подписаны SECRET_KEY с алгоритмом HS256
- Содержат token_id для отслеживания
- Проверяются черный список при использовании
- Access token имеет краткий TTL (60 минут)
- Refresh token одноразовый

DATABASE:
- SQLAlchemy ORM защищает от SQL injection
- UNIQUE constraints для username, email

VALIDATION:
- Pydantic валидирует все входящие данные
- Проверка уникальности username и email в БД

ТЕХНИЧЕСКИЕ ДЕТАЛИ
===================

DATABASE:
- SQLite в /workspaces/lab1/data/app.db
- SQLAlchemy ORM
- Таблица 'users' с полями: id, username, email, password_hash, birthday, created_at

AUTHENTICATION:
- JWT токены (HS256)
- Access token TTL: 60 минут
- Refresh token TTL: 7 дней
- Черный список отозванных токенов

PASSWORD HASHING:
- SHA256 хеширование + bcrypt с солью
- Автоматическое создание соли для каждого пароля

TESTING
=======

API документация с возможностью тестирования:
http://localhost:8000/docs

ПРИМЕРЫ
=======

Регистрация:
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "TestUser1",
    "email": "test@example.com",
    "password": "Test123!@#",
    "c_password": "Test123!@#",
    "birthday": "2000-01-01"
  }'

Вход:
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "TestUser1",
    "password": "Test123!@#"
  }'

Получение профиля:
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

Логаут:
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"

ИСТОРИЯ РАЗВИТИЯ
=================

Версия 1.0:
- Черно-белый дизайн в квадратах
- Простой интерфейс без украшений
- Полная документация в main.py
- SQLAlchemy ORM
- JWT токены
- Черный список токенов
- Refresh token функциональность

