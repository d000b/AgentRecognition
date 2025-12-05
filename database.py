# database.py
import os
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from config import config

# Создание движка базы данных
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

class InferenceRequestDB(Base):
    """Модель для хранения запросов inference"""
    __tablename__ = "inference_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), unique=True, index=True, nullable=False)
    session_id = Column(String(36), index=True, nullable=True)
    text_prompt = Column(Text, nullable=False)
    image_paths = Column(JSON, nullable=True)  # Список путей/URL к изображениям
    parameters = Column(JSON, nullable=True)  # Параметры генерации
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    tokens_generated = Column(Integer, nullable=True)
    model_used = Column(String(100), default="Qwen3-VL-30B-A3B-Instruct")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "text_prompt": self.text_prompt,
            "image_paths": self.image_paths,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "tokens_generated": self.tokens_generated,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

class FileStorage(Base):
    """Модель для хранения информации о файлах"""
    __tablename__ = "file_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # image, video, document
    file_extension = Column(String(10), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    md5_hash = Column(String(32), nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    uploaded_by = Column(String(100), nullable=True)
    session_id = Column(String(36), index=True, nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_result = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    
    def to_dict(self):
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "file_hash": self.file_hash,
            "original_filename": self.original_filename,
            "storage_path": self.storage_path,
            "file_type": self.file_type,
            "file_extension": self.file_extension,
            "size_bytes": self.size_bytes,
            "uploaded_by": self.uploaded_by,
            "session_id": self.session_id,
            "is_processed": self.is_processed,
            "processing_result": self.processing_result,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
        }

class SystemLog(Base):
    """Модель для системных логов"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    source = Column(String(100), nullable=False)  # Модуль/компонент
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    def to_dict(self):
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

# Создание таблиц
def create_tables():
    """Создание всех таблиц в базе данных"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def drop_tables():
    """Удаление всех таблиц (только для разработки)"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")

# Инициализация базы данных при импорте
if __name__ == "__main__":
    create_tables()
else:
    # Проверяем и создаем таблицы при запуске модуля
    try:
        create_tables()
    except Exception as e:
        print(f"Error creating tables: {e}")