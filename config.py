# config.py
import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Пути внутри Docker контейнера (Linux пути)
    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/model_weights")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "/app/processed")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/app/temp")
    LOG_DIR: str = os.getenv("LOG_DIR", "/app/logs")
    DB_PATH: str = os.getenv("DB_PATH", "/app/database")
    
    # Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:secure_password123@postgres:5432/agentrecognition")
    
    # Настройки Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "redispass123")
    
    # Настройки API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "2"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Настройки модели
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "2048"))
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    MODEL_TOP_P: float = float(os.getenv("MODEL_TOP_P", "0.9"))
    
    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Настройки файлов
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".mp4", ".avi", ".mov"}
    
    # Настройки базы данных
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secure_password123")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "agentrecognition")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", 
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    # Альтернативно, можно использовать admin пользователя для приложения:
    APP_DATABASE_URL: str = os.getenv("APP_DATABASE_URL",
        f"postgresql://admin:secure_password123@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    @classmethod
    def init_directories(cls) -> None:
        """Создание всех необходимых директорий"""
        directories = [
            cls.UPLOAD_DIR,
            cls.PROCESSED_DIR,
            cls.TEMP_DIR,
            cls.LOG_DIR,
            cls.DB_PATH,
            os.path.join(cls.UPLOAD_DIR, "images"),
            os.path.join(cls.UPLOAD_DIR, "videos"),
            os.path.join(cls.UPLOAD_DIR, "documents"),
            os.path.join(cls.PROCESSED_DIR, "results"),
            os.path.join(cls.PROCESSED_DIR, "archives"),
            os.path.join(cls.PROCESSED_DIR, "thumbnails"),
            os.path.join(cls.LOG_DIR, "app"),
            os.path.join(cls.LOG_DIR, "access"),
            os.path.join(cls.LOG_DIR, "errors"),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"Created/verified directory: {directory}")
    
    @classmethod
    def get_paths_info(cls) -> Dict[str, Any]:
        """Информация о всех путях"""
        return {
            "model": cls.MODEL_PATH,
            "uploads": cls.UPLOAD_DIR,
            "processed": cls.PROCESSED_DIR,
            "temp": cls.TEMP_DIR,
            "logs": cls.LOG_DIR,
            "database": cls.DB_PATH,
            "exists": {
                "model": os.path.exists(cls.MODEL_PATH),
                "uploads": os.path.exists(cls.UPLOAD_DIR),
                "processed": os.path.exists(cls.PROCESSED_DIR),
                "temp": os.path.exists(cls.TEMP_DIR),
                "logs": os.path.exists(cls.LOG_DIR),
                "database": os.path.exists(cls.DB_PATH),
            }
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Валидация конфигурации"""
        errors = []
        
        # Проверка обязательных путей
        if not os.path.exists(cls.MODEL_PATH):
            errors.append(f"Model path does not exist: {cls.MODEL_PATH}")
        
        # Проверка размера загрузки
        if cls.MAX_UPLOAD_SIZE_MB <= 0 or cls.MAX_UPLOAD_SIZE_MB > 1024:
            errors.append(f"Invalid MAX_UPLOAD_SIZE_MB: {cls.MAX_UPLOAD_SIZE_MB}")
        
        if errors:
            for error in errors:
                logging.error(error)
            return False
        
        return True

# Глобальный экземпляр конфигурации
config = Config()