# =============================================================================
# ОСНОВНОЙ ФАЙЛ ПРИЛОЖЕНИЯ - ПОЛНАЯ ДОКУМЕНТАЦИЯ ПРОЦЕССА АУТЕНТИФИКАЦИИ
# =============================================================================
# 
# ПРОЦЕСС:
# 1. РЕГИСТРАЦИЯ - пользователь создает аккаунт
# 2. ЛОГИН - пользователь входит и получает токены
# 3. ИСПОЛЬЗОВАНИЕ ТОКЕНА - доступ к защищенным ресурсам
# 4. ЛОГАУТ - выход из системы и отозыв токена
# =============================================================================

# ============= ИМПОРТЫ =============
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, date, timedelta
import json
import os
import bcrypt
import uuid
import jwt
import logging
from typing import Optional, Dict, List

# ИСТОЧНИК: app/models/user.py
# Функция инициализации БД и функции для работы с пользователями
from app.models.user import init_db

# ИСТОЧНИК: app/controllers/auth_controller.py
# Все API endpoints для аутентификации (register, login, me, refresh, logout)
from app.controllers.auth_controller import router as auth_router

# ИСТОЧНИК: app/services/token_service.py
# Синглтон для работы с JWT токенами
from app.services.token_service import TokenService

# ============= ЛОГИРОВАНИЕ =============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lab2")

# ============= ИНИЦИАЛИЗАЦИЯ БД =============
# ВЫЗОВ: app/models/user.py - init_db()
# Создает таблицу 'users' в SQLite если её еще нет
# Таблица содержит: id, username, email, password_hash, birthday, created_at
init_db()
logger.info("БД инициализирована")

# ============= КОНФИГУРАЦИЯ =============
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 10080
MAX_ACTIVE_TOKENS = 5

# ИСТОЧНИК: app/services/token_service.py
# TokenService - синглтон для управления токенами
token_service = TokenService()

# ============= МОДЕЛИ ДАННЫХ (REQUESTS) =============
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    c_password: str
    birthday: date
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v) < 7:
            raise ValueError('Минимум 7 символов')
        if not v[0].isupper():
            raise ValueError('Первая буква заглавная')
        if not v.isalnum():
            raise ValueError('Только буквы и цифры')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль минимум 8 символов')
        if not any(c.isupper() for c in v):
            raise ValueError('Нужна заглавная буква')
        if not any(c.isdigit() for c in v):
            raise ValueError('Нужна цифра')
        if not any(not c.isalnum() for c in v):
            raise ValueError('Нужен спецсимвол (!@#$%^&*)')
        return v

# ============= СОЗДАНИЕ ПРИЛОЖЕНИЯ =============
app = FastAPI(title="Система Аутентификации")

# РЕГИСТРАЦИЯ МАРШРУТОВ АУТЕНТИФИКАЦИИ
# ИСТОЧНИК: app/controllers/auth_controller.py
# Включает все API endpoints (POST /api/auth/register, /api/auth/login и т.д.)
app.include_router(auth_router)

# ============= СТАТИЧЕСКИЕ ФАЙЛЫ =============
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    logger.warning("Папка static не найдена")

# =============================================================================
# ПОЛНЫЙ ПРОЦЕСС АУТЕНТИФИКАЦИИ
# =============================================================================

# =============================================================================
# ЭТАП 1: РЕГИСТРАЦИЯ (POST /api/auth/register)
# =============================================================================
# АЛГОРИТМ:
# 1. Пользователь заполняет форму на странице /register (templates/register.html)
# 2. JavaScript отправляет POST запрос на /api/auth/register
# 3. ВАЛИДАЦИЯ:
#    - Проверка уникальности username (из БД app/config/database.py)
#    - Проверка уникальности email
#    - Проверка пароля (минимум 8 символов, заглавная, цифра, спецсимвол)
# 4. СОХРАНЕНИЕ:
#    - Хеширование пароля: SHA256 + bcrypt (app/models/user.py::User.hash_password)
#    - Сохранение в БД: /workspaces/lab1/data/app.db (SQLAlchemy ORM)
#    - ИСТОЧНИК ФУНКЦИЙ: app/services/auth_service.py::AuthService.register()
# 5. ВОЗВРАТ: UserDTO без пароля (безопасность)
#
# FILES INVOLVED:
# - templates/register.html - форма регистрации
# - app/controllers/auth_controller.py - endpoint @router.post("/register")
# - app/services/auth_service.py - бизнес логика регистрации
# - app/models/user.py - сохранение в БД
# - app/config/database.py - настройка SQLAlchemy

