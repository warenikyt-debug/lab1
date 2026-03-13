from fastapi import FastAPI
from .controllers import info_controller, auth_controller
from .config.settings import settings

# Создаем приложение FastAPI
app = FastAPI(
    title="Лабораторная работа №2",
    description="Реализация механизма авторизации и регистрации пользователей через API",
    version="2.0.0"
)

# Подключаем маршруты
app.include_router(info_controller.router)
app.include_router(auth_controller.router, prefix="/api")

@app.get("/")
async def root():
    """Корневой маршрут для проверки"""
    return {
        "message": "Лабораторная работа №2",
        "locale": settings.locale,
        "timezone": settings.timezone,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}