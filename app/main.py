"""
═════════════════════════════════════════════════════════════════════════════
ОСНОВНОЙ ФАЙЛ ПРИЛОЖЕНИЯ - ДОКУМЕНТАЦИЯ ПРОЦЕССА АУТЕНТИФИКАЦИИ
═════════════════════════════════════════════════════════════════════════════

ПОЛНЫЙ ЦИКЛ АУТЕНТИФИКАЦИИ И АВТОРИЗАЦИИ:

1. РЕГИСТРАЦИЯ (POST /api/auth/register)
   └─ Пользователь создает аккаунт сUsername, Email, Password, Birthday

2. ЛОГИН (POST /api/auth/login)
   └─ Пользователь входит, получает пару токенов (access + refresh)

3. ИСПОЛЬЗОВАНИЕ ТОКЕНА (GET /api/auth/me)
   └─ Отправляет access_token в заголовке Authorization: Bearer <token>
   └─ Сервер проверяет подпись, срок действия, черный список

4. ОБНОВЛЕНИЕ ТОКЕНА (POST /api/auth/refresh)
   └─ Обмен refresh_token на новую пару токенов
   └─ Refresh токен одноразовый и утрачивает силу

5. СПИСОК АКТИВНЫХ ТОКЕНОВ (GET /api/auth/tokens)
   └─ Получение метаданных всех активных токенов пользователя

6. ВЫХОД СО ВСЕХ УСТРОЙСТВ (POST /api/auth/out_all)
   └─ Отзыв всех активных токенов пользователя

7. ЛОГАУТ (POST /api/auth/logout)
   └─ Выход из текущей сессии, отзыв текущего токена

═════════════════════════════════════════════════════════════════════════════
"""

# ═════════════════════════════════════════════════════════════════════════════
# ИМПОРТЫ
# ═════════════════════════════════════════════════════════════════════════════

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging

# ИСТОЧНИК: app/models/user.py
# Функция: init_db() - инициализирует SQLite БД, создает таблицу users
from app.models.user import init_db

# ИСТОЧНИК: app/controllers/auth_controller.py
# Содержит: 7 маршрутов (login, register, me, refresh, logout, tokens, out_all)
from app.controllers.auth_controller import router as auth_router

# ИСТОЧНИК: app/controllers/info_controller.py
# Содержит: 3 маршрута информации (server, client, database)
from app.controllers.info_controller import router as info_router

# ИСТОЧНИК: app/controllers/role_controller.py
# Содержит: 7 маршрутов для управления ролями
from app.controllers.role_controller import router as role_router

# ИСТОЧНИК: app/controllers/permission_controller.py
# Содержит: 7 маршрутов для управления разрешениями
from app.controllers.permission_controller import router as permission_router

# ИСТОЧНИК: app/services/token_service.py
# Синглтон TokenService для управления JWT токенами
from app.services.token_service import TokenService

# ═════════════════════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lab2")

# ═════════════════════════════════════════════════════════════════════════════
# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ
# ═════════════════════════════════════════════════════════════════════════════

# Инициализация БД
# ИСТОЧНИК: app/models/user.py::init_db()
# Создает таблицу users с колонками: id, username, email, password_hash, birthday, created_at
init_db()
logger.info("✅ БД инициализирована")

app = FastAPI(
    title="Lab2 - Authentication API",
    description="Система аутентификации и авторизации с токенами",
    version="1.0.0"
)

# ИСТОЧНИК: app/controllers/auth_controller.py
# Подключение всех 7 API маршрутов для аутентификации
app.include_router(auth_router)

# ИСТОЧНИК: app/controllers/info_controller.py
# Подключение маршрутов информации о сервере, клиенте, БД
app.include_router(info_router)

# ИСТОЧНИК: app/controllers/role_controller.py
# Подключение маршрутов для управления ролями
app.include_router(role_router)

# ИСТОЧНИК: app/controllers/permission_controller.py
# Подключение маршрутов для управления разрешениями
app.include_router(permission_router)

# ═════════════════════════════════════════════════════════════════════════════
# HTML СТРАНИЦЫ
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Главная страница с навигацией
    ДИЗАЙН: Черно-белый, без украшений
    """
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Lab2 - Аутентификация</title>
        <style>
            body { font-family: Arial, sans-serif; background: #ffffff; display: flex; 
                   justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .container { background: #ffffff; border: 2px solid #000000; padding: 30px; 
                         width: 100%; max-width: 400px; }
            h1 { text-align: center; color: #000000; border-bottom: 2px solid #000000; padding-bottom: 15px; }
            .nav { text-align: center; margin-top: 20px; }
            a { display: block; margin: 10px 0; padding: 10px; background: #000000; 
                color: #ffffff; text-decoration: none; border: 1px solid #000000; }
            a:hover { background: #333333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>АУТЕНТИФИКАЦИЯ</h1>
            <div class="nav">
                <a href="/register">РЕГИСТРАЦИЯ</a>
                <a href="/login">ВХОД</a>
                <a href="/profile">ПРОФИЛЬ</a>
                <a href="/docs">API ДОКУМЕНТАЦИЯ</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """
    Страница регистрации
    МАРШРУТ БЕКЕНДА: POST /api/auth/register (app/controllers/auth_controller.py::register)
    """
    with open("templates/register.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """
    Страница логина
    МАРШРУТ БЕКЕНДА: POST /api/auth/login (app/controllers/auth_controller.py::login)
    """
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    """
    Страница профиля (защищенная, требует access_token)
    МАРШРУТЫ БЕКЕНДА:
      - GET /api/auth/me (app/controllers/auth_controller.py::get_me)
      - GET /api/auth/tokens (app/controllers/auth_controller.py::get_tokens)
      - POST /api/auth/logout (app/controllers/auth_controller.py::logout)
      - POST /api/auth/out_all (app/controllers/auth_controller.py::logout_all)
    """
    with open("templates/profile.html", "r", encoding="utf-8") as f:
        return f.read()

# ═════════════════════════════════════════════════════════════════════════════
# СИСТЕМНЫЕ МАРШРУТЫ
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Проверка здоровья сервера"""
    from datetime import datetime
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/info")
async def info():
    """
    Информация о приложении
    ИСТОЧНИКИ МОДУЛЕЙ:
      - app/models/user.py (User ORM model, init_db)
      - app/services/auth_service.py (AuthService for login/register)
      - app/services/token_service.py (TokenService for JWT management)
      - app/controllers/auth_controller.py (7 API endpoints)
      - app/dto/ (UserDTO, AuthSuccessDTO, TokenListDTO)
    """
    return {
        "name": "Lab2 - Authentication API",
        "version": "1.0.0",
        "description": "JWT-based authentication system with FastAPI",
        "documentation": "http://localhost:8000/docs",
        "endpoints": {
            "registration": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "get_profile": "GET /api/auth/me",
            "get_tokens": "GET /api/auth/tokens",
            "refresh_token": "POST /api/auth/refresh",
            "logout": "POST /api/auth/logout",
            "logout_all_devices": "POST /api/auth/out_all"
        }
    }

logger.info("✅ Приложение готово к работе на http://0.0.0.0:8000")
logger.info("✅ Документация доступна на http://0.0.0.0:8000/docs")