# =============================================================================
# ЭТАП 2: ЛОГИН (POST /api/auth/login)
# =============================================================================
# АЛГОРИТМ:
# 1. Пользователь вводит username и пароль на странице /login
# 2. JavaScript отправляет POST запрос на /api/auth/login
# 3. ПОИСК ПОЛЬЗОВАТЕЛЯ:
#    - Найти пользователя по username в БД
#    - ИСТОЧНИК: app/services/auth_service.py::AuthService.login()
# 4. ПРОВЕРКА ПАРОЛЯ:
#    - Хешировать введенный пароль (SHA256 + bcrypt)
#    - Сравнить с password_hash из БД
#    - ИСТОЧНИК: app/models/user.py::User.verify_password()
# 5. ГЕНЕРАЦИЯ ТОКЕНОВ:
#    - Если пароль верен, создать пару токенов
#    - ACCESS_TOKEN: живет 60 минут (для доступа к ресурсам)
#    - REFRESH_TOKEN: живет 7 дней (для обновления access token)
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.create_token_pair()
# 6. ВОЗВРАТ:
#    - access_token (JWT с payload: user_id, type='access', token_id, exp, iat)
#    - refresh_token (JWT с payload: user_id, type='refresh', token_id, exp, iat)
#    - user (UserDTO без пароля)
#
# FILES INVOLVED:
# - templates/login.html - форма входа
# - app/controllers/auth_controller.py - endpoint @router.post("/login")
# - app/services/auth_service.py - поиск и проверка пароля
# - app/services/token_service.py - генерация JWT токенов
# - app/models/user.py - получение пользователя из БД

# =============================================================================
# ЭТАП 3: ИСПОЛЬЗОВАНИЕ ТОКЕНА (GET /api/auth/me)
# =============================================================================
# АЛГОРИТМ:
# 1. Клиент отправляет запрос с Authorization: Bearer <access_token>
# 2. ПРОВЕРКА ТОКЕНА:
#    - Декодировать JWT токен
#    - Проверить signature (SECRET_KEY)
#    - Проверить тип токена (должен быть 'access')
#    - Проверить в черном списке (отозван ли токен)
#    - Проверить дату истечения (exp)
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.verify_token()
# 3. ПОЛУЧЕНИЕ ДАННЫХ:
#    - Из токена извлечь user_id
#    - Найти пользователя в БД по user_id
#    - ИСТОЧНИК: app/services/auth_service.py::AuthService.get_user_by_id()
# 4. ВОЗВРАТ:
#    - UserDTO с информацией о пользователе (id, username, email, birthday, created_at)
#    - БЕЗ password_hash (безопасность)
#
# FILES INVOLVED:
# - app/controllers/auth_controller.py - endpoint @router.get("/me")
# - app/services/token_service.py - проверка JWT токена
# - app/models/user.py - поиск пользователя в БД

# =============================================================================
# ЭТАП 4: ОБНОВЛЕНИЕ ТОКЕНА (POST /api/auth/refresh)
# =============================================================================
# АЛГОРИТМ:
# 1. Клиент отправляет refresh_token (старый access_token истек)
# 2. ПРОВЕРКА REFRESH ТОКЕНА:
#    - Проверить JWT refresh_token
#    - Проверить что это именно refresh_token (type='refresh')
#    - Проверить не использован ли еще (одноразовый)
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.verify_token()
# 3. ОТОЗЫВ СТАРОЙ ПАРЫ:
#    - Добавить старый access_token в черный список
#    - Добавить refresh_token в черный список
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.revoke_token()
# 4. ГЕНЕРАЦИЯ НОВОЙ ПАРЫ:
#    - Создать новый access_token
#    - Создать новый refresh_token
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.create_token_pair()
# 5. ВОЗВРАТ:
#    - Новые access_token и refresh_token
#
# FILES INVOLVED:
# - app/controllers/auth_controller.py - endpoint @router.post("/refresh")
# - app/services/token_service.py - проверка и обновление токенов

