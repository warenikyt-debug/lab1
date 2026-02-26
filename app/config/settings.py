from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Настройки приложения
    """
    # Локаль и временная зона
    locale: str = "ru"
    timezone: str = "Europe/Moscow"
    
    # Настройки базы данных
    DATABASE_DRIVER: str = "sqlite"
    DATABASE_NAME: str = "app.db"
    DATABASE_URL: str = "sqlite:///./app.db"
    
    # Добавляем поля из .env
    APP_NAME: str = "Laba1"
    APP_ENV: str = "local"
    DB_CONNECTION: str = "sqlite"
    DB_DATABASE: str = "app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()