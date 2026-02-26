from fastapi import FastAPI
from .controllers import info_controller
from .config.settings import settings

# Создаем приложение FastAPI
app = FastAPI(
    title="Лабораторная работа №1",
    description="Первичная установка и настройка. Работа с DTO",
    version="1.0.0"
)

# Подключаем маршруты
app.include_router(info_controller.router)

@app.get("/")
async def root():
    """Корневой маршрут для проверки"""
    return {
        "message": "Лабораторная работа №1",
        "locale": settings.locale,
        "timezone": settings.timezone,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}