# =============================================================================
# ЭТАП 5: ЛОГАУТ (POST /api/auth/logout)
# =============================================================================
# АЛГОРИТМ:
# 1. Клиент отправляет запрос с Authorization: Bearer <access_token>
# 2. ПРОВЕРКА ТОКЕНА:
#    - Проверить что токен действительный
#    - Извлечь token_id из payload
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.verify_token()
# 3. ОТОЗЫВ ТОКЕНА:
#    - Добавить token_id в черный список
#    - Удалить из списка активных токенов
#    - ИСТОЧНИК: app/services/token_service.py::TokenService.revoke_token()
# 4. ВОЗВРАТ:
#    - Сообщение об успехе
# 5. НА КЛИЕНТЕ:
#    - Удалить access_token из localStorage
#    - Удалить refresh_token из localStorage
#    - Перенаправить на /login
#
# FILES INVOLVED:
# - templates/login.html, profile.html - JavaScript для удаления токенов
# - app/controllers/auth_controller.py - endpoint @router.post("/logout")
# - app/services/token_service.py - отозыв токена

# =============================================================================
# СТРУКТУРА ПАПОК И ФАЙЛОВ
# =============================================================================
# 
# app/
#   config/
#     database.py .................. Конфигурация SQLAlchemy ORM
#   controllers/
#     auth_controller.py ........... API endpoints (register, login, me, refresh, logout)
#   dto/
#     auth_dto.py .................. Data Transfer Objects для API
#     user_dto.py .................. Модель пользователя для ответов
#   models/
#     user.py ...................... SQLAlchemy ORM модель User
#   services/
#     auth_service.py .............. Бизнес логика (регистрация, вход)
#     token_service.py ............. Работа с JWT токенами (создание, проверка, отозыв)
#   requests/
#     auth_requests.py ............. Валидация входящих данных
#   main.py ........................ Этот файл (регистрация маршрутов)
# 
# templates/
#   register.html .................. Форма регистрации
#   login.html ..................... Форма входа
#   profile.html ................... Профиль пользователя
# 
# data/
#   app.db ......................... SQLite база данных с таблицей 'users'
# 
# static/
#   (статические файлы если есть)

# =============================================================================
# ПОТОК ДАННЫХ: РЕГИСТРАЦИЯ
# =============================================================================
# 
# 1. ФОРМА (templates/register.html)
#    - Пользователь вводит: username, email, password, c_password, birthday
# 
# 2. ОТПРАВКА (JavaScript в register.html)
#    - fetch POST /api/auth/register { username, email, password, ... }
# 
# 3. ВАЛИДАЦИЯ (app/requests/auth_requests.py - RegisterRequest)
#    - Проверка формата username (мин 7 символов, заглавная, буквы/цифры)
#    - Проверка формата пароля (мин 8, заглавная, цифра, спецсимвол)
#    - Проверка что пароли совпадают
#    - Проверка возраста (>= 14 лет)
# 
# 4. КОНТРОЛЛЕР (app/controllers/auth_controller.py - @router.post("/register"))
#    - Вызывает auth_service.register(data)
# 
# 5. СЕРВИС (app/services/auth_service.py - AuthService.register)
#    - Проверка существования username в БД
#    - Проверка существования email в БД
#    - Хеширование пароля: User.hash_password() (SHA256 + bcrypt)
#    - Вызов save_user() для сохранения в БД
#    - Возврат UserDTO без пароля
# 
# 6. БД (app/models/user.py - save_user)
#    - Создание SQLAlchemy сессии (из app/config/database.py)
#    - INSERT в таблицу 'users' (app.db)
#    - COMMIT изменений
#    - Закрытие сессии
# 
# 7. ОТВЕТ
#    - JSON: { id, username, email, birthday, created_at }
#    - БЕЗ password_hash

