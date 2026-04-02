from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Laba"
    APP_ENV: str = "local"
    PORT: int = 8000
    
    locale: str = "ru"
    timezone: str = "Europe/Moscow"
    
    DATABASE_NAME: str 
    DATABASE_URL: str 
    
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 дней
    MAX_ACTIVE_TOKENS: int = 2  # Максимум 2 активных сеанса (2 пары = 4 токена)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()