# =============================================================================
# ПОТОК ДАННЫХ: ЛОГИН
# =============================================================================
# 
# 1. ФОРМА (templates/login.html)
#    - Пользователь вводит: username, password
# 
# 2. ОТПРАВКА (JavaScript в login.html)
#    - fetch POST /api/auth/login { username, password }
#    - Сохранение tokens в localStorage
# 
# 3. ВАЛИДАЦИЯ (app/requests/auth_requests.py - LoginRequest)
#    - Проверка формата username
#    - Проверка формата пароля
# 
# 4. КОНТРОЛЛЕР (app/controllers/auth_controller.py - @router.post("/login"))
#    - Вызывает auth_service.login(username, password)
# 
# 5. СЕРВИС (app/services/auth_service.py - AuthService.login)
#    - find_user_by_username(username) из БД
#    - User.verify_password(password) - проверка пароля
#    - token_service.create_token_pair(user_id) - генерация токенов
#    - Возврат { access_token, refresh_token, user }
# 
# 6. ГЕНЕРАЦИЯ ТОКЕНОВ (app/services/token_service.py)
#    - Создание JWT с payload: user_id, type, token_id, exp, iat
#    - Сохранение информации о токенах в memory (self.active_tokens)
#    - Возврат двух JWT строк
# 
# 7. ОТВЕТ
#    - JSON: { access_token, refresh_token, user }
# 
# 8. КЛИЕНТ (JavaScript)
#    - localStorage.setItem('access_token', token)
#    - localStorage.setItem('refresh_token', token)
#    - Показать токены пользователю (опционально)

# =============================================================================
# ПОТОК ДАННЫХ: ПОЛУЧЕНИЕ ПРОФИЛЯ (использование токена)
# =============================================================================
# 
# 1. ЗАПРОС (templates/profile.html)
#    - fetch GET /api/auth/me
#    - Header: Authorization: Bearer <access_token>
# 
# 2. КОНТРОЛЛЕР (app/controllers/auth_controller.py - @router.get("/me"))
#    - Извлечение токена из Header Authorization
#    - Проверка формата "Bearer <token>"
# 
# 3. ПРОВЕРКА ТОКЕНА (app/services/token_service.py - TokenService.verify_token)
#    - Декодирование JWT (SECRET_KEY)
#    - Проверка signature
#    - Проверка тип токена == 'access'
#    - Проверка token_id не в черном списке
#    - Проверка дата истечения exp > now
#    - Возврат payload или None
# 
# 4. ИЗВЛЕЧЕНИЕ ДАННЫХ (app/services/auth_service.py - get_user_by_id)
#    - user_id = payload['user_id']
#    - find_user_by_id(user_id) из БД
#    - Возврат пользователя
# 
# 5. ОТВЕТ
#    - JSON: UserDTO { id, username, email, birthday, created_at }
#    - БЕЗ password_hash

# =============================================================================
# ПОТОК ДАННЫХ: ЛОГАУТ
# =============================================================================
# 
# 1. ЗАПРОС (templates/profile.html)
#    - fetch POST /api/auth/logout
#    - Header: Authorization: Bearer <access_token>
# 
# 2. КОНТРОЛЛЕР (app/controllers/auth_controller.py - @router.post("/logout"))
#    - Проверка токена
#    - Вызов token_service.revoke_token(token_id)
# 
# 3. ОТОЗЫВ ТОКЕНА (app/services/token_service.py - TokenService.revoke_token)
#    - Добавить token_id в black_list (self.blacklisted_tokens)
#    - Удалить из active_tokens
#    - Удалить из user_tokens[user_id]
# 
# 4. ОТВЕТ
#    - JSON: { message: "Успешно вышли из системы" }
# 
# 5. КЛИЕНТ (JavaScript)
#    - localStorage.removeItem('access_token')
#    - localStorage.removeItem('refresh_token')
#    - window.location.href = '/login'

# =============================================================================
# БЕЗОПАСНОСТЬ
# =============================================================================
# 
# PASSWORD HASHING:
# - SHA256(password) -> bcrypt с солью
# - Никогда не возвращается password_hash в ответе
# - ИСТОЧНИК: app/models/user.py::User.hash_password()
# 
# JWT TOKENS:
# - Подписаны SECRET_KEY (HS256)
# - Содержат token_id для отслеживания
# - Проверка черного списка при использовании
# - ИСТОЧНИК: app/services/token_service.py
# 
# DATABASE:
# - SQLAlchemy ORM защищает от SQL injection
# - Constraints: UNIQUE для username, email
# - ИСТОЧНИК: app/config/database.py
# 
# VALIDATION:
# - Pydantic валидирует все входящие данные
# - ИСТОЧНИК: app/requests/auth_requests.py

# =============================================================================
# HTML СТРАНИЦЫ (ЧЕРНО-БЕЛЫЙ ДИЗАЙН)
# =============================================================================
# 
# /register - Форма регистрации
#   INPUT: username, email, password, c_password, birthday
#   BUTTON: "ЗАРЕГИСТРИРОВАТЬСЯ"
#   LINK: "ВХОД"
#   STYLE: Черно-белое, квадраты, простое
# 
# /login - Форма входа
#   INPUT: username, password
#   BUTTON: "ВОЙТИ"
#   OUTPUT: Показать tokens (опционально)
#   LINK: "РЕГИСТРАЦИЯ", "ПРОФИЛЬ"
#   STYLE: Черно-белое, квадраты, простое
# 
# /profile - Профиль пользователя
#   DISPLAY: id, username, email, birthday, created_at
#   BUTTON: "ВЫХОД", "ПРОВЕРИТЬ ТОКЕНЫ"
#   LINK: "ВХОД", "РЕГИСТРАЦИЯ"
#   STYLE: Черно-белое, квадраты, простое

# =============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# =============================================================================
# 
# python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# 
# Затем откройте:
# - Регистрация: http://localhost:8000/register
# - Вход: http://localhost:8000/login
# - Профиль: http://localhost:8000/profile
# - API документация: http://localhost:8000/docs

# =============================================================================
# HTML СТРАНИЦЫ
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с ссылками на регистрацию и вход"""
    return """
    <html>
    <head>
        <title>Главная</title>
        <style>
            body { font-family: Arial; background: #fff; margin: 0; padding: 20px; }
            .box { border: 2px solid #000; padding: 20px; max-width: 400px; }
            h1 { border-bottom: 2px solid #000; padding-bottom: 10px; }
            a { display: block; border: 1px solid #000; padding: 10px; margin: 10px 0; text-decoration: none; color: #000; }
            a:hover { background: #000; color: #fff; }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>ГЛАВНАЯ</h1>
            <a href="/register">РЕГИСТРАЦИЯ</a>
            <a href="/login">ВХОД</a>
            <a href="/profile">ПРОФИЛЬ</a>
        </div>
    </body>
    </html>
    """

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Страница регистрации"""
    with open("templates/register.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Страница входа"""
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    """Страница профиля (защищена токеном на клиенте)"""
    with open("templates/profile.html", "r", encoding="utf-8") as f:
        return f.read()

# =============================================================================
# ИНФОРМАЦИОННЫЕ ENDPOINTS
# =============================================================================

@app.get("/health")
async def health():
    """Проверка здоровья сервера"""
    return {"status": "OK", "timestamp": datetime.now().isoformat()}

@app.get("/info")
async def info():
    """Информация о приложении"""
    return {
        "name": "Система Аутентификации",
        "version": "1.0",
        "endpoints": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "me": "GET /api/auth/me",
            "refresh": "POST /api/auth/refresh",
            "logout": "POST /api/auth/logout"
        }
    }

# =============================================================================
# КОНЕЦ ФАЙЛА
# =============================================================================
